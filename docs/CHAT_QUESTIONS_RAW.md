# Chat questions (raw)

All user questions from the Cursor coding-agent session, **unsummarized**.
System/tool prompts (e.g. background task notices) omitted.
API keys in the original chat are redacted here.

---

## 1. Sunday, Aug 2, 2026, 10:12 AM (UTC-7)

Assignment
Functional Requirements
Develop an application to support creating, getting and updating leads. A lead is a form PUBLICLY available for prospects to fill in, the required fields include,

first name

last name

email

resume / CV

Once the lead is submitted by a prospect, the application will send emails to both the prospect and an attorney inside the company.

In addition, the application powers an internal UI guarded by auth to render a list of leads with all the information filled in by the prospect. Each lead also has a state, it starts with a PENDING state and transitions to REACHED_OUT when marked manually by an attorney after he / she reaches out to the prospect.

Tech Requirements
Create a system design to fulfill the above requirements

Develop the web app & APIs E2E using coding agents of your choice

The APIs need to be implemented using FastAPI and the web app using NextJS

Add a storage to persist data and integrate with an email service

Properly structure the code similar to how you would for a production level repo

Submission Guidance
Submit your code to a publicly available github repo

Submit a document on how to run your application locally in the same repo

Submit a design document on why/how you make those design choices in the same repo

Submit a Document your coding-agent usage. Heavy use is encouraged — we're evaluating how you use agents, not whether.

A short writeup (½ page max): which tools you used, what you delegated vs. wrote yourself and why, and one place the agent produced wrong or subtly bad code — how you caught it and fixed it.

Representative prompt logs or session transcripts (excerpts are fine).

Attribution in your commits or a NOTES file marking agent-generated vs. hand-written code.

Upload the github link in the assignment document within 6 hours since you start the exercise

Upload a short screen recording (e.g., Loom) showing the E2E workflow

1. Let's create a new project directory under "Coding Playground", then carry out the conversation from there. 
2. Per my understanding, it's a straightforward web app prtal, doesn't seem to have tricky parts but lmk if you think otherwise. 
3. I'm thinking to quickly go through a high-level deisgn, do a back of envelop calc on traffic qps, then dive deep into any components there if needed

---

## 2. Sunday, Aug 2, 2026, 10:29 AM (UTC-7)

1. Let's treat it as a light-weight production app that will be pulished and deployed, rather than a demo 
2. We need to deploy the application in production with a public url, so we need to handle all the dependencies correctly: db, email delivery service, files storage. Let's take the deployment efforts into considerations too when picking the tech stack and dependency services. 
3. What mailing service are we gonna use? SendGrid might be too much since the notification email should be simple text without fancy template management? should we some more light-wieght service? There might be some email background tasks management iteration too, eg tracking the async status and retry etc. note down for reference 
4. On async jobs: does FastAPI provide any async framework such as Celery in Django? 
5. On data storage, the qps looks reasonable to me, based on the low volume, does Supabase work sufficiently here? I think supabase can handle the structured data above well, let's confirm if resume files work well with it too. Again, deployment and maitainability is the main motivation here, data itself can be stored and handled easily

---

## 3. Sunday, Aug 2, 2026, 10:44 AM (UTC-7)

3. Agreed with the mailing component. Lock v1 scope, use Resend 
4. Tradeoffs between BackgroundTasks v.s. Postgres outbox? Celery and Redis should be out, it's too heavy for the scope of this app. For future scalability, we can easily switch to aws managed service, event bridge + sqs + lambda if email volume spikes. Let's nail down BackgroundTasks <> Postgres outbox for v1. In each framework how does the workers get managed? 
5. I lean to use Supabase for its deploybility, but one last check: how does it compare with aws managed storage, and let's give it a quick assessment on data migration cost if we need to do so in the future 

Re:
1. Railway is fine. 
2. Tell me more about Supabase Auth, I'm ok with the built-in auth as long as it suffies

