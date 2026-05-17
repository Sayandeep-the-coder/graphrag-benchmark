"""
FastAPI Dashboard Backend

Runs all 3 inference pipelines in parallel via /compare endpoint.
Provides ingest triggers, health check, and benchmark summary.
"""

import asyncio
import glob
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

load_dotenv()

# Add project root to Python path so pipeline imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.server.models import (
    CompareRequest,
    CompareResponse,
    HealthResponse,
    IngestStatus,
    PipelineResult,
    BenchmarkQuery,
    BenchmarkSampleRequest,
)
from src.pipelines import pipeline1_llm_only as p1
from src.pipelines.pipeline2_basic_rag import query as p2
from src.graphrag.pipeline import query as p3
from src.evaluation.accuracy import evaluate_all_pipelines
from src.evaluation.benchmark_runner import BENCHMARK_QUERIES
from src.utils.security import sanitize_error

app = FastAPI(
    title="GraphRAG Inference Benchmark",
    description="Compare LLM-Only, Basic RAG, and GraphRAG pipelines",
    version="1.0.0",
)

# CORS — allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/benchmark/questions", response_model=list[BenchmarkQuery])
async def get_benchmark_questions():
    """Return the full clinical benchmark suite."""
    return BENCHMARK_QUERIES

executor = ThreadPoolExecutor(max_workers=3)


@app.post("/compare", response_model=CompareResponse)
async def compare(request: CompareRequest):
    """
    Run all 3 pipelines in parallel on the same query.
    """
    loop = asyncio.get_event_loop()

    r1_future = loop.run_in_executor(executor, partial(p1.run, request.query))
    r2_future = loop.run_in_executor(executor, partial(p2.run, request.query, top_k=request.top_k, namespace=request.namespace))
    r3_future = loop.run_in_executor(executor, partial(p3.run, request.query))

    r1, r2, r3 = await asyncio.gather(r1_future, r2_future, r3_future)

    accuracy = None
    if request.ground_truth:
        try:
            accuracy = evaluate_all_pipelines(
                questions=[request.query],
                p1_answers=[r1["answer"]],
                p2_answers=[r2["answer"]],
                ground_truths=[request.ground_truth],
                p3_answers=[r3["answer"]],
            )
        except Exception as e:
            print(sanitize_error(f"Evaluation failed: {e}"))

    token_reduction_pct = None
    if r2["metrics"]["total_tokens"] > 0 and r3["metrics"]["total_tokens"] > 0:
        token_reduction_pct = (
            (r2["metrics"]["total_tokens"] - r3["metrics"]["total_tokens"]) 
            / r2["metrics"]["total_tokens"] * 100
        )

    return CompareResponse(
        llm_only=PipelineResult(**r1),
        basic_rag=PipelineResult(**r2),
        graphrag=PipelineResult(**r3),
        token_reduction_pct=token_reduction_pct,
        accuracy=accuracy,
    )


@app.post("/compare/stream")
async def compare_stream(request: CompareRequest):
    """
    Stream all 3 pipelines in parallel via Server-Sent Events (SSE).
    """
    async def event_generator():
        queue = asyncio.Queue()
        final_results = {}

        async def consume_pipeline(pipeline_id, gen):
            try:
                async for chunk in gen:
                    chunk["pipeline"] = pipeline_id
                    if chunk.get("type") == "done":
                        final_results[pipeline_id] = chunk
                    await queue.put(chunk)
            except Exception as e:
                err_msg = sanitize_error(f"Error: {e}")
                await queue.put({"pipeline": pipeline_id, "type": "chunk", "text": err_msg, "tokens": 0})
                done = {"pipeline": pipeline_id, "type": "done", "answer": err_msg, "metrics": {}}
                final_results[pipeline_id] = done
                await queue.put(done)

        # Start all consumers
        tasks = [
            asyncio.create_task(consume_pipeline("llm_only", p1.run_stream(request.query))),
            asyncio.create_task(consume_pipeline("basic_rag", p2.run_stream(request.query, request.top_k, request.namespace))),
            asyncio.create_task(consume_pipeline("graphrag", p3.run_stream(request.query))),
        ]

        while True:
            if all(t.done() for t in tasks) and queue.empty():
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield f"data: {json.dumps(item)}\n\n"
            except asyncio.TimeoutError:
                continue

        if request.ground_truth and len(final_results) == 3:
            try:
                accuracy = evaluate_all_pipelines(
                    questions=[request.query],
                    p1_answers=[final_results["llm_only"].get("answer", "")],
                    p2_answers=[final_results["basic_rag"].get("answer", "")],
                    ground_truths=[request.ground_truth],
                    p3_answers=[final_results["graphrag"].get("answer", "")],
                )
                yield f"data: {json.dumps({'type': 'accuracy', 'accuracy': accuracy})}\n\n"
            except Exception as e:
                err_msg = sanitize_error(f"Evaluation failed: {e}")
                yield f"data: {json.dumps({'type': 'status', 'pipeline': 'system', 'message': err_msg})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.get("/implementation/status")
