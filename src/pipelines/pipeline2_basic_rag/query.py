"""
Pipeline 2 — Basic RAG Query

Embeds queries with Pinecone Inference, retrieves from Pinecone with dynamic top-K,
then generates with models/gemma-4-26b-a4b-it via the GenAI REST API.
"""

import os
import time
import httpx
import json
import asyncio
import requests
from dotenv import load_dotenv

from src.utils.embeddings import get_pinecone_client, embed_texts
from src.utils.metrics import PipelineMetrics
from src.utils.retry import with_retry
from src.utils.security import sanitize_error

load_dotenv()

# --- Lazy-initialized clients ---
_pc = None
_index = None
_model_id = "models/gemma-4-26b-a4b-it"

TOP_K = 5  # Increased from 3 to improve recall


def _get_clients():
    """Lazily initialize Pinecone client and index on first call."""
    if not hasattr(_get_clients, "pc") or not hasattr(_get_clients, "index"):
        _get_clients.pc = get_pinecone_client()
        _get_clients.index = _get_clients.pc.Index(os.getenv("PINECONE_INDEX_NAME", "graphrag-benchmark"))
    return _get_clients.index, _get_clients.pc


def run(query: str, top_k: int = TOP_K, namespace: str = "medical-rag") -> dict:
    """
    Run a query through the Basic RAG pipeline.
    """
    metrics = PipelineMetrics("Basic-RAG")
    index, pc = _get_clients()

    # Step 1: Embed query (Pinecone Inference)
    query_embedding = embed_texts(pc, [query], input_type="query")[0]
    
    # Step 2: Pinecone similarity search
    fetch_k = max(15, top_k * 2)
    results = index.query(
        vector=query_embedding,
        top_k=fetch_k,
        namespace=namespace,
        include_metadata=True,
    )

    matches = results.get("matches", [])
    min_score_threshold = 0.2  # Lowered from 0.4 to handle low cosine scores in this dataset
    score_drop_threshold = 0.05
    chunks = []
    scores = []
    
    if matches:
        prev_score = matches[0]["score"]
        for match in matches:
            score = match["score"]
            # Flexible thresholding
            if score < min_score_threshold or (len(chunks) > 0 and (prev_score - score) > score_drop_threshold):
                break
            chunks.append(match["metadata"]["text"])
            scores.append(score)
            prev_score = score
            if len(chunks) >= top_k:
                break
    
    if not chunks:
        return {
            "answer": "Error: No relevant context was found in Pinecone. Ensure data is ingested.",
            "metrics": metrics.to_dict(),
            "chunks_retrieved": 0,
            "similarity_scores": [],
        }

    context = "\n\n---\n\n".join(chunks)
    prompt = (
        "Answer based ONLY on context. If unknown, say so.\n"
        f"Context:\n{context}\n"
        f"Q: {query}\n"
        "A:"
    )

    start = time.time()
    def _make_request():
        url = f"https://generativelanguage.googleapis.com/v1beta/{_model_id}:generateContent?key={os.getenv('GEMINI_API_KEY')}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

    try:
        response_json = with_retry(_make_request) or {}
        candidates = response_json.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]
            answer = "".join(text_parts).strip()
        else:
            answer = "Error: LLM service returned an empty response."
    except (requests.RequestException, ValueError, RuntimeError) as e:
        answer = sanitize_error(f"Error generating response: {str(e)}")
    
    metrics.record(prompt, answer, start)
    return {
        "answer": answer,
        "metrics": metrics.to_dict(),
        "chunks_retrieved": len(chunks),
        "similarity_scores": scores,
    }


async def run_stream(query: str, top_k: int = TOP_K, namespace: str = "medical-rag"):
    """
    Run Basic RAG pipeline and yield SSE events.
    """
    metrics = PipelineMetrics("Basic-RAG")
    yield {"type": "status", "message": "Retrieving context (Pinecone embedding)..."}

    index, pc = _get_clients()

    # Step 1: Embed query
    query_embedding = embed_texts(pc, [query], input_type="query")[0]

    # Step 2: Pinecone similarity search
    fetch_k = max(15, top_k * 2)
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, lambda: index.query(
        vector=query_embedding,
        top_k=fetch_k,
        namespace=namespace,
        include_metadata=True,
    ))

    matches = results.get("matches", [])
    min_score_threshold = 0.2
    score_drop_threshold = 0.05
    chunks = []
    scores = []
    
    if matches:
        prev_score = matches[0]["score"]
        for match in matches:
            score = match["score"]
            if score < min_score_threshold or (len(chunks) > 0 and (prev_score - score) > score_drop_threshold):
                break
            chunks.append(match["metadata"]["text"])
            scores.append(score)
            prev_score = score
            if len(chunks) >= top_k:
                break
    
    if not chunks:
        answer = "Error: No relevant context was found."
        yield {"type": "chunk", "text": answer, "tokens": 0}
        yield {"type": "done", "metrics": metrics.to_dict(), "answer": answer}
        return

    context = "\n\n---\n\n".join(chunks)
    prompt = (
        "Answer based ONLY on context. If unknown, say so.\n"
        f"Context:\n{context}\n"
        f"Q: {query}\n"
        "A:"
    )

    yield {"type": "status", "message": "Generating response (Gemma)..."}

    url = f"https://generativelanguage.googleapis.com/v1beta/{_model_id}:streamGenerateContent?alt=sse&key={os.getenv('GEMINI_API_KEY')}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    answer = ""
    prompt_tokens = int(len(prompt.split()) * 1.3)

    try:
        async with httpx.AsyncClient() as http_client:
            async with http_client.stream("POST", url, json=payload, timeout=60.0) as http_resp:
                http_resp.raise_for_status()
                async for line in http_resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    if "text" in p:
                                        chunk_text = p["text"]
                                        answer += chunk_text
                                        yield {"type": "chunk", "text": chunk_text, "tokens": prompt_tokens}
                        except json.JSONDecodeError:
                            continue
    except (httpx.HTTPError, ValueError, json.JSONDecodeError) as e:
        answer = sanitize_error(f"Error: {str(e)}")
        yield {"type": "chunk", "text": answer, "tokens": 0}

    metrics.completion_tokens = int(len(answer.split()) * 1.3)
    metrics.prompt_tokens = prompt_tokens
    
    yield {
        "type": "done",
        "answer": answer,
        "metrics": metrics.to_dict(),
        "chunks_retrieved": len(chunks),
    }
