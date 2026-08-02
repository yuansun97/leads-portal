# NOTES — attribution

Convention: **A** = primarily agent-generated · **H** = hand-directed / hand-fixed · **M** = mixed

| Path | Tag | Notes |
|---|---|---|
| `apps/api/app/**` | M | Agent scaffold; H steered auth status codes, JWKS path, rate limits, claim update, local storage |
| `apps/api/alembic/**` | A | Incl. RLS revoke migration |
| `apps/api/app/core/rate_limit.py` | A | In-process sliding window; H set prod defaults |
| `apps/api/app/core/security.py` | M | Agent first pass; H forced 401-not-500 + ES256/JWKS |
| `apps/web/src/app/**` | M | Agent UI; H resume blob download, login `next=` harden, pagination/filters |
| `apps/web/src/lib/**` | A | |
| `docs/DESIGN.md` | M | From design conversation; agent drafted / expanded caveats |
| `docs/RUN_LOCALLY.md` | M | Includes Homebrew Postgres path from setup |
| `docs/DEPLOY.md` | M | Agent draft; H Auth URL / private bucket checklist |
| `docs/SECURITY_AUDIT.md` | M | Findings from review; remediations applied with agent |
| `docs/AGENT_USAGE.md` | H | |
| `docs/CHAT_HISTORY.md` | H | Shortened Q&A export from Cursor session |
| `docs/SUBMISSION.md` | H | Grader map |
| `supabase/schema.sql` | A | RLS + revoke included |
| `docker-compose.yml` | A | |
| Plan / stack / shared-inbox decisions | H | Collaborative design before and during implementation |

Commit messages are narrative of the work; this file is the explicit agent vs hand split.
