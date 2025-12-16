"""
Test Suite for Expert Agent (Layer 3)

Tests the Expert Agent with mocked inputs to verify:
1. Typology detection
2. Decision making
3. SAR generation
"""

import pytest
from datetime import datetime, timedelta

from shared.models import (
    Transaction,
    TransactionParty,
    TransactionAmount,
    AccountStats,
    AccountHistory,
    TribunalInput,
)
from engines.expert.typologies import (
    detect_structuring,
    detect_smurfing,
    detect_layering,
    detect_all_typologies,
    get_risk_factors,
)


# =============================================================================
# FIXTURES - Mock Data Builders
# =============================================================================

def make_transaction(
    amount: float = 5000.0,
    payment_format: str = "Wire",
    sender_account: str = "TEST001",
    receiver_account: str = "TEST002",
    days_ago: int = 0,
) -> Transaction:
    """Create a mock transaction."""
    return Transaction(
        txn_id=f"TXN{datetime.now().timestamp()}",
        sender=TransactionParty(account_id=sender_account, bank_id="1"),
        receiver=TransactionParty(account_id=receiver_account, bank_id="2"),
        amount=TransactionAmount(
            sent=amount,
            received=amount,
            currency_sent="US Dollar",
            currency_received="US Dollar",
        ),
        payment_format=payment_format,
        timestamp=datetime.now() - timedelta(days=days_ago),
    )


def make_account_stats(
    total_transactions: int = 100,
    total_sent: float = 50000.0,
    total_received: float = 45000.0,
    avg_amount: float = 500.0,
    unique_counterparties: int = 10,
    frequency_per_day: float = 1.0,
) -> AccountStats:
    """Create mock account statistics."""
    return AccountStats(
        total_transactions=total_transactions,
        total_sent=total_sent,
        total_received=total_received,
        avg_transaction_amount=avg_amount,
        std_transaction_amount=avg_amount * 0.5,
        unique_counterparties=unique_counterparties,
        payment_format_distribution={"Wire": 0.5, "ACH": 0.3, "Cheque": 0.2},
        hour_distribution={h: 1/24 for h in range(24)},
        first_transaction=datetime.now() - timedelta(days=365),
        last_transaction=datetime.now(),
        transaction_frequency_per_day=frequency_per_day,
    )


def make_tribunal_input(
    amount: float = 5000.0,
    statistical_score: float = 5.0,
    narrative_score: float = 0.5,
    frequency_per_day: float = 1.0,
    unique_counterparties: int = 10,
    total_sent: float = 50000.0,
    total_received: float = 45000.0,
    triggered_by: str = "statistical",
) -> TribunalInput:
    """Create a complete TribunalInput for testing."""
    tx = make_transaction(amount=amount)
    stats = make_account_stats(
        frequency_per_day=frequency_per_day,
        unique_counterparties=unique_counterparties,
        total_sent=total_sent,
        total_received=total_received,
    )
    history = AccountHistory(
        account_id="TEST001",
        bank_id="1",
        stats=stats,
        recent_transactions=[],
    )
    return TribunalInput(
        transaction=tx,
        statistical_score=statistical_score,
        narrative_score=narrative_score,
        account_history=history,
        triggered_by=triggered_by,
    )


# =============================================================================
# TYPOLOGY DETECTION TESTS
# =============================================================================

class TestStructuringDetection:
    """Tests for Structuring typology detection."""

    def test_detects_near_threshold_amount(self):
        """Amount just below $10K should trigger structuring detection."""
        input_data = make_tribunal_input(
            amount=9500.0,
            statistical_score=6.0,
            narrative_score=0.3,
        )
        result = detect_structuring(input_data)

        assert result is not None
        assert result.name == "Structuring"
        assert "amount_near_10k_threshold" in result.signals_matched
        assert result.confidence >= 0.4

    def test_ignores_normal_amounts(self):
        """Normal amounts should not trigger structuring."""
        input_data = make_tribunal_input(
            amount=5000.0,
            statistical_score=2.0,
            narrative_score=0.8,
        )
        result = detect_structuring(input_data)

        assert result is None

    def test_round_number_adds_signal(self):
        """Round numbers near threshold increase confidence."""
        input_data = make_tribunal_input(
            amount=9500.0,  # Round number near threshold
            statistical_score=5.5,
            narrative_score=0.35,
        )
        result = detect_structuring(input_data)

        assert result is not None
        assert "round_number_amount" in result.signals_matched


class TestSmurfingDetection:
    """Tests for Smurfing typology detection."""

    def test_detects_high_frequency_small_amounts(self):
        """Many small transactions should trigger smurfing detection."""
        input_data = make_tribunal_input(
            amount=2000.0,
            statistical_score=5.0,
            narrative_score=0.4,
            frequency_per_day=5.0,
            unique_counterparties=25,
        )
        result = detect_smurfing(input_data)

        assert result is not None
        assert result.name == "Smurfing"
        assert "small_amount_high_frequency" in result.signals_matched
        assert "many_counterparties" in result.signals_matched

    def test_ignores_low_frequency(self):
        """Low frequency transactions should not trigger smurfing."""
        input_data = make_tribunal_input(
            amount=2000.0,
            statistical_score=2.0,
            narrative_score=0.8,
            frequency_per_day=0.5,
            unique_counterparties=5,
        )
        result = detect_smurfing(input_data)

        assert result is None


