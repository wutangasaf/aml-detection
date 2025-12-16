"""
Configuration and Thresholds for AML Three-Layer Tribunal

All configuration values in one place for easy tuning.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

MONGODB_URI = os.environ.get(
    "MONGODB_URI",
    "mongodb+srv://dev_db_user:EyMpA37VXGa3Kjmc@aml-research.sgpnzv8.mongodb.net/?appName=AML-Research"
)
DATABASE_NAME = "aml_db"

# Collection names
COLLECTIONS = {
    "transactions": "transactions",
    "accounts": "accounts",
    "banks": "banks",
    "regulatory_docs": "regulatory_docs",
    "cluster_baselines": "cluster_baselines",
    "account_embeddings": "account_embeddings",
}


# =============================================================================
# API KEYS
# =============================================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

LLM_MODEL = "claude-sonnet-4-20250514"  # For Expert Agent reasoning


# =============================================================================
# TRIBUNAL THRESHOLDS
# =============================================================================

@dataclass
class TribunalThresholds:
    """Configurable thresholds for the Three-Layer Tribunal."""

    # Layer 1: Statistical Engine
    statistical_gate: float = 3.0  # Score above this triggers Layer 2

    # Layer 2: Narrative Engine
    narrative_gate: float = 0.7  # Coherence below this triggers Layer 3

    # Layer 3: Expert Agent
    expert_confidence_block: float = 0.8  # Min confidence to BLOCK
    expert_confidence_review: float = 0.5  # Min confidence for REVIEW

    # Performance targets
    target_layer1_filter_rate: float = 0.98  # 98% should pass Layer 1
    target_precision: float = 0.15  # Target >15% precision
    target_recall: float = 0.70  # Target >70% recall


THRESHOLDS = TribunalThresholds()


# =============================================================================
# CLUSTERING CONFIGURATION (Statistical Engine)
# =============================================================================

@dataclass
class ClusteringConfig:
    """Configuration for behavioral peer group clustering."""

    n_clusters: int = 50  # Number of peer groups
    algorithm: str = "kmeans"  # "kmeans" or "dbscan"

    # Features to use for clustering
    features: tuple = (
        "log_avg_amount",
        "transaction_frequency",
        "unique_counterparties",
        "payment_format_entropy",
        "hour_distribution_entropy",
    )

    # Z-score thresholds
    zscore_warning: float = 2.0
    zscore_alert: float = 3.0
    zscore_critical: float = 4.0


CLUSTERING_CONFIG = ClusteringConfig()


# =============================================================================
# NARRATIVE ENGINE CONFIGURATION
# =============================================================================

@dataclass
class NarrativeConfig:
    """Configuration for narrative coherence analysis."""

    history_window: int = 50  # Number of past transactions to consider
    embedding_dim: int = 256  # Dimension of transaction embeddings

    # Coherence thresholds
    coherence_high: float = 0.8  # Very consistent with history
    coherence_medium: float = 0.5  # Somewhat consistent
    coherence_low: float = 0.3  # Suspicious deviation


NARRATIVE_CONFIG = NarrativeConfig()


# =============================================================================
# TYPOLOGIES
# =============================================================================

TYPOLOGIES = {
    "smurfing": {
        "name": "Smurfing",
        "description": "Breaking large amounts into smaller deposits to avoid reporting thresholds",
        "statistical_signals": ["high_frequency", "low_amounts", "multiple_accounts"],
        "narrative_signals": ["many_new_counterparties", "rapid_succession"],
    },
    "structuring": {
        "name": "Structuring",
        "description": "Transactions just below reporting thresholds ($10K in US)",
        "statistical_signals": ["amounts_near_threshold", "repetitive_patterns"],
        "narrative_signals": ["inconsistent_with_profile", "round_numbers"],
    },
    "layering": {
        "name": "Layering",
        "description": "Complex series of transactions to obscure money trail",
        "statistical_signals": ["high_velocity", "in_equals_out"],
        "narrative_signals": ["circular_flows", "rapid_movement"],
    },
    "tbml": {
        "name": "Trade-Based Money Laundering",
        "description": "Using trade transactions to move value (over/under invoicing)",
        "statistical_signals": ["unusual_amounts_for_goods", "price_anomalies"],
        "narrative_signals": ["mismatched_counterparties", "unusual_trade_partners"],
    },
    "shell_company": {
        "name": "Shell Company Activity",
        "description": "Using shell companies as passthrough entities",
        "statistical_signals": ["in_approx_out", "no_retained_value"],
        "narrative_signals": ["no_business_activity", "opaque_ownership"],
    },
}


# =============================================================================
# CONFIG CLASS
# =============================================================================

@dataclass
class Config:
    """Master configuration object."""

    # Database
    mongodb_uri: str = MONGODB_URI
    database_name: str = DATABASE_NAME
    collections: Dict[str, str] = field(default_factory=lambda: COLLECTIONS)

    # API Keys
    openai_api_key: str = OPENAI_API_KEY
    anthropic_api_key: str = ANTHROPIC_API_KEY

    # Models
    embedding_model: str = EMBEDDING_MODEL
    embedding_dimensions: int = EMBEDDING_DIMENSIONS
    llm_model: str = LLM_MODEL

    # Thresholds
    thresholds: TribunalThresholds = field(default_factory=TribunalThresholds)

    # Engine configs
    clustering: ClusteringConfig = field(default_factory=ClusteringConfig)
    narrative: NarrativeConfig = field(default_factory=NarrativeConfig)

    # Typologies
    typologies: Dict[str, Any] = field(default_factory=lambda: TYPOLOGIES)


# Global config instance
config = Config()
