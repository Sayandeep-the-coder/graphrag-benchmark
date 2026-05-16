"""
Query Router — Classifies medical queries and routes to the optimal
GraphRAG retriever for maximum accuracy and minimum tokens.

Categories:
  INTERACTION  → hybrid_search (drug-drug, drug-disease)
  DIAGNOSIS    → sibling retriever (symptom→disease chain)
  CONTRADICTION→ community retriever (guideline conflicts)
  TEMPORAL     → hybrid_search with date filters
  MULTIHOP     → hybrid_search with increased hop depth
  COUNTERFACTUAL → hybrid_search with increased hop depth
  CROSS_ENTITY → hybrid_search with increased hop depth
"""

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CLASSIFICATION_PROMPT = """Classify this medical query into exactly ONE category.
Return ONLY the category name, nothing else.

Categories:
- INTERACTION: drug-drug interactions, drug safety, polypharmacy, side effects when combining medications
- DIAGNOSIS: symptom→disease mapping, "what disease causes X", differential diagnosis
- CONTRADICTION: guideline conflicts, differing recommendations, "do guidelines agree"
- TEMPORAL: how treatment changed over time, historical evolution of guidelines
- MULTIHOP: complex multi-entity reasoning, enzyme cascades, 3+ entity chains
- COUNTERFACTUAL: asks what changes if a drug/entity/path is removed
- CROSS_ENTITY: asks for entities satisfying multiple constraints or joins

Query: {query}

Category:"""

# Keyword-based fast classifier (no API call needed)
KEYWORD_PATTERNS = {
    "INTERACTION": [
        r"interact", r"combin", r"together", r"safe.*with",
        r"polypharm", r"co-prescri", r"adverse.*event",
        r"side effect.*when.*taking", r"drug.*drug",
    ],
    "DIAGNOSIS": [
        r"symptom", r"diagnos", r"what.*caus", r"present.*with",
        r"differential", r"what.*disease",
    ],
    "CONTRADICTION": [
        r"contradict", r"guideline.*agree", r"conflict",
        r"recommend.*differ", r"WHO.*FDA", r"consensus",
    ],
    "TEMPORAL": [
        r"changed.*over", r"evolution", r"history.*of.*treatment",
        r"when.*reclassif", r"between.*\d{4}.*\d{4}",
    ],
    "MULTIHOP": [
        r"cascade", r"pathway", r"trace.*mechanism",
        r"enzyme.*connect", r"chain.*of",
    ],
    "COUNTERFACTUAL": [
        r"if.*stop", r"stops taking", r"remove", r"discontinue",
        r"which.*resolve", r"what.*remains", r"no longer apply",
    ],
    "CROSS_ENTITY": [
        r"which.*share", r"both.*and", r"without.*interacting",
        r"satisfy both", r"constraints", r"join",
    ],
}


def classify_query_fast(query: str) -> str:
    """Classify query using keyword patterns (zero-cost)."""
    query_lower = query.lower()
    scores = {}

    for category, patterns in KEYWORD_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, query_lower))
        scores[category] = score

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "MULTIHOP"  # Default for complex queries


def classify_query_llm(query: str) -> str:
    """Classify query using Gemini (more accurate, costs tokens)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": CLASSIFICATION_PROMPT.format(query=query)}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 20}
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip().upper()
            if text in KEYWORD_PATTERNS:
                return text
    except (requests.RequestException, KeyError, IndexError, ValueError):
        pass

    return classify_query_fast(query)


# Retriever routing map
RETRIEVER_MAP = {
    "INTERACTION": {"retriever": "hybrid", "hop_depth": 3},
    "DIAGNOSIS":   {"retriever": "sibling", "hop_depth": 2},
    "CONTRADICTION": {"retriever": "community", "hop_depth": 2},
    "TEMPORAL":    {"retriever": "hybrid", "hop_depth": 2},
    "MULTIHOP":    {"retriever": "hybrid", "hop_depth": 3},
    "COUNTERFACTUAL": {"retriever": "hybrid", "hop_depth": 3},
    "CROSS_ENTITY": {"retriever": "hybrid", "hop_depth": 3},
}


def route_query(query: str, use_llm: bool = False) -> dict:
    """
    Classify and route a query to the optimal retriever.

    Returns:
        {
            "category": "INTERACTION",
            "retriever": "hybrid",
            "hop_depth": 3,
            "confidence": "keyword"  # or "llm"
        }
    """
    if use_llm:
        category = classify_query_llm(query)
        confidence = "llm"
    else:
        category = classify_query_fast(query)
        confidence = "keyword"

    config = RETRIEVER_MAP.get(category, RETRIEVER_MAP["MULTIHOP"])

    return {
        "category": category,
        "retriever": config["retriever"],
        "hop_depth": config["hop_depth"],
        "confidence": confidence,
    }
