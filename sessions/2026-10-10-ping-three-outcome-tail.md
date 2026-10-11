# 2026-10-10 — cold ping: three-outcome tail (unknown branch)

Cold recall ping fired (window 2026-10-10..14, routing rule 1). Question: reconciliation job asks the provider, answer is "unknown" — what does the system do, what does the user see?

## Result

Learner answered (~1 day after coached lesson, unaided): "if it keeps on coming back as unknown, keep on checking the order status until the pending status becomes inappropriate. After that time, flag for a human."

- **Mechanism: recalled unaided, ~1 day.** Bounded re-asking + human escalation at the limit, in own words. This is the branch he missed entirely in yesterday's first attempt and got coached on — now holding at 1 day.
- **Gap: user-facing piece not mentioned.** The honest "still confirming" UX (never show success, never show failure while unknown) was not in the answer. Follow-up probe posed in chat, unanswered at time of writing.

Evidence level: mechanism = recalled unaided, 1 day. UX piece = pending probe.

Still owed in the 2026-10-10..14 window: five-question audit, precondition + reconciliation-job names, provider-lookup-by-request-ID, backoff/jitter split, and the went-through/never-happened branches of the tail (only the unknown branch was probed here).
