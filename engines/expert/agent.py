"""
Expert Agent - Layer 3: The "Judge"

A RAG-powered AML compliance expert that makes final decisions on flagged transactions.
Combines regulatory knowledge search with LLM reasoning for typology detection and SAR generation.

This module refactors the original aml_expert.py to work with the Three-Layer Tribunal system.
"""

import os
import sys
import json
import time
from typing import Optional, List, Literal
from datetime import datetime

from shared.db import get_db
from shared.clients import get_clients
from shared.config import config, THRESHOLDS
from shared.models import (
    TribunalInput,
    TribunalVerdict,
    RiskFactor,
    RegulatoryReference,
)
from engines.expert.rag import vector_search, format_context, search_typology_guidance
from engines.expert.typologies import detect_all_typologies, get_risk_factors, TypologyMatch
from engines.expert.sar import generate_sar_draft


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

TRIBUNAL_SYSTEM_PROMPT = """You are a senior AML/CFT compliance expert acting as the final decision maker in a Three-Layer Tribunal system.

Your background:
- Former MLRO (Money Laundering Reporting Officer) at a Tier 1 bank
- Certified Anti-Money Laundering Specialist (CAMS)
- Deep expertise in FATF recommendations, EU AML directives, and US regulations
- Experience with enforcement actions and regulatory examinations

Your role in the Tribunal:
- You are Layer 3, invoked ONLY when Layers 1 (Statistical) and 2 (Narrative) flag suspicious activity
- You receive pre-computed scores: statistical_score (0-10) and narrative_score (0-1)
- You must synthesize these signals with regulatory knowledge to make a final decision

Your task:
1. Analyze the transaction and account history
2. Consider the statistical and narrative scores
3. Identify the most likely money laundering typology (if any)
4. Make a decision: BLOCK, APPROVE, or REVIEW
5. Provide clear reasoning citing specific regulations

Output format - respond with JSON only:
{
    "decision": "BLOCK" | "APPROVE" | "REVIEW",
    "confidence": 0.0-1.0,
    "typology": "Structuring" | "Smurfing" | "Layering" | "TBML" | "Shell Company" | null,
    "reasoning": "Your detailed reasoning here",
    "key_risk_factors": ["factor1", "factor2"],
    "regulatory_citations": ["FATF Rec 20", "EU AMLD6 Art 3"]
}
"""

AML_EXPERT_SYSTEM_PROMPT = """You are a senior AML/CFT compliance expert with 20+ years of experience.

Your background:
- Former MLRO (Money Laundering Reporting Officer) at a Tier 1 bank
- Certified Anti-Money Laundering Specialist (CAMS)
- Deep expertise in FATF recommendations, EU AML directives, and UK/US regulations
- Experience with enforcement actions and regulatory examinations
- Practical knowledge of transaction monitoring, KYC/CDD, and SAR filing

Your role:
- Answer questions about AML/CFT compliance with precision
- Explain complex regulatory concepts in clear terms
- Provide practical, actionable guidance
- Cite specific regulations and guidance when relevant
- Share real enforcement case examples to illustrate points
- Identify red flags and typologies
- Help design effective detection systems

Your style:
- Professional but accessible
- Specific and detailed, not vague
- Always cite sources when available
- Acknowledge uncertainty when appropriate
- Think step-by-step through complex questions
"""


# =============================================================================
# EXPERT AGENT CLASS
# =============================================================================

