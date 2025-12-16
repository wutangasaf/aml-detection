"""
SAR (Suspicious Activity Report) Draft Generator

Generates draft SARs for transactions flagged by the Expert Agent.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from shared.models import (
    TribunalInput,
    SARDraft,
    RegulatoryReference,
    RiskFactor,
)
from engines.expert.typologies import TypologyMatch


def generate_sar_draft(
    input_data: TribunalInput,
    typology_match: Optional[TypologyMatch],
    risk_factors: List[RiskFactor],
    reasoning: str,
) -> SARDraft:
    """
    Generate a draft Suspicious Activity Report.

    Args:
        input_data: TribunalInput with transaction and account data
        typology_match: Detected typology (if any)
        risk_factors: List of identified risk factors
        reasoning: LLM-generated reasoning

    Returns:
        SARDraft object ready for compliance review
    """
    tx = input_data.transaction
    stats = input_data.account_history.stats

    # Determine activity type
    activity_type = typology_match.name if typology_match else "Unusual Activity"

    # Build red flags list
    red_flags = []
    for factor in risk_factors:
        red_flags.append(f"{factor.factor}: {factor.description}")

    if typology_match:
        red_flags.extend([f"Signal: {s}" for s in typology_match.signals_matched])

    # Build regulatory references
    references = _get_regulatory_references(activity_type)

    # Generate summary
    summary = _generate_summary(input_data, typology_match, risk_factors)

    # Generate detailed description
    detailed_description = _generate_detailed_description(
        input_data, typology_match, risk_factors, reasoning
    )

    # Determine recommended action
    if typology_match and typology_match.confidence > 0.7:
        recommended_action = "file_sar"
    elif any(f.severity == "critical" for f in risk_factors):
        recommended_action = "file_sar"
    elif len(risk_factors) >= 3:
        recommended_action = "escalate_to_compliance"
    else:
        recommended_action = "enhanced_monitoring"

    return SARDraft(
        subject_account=input_data.account_history.account_id,
        subject_name=None,  # No PII in this dataset
        filing_institution="Handle-AI",
        activity_type=activity_type,
        activity_date_range=(
            stats.first_transaction,
            tx.timestamp,
        ),
        total_amount_involved=stats.total_sent + tx.amount_sent,
        summary=summary,
        detailed_description=detailed_description,
        transaction_ids=[tx.txn_id] if tx.txn_id else [],
        red_flags=red_flags,
        regulatory_references=references,
        recommended_action=recommended_action,
    )


def _get_regulatory_references(activity_type: str) -> List[RegulatoryReference]:
    """Get relevant regulatory references for the activity type."""
    references = []

    # Common references
    references.append(RegulatoryReference(
        source="FATF",
        reference="Recommendation 20",
        relevance="Reporting of suspicious transactions",
    ))

    # Type-specific references
    if activity_type == "Structuring":
        references.extend([
            RegulatoryReference(
                source="FinCEN",
                reference="31 CFR 1010.314",
                relevance="Structuring transactions to evade reporting requirements",
            ),
            RegulatoryReference(
                source="FATF",
                reference="Recommendation 10",
                relevance="Customer due diligence for suspicious patterns",
            ),
        ])

    elif activity_type == "Smurfing":
        references.extend([
            RegulatoryReference(
                source="FATF",
                reference="Recommendation 10",
                relevance="Customer due diligence and ongoing monitoring",
            ),
            RegulatoryReference(
                source="EU AMLD6",
                reference="Article 3(4)(f)",
                relevance="Money laundering through multiple transactions",
            ),
        ])

    elif activity_type == "Layering":
        references.extend([
            RegulatoryReference(
                source="FATF",
                reference="Recommendation 16",
                relevance="Wire transfers and beneficiary information",
            ),
            RegulatoryReference(
                source="EU AMLR",
                reference="Article 50",
                relevance="Enhanced monitoring for complex transactions",
            ),
        ])

    elif "Trade" in activity_type:
        references.extend([
            RegulatoryReference(
                source="FATF",
                reference="Trade-Based Money Laundering Typologies Report",
                relevance="Red flags and detection methods for TBML",
            ),
            RegulatoryReference(
                source="Wolfsberg",
                reference="Trade Finance Principles",
                relevance="Due diligence for trade transactions",
            ),
        ])

    elif "Shell" in activity_type:
        references.extend([
            RegulatoryReference(
                source="FATF",
                reference="Recommendation 24",
                relevance="Transparency of beneficial ownership",
            ),
            RegulatoryReference(
                source="EU AMLD5",
                reference="Article 30",
                relevance="Beneficial ownership registers",
            ),
        ])

    return references


def _generate_summary(
    input_data: TribunalInput,
    typology_match: Optional[TypologyMatch],
    risk_factors: List[RiskFactor],
) -> str:
    """Generate a brief summary for the SAR."""
    tx = input_data.transaction
    stats = input_data.account_history.stats

    typology_text = typology_match.name if typology_match else "suspicious activity"

    summary = (
        f"Account {input_data.account_history.account_id} has been flagged for potential "
        f"{typology_text}. "
        f"A transaction of ${tx.amount_sent:,.2f} via {tx.payment_format} on "
        f"{tx.timestamp.strftime('%Y-%m-%d')} triggered automated detection systems. "
        f"The account has processed {stats.total_transactions} transactions totaling "
        f"${stats.total_sent:,.2f} sent and ${stats.total_received:,.2f} received. "
        f"Statistical analysis indicates a {input_data.statistical_score:.1f}/10 anomaly score, "
        f"and narrative coherence analysis shows {input_data.narrative_score:.0%} consistency "
        f"with historical behavior."
    )

    if risk_factors:
        summary += f" {len(risk_factors)} risk factors were identified."

    return summary


def _generate_detailed_description(
    input_data: TribunalInput,
    typology_match: Optional[TypologyMatch],
    risk_factors: List[RiskFactor],
    reasoning: str,
) -> str:
    """Generate detailed description for the SAR."""
    tx = input_data.transaction
    stats = input_data.account_history.stats

    sections = []

    # Transaction details
    sections.append(
        "TRANSACTION DETAILS:\n"
        f"- Transaction ID: {tx.txn_id or 'N/A'}\n"
        f"- Date/Time: {tx.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"- Amount Sent: ${tx.amount_sent:,.2f} {tx.amount.currency_sent}\n"
        f"- Amount Received: ${tx.amount.received:,.2f} {tx.amount.currency_received}\n"
        f"- Payment Method: {tx.payment_format}\n"
        f"- Sender: Account {tx.sender.account_id} at Bank {tx.sender.bank_id}\n"
        f"- Receiver: Account {tx.receiver.account_id} at Bank {tx.receiver.bank_id}"
    )

    # Account history
    sections.append(
        "ACCOUNT HISTORY:\n"
        f"- Total Transactions: {stats.total_transactions}\n"
        f"- Total Sent: ${stats.total_sent:,.2f}\n"
        f"- Total Received: ${stats.total_received:,.2f}\n"
        f"- Average Transaction: ${stats.avg_transaction_amount:,.2f}\n"
        f"- Unique Counterparties: {stats.unique_counterparties}\n"
        f"- Transaction Frequency: {stats.transaction_frequency_per_day:.2f}/day\n"
        f"- Account Active Since: {stats.first_transaction.strftime('%Y-%m-%d')}"
    )

    # Detection scores
    sections.append(
        "DETECTION ANALYSIS:\n"
        f"- Statistical Anomaly Score: {input_data.statistical_score:.2f}/10.0\n"
        f"- Narrative Coherence Score: {input_data.narrative_score:.2%}\n"
        f"- Triggered By: {input_data.triggered_by.title()} Engine"
    )

    # Typology analysis
    if typology_match:
        sections.append(
            f"TYPOLOGY ANALYSIS:\n"
            f"- Detected Pattern: {typology_match.name}\n"
            f"- Confidence: {typology_match.confidence:.0%}\n"
            f"- Description: {typology_match.description}\n"
            f"- Signals Matched:\n"
            + "\n".join(f"  * {s}" for s in typology_match.signals_matched)
        )

    # Risk factors
    if risk_factors:
        risk_text = "RISK FACTORS:\n"
        for i, factor in enumerate(risk_factors, 1):
            risk_text += (
                f"{i}. {factor.factor} [{factor.severity.upper()}]\n"
                f"   {factor.description}\n"
            )
            if factor.evidence:
                risk_text += "   Evidence: " + ", ".join(factor.evidence) + "\n"
        sections.append(risk_text)

    # AI reasoning
    sections.append(
        "AI ANALYSIS:\n" + reasoning
    )

    return "\n\n".join(sections)
