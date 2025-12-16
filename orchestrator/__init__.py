"""
Orchestrator - Transaction Pipeline

Routes transactions through the Three-Layer Tribunal:
1. Statistical Engine (fast gate) → 98% approved
2. Narrative Engine (context check) → Most approved
3. Expert Agent (final decision) → BLOCK/APPROVE/REVIEW
"""

from .pipeline import Pipeline

__all__ = ["Pipeline"]