---

## 4. Sunday, Aug 2, 2026, 10:45 AM (UTC-7)

Leads Portal — Locked Design & Implementation Plan

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

## 5. Sunday, Aug 2, 2026, 11:08 AM (UTC-7)

1. Update the read me file, note down the user flow, functoinality and tutorial 
2. layout the code structure for review  
3. add a new section in the design doc noting down the caveats and risk areas, e.g. duplicate leads and resume versioning, security, spam and abuse, system bottlenecks, scaling thresholds, monitoring and alerts etc. 

Re:
1. https://github.com/yuansun97 push the repo to this account 
2. Supabase + Resend + Railway + Vercel are all connected to the same github account above

---

## 6. Sunday, Aug 2, 2026, 11:19 AM (UTC-7)

One functional callout, there's no login / auth for attorney and all prospects seem to be accessible and shared by all potential attorneys -- if that's what the PRD meant (double check for me), then we need to think how to handle the idepotency, e.g. two attorneys processing the same prospect. 

"the application powers an internal UI guarded by auth to render a list of leads with all the information filled in by the prospect." the app seems missing the auth for atterney

---

## 7. Sunday, Aug 2, 2026, 11:26 AM (UTC-7)

share the detail of the atomic operation for idepotency

---

## 8. Sunday, Aug 2, 2026, 11:29 AM (UTC-7)

let's deploy

---

## 9. Sunday, Aug 2, 2026, 11:36 AM (UTC-7)

Supabase Access Tokens: sbp_[REDACTED]
Resend key: re_[REDACTED]

---

## 10. Sunday, Aug 2, 2026, 12:02 PM (UTC-7)

seems you are running in circle, railway shows the same error logs arocss all four deploy retries, it always failed at Healthcheck: "Attempt #5 failed with service unavailable. Continuing to retry for 40s". When I ran diagnosis it failed too: Diagnosis failed for this deployment.

---

## 11. Sunday, Aug 2, 2026, 12:13 PM (UTC-7)

Testsing in prod now. What's the attorney credential i can use to login?

---

## 12. Sunday, Aug 2, 2026, 12:16 PM (UTC-7)

Seeing "Invalid or expired token" error on the leads list page and there should be two testing leads but the UI did not show anything. I checked console "Failed to load resource: the server responded with a status of 401 ()"

---

## 13. Sunday, Aug 2, 2026, 12:16 PM (UTC-7)

GET https://api-production-06b2.up.railway.app/api/v1/leads?page=1&page_size=50 401 (Unauthorized)

---

## 14. Sunday, Aug 2, 2026, 12:16 PM (UTC-7)

GET https://api-production-06b2.up.railway.app/api/v1/leads?page=1&page_size=50 401 (Unauthorized)

---

## 15. Sunday, Aug 2, 2026, 12:20 PM (UTC-7)

let's add signup functionality for atterneys

---

## 16. Sunday, Aug 2, 2026, 12:23 PM (UTC-7)

Just realized crating attorney accounts is not in the PRD. Let's ignore it for now

---

## 17. Sunday, Aug 2, 2026, 12:26 PM (UTC-7)

Flagging a few caveats before we ramp up, let's run a thorough security check across the app and dependency services to ensure it's production ready, e.g. Supabase shos no Row Level Security (RLS) enabled for all three tables in this project.

---

## 18. Sunday, Aug 2, 2026, 12:46 PM (UTC-7)

yes

---

## 19. Sunday, Aug 2, 2026, 12:47 PM (UTC-7)

yes

---

## 20. Sunday, Aug 2, 2026, 1:37 PM (UTC-7)

update the security audit doc

---

## 21. Sunday, Aug 2, 2026, 1:41 PM (UTC-7)

what's left now ?

---

## 22. Sunday, Aug 2, 2026, 1:55 PM (UTC-7)

