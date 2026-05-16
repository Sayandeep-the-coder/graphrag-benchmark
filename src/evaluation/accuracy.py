"""
Combined accuracy evaluation — LLM-as-a-Judge + BERTScore.

Runs both evaluation methods on pipeline outputs and combines
results into a unified report with bonus achievement tracking.
"""

from src.evaluation.llm_judge import batch_judge
try:
    from src.evaluation.bertscore_eval import compute_bertscore
    BERTSCORE_AVAILABLE = True
except ImportError:
    BERTSCORE_AVAILABLE = False


def evaluate_pipeline(
    pipeline_name: str,
    questions: list[str],
    answers: list[str],
    ground_truths: list[str],
) -> dict:
    """
    Evaluate a single pipeline using both LLM-Judge and BERTScore.

    Args:
        pipeline_name: Display name of the pipeline.
        questions: List of original questions.
        answers: List of pipeline-generated answers.
        ground_truths: List of correct reference answers.

    Returns:
        Dict with pipeline name, llm_judge results, bertscore results,
        and max_bonus_achieved flag (True if both bonuses hit).
    """
    judge_results = batch_judge(questions, answers, ground_truths)
    
    if BERTSCORE_AVAILABLE:
        bert_results = compute_bertscore(answers, ground_truths)
        both_bonus = (
            judge_results["bonus_achieved"]
            and (bert_results["bonus_achieved_raw"] or bert_results["bonus_achieved_rescaled"])
        )
    else:
        bert_results = {"f1": 0, "precision": 0, "recall": 0, "f1_rescaled": 0, "bonus_achieved_raw": False, "bonus_achieved_rescaled": False, "message": "BERTScore disabled (Lite Build)"}
        both_bonus = False

    return {
        "pipeline": pipeline_name,
        "llm_judge": judge_results,
        "bertscore": bert_results,
        "max_bonus_achieved": both_bonus,
    }


def evaluate_all_pipelines(
    questions: list[str],
    p1_answers: list[str],
    p2_answers: list[str],
    ground_truths: list[str],
    p3_answers: list[str] | None = None,
) -> dict:
    """
    Evaluate all pipelines and return combined results.

    Args:
        questions: List of original questions.
        p1_answers: Pipeline 1 (LLM-Only) answers.
        p2_answers: Pipeline 2 (Basic RAG) answers.
        ground_truths: List of correct reference answers.
        p3_answers: Pipeline 3 (GraphRAG) answers.

    Returns:
        Dict with keys "LLM-Only", "Basic-RAG", "GraphRAG",
        each containing evaluate_pipeline() results.
    """
    results = {
        "LLM-Only": evaluate_pipeline("LLM-Only", questions, p1_answers, ground_truths),
        "Basic-RAG": evaluate_pipeline("Basic-RAG", questions, p2_answers, ground_truths),
    }
    if p3_answers is not None:
        results["GraphRAG"] = evaluate_pipeline("GraphRAG", questions, p3_answers, ground_truths)
    return results
