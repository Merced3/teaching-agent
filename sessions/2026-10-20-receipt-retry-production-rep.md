# 2026-10-20 — receipt-retry PRODUCTION rep (later same day)

Context: morning ping's receipt-retry question graded PARTIAL (statuses held, the
retry-move faded ~6th time). Learner flagged the question as confusing ("didn't know
what I was answering") — fair, it was a compound question. Re-asked plainly: retry
arrives, receipt exists, walk me through what your code does.

**Learner produced handler pseudocode UNAIDED:**
- Look up request ID, read stored result/status. (lookup-first ✓)
- COMPLETE → show COMPLETE, no second charge (noted: depends on what's sold). ✓
- FAILED → show FAILED, allow retry. ✓
- unknown/none → hand request ID to reconciliation job, show PENDING, disable retry. ✓
- reconciliation_job: bounded while-loop, `inappropriate_time_limit` → break,
  `notify_human()` after loop. ✓ bounded re-asking + human escalation.
- SELF-ADDED: provider_API_rate_limit check + slow_down() — unprompted transfer from
  the backoff/jitter node. Named out loud as transfer evidence.

**Sharpening given (one):** the reconciliation job must WRITE the learned result back
into the receipt, so future refreshes/retries are answered by the top branch.

**Grade:** applied / production rep, unaided — but same-day as the morning
re-presentation, so retention still unproven. Strongest evidence on this node since
the 10-03 cold production rep. Owed: cold re-probe after real delay.
