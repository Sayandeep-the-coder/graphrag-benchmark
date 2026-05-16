"""Verify TigerGraph Savanna credentials from .env."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    host = os.getenv("TG_HOST", "").strip().rstrip("/")
    username = os.getenv("TG_USERNAME", "").strip()
    password = os.getenv("TG_PASSWORD", "").strip()
    graph = os.getenv("TG_GRAPH_NAME", "GraphRAG").strip() or "GraphRAG"
    port = os.getenv("TG_RESTPP_PORT", "443")

    missing = [n for n, v in [("TG_HOST", host), ("TG_USERNAME", username), ("TG_PASSWORD", password)] if not v]
    if missing:
        print(f"Missing: {', '.join(missing)}", file=sys.stderr)
        return 1

    parsed = urlparse(host if "://" in host else f"https://{host}")
    base = f"{parsed.scheme}://{parsed.hostname}:{port}"

    session = requests.Session()
    session.auth = (username, password)
    session.verify = True

    echo = session.get(f"{base}/restpp/echo", timeout=30)
    echo.raise_for_status()
    print(f"REST++ echo OK: {echo.text.strip()}")

    try:
        from pyTigerGraph import TigerGraphConnection

        conn = TigerGraphConnection(
            host=host,
            username=username,
            password=password,
            graphname=graph,
            restppPort=str(port),
            gsPort=os.getenv("TG_GSQL_PORT", "14240"),
        )
        token = conn.getToken()[0]
        conn = TigerGraphConnection(
            host=host,
            username=username,
            password=password,
            graphname=graph,
            restppPort=str(port),
            gsPort=os.getenv("TG_GSQL_PORT", "14240"),
            apiToken=token,
        )
        print(f"GSQL token OK, TigerGraph version: {conn.getVer()}")
    except Exception as exc:
        print(f"GSQL token check failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
