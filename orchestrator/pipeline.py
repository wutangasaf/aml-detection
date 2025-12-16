"""
Orchestrator Pipeline - Transaction Routing

Routes transactions through the Three-Layer Tribunal:
1. Statistical Engine (fast gate) → 98% approved
2. Narrative Engine (context check) → Most approved
3. Expert Agent (final decision) → BLOCK/APPROVE/REVIEW

TODO: Implement in Phase D
"""

from typing import Optional
from dataclasses import dataclass
import time

from shared.config import THRESHOLDS
from shared.models import (
    Transaction,
    AccountHistory,
    TribunalInput,
    TribunalVerdict,
    PipelineResult,
    LayerResult,
)
from engines.statistical.engine import StatisticalEngine
from engines.narrative.engine import NarrativeEngine
from engines.expert.agent import ExpertAgent


class Pipeline:
    """
    Three-Layer Tribunal Pipeline.

    Orchestrates the flow of transactions through all three layers,
    with early exit for transactions that pass statistical and narrative checks.
    """

    def __init__(self):
        self.statistical = StatisticalEngine()
        self.narrative = NarrativeEngine()
        self.expert = ExpertAgent()

    def process(self, transaction: Transaction, history: AccountHistory) -> PipelineResult:
        """
        Process a transaction through the tribunal pipeline.

        Args:
            transaction: The transaction to analyze
            history: Account history for context

        Returns:
            PipelineResult with decision and all layer results
        """
        start_time = time.time()
        layers_invoked = []

        # Layer 1: Statistical Engine
        layers_invoked.append("statistical")
        stat_start = time.time()
        stat_result = self.statistical.analyze(transaction, history)
        stat_time = (time.time() - stat_start) * 1000

        layer1_result = LayerResult(
            layer="statistical",
            score=stat_result.score,
            passed=stat_result.passed,
            processing_time_ms=stat_time,
            details=stat_result.details,
        )

        # Early exit if passes statistical check
        if stat_result.passed:
            return PipelineResult(
                transaction_id=transaction.txn_id,
                statistical_result=layer1_result,
                narrative_result=None,
                expert_result=None,
                final_decision="APPROVE",
                final_confidence=1.0 - (stat_result.score / 10.0),
                total_processing_time_ms=(time.time() - start_time) * 1000,
                layers_invoked=layers_invoked,
            )

        # Layer 2: Narrative Engine
        layers_invoked.append("narrative")
        narr_start = time.time()
        narr_result = self.narrative.analyze(transaction, history)
        narr_time = (time.time() - narr_start) * 1000

        layer2_result = LayerResult(
            layer="narrative",
            score=narr_result.score,
            passed=narr_result.passed,
            processing_time_ms=narr_time,
            details=narr_result.details,
        )

        # Early exit if passes narrative check
        if narr_result.passed:
            return PipelineResult(
                transaction_id=transaction.txn_id,
                statistical_result=layer1_result,
                narrative_result=layer2_result,
                expert_result=None,
                final_decision="APPROVE",
                final_confidence=narr_result.score,
                total_processing_time_ms=(time.time() - start_time) * 1000,
                layers_invoked=layers_invoked,
            )

        # Layer 3: Expert Agent
        layers_invoked.append("expert")

        # Determine trigger reason
        if not stat_result.passed and not narr_result.passed:
            triggered_by = "both"
        elif not stat_result.passed:
            triggered_by = "statistical"
        else:
            triggered_by = "narrative"

        tribunal_input = TribunalInput(
            transaction=transaction,
            statistical_score=stat_result.score,
            narrative_score=narr_result.score,
            account_history=history,
            triggered_by=triggered_by,
        )

        verdict = self.expert.analyze(tribunal_input)

        return PipelineResult(
            transaction_id=transaction.txn_id,
            statistical_result=layer1_result,
            narrative_result=layer2_result,
            expert_result=verdict,
            final_decision=verdict.decision,
            final_confidence=verdict.confidence,
            total_processing_time_ms=(time.time() - start_time) * 1000,
            layers_invoked=layers_invoked,
        )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def process_transaction(transaction: Transaction, history: AccountHistory) -> PipelineResult:
    """Process a single transaction through the tribunal."""
    pipeline = Pipeline()
    return pipeline.process(transaction, history)
