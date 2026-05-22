# Polyglot API — production deploy

Automated deploy mirrors the PerFi app on the same droplet (`137.184.41.83`): GitHub Actions SSHs as **`deploy`**, updates **`/opt/poly_glot`**, and restarts the API on **port 8001** (PerFi uses **8000**).

Public API base URL: **`https://poly.thedevmind.com/api`**

---

## SSH keys (read this when you forget)

Polyglot uses its **own** key pair. Do **not** reuse PerFi’s deploy key on the `poly_glot` GitHub repo — GitHub only allows each deploy-key public key on **one** repository.

There are **two jobs** for keys; they are **not** interchangeable:

| Job | Direction | Private key lives | Public key lives |
|-----|-----------|-------------------|------------------|
| **CI deploy** | GitHub Actions → server (`deploy@137.184.41.83`) | GitHub secret **`DEPLOY_SSH_KEY`** | `/home/deploy/.ssh/authorized_keys` |
| **Git pull** | Server → `github.com` (`git pull` in `/opt/poly_glot`) | `/home/deploy/.ssh/polyglot_deploy_key` | **poly_glot** repo → Settings → **Deploy keys** |

For Polyglot, **the same key pair** is used for both rows: private = `polyglot_deploy_key`, public = `polyglot_deploy_key.pub`.

### Files on the server (`deploy` user)

| Path | What it is |
|------|------------|
| `/home/deploy/.ssh/polyglot_deploy_key` | **Private** — paste into GitHub **`DEPLOY_SSH_KEY`** |
| `/home/deploy/.ssh/polyglot_deploy_key.pub` | **Public** — GitHub Deploy keys + `authorized_keys` |
| `/home/deploy/.ssh/authorized_keys` | Allows CI to SSH in (contains the public key line) |
| `/home/deploy/.ssh/config` | Routes GitHub git traffic for Polyglot (see below) |

View keys (as root):

```bash
sudo cat /home/deploy/.ssh/polyglot_deploy_key      # → DEPLOY_SSH_KEY secret (private)
sudo cat /home/deploy/.ssh/polyglot_deploy_key.pub  # → GitHub Deploy keys (public)
```

### GitHub (`marcel-pieper/poly_glot` repo)

| Setting | Value |
|---------|--------|
| **Secrets → Actions → `DEPLOY_SSH_KEY`** | Full contents of **`polyglot_deploy_key`** (private) |
| **Settings → Deploy keys** | Contents of **`polyglot_deploy_key.pub`** (public), with write access if needed |

Workflow reference: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) uses `secrets.DEPLOY_SSH_KEY` and `username: deploy`.

### SSH config for git (Polyglot vs PerFi)

PerFi and Polyglot use **different** GitHub SSH host aliases so each repo uses the right key:

```
# /home/deploy/.ssh/config

Host github.com
  IdentityFile ~/.ssh/perfi_deploy_key
  IdentitiesOnly yes

Host github-polyglot
  HostName github.com
  User git
  IdentityFile ~/.ssh/polyglot_deploy_key
  IdentitiesOnly yes
```

Clone / remote URL for Polyglot (must use **`github-polyglot`**, not `github.com`):

```bash
git clone git@github-polyglot:marcel-pieper/poly_glot.git /opt/poly_glot
# or fix an existing clone:
git -C /opt/poly_glot remote set-url origin git@github-polyglot:marcel-pieper/poly_glot.git
```

### PerFi on the same server (for comparison)

| | PerFi | Polyglot |
|---|--------|----------|
| App path | `/opt/per_fi` | `/opt/poly_glot` |
| API port | 8000 | 8001 |
| Postgres host port | 5432 | 5433 |
| Git SSH host | `github.com` | `github-polyglot` |
| Private key file | `perfi_deploy_key` | `polyglot_deploy_key` |
| GitHub repo secret | `DEPLOY_SSH_KEY` in **per_fi** repo | `DEPLOY_SSH_KEY` in **poly_glot** repo |

### Root’s key (unrelated to deploy workflow)

`root` may have `/root/.ssh/github_key_ed25519` for manual root git operations. **Actions and `/opt/poly_glot` deploys use the `deploy` user**, not root.

---

## One-time server setup

1. **Clone** (as `deploy`):
   ```bash
   sudo mkdir -p /opt/poly_glot
   sudo chown deploy:deploy /opt/poly_glot
   sudo -u deploy git clone git@github-polyglot:marcel-pieper/poly_glot.git /opt/poly_glot
   ```

