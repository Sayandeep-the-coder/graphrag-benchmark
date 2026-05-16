# Evaluation Guide — Accuracy Metrics

Token reduction means nothing if accuracy drops. This guide covers both evaluation methods required by the hackathon judges.

---

## Two Required Methods

| Method | What It Measures | Bonus Threshold |
|--------|-----------------|-----------------|
| LLM-as-a-Judge | PASS/FAIL grading by hosted LLM | ≥ 90% pass rate |
| BERTScore | Semantic similarity F1 | F1 rescaled ≥ 0.55 (raw ≥ 0.88) |

Hitting **both** unlocks maximum bonus points.

---

## Method 1 — LLM-as-a-Judge

A free HuggingFace-hosted model grades each answer PASS or FAIL against ground truth.

```python
# evaluation/llm_judge.py
import requests, os

HF_TOKEN = os.getenv("HF_TOKEN")
JUDGE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
API_URL = f"https://api-inference.huggingface.co/models/{JUDGE_MODEL}"

JUDGE_PROMPT = """You are an expert evaluator. Compare the answer to the reference.

Reference answer: {reference}

Candidate answer: {answer}

Is the candidate answer factually correct and complete based on the reference?
Reply with exactly one word: PASS or FAIL"""

def llm_judge(answer: str, ground_truth: str) -> dict:
    prompt = JUDGE_PROMPT.format(reference=ground_truth, answer=answer)

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {HF_TOKEN}"},
        json={"inputs": prompt, "parameters": {"max_new_tokens": 5}}
    )

    raw = resp.json()
    generated = raw[0]["generated_text"].strip().upper()
    verdict = "PASS" if "PASS" in generated else "FAIL"

    return {"verdict": verdict, "raw_output": generated}

def batch_judge(answers: list[str], ground_truths: list[str]) -> dict:
    results = [llm_judge(a, g) for a, g in zip(answers, ground_truths)]
    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    pass_rate = pass_count / len(results) if results else 0

    return {
        "individual": results,
        "pass_count": pass_count,
        "total": len(results),
        "pass_rate": round(pass_rate, 4),
        "bonus_achieved": pass_rate >= 0.90
    }
```

---

## Method 2 — BERTScore

Measures semantic similarity between generated answer and ground truth using contextual BERT embeddings.

```python
# evaluation/bertscore_eval.py
from bert_score import score as bert_score_fn
import torch

def compute_bertscore(
    candidates: list[str],
    references: list[str],
    lang: str = "en"
) -> dict:
    P, R, F1 = bert_score_fn(
        cands=candidates,
        refs=references,
        lang=lang,
        model_type="distilbert-base-uncased",  # lighter, faster
        device="cpu",                           # safe for all machines
        verbose=False
    )

    f1_raw = F1.mean().item()
    # Rescale from [0,1] range: rescaled = (raw - 0.5) / 0.5
    f1_rescaled = (f1_raw - 0.5) / 0.5

    return {
        "precision": round(P.mean().item(), 4),
        "recall": round(R.mean().item(), 4),
        "f1_raw": round(f1_raw, 4),
        "f1_rescaled": round(f1_rescaled, 4),
        "bonus_achieved_raw": f1_raw >= 0.88,
        "bonus_achieved_rescaled": f1_rescaled >= 0.55
    }
```

---

## Combined Evaluation Runner

```python
# evaluation/accuracy.py
from evaluation.llm_judge import llm_judge, batch_judge
from evaluation.bertscore_eval import compute_bertscore

def evaluate_pipeline(
    pipeline_name: str,
    answers: list[str],
    ground_truths: list[str]
) -> dict:
    judge_results = batch_judge(answers, ground_truths)
    bert_results = compute_bertscore(answers, ground_truths)

    both_bonus = (
        judge_results["bonus_achieved"] and
        (bert_results["bonus_achieved_raw"] or bert_results["bonus_achieved_rescaled"])
    )

    return {
        "pipeline": pipeline_name,
        "llm_judge": judge_results,
        "bertscore": bert_results,
        "max_bonus_achieved": both_bonus
    }

def evaluate_all_pipelines(
    p1_answers: list[str],
    p2_answers: list[str],
    p3_answers: list[str],
    ground_truths: list[str]
) -> dict:
    return {
        "LLM-Only":  evaluate_pipeline("LLM-Only", p1_answers, ground_truths),
        "Basic-RAG": evaluate_pipeline("Basic-RAG", p2_answers, ground_truths),
        "GraphRAG":  evaluate_pipeline("GraphRAG", p3_answers, ground_truths),
    }
```

---

## Benchmark runner

**File:** `evaluation/benchmark_runner.py`

Runs **30 medical-domain** question/answer pairs through all three pipelines, computes per-query token reduction (P2 vs P3), runs `evaluate_all_pipelines`, and writes JSON to `results/benchmark_YYYYMMDD_HHMMSS.json`.

```bash
python -m evaluation.benchmark_runner
# or
python evaluation/benchmark_runner.py
```

Each entry in `BENCHMARK_QUERIES` uses `question` and `correct_answer` (symptoms, precautions, disease definitions from the medical KB). P2 is called with `namespace="medical-rag"` and `top_k=5` to match the dashboard defaults.

Summary fields in the report:

- `avg_token_reduction_pct`
- `graphrag_judge_pass_rate` / `graphrag_bertscore_f1`
- `max_bonus` (both judge + BERTScore thresholds met)

---

## Interpreting Results

| BERTScore F1 (rescaled) | Interpretation |
|------------------------|----------------|
| ≥ 0.55 | ✅ Bonus threshold — strong semantic match |
| 0.40 – 0.55 | 🟡 Acceptable — tune prompts |
| < 0.40 | 🔴 Poor — check ground truths, retune GraphRAG |

| LLM-Judge Pass Rate | Interpretation |
|--------------------|----------------|
| ≥ 90% | ✅ Bonus threshold |
| 70% – 90% | 🟡 Good — tune hop_depth or prompt template |
| < 70% | 🔴 Retune — check retriever mode and chunk size |

---

## Tuning Tips for High Accuracy

1. **Increase hop_depth** to 3 for complex multi-entity questions
2. **Switch retriever to `community`** for broad topic questions
3. **Add explicit system prompt** to GraphRAG: "Answer using only retrieved graph facts."
4. **Better ground truths** — write your own for your specific dataset
5. **Increase top_k** in Pinecone to 10 for better Basic RAG baseline (makes GraphRAG comparison stronger)
