# Architecture — Medical GraphRAG Inference Benchmark

**Version:** 1.1.0

---

## System overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     React dashboard (port 3000)                      │
│              POST /compare/stream  { query, top_k, namespace }       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI backend (port 8080)                       │
│         ThreadPoolExecutor / asyncio — 3 pipelines in parallel       │
└───────────┬───────────────────┬───────────────────┬────────────────┘
            │                   │                   │
            ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────────┐   ┌──────────────────────┐
│  Pipeline 1   │   │    Pipeline 2     │   │     Pipeline 3       │
│   LLM only    │   │    Basic RAG      │   │      GraphRAG        │
│    Gemma 4    │   │ Pinecone + Gemma 4│   │ GraphRAG REST :8000  │
│ (no context)  │   │ + Llama-Embed-v2  │   │ → TigerGraph Savanna │
└───────────────┘   └───────────────────┘   └──────────────────────┘
```

---

## Data flow

### Ingest (run once)

```
Medical CSVs  →  prepare_medical_data.py  →  data/medical/knowledge_base.txt
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 Pipeline 2 ingest                 Pipeline 3 ingest
 ─────────────────                 ─────────────────
 RecursiveCharacterTextSplitter    POST /documents/batch
 chunk_size=1000, overlap=100      → GraphRAG Docker service
        │                               │
 Llama-text-embed-v2                    Entity + relationship extraction
 (Pinecone Inference)                   │
        │                               │
        ▼                               ▼
 Pinecone (namespace: medical-rag)   TigerGraph graph
```

Default ingest entry points:

- `python pipelines/pipeline2_basic_rag/ingest.py --path ./data/medical`
- `python pipelines/pipeline3_graphrag/ingest.py --path ./data/medical`

### Query (per request)

Example: *"What are the symptoms of Malaria?"*

| Pipeline | Steps | Token profile |
|----------|--------|---------------|
| **1 — LLM only** | Prompt with question only → `gemma-4-26b-a4b-it` REST | Low prompt; no grounded context |
| **2 — Basic RAG** | Embed query → Pinecone (dynamic top-K) → prompt with chunks → `gemma-4-26b-a4b-it` REST | Higher (multiple chunks in prompt) |
| **3 — GraphRAG** | `POST /query` to GraphRAG service (`hybrid`, `hop_depth=2`) | Lower than P2 when graph context is selective |

The dashboard computes **token reduction %** as `(P2 total tokens − P3 total tokens) / P2 total tokens`.

---

## Component details

### Pinecone (Pipeline 2)

| Setting | Value |
|---------|--------|
| Index | `PINECONE_INDEX_NAME` (default `graphrag-benchmark`) |
| Namespace | `medical-rag` (dashboard default) |
| Embeddings | `models/embedding-001` |
| Index dimension | **1024** (Optimized for medical context) |
| Metric | cosine |
| Chunking | `CHUNK_SIZE=1000`, `CHUNK_OVERLAP=100` |

### TigerGraph GraphRAG (Pipeline 3)

The `tigergraph/graphrag` container connects to TigerGraph Savanna (`TG_HOST`, credentials in `.env`) and exposes:

- `POST /documents/batch` — ingest
- `POST /query` — retrieve + generate with `retriever` and `hop_depth`

Internal graph schema (entities, communities, document links) is managed by the GraphRAG service.

### FastAPI endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/compare` | Run all 3 pipelines; optional `ground_truth` for accuracy |
| `POST` | `/compare/stream` | SSE streaming for live UI updates |
| `POST` | `/ingest/rag` | Background Pinecone ingest from `data/medical` |
| `POST` | `/ingest/graphrag` | Background GraphRAG ingest |
| `GET` | `/knowledge-base` | Medical KB text for sidebar |
| `GET` | `/health` | Health check |
| `GET` | `/metrics/summary` | Latest `results/benchmark_*.json` summary |

---

## Directory structure

```text
graphrag-benchmark/
├── data/medical/                   # knowledge_base.txt (+ optional CSVs)
├── data/wikipedia/                 # optional legacy Wikipedia articles
├── pipelines/
│   ├── pipeline1_llm_only.py
│   ├── pipeline2_basic_rag/{ingest,query}.py
│   └── pipeline3_graphrag/{ingest,query}.py
├── evaluation/
│   ├── accuracy.py
│   ├── benchmark_runner.py
│   ├── llm_judge.py
│   └── bertscore_eval.py
├── dashboard/backend/main.py
├── dashboard/frontend/src/
├── utils/{metrics,retry,security}.py
├── results/                        # benchmark JSON output
├── docker-compose.yml
└── requirements.txt
```

---

## Deployment (`docker-compose.yml`)

| Service | Port | Role |
|---------|------|------|
| `graphrag` | 8000 | TigerGraph GraphRAG API |
| `backend` | 8080 | FastAPI |
| `frontend` | 3000 | React UI |

`GRAPHRAG_SERVICE_URL` inside the backend container is `http://graphrag:8000`.

---

## Metrics

- Token counts: **tiktoken** `cl100k_base` in `utils/metrics.py` (P1/P2); P3 may use counts returned by the GraphRAG service.
- Cost estimate: `(prompt + completion) / 1e6 × 0.075` USD (approximate; same formula across pipelines for comparison).

Target from the PRD: **40–70%** fewer tokens for GraphRAG vs Basic RAG on comparable medical questions, without sacrificing accuracy (LLM-judge + BERTScore).
