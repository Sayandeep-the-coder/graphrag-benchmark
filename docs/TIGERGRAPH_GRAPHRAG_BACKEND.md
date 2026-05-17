# TigerGraph GraphRAG Backend Contract

This benchmark uses the official TigerGraph GraphRAG backend in `graphrag/`.
The benchmark should not call invented endpoints such as `/query` or
`/documents/batch` at the service root.

## Services

- Official GraphRAG backend: `http://localhost:8000`
- Benchmark backend: `http://localhost:8080`
- Official GraphRAG UI dev proxy: `/ui/* -> http://localhost:8000`

In Docker, the benchmark backend reaches GraphRAG at:

```text
http://graphrag:8000
```

## Authentication

Most non-UI GraphRAG endpoints use HTTP Basic auth with the TigerGraph database
username and password:

```http
Authorization: Basic base64(TG_USERNAME:TG_PASSWORD)
```

The UI login endpoint is only for the official UI:

```http
POST /ui/ui-login
```

Programmatic benchmark code should use the direct graph endpoints below.

## Query Paths

Knowledge-graph RAG answer generation:

```http
POST /{TG_GRAPH_NAME}/graphrag/answerquestion
Content-Type: application/json

{
  "question": "What is aspirin?",
  "method": "hybrid",
  "method_params": {
    "indices": ["DocumentChunk", "Entity"],
    "top_k": 5,
    "num_hops": 2,
    "num_seen_min": 2,
    "verbose": false
  }
}
```

Retrieval-only debug path:

```http
POST /{TG_GRAPH_NAME}/graphrag/search
```

Natural-language graph assistant path:

```http
POST /{TG_GRAPH_NAME}/query

{
  "query": "How many DocumentChunk vertices are there?",
  "rag_method": "hybridsearch"
}
```

The official UI chat uses:

```http
GET /ui/{TG_GRAPH_NAME}/query?q=...&rag_pattern=...
WS  /ui/{TG_GRAPH_NAME}/chat
```

## Ingestion Paths

The official automation path is pyTigerGraph:

```python
conn.ai.configureGraphRAGHost("http://localhost:8000")
conn.ai.initializeGraphRAG()
res = conn.ai.createDocumentIngest(
    data_source="local",
    data_source_config={"data_path": "./data/tg_tutorials.jsonl"},
    file_format="json",
)
conn.ai.runDocumentIngest(res["load_job_id"], res["data_source_id"], res["data_path"])
conn.ai.forceConsistencyUpdate("graphrag")
```

For this benchmark on Savanna, `src/utils/tigergraph_ingest.py` uses
`runLoadingJobWithData(...)` so files do not need to exist inside TigerGraph
Cloud. After loading, it calls `conn.ai.forceConsistencyUpdate("graphrag")`.

Equivalent service endpoints, when the files are available to the backend:

```http
POST /{TG_GRAPH_NAME}/graphrag/create_ingest
POST /{TG_GRAPH_NAME}/graphrag/ingest
GET  /{TG_GRAPH_NAME}/graphrag/forceupdate
```

The `/ui/{graph}/uploads`, `/ui/{graph}/create_ingest`,
`/ui/{graph}/ingest`, and `/ui/{graph}/rebuild_graph` endpoints are admin UI
wrappers around the same backend logic.
