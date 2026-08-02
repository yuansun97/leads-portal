# Coding-agent chat history (reviewer export)

**Session:** Cursor agent · 2026-08-02  
**Purpose:** Representative user ↔ agent dialogue for the assignment’s agent-usage review.  
**Format:** User questions (edited lightly for typos) + shortened high-level agent answers. Tool traces and secrets omitted/redacted.

Companion writeup: [`AGENT_USAGE.md`](./AGENT_USAGE.md) · Attribution: [`../NOTES.md`](../NOTES.md)

---

### 1. Kickoff — PRD + approach
**User:** Build the leads app per the assignment (public form, emails, auth’d attorney UI, PENDING → REACHED_OUT). Create a project under Coding Playground. High-level design first, rough QPS, then dive deep where needed.

**Agent:** Created `leads-portal`. Core is straightforward; care areas are resume storage, transactional email durability, and attorney auth. Proposed sizing and a design-first pass before coding.

---

### 2. Production posture + stack questions
**User:** Treat as light production (public URL), not a demo. Account for DB / email / file storage in deploy. Prefer something lighter than SendGrid. How does FastAPI handle async jobs vs Celery? Is Supabase enough (incl. resumes)? Railway OK; explain Supabase Auth.

**Agent:** Locked toward **Resend** (simple transactional), **Postgres outbox** over pure `BackgroundTasks` (survives crash/deploy; Celery/Redis too heavy), **Supabase** for PG + Storage + Auth at this QPS, **Railway** for API + **Vercel** for Next.js. Supabase Auth (email/password JWT) sufficient for attorney gate.

---

### 3. Lock design decisions
**User:** Agree Resend. Prefer outbox over Celery; AWS EventBridge/SQS/Lambda as future path. Confirm Supabase Auth. Proceed with locked plan.

**Agent:** Confirmed tradeoffs; wrote locked plan (Railway + Supabase + Resend + outbox + shared attorney inbox).

---

### 4. Implement the plan
**User:** Implement the attached plan; don’t edit the plan file; drive existing todos to completion.

**Agent:** Shipped monorepo FastAPI + Next.js, lead CRUD, resume upload, outbox poller, Supabase Auth wiring, admin UI, local run path. Todos completed.

---

### 5. Docs + public GitHub
**User:** Update README (flows/tutorial/structure), expand DESIGN caveats (dupes, security, spam, bottlenecks, scaling). Push to `yuansun97/leads-portal`. Same GitHub owns Supabase/Resend/Railway/Vercel.

**Agent:** Updated README + DESIGN; pushed public repo https://github.com/yuansun97/leads-portal.

---

### 6. Auth / shared inbox / idempotency
**User:** Looks like no attorney auth and all leads shared — is that PRD? If shared, how do we handle two attorneys on the same prospect?

**Agent:** PRD = auth-gated list, not per-attorney ownership → shared inbox is correct. Auth exists (Supabase JWT); local `DEV_AUTH_BYPASS` can hide it. Atomic `UPDATE … WHERE status = PENDING` + claim fields; same attorney idempotent 200, other attorney 409.

**User:** Share detail of the atomic operation.

**Agent:** Walked through conditional SQLAlchemy `UPDATE … RETURNING`, race handling, and claim metadata (`reached_out_by`, email, timestamp).

---

### 7. Deploy to production
**User:** Let’s deploy. *(Later provided Supabase access token + Resend API key — stored privately, not repeated here.)*

**Agent:** Provisioned Railway API + Vercel web + Supabase + Resend; applied schema/bucket; wired env vars.

**User:** Railway healthcheck keeps failing across retries (“service unavailable”).

**Agent:** Root cause: `startCommand` passed literal `${PORT:-8000}` to uvicorn (no shell expansion). Fixed with `sh -c '…'`; API became healthy.

---

### 8. Prod auth bug (401 on leads list)
**User:** What’s the attorney login? Then: admin shows “Invalid or expired token” / 401 on `GET /api/v1/leads`.

