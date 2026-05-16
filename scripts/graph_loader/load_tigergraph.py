"""
TigerGraph Data Loader

Loads extracted entities and relationships into TigerGraph Cloud
using the pyTigerGraph REST API.
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

GRAPH_LOAD_PATH = "data/processed/graph_load_ready.json"


def get_tg_connection():
    """Establish connection to TigerGraph Cloud."""
    import pyTigerGraph as tg

    conn = tg.TigerGraphConnection(
        host=os.getenv("TG_HOST"),
        graphname=os.getenv("TG_GRAPH_NAME", "MedicalGraph"),
        username=os.getenv("TG_USERNAME"),
        password=os.getenv("TG_PASSWORD"),
        gsqlVersion="4.1",
        gsPort="443",
        restppPort="443",
        sslPort="443",
    )

    # Authenticate
    secret = os.getenv("TG_SECRET")
    if secret and secret != "your_secret_here":
        try:
            conn.getToken(secret)
            print("  ✅ Authenticated with secret")
        except (RuntimeError, ValueError, TypeError) as e:
            print(f"  ⚠ Secret auth failed: {e}")
            print("  Attempting password-based auth...")
            try:
                secret = conn.createSecret()
                conn.getToken(secret)
                print("  ✅ Authenticated with new secret")
            except (RuntimeError, ValueError, TypeError) as e2:
                print(f"  ❌ Authentication failed: {e2}")
                return None
    else:
        try:
            secret = conn.createSecret()
            conn.getToken(secret)
            print("  ✅ Authenticated with new secret")
        except (RuntimeError, ValueError, TypeError) as e:
            print(f"  ❌ Authentication failed: {e}")
            return None

    return conn


def load_vertices(conn, vertices: dict):
    """Load all vertex types into TigerGraph."""

    for vtype, vdata in vertices.items():
        if not vdata:
            continue
        print(f"\n  Loading {len(vdata)} {vtype} vertices...")
        success = 0
        for vid, attrs in vdata.items():
            try:
                conn.upsertVertex(vtype, vid, attrs)
                success += 1
            except (RuntimeError, ValueError, TypeError) as e:
                if success == 0:
                    print(f"    ⚠ Error on first vertex: {e}")
        print(f"    ✅ Loaded {success}/{len(vdata)} {vtype} vertices")


def resolve_vertex_id(vertices: dict, vtype: str, name: str) -> str | None:
    """Resolve a vertex name to its ID."""
    # First check existing vertices
    for vid, vdata in vertices.get(vtype, {}).items():
        if vdata.get("name", "").lower() == name.lower():
            return vid
    return None


def load_edges(conn, edges: list[dict], vertices: dict):
    """Load all edge types into TigerGraph."""

    print(f"\n  Loading {len(edges)} edges...")
    success = 0
    skipped = 0

    for edge in edges:
        etype = edge.get("type")
        from_type = edge.get("from_type")
        to_type = edge.get("to_type")

        # Resolve IDs
        from_id = edge.get("from_id") or resolve_vertex_id(vertices, from_type, edge.get("from_name", "")) or edge.get("from_name")
        to_id = edge.get("to_id") or resolve_vertex_id(vertices, to_type, edge.get("to_name", "")) or edge.get("to_name")

        if not from_id or not to_id or not etype:
            skipped += 1
            continue

        # Build edge attributes (exclude meta fields)
        attrs = {k: v for k, v in edge.items()
                 if k not in ("type", "from_type", "to_type", "from_id", "to_id",
                              "from_name", "to_name")}

        try:
            conn.upsertEdge(from_type, from_id, etype, to_type, to_id, attrs)
            success += 1
        except (RuntimeError, ValueError, TypeError) as e:
            skipped += 1
            if success == 0 and skipped == 1:
                print(f"    ⚠ First edge error ({etype}): {e}")

    print(f"    ✅ Loaded {success} edges, skipped {skipped}")


def load_graph():
    """Full graph loading pipeline."""

    print("=" * 60)
    print("  GraphRAG — TigerGraph Data Loader")
    print("=" * 60)

    # Load extracted data
    if not os.path.exists(GRAPH_LOAD_PATH):
        print(f"⚠ Graph data not found at {GRAPH_LOAD_PATH}")
        print("  Run: python scripts/entity_extraction/extract_and_load.py first")
        return

    with open(GRAPH_LOAD_PATH, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    vertices = graph_data["vertices"]
    edges = graph_data["edges"]
    total_verts = sum(len(v) for v in vertices.values())

    print(f"  Data loaded: {total_verts} vertices, {len(edges)} edges")

    # Connect to TigerGraph
    print("\n  Connecting to TigerGraph Cloud...")
    conn = get_tg_connection()
    if conn is None:
        print("  ❌ Cannot connect to TigerGraph. Check .env credentials.")
        print("  Data has been saved to:", GRAPH_LOAD_PATH)
        print("  You can load it manually once authentication is fixed.")
        return

    # Check graph exists
    try:
        stats = conn.getStatistics()
        print(f"  ✅ Connected to graph: {conn.graphname}")
    except (RuntimeError, ValueError, TypeError):
        print("  ⚠ Graph may not be initialized. Attempting to continue...")

    # Load data
    load_vertices(conn, vertices)
    load_edges(conn, edges, vertices)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  LOADING COMPLETE")
    print(f"{'=' * 60}")
    try:
        stats = conn.getStatistics()
        print(f"  Graph statistics: {json.dumps(stats, indent=2)[:500]}")
    except (RuntimeError, ValueError, TypeError):
        print("  (Could not retrieve graph statistics)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    load_graph()
