# Medical GraphRAG Inference Benchmark

A three-pipeline LLM inference benchmark that evaluates and proves how GraphRAG (TigerGraph) reduces token consumption and improves context relevance compared to Basic RAG (Pinecone) on a custom **Medical Dataset**.

This system allows for side-by-side performance comparison (latency, token usage, cost, and qualitative response) of three distinct approaches.

## The Pipelines

| # | Pipeline | Method | Retrieval Logic | Expected Token Usage |
|---|----------|--------|-----------------|----------------------|
| **1** | **LLM-Only** | Direct Google GenAI call (`gemma-4`) | No context provided. Used as a baseline for hallucination risk. | Very Low |
| **2** | **Basic RAG** | Pinecone Vector Search + `gemma-4` | Uses Gemini `text-embedding-004`. Implements **Dynamic Top-K Hopping** to fetch chunks and filter based on a score cliff. | High |
| **3** | **GraphRAG** | TigerGraph Multi-Hop Graph + `gemma-4` | REST API graph traversal fetching multi-hop relational entities (hybrid/community/sibling modes). | Medium |

> [!NOTE]
> Due to experimental backend instability with the `gemma-4-26b-a4b-it` SDK model on medical queries, pipelines 1 and 2 directly use the Google GenAI REST API to properly parse response structures and prevent 500 Internal Server errors.

## Tech Stack

- **LLM Models**: `gemma-4-26b-a4b-it` (Generation), `gemini-embedding-001` (Vector Embeddings)
- **Vector DB**: Pinecone Serverless
- **Graph DB**: TigerGraph Savanna
- **Backend**: FastAPI + Uvicorn + Python 3
- **Frontend**: React 18 + Tailwind CSS + Recharts

---

## 🚀 Setup Instructions for Contributors

### 1. Environment Variables
Copy the example environment file and fill in your API keys.
```bash
cp .env.example .env
```
Ensure you have the following configured:
- `GEMINI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME` (e.g., `medical-rag`)
- `TG_HOST` & `TG_PASSWORD` (if running GraphRAG)

### 2. Python Backend Setup
Initialize the virtual environment and install dependencies.
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Data Preparation
We use a custom medical dataset consisting of symptoms, precautions, and severity mappings. Convert the raw CSV files into a unified knowledge base:
```bash
python scripts/prepare_medical_data.py
```
This generates the unified `data/medical/knowledge_base.txt`.

### 4. Database Ingestion
Ingest the knowledge base into the Vector DB (Pinecone) and Graph DB (TigerGraph):
```bash
# Ingest into Pinecone for Basic RAG
python pipelines/pipeline2_basic_rag/ingest.py

# Ingest into TigerGraph for GraphRAG
python pipelines/pipeline3_graphrag/ingest.py
```

*(Optional) Verify your token counts:*
```bash
python scripts/count_tokens.py --path data/medical/knowledge_base.txt
```

### 5. Running the Dashboard Services

**Start the Backend (FastAPI)**
The backend coordinates the LLM inference and metrics collection.
```bash
# From the project root
uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8080 --reload
```

**Start the Frontend (React)**
The frontend provides the visual benchmark comparison UI.
```bash
cd dashboard/frontend
npm install
npm run dev
```

Finally, open your browser and navigate to **[http://localhost:3000](http://localhost:3000)**.

---

## 📁 Project Structure

```text
graphrag-benchmark/
├── data/
│   └── medical/               # Raw medical CSVs and parsed knowledge_base.txt
├── pipelines/
│   ├── pipeline1_llm_only.py  # Baseline inference
│   ├── pipeline2_basic_rag/   # Pinecone vector search & dynamic hopping logic
│   └── pipeline3_graphrag/    # TigerGraph REST integration
├── dashboard/
│   ├── backend/               # FastAPI orchestration (main.py)
│   └── frontend/              # Next.js/React benchmark UI
├── scripts/
│   ├── prepare_medical_data.py# CSV-to-text unified preparation
│   ├── count_tokens.py        # Token baseline verification
│   └── smoke_test.py          # Terminal validation script
├── utils/                     # Metrics tracking & retry logic
└── requirements.txt
```

## Contributing Guidelines
1. **Dynamic Top-K Search**: If editing the vector search algorithms in `pipeline2_basic_rag/query.py`, ensure that the *score cliff* detection logic (`min_score_threshold` and `score_drop_threshold`) remains intact, as this significantly optimizes token consumption.
2. **Graceful Degradation**: The GraphRAG pipeline handles REST connection failures gracefully. If the TigerGraph Docker container isn't running, it should return a clean error string to the frontend instead of crashing the backend. Keep this pattern for all new microservices.
3. **Dependencies**: When introducing new packages, ensure you add them to `requirements.txt` to avoid `Cannot find module` errors across environments.
