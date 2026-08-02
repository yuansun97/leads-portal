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

Email/password for attorneys. Next.js uses `@supabase/ssr`; the API verifies the access token with audience `authenticated`. Supabase projects on asymmetric signing keys issue ES256 tokens verified against the project JWKS endpoint; legacy projects sign HS256 with `SUPABASE_JWT_SECRET`, and both paths are supported. Public create stays open. Dev bypass (`DEV_AUTH_BYPASS` + Bearer `dev-token`) is local-only.

## Security notes

- Resumes never in a public bucket.
- Service role key only on the API.
- CORS locked to web origin(s).
- `DEV_AUTH_BYPASS` forced off conceptually in production (`environment` check).

## Caveats and risk areas

### What we have covered (production hardening)

| Area | Control |
|---|---|
| Spam on public submit | In-process rate limits on `POST /leads` (5/IP/min, 10/email/hour per replica); verified 429 in prod |
| Resume confidentiality | Private `resumes` bucket; anon object GET denied; access via service-role upload + short-lived signed URLs |
| Postgres exposure | RLS on `leads` / `email_outbox` + `REVOKE` from `anon`/`authenticated`; app uses `DATABASE_URL` only |
| Auth | Invite-only (`disable_signup`); JWT verify (JWKS/HS256); Site URL = Vercel origin; prod bypass flags off; API refuses `DEV_AUTH_BYPASS` in production |
| Shared-inbox races | Atomic `PENDING → REACHED_OUT` claim with 409 for losers |

Still open before **heavy marketing**: edge/WAF rate limit + CAPTCHA/Turnstile (in-process limits are not enough against distributed bots).

### Duplicate leads and resume versioning

- **No dedupe in v1.** The same email can submit many times; each creates a new lead + emails. Product risk: attorney noise and duplicate outreach.
- **Mitigations later:** unique constraint on `(email)` for open `PENDING` leads, or soft-merge UI (“related submissions”).
- **Resumes are immutable per lead.** Path is `{lead_id}/{filename}`. Re-submit = new lead, not a new version on the same row. There is no resume version history or replace flow.
- **Orphan files:** if DB insert fails after Storage upload, the object can remain without a lead row. Add compensating delete or upload-after-commit in a later iteration.

### Security (residual)

- Public `POST /leads` remains unauthenticated by design — rate limits help; CAPTCHA/edge WAF still recommended before marketing.
- Service role key bypasses Storage RLS; a leak is critical. Keep it only on Railway; rotate if exposed.
- Signed resume URLs expire (default ~1h) but are shareable while valid; avoid logging them.
- File validation is MIME + size only — not AV scanning or magic-byte sniffing. Malicious PDFs are possible; open resumes in a hardened viewer if the threat model requires it.
- Any Supabase `authenticated` user is treated as an attorney — keep Auth invite-only (or add a role claim later).

### Spam and abuse

- No CAPTCHA or email verification before accept.
- In-process API rate limits are a first line of defense only (per Railway replica; not global across IPs).
- Distributed attackers can still fill storage and burn Resend quota/reputation.
- **Before public marketing traffic:** edge rate limit (Cloudflare/Vercel WAF), honeypot or Turnstile, monitor Resend bounces/complaints.

### System bottlenecks

| Bottleneck | Why | Symptom |
|---|---|---|
| Resume upload | Multipart + Storage RTT on the request path | Slow `POST /leads` (seconds) |
| Outbox poller in API process | Shares CPU with HTTP; single process claim loop | Delayed emails under load or during deploys |
| Signed URL generation on list | List includes resume URLs | Higher latency / Storage QPS as list grows |
| Postgres connections | SQLAlchemy pool + Railway replicas | Exhaustion if many replicas without pooler tuning |

Create path does **not** wait on Resend (outbox), which is intentional. Worst user-facing latency is upload + DB commit.

### Production scaling: resumes, QPS, and when to leave Supabase

#### How many resumes can Supabase hold?

Object count is not the hard limit — **included Storage GB + egress** are. This app caps each resume at **10MB**; planning averages below assume ~**1MB** typical (adjust if your corpus is larger).

| Plan (Supabase pricing as of 2026) | Included file storage | ~Resumes @ 1MB avg | ~Resumes @ 10MB max | Notes |
|---|---|---|---|---|
| Free | 1 GB | ~1,000 | ~100 | Pauses on inactivity; demos only |
| Pro | 100 GB included (then ~$0.021/GB) | ~100,000 | ~10,000 | Practical production default; storage scales with overage |
| Team / Enterprise | Same Storage baseline / custom | 100k+ | 10k+ | Buy for support/SLA/compliance, not raw object count |

**Egress matters as much as storage.** Pro includes ~250 GB uncached + 250 GB cached egress/month. Rough download budget if each lead’s resume is opened once (~1MB):

