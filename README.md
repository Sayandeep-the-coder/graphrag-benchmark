# Medical GraphRAG Inference Benchmark

A three-pipeline LLM inference benchmark that evaluates how GraphRAG (TigerGraph) reduces token consumption and improves context relevance compared to Basic RAG (Pinecone) on a custom **medical dataset**.

The dashboard runs all three pipelines on the same query and compares latency, token usage, cost, and answer quality side by side.

## The Pipelines

| # | Pipeline | Generation model | Retrieval | Expected token profile |
|---|----------|------------------|-----------|----------------------|
| **1** | **LLM-Only** | `models/gemma-4-26b-a4b-it` | None (baseline; hallucination risk) | Lowest prompt tokens |
| **2** | **Basic RAG** | `models/gemma-4-26b-a4b-it` | Pinecone + `llama-text-embed-v2` | Highest (retrieved chunks in prompt) |
| **3** | **GraphRAG** | TigerGraph GraphRAG service (Docker) | Multi-hop graph (`hybrid` / `community` / `sibling`) | Medium (graph-selected context) |

Pipeline 2 uses **dynamic top-K**: it fetches up to 15 vector matches, then keeps chunks while similarity stays above `0.2` and scores do not drop more than `0.05` between consecutive hits (capped at `top_k`, default 5).

> [!NOTE]
> Pipelines 1 and 2 call the Google GenAI **REST API** (not the SDK `generate_content` path) for stable parsing with Gemma on medical queries. Pipeline 3 delegates generation to the TigerGraph GraphRAG container.

## Tech Stack

| Layer | Technology |
|-------|------------|
| LLM (P1) | `models/gemma-4-26b-a4b-it` |
| LLM (P2) | `models/gemma-4-26b-a4b-it` |
| Embeddings (P2) | `llama-text-embed-v2` (Pinecone Inference) |
| Vector DB | Pinecone Serverless, namespace `medical-rag` |
| Graph DB | TigerGraph Savanna + `tigergraph/graphrag` Docker image |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + Tailwind CSS + Recharts |

---

## Setup

### 1. Environment variables

```bash
cp .env.example .env
```

Required:

- `GEMINI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME` (e.g. `graphrag-benchmark`)
- `TG_HOST`, `TG_PASSWORD` (for GraphRAG / TigerGraph)
- `GRAPHRAG_SERVICE_URL` (default `http://localhost:8000`)

Create a Pinecone index whose **dimension matches** `PINECONE_EMBEDDING_DIMENSION` (default 1024). See `src/scripts/create_pinecone_index.py`.

### 2. Python

```bash
python -m venv venv
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Medical data

```bash
python src/scripts/prepare_medical_data.py
```

Produces `data/medical/knowledge_base.txt`.

### 4. Ingest

```bash
python src/pipelines/pipeline2_basic_rag/ingest.py --path ./data/medical --namespace medical-rag
python src/graphrag/pipeline/ingest.py --path ./data/medical
```

Optional token check:

```bash
python src/scripts/count_tokens.py --path data/medical/knowledge_base.txt
```

### 5. Dashboard

```bash
uvicorn src.server.main:app --host 0.0.0.0 --port 8080 --reload
```

```bash
cd src/frontend && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Or run the full stack: `docker compose up`.

---

## Project structure

```text
graphrag-benchmark/
├── data/                         # CSVs + knowledge_base.txt
├── src/
│   ├── graphrag/                 # GraphRAG specific logic (P3)
│   ├── pipelines/                # P1 (LLM-Only) and P2 (Basic RAG)
│   ├── server/                   # FastAPI backend
│   ├── frontend/                 # React benchmark UI
│   ├── evaluation/               # Accuracy + batch benchmark_runner
│   ├── scripts/                  # Data prep, Pinecone helpers, smoke_test
│   └── utils/                    # Shared metrics, retry, security
├── results/                      # Saved benchmark reports
└── docker-compose.yml            # Full stack orchestrator
```

## Contributing

1. **Dynamic top-K** (`pipeline2_basic_rag/query.py`): keep `min_score_threshold` and `score_drop_threshold` when changing retrieval.
2. **Graceful degradation** (`pipeline3_graphrag/query.py`): return user-safe errors if GraphRAG is down; do not crash the API.
3. **Dependencies**: add new packages to `requirements.txt`.

See [SETUP.md](SETUP.md), [TIGERGRAPH_CLOUD_SETUP.md](TIGERGRAPH_CLOUD_SETUP.md) (Savanna connection), [ARCHITECTURE.md](ARCHITECTURE.md), [PIPELINES.md](PIPELINES.md), and [EVALUATION.md](EVALUATION.md) for detail.

### Optional: Wikipedia dataset (legacy)

Scripts under `scripts/extract_wikipedia.py` and `data/wikipedia/` support the original hackathon Wikipedia benchmark. The default dashboard and ingest paths use **medical** data.
