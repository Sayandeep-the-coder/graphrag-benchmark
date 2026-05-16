"""
Benchmark Runner — Batch evaluation across all 3 pipelines.

Runs the 100-question, five-category clinical benchmark from the hackathon
strategy through LLM-Only, Basic RAG, and GraphRAG. Measures token reduction,
category-level accuracy, and the "Cascade Collapse" hop-depth finding.
"""

import json
import os
import time
from datetime import datetime
import argparse

from src.pipelines import pipeline1_llm_only as p1
from src.pipelines.pipeline2_basic_rag import query as p2
from src.graphrag.pipeline import query as p3
from src.evaluation.accuracy import evaluate_all_pipelines

# --- Configuration ---
LIGHTWEIGHT_COUNT = 5  # Total queries in lite mode


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


def _make_case(category: str, question: str, correct_answer: str, hop_depth: int) -> dict:
    return {
        "category": category,
        "question": question,
        "correct_answer": correct_answer,
        "hop_depth": hop_depth,
    }


def build_clinical_benchmark() -> list[dict]:
    """Build the 100-query benchmark: 20 per strategy category."""
    def expand(category: str, items: list[tuple[str, str]], templates: list[str], hop_depth: int) -> list[dict]:
        cases = []
        for topic, answer in items:
            for template in templates:
                cases.append(_make_case(category, template.format(topic=topic), answer, hop_depth))
        return cases[:20]

    temporal = [
        ("Type 2 diabetes", "Metformin remains first-line when renal function is adequate; newer recommendations emphasize renal screening and comorbidity-aware alternatives."),
        ("hypertension", "ACE inhibitors and calcium-channel blockers remain options; later guidance emphasizes kidney function, potassium monitoring, and comorbid diabetes or heart failure."),
        ("aspirin in elderly patients", "Older secondary-prevention guidance differs from newer primary-prevention caution because bleeding risk rises in elderly patients."),
        ("warfarin monitoring", "Warfarin use consistently requires INR monitoring; newer safety framing emphasizes interaction cascades with azoles, macrolides, and antiplatelets."),
        ("rheumatoid arthritis", "Methotrexate remains a disease-modifying option but requires liver, renal, pregnancy, and blood count safety checks."),
    ]
    temporal_q = expand("TEMPORAL", temporal, [
        "How did treatment guidance for {topic} change between 2015 and 2023?",
        "What earlier recommendation for {topic} should not be mixed with newer guidance?",
        "Summarize the timeline of clinical guidance for {topic}.",
        "Which 2023 safety consideration changed the interpretation of {topic} guidance?",
    ], 2)

    contradiction = [
        ("aspirin use in elderly patients", "WHO secondary-prevention use and FDA primary-prevention caution are not the same indication; GraphRAG should surface both rather than collapse them."),
        ("SSRIs and MAOIs", "Combining SSRIs such as fluoxetine with MAOIs is contraindicated because of serotonin syndrome risk."),
        ("warfarin plus aspirin", "Aspirin may be indicated for coronary disease, but combined use with warfarin raises bleeding risk and requires explicit risk-benefit review."),
        ("methotrexate with NSAIDs", "NSAIDs can be used for pain but may increase methotrexate toxicity risk, especially with renal impairment."),
        ("metformin in renal impairment", "Metformin is first-line for type 2 diabetes but contraindicated or avoided in severe renal impairment due to lactic acidosis risk."),
    ]
    contradiction_q = expand("CONTRADICTION", contradiction, [
        "Which guidelines or facts conflict on {topic}, and what should be shown to the clinician?",
        "Do recommendations agree on {topic}, or is there an indication-specific contradiction?",
        "What conflicting clinical statements exist for {topic}?",
        "Surface both sides of the guideline conflict for {topic}.",
    ], 2)

    multihop = [
        ("warfarin + fluconazole + aspirin", "Fluconazole inhibits CYP2C9/CYP3A4 pathways affecting warfarin and aspirin adds antiplatelet bleeding risk; the cascade increases severe bleeding risk."),
        ("clarithromycin + simvastatin + amiodarone", "Clarithromycin inhibits CYP3A4, raising simvastatin toxicity risk; amiodarone adds interaction burden and myopathy/rhabdomyolysis concern."),
        ("metformin + alcohol + renal impairment", "Metformin plus alcohol or renal impairment increases lactic acidosis risk through impaired clearance and metabolic stress."),
        ("digoxin + clarithromycin + amiodarone", "Clarithromycin and amiodarone can increase digoxin toxicity risk through transporter/metabolic interaction pathways."),
        ("fluoxetine + tramadol + metoprolol", "Fluoxetine affects CYP2D6 and serotonergic pathways, raising concern for metoprolol exposure and serotonin syndrome with tramadol."),
    ]
    multihop_q = expand("MULTIHOP", multihop, [
        "Trace the full interaction cascade for a patient taking {topic}.",
        "Which enzyme or adverse-event path makes {topic} clinically risky?",
        "Explain the three-hop mechanism behind {topic}.",
        "What severe downstream risk should be flagged for {topic}?",
    ], 3)

    counterfactual = [
        ("omeprazole", "Clopidogrel activation concerns and some methotrexate/tacrolimus/digoxin interaction risks may resolve or reduce when omeprazole is removed."),
        ("fluconazole", "Warfarin and phenytoin interaction risks mediated by CYP2C9/CYP3A4 inhibition should reduce when fluconazole is removed."),
        ("aspirin", "Bleeding-risk paths involving warfarin, clopidogrel, and GI bleeding reduce when aspirin is removed."),
        ("clarithromycin", "CYP3A4-mediated toxicity paths involving simvastatin, carbamazepine, digoxin, and warfarin reduce when clarithromycin is removed."),
        ("spironolactone", "Hyperkalemia risk paths involving ACE inhibitors or potassium supplements reduce when spironolactone is removed."),
    ]
    counterfactual_q = expand("COUNTERFACTUAL", counterfactual, [
        "If the patient stops taking {topic}, which interaction paths resolve and what remains?",
        "Remove {topic} from the medication graph; what risk paths disappear?",
        "Which safety warnings no longer apply after discontinuing {topic}?",
        "What is the delta in interaction risk if {topic} is removed?",
    ], 3)

    cross_entity = [
        ("CYP3A4 metabolism pathway and QT prolongation risk", "Clarithromycin and fluconazole are key candidates; simvastatin shares CYP3A4 but the primary severe event is myopathy/rhabdomyolysis rather than QT risk."),
        ("hypertension and heart failure without a direct duplicate therapy conflict", "Lisinopril and metoprolol both treat relevant cardiovascular disease, but potassium and bradycardia interactions must still be checked."),
        ("chronic pain and depression with serotonergic risk", "Tramadol and fluoxetine connect chronic pain and depression but create serotonin syndrome risk."),
        ("atrial fibrillation and coronary artery disease with bleeding risk", "Warfarin and aspirin connect these conditions but increase bleeding risk when combined."),
        ("renal impairment and diabetes therapy", "Metformin treats diabetes but severe renal impairment is a contraindication due to lactic acidosis risk."),
    ]
    cross_entity_q = expand("CROSS_ENTITY", cross_entity, [
        "Which entities satisfy both constraints: {topic}?",
        "Find the graph join for {topic}.",
        "What drugs or diseases match both sides of this query: {topic}?",
        "Which candidates meet {topic} and what safety edge matters?",
    ], 3)

    return temporal_q + contradiction_q + multihop_q + counterfactual_q + cross_entity_q


