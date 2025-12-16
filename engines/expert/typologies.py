"""
Typology Detection for Expert Agent

Detects money laundering typologies based on statistical and narrative signals.
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass

from shared.config import TYPOLOGIES
from shared.models import TribunalInput, RiskFactor


@dataclass
class TypologyMatch:
    """A detected typology with confidence score."""
    name: str
    confidence: float
    signals_matched: List[str]
    description: str


def detect_structuring(input_data: TribunalInput) -> Optional[TypologyMatch]:
    """
    Detect Structuring typology.

    Structuring: Transactions just below reporting thresholds ($10K in US)
    to avoid Currency Transaction Reports (CTRs).
    """
    signals = []
    confidence = 0.0

    amount = input_data.transaction.amount_sent

    # Check if amount is just below $10K threshold
    if 9000 <= amount < 10000:
        signals.append("amount_near_10k_threshold")
        confidence += 0.4

    # Check if amount is just below $3K threshold (some jurisdictions)
    if 2700 <= amount < 3000:
        signals.append("amount_near_3k_threshold")
        confidence += 0.3

    # High statistical anomaly suggests unusual pattern
    if input_data.statistical_score > 5.0:
        signals.append("high_statistical_anomaly")
        confidence += 0.2

    # Low narrative coherence suggests breaking from normal behavior
    if input_data.narrative_score < 0.4:
        signals.append("low_narrative_coherence")
        confidence += 0.2

    # Check for round numbers (common in structuring)
    if amount % 100 == 0 and amount > 1000:
        signals.append("round_number_amount")
        confidence += 0.1

    # Check transaction frequency
    if input_data.account_history.stats.transaction_frequency_per_day > 3:
        signals.append("high_transaction_frequency")
        confidence += 0.15

    if confidence >= 0.4 and signals:
        return TypologyMatch(
            name="Structuring",
            confidence=min(confidence, 1.0),
            signals_matched=signals,
            description=TYPOLOGIES["structuring"]["description"],
        )
    return None


def detect_smurfing(input_data: TribunalInput) -> Optional[TypologyMatch]:
    """
    Detect Smurfing typology.

    Smurfing: Breaking large amounts into many smaller deposits,
    often using multiple accounts or individuals.
    """
    signals = []
    confidence = 0.0

    amount = input_data.transaction.amount_sent
    stats = input_data.account_history.stats

    # Small amounts with high frequency
    if amount < 5000 and stats.transaction_frequency_per_day > 2:
        signals.append("small_amount_high_frequency")
        confidence += 0.35

    # Many unique counterparties
    if stats.unique_counterparties > 20:
        signals.append("many_counterparties")
        confidence += 0.25

    # High statistical anomaly
    if input_data.statistical_score > 4.0:
        signals.append("statistical_anomaly")
        confidence += 0.15

    # Low narrative coherence
    if input_data.narrative_score < 0.5:
        signals.append("narrative_break")
        confidence += 0.15

    # Check if sent ≈ received (passthrough)
    if stats.total_sent > 0 and stats.total_received > 0:
        ratio = stats.total_sent / stats.total_received
        if 0.8 <= ratio <= 1.2:
            signals.append("balanced_in_out")
            confidence += 0.1

    if confidence >= 0.4 and signals:
        return TypologyMatch(
            name="Smurfing",
            confidence=min(confidence, 1.0),
            signals_matched=signals,
            description=TYPOLOGIES["smurfing"]["description"],
        )
    return None


def detect_layering(input_data: TribunalInput) -> Optional[TypologyMatch]:
    """
    Detect Layering typology.

    Layering: Rapid movement of funds through multiple accounts
    to obscure the audit trail.
    """
    signals = []
    confidence = 0.0

    stats = input_data.account_history.stats

    # Very high transaction frequency
    if stats.transaction_frequency_per_day > 5:
        signals.append("very_high_frequency")
        confidence += 0.3

    # Many transactions in short time
    if stats.total_transactions > 100:
        signals.append("high_transaction_count")
        confidence += 0.2

    # In ≈ Out (passthrough behavior)
    if stats.total_sent > 0 and stats.total_received > 0:
        ratio = stats.total_sent / stats.total_received
        if 0.9 <= ratio <= 1.1:
            signals.append("in_equals_out")
            confidence += 0.25

    # High statistical anomaly
    if input_data.statistical_score > 6.0:
        signals.append("high_statistical_anomaly")
        confidence += 0.15

    # Very low narrative coherence
    if input_data.narrative_score < 0.3:
        signals.append("very_low_coherence")
        confidence += 0.2

    if confidence >= 0.5 and signals:
        return TypologyMatch(
            name="Layering",
            confidence=min(confidence, 1.0),
            signals_matched=signals,
            description=TYPOLOGIES["layering"]["description"],
        )
    return None


def detect_shell_company(input_data: TribunalInput) -> Optional[TypologyMatch]:
    """
    Detect Shell Company typology.

    Shell Company: Using entities with no real business activity
    as passthrough vehicles.
    """
    signals = []
    confidence = 0.0

    stats = input_data.account_history.stats

    # In ≈ Out (no value retention)
    if stats.total_sent > 0 and stats.total_received > 0:
        ratio = stats.total_sent / stats.total_received
        if 0.95 <= ratio <= 1.05:
            signals.append("exact_passthrough")
            confidence += 0.35

    # Low counterparty diversity (few trading partners)
    if stats.unique_counterparties < 5 and stats.total_transactions > 20:
        signals.append("limited_counterparties")
        confidence += 0.2

    # High amounts, low frequency (typical shell pattern)
    if stats.avg_transaction_amount > 50000 and stats.transaction_frequency_per_day < 1:
        signals.append("high_value_low_frequency")
        confidence += 0.25

    # Statistical anomaly
    if input_data.statistical_score > 5.0:
        signals.append("statistical_anomaly")
        confidence += 0.15

    if confidence >= 0.4 and signals:
        return TypologyMatch(
            name="Shell Company Activity",
            confidence=min(confidence, 1.0),
            signals_matched=signals,
            description=TYPOLOGIES["shell_company"]["description"],
        )
    return None


def detect_tbml(input_data: TribunalInput) -> Optional[TypologyMatch]:
    """
    Detect Trade-Based Money Laundering (TBML) typology.

    TBML: Using trade transactions to move value through
    over/under invoicing or phantom shipments.
    """
    signals = []
    confidence = 0.0

    amount = input_data.transaction.amount_sent
    stats = input_data.account_history.stats

    # Very high amounts (trade transactions tend to be large)
    if amount > 100000:
        signals.append("high_value_transaction")
        confidence += 0.2

    # High variance in amounts (price manipulation)
    if stats.std_transaction_amount > stats.avg_transaction_amount:
        signals.append("high_amount_variance")
        confidence += 0.25

    # Specific payment format (Wire transfers common in trade)
    if input_data.transaction.payment_format == "Wire":
        signals.append("wire_transfer")
        confidence += 0.1

    # High statistical anomaly (unusual pricing)
    if input_data.statistical_score > 7.0:
        signals.append("extreme_statistical_anomaly")
        confidence += 0.25

    # Low narrative coherence (breaks from normal trade)
    if input_data.narrative_score < 0.4:
        signals.append("narrative_break")
        confidence += 0.2

    if confidence >= 0.5 and signals:
        return TypologyMatch(
            name="Trade-Based Money Laundering",
            confidence=min(confidence, 1.0),
            signals_matched=signals,
            description=TYPOLOGIES["tbml"]["description"],
        )
    return None


def detect_all_typologies(input_data: TribunalInput) -> List[TypologyMatch]:
    """
    Run all typology detectors and return matches sorted by confidence.

    Args:
        input_data: TribunalInput with transaction and scores

    Returns:
        List of detected typologies, sorted by confidence (highest first)
    """
    detectors = [
        detect_structuring,
        detect_smurfing,
        detect_layering,
        detect_shell_company,
        detect_tbml,
    ]

    matches = []
    for detector in detectors:
        match = detector(input_data)
        if match:
            matches.append(match)

    # Sort by confidence, highest first
    matches.sort(key=lambda m: m.confidence, reverse=True)

    return matches


def get_risk_factors(input_data: TribunalInput, typology_match: Optional[TypologyMatch]) -> List[RiskFactor]:
    """
    Generate risk factors based on input data and detected typology.

    Args:
        input_data: TribunalInput
        typology_match: Detected typology (if any)

    Returns:
        List of RiskFactor objects
    """
    factors = []

    # Statistical anomaly risk
    if input_data.statistical_score > 7.0:
        factors.append(RiskFactor(
            factor="Extreme Statistical Anomaly",
            severity="critical",
            description=f"Transaction has statistical anomaly score of {input_data.statistical_score:.1f} (threshold: 3.0)",
            evidence=[f"Z-score: {input_data.statistical_score:.2f}"],
        ))
    elif input_data.statistical_score > 5.0:
        factors.append(RiskFactor(
            factor="High Statistical Anomaly",
            severity="high",
            description=f"Transaction deviates significantly from peer group baseline",
            evidence=[f"Z-score: {input_data.statistical_score:.2f}"],
        ))

    # Narrative coherence risk
    if input_data.narrative_score < 0.3:
        factors.append(RiskFactor(
            factor="Severe Narrative Break",
            severity="critical",
            description="Transaction is highly inconsistent with customer's behavioral history",
            evidence=[f"Coherence score: {input_data.narrative_score:.2f}"],
        ))
    elif input_data.narrative_score < 0.5:
        factors.append(RiskFactor(
            factor="Narrative Inconsistency",
            severity="high",
            description="Transaction does not fit customer's typical pattern",
            evidence=[f"Coherence score: {input_data.narrative_score:.2f}"],
        ))

    # Typology-specific risks
    if typology_match:
        severity = "critical" if typology_match.confidence > 0.7 else "high"
        factors.append(RiskFactor(
            factor=f"{typology_match.name} Pattern Detected",
            severity=severity,
            description=typology_match.description,
            evidence=typology_match.signals_matched,
        ))

    # Amount-based risks
    amount = input_data.transaction.amount_sent
    if 9000 <= amount < 10000:
        factors.append(RiskFactor(
            factor="Near-Threshold Amount",
            severity="medium",
            description="Transaction amount is just below $10,000 reporting threshold",
            evidence=[f"Amount: ${amount:,.2f}"],
        ))

    return factors
