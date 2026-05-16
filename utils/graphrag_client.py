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
}

DEFAULT_METHOD_PARAMS = {
    "hybrid": {
        "indices": ["DocumentChunk", "Entity"],
        "top_k": 5,
        "num_hops": 2,
        "num_seen_min": 2,
        "verbose": False,
    },
    "community": {
        "community_level": 2,
        "top_k": 3,
        "verbose": False,
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
    if method == "hybrid":
        params["num_hops"] = hop_depth
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