**Agent:** Shared demo attorney credentials. Diagnosed JWT alg mismatch: Supabase issued **ES256** (JWKS); API only checked HS256 secret. Added JWKS verification (+ HS256 fallback); list loaded.

---

### 9. Signup then revert
**User:** Add attorney signup.  
**Agent:** Added `/signup` flow.

**User:** Signup isn’t in the PRD — ignore for now.  
**Agent:** Removed signup; invite/admin-provisioned accounts only.

---

### 10. Security hardening
**User:** Thorough security check; Supabase shows no RLS on tables.

**Agent:** Confirmed critical issue: anon key could read `leads` / `email_outbox` via PostgREST. Full audit findings.

**User:** Yes *(apply RLS)*.  
**Agent:** Enabled RLS, revoked anon/authenticated grants; verified PostgREST deny + FastAPI still OK; disabled public signup.

**User:** Yes *(more hardening)*.  
**Agent:** Added `POST /leads` rate limits, production `DEV_AUTH_BYPASS` guard, login `next=` open-redirect harden; verified envs false in prod.

**User:** Update the security audit doc.  
**Agent:** Refreshed `docs/SECURITY_AUDIT.md` (+ related README/DESIGN pointers).

---

### 11. Submission polish + scaling notes
**User:** What’s left?  
**Agent:** Assignment-wise done; remaining = Loom + upload GitHub/Loom links; optional Auth URL / private bucket confirm.

**User:** Set Auth Site URL to Vercel; confirm private resumes bucket; add Loom link to README.  
**Agent:** Done all three.

**User:** Expand caveats: resume capacity, safe QPS, AWS migration triggers.  
**Agent:** Updated DESIGN with storage/egress bands, QPS thresholds, metrics that signal scale-out.

---

### 12. Resume validation + admin pagination
**User:** Do we enforce resume size on submit? Check in the browser too.  
**Agent:** API already caps 10MB; added client-side type/size checks on the public form.

**User:** Paginate leads (API + UI). Then: 10/page; filter Pending / Reached out.  
**Agent:** Implemented `page` / `page_size` / `status` + admin controls.

**User:** UI still shows >10 rows and no page controls.  
**Agent:** Vercel wasn’t auto-picking the web build; redeployed production; verified 10/page + filters + pagination in browser.

---

### 13. List latency / indexes
**User:** List feels slow — how is the table indexed?  
**Agent:** Indexes on `email` + `status` (+ PK); no `created_at` index. At 16 rows, delay is likely **sequential Supabase signed URL** calls per list row, not SQL.

**User:** E2E/pressure look good — final prod check; what must we fix now?  
**Agent:** Good to submit. Health/auth/RLS/outbox OK. Non-blockers: signed-URL latency, missing `created_at` index, CAPTCHA before marketing, etc.

**User:** Parallelize signed URLs? Page size is only 10 — thoughts?  
**Agent:** Optional quick win; fine to ship as-is. Better later: mint signed URL on click, not on list.

**User:** Does the 775ms Network time for `/api/v1/leads` include signed URLs?  
**Agent:** Yes — signed URLs are generated server-side inside that response.

---

### 14. Wrap-up / submission package
**User:** Update Loom to the latest recording; prepare all submission docs; commit/push.

**Agent:** Mapped requirements → `RUN_LOCALLY` / `DESIGN` / `AGENT_USAGE` / `NOTES` / Loom; added `SUBMISSION.md`; pushed to `main` with updated Loom link.

---

### 15. This export
**User:** Export coding-agent chat history for reviewers (questions + shortened high-level answers).

**Agent:** This document.

---

## Notes for reviewers

- Full Cursor transcript is longer (tool calls, retries, deploy logs). This file is the **decision-and-outcome** trail.
- Secrets shared in chat (API keys, passwords) are **not** reproduced here; demo attorney password lived only in private ops notes / env.
- Live app: https://leads-portal-eight.vercel.app · Repo: https://github.com/yuansun97/leads-portal · Loom: https://www.loom.com/share/2a2f4cf9eb6446e58bc729ea27cc1422
