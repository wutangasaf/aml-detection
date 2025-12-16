"""
Expert Agent - Layer 3: The "Judge"

Final decision maker with regulatory compliance checking.
Uses RAG over regulatory knowledge base + LLM reasoning.
Target latency: ~2-3 seconds (async, only triggered when needed)
Output: TribunalVerdict with decision, confidence, typology, SAR draft
"""

from .agent import ExpertAgent

__all__ = ["ExpertAgent"]
