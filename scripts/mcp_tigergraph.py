"""Run TigerGraph MCP tools from CLI (uses project .env)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _env_dict() -> dict[str, str]:
    try:
        from dotenv import dotenv_values

        raw = dotenv_values(ROOT / ".env")
    except ImportError:
        raw = {}
    host = (raw.get("TG_HOST") or os.getenv("TG_HOST", "")).strip().rstrip("/")
    graph = (raw.get("TG_GRAPH_NAME") or os.getenv("TG_GRAPH_NAME", "GraphRAG")).strip()
    user = (raw.get("TG_USERNAME") or os.getenv("TG_USERNAME", "")).strip()
    password = (raw.get("TG_PASSWORD") or os.getenv("TG_PASSWORD", "")).strip()
    restpp = (raw.get("TG_RESTPP_PORT") or os.getenv("TG_RESTPP_PORT", "443")).strip()
    gs = (raw.get("TG_GSQL_PORT") or os.getenv("TG_GSQL_PORT", "14240")).strip()
    env = {
        "TG_HOST": host,
        "TG_USERNAME": user,
        "TG_PASSWORD": password,
        "TG_RESTPP_PORT": restpp,
        "TG_GS_PORT": gs,
        "TG_TGCLOUD": "true",
    }
    if graph:
        env["TG_GRAPHNAME"] = graph
    try:
        from pyTigerGraph import TigerGraphConnection

        conn = TigerGraphConnection(
            host=host,
            username=user,
            password=password,
            graphname=graph,
            restppPort=str(restpp),
            gsPort=str(gs),
        )
        token = conn.getToken()[0]
        if token:
            env["TG_API_TOKEN"] = token
    except Exception:
        pass
    return env


async def call_tool(name: str, arguments: dict | None = None) -> str:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    exe = Path(
        os.environ.get(
            "TIGERGRAPH_MCP_EXE",
            r"C:\Users\user\AppData\Roaming\Python\Python313\Scripts\tigergraph-mcp.exe",
        )
    )
    if not exe.exists():
        raise FileNotFoundError(f"tigergraph-mcp not found at {exe}")

    params = StdioServerParameters(command=str(exe), args=["-v"], env=_env_dict())
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments=arguments or {})
            parts = []
            for block in result.content:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
            return "\n".join(parts)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/mcp_tigergraph.py <tool_name> [key=value ...]", file=sys.stderr)
        return 1
    tool = sys.argv[1]
    args: dict = {}
    for arg in sys.argv[2:]:
        if arg.startswith("{"):
            args = json.loads(arg)
            break
        if "=" in arg:
            key, val = arg.split("=", 1)
            args[key] = val
    if tool == "show_graph" and not args:
        args = {"graph_name": _env_dict().get("TG_GRAPHNAME", "GraphRAG")}
    out = asyncio.run(call_tool(tool if tool.startswith("tigergraph__") else f"tigergraph__{tool}", args))
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
