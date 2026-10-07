# 2026-10-07 — keyed-receipt preconditions lesson (voice)

Context: carried-over lesson request from earlier same day (learner asked for keyed-receipt preconditions, anchored on the socratic-partner project). Voice session, Socratic probing throughout.

## What happened, in order
1. Learner self-assessed: knows keyed receipts are atomic, store an action ID, exist for idempotency and retry-safety — but iffy on the difference between those two.
2. Probed the distinction via double-charge scenario. Learner separated them correctly unaided: retry-safe = twice doesn't break, idempotent = twice = same result; and explained the early-return-on-existing-key mechanism unaided.
3. Probed the crash window (payment sent, crash before receipt saved). Learner initially "no clue," then derived the fix unaided: write the receipt before the external call, and chose the prefer-loss trade-off himself. Coached only the name: that's a precondition.
4. Learner asked how a human fixes a stuck in-progress receipt. Taught: look up receipt, query provider by action ID, mark complete or roll back.
5. Learner independently proposed automating that as a background async process. Taught the name (reconciliation job) and the enabling trick: your action ID travels with the payment request, so the provider can be queried by it.

## Evidence
- precondition concept: derived unaided (coached naming only) — explained grade, same-day.
- idempotency-vs-retry-safe: recalled/explained unaided, same-day (had split on 2026-10-02 — re-probe after delay owed).
- crash-window / unweldable-outside-world insight: re-applied unaided, consistent with 2026-10-06.
- reconciliation job: presented (name + mechanism) — re-probe owed.

## Owed
- Delayed re-probe of "precondition" + "reconciliation job" names and the write-before-send mechanism, ~2026-10-10 to 2026-10-14.
- Consolidation lecture episode still UNPROBED.

Model: Alvar (pi).