2. **`backend/.env`** on the server (not in git). Example:
   ```env
   APP_ENV=production
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/polyglot
   JWT_SECRET=<strong-secret>
   OPENAI_API_KEY=<key>
   ```

3. **Postgres**: `docker compose up -d` from `/opt/poly_glot` (host port **5433**).

4. **nginx + TLS** for `poly.thedevmind.com` → proxy `/api/`, `/health`, `/docs` to `127.0.0.1:8001`. Site file: `/etc/nginx/sites-available/polyglot`. Optional: manage via `agent_helpers/server_mcp` (see `agent_helpers/server_mcp/README.md`).

5. **Smoke test** before relying on Actions:
   ```bash
   cd /opt/poly_glot/backend
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   ENV=production APP_ENV=production python run.py
   curl -s http://127.0.0.1:8001/health
   ```

## GitHub Actions deploy

- **Secret:** `DEPLOY_SSH_KEY` = private key `polyglot_deploy_key` (see table above).
- **Trigger:** push to `main` when `backend/`, `docker-compose.yml`, or `.github/workflows/deploy.yml` changes.

## After deploy

- **Health:** `https://poly.thedevmind.com/health`
- **Android** `local.properties`: `API_BASE_URL_RELEASE=https://poly.thedevmind.com/api`
- **Logs:** `/opt/poly_glot/logs/backend-*.log`
- **PID file:** `backend/.polyglot-backend.pid`

## Postgres password drift (Docker volume)

Same gotcha as PerFi: the official Postgres image sets `POSTGRES_PASSWORD` **only when the data directory is empty** (first `docker compose up`). After that, the password lives in the **volume** (`postgres_data`). Changing `POSTGRES_PASSWORD` in `docker-compose.yml` or `DATABASE_URL` in `backend/.env` does **not** update the running database.

**Symptom:** deploy fails at `alembic upgrade head` with:

```text
FATAL: password authentication failed for user "postgres"
```

…on `127.0.0.1:5433`, even though `docker-compose.yml` and `backend/.env` both use `postgres:postgres`.

**Diagnose (on the server):**

```bash
cd /opt/poly_glot

# Inside the container — local socket auth, no password in URL
docker compose exec postgres psql -U postgres -d polyglot -c "SELECT 1"

# From the host — must match DATABASE_URL in backend/.env
PGPASSWORD=postgres psql -h 127.0.0.1 -p 5433 -U postgres -d polyglot -c "SELECT 1"
```

If the first succeeds and the second fails, the volume password does not match `.env` / compose.

**Fix A — keep data (usual):** reset the role password inside the container to match compose and `.env`:

```bash
cd /opt/poly_glot
docker compose exec postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'postgres';"
PGPASSWORD=postgres psql -h 127.0.0.1 -p 5433 -U postgres -d polyglot -c "SELECT 1"
cd backend && source venv/bin/activate && alembic upgrade head
```

**Fix B — empty database only:** remove the volume and recreate (wipes all Polyglot DB data):

```bash
cd /opt/poly_glot
docker compose down -v
docker compose up -d
sleep 5
cd backend && source venv/bin/activate && alembic upgrade head
```

Use **B** only on a fresh prod DB with nothing to keep.

## Alembic `version_num` length

Alembic’s default `alembic_version.version_num` column is **VARCHAR(32)**. Revision `0002_threads_messages_translations` is longer than 32 characters.

**Not in `0001_initial`:** that migration runs *before* Alembic creates `alembic_version` (the table appears when `0001` is stamped).

**Fix in the chain:** `0002_threads_messages_translations.py` starts with:

```sql
ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128);
```

(Use **128** or larger if you add longer revision ids later.)

### If deploy failed with `value too long for type character varying(32)`

The database was up; the failure was the version stamp, not Postgres connectivity. Fix the column once, then re-run migrations.

**On the server (as `deploy` or root):**

```bash
cd /opt/poly_glot

# Option A — docker (matches docker-compose.yml)
docker compose exec postgres psql -U postgres -d polyglot -c \
  "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128);"

# Option B — if psql is on the host and port 5433 is published
psql "postgresql://postgres:postgres@127.0.0.1:5433/polyglot" -c \
  "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128);"
```

Then:

```bash
cd /opt/poly_glot/backend
source venv/bin/activate
alembic upgrade head
```

If `alembic upgrade head` fails with **“relation already exists”** (0002 schema applied but version stuck on `0001_initial`):

```bash
alembic stamp 0002_threads_messages_translations
alembic upgrade head
```

Push the latest `alembic/env.py` fix so future deploys pre-create a wide `alembic_version` table before any migration runs.
