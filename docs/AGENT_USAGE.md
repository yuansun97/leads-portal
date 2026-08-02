# Agent usage

**Tools:** Cursor (Grok agent) with shell, file edits, plan mode, MCP `create_project` / `move_agent_to_root`. No separate AutoGPT/Aider run.

**Delegated to the agent**

- Monorepo scaffold (FastAPI + Next.js)
- SQLAlchemy models, Alembic migration, outbox poller, Resend adapter
- Supabase Auth wiring (`@supabase/ssr`, JWT dependency)
- Public form + admin UI
- Design / run / deploy docs drafts

**Written or steered by hand**

- Stack lock (Railway + Supabase + Resend + Postgres outbox)
- Rejection of Celery/Redis; outbox + lifespan poller decision
- Local fallbacks (`DEV_AUTH_BYPASS`, disk uploads) when Docker/Supabase were unavailable
- Auth 401 vs 500 behavior for bad tokens without JWT secret
- Resume download via authenticated fetch + blob (browser cannot attach Bearer on `<a href>`)

**One place the agent got it subtly wrong**

Initial auth dependency returned **500** when `SUPABASE_JWT_SECRET` was empty and a non-dev token was presented — treating “not configured” as a server error. For a public API that should look like failed auth to clients (and not trip Railway error budgets), that was wrong. Caught with a curl smoke test (`Authorization: Bearer bad` expected 401). Fixed by returning 401 whenever verification cannot succeed, and only accepting `dev-token` under explicit non-production bypass.

**Prompt / session excerpts**

1. “Treat it as a light-weight production app… Resend… nail down BackgroundTasks <> Postgres outbox… Supabase deployability…”
2. “Implement the plan as specified… mark todos in progress… don’t stop until all todos are completed.”

**Attribution:** see [NOTES.md](../NOTES.md).
