"""
LLM-as-a-Judge — Accuracy evaluation using a hosted LLM.

Uses huggingface_hub InferenceClient with Llama-3.1-8B-Instruct
to grade each pipeline answer as PASS or FAIL against ground truth.
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# We use Gemma for the judge to stay consistent with the "Never Gemini" requirement.
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
JUDGE_MODEL = "models/gemma-4-26b-a4b-it"

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
    """
    prompt = JUDGE_PROMPT.format(
        question=question,
        correct=ground_truth,
        answer=answer,
    )

    try:
        response = client.models.generate_content(
            model=JUDGE_MODEL,
            contents=prompt,
        )
        if response and hasattr(response, "text") and response.text:
            raw_output = response.text.strip()
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
