# Product Requirements Document
## GraphRAG Inference Benchmark — TigerGraph Hackathon

**Version:** 1.0.0
**Author:** Sayandeep
**Status:** Active
**Last Updated:** 2025

---

## 1. Overview

### 1.1 Problem Statement

LLMs burn thousands of tokens answering complex questions. At scale, this gets expensive. Basic RAG (vector search + LLM) partially solves retrieval but treats documents as isolated chunks — it cannot reason across entity relationships.

**GraphRAG solves this.** By organizing data into a knowledge graph, it performs multi-hop reasoning and delivers precise, focused context to the LLM — fewer tokens, faster responses, lower cost, without sacrificing accuracy.

### 1.2 Project Goal

Build a three-pipeline benchmark system that proves:

> **GraphRAG reduces token consumption by 40–70% vs Basic RAG while maintaining or improving answer accuracy.**

### 1.3 Hackathon Context

- **Event:** GraphRAG Inference Hackathon by TigerGraph
- **Round 1:** 2M+ token dataset, open to all
- **Round 2:** 50–100M tokens, top 10 teams only
- **Prize Pool:** $700 + TigerGraph engineering mentorship

---

## 2. Scope

### 2.1 In Scope

- Three inference pipelines (LLM-Only, Basic RAG, GraphRAG)
- Pinecone-backed vector store for Pipeline 2
- TigerGraph knowledge graph for Pipeline 3
- Interactive comparison dashboard (single query → 3 answers + metrics)
- Token, latency, cost, and accuracy benchmarking
- LLM-as-a-Judge + BERTScore accuracy evaluation
- Wikipedia dataset ingestion (2M+ tokens)
- Public GitHub repo, demo video, blog post

### 2.2 Out of Scope

- Model fine-tuning
- Real-time streaming responses (v2 feature)
- Multi-language support
- User authentication / multi-tenant system

---

## 3. Users

| User | Goal |
|------|------|
| Hackathon Judges | Evaluate token reduction + accuracy improvement |
| Developers | Understand GraphRAG architecture and replicate |
| AI Teams | Adopt GraphRAG pattern in production |
| Open Source Community | Contribute and extend the benchmark |

---

## 4. Functional Requirements

### 4.1 Pipeline 1 — LLM Only

| ID | Requirement |
|----|-------------|
| P1-01 | Accept natural language query |
| P1-02 | Send query directly to Gemini 1.5 Flash with no retrieval context |
| P1-03 | Return answer, prompt tokens, completion tokens, latency, cost |
| P1-04 | Serve as worst-case token baseline |

### 4.2 Pipeline 2 — Basic RAG (Pinecone)

| ID | Requirement |
|----|-------------|
| P2-01 | Chunk dataset using RecursiveCharacterTextSplitter (chunk_size=512, overlap=64) |
| P2-02 | Embed chunks using `gemini-embedding-001` (3072 dimensions) |
| P2-03 | Store embeddings in Pinecone serverless index |
| P2-04 | At query time, retrieve top-k=5 semantically similar chunks |
| P2-05 | Inject retrieved chunks as context into Gemini prompt |
| P2-06 | Return answer + full token/latency/cost metrics |

### 4.3 Pipeline 3 — GraphRAG (TigerGraph)

| ID | Requirement |
|----|-------------|
| P3-01 | Ingest dataset into TigerGraph GraphRAG service via REST API |
| P3-02 | GraphRAG service auto-extracts entities and relationships |
| P3-03 | At query time, perform multi-hop graph traversal (default hop_depth=2) |
| P3-04 | Support retriever modes: `hybrid`, `community`, `sibling` |
| P3-05 | Return graph-grounded answer + token/latency/cost metrics |
| P3-06 | Expose tunable parameters: hop_depth, chunk_size, retriever type |

### 4.4 Comparison Dashboard

| ID | Requirement |
|----|-------------|
| D-01 | Single query input field triggers all 3 pipelines simultaneously |
| D-02 | Display answers side-by-side for all 3 pipelines |
| D-03 | Show per-pipeline: prompt tokens, completion tokens, total tokens, latency, cost |
| D-04 | Show token reduction % (GraphRAG vs Basic RAG) prominently |
| D-05 | Optional ground truth input for accuracy evaluation |
| D-06 | Display LLM-Judge verdict (PASS/FAIL) and BERTScore F1 per pipeline |
| D-07 | Exportable benchmark report (JSON/CSV) |

### 4.5 Accuracy Evaluation

| ID | Requirement |
|----|-------------|
| A-01 | LLM-as-a-Judge: hosted HuggingFace model grades PASS/FAIL |
| A-02 | BERTScore: semantic similarity F1 against ground truth |
| A-03 | Target: ≥90% LLM-Judge pass rate (bonus threshold) |
| A-04 | Target: BERTScore F1 rescaled ≥ 0.55 (bonus threshold) |
| A-05 | Accuracy must be maintained vs Basic RAG — token reduction alone is not a win |

---

## 5. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Dashboard query response < 30s for all 3 pipelines |
| Scalability | Pinecone serverless auto-scales; TigerGraph Savanna handles 2M–100M tokens |
| Cost | Round 1 target: free tier only (Gemini free, Pinecone free, TigerGraph Savanna credits) |
| Reliability | Retry logic on LLM API calls (exponential backoff, max 3 retries) |
| Observability | All metrics logged to JSON per query run |
| Reproducibility | Full dataset + config committed to GitHub |

---

## 6. Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Google Gemini 1.5 Flash |
| Vector DB | Pinecone Serverless (free tier) |
| Graph DB | TigerGraph Savanna / Community Edition |
| GraphRAG Service | github.com/tigergraph/graphrag (Docker) |
| Embeddings | gemini-embedding-001 (3072 dimensions) |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React + Tailwind CSS |
| Accuracy Eval | BERTScore + HuggingFace Inference API |
| Dataset | Wikipedia (Kaggle) — 2M+ tokens |
| Deployment | Docker Compose (local) |

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| Token reduction (GraphRAG vs Basic RAG) | ≥ 40% |
| LLM-Judge pass rate | ≥ 90% (bonus) |
| BERTScore F1 rescaled | ≥ 0.55 (bonus) |
| Dashboard query latency | < 30s end-to-end |
| Dataset size | ≥ 2M tokens (Round 1) |
| GitHub stars | Community validation |

---

## 8. Deliverables

- [ ] Public GitHub repo (built on TigerGraph GraphRAG repo)
- [ ] Architecture diagram
- [ ] Working comparison dashboard
- [ ] Benchmark report (tokens, cost, latency, accuracy per pipeline)
- [ ] Demo video (5–7 min)
- [ ] Blog post (Medium / Hashnode / Dev.to)
- [ ] Social media post (#GraphRAGInferenceHackathon)

---

## 9. Risks

| Risk | Mitigation |
|------|-----------|
| Pinecone free tier limits | Use serverless — scales automatically, generous free tier |
| TigerGraph ingestion slow on 2M tokens | Batch ingest, run overnight |
| Gemini rate limits | Exponential backoff with `withRetry()` |
| GraphRAG accuracy low | Tune hop_depth, chunk_size, retriever type iteratively |
| BERTScore below threshold | Use better ground truth answers, tune prompt templates |
