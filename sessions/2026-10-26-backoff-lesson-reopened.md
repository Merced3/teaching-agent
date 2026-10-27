# 2026-10-26 — backoff lesson reopened, Q1 posed unanswered

Model: Alvar (pi).

## What happened
- Unprompted ping re-verified sd/atomicity: learner recalled unaided at 5 days (atomic unit = state changes + receipts, boundary before the point of no return). Event logged.
- Learner ran /progress; summary given. Backoff flagged as the one soft spot (10-25 partial: jitter desynchronizes correct, backoff's depressurization job missed).
- Learner explicitly requested a backoff lesson: "I just need reps." Lesson opened (thread: backoff — depressurization reps).
- Probe Q1 posed with numbers: sick provider handles 100 rps, 1,000 clients each retrying on a FIXED 5s timer forever — what's the total incoming rate at start and one minute later; has the load changed? UNANSWERED at /close.

## Evidence
- sd/atomicity: recalled unaided, delay 5d (event appended 2026-10-26).
- No new backoff evidence — question posed, no answer. Do not record presented/recalled.

## Owed / next
- Next session re-opens with the same Q1 (fixed-timer rate arithmetic), then contrast with multiplying timer so the depressurization insight is derived, not told. Learner asked for reps — keep it numeric and short.
- Backoff delayed re-check still owed after lesson completes (~3-7 days after).
- Next node per routing: sd/backoff (rule 2 — oldest weak evidence: 10-25 PARTIAL; learner-requested lesson overrides sequence, recorded as data).

## Model
Alvar (pi).
