"""
Pipeline 3 — GraphRAG Query

Queries the TigerGraph GraphRAG service via REST API.
Supports multiple retriever modes (hybrid, community, sibling)
and configurable hop depth for multi-hop graph traversal.
"""

import os
import time
import asyncio
import requests
from dotenv import load_dotenv

from utils.metrics import PipelineMetrics
from utils.security import sanitize_error

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
        answer = sanitize_error(f"Error connecting to GraphRAG service at {GRAPHRAG_URL}. Please ensure the service is running. Details: {e}")
        entities_retrieved = []

    metrics.latency_ms = (time.time() - start) * 1000

    return {
        "answer": answer,
        "metrics": metrics.to_dict(),
        "entities_retrieved": entities_retrieved,
        "retriever": retriever,
        "hop_depth": hop_depth,
    }


async def run_stream(query: str, retriever: str = "hybrid", hop_depth: int = 2):
    """
    Run GraphRAG pipeline and yield SSE events.
    Since the GraphRAG service doesn't natively stream tokens, 
    we simulate the streaming protocol by yielding status updates
    and then yielding the entire final answer as a chunk.
    """
    metrics = PipelineMetrics("GraphRAG")
    yield {"type": "status", "message": "Querying GraphRAG Service (TigerGraph)..."}

    payload = {
        "query": query,
        "retriever": retriever,
        "hop_depth": hop_depth,
    }

    start = time.time()
    try:
        # We use asyncio to prevent blocking the event loop while waiting for GraphRAG
        loop = asyncio.get_event_loop()
        def _make_request():
            resp = requests.post(
                f"{GRAPHRAG_URL}/query",
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()
            
        data = await loop.run_in_executor(None, _make_request)

        answer = data.get("answer", "")
        entities_retrieved = data.get("entities", [])

        # GraphRAG service provides its own token counts
        metrics.prompt_tokens = data.get("prompt_tokens", 0)
        metrics.completion_tokens = data.get("completion_tokens", 0)
        metrics.cost_usd = (
            metrics.prompt_tokens + metrics.completion_tokens
        ) / 1_000_000 * 0.075
        
        # Yield the final chunk
        yield {"type": "chunk", "text": answer, "tokens": metrics.completion_tokens + metrics.prompt_tokens}

    except Exception as e:
        answer = sanitize_error(f"Error connecting to GraphRAG service at {GRAPHRAG_URL}. Please ensure the service is running. Details: {e}")
        entities_retrieved = []
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
