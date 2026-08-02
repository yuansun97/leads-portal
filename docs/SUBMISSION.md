# Submission map

Public repo: **https://github.com/yuansun97/leads-portal**  
Live app: **https://leads-portal-eight.vercel.app**  
E2E recording: **https://www.loom.com/share/2a2f4cf9eb6446e58bc729ea27cc1422**

| Requirement | Artifact |
|---|---|
| Public GitHub repo | This repository (`main`) |
| How to run locally | [`RUN_LOCALLY.md`](./RUN_LOCALLY.md) · short path in [`README.md`](../README.md) |
| Design document (why/how) | [`DESIGN.md`](./DESIGN.md) (includes [post-PRD roadmap](./DESIGN.md#post-prd-roadmap-v11)) |
| Coding-agent usage (½ page) | [`AGENT_USAGE.md`](./AGENT_USAGE.md) |
| Chat excerpts (Q&A export) | [`CHAT_HISTORY.md`](./CHAT_HISTORY.md) |
| Raw user questions | [`CHAT_QUESTIONS_RAW.md`](./CHAT_QUESTIONS_RAW.md) |
| Attribution (agent vs hand) | [`NOTES.md`](../NOTES.md) |
| Screen recording (E2E) | Loom link above (also in README) |

Optional supporting docs (not required by the prompt, useful for reviewers):

- [`DEPLOY.md`](./DEPLOY.md) — production topology
- [`SECURITY_AUDIT.md`](./SECURITY_AUDIT.md) — production hardening notes
- [`DESIGN.md` § Post-PRD roadmap](./DESIGN.md#post-prd-roadmap-v11) — v1.1 backlog (dedupe/versions, login throttle/MFA, etc.)

## Suggested grader path (5–10 min)

1. Watch the Loom.
2. Skim `DESIGN.md` (architecture + outbox + shared-inbox claim; optional post-PRD roadmap).
3. Run locally via `RUN_LOCALLY.md` **or** open the live app and submit a lead + attorney login.
4. Read `AGENT_USAGE.md` + `CHAT_HISTORY.md` + `NOTES.md`.
5. Spot-check `apps/api/app/api/routes/leads.py` and `apps/api/app/services/outbox.py`.
