# Setup Guide

Installation from zero to a running medical benchmark dashboard.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|--------|
| Python | 3.11+ | Backend + pipelines |
| Node.js | 18+ | Frontend |
| Docker + Compose | 24+ / 2.x | GraphRAG service (recommended) |
| Git | any | Clone repo |

---

## Step 1 — API keys and accounts

### Google Gemini

1. [aistudio.google.com](https://aistudio.google.com) → API key → `GEMINI_API_KEY`

Used for: P1/P2 (`gemma-4-26b-a4b-it`), GraphRAG container LLM config.

### Pinecone

1. [pinecone.io](https://pinecone.io) → API key
2. Create a **serverless** index:
   - Name: `graphrag-benchmark` (or set `PINECONE_INDEX_NAME`)
   - **Dimensions: 1024** (Optimized for `llama-text-embed-v2`)
   - Metric: cosine
   - Region: e.g. `us-east-1`

Or run:

```bash
python src/scripts/create_pinecone_index.py
```

### TigerGraph Savanna

See **[TIGERGRAPH_CLOUD_SETUP.md](TIGERGRAPH_CLOUD_SETUP.md)** for the full manual (workspace, database user, roles, `.env`, config generation, Docker, and verification).

Summary: [tgcloud.io](https://tgcloud.io) → workspace **Connect** URL → database user with schema-write role → set `TG_*` in `.env` → `python src/scripts/generate_server_config.py` → `python src/scripts/test_tigergraph_connection.py`

### HuggingFace (accuracy evaluation)

1. [huggingface.co](https://huggingface.co) → read token → `HF_TOKEN`

---

## Step 2 — Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/graphrag-benchmark.git
cd graphrag-benchmark
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=graphrag-benchmark
TG_HOST=https://your-instance.tgcloud.io
TG_USERNAME=tigergraph
TG_PASSWORD=...
TG_GRAPH_NAME=GraphRAG
TG_GET_TOKEN=true
GRAPHRAG_SERVICE_URL=http://localhost:8000
HF_TOKEN=...
PORT=8080
```

---

## Step 3 — Python environment

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

---

## Step 4 — Medical dataset

Place medical CSVs under `data/medical/` (if not already present), then:

```bash
python src/scripts/prepare_medical_data.py
```

Output: `data/medical/knowledge_base.txt`

Verify size:

```bash
python src/scripts/count_tokens.py --path data/medical/knowledge_base.txt
```

---

## Step 5 — GraphRAG service

**Option A — Docker Compose (recommended)**

From project root:

```bash
python src/scripts/generate_server_config.py
python src/scripts/test_tigergraph_connection.py
docker compose up -d graphrag
curl http://localhost:8000/health
```

**Option B — Standalone GraphRAG repo**

Clone [tigergraph/graphrag](https://github.com/tigergraph/graphrag), configure `.env` with Gemini + TigerGraph credentials, and run its compose stack. Set `GRAPHRAG_SERVICE_URL` accordingly.

---

## Step 6 — Ingest

```bash
python src/pipelines/pipeline2_basic_rag/ingest.py --path ./data/medical --namespace medical-rag
python src/graphrag/pipeline/ingest.py --path ./data/medical
```

Expect minutes, not hours, for the medical KB (vs. multi-million-token Wikipedia runs).

---

## Step 7 — Dashboard

```bash
# Terminal 1
uvicorn src.server.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2
cd src/frontend && npm install && npm run dev
```

Open `http://localhost:3000`.

**All-in-one:**

```bash
docker compose up
```

---

## Verify

```bash
python src/scripts/smoke_test.py
```

---

## Optional — Wikipedia dataset (legacy)

For the original hackathon Wikipedia benchmark:

1. Kaggle API + `src/scripts/extract_wikipedia.py` → `data/wikipedia/`
2. Ingest with `--path ./data/wikipedia` and namespace `wikipedia-2025` (if you maintain a separate Pinecone namespace)

The default medical dashboard uses `data/medical` and namespace `medical-rag`.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Pinecone dimension mismatch | Recreate index at **1024** for `llama-text-embed-v2`: `python src/scripts/recreate_pinecone_index.py` |
| Model 404 / API Error | Confirm model IDs (`models/gemma-4-26b-a4b-it`) and ensure API key has access to v1beta endpoints |
| TigerGraph 401 / REST-10016 | See [TIGERGRAPH_CLOUD_SETUP.md](TIGERGRAPH_CLOUD_SETUP.md); set `TG_GET_TOKEN=true`, regenerate config, verify with `test_tigergraph_connection.py` |
| TigerGraph permission denied | Grant DB user **globaldesigner** or **superuser** in Savanna, then `docker compose restart graphrag` |
| GraphRAG connection error in UI | `docker compose logs graphrag`; ensure `GRAPHRAG_SERVICE_URL` reachable from backend |
| Gemma 500 on P2 | REST path is already used; reduce `top_k` or chunk size |
| BERTScore CUDA error | Eval uses `device="cpu"` in `bertscore_eval.py` |
| Empty P2 answers | Re-run ingest; confirm namespace `medical-rag` matches dashboard |
