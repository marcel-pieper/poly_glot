# Server MCP (SSH)

MCP server for remote servers over SSH: read files/directories, manage nginx site configs, and run certbot. Uses its own `.venv` in this folder (not `backend/venv` or `database_mcp/.venv`).

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

Copy [`.cursor/mcp.json.example`](../../.cursor/mcp.json.example) to `.cursor/mcp.json` and adjust paths. The MCP server key should be **`server_mcp`**:

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

Restart the MCP server in Cursor after code changes.

## Tools

### Read

| Tool | Description |
|------|-------------|
| `list_servers` | Show configured server aliases |
| `list_directory` | List a remote directory |
| `read_file` | Read a file (`offset`, `limit`, `preview` for large files) |

### Nginx

| Tool | Description |
|------|-------------|
| `nginx_list_sites` | List `sites-available` and `sites-enabled` |
| `nginx_test_config` | Run `nginx -t` |
| `nginx_write_site` | Write full config to `sites-available/{site_name}` (optional backup) |
| `nginx_enable_site` | Symlink site into `sites-enabled` |
| `nginx_disable_site` | Remove symlink from `sites-enabled` |
| `nginx_apply` | `nginx -t` then `systemctl reload nginx` (**`confirm=true` required**) |
| `nginx_status` | `systemctl status nginx` |

Site names must match `^[a-z][a-z0-9_-]*$`. Only `/etc/nginx/sites-available/{name}` is writable via `nginx_write_site`.

### Certbot

| Tool | Description |
|------|-------------|
| `certbot_list` | `certbot certificates` |
| `certbot_issue` | `certbot certonly --nginx -d <domain>` (`dry_run=true` or `confirm=true`) |
| `certbot_renew` | `certbot renew` (default `dry_run=true`; live renew needs `confirm=true`) |

### Typical workflow (new subdomain)

1. `nginx_write_site` — full site file (HTTP first, or full SSL if cert exists)
2. `nginx_enable_site`
3. `nginx_test_config`
4. `certbot_issue` with `dry_run=true`, then `confirm=true`
5. Update site file SSL paths if you maintain them manually (like PerFi)
6. `nginx_test_config` → `nginx_apply` with `confirm=true`

There is no generic shell tool; commands are allowlisted in code.