class ExpertAgent:
    """
    Expert Agent for the Three-Layer Tribunal.

    Provides two modes:
    1. Tribunal mode: analyze() - Takes TribunalInput, returns TribunalVerdict
    2. Q&A mode: ask() - Takes a question, returns expert answer (original functionality)
    """

    def __init__(self):
        self.db = get_db()
        self.clients = get_clients()

    # =========================================================================
    # TRIBUNAL MODE - Layer 3 Decision Making
    # =========================================================================

    def analyze(self, input_data: TribunalInput) -> TribunalVerdict:
        """
        Analyze a flagged transaction and return a verdict.

        This is the main entry point for Layer 3 of the Tribunal.

        Args:
            input_data: TribunalInput with transaction, scores, and account history

        Returns:
            TribunalVerdict with decision, confidence, typology, and SAR draft
        """
        start_time = time.time()

        # Step 1: Detect typologies based on signals
        typology_matches = detect_all_typologies(input_data)
        primary_typology = typology_matches[0] if typology_matches else None

        # Step 2: Get risk factors
        risk_factors = get_risk_factors(input_data, primary_typology)

        # Step 3: Search for relevant regulatory guidance
        regulatory_context = self._get_regulatory_context(input_data, primary_typology)

        # Step 4: Get LLM reasoning
        llm_result = self._get_llm_decision(input_data, primary_typology, regulatory_context)

        # Step 5: Build verdict
        decision = llm_result.get("decision", "REVIEW")
        confidence = llm_result.get("confidence", 0.5)

        # Adjust decision based on thresholds
        if decision == "BLOCK" and confidence < THRESHOLDS.expert_confidence_block:
            decision = "REVIEW"
        elif decision == "APPROVE" and confidence < THRESHOLDS.expert_confidence_review:
            decision = "REVIEW"

        # Step 6: Generate SAR draft if needed
        sar_draft = None
        if decision in ["BLOCK", "REVIEW"]:
            sar_draft = generate_sar_draft(
                input_data,
                primary_typology,
                risk_factors,
                llm_result.get("reasoning", ""),
            )

        # Build regulatory references
        citations = []
        for ref in llm_result.get("regulatory_citations", []):
            citations.append(RegulatoryReference(
                source=ref.split()[0] if ref else "Unknown",
                reference=ref,
                relevance="Cited by Expert Agent",
            ))

        processing_time = (time.time() - start_time) * 1000

        return TribunalVerdict(
            decision=decision,
            confidence=confidence,
            typology=primary_typology.name if primary_typology else None,
            typology_confidence=primary_typology.confidence if primary_typology else None,
            risk_factors=risk_factors,
            risk_score=input_data.statistical_score,
            citations=citations,
            sar_draft=sar_draft,
            reasoning=llm_result.get("reasoning", ""),
            processing_time_ms=processing_time,
            model_used=config.llm_model,
        )

    def _get_regulatory_context(
        self,
        input_data: TribunalInput,
        typology: Optional[TypologyMatch],
    ) -> str:
        """Get relevant regulatory context via RAG."""
        contexts = []

        # Search for typology-specific guidance
        if typology:
            typology_context = search_typology_guidance(typology.name)
            contexts.append(f"TYPOLOGY GUIDANCE ({typology.name}):\n{typology_context}")

        # Search for amount-specific guidance
        amount = input_data.transaction.amount_sent
        if 9000 <= amount < 10000:
            results = vector_search("structuring reporting threshold $10000", limit=3)
            contexts.append(f"THRESHOLD GUIDANCE:\n{format_context(results)}")

        # General SAR guidance
        results = vector_search("suspicious activity report filing requirements", limit=3)
        contexts.append(f"SAR REQUIREMENTS:\n{format_context(results)}")

        return "\n\n".join(contexts)

    def _get_llm_decision(
        self,
        input_data: TribunalInput,
        typology: Optional[TypologyMatch],
        regulatory_context: str,
    ) -> dict:
        """Get decision from LLM."""
        tx = input_data.transaction
        stats = input_data.account_history.stats

        # Build prompt
        prompt = f"""TRANSACTION UNDER REVIEW:
- Amount: ${tx.amount_sent:,.2f} {tx.amount.currency_sent}
- Payment Format: {tx.payment_format}
- Date: {tx.timestamp.strftime('%Y-%m-%d %H:%M')}
- Sender: Account {tx.sender.account_id} at Bank {tx.sender.bank_id}
- Receiver: Account {tx.receiver.account_id} at Bank {tx.receiver.bank_id}

LAYER 1 (STATISTICAL) SCORE: {input_data.statistical_score:.2f}/10.0
- Interpretation: {"HIGH ANOMALY" if input_data.statistical_score > 5 else "MODERATE ANOMALY" if input_data.statistical_score > 3 else "LOW ANOMALY"}

LAYER 2 (NARRATIVE) SCORE: {input_data.narrative_score:.2%}
- Interpretation: {"SEVERE BREAK" if input_data.narrative_score < 0.3 else "SUSPICIOUS" if input_data.narrative_score < 0.5 else "MODERATE DEVIATION"}

ACCOUNT HISTORY:
- Total Transactions: {stats.total_transactions}
- Total Sent: ${stats.total_sent:,.2f}
- Total Received: ${stats.total_received:,.2f}
- Avg Transaction: ${stats.avg_transaction_amount:,.2f}
- Unique Counterparties: {stats.unique_counterparties}
- Frequency: {stats.transaction_frequency_per_day}/day

TRIGGERED BY: {input_data.triggered_by.upper()} ENGINE

PRE-DETECTED TYPOLOGY: {typology.name if typology else "None detected"}
{f"- Confidence: {typology.confidence:.0%}" if typology else ""}
{f"- Signals: {', '.join(typology.signals_matched)}" if typology else ""}

REGULATORY CONTEXT:
{regulatory_context}

Based on all the above, provide your decision as JSON."""

        response = self.clients.chat(
            user_message=prompt,
            system_prompt=TRIBUNAL_SYSTEM_PROMPT,
            model=config.llm_model,
            max_tokens=1500,
            temperature=0.0,
        )

        # Parse JSON response
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError:
            pass

        # Fallback if JSON parsing fails
        return {
            "decision": "REVIEW",
            "confidence": 0.5,
            "reasoning": response,
            "key_risk_factors": [],
            "regulatory_citations": [],
        }

    # =========================================================================
    # Q&A MODE - Original Expert Functionality
    # =========================================================================

    def ask(
        self,
        question: str,
        source: Optional[str] = None,
        verbose: bool = False,
    ) -> str:
        """
        Ask the AML expert a question (original functionality).

        Args:
            question: The question to ask
            source: Filter by source (e.g., "FATF", "EU", "Enforcement")
            verbose: Print progress

        Returns:
            Expert answer string
        """
        if verbose:
            print(f"\n{'─'*60}")
            print(f"Question: {question}")
            print(f"{'─'*60}")
            print("\nSearching regulatory knowledge base...")

        # Search for relevant context
        results = vector_search(question, limit=8, source_filter=source)

        if verbose:
            print(f"Found {len(results)} relevant documents:")
            for r in results[:5]:
                print(f"  - [{r['metadata']['source']}] {r['metadata']['filename']} ({r['score']:.2f})")

        # Format context
        context = format_context(results)

        # Build prompt
        prompt = f"""REGULATORY CONTEXT (from knowledge base):
{context}

USER QUESTION:
{question}

Provide a comprehensive answer based on the regulatory context above and your expertise.
Structure your response clearly. Cite specific documents when referencing guidance."""

        if verbose:
            print(f"\nGenerating expert response using {config.llm_model}...\n")

        # Get response
        answer = self.clients.chat(
            user_message=prompt,
            system_prompt=AML_EXPERT_SYSTEM_PROMPT,
            model=config.llm_model,
            max_tokens=2000,
            temperature=0.0,
        )

        if verbose:
            print("=" * 60)
            print("AML EXPERT RESPONSE")
            print("=" * 60)
            print(answer)
            print("=" * 60)

        return answer

    def search(self, query: str, limit: int = 5) -> List[dict]:
        """Search the knowledge base directly."""
        results = vector_search(query, limit=limit)
        return [
            {
                "source": r["metadata"]["source"],
                "filename": r["metadata"]["filename"],
                "text": r["text"][:500],
                "score": r["score"],
            }
            for r in results
        ]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def quick_query(question: str, source: str = None) -> str:
    """Quick function to ask a single question."""
    agent = ExpertAgent()
    return agent.ask(question, source=source, verbose=False)


