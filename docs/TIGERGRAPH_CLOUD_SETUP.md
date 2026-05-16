# Connecting to TigerGraph Savanna (Manual Guide)

This guide walks through connecting the GraphRAG benchmark to a **TigerGraph Savanna** workspace on [tgcloud.io](https://tgcloud.io). Pipeline 3 talks to your cloud database through the local `tigergraph/graphrag` Docker service.

## Overview

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│  .env           │ --> │ configs/             │ --> │ tigergraph/graphrag     │
│  (credentials)  │     │ server_config.json   │     │ (localhost:8000)        │
└─────────────────┘     └──────────────────────┘     └───────────┬─────────────┘
                                                                   │ GSQL token + REST++
                                                                   v
                                                       ┌─────────────────────────┐
                                                       │ TigerGraph Savanna      │
                                                       │ (your workspace URL)    │
                                                       └─────────────────────────┘
```

**Prerequisites:** Docker Desktop, Python 3.11+, a [Gemini API key](https://aistudio.google.com), and a Savanna workspace.

---

## Part 1 — Savanna (tgcloud.io)

### 1. Create a workspace

1. Log in at [tgcloud.io](https://tgcloud.io).
2. Open your **Workgroup** → **Workspace** tab.
3. Click **Create Workspace** (Free Tier is fine).
4. Pick a region and wait until status is **Ready**.

### 2. Create a database user

1. On the workspace card, open **⋯** → **Manage Access**.
2. Go to **Database Access** → **Add User** (`+`).
3. Set a **username** and **password**; copy the password immediately.
4. Assign a role that can create schema and run GSQL (required for GraphRAG ingest):
   - **globaldesigner** or **superuser** (recommended), or
   - A custom role with at least **READ_SCHEMA** and **WRITE_SCHEMA** on global, plus graph-level write access.

> Without schema-write privileges, the GraphRAG container may start but GDS install or ingest will fail with permission errors.

### 3. Copy the host URL

1. Click **Connect** on the workspace card.
2. Copy the **Host URL**, for example:
   ```
   https://tg-<workspace-id>.tg-<account-id>.i.tgcloud.io
   ```
3. Keep this for `TG_HOST` in `.env`. Savanna serves REST++ on port **443** (included in the URL or implied).

### 4. (Optional) REST++ secret / API token

Savanna supports [REST++ token authentication](https://docs.tigergraph.com/tigergraph-server/current/API/authentication). This project uses **database username + password** with `getToken: true` (see below), which is the usual path for GraphRAG. You do not need a separate REST secret unless you prefer static tokens.

---

## Part 2 — Local configuration

### 1. Create `.env`

From the project root:

```powershell
cp .env.example .env
```

Edit `.env`:

```env
# Google Gemini (required for GraphRAG LLM + embeddings)
GEMINI_API_KEY=your_gemini_key

# TigerGraph Savanna
TG_HOST=https://your-workspace-url.i.tgcloud.io
TG_USERNAME=your_db_username
TG_PASSWORD=your_db_password
TG_GRAPH_NAME=GraphRAG
TG_GET_TOKEN=true

# Optional overrides (defaults shown)
# TG_RESTPP_PORT=443
# TG_GSQL_PORT=14240
# GRAPHRAG_LLM_MODEL=gemma-4-26b-a4b-it
# GRAPHRAG_EMBEDDING_MODEL=models/text-embedding-004

GRAPHRAG_SERVICE_URL=http://localhost:8000
```

| Variable | Description |
|----------|-------------|
| `TG_HOST` | Workspace host URL from **Connect** (no trailing slash). |
| `TG_USERNAME` / `TG_PASSWORD` | Database user from **Manage Access → Database Access**. |
| `TG_GRAPH_NAME` | Graph name GraphRAG will use (created on first ingest if missing). |
| `TG_GET_TOKEN` | **Must be `true` for Savanna.** GraphRAG obtains a GSQL token at startup; REST calls fail with `REST-10016` if this is false. |
| `GEMINI_API_KEY` | Used by the GraphRAG container for completion and embeddings. |

`.env` is git-ignored; never commit credentials.

### 2. Generate `server_config.json`

The `tigergraph/graphrag` image expects a JSON file at `configs/server_config.json`. Generate it from `.env`:

```powershell
python scripts/generate_server_config.py
```

This writes `configs/server_config.json` (also git-ignored). Re-run this script whenever you change TigerGraph or Gemini settings in `.env`.

**What it configures:**

- **db_config:** hostname, user, password, graph name, port `443`, `getToken: true`
- **llm_config:** Google GenAI (`genai`) for `gemini-2.5-flash` and Gemini embedding model

### 3. Verify Savanna connectivity (before Docker)

```powershell
pip install -r requirements.txt   # if not already installed
python scripts/test_tigergraph_connection.py
```

Expected output:

```
REST++ echo OK: {"error":false, "message":"Hello GSQL"}
GSQL token OK, TigerGraph version: 4.2.x
```

If this fails, fix credentials or roles in Savanna before starting Docker.

---

## Part 3 — Start GraphRAG (Docker)

### 1. Launch the service

From the project root:

```powershell
docker compose up -d graphrag
```

`docker-compose.yml` mounts `./configs` into the container and sets `SERVER_CONFIG=/code/configs/server_config.json`.

### 2. Check health

```powershell
curl http://localhost:8000/health
```

Healthy response:

```json
{"status":"healthy","details":{"embedding_store":{"status":"ok","error":null}}}
```

### 3. Inspect logs (optional)

```powershell
docker compose logs graphrag --tail 50
```

Look for:

- `Uvicorn running on http://0.0.0.0:8000`
- `TigerGraph embedding store is initialized with graph GraphRAG`
- GDS install completing without `does not have the permission`

If you changed Savanna roles, restart GraphRAG so it re-runs startup checks:

```powershell
docker compose restart graphrag
```

### 4. Start the full stack (dashboard)

```powershell
docker compose up -d --build
```

- Dashboard: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8080](http://localhost:8080)
- GraphRAG API: [http://localhost:8000](http://localhost:8000)

---

## Part 4 — Ingest and query

### Ingest (build the graph in Savanna)

**Dashboard:** open [http://localhost:3000](http://localhost:3000) → **Ingest GraphRAG**.

**CLI:**

```powershell
python pipelines/pipeline3_graphrag/ingest.py
```

Ingest pushes documents to the GraphRAG service, which extracts entities and loads them into your `TG_GRAPH_NAME` graph on Savanna.

### Query

Use the dashboard **Pipeline 3** tab or:

```powershell
python pipelines/pipeline3_graphrag/query.py --question "Your question here"
```

---

## Checklist

| Step | Done when |
|------|-----------|
| Savanna workspace **Ready** | Host URL copied |
| DB user created with schema-write role | `test_tigergraph_connection.py` passes |
| `.env` filled | `generate_server_config.py` succeeds |
| `docker compose up -d graphrag` | `/health` returns `"healthy"` |
| Ingest | Dashboard or CLI ingest completes without errors |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|----------------|-----|
| `REST-10016` / empty token | `TG_GET_TOKEN=false` or missing token step | Set `TG_GET_TOKEN=true`, regenerate config, restart `graphrag` |
| `llm_model is not found in completion_service` | Outdated `server_config.json` format | Run `python scripts/generate_server_config.py` and restart container |
| `WRITE_SCHEMA` / permission denied on GDS or `ls` | DB user role too limited | In Savanna **Manage Access**, grant **globaldesigner** or **superuser**, then `docker compose restart graphrag` |
| GraphRAG container restart loop | Bad config or auth | `docker compose logs graphrag`; fix `.env`, regenerate config |
| `test_tigergraph_connection` REST OK but token fails | Wrong password or user | Reset password in Savanna Database Access |
| Dashboard “GraphRAG connection error” | Service down or wrong URL | Ensure `GRAPHRAG_SERVICE_URL=http://localhost:8000` and `curl http://localhost:8000/health` works |
| Port 8000 in use | Another process on 8000 | Stop conflicting service or change compose port mapping |

### After any `.env` change

```powershell
python scripts/generate_server_config.py
python scripts/test_tigergraph_connection.py
docker compose restart graphrag
```

---

## TigerGraph MCP (Cursor)

Install and wire the official MCP server so agents can inspect schema, run GSQL, and manage loading jobs:

```powershell
pip install tigergraph-mcp
```

Project config: `.cursor/mcp.json` (loads credentials from `.env`). Restart Cursor after editing.

CLI helper (same tools without Cursor MCP UI):

```powershell
python scripts/mcp_tigergraph.py show_graph_details graph_name=GraphRAG
python scripts/test_tigergraph_connection.py
```

Savanna note: MCP GSQL calls may return 401 until `TG_API_TOKEN` is set; `scripts/mcp_tigergraph.py` obtains a token from `getToken()` automatically.

## GraphRAG ingest (Savanna + local Docker)

The REST path `POST /graphrag/ingest` expects `DocumentContent` on the **cloud** filesystem. Local JSONL under `./data` is not visible to Savanna, so CLI ingest uses **inline load**:

```powershell
python pipelines/pipeline3_graphrag/ingest.py --path ./data/medical
```

This runs `runLoadingJobWithData` via pyTigerGraph, then triggers `forceConsistencyUpdate` to build chunks and entities.

**Savanna + Docker note:** The GraphRAG container must reach your workspace GSQL port (`TG_GSQL_PORT`, default `14240`). If rebuild fails with `Connection refused` on port 14240, complete **Rebuild graph** in the [Savanna / GraphRAG Admin UI](http://localhost:8000/ui) after ingest. Raw documents (`Document` / `Content`) can load while `DocumentChunk` stays empty until rebuild succeeds.

## Reference

- [TigerGraph Savanna docs](https://docs.tigergraph.com/savanna/main/)
- [GraphRAG Docker image](https://github.com/tigergraph/graphrag)
- [TigerGraph MCP](https://github.com/tigergraph/tigergraph-mcp)
- Project scripts: `scripts/generate_server_config.py`, `scripts/test_tigergraph_connection.py`, `scripts/mcp_tigergraph.py`
- Main setup: [SETUP.md](SETUP.md)
