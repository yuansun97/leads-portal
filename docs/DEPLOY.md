# Deploy

Target topology: **Vercel** (web) + **Railway** (API) + **Supabase** + **Resend**.

## 0. GitHub

```bash
gh auth login
cd /path/to/leads-portal
gh repo create leads-portal --public --source=. --remote=origin --push
```

Then continue with Supabase / Resend / Railway / Vercel below.


1. Create a project.
2. Apply schema: run Alembic against the database URL, or execute [`supabase/schema.sql`](../supabase/schema.sql) in the SQL editor.
3. Storage → create private bucket `resumes` (MIME: PDF/DOC/DOCX, max 10MB).
4. Auth → create attorney user(s) (email/password). Disable public signup for production. Set Authentication → URL Configuration: Site URL = your Vercel origin; add the same origin under Redirect URLs.
5. Settings → API: copy URL, anon key, service role key.
6. Settings → API → JWT Secret (only needed for legacy HS256 projects).
7. Storage → confirm `resumes` bucket is **private** (MIME: PDF/DOC/DOCX, max 10MB).

**Database URL for Railway:** use the direct connection or session mode pooler (`postgresql+asyncpg://...`). Avoid transaction pooler for SQLAlchemy long-lived sessions.

## 2. Resend

1. Create an API key.
2. Verify your sending domain (DNS records).
3. Note `from` address and attorney notify inbox.

## 3. Railway (API)

1. New project from this GitHub repo.
2. Set **Root Directory** to `apps/api` (Dockerfile lives there).
3. Environment variables:

```
DEV_AUTH_BYPASS=false
ENVIRONMENT=production
CORS_ORIGINS=https://YOUR_VERCEL_DOMAIN
# optional tuning
LEAD_CREATE_PER_IP_PER_MINUTE=5
LEAD_CREATE_PER_EMAIL_PER_HOUR=10
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_JWT_SECRET=          # leave empty unless the project still signs HS256
SUPABASE_RESUMES_BUCKET=resumes
EMAIL_ENABLED=true
RESEND_API_KEY=...
RESEND_FROM=Northbridge <leads@yourdomain.com>
ATTORNEY_NOTIFY_EMAIL=attorney@yourdomain.com
```

4. Deploy. Confirm `GET https://YOUR_RAILWAY_URL/health`.

## 4. Vercel (web)

1. Import the same repo; **Root Directory** `apps/web`.
2. Environment variables:

```
NEXT_PUBLIC_API_BASE_URL=https://YOUR_RAILWAY_URL
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_DEV_AUTH_BYPASS=false
```

3. Deploy. Update Railway `CORS_ORIGINS` if the Vercel URL changed.

## 5. E2E checklist

- [ ] Public form submits a lead
- [ ] Prospect + attorney emails arrive (or show as `sent` in `email_outbox`)
- [ ] Login with Supabase attorney works
- [ ] Admin list shows the lead; resume opens via signed URL
- [ ] Mark reached out transitions status

## Notes

Railway/Vercel CLIs were not available in the implementation environment; deploy via dashboards using the steps above. `apps/api/railway.toml` and `apps/web/vercel.json` document expected build/health settings.
