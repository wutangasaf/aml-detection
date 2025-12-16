"""
Narrative Prediction Experiment

Core hypothesis: If a narrative is strong, it can predict the next transaction.
Prediction error becomes both:
1. Narrative quality metric (low error = good narrative)
2. Anomaly signal (sudden high error after low error = suspicious)

This experiment tests whether prediction error correlates with is_laundering.
"""

import os
import certifi
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from pymongo import MongoClient
from dataclasses import dataclass, field
from typing import Optional
import json

# ============================================================
# CONFIGURATION
# ============================================================

MONGODB_URI = "mongodb+srv://dev_db_user:EyMpA37VXGa3Kjmc@aml-research.sgpnzv8.mongodb.net/?appName=AML-Research"
DATABASE_NAME = "aml_db"

# Minimum transactions needed to build a narrative
MIN_HISTORY_FOR_NARRATIVE = 10
# Minimum transactions in test set
MIN_TEST_TRANSACTIONS = 5
# Train/test split ratio
TRAIN_RATIO = 0.7

# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Narrative:
    """Statistical narrative built from transaction history."""
    # Amount statistics
    amount_mean: float = 0.0
    amount_std: float = 0.0
    amount_min: float = 0.0
    amount_max: float = 0.0

    # Timing statistics (days between transactions)
    interval_mean: float = 0.0
    interval_std: float = 0.0

    # Counterparty statistics
    known_counterparties: set = field(default_factory=set)
    known_banks: set = field(default_factory=set)
    new_counterparty_rate: float = 0.0  # How often they transact with new parties

    # Payment format distribution
    payment_format_probs: dict = field(default_factory=dict)

    # Direction (in vs out) - for this dataset we focus on outbound
    outbound_ratio: float = 1.0

    # Transaction count used to build this narrative
    transaction_count: int = 0

    def __post_init__(self):
        if not isinstance(self.known_counterparties, set):
            self.known_counterparties = set()
        if not isinstance(self.known_banks, set):
            self.known_banks = set()
        if not isinstance(self.payment_format_probs, dict):
            self.payment_format_probs = {}


@dataclass
class Prediction:
    """Prediction for next transaction."""
    amount_expected: float
    amount_std: float
    days_until_next: float
    days_std: float
    likely_known_counterparty: bool
    likely_payment_format: str


@dataclass
class PredictionResult:
    """Result of comparing prediction to actual transaction."""
    # Raw values
    predicted_amount: float
    actual_amount: float
    predicted_interval: float
    actual_interval: float
    predicted_known_counterparty: bool
    actual_known_counterparty: bool
    predicted_payment_format: str
    actual_payment_format: str

    # Error components
    amount_z_score: float  # How many std devs from expected
    interval_z_score: float
    counterparty_error: float  # 0 if matched prediction, 1 if not
    format_error: float  # 0 if matched, 1 if not

    # Combined error
    total_error: float

    # Ground truth
    is_laundering: bool

    # Metadata
    account_id: str = ""
    transaction_timestamp: Optional[datetime] = None


# ============================================================
# NARRATIVE BUILDER
# ============================================================

