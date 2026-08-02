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

## PRD interpretation: shared attorney inbox

The assignment asks for an **internal UI guarded by auth** that lists leads, and a manual `PENDING → REACHED_OUT` transition after an attorney reaches out. It does **not** require per-attorney ownership, assignment queues, or prospect isolation between attorneys.

**v1 model:** any authenticated attorney sees the full lead list (shared firm inbox). That matches the PRD wording.

**Auth is implemented** (Supabase JWT on `GET/PATCH /leads*`, Next.js middleware on `/admin/*`). Locally it can look “missing” because `DEV_AUTH_BYPASS=true` accepts Bearer `dev-token` without a real login — that is **dev-only** and must be off in production (`ENVIRONMENT=production`, `DEV_AUTH_BYPASS=false`, real Supabase Auth users).

### Concurrent attorneys (idempotency / double outreach)

Shared inbox implies two attorneys can open the same `PENDING` lead.

| Case | Behavior |
|---|---|
| Same attorney marks twice | Idempotent **200** — already claimed by them |
| Two attorneys race | Single atomic `UPDATE … WHERE status = PENDING`; winner wins |
| Loser / late click | **409** with who claimed it (`reached_out_by` / email) |
| UI | Shows claimer email; refreshes list on 409 |

Fields: `reached_out_by` (auth `sub`), `reached_out_by_email`, `reached_out_at`.

This prevents double status writes; it does **not** stop both from emailing the prospect before either clicks — that would need soft-claim / “I’m working this” locking, which is out of PRD scope but a natural follow-up.

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

## Caveats and risk areas

### Duplicate leads and resume versioning

- **No dedupe in v1.** The same email can submit many times; each creates a new lead + emails. Product risk: attorney noise and duplicate outreach.
- **Mitigations later:** unique constraint on `(email)` for open `PENDING` leads, or soft-merge UI (“related submissions”).
- **Resumes are immutable per lead.** Path is `{lead_id}/{filename}`. Re-submit = new lead, not a new version on the same row. There is no resume version history or replace flow.
- **Orphan files:** if DB insert fails after Storage upload, the object can remain without a lead row. Add compensating delete or upload-after-commit in a later iteration.

### Security

- Public `POST /leads` is unauthenticated by design — treat it as an attack surface (see spam below).
- Service role key bypasses Storage RLS; a leak is critical. Keep it only on Railway; rotate if exposed.
- Signed resume URLs expire (default ~1h) but are shareable while valid; avoid logging them.
- Local `DEV_AUTH_BYPASS` / Bearer `dev-token` must never be enabled in production.
- File validation is MIME + size only — not AV scanning or content sniffing beyond `content_type`. Malicious PDFs are possible; open resumes in a hardened viewer if threat model requires it.
- No CSRF token on the public form; browser CORS + same-site defaults help for cookie sessions, but the create API is callable cross-origin without cookies. Rate limits and bot checks matter more than CSRF here.

### Spam and abuse

- No CAPTCHA, IP rate limit, or email verification before accept.
- Attackers can fill storage and trigger email volume (Resend cost / reputation).
- **Add before public marketing traffic:** edge rate limit (e.g. Vercel/Railway/WAF), honeypot or Turnstile, and optional confirmation email before attorney notify.
- Resend domain reputation: monitor bounces/complaints; keep transactional stream clean.

### System bottlenecks

| Bottleneck | Why | Symptom |
|---|---|---|
| Resume upload | Multipart + Storage RTT on request path | Slow `POST /leads` (seconds) |
| Outbox poller in API process | Shares CPU with HTTP; single process claim loop | Delayed emails under load or during deploys |
| Signed URL generation on list | List includes resume URLs | Higher latency / Storage QPS as list grows |
| Postgres connections | SQLAlchemy pool + Railway replicas | Exhaustion if many replicas without pooler tuning |

Create path does **not** wait on Resend (outbox), which is intentional. Worst user-facing latency is upload + DB commit.

### Scaling thresholds (rough)

| Signal | Approx threshold | Action |
|---|---|---|
| Leads/day | &lt; 1k | Current design fine |
| Leads/day | 1k–10k | Rate limits, CAPTCHA, watch Storage + Resend spend |
| Sustained create QPS | &gt; ~5–10 | Separate outbox worker process; consider direct-to-Storage upload |
| Email volume | Hits Resend daily/monthly caps | Paid plan; eventually EventBridge + SQS + Lambda |
| Attorney list size | Thousands of rows, no filters | Pagination UX + indexes already present; add filters/search |
| API replicas &gt; 1 | Duplicate pollers OK with `SKIP LOCKED` | Still prefer dedicated worker for isolation |

Celery/Redis stay out of scope until email or job volume forces a broker. Documented scale path: outbox → EventBridge + SQS + Lambda.

### Monitoring and alerts

**v1 has no first-class observability stack** (no Datadog/Sentry wired). Minimum production checklist:

| Signal | How | Alert when |
|---|---|---|
| API health | Railway healthcheck `/health` | Failing probes |
| Create errors | Platform HTTP 5xx metrics | Spike in `POST /leads` 5xx |
| Outbox lag | Query `email_outbox` where `status in (pending,failed)` and `attempts` high | Age of oldest pending &gt; N minutes |
| Outbox poison | `status = failed` after max attempts | Any sustained growth |
| Resend | Provider dashboard / webhooks (future) | Bounce/complaint rate |
| Storage | Supabase usage | Approaching plan limits |
| Auth | Failed login / 401 rates on admin routes | Unexpected spikes (credential stuffing) |

Log lines already emit outbox send failures; ship logs to a drain and add a periodic SQL check or small admin badge for failed emails.

### Operational caveats

- Multi-replica deploys briefly double pollers — safe with row locks; may send faster, not incorrectly if idempotency keys are honored by Resend.
- Alembic runs on container start — overlapping deploys should use a single migration leader or rely on Postgres DDL locks carefully.
- Supabase Auth is the stickiest migration dependency (password hashes); keep authorization in FastAPI so IdP swap stays feasible.

## Alternatives considered

- SQLite: simpler local, weaker production story.
- SendGrid: heavier than needed for plain transactional mail.
- Sync email in request path: couples UX to provider latency/failures.
