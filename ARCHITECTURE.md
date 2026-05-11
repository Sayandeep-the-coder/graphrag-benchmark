# Architecture — GraphRAG Inference Benchmark

**Version:** 1.0.0

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER / DASHBOARD                             │
│                    React + Tailwind Frontend                        │
│            POST /compare { query, ground_truth? }                   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                             │
│                        /compare endpoint                            │
│              Spawns 3 pipeline calls in parallel                    │
└───────────┬───────────────────┬───────────────────┬────────────────┘
            │                   │                   │
            ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────────┐   ┌──────────────────────┐
│  Pipeline 1   │   │    Pipeline 2     │   │     Pipeline 3       │
│   LLM Only    │   │    Basic RAG      │   │      GraphRAG        │
│               │   │   (Pinecone)      │   │   (TigerGraph)       │
└──────┬────────┘   └────────┬──────────┘   └──────────┬───────────┘
       │                     │                          │
       ▼                     ▼                          ▼
┌─────────────┐   ┌──────────────────┐   ┌─────────────────────────┐
│ Gemini 1.5  │   │ Pinecone Index   │   │  TigerGraph GraphRAG    │
│    Flash    │   │  (vector search) │   │     Service (Docker)    │
└─────────────┘   └────────┬─────────┘   └──────────┬──────────────┘
                            │                        │
                            ▼                        ▼
                  ┌──────────────────┐   ┌─────────────────────────┐
                  │  Gemini 1.5      │   │  TigerGraph Savanna     │
                  │  Flash           │   │  (Knowledge Graph DB)   │
                  └──────────────────┘   └─────────────────────────┘
```

---

## Data Flow

### Ingest Phase (Run Once)

```
Wikipedia Dataset (raw .txt files)
            │
            ├──────────────────────────────────┐
            │                                  │
            ▼                                  ▼
  Pipeline 2 Ingest                  Pipeline 3 Ingest
  ─────────────────                  ─────────────────
  RecursiveCharacterTextSplitter     POST /documents →
  chunk_size=512, overlap=64         TigerGraph GraphRAG service
            │                                  │
            ▼                                  ▼
  all-MiniLM-L6-v2 embeddings        Auto entity extraction
            │                        Auto relationship mapping
            ▼                                  │
  Pinecone Serverless Index ◄──────────────────┘
  (vectors stored)                   TigerGraph DB
                                     (nodes + edges stored)
```

### Query Phase (Per Request)

```
User Query: "Which scientists collaborated on quantum computing papers?"

Pipeline 1 (LLM Only)
├── Prompt: "Answer: {query}"
├── No context retrieved
├── Tokens: ~500 (high hallucination risk)
└── Gemini → answer

Pipeline 2 (Basic RAG / Pinecone)
├── Embed query → Pinecone similarity search → top 5 chunks
├── Prompt: "Context: {5 chunks}\nAnswer: {query}"
├── Tokens: ~1800 (chunks often irrelevant/redundant)
└── Gemini → answer

Pipeline 3 (GraphRAG / TigerGraph)
├── Query → GraphRAG service → multi-hop graph traversal
│   ├── Entity: "quantum computing" → linked scientists
│   ├── Hop 1: scientists → their papers
│   └── Hop 2: papers → co-authors
├── Prompt: "Facts: {precise entities}\nAnswer: {query}"
├── Tokens: ~400 (precise, no noise)
└── Gemini → answer

Result: 78% token reduction, same or better accuracy
```

---

## Component Details

### Pinecone Setup (Pipeline 2)

```
Index name:    graphrag-benchmark
Dimension:     384 (all-MiniLM-L6-v2 output)
Metric:        cosine
Environment:   serverless (free tier)
Region:        us-east-1 (AWS)
Namespace:     wikipedia-2025
```

### TigerGraph Schema (Pipeline 3)

```
Vertex Types:
  Document    { doc_id, title, content, chunk_index }
  Entity      { entity_id, name, type, description }
  Community   { community_id, summary, level }

Edge Types:
  MENTIONS         Document → Entity
  RELATED_TO       Entity   → Entity
  BELONGS_TO       Entity   → Community
  NEXT_CHUNK       Document → Document
```

### FastAPI Endpoints

```
POST /compare           → runs all 3 pipelines, returns unified metrics
POST /ingest/rag        → triggers Pinecone ingest for P2
POST /ingest/graphrag   → triggers TigerGraph ingest for P3
GET  /health            → service health check
GET  /metrics/summary   → aggregated benchmark stats
```

---

## Directory Structure

```
graphrag-benchmark/
├── data/
│   └── wikipedia/                  # raw .txt files (2M+ tokens)
├── pipelines/
│   ├── pipeline1_llm_only.py
│   ├── pipeline2_basic_rag/
│   │   ├── ingest.py               # chunk + embed + push to Pinecone
│   │   └── query.py                # search Pinecone + call Gemini
│   └── pipeline3_graphrag/
│       ├── ingest.py               # push docs to GraphRAG service
│       └── query.py                # query GraphRAG REST API
├── evaluation/
│   ├── accuracy.py                 # LLM-as-Judge + BERTScore
│   └── benchmark_runner.py         # batch query runner
├── dashboard/
│   ├── backend/
│   │   └── main.py                 # FastAPI app
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx
│       │   ├── PipelineCard.jsx
│       │   └── MetricsTable.jsx
│       └── package.json
├── graphrag/                       # cloned TigerGraph GraphRAG repo
├── utils/
│   ├── metrics.py                  # token counter, cost calculator
│   └── retry.py                    # exponential backoff
├── results/                        # JSON benchmark outputs
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── PRD.md
├── ARCHITECTURE.md
├── README.md
├── SETUP.md
├── PIPELINES.md
├── EVALUATION.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── BUILD_PROMPT.md
```

---

## Deployment

```yaml
# docker-compose.yml (simplified)
services:
  graphrag:
    image: tigergraph/graphrag:latest
    ports: ["8000:8000"]
    env_file: .env

  dashboard-backend:
    build: ./dashboard/backend
    ports: ["8080:8080"]
    depends_on: [graphrag]

  dashboard-frontend:
    build: ./dashboard/frontend
    ports: ["3000:3000"]
    depends_on: [dashboard-backend]
```

---

## Token Reduction Model

```
Token cost formula:
  cost = (prompt_tokens + completion_tokens) × price_per_million

Expected benchmark results:
  Pipeline 1 (LLM Only):  ~500  tokens  — no context, vague answers
  Pipeline 2 (Basic RAG): ~1800 tokens  — 5 chunks, noisy context
  Pipeline 3 (GraphRAG):  ~400  tokens  — precise graph facts only

Token reduction (P3 vs P2): (1800 - 400) / 1800 = 77.8%
```
