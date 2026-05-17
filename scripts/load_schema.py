#!/usr/bin/env python3
"""Load the medical schema into TigerGraph."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from pyTigerGraph import TigerGraphConnection

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def load_schema(schema_file: str):
    """Load GSQL schema file into TigerGraph."""
    print(f"[*] Loading schema from: {schema_file}")
    schema_path = Path(schema_file).resolve()
    if not schema_path.exists():
        print(f"[ERROR] Schema file not found: {schema_path}")
        return False

    gsql_content = schema_path.read_text(encoding="utf-8")
    print(f"[*] Read {len(gsql_content)} bytes of GSQL")

    # Connect to TigerGraph
    host = os.getenv("TG_HOST", "").strip().rstrip("/")
    user = os.getenv("TG_USERNAME", "").strip()
    password = os.getenv("TG_PASSWORD", "").strip()
    restpp = os.getenv("TG_RESTPP_PORT", "443").strip()
    gs = os.getenv("TG_GSQL_PORT", "14240").strip()

    if not all([host, user, password]):
        print("[ERROR] TG_HOST, TG_USERNAME, TG_PASSWORD required in .env")
        return False

    print(f"[*] Connecting to TigerGraph at {host}...")
    try:
        conn = TigerGraphConnection(
            host=host,
            username=user,
            password=password,
            restppPort=restpp,
            gsPort=gs,
        )
        if conn.restppPort == conn.gsPort and "/restpp" not in conn.restppUrl:
            conn.restppUrl = conn.restppUrl + "/restpp"
        token = conn.getToken()[0]
        conn = TigerGraphConnection(
            host=host,
            username=user,
            password=password,
            restppPort=restpp,
            gsPort=gs,
            apiToken=token,
        )
        if conn.restppUrl == conn.restppUrl and "/restpp" not in conn.restppUrl:
            conn.restppUrl = conn.restppUrl + "/restpp"
        print("[✓] Connected")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

    # Execute GSQL
    print("[*] Executing GSQL schema...")
    try:
        result = conn.gsql(gsql_content)
        print(f"[✓] Schema loaded successfully")
        print(f"\nResult:\n{result}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to load schema: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load medical schema into TigerGraph")
    parser.add_argument(
        "--schema",
        type=str,
        default="src/scripts/schema/medical_graph.gsql",
        help="Path to GSQL schema file",
    )
    args = parser.parse_args()

    success = load_schema(args.schema)
    sys.exit(0 if success else 1)