# =============================================================================
# INTERACTIVE MODE
# =============================================================================

def interactive_mode():
    """Run interactive Q&A session with the AML expert."""
    agent = ExpertAgent()

    print("\n" + "=" * 60)
    print("AML DOMAIN EXPERT AGENT")
    print(f"Powered by {config.llm_model}")
    print("=" * 60)
    print("""
Welcome! I'm your AML/CFT compliance expert.

I have access to:
- FATF 40 Recommendations & Guidance
- EU AML Regulations (AMLR, AMLD5, AMLD6)
- JMLSG Guidance (UK)
- EBA Guidelines
- Wolfsberg Principles
- Basel Committee Guidance
- Enforcement Cases (FCA, FinCEN, OCC)

Commands:
- Type your question and press Enter
- Type 'sources' to filter by source (e.g., 'sources:FATF')
- Type 'quit' to exit
""")

    source_filter = None

    while True:
        try:
            user_input = input("\nYour question: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("\nGoodbye!")
                break

            if user_input.lower().startswith("sources:"):
                source_filter = user_input.split(":")[1].strip()
                print(f"Filter set to: {source_filter}")
                continue

            if user_input.lower() == "sources":
                source_filter = None
                print("Source filter cleared")
                continue

            agent.ask(user_input, source=source_filter, verbose=True)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        agent = ExpertAgent()
        agent.ask(question, verbose=True)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
