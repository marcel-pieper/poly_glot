# Database MCP (read-only Postgres)

Read-only MCP server for exploring Postgres and running `SELECT` queries. Uses its own `.venv` in this folder (not `backend/venv`).

## Setup

```powershell
cd agent_helpers/database_mcp
C:\Users\marce\tech\python3.13.4\python.exe -m venv .venv
.\.venv\Scripts\pip install -e .
copy config.example.json config.json
```

Edit `config.json` (gitignored). For local dev, start Postgres from the repo root: `docker compose up -d`.

## Config

Each database needs a `connection_string`. For a **remote** Postgres reachable only on the server (e.g. prod Docker on port 5433), add an `ssh` block. The MCP starts an **SSH tunnel automatically** when you first query that alias—no manual `ssh -N` required.

```json
"polyglot_prod": {
  "description": "Polyglot prod",
  "connection_string": "postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5433/polyglot",
  "ssh": {
    "host": "137.184.41.83",
    "user": "deploy",
    "port": 22,
    "key_file": "C:/Users/you/.ssh/id_ed25519",
    "remote_host": "127.0.0.1",
    "remote_port": 5433
  }
}
```

| `ssh` field | Meaning |
|-------------|---------|
| `host`, `user`, `port` | SSH server (same idea as `server_mcp` config) |
| `key_file` | Private key path; omit to use SSH agent |
| `key_passphrase` | Optional, for encrypted keys |
| `remote_host`, `remote_port` | Where Postgres listens **on the server** (Polyglot: `127.0.0.1:5433`) |
| `local_port` | Local bind port; `0` = pick a free port (default) |

The tunnel rewrites `connection_string` to `127.0.0.1:<local_port>` while keeping user, password, and database name from the URL.

Override the config path with `POLYGLOT_DB_MCP_CONFIG` if needed.

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

Restart the MCP server in Cursor after changing `config.json` or installing dependencies.

## Tools

`list_databases`, `list_schemas`, `list_tables`, `describe_table`, `run_query` (read-only SQL only).

Pass `database: "polyglot_prod"` (or your alias) to target prod; omit to use `default_database`.
