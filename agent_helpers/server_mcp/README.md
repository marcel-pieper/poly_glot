# Server MCP (read-only SSH)

Read-only MCP server for exploring remote servers over SSH: list directories and read files (with preview/section support for large files). Uses its own `.venv` in this folder (not `backend/venv` or `database_mcp/.venv`).

## Setup

```powershell
cd agent_helpers/server_mcp
C:\Users\marce\tech\python3.13.4\python.exe -m venv .venv
.\.venv\Scripts\pip install -e .
copy config.example.yaml config.yaml
```

Edit `config.yaml` with SSH host, user, and key path for each server alias.

## Config

`config.yaml` defines named servers under `servers:`. Each server needs at least `host`, `user`, and usually `key_file`. Override the config path with `POLYGLOT_SERVER_MCP_CONFIG` if needed.

See `config.example.yaml` for the full shape.

## Cursor

Copy [`.cursor/mcp.json.example`](../../.cursor/mcp.json.example) to `.cursor/mcp.json` and adjust paths. The MCP server key should be **`server_mcp`** (same as this subproject folder):

```json
{
  "mcpServers": {
    "server_mcp": {
      "command": "C:/path/to/poly_glot/agent_helpers/server_mcp/.venv/Scripts/python.exe",
      "args": ["-m", "server_mcp.server"],
      "cwd": "C:/path/to/poly_glot/agent_helpers/server_mcp"
    }
  }
}
```

Each MCP subprocess must use **this folder's `.venv` Python**, not `backend/venv`.

## Tools

| Tool | Description |
|------|-------------|
| `list_servers` | Show configured server aliases |
| `list_directory` | List a remote directory (`server`, `path`, optional `show_hidden`) |
| `read_file` | Read a remote file (`server`, `path`, optional `offset`, `limit`, `preview`) |

Write/deploy tools will be added later.
