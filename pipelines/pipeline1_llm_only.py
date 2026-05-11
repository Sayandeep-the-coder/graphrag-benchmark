"""
Pipeline 1 — LLM Only

Sends the query directly to Gemma 3 2B with no retrieval context.
Serves as the worst-case token baseline (high hallucination risk).
"""

import os
import time

from google import genai
from dotenv import load_dotenv

from utils.metrics import PipelineMetrics
from utils.retry import with_retry

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model_id = "models/gemma-4-26b-a4b-it"


def run(query: str) -> dict:
    """
    Run a query through the LLM-only pipeline (no retrieval context).

    Args:
        query: Natural language question.

    Returns:
        Dict with 'answer' and 'metrics' keys.
    """
    metrics = PipelineMetrics("LLM-Only")

    prompt = (
        f"Answer the following question as accurately as possible.\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
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

    return {"answer": answer, "metrics": metrics.to_dict()}
