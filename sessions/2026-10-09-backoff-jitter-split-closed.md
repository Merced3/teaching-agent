# 2026-10-09 — backoff/jitter split CLOSED (voice, lesson thread "backoff vs jitter")

Third session of the day, voice, inside the open lesson thread. NEXT-BOOT re-opened the unanswered probe; lesson brief had been posted as thread opener earlier (presented-only, see 2026-10-09-backoff-jitter-brief-close.md).

## What happened

1. **Probe answered (the one left open 10-08):** "50k failed payments, everyone retries with plain exponential backoff 2s/4s/8s — why does the provider still get slammed, what's the extra ingredient?" Learner: even with exponential backoff, the same crowd crams in at every backoff interval; jitter (random addition) spreads the load. EVIDENCE: lockstep problem + jitter's role explained UNAIDED, 1 day after the PARTIAL two-piece check.
2. **Learner self-initiated the harder question:** "I'm gonna try and push on why both may be needed just to see if I understand it correct." First attempt PARTIAL: backoff gives the real break time (right); jitter "gives even more break time, but spreads the load" (half wrong — jitter does NOT add wait time on average, same wait scattered). One coached correction given: backoff = how long, jitter = how synchronized.
3. **Split restated in own words:** "backoff handles how long, jitter handles how synchronized" — confirmed sits right. EVIDENCE: explained, same-day, one coached fix. Split CLOSED at explained level; NOT yet retention — cold re-ping owed.
4. Milestone posted to thread. Learner told: strand basically closed, cold ping coming later this week, next move is his (pick next edge strand or /lesson end). Lesson thread still OPEN at close — learner did not run /lesson end.

## Operational note

Voice STT fragmented badly mid-session ("is because", "x back off is", "exponential gap of is what") — three partial turns in a row; recovered after suggesting slow re-say or text, and a later "test one two three" came through clean. No action taken; if it recurs, check the hub stream before assuming learner-side mic.

## Evidence summary

- Thundering-herd lockstep-under-plain-backoff: explained unaided (1 day after presented/fuzzy).
- Backoff-vs-jitter division of labor: explained with one coached fix, same-day.
- Owed cold pings 2026-10-10..14 (unchanged list + backoff/jitter split cold re-ping now confirmed in it): five-question audit; precondition + reconciliation-job names; provider-lookup-by-request-ID; muddy post-debate outcomes; jitter's purpose + backoff-vs-jitter split.

Model: Alvar (pi).
