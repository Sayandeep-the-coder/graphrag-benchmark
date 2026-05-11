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
        "question": "Who invented the World Wide Web?",
        "correct_answer": "Tim Berners-Lee invented the World Wide Web in 1989 while working at CERN.",
    },
    {
        "question": "What is the capital of Japan and what is its population?",
        "correct_answer": "Tokyo is the capital of Japan with a population of approximately 14 million in the city proper.",
    },
    {
        "question": "Which programming language was created by Guido van Rossum and in what year?",
        "correct_answer": "Python was created by Guido van Rossum and first released in 1991.",
    },
    {
        "question": "What ocean does the Amazon River empty into?",
        "correct_answer": "The Amazon River empties into the Atlantic Ocean.",
    },
    {
        "question": "Who wrote 'A Brief History of Time' and what is it about?",
        "correct_answer": "Stephen Hawking wrote 'A Brief History of Time', a book about cosmology covering topics like the Big Bang, black holes, and the nature of time.",
    },
    {
        "question": "Who developed the theory of general relativity?",
        "correct_answer": "Albert Einstein developed the theory of general relativity, published in 1915.",
    },
    {
        "question": "What is the capital of France and what river runs through it?",
        "correct_answer": "Paris is the capital of France. The Seine river runs through it.",
    },
    {
        "question": "What is photosynthesis and which organisms perform it?",
        "correct_answer": "Photosynthesis is the process by which plants, algae, and some bacteria convert sunlight, water, and carbon dioxide into glucose and oxygen.",
    },
    {
        "question": "Who painted the Mona Lisa and where is it displayed?",
        "correct_answer": "Leonardo da Vinci painted the Mona Lisa. It is displayed at the Louvre Museum in Paris, France.",
    },
    {
        "question": "What are the three laws of motion and who formulated them?",
        "correct_answer": "Isaac Newton formulated the three laws of motion: 1) an object at rest stays at rest unless acted upon by a force, 2) force equals mass times acceleration, 3) every action has an equal and opposite reaction.",
    },
    {
        "question": "What is the largest planet in the solar system and how many moons does it have?",
        "correct_answer": "Jupiter is the largest planet in the solar system with 95 known moons.",
    },
    {
        "question": "Who discovered penicillin and in what year?",
        "correct_answer": "Alexander Fleming discovered penicillin in 1928 at St Mary's Hospital in London.",
    },
    {
        "question": "What is the Great Wall of China and how long is it?",
        "correct_answer": "The Great Wall of China is a series of fortifications built across northern China. It stretches approximately 21,196 kilometers (13,171 miles).",
    },
    {
        "question": "What is DNA and who discovered its double helix structure?",
        "correct_answer": "DNA (deoxyribonucleic acid) is the molecule that carries genetic information. James Watson and Francis Crick discovered its double helix structure in 1953, with critical contributions from Rosalind Franklin.",
    },
    {
        "question": "What is the theory of evolution and who proposed it?",
        "correct_answer": "The theory of evolution by natural selection was proposed by Charles Darwin in his 1859 book 'On the Origin of Species'. It explains how species change over time through natural selection.",
    },
    {
        "question": "What is the speed of light in a vacuum?",
        "correct_answer": "The speed of light in a vacuum is approximately 299,792,458 meters per second (about 3 × 10^8 m/s).",
    },
    {
        "question": "Who was the first person to walk on the Moon and when?",
        "correct_answer": "Neil Armstrong was the first person to walk on the Moon on July 20, 1969, during the Apollo 11 mission.",
    },
    {
        "question": "What is the Pythagorean theorem?",
        "correct_answer": "The Pythagorean theorem states that in a right triangle, the square of the hypotenuse equals the sum of the squares of the other two sides (a² + b² = c²).",
    },
    {
        "question": "What is the periodic table and who created it?",
        "correct_answer": "The periodic table is a tabular arrangement of chemical elements organized by atomic number. Dmitri Mendeleev created the first widely recognized periodic table in 1869.",
    },
    {
        "question": "What is the Renaissance and when did it occur?",
        "correct_answer": "The Renaissance was a cultural and intellectual movement that began in Italy in the 14th century and spread across Europe through the 17th century, marking the transition from the Middle Ages to modernity.",
    },
    {
        "question": "What is the greenhouse effect and how does it relate to climate change?",
        "correct_answer": "The greenhouse effect is the process where greenhouse gases in Earth's atmosphere trap heat from the sun, warming the planet. Increased emissions of CO2 and methane from human activities enhance this effect, driving global climate change.",
    },
    {
        "question": "Who composed the four seasons and what nationality were they?",
        "correct_answer": "Antonio Vivaldi, an Italian composer, composed The Four Seasons (Le quattro stagioni), a set of four violin concertos published in 1725.",
    },
    {
        "question": "What is the human genome project and when was it completed?",
        "correct_answer": "The Human Genome Project was an international scientific research project to map all genes of the human genome. It was completed in April 2003 after 13 years of work.",
    },
    {
        "question": "What is blockchain technology and what was the first cryptocurrency?",
        "correct_answer": "Blockchain is a distributed ledger technology that records transactions across multiple computers. Bitcoin, created by the pseudonymous Satoshi Nakamoto in 2009, was the first cryptocurrency to use blockchain.",
    },
    {
        "question": "What is the Turing test and who proposed it?",
        "correct_answer": "The Turing test, proposed by Alan Turing in 1950, is a test of a machine's ability to exhibit intelligent behavior indistinguishable from a human.",
    },
    {
        "question": "What is the Hubble Space Telescope and when was it launched?",
        "correct_answer": "The Hubble Space Telescope is a space telescope launched into low Earth orbit in 1990 by the Space Shuttle Discovery. It has provided some of the most detailed visible-light images of distant galaxies.",
    },
    {
        "question": "What are tectonic plates and how do they cause earthquakes?",
        "correct_answer": "Tectonic plates are massive segments of Earth's lithosphere that move, float, and interact. Earthquakes occur when plates collide, separate, or slide past each other, releasing stored energy as seismic waves.",
    },
    {
        "question": "Who wrote Romeo and Juliet and when was it written?",
        "correct_answer": "William Shakespeare wrote Romeo and Juliet, believed to have been written between 1591 and 1596. It is one of the most famous tragedies in English literature.",
    },
    {
        "question": "What is CRISPR and what is it used for?",
        "correct_answer": "CRISPR (Clustered Regularly Interspaced Short Palindromic Repeats) is a gene-editing technology that allows scientists to precisely modify DNA sequences. It is used in genetic research, disease treatment, and agricultural biotechnology.",
    },
    {
        "question": "What is the International Space Station and how many countries are involved?",
        "correct_answer": "The International Space Station (ISS) is a modular space station in low Earth orbit. It is a collaborative project involving 5 space agencies and 15 countries, including the US, Russia, Japan, Canada, and ESA member states.",
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
