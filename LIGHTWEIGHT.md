# ⚡ GraphRAG Benchmark — Lightweight Mode

If you want to run the benchmark without downloading massive NVIDIA CUDA libraries (over 1GB) or if you want a quick verification of the pipeline, use the **Lightweight Mode**.

## 1. Minimal Installation

Instead of the full `requirements.txt`, use the lightweight version which installs the **CPU-only** version of Torch. This reduces the installation size by roughly 10x.

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install lightweight dependencies
pip install -r requirements-light.txt
```

## 2. Running the "Quick" Benchmark

The full benchmark runs 100 queries across 3 pipelines (300 total calls). To run a quick test with only **5 representative queries** (one per clinical category), use the `--light` flag:

```bash
python -m evaluation.benchmark_runner --light
```

Alternatively, you can set an environment variable:
```bash
$env:LIGHTWEIGHT="true"; python -m evaluation.benchmark_runner  # PowerShell
export LIGHTWEIGHT=true; python -m evaluation.benchmark_runner    # Bash
```

## 3. How it Works

- **CPU-only Torch**: Uses `torch+cpu` which runs BERTScore on your processor instead of needing a GPU.
- **API-First**: The core RAG and GraphRAG logic uses Google GenAI and Pinecone APIs, so they are naturally "light" on your local machine.
- **Subset Selection**: The `--light` mode automatically selects one question from each category (`MULTIHOP`, `COUNTERFACTUAL`, `TEMPORARY`, etc.) to ensure your evaluation still covers the full range of reasoning types.
- **Graceful Degrade**: If the BERTScore models fail to download due to disk space, the runner will still complete using the **LLM-Judge** accuracy metrics.
