"""
Pipeline 1 — LLM Only

Sends the query directly to gemma-4-26b-a4b-it with no retrieval context.
Serves as the lowest-context baseline (high hallucination risk on medical facts).
"""

import os
import time
import httpx
import json
import asyncio
from google import genai
from dotenv import load_dotenv

from src.utils.metrics import PipelineMetrics
from src.utils.retry import with_retry
from src.utils.security import sanitize_error

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model_id = "models/gemma-4-26b-a4b-it"


def run(query: str) -> dict:
    """
    Run a query through the LLM-only pipeline (no retrieval context).
    """
    metrics = PipelineMetrics("LLM-Only")

    prompt = (
        "Answer the question accurately.\n"
        f"Q: {query}\n"
        "A:"
    )

    start = time.time()
    try:
        def _make_request():
            import requests
            url = f"https://generativelanguage.googleapis.com/v1beta/{model_id}:generateContent?key={os.getenv('GEMINI_API_KEY')}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

        response_json = with_retry(_make_request) or {}
        
        candidates = response_json.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]
            answer = "".join(text_parts).strip()
            if not answer:
                answer = "Error: LLM returned an empty response."
        else:
            answer = "Error: LLM service returned an invalid response."
            
    except Exception as e:
        answer = sanitize_error(f"Error generating response: {str(e)}")
    
    metrics.record(prompt, answer, start)
    return {"answer": answer, "metrics": metrics.to_dict()}


async def run_stream(query: str):
    """
    Run LLM-only pipeline and yield SSE events.
    """
    metrics = PipelineMetrics("LLM-Only")
    prompt = (
        "Answer the question accurately.\n"
        f"Q: {query}\n"
        "A:"
    )
    start = time.time()
    yield {"type": "status", "message": "Generating response..."}

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_id}:streamGenerateContent?alt=sse&key={os.getenv('GEMINI_API_KEY')}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    answer = ""
    prompt_tokens = int(len(prompt.split()) * 1.3)

    try:
        async with httpx.AsyncClient() as http_client:
            async with http_client.stream("POST", url, json=payload, timeout=60.0) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                text_parts = [p.get("text", "") for p in parts if not p.get("thought", False)]
                                chunk = "".join(text_parts)
                                if chunk:
                                    answer += chunk
                                    metrics.completion_tokens = int(len(answer.split()) * 1.3)
                                    yield {"type": "chunk", "text": chunk, "tokens": metrics.completion_tokens + prompt_tokens}
                        except Exception:
                            continue
    except Exception as e:
        answer = sanitize_error(f"Error generating response: {str(e)}")
        yield {"type": "chunk", "text": answer, "tokens": 0}

    metrics.prompt_tokens = prompt_tokens
    metrics.record(prompt, answer, start)

    yield {"type": "done", "metrics": metrics.to_dict(), "answer": answer}
