"""Generate configs/server_config.json for the TigerGraph GraphRAG Docker image."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "server_config.json"


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def build_config() -> dict:
    host = _require("TG_HOST").rstrip("/")
    return {
        "db_config": {
            "hostname": host,
            "username": _require("TG_USERNAME"),
            "password": _require("TG_PASSWORD"),
            "graphname": os.getenv("TG_GRAPH_NAME", "GraphRAG").strip() or "GraphRAG",
            "restppPort": os.getenv("TG_RESTPP_PORT", "443"),
            "gsPort": os.getenv("TG_GSQL_PORT", "14240"),
            "getToken": os.getenv("TG_GET_TOKEN", "true").lower() in ("1", "true", "yes"),
            "default_timeout": 300,
            "default_mem_threshold": 5000,
            "default_thread_limit": 8,
        },
        "llm_config": {
            "token_limit": 0,
            "authentication_configuration": {
                "GOOGLE_API_KEY": _require("GEMINI_API_KEY"),
            },
            "completion_service": {
                "llm_service": "genai",
                "llm_model": os.getenv("GRAPHRAG_LLM_MODEL", "gemma-4-26b-a4b-it"),
                "model_kwargs": {"temperature": 0},
                "prompt_path": "./common/prompts/google_gemini/",
            },
            "embedding_service": {
                "embedding_model_service": "genai",
                "model_name": os.getenv(
                    "GRAPHRAG_EMBEDDING_MODEL", "models/text-embedding-004"
                ),
                "dimensions": int(os.getenv("GRAPHRAG_EMBEDDING_DIM", "768")),
            },
        },
    }


def main() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(build_config(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {CONFIG_PATH}")


if __name__ == "__main__":
    main()
