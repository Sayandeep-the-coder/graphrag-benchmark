"""
Pipeline 3 — GraphRAG Ingest

Loads documents into TigerGraph Savanna via pyTigerGraph. The default path uses
CSV shards, then rebuilds the GraphRAG knowledge graph through the local
GraphRAG service.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from src.utils.tigergraph_ingest import ingest_to_savanna

load_dotenv()


def ingest_documents(docs_folder: str = "./data/processed", rebuild: bool = True, format: str = "csv"):
    """Ingest documents and rebuild the GraphRAG graph."""
    print(f"Ingesting from {docs_folder} into TigerGraph Savanna via {format.upper()}...")
    result = ingest_to_savanna(docs_folder, rebuild=rebuild, format=format)
    print(f"  Format        : {result['format']}")
    print(f"  Load files    : {len(result['load_files'])}")
    print(f"  Documents     : {result['document_count']}")
    print(f"  Content nodes : {result['content_count']}")
    print(f"  Doc chunks    : {result.get('document_chunk_count', '?')}")
    print(f"  Entities      : {result.get('entity_count', '?')}")
    if result.get("rebuild_error"):
        print(f"  [WARN] Rebuild: {result['rebuild_error']}")
    if result.get("rebuild_warning"):
        print(f"  [WARN] Rebuild: {result['rebuild_warning']}")
    print("\n[SUCCESS] Savanna load complete.")
    if result.get("document_chunk_count", 0) == 0:
        print(
            "  Chunks not built yet - open http://localhost:8000/ui GraphRAG admin "
            "and Rebuild graph, or re-run ingest without --no-rebuild."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into TigerGraph GraphRAG.")
    parser.add_argument("--path", type=str, default="./data/processed")
    parser.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    parser.add_argument("--no-rebuild", action="store_true", help="Skip knowledge-graph rebuild")
    args = parser.parse_args()
    ingest_documents(args.path, rebuild=not args.no_rebuild, format=args.format)
