# Design Document

## Problem

Capture prospect leads (name, email, resume), notify both prospect and attorney, and give attorneys an authenticated UI to review leads and mark outreach complete.

## Architecture

```
Prospect / Attorney → Next.js (Vercel)
                         ↓
                    FastAPI (Railway)
                    ↙    ↓     ↘
            Supabase   Outbox   Resend
           PG+Storage  poller
```

| Layer | Choice | Rationale |
|---|---|---|
| Web | Next.js App Router on Vercel | Spec + zero-ops frontend hosting |
| API | FastAPI on Railway | Spec + long-lived process for outbox poller |
| Data / files / auth | Supabase | One managed vendor; low ops at low QPS |
| Email | Resend | Lightweight transactional API; no template product needed |

## Traffic sizing

Assumptions: ~200–1000 leads/day, attorney list polling ~2 QPS.

Peak create QPS ≈ 0.12. Design target ~10 QPS sustained. Bottlenecks are resume upload I/O and email latency, not CPU/DB. No cache, queue broker, or read replica in v1.

## Lead lifecycle

1. Public `POST /api/v1/leads` (multipart) validates fields + resume MIME/size.
2. Resume uploaded to private Storage (or local `uploads/` in dev).
3. Single DB transaction inserts `leads` (`PENDING`) + two `email_outbox` rows.
4. `BackgroundTasks` kicks immediate send; lifespan poller retries durable leftovers.
5. Attorney lists leads; `PATCH` allows only `PENDING → REACHED_OUT`.

## Email: outbox vs BackgroundTasks

Pure `BackgroundTasks` runs in the same uvicorn worker and is lost on crash/deploy. Rejected for production.

**v1:** Postgres outbox is source of truth. An asyncio poller in FastAPI `lifespan` claims rows with `FOR UPDATE SKIP LOCKED`, sends via Resend, applies exponential backoff. Optional BackgroundTasks wake reduces latency only.

Celery/Redis excluded as too heavy. Scale path: treat outbox rows as events → EventBridge + SQS + Lambda.

## Supabase vs AWS S3

At this volume both work. Supabase wins on deployability (DB + Storage + Auth together). Storage is S3-compatible; private bucket + signed URLs fit resumes.

### Migration cost if leaving Supabase

| Asset | Cost | Notes |
|---|---|---|
| Postgres data | Low | `pg_dump` / SQLAlchemy stays portable |
| Resume objects | Low–medium | Scripted copy to S3; path remap |
| Auth users | Medium–high | Password hashes usually not portable; re-invite |
| App authz | Low | Rules live in FastAPI; Auth is an IdP |

## Supabase Auth

Email/password for attorneys. Next.js uses `@supabase/ssr`; API verifies HS256 JWT with `SUPABASE_JWT_SECRET` (audience `authenticated`). Public create stays open. Dev bypass (`DEV_AUTH_BYPASS` + Bearer `dev-token`) is local-only.

## Security notes

- Resumes never in a public bucket.
- Service role key only on the API.
- CORS locked to web origin(s).
- `DEV_AUTH_BYPASS` forced off conceptually in production (`environment` check).

## Alternatives considered

- SQLite: simpler local, weaker production story.
- SendGrid: heavier than needed for plain transactional mail.
- Sync email in request path: couples UX to provider latency/failures.
