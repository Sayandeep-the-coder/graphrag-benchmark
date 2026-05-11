# Changelog

All notable changes to this project will be documented here.
Format: [Semantic Versioning](https://semver.org)

---

## [Unreleased]

- Round 2 scale-up to 50M tokens
- Streaming dashboard responses
- Query history persistence

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
