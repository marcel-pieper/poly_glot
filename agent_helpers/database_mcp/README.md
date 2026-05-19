# Database MCP (read-only Postgres)

Read-only MCP server for exploring Postgres and running `SELECT` queries. Uses its own `.venv` in this folder (not `backend/venv`).

## Setup

```bash
cd agent_helpers/database_mcp
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -e .
cp config.example.json config.json
```

Postgres should be running (`docker compose up -d` from the repo root).

## Config

Edit `config.json` to add databases. See `config.example.json` for the shape. Override the file path with `POLYGLOT_DB_MCP_CONFIG` if needed.

## Cursor

Point MCP at this venv’s Python — see [`.cursor/mcp.json.example`](../../.cursor/mcp.json.example).

## Tools

`list_databases`, `list_schemas`, `list_tables`, `describe_table`, `run_query` (read-only SQL only).
