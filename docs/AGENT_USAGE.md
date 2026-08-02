# Agent usage

**Tools:** Cursor IDE agent (Grok) — plan mode, file edits, shell, browser verification, Railway/Supabase CLIs via MCP/shell. No separate AutoGPT/Aider run.

**Delegated to the agent (most of the implementation)**

- Monorepo scaffold (FastAPI + Next.js), models, Alembic, outbox poller, Resend adapter
- Supabase Auth wiring (`@supabase/ssr`, JWT dependency), public form + admin UI
- Deploy/debug loops (Railway startCommand/`PORT`, ES256 JWKS auth, RLS migration)
- Drafts of design / run / deploy / security docs

**Written or steered by hand (product + correctness)**

- Stack lock: Railway + Supabase + Resend; reject Celery/Redis for v1 → Postgres outbox + lifespan poller
- Shared-inbox / atomic `PENDING → REACHED_OUT` claim semantics
- Auth failure must be **401** (not 500); production guards for `DEV_AUTH_BYPASS`
- Resume open via authenticated fetch + blob (Bearer cannot ride on `<a href>`)

**One place the agent produced subtly bad code**

Initial `require_attorney` returned **500** when `SUPABASE_JWT_SECRET` was unset and a non-dev token arrived — treating misconfiguration as a server fault. For a public API that should fail closed as “not authenticated,” that was wrong (and noisy for error budgets). Caught with `curl -H "Authorization: Bearer bad"` expecting **401**. Fixed by returning 401 whenever verification cannot succeed; `dev-token` only under explicit non-production bypass.

A second live catch: the agent first verified only HS256 with the JWT secret; production Supabase issued **ES256**. Admin list returned 401 for valid sessions. Fixed by reading the JWT `alg` and verifying via JWKS (with HS256 fallback).

**Representative prompts**

1. “Treat it as a light-weight production app… Resend… nail down BackgroundTasks vs Postgres outbox… Supabase deployability…”
2. “Implement the plan as specified… mark todos in progress… don’t stop until all todos are completed.”
3. “Flagging… Supabase shows no RLS… run a thorough security check… then apply the fix.”

**Attribution:** [NOTES.md](../NOTES.md) (A/H/M tags by path).  
**Session excerpts (longer Q&A):** [CHAT_HISTORY.md](./CHAT_HISTORY.md).
