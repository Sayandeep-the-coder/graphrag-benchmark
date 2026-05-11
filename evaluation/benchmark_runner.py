"""
Benchmark Runner — Batch evaluation across all 3 pipelines.

Runs 30 Wikipedia-domain queries through LLM-Only, Basic RAG, and GraphRAG,
measures token reduction, evaluates accuracy, and saves a JSON report.
"""

import json
import os
import time
from datetime import datetime

from pipelines import pipeline1_llm_only as p1
from pipelines.pipeline2_basic_rag import query as p2
from pipelines.pipeline3_graphrag import query as p3
from evaluation.accuracy import evaluate_all_pipelines

# ──────────────────────────────────────────────────────────────
# 30 Wikipedia-domain benchmark queries with ground truths
# Mix of factual, relational, and multi-entity questions
# ──────────────────────────────────────────────────────────────

BENCHMARK_QUERIES = [
    {
        "question": "What are the symptoms and precautions for a drug reaction?",
        "correct_answer": "Symptoms include burning micturition, itching, skin rash, spotting urination, and stomach pain. Precautions include stopping irritation, consulting a hospital, stopping the drug, and following up.",
    },
    {
        "question": "What are the symptoms of Malaria?",
        "correct_answer": "Symptoms of malaria include chills, diarrhoea, headache, high fever, muscle pain, nausea, sweating, and vomiting.",
    },
    {
        "question": "What precautions should I take for an allergy?",
        "correct_answer": "Precautions for an allergy include applying calamine, covering the area with a bandage, and using ice to compress itching.",
    },
    {
        "question": "What is Hypothyroidism and what are its symptoms?",
        "correct_answer": "Hypothyroidism is a disorder where the thyroid gland does not produce enough thyroid hormone. Symptoms include abnormal menstruation, brittle nails, cold hands and feet, depression, dizziness, enlarged thyroid, fatigue, irritability, lethargy, mood swings, puffy face and eyes, swollen extremities, and weight gain.",
    },
    {
        "question": "What is Psoriasis?",
        "correct_answer": "Psoriasis is a common skin disorder that forms thick, red, bumpy patches covered with silvery scales, mostly appearing on the scalp, elbows, knees, and lower back.",
    },
    {
        "question": "What are the precautions for GERD?",
        "correct_answer": "Avoid fatty spicy food, avoid lying down after eating, maintain a healthy weight, and exercise.",
    },
    {
        "question": "What are the symptoms of chronic cholestasis?",
        "correct_answer": "Symptoms include abdominal pain, itching, loss of appetite, nausea, vomiting, yellowing of eyes, and yellowish skin.",
    },
    {
        "question": "How is Hepatitis A described?",
        "correct_answer": "Hepatitis A is a highly contagious liver infection caused by the hepatitis A virus, affecting the liver's ability to function.",
    },
    {
        "question": "What is Osteoarthritis?",
        "correct_answer": "Osteoarthritis is the most common form of arthritis, occurring when the protective cartilage that cushions the ends of your bones wears down over time.",
    },
    {
        "question": "What precautions should be taken for vertigo (BPPV)?",
        "correct_answer": "Precautions include lying down, avoiding sudden changes in body position, avoiding abrupt head movement, and relaxing.",
    },
    {
        "question": "What are the symptoms of Hypoglycemia?",
        "correct_answer": "Symptoms include anxiety, blurred vision, drying and tingling lips, excessive hunger, fatigue, headache, irritability, nausea, palpitations, slurred speech, sweating, and vomiting.",
    },
    {
        "question": "What precautions should be taken for acne?",
        "correct_answer": "Bathe twice a day, avoid fatty spicy food, drink plenty of water, and avoid using too many products.",
    },
    {
        "question": "What are the symptoms of Diabetes?",
        "correct_answer": "Symptoms include blurred vision, excessive hunger, fatigue, increased appetite, irregular sugar level, lethargy, obesity, polyuria, restlessness, and weight loss.",
    },
    {
        "question": "What is Impetigo?",
        "correct_answer": "Impetigo is a common and highly contagious skin infection that mainly affects infants and children, appearing as red sores that burst and develop honey-colored crusts.",
    },
    {
        "question": "What are the precautions for Hypertension?",
        "correct_answer": "Precautions include meditation, salt baths, reducing stress, and getting proper sleep.",
    },
    {
        "question": "What are the symptoms of peptic ulcer disease?",
        "correct_answer": "Symptoms include abdominal pain, indigestion, internal itching, loss of appetite, passage of gases, and vomiting.",
    },
    {
        "question": "What precautions should be taken for the common cold?",
        "correct_answer": "Drink vitamin C rich drinks, take vapour, avoid cold food, and keep fever in check.",
    },
    {
        "question": "What is Chicken pox and what causes it?",
        "correct_answer": "Chickenpox is a highly contagious disease caused by the varicella-zoster virus (VZV), causing an itchy, blister-like rash.",
    },
    {
        "question": "What are the symptoms of Hyperthyroidism?",
        "correct_answer": "Symptoms include abnormal menstruation, diarrhoea, excessive hunger, fast heart rate, fatigue, irritability, mood swings, muscle weakness, restlessness, sweating, and weight loss.",
    },
    {
        "question": "What precautions should I take for a urinary tract infection?",
        "correct_answer": "Drink plenty of water, increase vitamin C intake, drink cranberry juice, and take probiotics.",
    },
    {
        "question": "What are the symptoms of varicose veins?",
        "correct_answer": "Symptoms include bruising, cramps, fatigue, obesity, prominent veins on calf, swollen blood vessels, and swollen legs.",
    },
    {
        "question": "What is AIDS and what causes it?",
        "correct_answer": "Acquired immunodeficiency syndrome (AIDS) is a chronic, potentially life-threatening condition caused by the human immunodeficiency virus (HIV).",
    },
    {
        "question": "What are the precautions for Typhoid?",
        "correct_answer": "Eat high calorie vegetables, take antibiotic therapy, consult a doctor, and take medication.",
    },
    {
        "question": "What are the symptoms of a Migraine?",
        "correct_answer": "Symptoms include acidity, blurred vision, depression, excessive hunger, headache, indigestion, irritability, stiff neck, and visual disturbances.",
    },
    {
        "question": "What is Bronchial Asthma?",
        "correct_answer": "Bronchial asthma is a medical condition which causes the airway path of the lungs to swell and narrow, producing excess mucus and resulting in coughing, short breath, and wheezing.",
    },
    {
        "question": "What are the symptoms of Jaundice?",
        "correct_answer": "Symptoms include abdominal pain, dark urine, fatigue, high fever, itching, vomiting, weight loss, and yellowish skin.",
    },
    {
        "question": "What precautions should be taken for Dengue?",
        "correct_answer": "Drink papaya leaf juice, avoid fatty spicy food, keep mosquitoes away, and keep hydrated.",
    },
    {
        "question": "What is a Heart attack?",
        "correct_answer": "A heart attack is the death of heart muscle due to the loss of blood supply, usually caused by a complete blockage of a coronary artery.",
    },
    {
        "question": "What are the symptoms of Pneumonia?",
        "correct_answer": "Symptoms include breathlessness, chest pain, chills, cough, fast heart rate, fatigue, high fever, malaise, phlegm, rusty sputum, and sweating.",
    },
    {
        "question": "What precautions should I take for Gastroenteritis?",
        "correct_answer": "Stop eating solid food for a while, try taking small sips of water, rest, and ease back into eating.",
    },
]


