# 2026-10-20 — ping: receipt-retry re-verification (1 day after coached recovery)

Unprompted ping (routing rule 2: freshest-fading node). Question: retry arrives and a
keyed receipt already exists for that request ID — what do you do, and what does the
caller learn?

**Learner answer:** "the payment is pending (we don't know the results) until the
request goes through (complete) and if it doesn't (failed)."

**Grade:** PARTIAL — ~6th fade of the same lookup detail. Status lifecycle
(PENDING/COMPLETE/FAILED) produced unaided = held. The MOVE — don't re-execute, read
the receipt, return the recorded result to the caller — not produced. Re-presented
plainly: success → return the recorded success; failure → return it loud; PENDING →
"sent, unknown" → provider query path.

**Pattern note:** statuses stick, the retry-move fades. Re-explanation is not
converting this node. It passed a cold production rep at ~2 weeks on 10-03 and still
faded afterward — even production-grade evidence decays here. Next rep must change
form (production pseudocode rep / targeted episode), planned as centerpiece of the
~10-22..23 full audit.
