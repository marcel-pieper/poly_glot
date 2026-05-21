# Polyglot API — production deploy

Automated deploy mirrors the PerFi app on the same droplet: GitHub Actions SSHs as `deploy`, updates `/opt/poly_glot`, and restarts the API on **port 8001** (PerFi uses **8000**).

## One-time server setup (you)

1. **Clone** (as `deploy`):
   ```bash
   sudo mkdir -p /opt/poly_glot
   sudo chown deploy:deploy /opt/poly_glot
   git clone <your-poly_glot-repo-url> /opt/poly_glot
   ```

2. **`backend/.env`** on the server (not in git). Example:
   ```env
   APP_ENV=production
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/polyglot
   JWT_SECRET=<strong-secret>
   OPENAI_API_KEY=<key>
   ```

3. **Postgres**: `docker compose up -d` from `/opt/poly_glot` (host port **5433** — does not clash with PerFi’s **5432**).

4. **nginx** + TLS for `poly.thedevmind.com` → proxy `/api/`, `/health`, `/docs` to `127.0.0.1:8001` (use `server_mcp` or manual config; see `agent_helpers/server_mcp/README.md`).

5. **Smoke test** before enabling Actions:
   ```bash
   cd /opt/poly_glot/backend
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   ENV=production APP_ENV=production python run.py
   curl -s http://127.0.0.1:8001/health
   ```

## GitHub

- Repository secret: **`DEPLOY_SSH_KEY`** (private key for `deploy@137.184.41.83`, same pattern as PerFi).
- Workflow: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) runs on push to `main` when `backend/`, `docker-compose.yml`, or the workflow changes.

## After deploy

- Public API base URL: `https://poly.thedevmind.com/api`
- Android `local.properties`: `API_BASE_URL_RELEASE=https://poly.thedevmind.com/api`
- Logs: `/opt/poly_glot/logs/backend-*.log`
- PID file: `backend/.polyglot-backend.pid`
