# Session close — 2026-11-21..25 retention sweep (ping-driven)

Model: Claude (Alvar, Discord harness). Channel: discord, unprompted ping slots.

## What happened
A full retention sweep of the sd/ map via daily unprompted pings. One question per slot; outstanding questions re-asked (never stacked). Seven nodes re-verified, all unaided:

- 11-21 purpose-of-tests: explained, 15d. ("tests prove our current idea works, not that the idea is right; that's why maintenance")
- 11-22 keyed-receipt: explained, 6d (receipt+request ID atomic before send; retry skips re-executing). Also idempotency: explained, 3d — own synthesis "retry-safe protects the user, idempotency protects the system."
- 11-22 timeout-unknown-state: applied, 6d (pending/executed/failed; blind retry = double-charge).
- 11-23 jitter: explained, 5d ("smaller and smaller mountain peaks; give the provider room to breathe").
- 11-23 state-machine: explained, 5d (CLOSING as crash witness; resume completes the close).
- 11-23 write-boundary: recalled, 5d ("border patrol at every crossing — always or nothing").
- 11-24 atomicity: explained, 5d (all-or-nothing; refined: unit = set of writes that must succeed/fail together, not a fixed count).
- 11-25 backoff: explained, 6d (stretches intervals, herds persist but shrink; connected jitter on top himself).

Result: every node on the map now has evidence ≤5 days old. Sweep complete.

## Learner observations
Answers are compressed, metaphor-rich, and reliably unaided at 5–6 day delays across the whole map — concepts AND mechanisms both held this week (contrast with the 11-19..21 stretch where names/distinctions faded first). The daily ping + plain re-ask cadence is working.

## Next owed
- sd/invariant — last evidence 11-20 (coached explained; abstraction fades fastest for this learner). Re-verify ~11-26.
- sd/purpose-of-tests — 11-21; re-verify ~11-28.

Next node per routing: sd/invariant (rule 2 — oldest evidence after the sweep, and the known fast-fader).
