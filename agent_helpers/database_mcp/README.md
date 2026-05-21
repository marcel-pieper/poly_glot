# Database MCP (read-only Postgres)

Read-only MCP server for exploring Postgres and running `SELECT` queries. Uses its own `.venv` in this folder (not `backend/venv`).

## Setup

```powershell
cd agent_helpers/database_mcp
C:\Users\marce\tech\python3.13.4\python.exe -m venv .venv
.\.venv\Scripts\pip install -e .
copy config.example.json config.json
```

Postgres should be running (`docker compose up -d` from the repo root).

## Config

Edit `config.json` to add databases. See `config.example.json` for the shape. Override the file path with `POLYGLOT_DB_MCP_CONFIG` if needed.

## Cursor

Copy [`.cursor/mcp.json.example`](../../.cursor/mcp.json.example) to `.cursor/mcp.json` and adjust paths. The MCP server key should be **`database_mcp`** (same as this subproject folder):

```json
{
  "mcpServers": {
    "database_mcp": {
      "command": "C:/path/to/poly_glot/agent_helpers/database_mcp/.venv/Scripts/python.exe",
      "args": ["-m", "database_mcp.server"],
      "cwd": "C:/path/to/poly_glot/agent_helpers/database_mcp"
    }
  }
}
```

Each MCP subprocess must use **this folder's `.venv` Python**, not `backend/venv`.

## Tools

`list_databases`, `list_schemas`, `list_tables`, `describe_table`, `run_query` (read-only SQL only).
