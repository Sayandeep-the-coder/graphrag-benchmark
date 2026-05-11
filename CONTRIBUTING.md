# Contributing Guide

Thanks for your interest in contributing to the GraphRAG Inference Benchmark.

---

## Getting Started

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Set up locally: follow [SETUP.md](SETUP.md)
4. Make changes
5. Run tests: `python -m pytest tests/`
6. Submit PR with description of what changed and why

---

## What to Contribute

| Area | Examples |
|------|---------|
| New pipeline variant | Weaviate RAG, Neo4j GraphRAG |
| Dataset support | Script to ingest PubMed, legal docs |
| Dashboard features | Query history, export chart, dark mode |
| Benchmark queries | More ground truth Q&A pairs |
| Accuracy eval | New judge models, ROUGE score |
| Documentation | Fix typos, clarify setup steps |

---

## Code Style

- Python: follow PEP8, use type hints
- Keep functions small — one responsibility
- Add docstrings to all public functions
- New pipeline must implement `run(query: str) -> dict` interface

---

## PR Requirements

- [ ] Code runs without errors
- [ ] `metrics.to_dict()` returns all required fields
- [ ] No API keys committed (use `.env`)
- [ ] Update CHANGELOG.md with your change

---

## Issues

Open a GitHub Issue for:
- Bug reports (include error + reproduction steps)
- Feature requests
- Dataset suggestions
- Accuracy improvement ideas