async def implementation_status():
    """Expose implemented hackathon strategy pieces for the frontend."""
    categories = {}
    for item in BENCHMARK_QUERIES:
        category = item.get("category", "GENERAL")
        categories[category] = categories.get(category, 0) + 1

    files = {
        "medical_graph_schema": "src/scripts/schema/medical_graph.gsql",
        "polypharmacy_query": "src/scripts/schema/polypharmacy_query.gsql",
        "query_router": "src/utils/query_router.py",
        "context_compression": "src/utils/context_compression.py",
        "who_guideline_loader": "src/scripts/data_collection/who_guidelines_loader.py",
        "entity_extraction": "src/scripts/entity_extraction/extract_and_load.py",
        "gsd_checklist": ".planning/GSD-IMPLEMENTATION-CHECKLIST.md",
    }

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    artifacts = {
        name: {
            "path": path,
            "present": os.path.exists(os.path.join(root, path)),
        }
        for name, path in files.items()
    }

    return {
        "thesis": "Polypharmacy and symptom-to-diagnosis reasoning are graph traversal problems.",
        "benchmark": {
            "total_questions": len(BENCHMARK_QUERIES),
            "categories": categories,
            "target_accuracy": {"llm_judge": 0.90, "bertscore": 0.55},
            "named_finding": "The Cascade Collapse",
        },
        "pipelines": [
            {"name": "LLM-Only", "status": "implemented", "role": "training-knowledge baseline"},
            {"name": "Basic RAG", "status": "implemented", "role": "Pinecone vector retrieval baseline"},
            {"name": "GraphRAG", "status": "implemented", "role": "TigerGraph route-aware graph traversal"},
        ],
        "graph_features": [
            "Clinical graph schema with drugs, diseases, symptoms, enzymes, adverse events, and guidelines",
            "Polypharmacy GSQL traversal for direct, enzyme-mediated, and adverse-event cascades",
            "Route-aware retrievers for interaction, diagnosis, contradiction, temporal, multihop, counterfactual, and cross-entity queries",
            "Compressed structured JSON graph context for token reduction",
            "Dashboard clinical warnings and graph path surfacing",
        ],
        "artifacts": artifacts,
    }


def _run_rag_ingest():
    from src.pipelines.pipeline2_basic_rag.ingest import ingest_documents
    kb_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "medical")
    ingest_documents(input_path=kb_path)


def _run_graphrag_ingest():
    from src.graphrag.pipeline.ingest import ingest_documents
    ingest_documents("./data/processed", format="csv")


@app.post("/ingest/rag", response_model=IngestStatus)
async def ingest_rag(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_rag_ingest)
    return IngestStatus(pipeline="basic-rag", status="started", message="Ingest running")


@app.post("/ingest/graphrag", response_model=IngestStatus)
async def ingest_graphrag(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_graphrag_ingest)
    return IngestStatus(pipeline="graphrag", status="started", message="Ingest running")


