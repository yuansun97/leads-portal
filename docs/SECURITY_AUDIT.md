# Security Audit — Leads Portal

**Date:** 2026-08-02  
**Scope:** FastAPI (Railway) · Next.js (Vercel) · Supabase (Postgres / Auth / Storage) · Resend  
**Method:** Code review + live PostgREST anon probe + production env verification + rate-limit smoke test

App data path is **FastAPI → Postgres via `DATABASE_URL`**. The browser anon key is for Supabase Auth only. Service role is Storage-only on the API.

---

## Status summary

| Severity | Open | Resolved |
|---|---|---|
| Critical | 0 | 1 |
| High | 1 (residual: no CAPTCHA / edge WAF) | 3 |
| Medium | 2 | 1 |
| Low | 1 | 0 |

**Ramp gate (must-have):** cleared — RLS/revokes applied, signup disabled, bypass flags false in prod, in-process rate limit verified.

**Before heavy marketing:** edge/WAF rate limit + CAPTCHA/Turnstile; set Auth Site URL to the Vercel origin; optional magic-byte resume sniff.

---

## Findings

### Critical

| ID | Finding | Status | Notes |
|---|---|---|---|
| C1 | No RLS on `leads` / `email_outbox`; anon key could `GET /rest/v1/…` and read PII | **Resolved** | Enabled RLS (no anon/authenticated policies), `REVOKE ALL` from those roles. Re-probe: anon → 401, authenticated JWT via PostgREST → 403. FastAPI list still 200. Captured in `supabase/schema.sql` + Alembic `003_rls_revoke_postgrest`. |

### High

| ID | Finding | Status | Notes |
|---|---|---|---|
| H1 | Public Supabase signup; any `authenticated` JWT = attorney on API | **Mitigated** | `disable_signup=true` (invite-only). API still has no role/allowlist — keep Auth invite-only. Optional later: `app_metadata.role` check in `require_attorney`. |
| H2 | Public `POST /leads` with no abuse controls | **Mitigated** | In-process limits: 5/IP/min, 10/email/hour per Railway replica. Verified in prod (5×201 then 429). Still no CAPTCHA or edge WAF — add before marketing traffic. |
| H3 | `DEV_AUTH_BYPASS` / frontend bypass risk in production | **Resolved** | Railway: `ENVIRONMENT=production`, `DEV_AUTH_BYPASS=false`. Vercel: `NEXT_PUBLIC_DEV_AUTH_BYPASS=false` (forced + redeployed). API startup refuses bypass when production. `.env.example` defaults are `false`. |

### Medium

| ID | Finding | Status | Notes |
|---|---|---|---|
| M1 | Login `next=` open redirect | **Resolved** | `safeNextPath()` allows only `/admin…` same-origin paths. |
| M2 | Resume validation is Content-Type only; signed URLs ~1h and shareable | **Open** | MIME allowlist + 10MB cap; no magic-byte sniff / AV. Keep `resumes` bucket private. |
| M3 | Auth Site URL still `http://localhost:3000` | **Open** | Set Site URL + Redirect URLs to the production Vercel origin in Supabase Auth settings. |

### Low / Info

| ID | Finding | Status | Notes |
|---|---|---|---|
| L1 | CORS `allow_methods/headers=*`; JWT `iss` not pinned | **Open (accepted for v1)** | Prod `CORS_ORIGINS` is HTTPS-only (2 origins, no localhost). Optionally pin `iss` to `https://<ref>.supabase.co/auth/v1`. |
| I1 | Architecture: no PostgREST for app SQL; service role Storage-only | **Good** | Keep this split. |

---

## Applied remediations (production)

```sql
alter table public.leads enable row level security;
alter table public.email_outbox enable row level security;
revoke all on table public.leads from anon, authenticated;
revoke all on table public.email_outbox from anon, authenticated;
grant all on table public.leads to postgres, service_role;
grant all on table public.email_outbox to postgres, service_role;
```

| Control | Evidence |
|---|---|
| PostgREST deny | Anon `GET /rest/v1/leads` → 401 permission denied |
| App path OK | Attorney `GET /api/v1/leads` → 200 |
| Signup off | Auth `disable_signup=true` |
| Rate limit | Sixth `POST /leads` from same IP → 429 |
| Bypass off | Railway + Vercel flags false; API guard on boot |

---

## Remaining checklist

| Item | Owner | Priority |
|---|---|---|
| Confirm `resumes` bucket is private (no public policies) | Supabase Storage | Verify |
| Auth Site URL + redirect allowlist = Vercel production URL | Supabase Auth | Do soon |
| Edge/WAF rate limit + Turnstile/honeypot on public form | Vercel / Cloudflare | Before marketing |
| Magic-byte sniff for PDF/DOCX | API | Nice to have |
| Optional attorney role/allowlist claim in JWT | API + Auth | Nice to have |
| Pin JWT `iss` | API | Nice to have |

---

## Already in good shape

- Attorney FastAPI routes verify Supabase JWT (ES256 JWKS or legacy HS256, `aud=authenticated`).
- Resumes via service role + signed URLs; filenames sanitized; size capped at 10MB.
- `REACHED_OUT` claim is atomic (`UPDATE … WHERE status = PENDING`).
- Secrets (`.env`, `.secrets/`) gitignored; service role not in the browser bundle.
- Outbox emails use idempotency keys; no resume links in email bodies.

---

## Related docs

- Design caveats: [`DESIGN.md`](./DESIGN.md) (Security / Spam sections)
- Deploy env checklist: [`DEPLOY.md`](./DEPLOY.md)
