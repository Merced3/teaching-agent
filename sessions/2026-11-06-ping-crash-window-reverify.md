# 2026-11-06 — Ping: crash-window re-verification

Unprompted ping per routing rule 2 (fading `known` node — sd/crash-window, sd/invariant,
sd/state-machine, sd/write-boundary all tied oldest at last evidence 2026-10-23, 14 days).
Chose crash-window. Owed recall queue (timeout-unknown-state due 11-07..10, keyed-receipt
cold re-check ~11-10..13) not yet due today.

**Question:** service charges the card, then dies before writing the receipt — what two
failure modes are you forced to choose between?

**Answer (unaided, same day):** duplication or loss; pick loss — no chance of duplication.

**Verdict:** correct and unaided. Loss is right here: a missing record of a successful
charge is recoverable later (provider query by request ID); a duplicate charge is
customer-facing harm you cannot take back. Recorded as `explained`, delay_days 14,
coached false. Retention holds at 14 days.

Still owed, unchanged: (1) sd/timeout-unknown-state re-check due 2026-11-07..10
(executed-vs-pending, "don't know" is the asker's position); (2) sd/keyed-receipt
UNAIDED full-pattern cold re-check ~2026-11-10..13 (blank page, four moves, must include
check-store-first and retry-returns-recorded-result).

Next node per routing: sd/timeout-unknown-state (rule 1 — owed, due tomorrow 11-07).

Model: Alvar (pi).
