"""
Narrative Engine - Layer 2: The "Context Layer"

Performs semantic anomaly detection - checks if transaction fits user's behavioral story.
Target latency: <200ms
Output: narrative_coherence_score (0.0 - 1.0)
"""

from .engine import NarrativeEngine

__all__ = ["NarrativeEngine"]
