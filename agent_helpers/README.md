# Agent helpers

Small subprojects that extend Cursor agents (MCP servers, etc.).

MCP server keys in `.cursor/mcp.json` match subproject folder names: **`database_mcp`**, **`server_mcp`**.

| Subproject | MCP key | Purpose |
|------------|---------|---------|
| [database_mcp](database_mcp/) | `database_mcp` | Read-only Postgres MCP; optional SSH tunnel to remote DB (own `.venv`) |
| [server_mcp](server_mcp/) | `server_mcp` | SSH server MCP: read files, nginx, certbot (own `.venv`) |
