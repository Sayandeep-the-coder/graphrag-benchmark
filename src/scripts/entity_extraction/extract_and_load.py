"""
Entity Extraction & Graph Loading Pipeline

Two-stage pipeline:
1. Extract entities from unified corpus (GLiNER or Gemini-based)
2. Load extracted entities + relationships into TigerGraph

This script works with OR without GLiNER installed, falling back
to Gemini-based extraction if GLiNER is unavailable.
"""

import os
import sys
import json
import time
import re
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CORPUS_PATH = "data/processed/unified_corpus.json"
ENTITIES_PATH = "data/processed/extracted_entities.json"
RELATIONSHIPS_PATH = "data/processed/extracted_relationships.json"
GRAPH_LOAD_PATH = "data/processed/graph_load_ready.json"


# ── Stage 1: Entity Extraction ──

RELATIONSHIP_PROMPT = """You are a medical knowledge extraction system.
Given this medical text, extract relationships in this exact JSON format only.
No preamble. No explanation. JSON only.

Text: {text}

Extract relationships of these types only:
- INTERACTS_WITH: {{"type": "INTERACTS_WITH", "from": "drug1", "to": "drug2", "severity": "mild|moderate|severe|contraindicated", "mechanism": "description"}}
- CAUSES: {{"type": "CAUSES", "from": "drug", "to": "adverse_event", "severity": "mild|moderate|severe|fatal"}}
- TREATS: {{"type": "TREATS", "from": "drug", "to": "disease", "first_line": true|false}}
- CONTRAINDICATED_FOR: {{"type": "CONTRAINDICATED_FOR", "from": "drug", "to": "disease", "reason": "description", "absolute": true|false}}
- PRESENTS_AS: {{"type": "PRESENTS_AS", "from": "disease", "to": "symptom", "frequency": 0.0-1.0}}
- METABOLIZED_BY: {{"type": "METABOLIZED_BY", "from": "drug", "to": "enzyme", "is_inhibitor": true|false}}

Return a JSON array. If no relationships found, return [].
"""


LLM_MODEL = os.getenv("LLM_MODEL", "models/gemma-4-26b-a4b-it")


def extract_relationships_gemini(text: str, max_retries: int = 3) -> list[dict]:
    """Extract relationships from text using Gemini API."""
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=RELATIONSHIP_PROMPT.format(text=text[:3000]),
                config={"temperature": 0.1, "max_output_tokens": 2048}
            )
            raw_text = response.text or "[]"

            # Extract JSON from response
            json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  ⚠ Extraction failed after {max_retries} attempts: {e}")
                return []


