"""
CNA Day-by-Day Simulator

Simulates processing transactions chronologically to test if the
Customer Narrative Analyzer can detect laundering by identifying
transactions that break the customer's established narrative.
"""

import os
import json
import certifi
from datetime import datetime, timedelta
from pymongo import MongoClient
from openai import OpenAI

# ============================================================
# CONFIGURATION
# ============================================================

MONGODB_URI = "mongodb+srv://dev_db_user:EyMpA37VXGa3Kjmc@aml-research.sgpnzv8.mongodb.net/?appName=AML-Research"
DATABASE_NAME = "aml_db"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# CNA Analysis thresholds
HIGH_RISK_THRESHOLD = 70
MEDIUM_RISK_THRESHOLD = 40

# ============================================================
# CNA ANALYSIS PROMPT
# ============================================================

CNA_PROMPT = """You are a Customer Narrative Analyzer (CNA) for anti-money laundering.

CUSTOMER PROFILE:
{profile}

CUSTOMER'S NORMAL BEHAVIOR:
- Average transaction: {avg_amount}
- Typical frequency: {frequency} per month
- Expected range: {expected_range}
- Account purpose: {account_purpose}

NEW TRANSACTION TO ANALYZE:
- Amount: {txn_amount}
- Payment method: {payment_method}
- Recipient bank: {to_bank}
- Timestamp: {timestamp}

QUESTION: Does this transaction fit the customer's narrative?

Analyze whether this transaction is coherent with the established customer profile.
Consider:
1. Is the amount consistent with their typical behavior?
2. Does the payment method match their usual patterns?
3. Does the recipient make sense for their stated business/purpose?
4. Are there any red flags that break the narrative?

Output JSON only:
{{
    "fits_narrative": true/false,
    "risk_score": 0-100,
    "reasoning": "one sentence explanation",
    "red_flags": ["list of concerns if any"],
    "questions_for_customer": ["what would you ask to resolve concerns"]
}}
"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_mongo_client():
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=30000,
        tlsCAFile=certifi.where()
    )

def get_openai_client():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=OPENAI_API_KEY)

def analyze_transaction_with_cna(openai_client, profile: dict, transaction: dict) -> dict:
    """Use LLM to analyze if transaction fits the customer narrative."""

    # Extract transaction details
    amt = transaction.get("amount", {})
    if isinstance(amt, dict):
        txn_amount = amt.get("sent", 0)
        currency = amt.get("currency_sent", "USD")
    else:
        txn_amount = amt
        currency = "USD"

    receiver = transaction.get("receiver", {})
    to_bank = receiver.get("bank_id", "Unknown") if isinstance(receiver, dict) else "Unknown"

    # Build prompt
    stats = profile.get("_behavioral_stats", {})
    prompt = CNA_PROMPT.format(
        profile=json.dumps({
            "customer_type": profile.get("customer_type"),
            "industry": profile.get("likely_occupation_or_industry"),
            "narrative": profile.get("narrative_summary")
        }, indent=2),
        avg_amount=f"{stats.get('avg_amount', 0):,.2f}",
        frequency=stats.get("frequency", "unknown"),
        expected_range=profile.get("expected_transaction_range", "unknown"),
        account_purpose=profile.get("account_purpose", "unknown"),
        txn_amount=f"{currency} {txn_amount:,.2f}",
        payment_method=transaction.get("payment_format", "Unknown"),
        to_bank=to_bank,
        timestamp=str(transaction.get("timestamp", "Unknown"))
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a CNA system. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=300
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    return json.loads(content)

# ============================================================
# SIMULATOR
# ============================================================

def run_simulation(db, openai_client, limit_accounts: int = 10, limit_txns_per_account: int = 20):
    """Run the CNA simulation on accounts with profiles."""

    print("\n" + "="*70)
    print("CNA DAY-BY-DAY SIMULATOR")
    print("="*70)

    # Get accounts with profiles that have laundering
    accounts_with_laundering = list(db.accounts.find({
        "profile_generated": True,
        "profile._has_laundering": True
    }).limit(limit_accounts))

    print(f"\nTesting {len(accounts_with_laundering)} accounts with laundering activity")

    # Statistics
    stats = {
        "total_txns_analyzed": 0,
        "true_positives": 0,      # Correctly flagged laundering
        "false_positives": 0,     # Incorrectly flagged clean txn
        "true_negatives": 0,      # Correctly passed clean txn
        "false_negatives": 0,     # Missed laundering
        "details": []
    }

    for account in accounts_with_laundering:
        account_id = account["account_id"]
        profile = account["profile"]

        print(f"\n{'─'*70}")
        print(f"Account: {account_id}")
        print(f"Profile: {profile.get('customer_type')} - {profile.get('likely_occupation_or_industry')}")
        print(f"Narrative: {profile.get('narrative_summary', 'N/A')[:80]}...")
        print(f"{'─'*70}")

        # Get transactions for this account (chronologically)
        transactions = list(db.transactions.find({
            "sender.account_id": account_id
        }).sort("timestamp", 1).limit(limit_txns_per_account))

        for txn in transactions:
            is_laundering = txn.get("is_laundering", False)

            # Analyze with CNA
            try:
                analysis = analyze_transaction_with_cna(openai_client, profile, txn)
                risk_score = analysis.get("risk_score", 0)
                fits_narrative = analysis.get("fits_narrative", True)

                # Determine if flagged
                flagged = risk_score >= MEDIUM_RISK_THRESHOLD or not fits_narrative

                # Extract amount for display
                amt = txn.get("amount", {})
                txn_amount = amt.get("sent", 0) if isinstance(amt, dict) else 0

                # Update statistics
                stats["total_txns_analyzed"] += 1

                if flagged and is_laundering:
                    stats["true_positives"] += 1
                    result = "✅ TRUE POSITIVE"
                elif flagged and not is_laundering:
                    stats["false_positives"] += 1
                    result = "⚠️  FALSE POSITIVE"
                elif not flagged and not is_laundering:
                    stats["true_negatives"] += 1
                    result = "✓  True Negative"
                else:  # not flagged and is_laundering
                    stats["false_negatives"] += 1
                    result = "❌ FALSE NEGATIVE"

                # Print result
                launder_marker = " [LAUNDER]" if is_laundering else ""
                print(f"\n  ${txn_amount:>12,.2f}{launder_marker}")
                print(f"  Risk Score: {risk_score}/100 | Fits Narrative: {fits_narrative}")
                print(f"  {result}: {analysis.get('reasoning', 'N/A')[:60]}...")

                if analysis.get("red_flags"):
                    print(f"  Red Flags: {', '.join(analysis['red_flags'][:2])}")

                # Store details for analysis
                stats["details"].append({
                    "account_id": account_id,
                    "amount": txn_amount,
                    "is_laundering": is_laundering,
                    "risk_score": risk_score,
                    "flagged": flagged,
                    "result": result,
                    "reasoning": analysis.get("reasoning")
                })

            except Exception as e:
                print(f"  Error analyzing transaction: {e}")
                continue

    # Print summary
    print("\n" + "="*70)
    print("SIMULATION RESULTS")
    print("="*70)

    total = stats["total_txns_analyzed"]
    tp = stats["true_positives"]
    fp = stats["false_positives"]
    tn = stats["true_negatives"]
    fn = stats["false_negatives"]

    print(f"\nTransactions Analyzed: {total}")
    print(f"\nConfusion Matrix:")
    print(f"  ┌────────────────┬──────────────┬──────────────┐")
    print(f"  │                │ Actual LAUND │ Actual CLEAN │")
    print(f"  ├────────────────┼──────────────┼──────────────┤")
    print(f"  │ Predicted FLAG │ TP: {tp:>6}   │ FP: {fp:>6}   │")
    print(f"  │ Predicted PASS │ FN: {fn:>6}   │ TN: {tn:>6}   │")
    print(f"  └────────────────┴──────────────┴──────────────┘")

    # Calculate metrics
    if tp + fp > 0:
        precision = tp / (tp + fp)
        print(f"\nPrecision (of flagged, how many were laundering): {precision:.1%}")

    if tp + fn > 0:
        recall = tp / (tp + fn)
        print(f"Recall (of laundering, how many were caught): {recall:.1%}")

    if tp + fp > 0 and tp + fn > 0:
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        print(f"F1 Score: {f1:.3f}")

    print("\n" + "="*70)

    return stats

# ============================================================
# ENTRY POINT
# ============================================================

def main():
    mongo_client = get_mongo_client()
    db = mongo_client[DATABASE_NAME]
    openai_client = get_openai_client()

    # Run simulation
    stats = run_simulation(
        db,
        openai_client,
        limit_accounts=5,        # Test 5 accounts with laundering
        limit_txns_per_account=15  # Up to 15 txns each
    )

    print("\nSimulation complete!")

if __name__ == "__main__":
    main()
