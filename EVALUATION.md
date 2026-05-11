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

## Benchmark Runner

Run 30+ queries across all pipelines, save results:

```python
# evaluation/benchmark_runner.py
import json, time
from datetime import datetime
from pipelines import pipeline1_llm_only as p1
from pipelines.pipeline2_basic_rag import query as p2
from pipelines.pipeline3_graphrag import query as p3
from evaluation.accuracy import evaluate_all_pipelines

# Sample benchmark queries + ground truths for Wikipedia dataset
BENCHMARK_QUERIES = [
    {
        "query": "Who developed the theory of general relativity?",
        "ground_truth": "Albert Einstein developed the theory of general relativity, published in 1915."
    },
    {
        "query": "What is the capital of France and what river runs through it?",
        "ground_truth": "Paris is the capital of France. The Seine river runs through it."
    },
    {
        "query": "What programming language was developed by Guido van Rossum?",
        "ground_truth": "Python programming language was developed by Guido van Rossum, first released in 1991."
    },
    # Add 30+ more queries for robust benchmark
]

def run_benchmark():
    p1_answers, p2_answers, p3_answers, ground_truths = [], [], [], []
    all_metrics = []

    for item in BENCHMARK_QUERIES:
        query = item["query"]
        gt = item["ground_truth"]
        ground_truths.append(gt)

        r1 = p1.run(query)
        r2 = p2.run(query)
        r3 = p3.run(query)

        p1_answers.append(r1["answer"])
        p2_answers.append(r2["answer"])
        p3_answers.append(r3["answer"])

        # Token reduction per query
        rag_tokens = r2["metrics"]["total_tokens"]
        graph_tokens = r3["metrics"]["total_tokens"]
        reduction = (rag_tokens - graph_tokens) / rag_tokens * 100

        all_metrics.append({
            "query": query,
            "p1": r1["metrics"],
            "p2": r2["metrics"],
            "p3": r3["metrics"],
            "token_reduction_pct": round(reduction, 2)
        })

        print(f"✅ Query done | Reduction: {reduction:.1f}%")
        time.sleep(1)  # rate limit safety

    accuracy = evaluate_all_pipelines(p1_answers, p2_answers, p3_answers, ground_truths)

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_queries": len(BENCHMARK_QUERIES),
        "per_query_metrics": all_metrics,
        "accuracy": accuracy,
        "summary": {
            "avg_token_reduction_pct": sum(
                m["token_reduction_pct"] for m in all_metrics
            ) / len(all_metrics),
            "graphrag_judge_pass_rate": accuracy["GraphRAG"]["llm_judge"]["pass_rate"],
            "graphrag_bertscore_f1": accuracy["GraphRAG"]["bertscore"]["f1_rescaled"],
            "max_bonus": accuracy["GraphRAG"]["max_bonus_achieved"]
        }
    }

    with open(f"./results/benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n=== BENCHMARK COMPLETE ===")
    print(f"Avg token reduction: {report['summary']['avg_token_reduction_pct']:.1f}%")
    print(f"Judge pass rate:     {report['summary']['graphrag_judge_pass_rate']*100:.1f}%")
    print(f"BERTScore F1:        {report['summary']['graphrag_bertscore_f1']:.3f}")
    print(f"Max bonus achieved:  {report['summary']['max_bonus']}")

if __name__ == "__main__":
    run_benchmark()
```

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
5. **Increase top_k** in Pinecone to 7 for better Basic RAG baseline (makes GraphRAG comparison stronger)