class NarrativeBuilder:
    """Builds statistical narratives from transaction history."""

    @staticmethod
    def extract_amount(transaction: dict) -> float:
        """Extract amount from transaction."""
        amt = transaction.get("amount", {})
        if isinstance(amt, dict):
            return float(amt.get("sent", 0) or amt.get("received", 0) or 0)
        return float(amt or 0)

    @staticmethod
    def extract_counterparty(transaction: dict) -> str:
        """Extract receiver account ID."""
        receiver = transaction.get("receiver", {})
        if isinstance(receiver, dict):
            return receiver.get("account_id", "unknown")
        return "unknown"

    @staticmethod
    def extract_bank(transaction: dict) -> str:
        """Extract receiver bank ID."""
        receiver = transaction.get("receiver", {})
        if isinstance(receiver, dict):
            return receiver.get("bank_id", "unknown")
        return "unknown"

    @staticmethod
    def extract_timestamp(transaction: dict) -> Optional[datetime]:
        """Extract timestamp from transaction."""
        ts = transaction.get("timestamp")
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except:
                return None
        return None

    def build_narrative(self, transactions: list) -> Narrative:
        """Build a narrative from transaction history."""
        if not transactions:
            return Narrative()

        # Extract amounts
        amounts = [self.extract_amount(t) for t in transactions]
        amounts = [a for a in amounts if a > 0]  # Filter zeros

        # Extract timestamps and compute intervals
        timestamps = [self.extract_timestamp(t) for t in transactions]
        timestamps = [ts for ts in timestamps if ts is not None]
        timestamps.sort()

        intervals = []
        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i-1]).total_seconds() / 86400  # Days
            if delta > 0:
                intervals.append(delta)

        # Extract counterparties
        counterparties = [self.extract_counterparty(t) for t in transactions]
        banks = [self.extract_bank(t) for t in transactions]

        # Track new counterparty rate
        seen = set()
        new_count = 0
        for cp in counterparties:
            if cp not in seen:
                new_count += 1
                seen.add(cp)
        new_counterparty_rate = new_count / len(counterparties) if counterparties else 0

        # Payment format distribution
        formats = [t.get("payment_format", "Unknown") for t in transactions]
        format_counts = defaultdict(int)
        for f in formats:
            format_counts[f] += 1
        total = sum(format_counts.values())
        format_probs = {k: v/total for k, v in format_counts.items()}

        return Narrative(
            amount_mean=np.mean(amounts) if amounts else 0,
            amount_std=np.std(amounts) if len(amounts) > 1 else np.mean(amounts) * 0.5,
            amount_min=min(amounts) if amounts else 0,
            amount_max=max(amounts) if amounts else 0,
            interval_mean=np.mean(intervals) if intervals else 7,
            interval_std=np.std(intervals) if len(intervals) > 1 else 3,
            known_counterparties=set(counterparties),
            known_banks=set(banks),
            new_counterparty_rate=new_counterparty_rate,
            payment_format_probs=format_probs,
            transaction_count=len(transactions)
        )

    def update_narrative(self, narrative: Narrative, transaction: dict) -> Narrative:
        """Incrementally update narrative with new transaction."""
        # For simplicity, we'll rebuild from scratch in this experiment
        # In production, you'd use online/streaming statistics
        return narrative


# ============================================================
# PREDICTOR
# ============================================================

