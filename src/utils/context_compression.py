"""
Context Compression — Structured JSON Context for GraphRAG

Converts graph traversal results into minimal, structured JSON context
that achieves ~600 tokens vs RAG's ~4,500 tokens.

Key insight: Structured JSON = dense information. No prose repetition.
No chunk overlap. No irrelevant context.
"""

import json


def compress_graph_context(graph_result: dict) -> str:
    """
    Convert graph traversal result to minimal structured context.

    Target: ~600 tokens (vs RAG's ~4,500 tokens = 87% reduction)

    Args:
        graph_result: Raw response from GraphRAG service or GSQL query

    Returns:
        Compressed JSON string ready for LLM prompt injection
    """

    compressed = {}

    # ── Critical interactions (severity filter) ──
    interactions = graph_result.get("interactions", [])
    critical = [
        {
            "drugs": [i.get("drug1", i.get("from", "")), i.get("drug2", i.get("to", ""))],
            "severity": i.get("severity", "unknown"),
            "mechanism": i.get("mechanism", ""),
            "action": i.get("clinical_action", i.get("action", "Monitor")),
        }
        for i in interactions
        if i.get("severity") in ("severe", "contraindicated", "moderate")
    ]
    if critical:
        compressed["critical_interactions"] = critical

    # ── Diagnosis chain ──
    diagnosis = graph_result.get("symptom_to_disease_chain", graph_result.get("diagnosis_path", []))
    if diagnosis:
        if isinstance(diagnosis, list):
            compressed["diagnosis_path"] = diagnosis[:5]  # Top 5
        else:
            compressed["diagnosis_path"] = diagnosis

    # ── Safe alternatives ──
    alternatives = graph_result.get("safe_alternatives", graph_result.get("non_interacting_alternatives", []))
    if alternatives:
        compressed["safe_alternatives"] = alternatives[:3]

    # ── Contraindications ──
    contras = graph_result.get("contraindications", graph_result.get("absolute_contraindications", []))
    if contras:
        compressed["contraindications"] = contras[:5]

    # ── Enzyme cascades ──
    enzymes = graph_result.get("enzyme_cascades", graph_result.get("affected_enzymes", []))
    if enzymes:
        compressed["enzyme_pathways"] = enzymes[:3]

    # ── Adverse events ──
    adverse = graph_result.get("adverse_events", graph_result.get("shared_adverse", []))
    if adverse:
        severe = [a for a in adverse if a.get("severity") in ("severe", "fatal")]
        if severe:
            compressed["severe_adverse_events"] = [
                {"event": a.get("description", a.get("name", "")),
                 "severity": a.get("severity", ""),
                 "drugs": a.get("drugs", [])}
                for a in severe[:3]
            ]

    # ── Evidence/guideline references ──
    guidelines = graph_result.get("guidelines", graph_result.get("treatment_guidelines", []))
    if guidelines:
        compressed["evidence"] = [
            {"source": g.get("source", ""), "recommendation": g.get("recommendation", ""),
             "level": g.get("evidence_level", "")}
            for g in guidelines[:2]
        ]

    # If no structured data was found, pass through the raw answer
    if not compressed:
        raw_answer = graph_result.get("answer", graph_result.get("response", ""))
        if raw_answer:
            compressed["context"] = raw_answer[:2000]

    return json.dumps(compressed, separators=(',', ':'))  # Compact JSON


def build_graphrag_prompt(query: str, compressed_context: str) -> str:
    """
    Build the final LLM prompt with compressed graph context.

    Target prompt: ~600 tokens total
    """
    return (
        "You are a clinical decision support system. "
        "Answer using ONLY the structured graph context below. "
        "Be specific about drug names, severity levels, and clinical actions. "
        "If interactions are found, list them with severity.\n\n"
        f"Graph Context: {compressed_context}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )


def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 chars for English)."""
    return len(text) // 4
