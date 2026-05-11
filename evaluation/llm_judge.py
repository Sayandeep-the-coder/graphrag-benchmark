"""
LLM-as-a-Judge — Accuracy evaluation using a hosted LLM.

Uses huggingface_hub InferenceClient with Llama-3.1-8B-Instruct
to grade each pipeline answer as PASS or FAIL against ground truth.
"""

import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
JUDGE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

client = InferenceClient(model=JUDGE_MODEL, token=HF_TOKEN)

JUDGE_PROMPT = """Grade the system's answer.
Question: {question}
Correct answer: {correct}
System answer: {answer}

Reply with only PASS or FAIL.
PASS = the system answer correctly addresses the question with no major errors.
FAIL = the answer is wrong, missing, or contradicts the correct answer."""


def llm_judge(question: str, answer: str, ground_truth: str) -> dict:
    """
    Grade a single answer against ground truth using LLM-as-a-Judge.

    Args:
        question: The original question asked.
        answer: The pipeline's generated answer.
        ground_truth: The correct reference answer.

    Returns:
        Dict with 'verdict' (PASS/FAIL) and 'raw_output'.
    """
    prompt = JUDGE_PROMPT.format(
        question=question,
        correct=ground_truth,
        answer=answer,
    )

    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.0,
        )
        if response and response.choices and response.choices[0].message.content:
            raw_output = response.choices[0].message.content.strip()
        else:
            raw_output = "FAIL (No response)"
    except Exception as e:
        raw_output = f"FAIL (Error: {str(e)})"
    verdict = "PASS" if "PASS" in raw_output.upper() else "FAIL"

    return {"verdict": verdict, "raw_output": raw_output}


def batch_judge(
    questions: list[str],
    answers: list[str],
    ground_truths: list[str],
) -> dict:
    """
    Grade a batch of answers and compute pass rate.

    Args:
        questions: List of original questions.
        answers: List of pipeline-generated answers.
        ground_truths: List of correct reference answers.

    Returns:
        Dict with individual results, pass_count, total, pass_rate,
        and bonus_achieved (True if pass_rate >= 0.90).
    """
    results = []
    for q, a, g in zip(questions, answers, ground_truths):
        result = llm_judge(q, a, g)
        results.append(result)

    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    total = len(results)
    pass_rate = pass_count / total if total > 0 else 0.0

    return {
        "individual": results,
        "pass_count": pass_count,
        "total": total,
        "pass_rate": round(pass_rate, 4),
        "bonus_achieved": pass_rate >= 0.90,
    }