def extract_from_structured_data(corpus: list[dict]) -> dict:
    """
    Extract entities and relationships from structured data
    (drugbank_seed, disease_symptom_dataset) without using LLM.
    """
    vertices = {
        "Drug": {},
        "Disease": {},
        "Symptom": {},
        "Enzyme": {},
        "Adverse_Event": {},
        "Treatment_Guideline": {},
    }
    edges = []

    for doc in corpus:
        source = doc.get("source", "")

        if source == "drugbank_seed":
            # Drug vertex
            drug_id = doc["id"]
            vertices["Drug"][drug_id] = {
                "drug_id": drug_id,
                "name": doc["name"],
                "generic_name": doc.get("generic_name", doc["name"].lower()),
                "drug_class": doc.get("drug_class", ""),
                "half_life_hours": doc.get("half_life_hours", 0),
                "metabolism_pathway": doc.get("metabolism_pathway", ""),
            }

            # Drug interactions (INTERACTS_WITH edges)
            for interacting_drug in doc.get("interactions", []):
                edges.append({
                    "type": "INTERACTS_WITH",
                    "from_type": "Drug", "from_id": drug_id,
                    "to_type": "Drug", "to_name": interacting_drug,
                    "severity": "moderate",
                    "mechanism": "clinical"
                })

            # Adverse events (CAUSES edges)
            for ae in doc.get("adverse_events", []):
                ae_id = "AE_" + re.sub(r'[^a-zA-Z0-9]', '_', ae).lower()
                vertices["Adverse_Event"][ae_id] = {
                    "event_id": ae_id,
                    "description": ae,
                    "severity": "moderate",
                }
                edges.append({
                    "type": "CAUSES",
                    "from_type": "Drug", "from_id": drug_id,
                    "to_type": "Adverse_Event", "to_id": ae_id,
                    "severity": "moderate"
                })

            # Contraindications
            for ci in doc.get("contraindications", []):
                edges.append({
                    "type": "CONTRAINDICATED_FOR",
                    "from_type": "Drug", "from_id": drug_id,
                    "to_type": "Disease", "to_name": ci,
                    "reason": ci,
                    "absolute": True
                })

            # Enzyme metabolism (METABOLIZED_BY edges)
            for pathway in doc.get("metabolism_pathway", "").split(","):
                pathway = pathway.strip()
                if pathway and pathway != "Renal" and pathway != "Hepatic":
                    enz_id = "ENZ_" + pathway.replace(" ", "_")
                    vertices["Enzyme"][enz_id] = {
                        "enzyme_id": enz_id,
                        "name": pathway,
                        "type": "CYP450" if pathway.startswith("CYP") else "transporter",
                    }
                    edges.append({
                        "type": "METABOLIZED_BY",
                        "from_type": "Drug", "from_id": drug_id,
                        "to_type": "Enzyme", "to_id": enz_id,
                        "is_substrate": True,
                        "is_inhibitor": False,
                        "is_inducer": False,
                    })

        elif source == "disease_symptom_dataset":
            # Disease vertex
            disease_id = doc["id"]
            vertices["Disease"][disease_id] = {
                "disease_id": disease_id,
                "name": doc["name"],
                "icd_code": doc.get("icd_code", ""),
                "category": doc.get("category", ""),
                "chronic": doc.get("chronic", False),
            }

            # Symptom vertices + PRESENTS_AS edges
            for symptom in doc.get("symptoms", []):
                sym_id = "SYM_" + re.sub(r'[^a-zA-Z0-9]', '_', symptom["name"]).lower()
                vertices["Symptom"][sym_id] = {
                    "symptom_id": sym_id,
                    "name": symptom["name"],
                    "severity_default": "moderate",
                }
                edges.append({
                    "type": "PRESENTS_AS",
                    "from_type": "Disease", "from_id": disease_id,
                    "to_type": "Symptom", "to_id": sym_id,
                    "frequency": symptom.get("frequency", 0.5),
                    "early_sign": symptom.get("early_sign", False),
                })
                # Reverse: INDICATES
                edges.append({
                    "type": "INDICATES",
                    "from_type": "Symptom", "from_id": sym_id,
                    "to_type": "Disease", "to_id": disease_id,
                    "specificity": symptom.get("frequency", 0.5),
                    "sensitivity": 0.5,
                })

            # TREATS edges
            for drug_name in doc.get("first_line_drugs", []):
                edges.append({
                    "type": "TREATS",
                    "from_type": "Drug", "from_name": drug_name,
                    "to_type": "Disease", "to_id": disease_id,
                    "first_line": True,
                })
            for drug_name in doc.get("second_line_drugs", []):
                edges.append({
                    "type": "TREATS",
                    "from_type": "Drug", "from_name": drug_name,
                    "to_type": "Disease", "to_id": disease_id,
                    "first_line": False,
                })

            # COMORBID_WITH edges
            for comorbidity in doc.get("comorbidities", []):
                edges.append({
                    "type": "COMORBID_WITH",
                    "from_type": "Disease", "from_id": disease_id,
                    "to_type": "Disease", "to_name": comorbidity,
                    "correlation_strength": 0.6,
                    "bidirectional": True,
                })

        elif doc.get("source_type") == "guideline":
            guideline_id = doc["id"]
            vertices["Treatment_Guideline"][guideline_id] = {
                "guideline_id": guideline_id,
                "source": doc.get("source", ""),
                "year": int(doc.get("year", 0) or 0),
                "recommendation": doc.get("recommendation", doc.get("text", ""))[:500],
                "evidence_level": doc.get("evidence_level", ""),
            }

            drug_name = doc.get("drug")
            if drug_name:
                edges.append({
                    "type": "RECOMMENDED_BY",
                    "from_type": "Treatment_Guideline", "from_id": guideline_id,
                    "to_type": "Drug", "to_name": drug_name,
                    "for_disease": doc.get("for_disease", ""),
                    "year": int(doc.get("year", 0) or 0),
                })

            for other_guideline_id in doc.get("contradicts", []):
                edges.append({
                    "type": "CONTRADICTS",
                    "from_type": "Treatment_Guideline", "from_id": guideline_id,
                    "to_type": "Treatment_Guideline", "to_id": other_guideline_id,
                    "on_drug": drug_name or "",
                    "reason": "Guideline recommendation differs by year, population, or indication.",
                })

    return {"vertices": vertices, "edges": edges}


def run_extraction(use_gemini_for_unstructured: bool = False):
    """Run the full entity extraction pipeline."""

    print("=" * 60)
    print("  GraphRAG — Entity Extraction Pipeline")
    print("=" * 60)

    # Load corpus
    if not os.path.exists(CORPUS_PATH):
        print(f"⚠ Corpus not found at {CORPUS_PATH}")
        print("  Run: python scripts/data_collection/collect_all.py first")
        return

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    print(f"  Loaded {len(corpus)} documents from corpus")

    # ── Extract from structured data ──
    print("\n[1/2] Extracting from structured data...")
    graph_data = extract_from_structured_data(corpus)

    v_counts = {k: len(v) for k, v in graph_data["vertices"].items()}
    print(f"  Vertices: {v_counts}")
    print(f"  Edges: {len(graph_data['edges'])}")

    # ── Optional: Gemini extraction for unstructured text ──
    if use_gemini_for_unstructured:
        print("\n[2/2] Extracting from unstructured text (Gemini)...")
        unstructured = [d for d in corpus if d.get("source") in ("pubmed", "fda_faers")]
        print(f"  Processing {len(unstructured)} unstructured documents...")

        extra_rels = []
        for i, doc in enumerate(unstructured[:50]):  # Limit to 50 for free tier
            text = doc.get("text", "")
            if text:
                rels = extract_relationships_gemini(text)
                extra_rels.extend(rels)
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i + 1}/{min(len(unstructured), 50)}")
                time.sleep(4)  # Rate limit: 15 req/min

        print(f"  Extracted {len(extra_rels)} additional relationships")
        graph_data["edges"].extend(extra_rels)
    else:
        print("\n[2/2] Skipping unstructured extraction (use --gemini flag to enable)")

    # ── Save extracted data ──
    os.makedirs("data/processed", exist_ok=True)
    with open(GRAPH_LOAD_PATH, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print("  EXTRACTION COMPLETE")
    print(f"{'=' * 60}")
    total_verts = sum(len(v) for v in graph_data["vertices"].values())
    print(f"  Total vertices: {total_verts}")
    print(f"  Total edges   : {len(graph_data['edges'])}")
    print(f"  Output        : {GRAPH_LOAD_PATH}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    use_gemini = "--gemini" in sys.argv
    run_extraction(use_gemini_for_unstructured=use_gemini)
