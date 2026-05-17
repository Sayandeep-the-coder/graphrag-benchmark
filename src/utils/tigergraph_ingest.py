"""Load medical documents into TigerGraph Savanna for GraphRAG (pyTigerGraph).

The preferred path is CSV shard loading. TigerGraph's loader handles quoted
multi-line text reliably, and separate shard files avoid one large JSONL HTTP
payload.
"""

from __future__ import annotations

import csv
import glob
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

LOAD_JOB_JSON = "load_documents_content_json"
LOAD_JOB_CSV = "load_documents_content_csv_benchmark"
FILE_TAG = "DocumentContent"
CSV_HEADER = ["doc_id", "content"]


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
    if base.restppPort == base.gsPort and "/restpp" not in base.restppUrl:
        base.restppUrl = base.restppUrl + "/restpp"
    token = base.getToken()[0]
    conn = TigerGraphConnection(
        host=host,
        username=user,
        password=password,
        graphname=graph,
        restppPort=restpp,
        gsPort=gs,
        apiToken=token,
    )
    if conn.restppPort == conn.gsPort and "/restpp" not in conn.restppUrl:
        conn.restppUrl = conn.restppUrl + "/restpp"
    return conn


def _iter_document_records(docs_folder: str):
    docs_path = Path(docs_folder).resolve()

    unified_path = docs_path / "unified_corpus.json"
    if unified_path.exists():
        docs = json.loads(unified_path.read_text(encoding="utf-8"))
        for i, doc in enumerate(docs, start=1):
            doc_id = (
                doc.get("id")
                or doc.get("doc_id")
                or doc.get("title")
                or doc.get("name")
                or f"doc_{i:06d}"
            )
            source = doc.get("source") or doc.get("source_type") or "medical"
            title = doc.get("title") or doc.get("name") or doc_id
            text = doc.get("text") or doc.get("content") or ""
            if text.strip():
                yield {
                    "doc_id": f"{source}_{doc_id}",
                    "doc_type": source,
                    "content": f"Source: {source}\nRecord: {title}\n{text}",
                }
        return

    filepaths = sorted(glob.glob(str(docs_path / "**/*.txt"), recursive=True))
    for filepath in filepaths:
        content = Path(filepath).read_text(encoding="utf-8")
        if content.strip():
            yield {
                "doc_id": os.path.basename(filepath),
                "doc_type": "",
                "content": content,
            }


