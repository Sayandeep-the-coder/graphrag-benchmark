# Product Requirements Document
## Medical GraphRAG Inference Benchmark

**Version:** 1.2.0  
**Status:** Active  
**Last updated:** 2026-05-16

---

## 1. Overview

### 1.1 Problem statement

LLMs consume large prompts when answering domain questions. Basic RAG retrieves similar text chunks but misses relational structure (e.g. disease → symptoms → precautions). GraphRAG uses a knowledge graph for multi-hop retrieval and tighter context.

### 1.2 Project goal

> **GraphRAG reduces token consumption by 40–70% vs Basic RAG while maintaining or improving answer accuracy** on a medical Q&A benchmark.

### 1.3 Context

Built for the TigerGraph GraphRAG Inference Hackathon. The repository originally targeted a 2M+ token Wikipedia corpus; the **current default dataset is medical** (`data/medical/knowledge_base.txt`). Wikipedia tooling remains optional under `scripts/extract_wikipedia.py`.

---

## 2. Scope

### 2.1 In scope

- Three pipelines: LLM-only, Basic RAG (Pinecone), GraphRAG (TigerGraph service)
- Medical dataset preparation and dual ingest (Pinecone + GraphRAG)
- Comparison dashboard with streaming responses (`/compare/stream`)
- Per-pipeline tokens, latency, cost; token reduction vs Basic RAG
- Optional ground-truth accuracy: LLM-as-judge + BERTScore
- Batch benchmark reports in `results/`
- Docker Compose deployment

### 2.2 Out of scope

- Model fine-tuning
- Multi-tenant auth
- Non-English locales (v1)

---

## 3. Functional requirements

### 4.1 Pipeline 1 — LLM only

| ID | Requirement |
|----|-------------|
| P1-01 | Accept natural language query |
| P1-02 | Call `models/gemma-4-26b-a4b-it` via GenAI REST with **no** retrieval context |
| P1-03 | Return answer, token metrics, latency, cost |
| P1-04 | Baseline for minimum prompt size / ungrounded answers |

### 4.2 Pipeline 2 — Basic RAG

| ID | Requirement |
|----|-------------|
| P2-01 | Chunk medical KB (`CHUNK_SIZE=1000`, `OVERLAP=100`) |
| P2-02 | Embed with `llama-text-embed-v2` (Pinecone Inference) |
| P2-03 | Store in Pinecone (namespace `medical-rag`) |
| P2-04 | Dynamic top-K retrieval (score threshold `0.2` + cliff detection) |
| P2-05 | Generate with `models/gemma-4-26b-a4b-it` (REST) using retrieved chunks only |
| P2-06 | Return answer + chunk count + similarity scores + metrics |

### 4.3 Pipeline 3 — GraphRAG

| ID | Requirement |
|----|-------------|
| P3-01 | Ingest via GraphRAG `POST /documents/batch` |
| P3-02 | Service builds entities/relationships in TigerGraph |
| P3-03 | Query with configurable `hop_depth` (default 2) |
| P3-04 | Retrievers: `hybrid`, `community`, `sibling` |
| P3-05 | Return answer + entities + metrics; fail gracefully if service down |

### 4.4 Dashboard

| ID | Requirement |
|----|-------------|
| D-01 | Single query runs all three pipelines |
| D-02 | Side-by-side answers and metrics |
| D-03 | Token reduction % (GraphRAG vs Basic RAG) |
| D-04 | SSE streaming for live output |
| D-05 | Optional ground truth → accuracy badges |
| D-06 | Display knowledge base snippet |

### 4.5 Accuracy evaluation

| ID | Requirement |
|----|-------------|
| A-01 | LLM-as-judge (Mistral 7B in `llm_judge.py`) |
| A-02 | BERTScore semantic F1 |
| A-03 | Targets: ≥90% judge pass rate; BERTScore F1 rescaled ≥ 0.55 (bonus thresholds) |

---

## 4. Tech stack (current)

| Layer | Technology |
|-------|------------|
| LLM — P1 | `models/gemma-4-26b-a4b-it` |
| LLM — P2 | `models/gemma-4-26b-a4b-it` |
| Embeddings — P2 | `llama-text-embed-v2` (Pinecone Inference) |
| Vector DB | Pinecone Serverless |
| Graph | TigerGraph Savanna + `tigergraph/graphrag` Docker |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React + Tailwind + Recharts |
| Eval | BERTScore + LLM judge |
| Dataset (default) | Medical KB (`prepare_medical_data.py`) |

---

## 5. Success metrics

| Metric | Target |
|--------|--------|
| Token reduction (P3 vs P2) | ≥ 40% |
| LLM-judge pass rate | ≥ 90% (bonus) |
| BERTScore F1 rescaled | ≥ 0.55 (bonus) |
| End-to-end dashboard latency | < 30s typical |

---

## 6. Risks

| Risk | Mitigation |
|------|------------|
| Gemma / Gemini rate limits | `with_retry` exponential backoff |
| Pinecone dimension mismatch | Index at 1024 for `llama-text-embed-v2` |
| GraphRAG unavailable | Sanitized errors in P3; compose health checks |
| Medical hallucination on P1 | Use P2/P3 for grounded answers; judge in eval |
