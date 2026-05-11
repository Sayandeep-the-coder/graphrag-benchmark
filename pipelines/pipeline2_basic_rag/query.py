"""
Pipeline 2 — Basic RAG Query

Embeds the query with Gemini text-embedding-004, searches Pinecone,
builds a context prompt, and calls Gemma.
"""

import os
import time

from google import genai
from dotenv import load_dotenv
from pinecone import Pinecone

from utils.metrics import PipelineMetrics
from utils.retry import with_retry

load_dotenv()

# --- Lazy-initialized clients ---
_pc = None
_index = None
_client = None
_model_id = "models/gemma-4-26b-a4b-it"
EMBEDDING_MODEL = "models/gemini-embedding-001"

TOP_K = 3  # Number of chunks to retrieve (optimized for medical data)


def _get_clients():
    """Lazily initialize external clients on first call."""
    global _pc, _index, _client
    if _pc is None:
        _pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _index = _pc.Index(os.getenv("PINECONE_INDEX_NAME", "graphrag-benchmark"))
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _index, _client


def run(query: str, top_k: int = TOP_K, namespace: str = "medical-rag") -> dict:
    """
    Run a query through the Basic RAG pipeline.

    1. Embed query with Gemini text-embedding-004
    2. Search Pinecone for top_k similar chunks
    3. Build context-augmented prompt
    4. Call Gemma

    Args:
        query: Natural language question.
        top_k: Number of similar chunks to retrieve.
        namespace: Pinecone namespace to search in.

    Returns:
        Dict with answer, metrics, chunks_retrieved, similarity_scores.
    """
    metrics = PipelineMetrics("Basic-RAG")

    index, client = _get_clients()

    # Step 1: Embed query
    response = with_retry(lambda: client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query
    ))
    
    if response is None or not hasattr(response, "embeddings") or not response.embeddings:
        raise ValueError(f"Gemini embedding API returned an invalid or empty response: {response}")
        
    query_embedding = response.embeddings[0].values

    # Step 2: Pinecone similarity search
    # Fetch more chunks than needed to allow for dynamic hopping
    fetch_k = max(15, top_k * 2)
    print(f"DEBUG: Searching Pinecone in namespace '{namespace}' with fetch_k={fetch_k}...")
    results = index.query(
        vector=query_embedding,
        top_k=fetch_k,
        namespace=namespace,
        include_metadata=True,
    )

    matches = results.get("matches", [])
    
    # Dynamic Top-K Hopping Logic
    min_score_threshold = 0.5
    score_drop_threshold = 0.05
    
    chunks = []
    scores = []
    
    if matches:
        prev_score = matches[0]["score"]
        
        for match in matches:
            score = match["score"]
            
            # Absolute quality threshold
            if score < min_score_threshold:
                print(f"DEBUG: Stopping retrieval. Score {score:.3f} is below min_threshold {min_score_threshold}.")
                break
                
            # Relative quality drop (hopping cliff)
            if len(chunks) > 0 and (prev_score - score) > score_drop_threshold:
                print(f"DEBUG: Score cliff detected! Dropped from {prev_score:.3f} to {score:.3f}. Stopping hopping.")
                break
                
            chunks.append(match["metadata"]["text"])
            scores.append(score)
            prev_score = score
            
            # Cap at the requested top_k
            if len(chunks) >= top_k:
                break
    
    print(f"DEBUG: Retained {len(chunks)} chunks after dynamic hopping. Top score: {scores[0] if scores else 'N/A'}")
    
    if not chunks:
        return {
            "answer": "Error: No relevant context was found in the database for this query. Please ensure the data was ingested correctly and the namespace is correct.",
            "metrics": metrics.to_dict(),
            "chunks_retrieved": 0,
            "similarity_scores": [],
        }

    context = "\n\n---\n\n".join(chunks)

    # Step 3: Build prompt + call Gemini
    prompt = (
        "You are a medical assistant. Use ONLY the context provided below to answer the question.\n"
        "If the answer is not in the context, say you don't know.\n\n"
        f"CONTEXT FROM DATABASE:\n{context}\n\n"
        f"USER QUESTION: {query}\n\n"
        "ASSISTANT ANSWER:"
    )

    start = time.time()
    try:
        def _make_request():
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/{_model_id}:generateContent?key={os.getenv('GEMINI_API_KEY')}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

        response_json = with_retry(_make_request)
        
        # Parse the JSON response
        try:
            candidates = response_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                # Filter out thought parts and get the actual text response
                text_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]
                answer = "".join(text_parts).strip()
                if not answer:
                    answer = "Error: LLM returned an empty or invalid response."
            else:
                answer = "Error: LLM service returned an invalid response object."
        except Exception as parse_e:
            answer = f"Error parsing response: {str(parse_e)}"
    except Exception as e:
        answer = f"Error generating response: {str(e)}"
    
    metrics.record(prompt, answer, start)

    return {
        "answer": answer,
        "metrics": metrics.to_dict(),
        "chunks_retrieved": len(chunks),
        "similarity_scores": scores,
    }