def build_jsonl(docs_folder: str) -> Path:
    docs_path = Path(docs_folder).resolve()
    jsonl_path = docs_path / "graphrag_ingest.jsonl"
    records = list(_iter_document_records(docs_folder))
    if not records:
        raise FileNotFoundError(f"No ingestible documents under {docs_folder}")

    with jsonl_path.open("w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return jsonl_path


def build_csv_shards(
    docs_folder: str,
    *,
    output_dir: str | None = None,
    rows_per_file: int = 100,
) -> list[Path]:
    docs_path = Path(docs_folder).resolve()
    records = list(_iter_document_records(docs_folder))
    if not records:
        raise FileNotFoundError(f"No ingestible documents under {docs_folder}")

    shard_dir = Path(output_dir).resolve() if output_dir else docs_path / "graphrag_csv_shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    for old_file in shard_dir.glob("documents_*.csv"):
        old_file.unlink()

    shard_paths: list[Path] = []
    rows_per_file = max(1, rows_per_file)
    for shard_index in range(0, len(records), rows_per_file):
        shard_records = records[shard_index : shard_index + rows_per_file]
        shard_path = shard_dir / f"documents_{(shard_index // rows_per_file) + 1:04d}.csv"
        with shard_path.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(
                out,
                fieldnames=CSV_HEADER,
                delimiter="|",
                quotechar='"',
                quoting=csv.QUOTE_ALL,
                lineterminator="\n",
            )
            writer.writeheader()
            for record in shard_records:
                writer.writerow(
                    {
                        "doc_id": str(record["doc_id"]).lower(),
                        "content": record["content"],
                    }
                )
        shard_paths.append(shard_path)
    return shard_paths


def _ensure_csv_loading_job(conn, graphname: str, load_job: str = LOAD_JOB_CSV) -> str:
    schema = conn.gsql(f"USE GRAPH {graphname}\nLS")
    marker = f"CREATE LOADING JOB {load_job}"
    if marker in schema:
        return load_job

    gsql = f"""
CREATE LOADING JOB {load_job} {{
    DEFINE FILENAME DocumentContent;
    LOAD DocumentContent TO VERTEX Document VALUES(gsql_lower($0), gsql_current_time_epoch(0), _, _) USING SEPARATOR="|", HEADER="true", EOL="\\n", QUOTE="double";
    LOAD DocumentContent TO VERTEX Content VALUES(gsql_lower($0), _, $1, gsql_current_time_epoch(0)) USING SEPARATOR="|", HEADER="true", EOL="\\n", QUOTE="double";
    LOAD DocumentContent TO EDGE HAS_CONTENT VALUES(gsql_lower($0) Document, gsql_lower($0) Content) USING SEPARATOR="|", HEADER="true", EOL="\\n", QUOTE="double";
}}
"""
    result = conn.gsql(f"USE GRAPH {graphname}\nBEGIN\n{gsql}\nEND\n")
    if isinstance(result, str) and ("failed" in result.lower() or "error" in result.lower()):
        raise RuntimeError(f"Failed to create CSV loading job {load_job}: {result}")
    return load_job


def _parse_load_result(load_result) -> dict:
    summary = {
        "valid_lines": 0,
        "rejected_lines": 0,
        "documents_loaded": 0,
        "raw": load_result,
    }
    if not load_result:
        return summary
    for entry in load_result if isinstance(load_result, list) else [load_result]:
        stats = entry.get("statistics", {}) if isinstance(entry, dict) else {}
        parsing = stats.get("parsingStatistics", stats)
        file_level = parsing.get("fileLevel", {})
        summary["valid_lines"] += file_level.get("validLine", stats.get("validLine", 0))
        summary["rejected_lines"] += file_level.get("invalidLine", stats.get("invalidLine", 0))
        obj_level = parsing.get("objectLevel", stats)
        for vertex in obj_level.get("vertex", []):
            if vertex.get("typeName") == "Document":
                summary["documents_loaded"] += vertex.get("validObject", 0)
    return summary


def ingest_to_savanna(
    docs_folder: str = "./data/processed",
    *,
    graphrag_url: str | None = None,
    rebuild: bool = True,
    rebuild_timeout: int = 600,
    format: str = "csv",
    rows_per_file: int = 100,
) -> dict:
    """
    Ingest documents into Savanna and optionally rebuild the GraphRAG knowledge graph.

    CSV mode writes quoted pipe-delimited shards and loads each shard with
    runLoadingJobWithFile. JSONL mode is kept as a fallback for compatibility.
    """
    conn = _connection()
    graphname = os.getenv("TG_GRAPH_NAME", "GraphRAG").strip() or "GraphRAG"

    graphrag_host = (graphrag_url or os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000")).rstrip("/")
    init = None
    try:
        conn.ai.configureGraphRAGHost(graphrag_host)
        init = conn.ai.initializeGraphRAG()
    except Exception as exc:
        init = {"skipped": True, "reason": str(exc)}

    if format.lower() == "jsonl":
        jsonl_path = build_jsonl(docs_folder)
        payload = jsonl_path.read_text(encoding="utf-8")
        load = conn.runLoadingJobWithData(
            payload,
            fileTag=FILE_TAG,
            jobName=LOAD_JOB_JSON,
            eol="\n",
        )
        load_files = [str(jsonl_path)]
        load_summary = [_parse_load_result(load)]
    elif format.lower() == "csv":
        load_job = _ensure_csv_loading_job(conn, graphname)
        csv_paths = build_csv_shards(docs_folder, rows_per_file=rows_per_file)
        load_files = [str(path) for path in csv_paths]
        load_summary = []
        load = []
        for csv_path in csv_paths:
            result = conn.runLoadingJobWithFile(str(csv_path), FILE_TAG, load_job, sep="|")
            load.append(result)
            parsed = _parse_load_result(result)
            parsed["file"] = str(csv_path)
            load_summary.append(parsed)
    else:
        raise ValueError("format must be 'csv' or 'jsonl'")

    result = {
        "format": format.lower(),
        "load_files": load_files,
        "initialize": init,
        "load": load,
        "load_summary": load_summary,
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
