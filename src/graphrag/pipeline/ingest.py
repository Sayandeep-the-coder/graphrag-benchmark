"""
Pipeline 3 — GraphRAG Ingest

Loads .txt documents into TigerGraph Savanna via pyTigerGraph (inline JSONL load),
then rebuilds the GraphRAG knowledge graph through the local GraphRAG service.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from src.utils.tigergraph_ingest import ingest_to_savanna

load_dotenv()


def ingest_documents(docs_folder: str = "./data/medical", rebuild: bool = True):
    """Ingest documents and rebuild the GraphRAG graph."""
    print(f"Ingesting from {docs_folder} into TigerGraph Savanna...")
    result = ingest_to_savanna(docs_folder, rebuild=rebuild)
    print(f"  JSONL         : {result['jsonl_path']}")
    print(f"  Documents     : {result['document_count']}")
    print(f"  Content nodes : {result['content_count']}")
    print(f"  Doc chunks    : {result.get('document_chunk_count', '?')}")
    print(f"  Entities      : {result.get('entity_count', '?')}")
    if result.get("rebuild_error"):
        print(f"  [WARN] Rebuild: {result['rebuild_error']}")
    print("\n[SUCCESS] Savanna load complete.")
    if result.get("document_chunk_count", 0) == 0:
        print(
            "  Chunks not built yet - open http://localhost:8000/ui GraphRAG admin "
            "and Rebuild graph, or re-run ingest without --no-rebuild."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into TigerGraph GraphRAG.")
    parser.add_argument("--path", type=str, default="./data/medical")
    parser.add_argument("--no-rebuild", action="store_true", help="Skip knowledge-graph rebuild")
    args = parser.parse_args()
    ingest_documents(args.path, rebuild=not args.no_rebuild)
