# Changelog

All notable changes to this project will be documented here.
Format: [Semantic Versioning](https://semver.org)

---

## [1.2.0] — 2026-05-16

### Changed
- **Comprehensive Documentation Sync:** All core Markdown files (`README.md`, `PRD.md`, `ARCHITECTURE.md`, `SETUP.md`, `PIPELINES.md`, `EVALUATION.md`) updated to reflect current technical implementation.
- **Model Standardization:** Standardized all pipelines to use `models/gemma-4-26b-a4b-it` as the primary LLM.
- **Embedding Alignment:** Updated Basic RAG to use `llama-text-embed-v2` via Pinecone Inference (1024 dimensions), replacing `embedding-001`.
- **Retrieval Optimization:** Synchronized dynamic `top_k` logic and similarity thresholds (score < 0.2) across documentation and code.
- **Master Prompt Update:** Refactored `BUILD_PROMPT.md` to use the medical dataset and current model IDs.

---

## [1.1.0] — 2026-05-14

### Changed
- Transitioned project focus from Wikipedia to **Medical Benchmark** (DrugBank/Symptoms dataset).
- Updated ingest scripts to default to `./data/medical`.
- Integrated TigerGraph Savanna as the primary Knowledge Graph provider.

---

## [1.0.0] — 2025

### Added
- Pipeline 1: LLM-Only baseline with Gemini 1.5 Flash
- Pipeline 2: Basic RAG with Pinecone serverless vector store
- Pipeline 3: GraphRAG with TigerGraph via official GraphRAG repo
- FastAPI comparison backend (`/compare` endpoint)
- React + Tailwind dashboard with side-by-side metrics
- LLM-as-a-Judge accuracy evaluation (HuggingFace hosted)
- BERTScore semantic similarity evaluation
- Benchmark runner for batch query evaluation
- Wikipedia dataset ingest scripts (2M+ tokens)
- Exponential backoff retry utility for Gemini API
- Token counter + cost calculator utilities
- Full documentation: PRD, ARCHITECTURE, SETUP, PIPELINES, EVALUATION
- Docker Compose setup for GraphRAG service

### Tech Stack
- Pinecone Serverless (replaces ChromaDB for production-grade vector search)
- sentence-transformers/all-MiniLM-L6-v2 for embeddings
- TigerGraph Savanna for graph DB
- Gemini 1.5 Flash as primary LLM

---

## [0.1.0] — Initial scaffold

- Project structure created
- Environment config setup
- Basic pipeline stubs
