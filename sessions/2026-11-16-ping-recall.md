# 2026-11-16 — Ping-driven recall day (invariant rebuild + timeout win)

Model: Alvar (pi). No lesson thread; all work via unprompted pings + replies. Prior context: sessions/NEXT-BOOT.consumed-2026-11-16.md (written 11-15).

## What happened

1. **sd/invariant cold re-probe** (was due 11-11..12, asked 11-16). Definition recalled unaided but with enforcement folded in; charge-flow invariant NOT recalled — learner guessed the receipt-write mechanism, self-questioned. Coached rebuild across three exchanges: mechanism-vs-rule distinction re-taught; double-charge rule produced on prompt; directions probed — charge-without-record NEVER (correct), record-without-charge said OKAY (wrong — corrected: silent revenue leak). Learner volunteered atomicity as the guard (mechanism correctly attached). Lock-in then collapsed: labeled three mechanisms as "invariants" and surfaced a REAL design bug — request ID saved AFTER the provider call instead of generated-first/sent-with. Corrected; gave heuristic "rules are about data; mechanisms are verbs." Ended at fatigue/question-substitution signal.
2. **sd/timeout-unknown-state cold check** (due ~11-15, asked + answered 11-16). UNAIDED WIN at 8d: executed/failed/pending enumeration immediate (the list that failed at 5d on 11-07 and re-armed 11-08 now holds). Recovery flow produced unaided: check receipt, provider query by request ID, branch failed/pending/completed. No blind retry embodied (named the rule for him after). Receipt-before-provider composition held (11-06 coached fix retained at 10d).
3. **Transfer moments:** request-ID-before-send correction (made 1h earlier) surfaced unprompted in the timeout walkthrough — same-day transfer. Keyed-receipt move 3 (return recorded result — coached YESTERDAY 11-15) applied unaided in the completed branch ("retry skips it, they already paid") — 1d retention of a coached move.

## Events appended (6, all 2026-11-16)

- sd/invariant: recalled/unaided/8d (partial — definition only, mechanism conflation); recognized/coached/8d (charge-flow rebuild); recognized/coached/0d (lock-in collapse + request-ID bug fix)
- sd/timeout-unknown-state: recalled/unaided/8d (enumeration); applied/unaided/8d (recovery flow)
- sd/keyed-receipt: applied/unaided/1d (move 3 held inside timeout walkthrough)

View regenerated via kb_derive. No git commit (nightly cron).

## Owed next (mirrors sessions/NEXT-BOOT.md)

1. sd/invariant cold re-check ~2026-11-18..19 (distinction + charge-flow invariant).
2. sd/keyed-receipt move-3 cold re-check ~2026-11-22.
3. sd/timeout-unknown-state next cold check ~2026-11-23..24.

Next node per routing: sd/invariant (rule 1 — re-check due 11-18..19; 11-17 is SILENT or a one-line lesson offer at the edge).