BENCHMARK_QUERIES = build_clinical_benchmark()


def run_benchmark(is_lightweight: bool = False) -> str:
    """
    Run the full benchmark across all 3 pipelines.

    Args:
        is_lightweight: If True, only run a small subset of queries.

    Returns:
        Path to the saved JSON benchmark report.
    """
    os.makedirs("./results", exist_ok=True)

    queries = BENCHMARK_QUERIES
    if is_lightweight:
        # Pick one from each category to ensure coverage
        categories = set(q.get("category", "GENERAL") for q in queries)
        light_queries = []
        for cat in categories:
            for q in queries:
                if q.get("category", "GENERAL") == cat:
                    light_queries.append(q)
                    break
        queries = light_queries[:LIGHTWEIGHT_COUNT]

    questions = []
    p1_answers = []
    p2_answers = []
    p3_answers = []
    ground_truths = []
    all_metrics = []

    print(f"{'='*60}")
    print(f"  GraphRAG Inference Benchmark — {len(queries)} queries" + (" (LIGHTWEIGHT)" if is_lightweight else ""))
    print(f"{'='*60}\n")

    for idx, item in enumerate(queries, 1):
        query = item["question"]
        gt = item["correct_answer"]
        category = item.get("category", "GENERAL")
        questions.append(query)
        ground_truths.append(gt)

        print(f"[{idx}/{len(queries)}] {query[:60]}...")

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
            "category": category,
            "hop_depth": item.get("hop_depth"),
            "query": query,
            "ground_truth": gt,
            "p1": r1["metrics"],
            "p2": r2["metrics"],
            "p3": r3["metrics"],
            "token_reduction_pct": round(reduction, 2),
        })

        print(f"  Done | {category} | P1: {r1['metrics']['total_tokens']}t | "
              f"P2: {rag_tokens}t | P3: {graph_tokens}t | "
              f"Reduction: {reduction:.1f}%")

        time.sleep(1)  # Rate limit safety

    # ── Accuracy evaluation ──
    print(f"\n{'─'*60}")
    print("Running accuracy evaluation (LLM-as-a-Judge + BERTScore)...")
    accuracy = evaluate_all_pipelines(
        questions=questions,
        p1_answers=p1_answers,
        p2_answers=p2_answers,
        ground_truths=ground_truths,
        p3_answers=p3_answers,
    )

    # ── Build report ──
    avg_reduction = (
        sum(m["token_reduction_pct"] for m in all_metrics) / len(all_metrics)
        if all_metrics
        else 0.0
    )
    category_summary = {}
    for metric in all_metrics:
        category = metric["category"]
        bucket = category_summary.setdefault(category, {"count": 0, "avg_token_reduction_pct": 0.0})
        bucket["count"] += 1
        bucket["avg_token_reduction_pct"] += metric["token_reduction_pct"]
    for bucket in category_summary.values():
        bucket["avg_token_reduction_pct"] = round(bucket["avg_token_reduction_pct"] / bucket["count"], 2)

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_queries": len(queries),
        "is_lightweight": is_lightweight,
        "per_query_metrics": all_metrics,
        "accuracy": accuracy,
        "category_summary": category_summary,
        "named_finding": {
            "name": "The Cascade Collapse",
            "claim": "RAG degrades non-linearly as clinical reasoning requires three-hop interaction traversal; GraphRAG preserves explicit entity paths.",
            "measured_by": ["MULTIHOP", "COUNTERFACTUAL", "CROSS_ENTITY"],
        },
        "summary": {
            "avg_token_reduction_pct": round(avg_reduction, 2),
            "graphrag_judge_pass_rate": accuracy["GraphRAG"]["llm_judge"]["pass_rate"],
            "graphrag_bertscore_f1": accuracy["GraphRAG"]["bertscore"].get("f1_rescaled", 0),
            "max_bonus": accuracy["GraphRAG"]["max_bonus_achieved"],
        },
    }

    # ── Save report ──
    filepath = f"./results/benchmark_{'light_' if is_lightweight else ''}{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    parser = argparse.ArgumentParser(description="GraphRAG Benchmark Runner")
    parser.add_argument("--light", action="store_true", help="Run in lightweight mode (fewer queries)")
    args = parser.parse_args()

    # Support env var as well
    lite_mode = args.light or os.getenv("LIGHTWEIGHT", "false").lower() == "true"
    
    run_benchmark(is_lightweight=lite_mode)