class NarrativePredictor:
    """Predicts next transaction based on narrative."""

    def predict_next(self, narrative: Narrative) -> Prediction:
        """Generate prediction for next transaction."""
        # Most likely payment format
        if narrative.payment_format_probs:
            likely_format = max(narrative.payment_format_probs,
                              key=narrative.payment_format_probs.get)
        else:
            likely_format = "Unknown"

        return Prediction(
            amount_expected=narrative.amount_mean,
            amount_std=narrative.amount_std if narrative.amount_std > 0 else narrative.amount_mean * 0.5,
            days_until_next=narrative.interval_mean,
            days_std=narrative.interval_std if narrative.interval_std > 0 else 3,
            likely_known_counterparty=(narrative.new_counterparty_rate < 0.5),
            likely_payment_format=likely_format
        )

    def score_transaction(self,
                         prediction: Prediction,
                         narrative: Narrative,
                         transaction: dict,
                         prev_timestamp: Optional[datetime]) -> PredictionResult:
        """Score how well actual transaction matches prediction."""

        builder = NarrativeBuilder()

        # Extract actual values
        actual_amount = builder.extract_amount(transaction)
        actual_counterparty = builder.extract_counterparty(transaction)
        actual_bank = builder.extract_bank(transaction)
        actual_format = transaction.get("payment_format", "Unknown")
        actual_timestamp = builder.extract_timestamp(transaction)
        is_laundering = transaction.get("is_laundering", False)

        # Compute actual interval
        if prev_timestamp and actual_timestamp:
            actual_interval = (actual_timestamp - prev_timestamp).total_seconds() / 86400
        else:
            actual_interval = prediction.days_until_next  # Assume expected if unknown

        # Check if counterparty is known
        actual_known = actual_counterparty in narrative.known_counterparties

        # Compute errors

        # Amount z-score (how many std devs from mean)
        if prediction.amount_std > 0:
            amount_z = abs(actual_amount - prediction.amount_expected) / prediction.amount_std
        else:
            amount_z = 0 if actual_amount == prediction.amount_expected else 2.0

        # Interval z-score
        if prediction.days_std > 0:
            interval_z = abs(actual_interval - prediction.days_until_next) / prediction.days_std
        else:
            interval_z = 0

        # Counterparty error (weighted by new counterparty rate)
        # If we expect known counterparties and get unknown, that's surprising
        if prediction.likely_known_counterparty and not actual_known:
            # Surprise factor based on how rarely they use new counterparties
            counterparty_error = 1.0 - narrative.new_counterparty_rate
        elif not prediction.likely_known_counterparty and actual_known:
            counterparty_error = narrative.new_counterparty_rate
        else:
            counterparty_error = 0.0

        # Format error
        format_prob = narrative.payment_format_probs.get(actual_format, 0)
        format_error = 1.0 - format_prob  # Higher error for less common formats

        # Combined error (weighted)
        # Amount is most important, then counterparty, then timing, then format
        total_error = (
            0.40 * min(amount_z, 5.0) +      # Cap at 5 std devs
            0.25 * counterparty_error * 3 +   # Scale to similar range
            0.20 * min(interval_z, 5.0) +
            0.15 * format_error * 3
        )

        return PredictionResult(
            predicted_amount=prediction.amount_expected,
            actual_amount=actual_amount,
            predicted_interval=prediction.days_until_next,
            actual_interval=actual_interval,
            predicted_known_counterparty=prediction.likely_known_counterparty,
            actual_known_counterparty=actual_known,
            predicted_payment_format=prediction.likely_payment_format,
            actual_payment_format=actual_format,
            amount_z_score=amount_z,
            interval_z_score=interval_z,
            counterparty_error=counterparty_error,
            format_error=format_error,
            total_error=total_error,
            is_laundering=is_laundering,
            transaction_timestamp=actual_timestamp
        )


# ============================================================
# EXPERIMENT RUNNER
# ============================================================

