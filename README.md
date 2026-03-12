# Polyglot Starter (FastAPI + Expo + Postgres)

This is a simple local-first starter for **Polyglot**:
- Backend: FastAPI
- Frontend: React Native with Expo
- Database: Postgres via Docker Compose
- Auth: Passwordless (email + verification code, no password)
- OpenAI: basic backend integration endpoint

## 1) Prerequisites

- Docker + Docker Compose
- Python 3.11+ and `pip`
- Node 20+ and `npm`
- Android phone with **Expo Go** app installed
- Phone and dev machine on the same Wi-Fi network

## 2) Project structure

- `backend/` FastAPI app, auth flow, DB models, Alembic migrations
- `frontend/` Expo app with simple login UI
- `docker-compose.yml` Postgres service

## 3) First-time setup

### 3.1 Start Postgres

From repo root:

```bash
docker compose up -d
```

### 3.2 Setup backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:
- Health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### 3.3 Setup frontend

In a new terminal:

```bash
cd frontend
cp .env.example .env
```

Edit `frontend/.env`:
- Set `EXPO_PUBLIC_API_BASE_URL` to your machine LAN IP, for example:
  - `http://192.168.1.100:8000/api/v1`

Then run:

```bash
npm install
npm run start
```

Scan the QR code in terminal with Expo Go on Android.

## 4) Test flow on Android

1. In Expo app, enter your email and tap **Send verification code**.
2. Check backend terminal logs. You will see:
   - `Dev verification code for you@example.com: 123456`
3. Enter that 6-digit code in the app and tap **Verify and login**.
4. App stores token locally and shows logged-in user info from `/me`.

## 5) API overview

- `POST /api/v1/auth/request-code`
  - body: `{ "email": "you@example.com" }`
- `POST /api/v1/auth/verify-code`
  - body: `{ "email": "you@example.com", "code": "123456" }`
- `GET /api/v1/me`
  - requires bearer token
- `POST /api/v1/ai/dummy`
  - body: `{ "prompt": "..." }`
  - if `OPENAI_API_KEY` is missing, returns a dummy fallback message

## 6) Environment files

- `backend/.env` from `backend/.env.example`
- `frontend/.env` from `frontend/.env.example`

Important backend vars:
- `DATABASE_URL`
- `JWT_SECRET`
- `OPENAI_API_KEY` (optional for now)

## 7) Common scripts

### Backend

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm run start
```

## 8) Troubleshooting

- If phone cannot reach backend:
  - Confirm backend runs on `0.0.0.0`
  - Confirm `EXPO_PUBLIC_API_BASE_URL` uses LAN IP (not `localhost`)
  - Confirm both devices are on same network
  - Check local firewall rules for port `8000`
- If migration fails:
  - Check Postgres is healthy: `docker compose ps`
  - Re-run: `alembic upgrade head`
- If Expo QR not loading:
  - Try `npm run start -- --tunnel`

Postgres is exposed on host port `5433` by default to avoid collisions with any existing local Postgres using `5432`.