class TestLayeringDetection:
    """Tests for Layering typology detection."""

    def test_detects_passthrough_pattern(self):
        """In ≈ Out pattern should trigger layering detection."""
        input_data = make_tribunal_input(
            amount=10000.0,
            statistical_score=7.0,
            narrative_score=0.2,
            frequency_per_day=8.0,
            total_sent=100000.0,
            total_received=100000.0,  # In = Out
        )
        result = detect_layering(input_data)

        assert result is not None
        assert result.name == "Layering"
        assert "in_equals_out" in result.signals_matched
        assert "very_high_frequency" in result.signals_matched


class TestAllTypologiesDetection:
    """Tests for combined typology detection."""

    def test_returns_sorted_by_confidence(self):
        """Multiple typologies should be sorted by confidence."""
        # Input that could match multiple typologies
        input_data = make_tribunal_input(
            amount=9500.0,
            statistical_score=8.0,
            narrative_score=0.2,
            frequency_per_day=6.0,
            unique_counterparties=30,
            total_sent=100000.0,
            total_received=95000.0,
        )
        results = detect_all_typologies(input_data)

        assert len(results) >= 1
        # Results should be sorted by confidence, highest first
        for i in range(len(results) - 1):
            assert results[i].confidence >= results[i + 1].confidence

    def test_returns_empty_for_clean_transaction(self):
        """Clean transaction should return no typologies."""
        input_data = make_tribunal_input(
            amount=500.0,
            statistical_score=1.0,
            narrative_score=0.9,
            frequency_per_day=0.3,
            unique_counterparties=5,
        )
        results = detect_all_typologies(input_data)

        assert len(results) == 0


# =============================================================================
# RISK FACTOR TESTS
# =============================================================================

class TestRiskFactors:
    """Tests for risk factor generation."""

    def test_critical_statistical_anomaly(self):
        """Score > 7.0 should generate critical risk factor."""
        input_data = make_tribunal_input(statistical_score=8.5)
        factors = get_risk_factors(input_data, None)

        critical_factors = [f for f in factors if f.severity == "critical"]
        assert len(critical_factors) >= 1
        assert any("Statistical" in f.factor for f in critical_factors)

    def test_severe_narrative_break(self):
        """Narrative score < 0.3 should generate critical risk factor."""
        input_data = make_tribunal_input(narrative_score=0.2)
        factors = get_risk_factors(input_data, None)

        critical_factors = [f for f in factors if f.severity == "critical"]
        assert len(critical_factors) >= 1
        assert any("Narrative" in f.factor for f in critical_factors)

    def test_near_threshold_generates_medium_risk(self):
        """Amount near $10K threshold should generate medium risk."""
        input_data = make_tribunal_input(amount=9500.0)
        factors = get_risk_factors(input_data, None)

        threshold_factors = [f for f in factors if "Threshold" in f.factor]
        assert len(threshold_factors) >= 1
        assert threshold_factors[0].severity == "medium"


# =============================================================================
# MOCK EXPERT AGENT TESTS (without LLM calls)
# =============================================================================

class TestMockScenarios:
    """
    Test scenarios with mocked inputs.

    These tests verify the typology detection and risk assessment
    without making actual LLM calls.
    """

    def test_scenario_structuring(self):
        """
        Scenario: Multiple transactions just below $10K
        Expected: Detect Structuring with high confidence
        """
        input_data = make_tribunal_input(
            amount=9800.0,
            statistical_score=7.5,
            narrative_score=0.25,
            frequency_per_day=4.0,
        )

        typologies = detect_all_typologies(input_data)
        risk_factors = get_risk_factors(input_data, typologies[0] if typologies else None)

        assert len(typologies) >= 1
        assert typologies[0].name == "Structuring"
        assert typologies[0].confidence >= 0.6
        assert len(risk_factors) >= 2

    def test_scenario_smurfing(self):
        """
        Scenario: Many small deposits from many counterparties
        Expected: Detect Smurfing
        """
        input_data = make_tribunal_input(
            amount=1500.0,
            statistical_score=6.0,
            narrative_score=0.35,
            frequency_per_day=8.0,
            unique_counterparties=40,
        )

        typologies = detect_all_typologies(input_data)

        assert len(typologies) >= 1
        # Smurfing should be detected
        smurfing = [t for t in typologies if t.name == "Smurfing"]
        assert len(smurfing) >= 1
        assert smurfing[0].confidence >= 0.5

    def test_scenario_layering(self):
        """
        Scenario: Rapid in/out with balanced flows
        Expected: Detect Layering
        """
        input_data = make_tribunal_input(
            amount=25000.0,
            statistical_score=8.0,
            narrative_score=0.15,
            frequency_per_day=10.0,
            total_sent=500000.0,
            total_received=500000.0,
        )

        typologies = detect_all_typologies(input_data)

        assert len(typologies) >= 1
        layering = [t for t in typologies if t.name == "Layering"]
        assert len(layering) >= 1

    def test_scenario_clean_transaction(self):
        """
        Scenario: Normal transaction within expected patterns
        Expected: No typologies detected, minimal risk factors
        """
        input_data = make_tribunal_input(
            amount=750.0,
            statistical_score=1.5,
            narrative_score=0.85,
            frequency_per_day=0.5,
            unique_counterparties=8,
        )

        typologies = detect_all_typologies(input_data)
        risk_factors = get_risk_factors(input_data, None)

        assert len(typologies) == 0
        # Should have minimal or no critical/high risk factors
        severe_factors = [f for f in risk_factors if f.severity in ["critical", "high"]]
        assert len(severe_factors) == 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
