# 2026-11-06 — Ping: state-machine re-verification

Second unprompted ping of the day (routing rule 2). After the crash-window re-verify,
sd/invariant, sd/state-machine, sd/write-boundary remained tied-oldest at last evidence
2026-10-23 (14 days). Chose state-machine.

**Question:** why give a lifecycle a middle state like CLOSING instead of OPEN → CLOSED
directly — what does it buy when something crashes?

**Answer (unaided, same day):** the middle state exists only for the crash case; in a
no-crash world you wouldn't need it. When a crash happens it tells you what state of the
world you're in, and it makes retry safe — CLOSING is more a flag than a state, so on
resume you go straight CLOSING → CLOSED instead of sitting in OPEN and forgetting you
were mid-action.

**Verdict:** correct and unaided, 14-day delay. The "persisted flag" framing is exactly
the witness idea: the middle state records that the transition was attempted but not
confirmed complete, so recovery can finish it deliberately. Recorded `explained`,
delay_days 14, coached false.

Still owed, unchanged: (1) sd/timeout-unknown-state re-check due 2026-11-07..10
(executed-vs-pending); (2) sd/keyed-receipt UNAIDED cold re-check ~2026-11-10..13.
Oldest nodes now: sd/invariant and sd/write-boundary (10-23).

Next node per routing: sd/timeout-unknown-state (rule 1 — owed, due 11-07).

Model: Alvar (pi).