| Leads / month | Resume egress (order of magnitude) | On Pro 250 GB quota |
|---|---|---|
| 1k leads/day (~30k/mo) | ~30 GB | Comfortable |
| 5k leads/day (~150k/mo) | ~150 GB | Watch dashboard; usually OK |
| 10k leads/day (~300k/mo) | ~300 GB | Likely overage or CDN/cache tuning; revisit S3 |

Database size for `leads` + `email_outbox` stays tiny vs Storage (rows are KB-scale). Postgres disk is not the resume bottleneck.

#### Safe QPS for the *current* architecture

Assumptions stay: ~200–1000 leads/day → average create ≪ 0.1 QPS; design headroom ~10 QPS sustained.

| Band | Sustained `POST /leads` | What it means for this stack |
|---|---|---|
| **Comfortable (today)** | **&lt; ~1 QPS** | Single Railway API + Supabase Storage/DB + in-process outbox are fine |
| **Watch closely** | **~1–5 QPS** | Upload latency dominates; watch p95 create time, Storage errors, pooler wait, outbox lag |
| **Scale the app first** | **~5–10 QPS** | Split outbox worker from HTTP; consider browser→Storage direct upload + API metadata-only; add edge rate limits |
| **Re-architect / AWS path** | **&gt; ~10 QPS sustained** or sharp marketing spikes | Dedicated queue (SQS), object storage at S3 scale, possibly multiple API replicas with external worker |

Attorney list traffic (~2 QPS polling in the original sizing) is cheap vs creates; the expensive unit of work is **multipart upload + Storage write**, not the Postgres insert.

Rate-limit ceiling today (5/IP/min) caps a single client but **does not** define global capacity — N IPs can still sum to more than one replica wants to handle.

#### Metrics that say “scale in place” vs “migrate to AWS”

**Scale in place (stay on Supabase/Railway/Vercel/Resend)** when you hit app bottlenecks but plan quotas are healthy:

| Metric | Watch for | First action |
|---|---|---|
| `POST /leads` p95 / p99 latency | Climbing toward multi-second or timeouts | Direct-to-Storage upload; raise Railway compute |
| `POST /leads` 5xx / Storage 5xx | Sustained error rate | Retry/backoff; check Supabase status; replica sizing |
| Outbox oldest `pending` age | &gt; 5–15 minutes | Dedicated worker process; increase poll batch |
| Outbox `failed` after max attempts | Growing pile | Resend health; poison-queue triage |
| Postgres pool wait / connection errors | Non-zero under load | Session pooler tuning; fewer oversized pools per replica |
| Railway CPU / memory | Sustained high during creates | Larger instance or split worker |

**Migrate components toward AWS managed services** when cost, compliance, or hard ceilings dominate — not at a magic lead count:

| Signal | Why it pushes AWS | Likely target |
|---|---|---|
| Storage + egress bill ≫ app value, or &gt;100 GB hot objects with heavy re-download | S3 + CloudFront usually cheaper/clearer at media scale | **S3** (+ CloudFront); keep FastAPI signing or CloudFront signed URLs |
| Need multi-AZ SLA, HIPAA, private networking, org IAM | Supabase Pro is convenience-first; Enterprise/AWS fit regulated ops | **RDS Postgres** or Aurora; **Cognito** / SSO IdP |
| Email volume hits Resend caps or needs SES reputation tooling | Provider/ops choice | **SES** (+ SNS bounce hooks); keep outbox table |
| Sustained create QPS &gt; ~10 or fan-out jobs | In-process poller is the wrong abstraction | Outbox → **EventBridge + SQS + Lambda** (or ECS worker) |
| Auth becomes sticky enterprise requirement | Password-hash portability is the costly Supabase exit | Migrate IdP last; keep FastAPI authz |

**Practical rule of thumb for this product:** stay on the current stack through **~1k leads/day** without drama; treat **~1–5k/day** as “instrument and maybe split the worker”; start an AWS storage/queue design brief when you forecast **sustained &gt;5–10 create QPS**, **Storage/egress overages as a line item**, or a **compliance** requirement — whichever comes first.

Celery/Redis stay out of scope until email or job volume forces a broker. Documented scale path: outbox → EventBridge + SQS + Lambda; resumes → S3.

### Monitoring and alerts

**v1 has no first-class observability stack** (no Datadog/Sentry wired). Minimum production checklist:

| Signal | How | Alert when |
|---|---|---|
| API health | Railway healthcheck `/health` | Failing probes |
| Create latency / errors | Platform HTTP metrics for `POST /leads` | p95 regression or 5xx spike |
| Outbox lag | `email_outbox` where `status in (pending,failed)` | Oldest pending age &gt; N minutes |
| Outbox poison | `status = failed` after max attempts | Any sustained growth |
| Resend | Provider dashboard / webhooks (future) | Bounce/complaint rate |
| Storage / egress | Supabase usage (GB stored, egress) | &gt;70% of plan quota |
| DB connections | Supabase + Railway metrics | Pool wait / connection errors |
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