def run_benchmark() -> str:
    """
    Run the full benchmark across all 3 pipelines and 30 queries.

    Returns:
        Path to the saved JSON benchmark report.
    """
    os.makedirs("./results", exist_ok=True)

    questions = []
    p1_answers = []
    p2_answers = []
    p3_answers = []
    ground_truths = []
    all_metrics = []

    print(f"{'='*60}")
    print(f"  GraphRAG Inference Benchmark — {len(BENCHMARK_QUERIES)} queries")
    print(f"{'='*60}\n")

    for idx, item in enumerate(BENCHMARK_QUERIES, 1):
        query = item["question"]
        gt = item["correct_answer"]
        questions.append(query)
        ground_truths.append(gt)

        print(f"[{idx}/{len(BENCHMARK_QUERIES)}] {query[:60]}...")

        # Run all 3 pipelines
        r1 = p1.run(query)
        r2 = p2.run(query)
        r3 = p3.run(query)

        p1_answers.append(r1["answer"])
        p2_answers.append(r2["answer"])
        p3_answers.append(r3["answer"])

        # Token reduction per query
        rag_tokens = r2["metrics"]["total_tokens"]
        graph_tokens = r3["metrics"]["total_tokens"]
        reduction = (
            (rag_tokens - graph_tokens) / rag_tokens * 100
            if rag_tokens > 0
            else 0.0
        )

        all_metrics.append({
            "query": query,
            "ground_truth": gt,
            "p1": r1["metrics"],
            "p2": r2["metrics"],
            "p3": r3["metrics"],
            "token_reduction_pct": round(reduction, 2),
        })

        print(f"  ✅ Done | P1: {r1['metrics']['total_tokens']}t | "
              f"P2: {rag_tokens}t | P3: {graph_tokens}t | "
              f"Reduction: {reduction:.1f}%")

        time.sleep(1)  # Rate limit safety

    # ── Accuracy evaluation ──
    print(f"\n{'─'*60}")
    print("Running accuracy evaluation (LLM-as-a-Judge + BERTScore)...")
    accuracy = evaluate_all_pipelines(
        questions, p1_answers, p2_answers, p3_answers, ground_truths
    )

    # ── Build report ──
    avg_reduction = (
        sum(m["token_reduction_pct"] for m in all_metrics) / len(all_metrics)
        if all_metrics
        else 0.0
    )

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_queries": len(BENCHMARK_QUERIES),
        "per_query_metrics": all_metrics,
        "accuracy": accuracy,
        "summary": {
            "avg_token_reduction_pct": round(avg_reduction, 2),
            "graphrag_judge_pass_rate": accuracy["GraphRAG"]["llm_judge"]["pass_rate"],
            "graphrag_bertscore_f1": accuracy["GraphRAG"]["bertscore"]["f1_rescaled"],
            "max_bonus": accuracy["GraphRAG"]["max_bonus_achieved"],
        },
    }

    # ── Save report ──
    filepath = f"./results/benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)

    # ── Print summary ──
    print(f"\n{'='*60}")
    print("  BENCHMARK COMPLETE")
    print(f"{'='*60}")
    print(f"  Total queries        : {report['total_queries']}")
    print(f"  Avg token reduction  : {report['summary']['avg_token_reduction_pct']:.1f}%")
    print(f"  Judge pass rate      : {report['summary']['graphrag_judge_pass_rate']*100:.1f}%")
    print(f"  BERTScore F1 (resc.) : {report['summary']['graphrag_bertscore_f1']:.3f}")
    print(f"  Max bonus achieved   : {'✅ YES' if report['summary']['max_bonus'] else '❌ NO'}")
    print(f"  Report saved to      : {filepath}")
    print(f"{'='*60}")

    return filepath


if __name__ == "__main__":
    run_benchmark()
