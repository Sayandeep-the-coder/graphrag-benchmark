"""
BERTScore evaluation — Semantic similarity scoring.

Uses the HuggingFace `evaluate` library with rescale_with_baseline=True
for an honest 0–1 scale. Runs locally on CPU.
"""

import evaluate

_bertscore_metric = None

def compute_bertscore(candidates: list[str], references: list[str]) -> dict:
    global _bertscore_metric
    if _bertscore_metric is None:
        _bertscore_metric = evaluate.load("bertscore")
    bertscore = _bertscore_metric
    """
    Compute BERTScore between candidate answers and reference answers.

    Uses rescale_with_baseline=True for honest 0–1 scoring where
    0 = random and 1 = perfect semantic match.

    Args:
        candidates: List of pipeline-generated answers.
        references: List of correct reference answers.

    Returns:
        Dict with precision, recall, f1_rescaled, f1_raw,
        and bonus achievement flags.
    """
    results = bertscore.compute(
        predictions=candidates,
        references=references,
        lang="en",
        rescale_with_baseline=True,
    )
    
    if not results or "precision" not in results:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1_rescaled": 0.0,
            "f1_raw": 0.0,
            "bonus_achieved_rescaled": False,
            "bonus_achieved_raw": False,
        }

    # Average scores across all pairs
    precision = sum(results["precision"]) / len(results["precision"])
    recall = sum(results["recall"]) / len(results["recall"])
    f1_rescaled = sum(results["f1"]) / len(results["f1"])

    # Also compute raw (non-rescaled) for bonus check
    raw_results = bertscore.compute(
        predictions=candidates,
        references=references,
        lang="en",
        rescale_with_baseline=False,
    )
    f1_raw = (sum(raw_results["f1"]) / len(raw_results["f1"])) if raw_results and "f1" in raw_results else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_rescaled": round(f1_rescaled, 4),
        "f1_raw": round(f1_raw, 4),
        "bonus_achieved_rescaled": f1_rescaled >= 0.55,
        "bonus_achieved_raw": f1_raw >= 0.88,
    }
