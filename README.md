# Leads Portal

Public lead intake form and attorney admin console.

**Stack:** Next.js (Vercel) · FastAPI (Railway) · Supabase (Postgres / Storage / Auth) · Resend

## Quick links

- [Run locally](docs/RUN_LOCALLY.md)
- [Design](docs/DESIGN.md)
- [Deploy](docs/DEPLOY.md)
- [Agent usage](docs/AGENT_USAGE.md)
- [Attribution](NOTES.md)

## Features

- Public multipart lead form (name, email, resume)
- Confirmation + attorney notification emails via Resend (Postgres outbox)
- Auth-guarded admin list with `PENDING → REACHED_OUT`
- Private resume storage (Supabase Storage or local disk in development)

## Repo layout

```
apps/api   FastAPI service
apps/web   Next.js app
docs/      Design, run, deploy, agent notes
supabase/  SQL schema reference
```
