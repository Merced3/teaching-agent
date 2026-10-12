# 2026-10-12 — cold ping: backoff/jitter split

Question posed 2026-10-11, re-posed 2026-10-12 (learner had left it + the 10-10 UX follow-up unanswered; re-asked one question rather than stacking a third thread).

## Result (~3 days after coached same-day close on 10-09; taught 10-08)

- **Backoff:** recalled unaided — flagged uncertainty ("I think you would've said exponential backoff") then gave it: exponential growth of the wait every interval. Correct.
- **Jitter:** recalled unaided — random number on each backoff interval to spread out incoming requests, "more digestible for the system." Correct — that's the desynchronization job.
- **The split itself held** (the thing he couldn't do on 10-08 and was coached through on 10-09): backoff = how long, jitter = how synchronized.

Evidence level: recalled unaided, ~3 days. First retention-grade result on the backoff/jitter node.

Sharpening given (not a correction): jitter barely changes the average wait — its whole job is the spread.

Still owed in the 2026-10-10..14 window: five-question audit, precondition + reconciliation-job names, provider-lookup-by-request-ID, went-through/never-happened tail branches, and the open UX probe (what the user sees during unknown-state re-checking — posed 10-10, still unanswered).
