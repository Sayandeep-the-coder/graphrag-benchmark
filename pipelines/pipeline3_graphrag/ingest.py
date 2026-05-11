"""
Pipeline 3 — GraphRAG Ingest

Pushes Wikipedia .txt files to the TigerGraph GraphRAG service
in batches of 10 via REST API. The service auto-extracts entities
and relationships to build the knowledge graph.
"""

import glob
import os

import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

GRAPHRAG_URL = os.getenv("GRAPHRAG_SERVICE_URL", "http://localhost:8000")
BATCH_SIZE = 10


def ingest_documents(docs_folder: str = "./data/wikipedia"):
    """
    Ingest all .txt files into TigerGraph GraphRAG service.

    Sends documents in batches of 10 via POST /documents/batch.
    The service handles entity extraction and relationship mapping automatically.
    """
    filepaths = glob.glob(f"{docs_folder}/**/*.txt", recursive=True)
    print(f"Ingesting {len(filepaths)} documents into TigerGraph GraphRAG from {docs_folder}...")

    succeeded = 0
    failed = 0

    for i in tqdm(range(0, len(filepaths), BATCH_SIZE), desc="Batching documents"):
        batch = filepaths[i : i + BATCH_SIZE]
        batch_docs = []

        for filepath in batch:
            with open(filepath, encoding="utf-8") as f:
                text = f.read()
            batch_docs.append({
                "content": text,
                "filename": os.path.basename(filepath),
                "source": "medical_csv" if "medical" in docs_folder else "wikipedia",
            })

        try:
            resp = requests.post(
                f"{GRAPHRAG_URL}/documents/batch",
                json={"documents": batch_docs},
                timeout=120,
            )

            if resp.status_code == 200:
                succeeded += len(batch)
            else:
                print(f"\n[FAILED] Batch {i // BATCH_SIZE} failed (HTTP {resp.status_code}): {resp.text[:200]}")
                failed += len(batch)
        except requests.exceptions.RequestException as e:
            print(f"\n[ERROR] Batch {i // BATCH_SIZE} error: {e}")
            failed += len(batch)

    print(f"\n[SUCCESS] TigerGraph GraphRAG ingest complete.")
    print(f"   Total files attempted: {len(filepaths)}")
    print(f"   Succeeded            : {succeeded}")
    print(f"   Failed               : {failed}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest documents into TigerGraph GraphRAG.")
    parser.add_argument("--path", type=str, default="./data/wikipedia", help="Path to folder to ingest.")
    
    args = parser.parse_args()
    ingest_documents(args.path)
