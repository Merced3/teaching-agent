# 2026-10-28 — re-verification pings + keyed-receipt retention failure, lesson opened

Model: Alvar (pi). Channel: Discord unprompted pings, then learner-initiated lesson.

## What happened

- 10-27 (prior day, same boot cycle): sd/reconciliation-job re-verified cold via ping — explained, unaided, 4-day delay. Full bounded loop described (poll by request ID, surface state, unknown ID = safe retry, human escalation).
- 10-27: sd/thundering-herd probe asked; learner answered 10-28 — flood re-crashes provider, cited rate limits. Explained, unaided, 4-day delay. Sharpened in reply: rate limits are the provider's shield; the herd is *valid* retries; client-side fix is backoff+jitter.
- 10-28: sd/idempotency probe (5 retries, same key) answered same day — one charge, later retries skip re-execution, recorded state returned, DB as source of truth. Explained, unaided, 4-day delay. When the keyed-receipt mechanism was named in the reply, learner self-reported: remembers the name, forgot the mechanism. Logged as RETENTION FAILURE (recognized, 5-day delay) on sd/keyed-receipt — contradicts its transferred/retention-win grade; node is now stale despite 25 events.
- Learner accepted a rebuild lesson on the spot ("yeah, sure, do it"). Lesson thread opened (keyed-receipt rebuild); first reconstruction probe asked (walk through the charge endpoint step by step, no hints). /close arrived before the learner answered — probe still outstanding in the thread.

## Evidence events appended (this boot cycle)

- sd/reconciliation-job — explained, unaided, delay 4 (2026-10-27)
- sd/thundering-herd — explained, unaided, delay 4 (2026-10-28)
- sd/idempotency — explained, unaided, delay 4 (2026-10-28)
- sd/keyed-receipt — recognized, unaided, delay 5, RETENTION FAILURE self-reported (2026-10-28)

## Notes for next session

- Active lesson: keyed-receipt rebuild — resume with the outstanding probe (charge endpoint walkthrough) unless the learner already answered in-thread.
- Owed: sd/backoff delayed re-check, due 2026-10-29 to 11-02 (fixed-timer 200 rps vs doubling 12.5 rps + why backoff protects a recovering dependency). Lesson takes precedence if learner is in it.
- After the rebuild lesson closes: re-probe keyed-receipt cold in 3–7 days (~2026-11-01 to 11-05).
- FLAG: derive still shows sd/reconciliation-job "no delayed evidence" despite the 10-27 delayed event — possible derive rule gap (may require delay at the graded level). Cannot inspect/fix code from teacher seat; describe to learner or a code session.
- Learner.md updated: self-reported fades are trustworthy, immediate (observed, 2026-10-28).

## Next node per routing

sd/keyed-receipt (active lesson — learner override honored and recorded), then sd/backoff re-check (rule 1, due 10-29).
