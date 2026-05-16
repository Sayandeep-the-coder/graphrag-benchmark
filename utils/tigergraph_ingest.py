"""Load medical documents into TigerGraph Savanna for GraphRAG (pyTigerGraph)."""

from __future__ import annotations

import glob
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LOAD_JOB = "load_documents_content_json"
FILE_TAG = "DocumentContent"


def _connection():
    from pyTigerGraph import TigerGraphConnection

    host = os.getenv("TG_HOST", "").strip().rstrip("/")
    graph = os.getenv("TG_GRAPH_NAME", "GraphRAG").strip() or "GraphRAG"
    user = os.getenv("TG_USERNAME", "").strip()
    password = os.getenv("TG_PASSWORD", "").strip()
    restpp = os.getenv("TG_RESTPP_PORT", "443").strip()
    gs = os.getenv("TG_GSQL_PORT", "14240").strip()
    if not all([host, user, password]):
        raise RuntimeError("TG_HOST, TG_USERNAME, and TG_PASSWORD are required")

    base = TigerGraphConnection(
        host=host,
        username=user,
        password=password,
        graphname=graph,
        restppPort=restpp,
        gsPort=gs,
    )
    token = base.getToken()[0]
    return TigerGraphConnection(
        host=host,
        username=user,
        password=password,
        graphname=graph,
        restppPort=restpp,
        gsPort=gs,
        apiToken=token,
    )


def build_jsonl(docs_folder: str) -> Path:
    docs_path = Path(docs_folder).resolve()
    jsonl_path = docs_path / "graphrag_ingest.jsonl"
    filepaths = sorted(glob.glob(str(docs_path / "**/*.txt"), recursive=True))
    if not filepaths:
        raise FileNotFoundError(f"No .txt files under {docs_folder}")

    with jsonl_path.open("w", encoding="utf-8") as out:
        for filepath in filepaths:
            content = Path(filepath).read_text(encoding="utf-8")
            record = {
                "doc_id": os.path.basename(filepath),
                "doc_type": "",
                "content": content,
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return jsonl_path


def ingest_to_savanna(
    docs_folder: str = "./data/medical",
    *,
    graphrag_url: str | None = None,
    rebuild: bool = True,
    rebuild_timeout: int = 600,
) -> dict:
    """
    Ingest .txt files into Savanna and optionally rebuild the GraphRAG knowledge graph.

    Uses runLoadingJobWithData so cloud Savanna does not need a local file path
    (the REST /graphrag/ingest path fails with DocumentContent not found on cloud).
    """
    jsonl_path = build_jsonl(docs_folder)
    payload = jsonl_path.read_text(encoding="utf-8")
    conn = _connection()

    graphrag_host = (graphrag_url or os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000")).rstrip("/")
    init = None
    try:
        conn.ai.configureGraphRAGHost(graphrag_host)
        init = conn.ai.initializeGraphRAG()
    except Exception as exc:
        init = {"skipped": True, "reason": str(exc)}

    load = conn.runLoadingJobWithData(
        payload,
        fileTag=FILE_TAG,
        jobName=LOAD_JOB,
        eol="\n",
    )

    result = {
        "jsonl_path": str(jsonl_path),
        "initialize": init,
        "load": load,
        "document_count": conn.getVertexCount("Document"),
        "content_count": conn.getVertexCount("Content"),
    }

    if rebuild:
        try:
            conn.ai.forceConsistencyUpdate("graphrag")
        except Exception as exc:
            result["rebuild_error"] = str(exc)
        else:
            deadline = time.time() + rebuild_timeout
            while time.time() < deadline:
                progress = conn.ai.checkConsistencyProgress("graphrag")
                result["rebuild_progress"] = progress
                status = ""
                if isinstance(progress, dict):
                    status = str(progress.get("status", "")).lower()
                if status in ("completed", "done", "success", "idle"):
                    break
                time.sleep(15)

    result["document_chunk_count"] = conn.getVertexCount("DocumentChunk")
    result["entity_count"] = conn.getVertexCount("Entity")
    return result
