"""
Data Collection Orchestrator

Runs all data collection scripts and merges outputs into a unified
corpus for entity extraction and graph loading.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def collect_all():
    """Run all data collection scripts and merge into unified corpus."""

    print("=" * 60)
    print("  GraphRAG — Data Collection Pipeline")
    print("=" * 60)

    all_documents = []

    # ── Step 1: DrugBank (seed or CSV) ──
    print("\n[1/5] Collecting DrugBank data...")
    from src.scripts.data_collection.drugbank_parser import save_drugbank_data
    drugs = save_drugbank_data()
    all_documents.extend(drugs)

    # ── Step 2: Disease-Symptom Dataset ──
    print("\n[2/5] Generating disease-symptom dataset...")
    from src.scripts.data_collection.disease_symptom_loader import save_disease_data
    diseases = save_disease_data()
    all_documents.extend(diseases)

    # ── Step 3: WHO Essential Medicines / Guidelines ──
    print("\n[3/5] Collecting WHO guideline data...")
    from src.scripts.data_collection.who_guidelines_loader import save_who_guidelines
    guidelines = save_who_guidelines()
    all_documents.extend(guidelines)

    # ── Step 4: PubMed (optional — requires network) ──
    print("\n[4/5] PubMed collection...")
    pubmed_path = "data/raw/pubmed/pubmed_abstracts.json"
    if os.path.exists(pubmed_path):
        with open(pubmed_path, "r", encoding="utf-8") as f:
            pubmed = json.load(f)
        all_documents.extend(pubmed)
        print(f"  [OK] Loaded {len(pubmed)} PubMed abstracts from cache")
    else:
        print("  [WARN] PubMed data not found. Run pubmed_scraper.py separately.")
        print("    python src/scripts/data_collection/pubmed_scraper.py")

    # ── Step 5: FDA FAERS (optional — requires network) ──
    print("\n[5/5] FDA FAERS collection...")
    fda_path = "data/raw/fda/fda_events.json"
    if os.path.exists(fda_path):
        with open(fda_path, "r", encoding="utf-8") as f:
            fda = json.load(f)
        all_documents.extend(fda)
        print(f"  [OK] Loaded {len(fda)} FDA event reports from cache")
    else:
        print("  [WARN] FDA data not found. Run fda_scraper.py separately.")
        print("    python src/scripts/data_collection/fda_scraper.py")

    # ── Merge into unified corpus ──
    os.makedirs("data/processed", exist_ok=True)
    corpus_path = "data/processed/unified_corpus.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(all_documents, f, indent=2)

    # ── Also produce a plain text version for RAG ingestion ──
    text_path = "data/processed/corpus_text.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        for doc in all_documents:
            f.write(doc.get("text", "") + "\n\n")

    # ── Token estimate ──
    total_chars = sum(len(doc.get("text", "")) for doc in all_documents)
    estimated_tokens = int(total_chars / 4)  # rough estimate

    print(f"\n{'=' * 60}")
    print("  COLLECTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Total documents : {len(all_documents)}")
    print(f"  Estimated tokens: {estimated_tokens:,}")
    print(f"  Unified corpus  : {corpus_path}")
    print(f"  Text corpus     : {text_path}")
    print(f"{'=' * 60}")

    return all_documents


if __name__ == "__main__":
    collect_all()
