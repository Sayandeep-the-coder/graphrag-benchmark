# Setup Guide

Complete installation walkthrough from zero to running dashboard.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | python.org |
| Docker | 24+ | docker.com |
| Docker Compose | 2.x | included with Docker Desktop |
| Node.js | 18+ | nodejs.org |
| Git | any | git-scm.com |

---

## Step 1 — Accounts & API Keys

### Google Gemini (free)
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Create API key
3. Free tier: 15 req/min, 1M tokens/day — enough for hackathon

### Pinecone (free)
1. Go to [pinecone.io](https://pinecone.io) → Sign up free
2. Dashboard → API Keys → copy your key
3. Create index:
   - Name: `graphrag-benchmark`
   - Dimensions: `3072` (for Gemini `models/gemini-embedding-001`)
   - Metric: `cosine`
   - Plan: Serverless (free)
   - Region: `us-east-1`

### TigerGraph Savanna (free ~$60 credits)
1. Go to [tgcloud.io](https://tgcloud.io) → Sign up
2. Create new cluster → note host URL, username, password
3. Credits auto-applied — more available on request

### HuggingFace (free — for accuracy eval)
1. Go to [huggingface.co](https://huggingface.co) → Sign up
2. Settings → Access Tokens → New token (read)

### Kaggle (for dataset download)
1. Go to [kaggle.com](https://kaggle.com) → Account → API → Download `kaggle.json`
2. Place at `~/.kaggle/kaggle.json`

---

## Step 2 — Clone Repos

```bash
# Main project
git clone https://github.com/YOUR_USERNAME/graphrag-benchmark.git
cd graphrag-benchmark

# TigerGraph GraphRAG service (goes inside project)
git clone https://github.com/tigergraph/graphrag.git
```

---

## Step 3 — Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# LLM
GEMINI_API_KEY=your_gemini_api_key_here

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=graphrag-benchmark
PINECONE_ENVIRONMENT=us-east-1

# TigerGraph
TG_HOST=https://your-instance.tgcloud.io
TG_USERNAME=tigergraph
TG_PASSWORD=your_password_here
TG_GRAPH_NAME=GraphRAG

# TigerGraph GraphRAG Service (Docker)
GRAPHRAG_SERVICE_URL=http://localhost:8000

# HuggingFace (accuracy eval)
HF_TOKEN=your_huggingface_token_here

# App
PORT=8080
```

---

## Step 4 — Python Dependencies

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

`requirements.txt`:
```
fastapi==0.111.0
uvicorn==0.30.1
pinecone-client==3.2.2
sentence-transformers==2.7.0
langchain==0.2.6
langchain-community==0.2.6
tiktoken==0.7.0
bert-score==0.3.13
google-generativeai==0.5.4
python-dotenv==1.0.1
requests==2.32.3
httpx==0.27.0
pandas==2.2.2
tqdm==4.66.4
```

---

## Step 5 — Dataset Setup

```bash
# Download Wikipedia dataset
kaggle datasets download jkkphys/english-wikipedia-articles-20170820-sqlite
unzip english-wikipedia-articles-20170820-sqlite.zip -d ./data/raw/

# Extract text articles to ./data/wikipedia/
python scripts/extract_wikipedia.py

# Verify token count
python scripts/count_tokens.py
# Should print: Total tokens: 2,300,000+
```

`scripts/extract_wikipedia.py`:
```python
import sqlite3, os

conn = sqlite3.connect("./data/raw/articles.db")
cursor = conn.cursor()
cursor.execute("SELECT title, text FROM articles LIMIT 5000")  # ~2M tokens

os.makedirs("./data/wikipedia", exist_ok=True)

for i, (title, text) in enumerate(cursor.fetchall()):
    filename = f"./data/wikipedia/article_{i:05d}.txt"
    with open(filename, "w") as f:
        f.write(f"# {title}\n\n{text}")

conn.close()
print(f"Extracted {i+1} articles")
```

---

## Step 6 — Start TigerGraph GraphRAG Service

```bash
cd graphrag

# Configure GraphRAG service
cp .env.example .env
# Add your GEMINI_API_KEY, TG_HOST, TG_USERNAME, TG_PASSWORD

docker-compose up -d

# Verify running
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## Step 7 — Ingest Data

```bash
# Pipeline 2: chunk + embed + push to Pinecone
# Estimated time: 15-30 min for 2M tokens
python pipelines/pipeline2_basic_rag/ingest.py

# Pipeline 3: push to TigerGraph GraphRAG
# Estimated time: 30-60 min for 2M tokens (entity extraction happening)
python pipelines/pipeline3_graphrag/ingest.py
```

Watch progress:
```
[Pipeline 2] Chunking... 5000 articles → 45,231 chunks
[Pipeline 2] Embedding batch 1/453...
[Pipeline 2] Pushing to Pinecone... Done. 45,231 vectors stored.

[Pipeline 3] Ingesting article 1/5000...
[Pipeline 3] Entities extracted: 12,483 | Relationships: 34,217
[Pipeline 3] Knowledge graph built. Ready.
```

---

## Step 8 — Launch Dashboard

```bash
# Terminal 1: Backend
uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Frontend
cd dashboard/frontend
npm install
npm run dev
```

Open `http://localhost:3000`

---

## Verify Everything Works

```bash
python scripts/smoke_test.py
```

Expected output:
```
✅ Gemini API: connected
✅ Pinecone: 45,231 vectors in index
✅ TigerGraph GraphRAG service: healthy
✅ Pipeline 1: answered in 1.2s
✅ Pipeline 2: answered in 4.8s (5 chunks retrieved)
✅ Pipeline 3: answered in 3.1s (multi-hop traversal: 2 hops)
✅ All systems go.
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Pinecone index not found` | Create index with correct dimensions (384) |
| `TigerGraph 401 Unauthorized` | Check TG_USERNAME and TG_PASSWORD in .env |
| `Gemini 429 Too Many Requests` | Exponential backoff already in `utils/retry.py` |
| `GraphRAG service 503` | `docker-compose logs graphrag` to debug |
| `BERTScore CUDA error` | Add `device="cpu"` to bert_score call |
| `Ingest very slow` | Reduce batch to 100 articles, re-run |
