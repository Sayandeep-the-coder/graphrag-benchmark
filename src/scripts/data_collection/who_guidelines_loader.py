"""
WHO Essential Medicines / Guideline Loader

Uses a local extracted WHO PDF text file when available and falls back to a
small guideline seed set so the benchmark can run before the full PDF is
processed.

Optional inputs:
  data/raw/who/essential_medicines.txt
  data/raw/who/who_guidelines.json
"""

import json
import os

OUTPUT_DIR = "data/raw/who"


def generate_seed_guidelines() -> list[dict]:
    """Generate authoritative-style guideline records for graph/eval demos."""
    return [
        {
            "id": "WHO-EML-2023-AF-WARFARIN",
            "source": "WHO Essential Medicines List",
            "year": 2023,
            "drug": "Warfarin",
            "for_disease": "Atrial Fibrillation",
            "recommendation": "Warfarin is an oral anticoagulant option requiring INR monitoring; avoid unsafe combinations that increase bleeding risk.",
            "evidence_level": "A",
            "contradicts": [],
            "text": "WHO 2023 guideline: Warfarin treats atrial fibrillation and venous thrombosis but requires INR monitoring. Co-prescribing with antiplatelets, azole antifungals, or macrolide antibiotics can increase bleeding risk.",
            "source_type": "guideline",
        },
        {
            "id": "WHO-EML-2023-DM-METFORMIN",
            "source": "WHO Essential Medicines List",
            "year": 2023,
            "drug": "Metformin",
            "for_disease": "Type 2 Diabetes Mellitus",
            "recommendation": "Metformin remains first-line therapy for type 2 diabetes when renal function is adequate.",
            "evidence_level": "A",
            "contradicts": [],
            "text": "WHO 2023 guideline: Metformin is first-line treatment for type 2 diabetes mellitus when kidney function is adequate. Avoid in severe renal impairment or metabolic acidosis because of lactic acidosis risk.",
            "source_type": "guideline",
        },
        {
            "id": "WHO-EML-2023-HTN-LISINOPRIL",
            "source": "WHO Essential Medicines List",
            "year": 2023,
            "drug": "Lisinopril",
            "for_disease": "Hypertension",
            "recommendation": "ACE inhibitors are recommended antihypertensive options, with monitoring for renal function and potassium.",
            "evidence_level": "A",
            "contradicts": [],
            "text": "WHO 2023 guideline: Lisinopril treats hypertension and heart failure. Monitor creatinine and potassium. Avoid combining with potassium supplements or spironolactone unless closely monitored.",
            "source_type": "guideline",
        },
        {
            "id": "WHO-EML-2023-RA-MTX",
            "source": "WHO Essential Medicines List",
            "year": 2023,
            "drug": "Methotrexate",
            "for_disease": "Rheumatoid Arthritis",
            "recommendation": "Methotrexate is a disease-modifying therapy requiring hepatic, renal, and blood count monitoring.",
            "evidence_level": "A",
            "contradicts": [],
            "text": "WHO 2023 guideline: Methotrexate treats rheumatoid arthritis but is contraindicated in pregnancy and severe renal or hepatic impairment. NSAIDs can increase toxicity risk.",
            "source_type": "guideline",
        },
        {
            "id": "FDA-2023-ASPIRIN-ELDERLY",
            "source": "FDA Safety Communication",
            "year": 2023,
            "drug": "Aspirin",
            "for_disease": "Primary Prevention",
            "recommendation": "Routine aspirin for primary prevention in older adults is discouraged when bleeding risk outweighs benefit.",
            "evidence_level": "B",
            "contradicts": ["WHO-EML-2015-ASPIRIN-CAD"],
            "text": "FDA 2023 guidance: Aspirin for primary prevention in elderly patients is discouraged when bleeding risk is high, especially with anticoagulants such as warfarin.",
            "source_type": "guideline",
        },
        {
            "id": "WHO-EML-2015-ASPIRIN-CAD",
            "source": "WHO Essential Medicines List",
            "year": 2015,
            "drug": "Aspirin",
            "for_disease": "Coronary Artery Disease",
            "recommendation": "Aspirin is used for secondary prevention of coronary artery disease.",
            "evidence_level": "A",
            "contradicts": ["FDA-2023-ASPIRIN-ELDERLY"],
            "text": "WHO 2015 guideline: Aspirin is used for secondary prevention of coronary artery disease. This does not imply routine primary prevention in elderly patients with high bleeding risk.",
            "source_type": "guideline",
        },
    ]


def load_who_guidelines() -> list[dict]:
    """Load local WHO guideline records or seed records."""
    json_path = os.path.join(OUTPUT_DIR, "who_guidelines.json")
    text_path = os.path.join(OUTPUT_DIR, "essential_medicines.txt")

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        print(f"  Loaded {len(records)} WHO guideline records from {json_path}")
        return records

    if os.path.exists(text_path):
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
        records = [
            {
                "id": f"WHO-TEXT-{idx:04d}",
                "source": "WHO Essential Medicines List",
                "year": 2023,
                "text": chunk,
                "source_type": "guideline",
            }
            for idx, chunk in enumerate(chunks, 1)
        ]
        print(f"  Loaded {len(records)} WHO text chunks from {text_path}")
        return records

    print("  WHO files not found; using seed guideline records.")
    return generate_seed_guidelines()


def save_who_guidelines(records: list[dict] | None = None) -> list[dict]:
    """Save WHO guideline records for downstream collection."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if records is None:
        records = load_who_guidelines()
    output_path = os.path.join(OUTPUT_DIR, "who_guidelines.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Saved {len(records)} WHO guideline records to {output_path}")
    return records


if __name__ == "__main__":
    save_who_guidelines()
