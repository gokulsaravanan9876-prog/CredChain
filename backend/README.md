# CredChain Backend

FastAPI + PostgreSQL backend for CredChain. Replaces the frontend's mock
`src/lib/api.ts` layer with a real REST API, real persistence, real
authentication, and real cryptographic credential signing/verification.

**Status: Phase 1 only** — app wiring, database connection, Alembic
migrations, health endpoint. No models, auth, or business routes yet —
those land in later phases.

## Architecture

```
React (Vite, :5173)
      |  fetch() with Authorization: Bearer <JWT>
      v
FastAPI (:8000)
      |
Service layer (app/services)
      |
SQLAlchemy ORM (app/models)
      |
PostgreSQL
```

## Requirements

- Python 3.11+ (developed against 3.13)
- PostgreSQL 14+ running locally (or via Docker)

## Setup

```bash
cd backend
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# edit .env — at minimum set DATABASE_URL to match your local Postgres
```

## PostgreSQL setup

If you don't have Postgres running yet, the fastest path is Docker:

```bash
docker run --name credchain-db -e POSTGRES_USER=credchain -e POSTGRES_PASSWORD=credchain -e POSTGRES_DB=credchain -p 5432:5432 -d postgres:16
```

Or with a native install, create the role/db manually:

```sql
CREATE USER credchain WITH PASSWORD 'credchain';
CREATE DATABASE credchain OWNER credchain;
```

Then make sure `.env`'s `DATABASE_URL` matches whichever you chose:

```
DATABASE_URL=postgresql+psycopg2://credchain:credchain@localhost:5432/credchain
```

## Run the backend

```bash
uvicorn app.main:app --reload
```

- API root: http://localhost:8000
- Health check: http://localhost:8000/api/health
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

`GET /api/health` returns `{"status": "ok", "database": "connected"}` when
both the API process and the Postgres connection are healthy, or
`"database": "unavailable"` if the DB can't be reached (check `DATABASE_URL`
and that Postgres is actually running).

## Database migrations (Alembic)

No models exist yet in Phase 1, so there's nothing to migrate. Once Phase 2
adds models, migrations are managed with:

```bash
# generate a migration from model changes
alembic revision --autogenerate -m "description"

# apply all pending migrations
alembic upgrade head

# roll back one migration
alembic downgrade -1
```

Alembic reads `DATABASE_URL` from `app.config.settings` (i.e. from your
`.env`) — `alembic.ini` intentionally does not hardcode a connection string,
so there's exactly one place the DB URL lives.

## Project structure

```
backend/
  app/
    main.py          — FastAPI app, CORS, health endpoint
    config.py         — Settings loaded from .env (pydantic-settings)
    database.py        — SQLAlchemy engine/session, Base, get_db()
    models/             — SQLAlchemy ORM models (Phase 2+)
    schemas/             — Pydantic request/response schemas (Phase 3+)
    routes/               — FastAPI routers (Phase 3+)
    services/              — business logic, called by routes (Phase 3+)
    security/                — password hashing, JWT, permissions, signing (Phase 3+)
  alembic/                    — migration environment + versions/
  storage/                      — private document storage root (Phase 4+, git-ignored)
  requirements.txt
  .env.example
```

## Frontend integration

The frontend's `VITE_API_BASE_URL` (see `../.env.example` at the frontend
root once added) should point at `http://localhost:8000/api`. CORS is
configured via `CORS_ORIGINS` in `.env` (comma-separated), defaulting to
`http://localhost:5173` — the Vite dev server's default port.

## Security notes (so far)

- `.env` is git-ignored; only `.env.example` (placeholders, no real secrets) is committed.
- `JWT_SECRET_KEY`'s example value is explicitly a dev placeholder — generate a real one before any real deployment: `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- No authentication, password storage, or signing exists yet — those are Phase 3+ and will get their own security notes as they're added.

## What's next (not in this phase)

Phase 2 adds the SQLAlchemy models (users, students, institutions,
companies, credentials, documents, requests, shares, verification events,
activity log) and the first real Alembic migration.
