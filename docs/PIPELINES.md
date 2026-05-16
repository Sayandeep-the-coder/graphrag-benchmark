# Pipeline Implementation Guide

Reference for the three inference pipelines. **Source files are authoritative**; this document summarizes behavior and tunables.

---

## Shared conventions

- Each pipeline exposes `run(query: str) -> dict` with `answer` and `metrics` (`utils/metrics.py`).
- Pipelines 1 and 2 also expose `run_stream(query)` for SSE (`/compare/stream`).
- Retries: `utils/retry.with_retry` (exponential backoff, max 3 attempts).

---

## Pipeline 1 — LLM only

**File:** `pipelines/pipeline1_llm_only.py`

| Item | Value |
|------|--------|
| Model | `models/gemma-4-26b-a4b-it` |
| API | Google GenAI REST `generateContent` / `streamGenerateContent` |
| Retrieval | None |
| Purpose | Baseline: lowest context tokens, highest hallucination risk on medical facts |

**Prompt shape:**

```text
Answer the question accurately.
Q: {query}
A:
```

**When to use P1:** Establish a no-retrieval baseline. P2 and P3 should beat P1 on factual accuracy when ground truth is available.

---

## Pipeline 2 — Basic RAG (Pinecone)

**Files:** `pipelines/pipeline2_basic_rag/ingest.py`, `query.py`

| Item | Value |
|------|--------|
| Generation | `models/gemma-4-26b-a4b-it` (REST) |
| Embeddings | `llama-text-embed-v2` (Pinecone Inference) |
| Vector store | Pinecone, namespace default `medical-rag` |
| Default `top_k` | 5 |
| Chunking (ingest) | `CHUNK_SIZE=1000`, `CHUNK_OVERLAP=100` |

### Ingest

1. Read `.txt` from `--path` (default `./data/medical`).
2. Split with `RecursiveCharacterTextSplitter`.
3. Batch-embed chunks with `llama-text-embed-v2` (1024 dimensions).
4. Upsert to Pinecone with metadata `{"text": chunk}`.

```bash
python pipelines/pipeline2_basic_rag/ingest.py --path ./data/medical --namespace medical-rag
```

### Query — dynamic top-K

1. Embed the user query with `llama-text-embed-v2` (input_type="query").
2. Query Pinecone with `top_k = 15` (to allow for threshold filtering).
3. Walk matches in score order; **stop** when:
   - `score < 0.2` (`min_score_threshold`), or
   - score drops more than `0.1` from the previous match (`score_drop_threshold`), or
   - `len(chunks) >= 5` (`top_k`).
4. Build prompt with joined chunks; call Gemma 4 via REST.

### Tuning (Pipeline 2)

| Parameter | Default | Effect |
|-----------|---------|--------|
| `top_k` | 5 | Max chunks after dynamic filter |
| `min_score_threshold` | 0.2 | Minimum similarity to include a chunk |
| `score_drop_threshold` | 0.1 | Stop when relevance cliff detected |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 1000 / 100 | Ingest granularity |
| `namespace` | `medical-rag` | Pinecone namespace |

---

## Pipeline 3 — GraphRAG (TigerGraph)

**Files:** `pipelines/pipeline3_graphrag/ingest.py`, `query.py`

| Item | Value |
|------|--------|
| Service | `GRAPHRAG_SERVICE_URL` (default `http://localhost:8000`) |
| Ingest | `POST /documents/batch` (batches of 10) |
| Query | `POST /query` |
| Default retriever | `hybrid` |
| Default `hop_depth` | 2 |

### Ingest

```bash
python pipelines/pipeline3_graphrag/ingest.py --path ./data/medical
```

Documents are sent as `{content, filename, source}`; `source` is `medical_csv` when path contains `medical`.

### Query

Payload:

```json
{
  "query": "...",
  "retriever": "hybrid",
  "hop_depth": 2
}
```

On failure, returns a sanitized error string (does not crash the backend).

### Retriever modes

| Retriever | Best for |
|-----------|----------|
| `hybrid` | General medical Q&A (dashboard default) |
| `community` | Broad topic / summary questions |
| `sibling` | Adjacent document context |

### Tuning (Pipeline 3)

| Parameter | Default | Effect |
|-----------|---------|--------|
| `hop_depth` | 2 | Graph traversal depth (1 = cheaper, 3 = richer) |
| `retriever` | `hybrid` | Retrieval strategy inside GraphRAG service |

---

## Metrics utility

**File:** `utils/metrics.py`

- Encoding: tiktoken `cl100k_base`
- `PipelineMetrics.record(prompt, response, start_time)` sets tokens, latency, and `cost_usd` using `total / 1e6 * 0.075`

GraphRAG may set `prompt_tokens` / `completion_tokens` from the service response before `to_dict()`.

---

## Retry utility

**File:** `utils/retry.py`

`with_retry(fn, max_retries=3, base_delay=2.0)` — used by P1/P2 REST calls.