Yes do the following: Supabase Auth Site URL → Vercel origin, Confirm resumes bucket is private

Include the loom demo video in the read me file: https://www.loom.com/share/9c957723c25c4fda8d8479a5d113f830

---

## 23. Sunday, Aug 2, 2026, 1:59 PM (UTC-7)

On the risk and caveats section, 
What we've covered: rate limit on submission to prevent spam, private bucket for resume storage, security and auth checks across services

What's left, let's review the production scaling scenario: up to how many resumes does Supabase support? the safe qps threshold we are looking at now? what metrics we should look closely to determine we need to sclae or migrate to managed services in aws

---

## 24. Sunday, Aug 2, 2026, 2:02 PM (UTC-7)

did we enforce the size limit per resume at submission?

---

## 25. Sunday, Aug 2, 2026, 2:03 PM (UTC-7)

let's check at the browser

---

## 26. Sunday, Aug 2, 2026, 2:03 PM (UTC-7)

on the list of leads page, we might need pagination as well, UI and api

---

## 27. Sunday, Aug 2, 2026, 2:06 PM (UTC-7)

10 leads per page by default; filter to show pending only, reached out only;

---

## 28. Sunday, Aug 2, 2026, 2:08 PM (UTC-7)

the UI still shows more than 10 rows the page, and no pages options

---

## 29. Sunday, Aug 2, 2026, 2:08 PM (UTC-7)

the UI still shows more than 10 rows the page, and no pages options

---

## 30. Sunday, Aug 2, 2026, 2:13 PM (UTC-7)

Seeing some delay on listing leads, suspecting it's the query, how did we index the table?

---

## 31. Sunday, Aug 2, 2026, 2:16 PM (UTC-7)

E2E testing, pressure test look good on my end. Can you do a one last round of production check, and call out the points need to addressed now? otherwise I'm ok proceed to the submission part and wrap up the work

---

## 32. Sunday, Aug 2, 2026, 2:19 PM (UTC-7)

i"generating 10 Supabase signed resume URLs sequentially—one network call per row—during every list request." -- this can be a quick fix by parallelling them? it's prob ok anyways, as the page size is just 10. wdyt

---

## 33. Sunday, Aug 2, 2026, 2:21 PM (UTC-7)

Based on the console, api/v1/leads?page=1&page_size=10 takes 775ms for server response, does signed url goes into that or not

---

## 34. Sunday, Aug 2, 2026, 2:34 PM (UTC-7)

update the latest loom video link: https://www.loom.com/share/2a2f4cf9eb6446e58bc729ea27cc1422

---

## 35. Sunday, Aug 2, 2026, 2:35 PM (UTC-7)

Let's wrap up. Review the submission, I know we already have a few docs ready, help me prepare all the docs to submit, 

Submission Guidance

Submit your code to a publicly available github repo

Submit a document on how to run your application locally in the same repo

Submit a design document on why/how you make those design choices in the same repo

Submit a Document your coding-agent usage. Heavy use is encouraged — we're evaluating how you use agents, not whether.

A short writeup (½ page max): which tools you used, what you delegated vs. wrote yourself and why, and one place the agent produced wrong or subtly bad code — how you caught it and fixed it.

Representative prompt logs or session transcripts (excerpts are fine).

Attribution in your commits or a NOTES file marking agent-generated vs. hand-written code.

Upload the github link in the assignment document within 6 hours since you start the exercise

Upload a short screen recording (e.g., Loom) showing the E2E workflow

---

## 36. Sunday, Aug 2, 2026, 2:36 PM (UTC-7)

and yes, commit and push the latest loom video link

---

## 37. Sunday, Aug 2, 2026, 2:41 PM (UTC-7)

Export the coding agent chat history for reviwer's refrence. With my questions and shortened high-level agent answers are fine

---

## 38. Sunday, Aug 2, 2026, 2:43 PM (UTC-7)

a new file for all my questions in chat raw, no summarized

---
