# 2026-10-21 — Timeout strand capstone (lesson thread: unknown-state-after-timeout)

Model: Alvar (pi). Surface: Discord text, lesson thread.

## What happened

1. Thread resumed from 10-20 open; probe re-asked: charge call to provider hangs/times out — (a) what do you know about the state of the world, (b) what breaks on shrug-reset-and-retry?
2. Learner answered UNAIDED: knows nothing; possibilities = provider executed it / still working / failed; self-connected the keyed receipt + request ID; blind retry risks double-charging ("big no no"). Sharpening given: receipt written BEFORE the call, marked PENDING — ordering is load-bearing.
3. Next probe: walk the recovery path step by step — user on a spinner, how do they learn the true outcome without double-charge risk?
4. Learner assembled the full path UNAIDED: lookup keyed receipt + request ID first; no request ID → no receipt (atomic action) → safe to retry; receipt present → check status on provider end; if it times out again, mark/keep PENDING and re-query by request ID later, never re-execute; user shown whatever status the request ID resolves to.
5. Two sharpenings given: (a) on retry the receipt isn't "skipped" — it RETURNS the recorded result, and the reconciliation job must WRITE the learned result back into the receipt so future refreshes hit the top branch (the chronic-fade detail, 6 prior fades); (b) pending is not an ending — spinner becomes an honest "we're confirming," bounded re-asking by the job, human escalation when too old.
6. Learner asked whether his step-by-step was what was wanted — confirmed, graded out loud as the strand capstone. He'd forgotten `/lesson end` syntax; asked that stating the command in wrap-ups be recorded → logged in docs/learner.md (observed, 2026-10-21).

## Evidence recorded

- Timeout possibilities + double-charge risk: recalled/applied UNAIDED, ~2 weeks after teaching (strand taught 10-08..10-09).
- Full recovery path: applied/transfer UNAIDED, ~2 weeks. Strongest evidence on this node to date.
- Retention after real delay: STILL OWED (cold re-probe ~2026-10-26+).

## Pings today

Three unprompted ping slots, all answered SILENT — open lesson probe + nothing recall-due until the 10-22..23 audit; one-open-question cadence held (matches 2026-10-18 precedent).

## Owed after this session

- Full five-question audit re-ping 2026-10-22..23 (learner standing request) — centerpieces: receipt-retry production rep, state-machine name (chronic fader), unknown-branch tail detail.
- Cold re-probe of receipt-retry production ~2026-10-26+.
- NEW: cold re-probe of the timeout-recovery path ~2026-10-26+.

Next node per routing: owed recall pings (rule 1) — full audit 10-22..23.
