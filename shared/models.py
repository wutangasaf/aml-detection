"""
Pydantic Data Models for AML Three-Layer Tribunal

Defines the core data structures used across all engines.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# =============================================================================
# TRANSACTION MODELS
# =============================================================================

class TransactionParty(BaseModel):
    """Sender or receiver in a transaction."""
    account_id: str
    bank_id: str


class TransactionAmount(BaseModel):
    """Amount details for a transaction."""
    sent: float
    received: float
    currency_sent: str = "US Dollar"
    currency_received: str = "US Dollar"


class Transaction(BaseModel):
    """A single financial transaction."""
    txn_id: Optional[str] = None
    sender: TransactionParty
    receiver: TransactionParty
    amount: TransactionAmount
    payment_format: str  # "Wire", "Cheque", "ACH", "Reinvestment", "Credit Card"
    timestamp: datetime
    is_laundering: Optional[bool] = None  # Ground truth label (if available)

    @property
    def amount_sent(self) -> float:
        """Convenience property for sent amount."""
        return self.amount.sent


# =============================================================================
# ACCOUNT HISTORY MODELS
# =============================================================================

class AccountStats(BaseModel):
    """Statistical summary of an account's transaction history."""
    total_transactions: int
    total_sent: float
    total_received: float
    avg_transaction_amount: float
    std_transaction_amount: float
    unique_counterparties: int
    payment_format_distribution: Dict[str, float]
    hour_distribution: Dict[int, float]
    first_transaction: datetime
    last_transaction: datetime
    transaction_frequency_per_day: float


class AccountHistory(BaseModel):
    """Complete history context for an account."""
    account_id: str
    bank_id: str
    stats: AccountStats
    recent_transactions: List[Transaction] = Field(default_factory=list, max_length=50)
    cluster_id: Optional[int] = None  # Behavioral peer group
    profile_narrative: Optional[str] = None  # LLM-generated profile


# =============================================================================
# TRIBUNAL INPUT/OUTPUT MODELS
# =============================================================================

class TribunalInput(BaseModel):
    """
    Input to the Expert Agent (Layer 3).

    Contains the transaction under review plus scores from Layer 1 and Layer 2.
    """
    transaction: Transaction
    statistical_score: float = Field(ge=0.0, le=10.0, description="Anomaly score from Statistical Engine")
    narrative_score: float = Field(ge=0.0, le=1.0, description="Coherence score from Narrative Engine")
    account_history: AccountHistory
    triggered_by: Literal["statistical", "narrative", "both"]

    # Optional: Additional context
    counterparty_history: Optional[AccountHistory] = None
    related_transactions: List[Transaction] = Field(default_factory=list)


class RiskFactor(BaseModel):
    """A single risk factor identified by the Expert Agent."""
    factor: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    evidence: List[str] = Field(default_factory=list)


class RegulatoryReference(BaseModel):
    """Reference to a regulatory document or requirement."""
    source: str  # "FATF", "EU AMLD6", "FinCEN", etc.
    reference: str  # "Recommendation 20", "Article 3(4)", etc.
    relevance: str  # Why this reference applies


class SARDraft(BaseModel):
    """
    Draft Suspicious Activity Report.

    Structure follows standard SAR format for regulatory filing.
    """
    subject_account: str
    subject_name: Optional[str] = None
    filing_institution: str = "Handle-AI"

    # Suspicious activity details
    activity_type: str  # "Structuring", "Smurfing", etc.
    activity_date_range: tuple[datetime, datetime]
    total_amount_involved: float

    # Narrative sections
    summary: str  # Brief summary (1-2 paragraphs)
    detailed_description: str  # Full narrative of suspicious activity

    # Supporting information
    transaction_ids: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    regulatory_references: List[RegulatoryReference] = Field(default_factory=list)

    # Recommendation
    recommended_action: Literal["file_sar", "enhanced_monitoring", "escalate_to_compliance"]


class TribunalVerdict(BaseModel):
    """
    Output from the Expert Agent (Layer 3).

    Contains the final decision plus supporting evidence and optional SAR draft.
    """
    # Core decision
    decision: Literal["BLOCK", "APPROVE", "REVIEW"]
    confidence: float = Field(ge=0.0, le=1.0)

    # Typology detection
    typology: Optional[str] = None  # "Smurfing", "Structuring", etc.
    typology_confidence: Optional[float] = None

    # Risk assessment
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    risk_score: float = Field(ge=0.0, le=10.0, default=0.0)

    # Regulatory compliance
    citations: List[RegulatoryReference] = Field(default_factory=list)

    # SAR draft (only if decision is BLOCK or REVIEW)
    sar_draft: Optional[SARDraft] = None

    # Reasoning
    reasoning: str  # Explanation of the decision

    # Metadata
    processing_time_ms: Optional[float] = None
    model_used: Optional[str] = None


# =============================================================================
# PIPELINE RESULT MODELS
# =============================================================================

class LayerResult(BaseModel):
    """Result from a single layer of the tribunal."""
    layer: Literal["statistical", "narrative", "expert"]
    score: float
    passed: bool  # True if transaction passed this layer (not flagged)
    processing_time_ms: float
    details: Dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    """
    Complete result from the Three-Layer Tribunal pipeline.

    Tracks which layers were invoked and their individual results.
    """
    transaction_id: Optional[str] = None

    # Layer results
    statistical_result: LayerResult
    narrative_result: Optional[LayerResult] = None  # Only if Layer 1 flagged
    expert_result: Optional[TribunalVerdict] = None  # Only if Layer 2 flagged

    # Final decision
    final_decision: Literal["APPROVE", "BLOCK", "REVIEW"]
    final_confidence: float

    # Performance metrics
    total_processing_time_ms: float
    layers_invoked: List[str]


# =============================================================================
# EVALUATION MODELS
# =============================================================================

class EvaluationMetrics(BaseModel):
    """Metrics for evaluating tribunal performance."""
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP)"""
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN)"""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0

    @property
    def f1_score(self) -> float:
        """F1 = 2 * (precision * recall) / (precision + recall)"""
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        """Accuracy = (TP + TN) / total"""
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        return (self.true_positives + self.true_negatives) / total if total > 0 else 0.0
