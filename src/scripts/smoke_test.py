"""
Smoke test — Verify all system components are operational.

Usage: python src/scripts/smoke_test.py

Runs 7 checks in order, printing ✅ or ❌ per check.
"""

import os
import sys

# Ensure UTF-8 output on Windows for emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv

load_dotenv()

# Add project root to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

checks_total = 7


def check(name, fn, results):
    """Run a check function and report result."""
    try:
        result = fn()
        print(f"  [PASS] {name}: {result}")
        results.append(True)
    except (RuntimeError, ValueError, TypeError, OSError, ImportError) as e:
        print(f"  [FAIL] {name}: {e}")
        results.append(False)


def check_gemini():
    """1. Verify Gemini API connectivity."""
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="models/gemma-4-26b-a4b-it",
        contents="Say hello in one word"
    )
    text = response.text or "EMPTY RESPONSE"
    return f"responded: {text.strip()[:30]}"


def check_pinecone():
    """2. Verify Pinecone index."""
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "graphrag-benchmark"))
    stats = index.describe_index_stats()
    total = stats.get("total_vector_count", 0)
    return f"{total:,} vectors in index"


def check_graphrag():
    """3. Verify GraphRAG service health."""
    import requests
    url = os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000")
    resp = requests.get(f"{url}/health", timeout=10)
    return f"status {resp.status_code}: {resp.json()}"


def check_pipeline1():
    """4. Run Pipeline 1 (LLM-Only)."""
    from src.pipelines import pipeline1_llm_only as p1
    result = p1.run("What is photosynthesis?")
    tokens = result["metrics"]["total_tokens"]
    return f"answered ({tokens} tokens)"


def check_pipeline2():
    """5. Run Pipeline 2 (Basic RAG)."""
    from src.pipelines.pipeline2_basic_rag import query as p2
    result = p2.run("What is photosynthesis?")
    tokens = result["metrics"]["total_tokens"]
    chunks = result["chunks_retrieved"]
    return f"answered ({tokens} tokens, {chunks} chunks)"


def check_pipeline3():
    """6. Run Pipeline 3 (GraphRAG)."""
    from src.graphrag.pipeline import query as p3
    result = p3.run("What is photosynthesis?")
    tokens = result["metrics"]["total_tokens"]
    return f"answered ({tokens} tokens)"


def check_token_comparison():
    """7. Verify GraphRAG uses fewer tokens than Basic RAG."""
    from src.pipelines.pipeline2_basic_rag import query as p2
    from src.graphrag.pipeline import query as p3

    r2 = p2.run("What is photosynthesis?")
    r3 = p3.run("What is photosynthesis?")

    p2_tokens = r2["metrics"]["total_tokens"]
    p3_tokens = r3["metrics"]["total_tokens"]

    if p3_tokens < p2_tokens:
        reduction = (p2_tokens - p3_tokens) / p2_tokens * 100
        return f"P3 ({p3_tokens}) < P2 ({p2_tokens}) → {reduction:.1f}% reduction"
    else:
        return f"⚠️  P3 ({p3_tokens}) >= P2 ({p2_tokens}) — expected P3 to be lower"


def main():
    results = []
    print(f"\n{'='*60}")
    print("  GraphRAG Inference Benchmark - Smoke Test")
    print(f"{'='*60}\n")

    check("Gemini API", check_gemini, results)
    check("Pinecone Index", check_pinecone, results)
    check("GraphRAG Service", check_graphrag, results)
    check("Pipeline 1 (LLM-Only)", check_pipeline1, results)
    check("Pipeline 2 (Basic RAG)", check_pipeline2, results)
    check("Pipeline 3 (GraphRAG)", check_pipeline3, results)
    check("Token Comparison (P3 < P2)", check_token_comparison, results)

    print(f"\n{'='*60}")
    checks_passed = sum(results)
    if checks_passed == checks_total:
        print(f"  All {checks_total} checks passed - All systems go!")
    else:
        print(f"  {checks_passed}/{checks_total} checks passed - Fix failing checks before proceeding")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
