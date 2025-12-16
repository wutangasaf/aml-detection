"""
Statistical Engine - Layer 1: The "Fast Gate"

Performs anomaly detection based on numerical deviation.
Target latency: <10ms
Output: statistical_anomaly_score (0.0 - 10.0)
"""

from .engine import StatisticalEngine

__all__ = ["StatisticalEngine"]
