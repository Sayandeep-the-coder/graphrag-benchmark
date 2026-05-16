"""
Pipeline 3 — GraphRAG Query

Queries the TigerGraph GraphRAG service via REST API.
Supports multiple retriever modes (hybrid, community, contextual)
and configurable hop depth for multi-hop graph traversal.
"""

import os
import time
import asyncio
from dotenv import load_dotenv

from src.utils.metrics import PipelineMetrics
from src.utils.security import sanitize_error
from src.utils.context_compression import build_graphrag_prompt, compress_graph_context
from src.utils.graphrag_client import (
    GRAPHRAG_URL,
    extract_clinical_signals,
    query_graphrag,
    parse_answer,
)
from src.utils.query_router import route_query

load_dotenv()


from src.utils.cypher_tool import run_cypher_query

def _resolve_route(query: str, retriever: str | None, hop_depth: int | None) -> dict:
    """Return an explicit GraphRAG route, using the query router when needed."""
    route = route_query(query, use_llm=True)
    if retriever and retriever in ["hybrid", "community", "contextual", "cypher"]:
        route["retriever"] = retriever
    if hop_depth:
        route["hop_depth"] = hop_depth
    return route


def _record_graph_metrics(metrics: PipelineMetrics, query: str, data: dict, answer: str, start: float) -> None:
    """Record comparable token metrics from compressed graph context."""
    compressed_context = compress_graph_context(data)
    prompt = build_graphrag_prompt(query, compressed_context)
    metrics.record(prompt, answer, start)


def run(query: str, retriever: str | None = None, hop_depth: int | None = None) -> dict:
    """
    Run a query through the GraphRAG pipeline.
    """
    metrics = PipelineMetrics("GraphRAG")
    answer = ""
    entities_retrieved = []
    clinical_signals = {}
    route = _resolve_route(query, retriever, hop_depth)

    start = time.time()
    try:
        if route["retriever"] == "cypher":
            print(f"  [PIPELINE] Routing to GENERATE_CYPHER for: {query}")
            answer = run_cypher_query(query)
            metrics.record(query, answer, start) # Rough recording for cypher
        else:
            data = query_graphrag(
                query,
                retriever=route["retriever"],
                hop_depth=route["hop_depth"],
            )
            answer, entities_retrieved = parse_answer(data)
            if not answer:
                answer = "GraphRAG returned an empty response. Ensure the graph is initialized and ingested."
            clinical_signals = extract_clinical_signals(data, answer)
            _record_graph_metrics(metrics, query, data, answer, start)
    except Exception as e:
        answer = sanitize_error(
            f"Error in GraphRAG pipeline. Details: {e}"
        )
        metrics.record(query, answer, start)

    return {
        "answer": answer,
        "metrics": metrics.to_dict(),
        "entities_retrieved": entities_retrieved,
        "retriever": route["retriever"],
        "hop_depth": route["hop_depth"],
        "query_category": route["category"],
        "route_confidence": route["confidence"],
        "clinical_signals": clinical_signals,
    }


async def run_stream(query: str, retriever: str | None = None, hop_depth: int | None = None):
    """Run GraphRAG pipeline and yield SSE events."""
    metrics = PipelineMetrics("GraphRAG")
    route = _resolve_route(query, retriever, hop_depth)
    yield {
        "type": "status",
        "message": (
            "Routing query as "
            f"{route['category']} via {route['retriever']} "
            f"(hops={route['hop_depth']})..."
        ),
    }

    answer = ""
    entities_retrieved = []
    clinical_signals = {}
    start = time.time()

    try:
        loop = asyncio.get_event_loop()

        if route["retriever"] == "cypher":
            yield {
                "type": "status",
                "message": f"Generating and running Cypher for structural query...",
            }
            answer = await loop.run_in_executor(None, run_cypher_query, query)
            metrics.record(query, answer, start)
        else:
            def _make_request():
                return query_graphrag(
                    query,
                    retriever=route["retriever"],
                    hop_depth=route["hop_depth"],
                )

            data = await loop.run_in_executor(None, _make_request)
            answer, entities_retrieved = parse_answer(data)
            if not answer:
                answer = "GraphRAG returned an empty response. Ensure the graph is initialized and ingested."
            clinical_signals = extract_clinical_signals(data, answer)
            _record_graph_metrics(metrics, query, data, answer, start)
            
        yield {
            "type": "chunk",
            "text": answer,
            "tokens": metrics.total_tokens,
        }
    except Exception as e:
        answer = sanitize_error(
            f"Error in GraphRAG pipeline. Details: {e}"
        )
        metrics.record(query, answer, start)
        yield {"type": "chunk", "text": answer, "tokens": 0}

    yield {
        "type": "done",
        "answer": answer,
        "metrics": metrics.to_dict(),
        "entities_retrieved": entities_retrieved,
        "retriever": route["retriever"],
        "hop_depth": route["hop_depth"],
        "query_category": route["category"],
        "route_confidence": route["confidence"],
        "clinical_signals": clinical_signals,
    }
