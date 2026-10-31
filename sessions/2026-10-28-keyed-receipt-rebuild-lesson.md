# 2026-10-28 — keyed-receipt rebuild lesson (after 5-day retention failure)

Model: Alvar (pi). Channel: Discord lesson thread "keyed-receipt rebuild". Trigger: same-day self-reported retention failure (name recalled, mechanism gone) during idempotency ping — see sessions/2026-10-28-pings-and-keyed-receipt-lesson-open.md.

## What happened (in order)

- Probe: re-derive the pattern. Learner produced the checkpoint/save-game framing unaided: write the save before the dangerous call, resume skips the finished side-quest. Receipt-before-send: re-derived, unaided.
- Gap located: no picture for "keyed". First guess: key = user ID + farthest progress. Broken by counterexample (Friday pizza skipped because Monday's receipt matched user ID) — learner saw the break. Operation-not-person: landed after counterexample (coached).
- Who creates the key: learner first said "client side, before the crash" unaided, then dropped it in the walkthrough (server minted the key). Walked the server-minted design breaking (retry can't name the receipt → double charge). Coached correction; vocabulary friction ("mint") was teacher-caused, owned in-thread.
- Same-vs-new fingerprint discrimination (Monday retry = same, Friday pizza = new): correct, unaided, fast.
- Unprompted transfer: pulled reconciliation job + pending state into the sent-but-unknown crash window (from sd/timeout-unknown-state / sd/reconciliation-job). Not coached.
- Final integrative playback (whole pattern, own words, under stated fatigue): all pieces present but SEQUENCE garbled — receipt-before-send stated late and out of order, reconciliation job overused as catch-all. Synthesis ordering degrades before individual pieces do.
- Lesson wrapped by learner fatigue ("I'm tired"). Cold re-probe owed 2026-11-01 to 11-05 (3–7 days).

## Evidence event appended

- sd/keyed-receipt — explained, coached, delay 0 (2026-10-28). Notes: rebuilt all pieces post-fade; crash windows + fingerprint rule unaided; client-creates-key needed one correction; ordered synthesis still shaky.

## Learner model update

- Added to docs/learner.md (observed): under fatigue, individual pieces stay intact but sequencing/synthesis degrades first — final garbled playback followed a string of correct unaided answers. End lessons at first fatigue signal; the synthesis probe belongs early or fresh.

## Next node per routing

sd/backoff delayed re-check (rule 1, due 2026-10-29), then sd/keyed-receipt cold re-probe 11-01 to 11-05.