@app.get("/knowledge-base")
async def get_knowledge_base():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def estimate_tokens(text: str) -> int:
        return int(len(text) / 4)

    def file_info(path: str) -> dict:
        stat = os.stat(path)
        return {
            "source_path": os.path.relpath(path, root).replace("\\", "/"),
            "last_modified": stat.st_mtime,
            "size_bytes": stat.st_size,
        }

    def tigergraph_status() -> dict:
        status = {
            "available": False,
            "counts": {},
            "index_ready": False,
            "message": "TigerGraph status not checked",
        }
        try:
            from src.utils.tigergraph_ingest import _connection

            conn = _connection()
            for vertex_type in ["Document", "Content", "DocumentChunk", "Entity", "Community"]:
                try:
                    status["counts"][vertex_type] = conn.getVertexCount(vertex_type)
                except Exception:
                    status["counts"][vertex_type] = None
            status["available"] = True
            status["index_ready"] = bool(status["counts"].get("DocumentChunk", 0))
            status["message"] = (
                "GraphRAG chunks are searchable"
                if status["index_ready"]
                else "Raw documents exist, but GraphRAG chunks have not been built yet"
            )
        except Exception as exc:
            status["message"] = sanitize_error(f"TigerGraph status unavailable: {exc}")
        return status

    def graph_preview(source_counts: dict, tg_status: dict) -> dict:
        counts = tg_status.get("counts", {})
        nodes = [
            {"id": "Corpus", "x": 280, "y": 230, "type": "Entity"},
            {"id": "Document", "x": 150, "y": 135, "type": "Concept", "count": counts.get("Document", 0)},
            {"id": "Content", "x": 410, "y": 135, "type": "Concept", "count": counts.get("Content", 0)},
            {"id": "Chunk", "x": 150, "y": 335, "type": "Action", "count": counts.get("DocumentChunk", 0)},
            {"id": "Entity", "x": 410, "y": 335, "type": "Entity", "count": counts.get("Entity", 0)},
            {"id": "Community", "x": 285, "y": 420, "type": "Observation", "count": counts.get("Community", 0)},
        ]
        links = [
            {"source": "Corpus", "target": "Document"},
            {"source": "Document", "target": "Content"},
            {"source": "Content", "target": "Chunk"},
            {"source": "Chunk", "target": "Entity"},
            {"source": "Entity", "target": "Community"},
        ]
        for i, (source, count) in enumerate(sorted(source_counts.items())[:6]):
            nodes.append(
                {
                    "id": source,
                    "x": 75 + (i % 3) * 225,
                    "y": 45 + (i // 3) * 405,
                    "type": "Concept",
                    "count": count,
                }
            )
            links.append({"source": source, "target": "Corpus"})
        return {"nodes": nodes, "links": links}

    def with_runtime_metadata(payload: dict) -> dict:
        tg_status = tigergraph_status()
        payload["tigergraph"] = tg_status
        payload["index_status"] = "ready" if tg_status.get("index_ready") else "needs_rebuild"
        payload["graph"] = graph_preview(payload.get("source_counts", {}), tg_status)
        return payload

    unified_path = os.path.join(root, "data", "processed", "unified_corpus.json")
    corpus_text_path = os.path.join(root, "data", "processed", "corpus_text.txt")
    graphrag_jsonl_path = os.path.join(root, "data", "medical", "graphrag_ingest.jsonl")
    legacy_kb_path = os.path.join(root, "data", "medical", "knowledge_base.txt")

    if os.path.exists(unified_path):
        try:
            with open(unified_path, "r", encoding="utf-8") as f:
                docs = json.load(f)

            source_counts = {}
            for doc in docs:
                source = doc.get("source") or doc.get("source_type") or "unknown"
                source_counts[source] = source_counts.get(source, 0) + 1

            # Return metadata only, not the full corpus content
            return with_runtime_metadata({
                "local_corpus_records": len(docs),
                "source_counts": source_counts,
                "status": "dynamic_processed_corpus",
                "architecture": "Generated corpus from DrugBank/seed drugs, disease-symptom mappings, WHO guidelines, and any cached PubMed/FDA data; indexed by Pinecone and traversed by TigerGraph GraphRAG.",
                **file_info(unified_path),
            })
        except Exception as e:
            return {"content": f"Error reading processed corpus: {str(e)}", "total_tokens": 0, "status": "error"}

    if os.path.exists(corpus_text_path):
        try:
            with open(corpus_text_path, "r", encoding="utf-8") as f:
                content = f.read()
            return with_runtime_metadata({
                "local_corpus_records": content.count("\n\n") + 1 if content else 0,
                "source_counts": {"processed_text": 1},
                "status": "dynamic_processed_text",
                "architecture": "Generated text corpus from the data collection pipeline; ready for Pinecone ingestion and GraphRAG extraction.",
                **file_info(corpus_text_path),
            })
        except Exception as e:
            return {"error": f"Error reading processed text corpus: {str(e)}", "status": "error"}

    if os.path.exists(graphrag_jsonl_path):
        try:
            records = []
            with open(graphrag_jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            return with_runtime_metadata({
                "local_corpus_records": len(records),
                "source_counts": {"graphrag_jsonl": len(records)},
                "status": "dynamic_graphrag_ingest",
                "architecture": "GraphRAG JSONL ingest file generated from local medical knowledge; use the collection pipeline for the full clinical corpus.",
                **file_info(graphrag_jsonl_path),
            })
        except Exception as e:
            return {"error": f"Error reading GraphRAG ingest JSONL: {str(e)}", "status": "error"}

    kb_path = legacy_kb_path
    if not os.path.exists(kb_path):
        return with_runtime_metadata({
            "error": "No knowledge base found. Run python scripts/data_collection/collect_all.py to build the dynamic corpus.",
            "local_corpus_records": 0,
            "source_counts": {},
            "status": "missing",
        })
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()
            return with_runtime_metadata({
                "local_corpus_records": content.count("Disease:"),
                "source_counts": {"legacy_medical_text": 1},
                "status": "legacy_static_file",
                "architecture": "Legacy static demo file. Run python scripts/data_collection/collect_all.py to replace this with the dynamic multi-source corpus.",
                **file_info(kb_path),
            })
    except Exception as e:
        return {"error": f"Error: {str(e)}", "status": "error"}


@app.get("/api/knowledge-base")
async def get_knowledge_base_alias():
    return await get_knowledge_base()


@app.get("/metrics/summary")
async def metrics_summary():
    results_dir = "./results"
    os.makedirs(results_dir, exist_ok=True)
    reports = []
    for filepath in sorted(glob.glob(f"{results_dir}/benchmark_*.json")):
        with open(filepath) as f:
            reports.append(json.load(f))
    if not reports:
        return {"total_reports": 0, "message": "No reports found."}
    latest = reports[-1]
    return {
        "total_reports": len(reports),
        "latest_generated_at": latest.get("generated_at"),
        "total_queries": latest.get("total_queries"),
        "summary": latest.get("summary"),
        "accuracy": {
            pipeline: {
                "judge_pass_rate": data["llm_judge"]["pass_rate"],
                "bertscore_f1": data["bertscore"]["f1_rescaled"],
                "max_bonus": data["max_bonus_achieved"],
            }
            for pipeline, data in latest.get("accuracy", {}).items()
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
