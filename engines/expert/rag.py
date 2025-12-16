"""
RAG (Retrieval-Augmented Generation) for Expert Agent

Provides vector search over regulatory knowledge base.
"""

from typing import List, Dict, Any, Optional
from shared.db import get_db
from shared.clients import get_clients


def vector_search(
    query: str,
    limit: int = 8,
    source_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search the regulatory docs vector database.

    Args:
        query: Search query
        limit: Maximum number of results
        source_filter: Filter by source (e.g., "FATF", "EU", "Enforcement")

    Returns:
        List of matching documents with metadata and relevance scores
    """
    clients = get_clients()
    db = get_db()

    # Generate embedding for query
    query_embedding = clients.get_embedding(query)

    # Build aggregation pipeline
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": limit,
            }
        },
        {
            "$project": {
                "text": 1,
                "metadata": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    # Add source filter if specified
    if source_filter:
        pipeline[0]["$vectorSearch"]["filter"] = {"metadata.source": source_filter}

    results = list(db.regulatory_docs.aggregate(pipeline))
    return results


def format_context(results: List[Dict[str, Any]], max_chars: int = 1500) -> str:
    """
    Format search results as context for the LLM.

    Args:
        results: Vector search results
        max_chars: Maximum characters per result

    Returns:
        Formatted context string
    """
    context_parts = []

    for i, r in enumerate(results, 1):
        source = r["metadata"]["source"]
        filename = r["metadata"]["filename"]
        text = r["text"][:max_chars]
        score = r["score"]

        context_parts.append(
            f"---\n"
            f"SOURCE {i}: [{source}] {filename} (relevance: {score:.2f})\n"
            f"{text}\n"
            f"---"
        )

    return "\n".join(context_parts)


def search_typology_guidance(typology: str) -> str:
    """
    Search for regulatory guidance specific to a typology.

    Args:
        typology: Name of the typology (e.g., "Structuring", "Smurfing")

    Returns:
        Formatted context about the typology
    """
    # Search for typology-specific guidance
    queries = [
        f"{typology} money laundering typology red flags",
        f"{typology} suspicious activity indicators",
        f"{typology} detection methods AML",
    ]

    all_results = []
    for query in queries:
        results = vector_search(query, limit=3)
        all_results.extend(results)

    # Deduplicate by text
    seen_texts = set()
    unique_results = []
    for r in all_results:
        text_hash = hash(r["text"][:100])
        if text_hash not in seen_texts:
            seen_texts.add(text_hash)
            unique_results.append(r)

    return format_context(unique_results[:6])


def search_sar_requirements() -> str:
    """
    Search for SAR filing requirements and guidance.

    Returns:
        Formatted context about SAR requirements
    """
    results = vector_search(
        "Suspicious Activity Report filing requirements thresholds",
        limit=5,
    )
    return format_context(results)
