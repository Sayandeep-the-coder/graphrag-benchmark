# BUILD_PROMPT.md
## Master AI Build Prompt — GraphRAG Inference Benchmark

> **Note:** This file provides a master prompt to scaffold a project similar to this medical benchmark. The **implemented repo** uses the models and settings defined in [README.md](README.md) and [PIPELINES.md](PIPELINES.md) (`gemma-4-26b-a4b-it`, `llama-text-embed-v2`).

Use this prompt with any AI coding assistant to scaffold a similar project. Attach the current `PRD.md`, `ARCHITECTURE.md`, `SETUP.md`, `PIPELINES.md`, and `EVALUATION.md` for up-to-date behavior.

---

## Context Files to Attach

Before running this prompt, attach these files as context to your AI assistant:
- `PRD.md`
- `ARCHITECTURE.md`
- `SETUP.md`
- `PIPELINES.md`
- `EVALUATION.md`

---

## THE MASTER BUILD PROMPT

```
You are an expert Python + React developer. Build the GraphRAG Inference Benchmark application
described in the attached documentation files.

=== PROJECT OVERVIEW ===
Build a three-pipeline LLM benchmark system that proves GraphRAG (TigerGraph knowledge graph)
reduces token consumption by 40-70% vs Basic RAG (Pinecone vector search) while maintaining
or improving answer accuracy. The project is for the TigerGraph GraphRAG Inference Hackathon.

=== TECH STACK (STRICT — DO NOT SUBSTITUTE) ===
- LLM: Google Gemma 4 (models/gemma-4-26b-a4b-it)
- Vector DB: Pinecone Serverless (pinecone-client v3+)
- Embeddings: Pinecone Inference (llama-text-embed-v2, 1024 dimensions)
- Graph DB + RAG: TigerGraph via official GraphRAG service (REST API at localhost:8000)
- Backend: FastAPI with uvicorn
- Frontend: React 18 + Tailwind CSS
- Accuracy eval: bert-score library + HuggingFace Inference API (Mistral 7B judge)
- Token counting: tiktoken (cl100k_base encoding)
- Dataset: Medical (plain .txt files in ./data/medical/)

=== WHAT TO BUILD ===

STEP 1 — Project scaffold
Create this exact directory structure:
graphrag-benchmark/
├── data/wikipedia/              (empty, populated by ingest)
├── pipelines/
│   ├── __init__.py
│   ├── pipeline1_llm_only.py
│   ├── pipeline2_basic_rag/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   └── query.py
│   └── pipeline3_graphrag/
│       ├── __init__.py
│       ├── ingest.py
│       └── query.py
├── evaluation/
│   ├── __init__.py
│   ├── llm_judge.py
│   ├── bertscore_eval.py
│   ├── accuracy.py
│   └── benchmark_runner.py
├── dashboard/
│   ├── backend/
│   │   ├── main.py              (FastAPI app)
│   │   └── models.py            (Pydantic schemas)
│   └── frontend/
│       ├── package.json
│       ├── tailwind.config.js
│       └── src/
│           ├── App.jsx
│           ├── components/
│           │   ├── QueryInput.jsx
│           │   ├── PipelineCard.jsx
│           │   ├── MetricsBar.jsx
│           │   └── TokenChart.jsx
│           └── index.css
├── utils/
│   ├── __init__.py
│   ├── metrics.py
│   └── retry.py
├── scripts/
│   ├── extract_wikipedia.py
│   ├── count_tokens.py
│   └── smoke_test.py
├── results/                     (empty, populated by benchmark)
├── .env.example
├── requirements.txt
├── docker-compose.yml
└── README.md

STEP 2 — Core utilities (build first, others depend on these)

Build utils/metrics.py:
- Class PipelineMetrics with fields: name, prompt_tokens, completion_tokens, latency_ms, cost_usd
- Method record(prompt, response, start_time) counts tokens with tiktoken cl100k_base
- Cost formula: (prompt_tokens + completion_tokens) / 1_000_000 * 0.075 (Gemini 1.5 Flash rate)
- Method to_dict() returns all fields as dict

Build utils/retry.py:
- Function with_retry(fn, max_retries=3, base_delay=2.0)
- Exponential backoff: delay = base_delay * (2 ** attempt)
- Catches all exceptions, re-raises on final attempt

STEP 3 — Pipeline 1 (LLM Only)

File: pipelines/pipeline1_llm_only.py
- Configure Gemini 1.5 Flash from GEMINI_API_KEY env var
- Function run(query: str) -> dict
- Prompt: simple "Answer: {query}" — NO retrieval context
- Use with_retry wrapper on generate_content call
- Return: {"answer": str, "metrics": dict}

STEP 4 — Pipeline 2 (Basic RAG with Pinecone)

File: pipelines/pipeline2_basic_rag/ingest.py
- Read all .txt files from ./data/medical/
- Split with RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
- Embed with Pinecone Inference (llama-text-embed-v2, 1024 dims)
- Upsert to Pinecone in batches of 100
- Index name from PINECONE_INDEX_NAME env var
- Namespace: "medical-rag"
- Metadata per vector: {"text": chunk_text}
- Show progress bar with tqdm

File: pipelines/pipeline2_basic_rag/query.py
- Function run(query: str, top_k: int = 5) -> dict
- Embed query, search Pinecone, retrieve top_k chunks (using dynamic thresholds: score < 0.2 filter)
- Build prompt: "Context:\n{chunks}\n\nQuestion: {query}\n\nAnswer:"
- Call Gemma 4 with retry
- Return: {"answer": str, "metrics": dict, "chunks_retrieved": int}

STEP 5 — Pipeline 3 (GraphRAG with TigerGraph)

File: pipelines/pipeline3_graphrag/ingest.py
- POST each document to {GRAPHRAG_SERVICE_URL}/documents/batch (batches of 10)
- Each document: {"content": text, "filename": basename, "source": "medical"}
- Handle 200 vs error responses with logging
- Show tqdm progress

File: pipelines/pipeline3_graphrag/query.py
- Function run(query: str, retriever: str = "hybrid", hop_depth: int = 2) -> dict
- POST to {GRAPHRAG_SERVICE_URL}/query with {query, retriever, hop_depth}
- Parse response: answer, prompt_tokens, completion_tokens from response JSON
- Return: {"answer": str, "metrics": dict, "entities_retrieved": list, "retriever": str, "hop_depth": int}

STEP 6 — Evaluation

File: evaluation/llm_judge.py
- Use HuggingFace Inference API with HF_TOKEN env var
- Model: "mistralai/Mistral-7B-Instruct-v0.2"
- Judge prompt compares answer vs ground_truth, expects "PASS" or "FAIL"
- Function llm_judge(answer, ground_truth) -> {"verdict": "PASS"|"FAIL", "raw_output": str}
- Function batch_judge(answers, ground_truths) -> {individual, pass_count, total, pass_rate, bonus_achieved}
- bonus_achieved = pass_rate >= 0.90

File: evaluation/bertscore_eval.py
- Use bert_score library with model_type="distilbert-base-uncased", device="cpu"
- Function compute_bertscore(candidates, references) -> {precision, recall, f1_raw, f1_rescaled, bonus_achieved_raw, bonus_achieved_rescaled}
- f1_rescaled = (f1_raw - 0.5) / 0.5
- bonus_achieved_raw: f1_raw >= 0.88
- bonus_achieved_rescaled: f1_rescaled >= 0.55

File: evaluation/benchmark_runner.py
- Load at least 10 hardcoded benchmark queries with ground truths (Wikipedia domain)
- Run all 3 pipelines per query
- Calculate token_reduction_pct = (p2_tokens - p3_tokens) / p2_tokens * 100
- After all queries, run accuracy evaluation on all answers
- Save full JSON report to ./results/benchmark_{timestamp}.json
- Print summary table to console

STEP 7 — FastAPI Backend

File: dashboard/backend/main.py
- CORS enabled for localhost:3000
- POST /compare endpoint:
  - Request: {query: str, ground_truth: str (optional)}
  - Run all 3 pipelines (can be parallel with asyncio)
  - Calculate token_reduction_pct (GraphRAG vs Basic RAG)
  - If ground_truth provided: run both accuracy evaluations on all 3 answers
  - Return unified response with all answers, metrics, accuracy (if available)
- GET /health endpoint returns {"status": "ok"}
- POST /ingest/rag triggers pipeline2 ingest (background task)
- POST /ingest/graphrag triggers pipeline3 ingest (background task)
- GET /metrics/summary returns summary stats from ./results/ JSON files

File: dashboard/backend/models.py
- Pydantic models for all request/response schemas

STEP 8 — React Frontend Dashboard

Build a clean, professional dark-theme dashboard:

App.jsx layout:
- Header: "GraphRAG Inference Benchmark" title + subtitle
- Query input area:
  - Large text input for query
  - Optional ground truth input (collapsible)
  - "Run Benchmark" button
  - Loading spinner while running
- Results area (3 columns, side by side):
  - Column 1: LLM Only (red accent)
  - Column 2: Basic RAG (yellow accent)
  - Column 3: GraphRAG (green accent)

PipelineCard.jsx (per pipeline column):
- Pipeline name header with color accent
- Answer text display (scrollable, max height)
- Metrics section:
  - Prompt tokens
  - Completion tokens
  - Total tokens (bold)
  - Latency (ms)
  - Cost (USD, 6 decimal places)
- Accuracy section (if ground truth provided):
  - LLM-Judge: PASS/FAIL badge (green/red)
  - BERTScore F1: number + progress bar

TokenChart.jsx:
- Bar chart comparing total tokens across 3 pipelines
- Token reduction % prominently displayed: "GraphRAG uses X% fewer tokens than Basic RAG"
- Use recharts library

MetricsBar.jsx:
- Horizontal comparison bar for any single metric
- Color coded: red for worst, green for best

Styling requirements:
- Dark theme (#0f172a background)
- Tailwind CSS only
- Responsive (mobile + desktop)
- No external component libraries

STEP 9 — Docker Compose

docker-compose.yml:
- Service: graphrag (tigergraph/graphrag:latest, port 8000, env_file .env)
- Service: backend (build ./dashboard/backend, port 8080, depends_on graphrag)
- Service: frontend (build ./dashboard/frontend, port 3000, depends_on backend)

STEP 10 — Scripts

scripts/extract_wikipedia.py:
- Connect to SQLite db at ./data/raw/articles.db
- SELECT title, text FROM articles LIMIT 5000
- Write each as ./data/wikipedia/article_{i:05d}.txt with "# {title}\n\n{text}" format

scripts/count_tokens.py:
- Count total tokens in ./data/wikipedia/*.txt using tiktoken cl100k_base
- Print: "Total tokens: {n:,}" and "Estimated 2M+ requirement: {'MET' if n >= 2_000_000 else 'NOT MET'}"

scripts/smoke_test.py:
- Check Gemini API: generate "Hello"
- Check Pinecone: describe_index, print vector count
- Check GraphRAG service: GET /health
- Run one query through all 3 pipelines
- Print ✅ or ❌ for each check

=== IMPORTANT CONSTRAINTS ===

1. All API keys come from environment variables via python-dotenv. NEVER hardcode.
2. All pipelines must implement identical interface: run(query) -> {"answer": str, "metrics": dict}
3. Token counting uses tiktoken, NOT the LLM provider's reported token count (for consistency)
4. Pinecone upsert in batches of 100 max (API limit)
5. Add 1 second sleep between benchmark queries to avoid rate limits
6. GraphRAG service is a separate Docker container — communicate via REST only
7. All results saved as JSON to ./results/ directory (create if missing)
8. Frontend calls backend at http://localhost:8080 (not direct API calls)
9. requirements.txt must be pinned versions (no floating deps)

=== DELIVERABLE FORMAT ===
Build each file completely. No stubs. No TODOs. Production-ready code.
Start with utils/, then pipelines/, then evaluation/, then dashboard/backend/, then dashboard/frontend/.
After each file, confirm: "✅ {filename} complete."
End with: "🚀 All files complete. Run: docker-compose up -d && python scripts/smoke_test.py"
```

---

## Iterative Prompts (use after initial build)

### Add more benchmark queries
```
Add 20 more benchmark query + ground truth pairs to evaluation/benchmark_runner.py.
Queries must be answerable from Wikipedia data and test multi-entity reasoning.
Examples of good queries: ones that require knowing relationships between 2+ entities.
```

### Tune GraphRAG for accuracy
```
In pipelines/pipeline3_graphrag/query.py, add a tune() function that runs the same
query with hop_depth=[1,2,3] and retriever=["hybrid","community","sibling"] and
returns the combination with best BERTScore F1. Update the run() function to use
cached best params per query type.
```

### Dashboard export feature
```
Add an "Export Report" button to the React dashboard. On click, call GET /metrics/summary
and download the JSON as benchmark_report_{date}.json. Also add a CSV export option
that flattens all metrics into a table.
```

### Graph visualization panel
```
Add a fourth panel to the dashboard that shows a force-directed graph of the entities
retrieved by Pipeline 3 using D3.js. Nodes = entities, edges = relationships.
Size nodes by relevance score. Color by entity type.
```
