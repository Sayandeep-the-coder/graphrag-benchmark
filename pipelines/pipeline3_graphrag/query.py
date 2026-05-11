"""
Pipeline 3 — GraphRAG Query

Queries the TigerGraph GraphRAG service via REST API.
Supports multiple retriever modes (hybrid, community, sibling)
and configurable hop depth for multi-hop graph traversal.
"""

import os
import time

import requests
from dotenv import load_dotenv

from utils.metrics import PipelineMetrics

load_dotenv()

GRAPHRAG_URL = os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000")


def run(query: str, retriever: str = "hybrid", hop_depth: int = 2) -> dict:
    """
    Run a query through the GraphRAG pipeline.

    1. POST query to GraphRAG service
    2. Parse answer and token counts from response
    3. Calculate cost and latency manually

    Args:
        query: Natural language question.
        retriever: Retrieval mode — "hybrid", "community", or "sibling".
        hop_depth: Graph traversal depth (1=fast/cheap, 3=deep/expensive).

    Returns:
        Dict with answer, metrics, entities_retrieved, retriever, hop_depth.
    """
    metrics = PipelineMetrics("GraphRAG")

    payload = {
        "query": query,
        "retriever": retriever,
        "hop_depth": hop_depth,
    }

    start = time.time()
    try:
        resp = requests.post(
            f"{GRAPHRAG_URL}/query",
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        answer = data.get("answer", "")
        entities_retrieved = data.get("entities", [])

        # GraphRAG service provides its own token counts
        metrics.prompt_tokens = data.get("prompt_tokens", 0)
        metrics.completion_tokens = data.get("completion_tokens", 0)
        metrics.cost_usd = (
            metrics.prompt_tokens + metrics.completion_tokens
        ) / 1_000_000 * 0.075
    except Exception as e:
        answer = f"Error connecting to GraphRAG service at {GRAPHRAG_URL}. Please ensure the service is running. Details: {e}"
        entities_retrieved = []

    metrics.latency_ms = (time.time() - start) * 1000

    return {
        "answer": answer,
        "metrics": metrics.to_dict(),
        "entities_retrieved": entities_retrieved,
        "retriever": retriever,
        "hop_depth": hop_depth,
    }