def run_experiment(db, max_accounts: int = 200, verbose: bool = True):
    """
    Run the prediction experiment on accounts with transaction history.

    For each account:
    1. Split transactions into train (70%) and test (30%)
    2. Build narrative from training transactions
    3. For each test transaction, predict and measure error
    4. Compare error distributions for laundering vs clean
    """

    print("\n" + "="*70)
    print("NARRATIVE PREDICTION EXPERIMENT")
    print("Hypothesis: Prediction error correlates with laundering")
    print("="*70)

    builder = NarrativeBuilder()
    predictor = NarrativePredictor()

    # Collect results
    all_results: list[PredictionResult] = []
    accounts_processed = 0

    # Find accounts with sufficient transaction history
    print("\n[1/3] Finding accounts with sufficient history...")

    # Get accounts with laundering transactions (prioritize these)
    laundering_accounts = list(db.transactions.aggregate([
        {"$match": {"is_laundering": True}},
        {"$group": {"_id": "$sender.account_id", "launder_count": {"$sum": 1}}},
        {"$match": {"launder_count": {"$gte": 1}}},
        {"$limit": max_accounts // 2}
    ]))
    laundering_account_ids = [a["_id"] for a in laundering_accounts]

    # Get clean accounts (no laundering)
    clean_accounts = list(db.transactions.aggregate([
        {"$match": {"sender.account_id": {"$nin": laundering_account_ids}}},
        {"$group": {"_id": "$sender.account_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": MIN_HISTORY_FOR_NARRATIVE + MIN_TEST_TRANSACTIONS}}},
        {"$limit": max_accounts // 2}
    ]))
    clean_account_ids = [a["_id"] for a in clean_accounts]

    all_account_ids = laundering_account_ids + clean_account_ids
    print(f"    Found {len(laundering_account_ids)} accounts with laundering")
    print(f"    Found {len(clean_account_ids)} clean accounts")

    # Process each account
    print(f"\n[2/3] Processing {len(all_account_ids)} accounts...")

    for account_id in all_account_ids:
        # Get all transactions for this account, sorted by time
        transactions = list(db.transactions.find({
            "sender.account_id": account_id
        }).sort("timestamp", 1))

        if len(transactions) < MIN_HISTORY_FOR_NARRATIVE + MIN_TEST_TRANSACTIONS:
            continue

        # Split into train/test
        split_idx = int(len(transactions) * TRAIN_RATIO)
        train_txns = transactions[:split_idx]
        test_txns = transactions[split_idx:]

        if len(train_txns) < MIN_HISTORY_FOR_NARRATIVE or len(test_txns) < MIN_TEST_TRANSACTIONS:
            continue

        # Build narrative from training data
        narrative = builder.build_narrative(train_txns)

        # Get last training timestamp
        prev_timestamp = builder.extract_timestamp(train_txns[-1])

        # Test predictions
        account_results = []
        for txn in test_txns:
            prediction = predictor.predict_next(narrative)
            result = predictor.score_transaction(prediction, narrative, txn, prev_timestamp)
            result.account_id = account_id
            account_results.append(result)

            # Update prev_timestamp for next iteration
            current_ts = builder.extract_timestamp(txn)
            if current_ts:
                prev_timestamp = current_ts

            # Update narrative with this transaction (incremental learning)
            # For simplicity, rebuild with all history up to this point
            narrative.known_counterparties.add(builder.extract_counterparty(txn))
            narrative.known_banks.add(builder.extract_bank(txn))

        all_results.extend(account_results)
        accounts_processed += 1

        if verbose and accounts_processed % 20 == 0:
            print(f"    Processed {accounts_processed} accounts, {len(all_results)} predictions...")

    print(f"\n    Total: {accounts_processed} accounts, {len(all_results)} predictions")

    # Analyze results
    print(f"\n[3/3] Analyzing results...")

    return analyze_results(all_results)


def analyze_results(results: list[PredictionResult]) -> dict:
    """Analyze prediction results and compute statistics."""

    if not results:
        print("No results to analyze!")
        return {}

    # Separate by laundering status
    laundering_results = [r for r in results if r.is_laundering]
    clean_results = [r for r in results if not r.is_laundering]

    print(f"\n    Laundering transactions: {len(laundering_results)}")
    print(f"    Clean transactions: {len(clean_results)}")

    # Compute error statistics
    launder_errors = [r.total_error for r in laundering_results]
    clean_errors = [r.total_error for r in clean_results]

    launder_amount_z = [r.amount_z_score for r in laundering_results]
    clean_amount_z = [r.amount_z_score for r in clean_results]

    launder_cp_err = [r.counterparty_error for r in laundering_results]
    clean_cp_err = [r.counterparty_error for r in clean_results]

    print("\n" + "="*70)
    print("RESULTS: ERROR DISTRIBUTION BY TRANSACTION TYPE")
    print("="*70)

    print("\n┌─────────────────────┬────────────────┬────────────────┐")
    print("│ Metric              │   Laundering   │     Clean      │")
    print("├─────────────────────┼────────────────┼────────────────┤")

    if launder_errors and clean_errors:
        print(f"│ Total Error (mean)  │     {np.mean(launder_errors):>6.3f}     │     {np.mean(clean_errors):>6.3f}     │")
        print(f"│ Total Error (std)   │     {np.std(launder_errors):>6.3f}     │     {np.std(clean_errors):>6.3f}     │")
        print(f"│ Total Error (median)│     {np.median(launder_errors):>6.3f}     │     {np.median(clean_errors):>6.3f}     │")
        print("├─────────────────────┼────────────────┼────────────────┤")
        print(f"│ Amount Z-score      │     {np.mean(launder_amount_z):>6.3f}     │     {np.mean(clean_amount_z):>6.3f}     │")
        print(f"│ Counterparty Error  │     {np.mean(launder_cp_err):>6.3f}     │     {np.mean(clean_cp_err):>6.3f}     │")

    print("└─────────────────────┴────────────────┴────────────────┘")

    # Statistical significance test
    if launder_errors and clean_errors:
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(launder_errors, clean_errors)

        print(f"\nStatistical Test (t-test):")
        print(f"    t-statistic: {t_stat:.4f}")
        print(f"    p-value: {p_value:.6f}")

        if p_value < 0.05:
            print("    *** SIGNIFICANT DIFFERENCE (p < 0.05) ***")
        else:
            print("    Not statistically significant (p >= 0.05)")

        # Effect size (Cohen's d)
        pooled_std = np.sqrt((np.std(launder_errors)**2 + np.std(clean_errors)**2) / 2)
        if pooled_std > 0:
            cohens_d = (np.mean(launder_errors) - np.mean(clean_errors)) / pooled_std
            print(f"    Effect size (Cohen's d): {cohens_d:.4f}")

    # Distribution analysis
    print("\n" + "="*70)
    print("ERROR DISTRIBUTION (PERCENTILES)")
    print("="*70)

    if launder_errors and clean_errors:
        percentiles = [25, 50, 75, 90, 95, 99]

        print("\n┌─────────────┬────────────────┬────────────────┐")
        print("│ Percentile  │   Laundering   │     Clean      │")
        print("├─────────────┼────────────────┼────────────────┤")

        for p in percentiles:
            l_val = np.percentile(launder_errors, p)
            c_val = np.percentile(clean_errors, p)
            print(f"│     {p:>2}th     │     {l_val:>6.3f}     │     {c_val:>6.3f}     │")

        print("└─────────────┴────────────────┴────────────────┘")

    # ROC-like analysis: Can error alone separate laundering from clean?
    print("\n" + "="*70)
    print("DETECTION PERFORMANCE (using error as threshold)")
    print("="*70)

    if launder_errors and clean_errors:
        all_errors = [(r.total_error, r.is_laundering) for r in results]
        all_errors.sort(key=lambda x: x[0], reverse=True)  # Highest error first

        # Try different thresholds
        thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

        print("\n┌───────────┬───────────┬───────────┬───────────┬───────────┐")
        print("│ Threshold │ Precision │  Recall   │    F1     │  Flagged  │")
        print("├───────────┼───────────┼───────────┼───────────┼───────────┤")

        best_f1 = 0
        best_threshold = 0

        for threshold in thresholds:
            # Transactions with error > threshold are "flagged"
            flagged = [r for r in results if r.total_error > threshold]
            tp = sum(1 for r in flagged if r.is_laundering)
            fp = sum(1 for r in flagged if not r.is_laundering)
            fn = sum(1 for r in results if r.is_laundering and r.total_error <= threshold)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold

            print(f"│   {threshold:>5.1f}   │   {precision:>5.1%}   │   {recall:>5.1%}   │   {f1:>5.3f}   │   {len(flagged):>5}   │")

        print("└───────────┴───────────┴───────────┴───────────┴───────────┘")
        print(f"\n    Best F1: {best_f1:.3f} at threshold {best_threshold}")

    # Component analysis: which error component is most predictive?
    print("\n" + "="*70)
    print("COMPONENT ANALYSIS")
    print("="*70)

    print("\nWhich error component best separates laundering from clean?")

    if laundering_results and clean_results:
        components = [
            ("Amount Z-score", launder_amount_z, clean_amount_z),
            ("Counterparty Error", launder_cp_err, clean_cp_err),
            ("Interval Z-score",
             [r.interval_z_score for r in laundering_results],
             [r.interval_z_score for r in clean_results]),
            ("Format Error",
             [r.format_error for r in laundering_results],
             [r.format_error for r in clean_results])
        ]

        print("\n┌─────────────────────┬────────────┬───────────────┐")
        print("│ Component           │  Diff Mean │   p-value     │")
        print("├─────────────────────┼────────────┼───────────────┤")

        for name, launder_vals, clean_vals in components:
            if launder_vals and clean_vals:
                diff = np.mean(launder_vals) - np.mean(clean_vals)
                _, p = stats.ttest_ind(launder_vals, clean_vals)
                sig = "***" if p < 0.05 else ""
                print(f"│ {name:<19} │   {diff:>+6.3f}  │  {p:>10.6f} {sig:<3}│")

        print("└─────────────────────┴────────────┴───────────────┘")

    # Return summary
    return {
        "total_predictions": len(results),
        "laundering_count": len(laundering_results),
        "clean_count": len(clean_results),
        "laundering_error_mean": np.mean(launder_errors) if launder_errors else 0,
        "clean_error_mean": np.mean(clean_errors) if clean_errors else 0,
        "best_f1": best_f1 if launder_errors and clean_errors else 0,
        "best_threshold": best_threshold if launder_errors and clean_errors else 0,
        "all_results": results
    }


def visualize_distribution(results: list[PredictionResult]):
    """Create ASCII histogram of error distributions."""

    laundering_errors = [r.total_error for r in results if r.is_laundering]
    clean_errors = [r.total_error for r in results if not r.is_laundering]

    if not laundering_errors or not clean_errors:
        return

    print("\n" + "="*70)
    print("ERROR DISTRIBUTION HISTOGRAM")
    print("="*70)

    # Create bins
    max_error = max(max(laundering_errors), max(clean_errors))
    bins = np.linspace(0, min(max_error, 5), 20)

    launder_hist, _ = np.histogram(laundering_errors, bins=bins)
    clean_hist, _ = np.histogram(clean_errors, bins=bins)

    # Normalize to percentages
    launder_hist = launder_hist / len(laundering_errors) * 100
    clean_hist = clean_hist / len(clean_errors) * 100

    max_pct = max(max(launder_hist), max(clean_hist))
    scale = 40 / max_pct if max_pct > 0 else 1

    print("\nLaundering transactions (L) vs Clean transactions (C)")
    print("Each character = ~{:.1f}%".format(1/scale))
    print()

    for i, (l, c) in enumerate(zip(launder_hist, clean_hist)):
        bin_start = bins[i]
        bin_end = bins[i+1] if i+1 < len(bins) else bins[i]

        l_bar = "L" * int(l * scale)
        c_bar = "C" * int(c * scale)

        print(f"{bin_start:>4.1f}-{bin_end:<4.1f} │ {l_bar}")
        print(f"         │ {c_bar}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("Connecting to MongoDB...")
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=30000,
        tlsCAFile=certifi.where()
    )
    db = client[DATABASE_NAME]

    # Run experiment
    results = run_experiment(db, max_accounts=200, verbose=True)

    # Visualize if we have results
    if results.get("all_results"):
        visualize_distribution(results["all_results"])

    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)

    if results.get("laundering_error_mean", 0) > results.get("clean_error_mean", 0):
        diff_pct = ((results["laundering_error_mean"] / results["clean_error_mean"]) - 1) * 100 if results["clean_error_mean"] > 0 else 0
        print(f"\nLaundering transactions have {diff_pct:.1f}% higher prediction error on average.")
        print(f"Best F1 score achievable: {results.get('best_f1', 0):.3f}")
        print("\nThis suggests prediction error CAN be used as an anomaly signal,")
        print("but likely needs to be combined with other features for production use.")
    else:
        print("\nUnexpected: Clean transactions have higher error than laundering.")
        print("This may indicate the narrative model needs refinement.")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
