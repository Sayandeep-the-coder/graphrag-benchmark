"""
Pipeline 3 — GraphRAG Query

Queries the TigerGraph GraphRAG service via REST API.
Supports multiple retriever modes (hybrid, community, sibling/contextual)
and configurable hop depth for multi-hop graph traversal.
"""

import os
import time
import asyncio
from dotenv import load_dotenv

from utils.metrics import PipelineMetrics
from utils.security import sanitize_error
from utils.graphrag_client import (
    GRAPHRAG_URL,
    query_graphrag,
    parse_answer,
)

load_dotenv()


def run(query: str, retriever: str = "hybrid", hop_depth: int = 2) -> dict:
    """
    Run a query through the GraphRAG pipeline.

    Args:
        query: Natural language question.
        retriever: Retrieval mode — "hybrid", "community", or "sibling".
        hop_depth: Graph traversal depth (1=fast/cheap, 3=deep/expensive).

    Returns:
        Dict with answer, metrics, entities_retrieved, retriever, hop_depth.
    """
    metrics = PipelineMetrics("GraphRAG")
    answer = ""
    entities_retrieved = []

    start = time.time()
    try:
        data = query_graphrag(query, retriever=retriever, hop_depth=hop_depth)
        answer, entities_retrieved = parse_answer(data)
        if not answer:
            answer = "GraphRAG returned an empty response. Ensure the graph is initialized and ingested."
    except Exception as e:
        answer = sanitize_error(
            f"Error connecting to GraphRAG service at {GRAPHRAG_URL}. "
            f"Please ensure the service is running and data is ingested. Details: {e}"
        )

    metrics.latency_ms = (time.time() - start) * 1000

    return {
        "answer": answer,
        "metrics": metrics.to_dict(),
        "entities_retrieved": entities_retrieved,
        "retriever": retriever,
        "hop_depth": hop_depth,
    }


async def run_stream(query: str, retriever: str = "hybrid", hop_depth: int = 2):
    """Run GraphRAG pipeline and yield SSE events."""
    metrics = PipelineMetrics("GraphRAG")
    yield {"type": "status", "message": "Querying GraphRAG Service (TigerGraph)..."}

    answer = ""
    entities_retrieved = []
    start = time.time()

    try:
        loop = asyncio.get_event_loop()

        def _make_request():
            return query_graphrag(query, retriever=retriever, hop_depth=hop_depth)

        data = await loop.run_in_executor(None, _make_request)
        answer, entities_retrieved = parse_answer(data)
        if not answer:
            answer = "GraphRAG returned an empty response. Ensure the graph is initialized and ingested."
        yield {
            "type": "chunk",
            "text": answer,
            "tokens": metrics.completion_tokens + metrics.prompt_tokens,
        }
    except Exception as e:
        answer = sanitize_error(
            f"Error connecting to GraphRAG service at {GRAPHRAG_URL}. "
            f"Please ensure the service is running and data is ingested. Details: {e}"
        )
        yield {"type": "chunk", "text": answer, "tokens": 0}

    metrics.latency_ms = (time.time() - start) * 1000

    yield {
        "type": "done",
        "answer": answer,
        "metrics": metrics.to_dict(),
        "entities_retrieved": entities_retrieved,
        "retriever": retriever,
        "hop_depth": hop_depth,
    }
