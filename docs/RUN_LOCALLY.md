# Run locally

## Prerequisites

- Node.js 20+
- Python 3.13+ and [uv](https://github.com/astral-sh/uv)
- PostgreSQL 16 (Docker Compose **or** Homebrew `postgresql@16`)

## 1. Database

**Option A — Docker**

```bash
docker compose up -d
```

Connection string:

```
postgresql+asyncpg://postgres:postgres@localhost:5432/leads
```

**Option B — Homebrew** (used during development when Docker was unavailable)

```bash
brew install postgresql@16
brew services start postgresql@16
createdb leads   # as your OS user
```

Connection string example:

```
postgresql+asyncpg://YOUR_OS_USER@localhost:5432/leads
```

## 2. API

```bash
cd apps/api
cp .env.example .env
# edit DATABASE_URL if needed; keep DEV_AUTH_BYPASS=true for local admin
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Health: [http://localhost:8000/health](http://localhost:8000/health)

With `EMAIL_ENABLED=false`, emails are logged instead of sent via Resend.  
With empty Supabase keys, resumes land in `apps/api/uploads/`.

## 3. Web

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

With `NEXT_PUBLIC_DEV_AUTH_BYPASS=true` and placeholder Supabase URLs, `/login` → **Enter admin** uses Bearer `dev-token` against the API.

## 4. Smoke test

```bash
# create lead
curl -X POST http://localhost:8000/api/v1/leads \
  -F first_name=Ada \
  -F last_name=Lovelace \
  -F email=ada@example.com \
  -F resume=@./sample.pdf;type=application/pdf

# list (dev auth)
curl -H "Authorization: Bearer dev-token" http://localhost:8000/api/v1/leads
```

## Optional: real Supabase + Resend locally

1. Create a Supabase project; run `supabase/schema.sql` (or Alembic against the Supabase DB URL — use the **session** pooler / direct connection for FastAPI).
2. Create private Storage bucket `resumes` (PDF/DOC/DOCX, 10MB).
3. Copy project URL, service role key, JWT secret, and anon key into API/web env files.
4. Create an attorney user in Supabase Auth.
5. Set `DEV_AUTH_BYPASS=false` / `NEXT_PUBLIC_DEV_AUTH_BYPASS=false`.
6. Add a Resend API key and set `EMAIL_ENABLED=true`.
