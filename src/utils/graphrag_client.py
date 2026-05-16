"""TigerGraph GraphRAG service HTTP client."""

import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPHRAG_URL = os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000").rstrip("/")
GRAPH_NAME = os.getenv("TG_GRAPH_NAME", "GraphRAG")

RETRIEVER_TO_METHOD = {
    "hybrid": "hybrid",
    "community": "community",
    "sibling": "contextual",
    "contextual": "contextual",
}

DEFAULT_METHOD_PARAMS = {
    "hybrid": {
        "indices": ["DocumentChunk", "Entity"],
        "top_k": 5,
        "num_hops": 2,
        "num_seen_min": 2,
        "verbose": False,
        "similarity_threshold": 0.90,
    },
    "community": {
        "community_level": 2,
        "top_k": 3,
        "verbose": False,
        "with_chunk": True,
        "with_doc": False,
        "similarity_threshold": 0.90,
    },
    "contextual": {
        "index": "DocumentChunk",
        "top_k": 5,
        "lookahead": 3,
        "lookback": 3,
        "withHyDE": False,
        "verbose": False,
    },
}


def _auth() -> tuple[str, str] | None:
    user = os.getenv("TG_USERNAME", "").strip()
    password = os.getenv("TG_PASSWORD", "").strip()
    if user and password:
        return user, password
    return None


def _session() -> requests.Session:
    session = requests.Session()
    auth = _auth()
    if not auth:
        return session
    session.auth = auth
    login = session.post(f"{GRAPHRAG_URL}/{GRAPH_NAME}/login", timeout=30)
    if login.ok:
        session_id = login.json().get("session_id")
        if session_id:
            session.headers["X-Session-Id"] = session_id
    return session


def _method_params(retriever: str, hop_depth: int) -> dict[str, Any]:
    method = RETRIEVER_TO_METHOD.get(retriever, "hybrid")
    params = dict(DEFAULT_METHOD_PARAMS.get(method, DEFAULT_METHOD_PARAMS["hybrid"]))
    
    # Override defaults with runtime values if provided
    if method == "hybrid":
        params["num_hops"] = hop_depth
    elif method == "community" and hop_depth != 2:
        # For community, we repurpose hop_depth as community_level if explicitly set
        params["community_level"] = hop_depth
        
    return params


def query_graphrag(
    question: str,
    retriever: str = "hybrid",
    hop_depth: int = 2,
    timeout: int = 180,
) -> dict[str, Any]:
    """Query GraphRAG via the answerquestion API."""
    method = RETRIEVER_TO_METHOD.get(retriever, "hybrid")
    payload = {
        "question": question,
        "method": method,
        "method_params": _method_params(retriever, hop_depth),
    }
    session = _session()
    url = f"{GRAPHRAG_URL}/{GRAPH_NAME}/graphrag/answerquestion"
    resp = session.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def parse_answer(data: dict[str, Any]) -> tuple[str, list]:
    answer = (
        data.get("response")
        or data.get("natural_language_response")
        or ""
    )
    if isinstance(answer, dict):
        answer = answer.get("text", str(answer))
    answer = str(answer).strip()
    if "no context information was provided" in answer.lower():
        answer = (
            "GraphRAG has no indexed chunks yet. Run ingest, then rebuild the knowledge graph "
            "(http://localhost:8000/ui or Savanna UI) so documents are chunked and embedded."
        )
    retrieved = data.get("retrieved") or data.get("query_sources") or {}
    entities = []
    if isinstance(retrieved, dict):
        entities = retrieved.get("entities") or retrieved.get("Entity") or []
    return answer, entities


def extract_clinical_signals(data: dict[str, Any], answer: str) -> dict[str, Any]:
    """Extract dashboard-friendly clinical warning signals from graph output."""
    interactions = data.get("interactions") or data.get("critical_interactions") or []
    severe_terms = ("contraindicated", "severe", "fatal", "bleeding", "rhabdomyolysis", "toxicity")
    warnings = []

    if isinstance(interactions, list):
        for item in interactions:
            if not isinstance(item, dict):
                continue
            severity = str(item.get("severity", "")).lower()
            mechanism = item.get("mechanism") or item.get("path") or item.get("interaction_path") or ""
            drugs = item.get("drugs") or [item.get("drug1") or item.get("from"), item.get("drug2") or item.get("to")]
            drugs = [d for d in drugs if d]
            if severity in {"moderate", "severe", "contraindicated", "fatal"} or any(term in mechanism.lower() for term in severe_terms):
                warnings.append({
                    "drugs": drugs,
                    "severity": severity or "clinical",
                    "mechanism": mechanism,
                    "action": item.get("clinical_action") or item.get("action") or "Review before co-prescribing",
                })

    if not warnings and any(term in answer.lower() for term in severe_terms):
        first_line = next((line.strip() for line in answer.splitlines() if line.strip()), answer[:180])
        warnings.append({
            "drugs": [],
            "severity": "clinical",
            "mechanism": first_line,
            "action": "Review highlighted risk",
        })

    paths = (
        data.get("paths")
        or data.get("reasoning_paths")
        or data.get("enzyme_cascades")
        or data.get("affected_enzymes")
        or []
    )
    contraindications = data.get("contraindications") or data.get("absolute_contraindications") or []

    return {
        "warnings": warnings[:5],
        "paths": paths[:5] if isinstance(paths, list) else [str(paths)],
        "contraindications": contraindications[:5] if isinstance(contraindications, list) else [str(contraindications)],
        "authority_score": data.get("authority_score") or data.get("confidence") or None,
    }
