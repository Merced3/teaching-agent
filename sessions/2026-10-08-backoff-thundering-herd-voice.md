# 2026-10-08 — backoff & thundering herd (voice lesson, taught)

Lesson opened earlier same day (sessions/2026-10-08-backoff-lesson-opened.md), Q1 posed in text; this voice session carried it through. Learner was driving partway through — STT garbling and one voluntary pause; close suggested by agent, accepted.

## Evidence events

- **Thundering herd intuition: DERIVED.** Q: 50k valid retries land the same second on a just-recovered provider — what happens? Learner: "it crashed... I don't know how I would protect myself" — derived unaided that the retry wave re-kills the provider. Named for him: thundering herd. Note: learner first reached for the keyed receipt (wrong problem — that's double-charge, not load); corrected the aim, not counted as a fade (he was pattern-matching to last lesson, reasonable).
- **"Exponential backoff" term surfaced by learner** — but when probed for the mechanism he guessed wrong (retry immediately, fail immediately). Term was recognized, mechanism was NOT known. Do not record the term as recalled.
- **Backoff mechanism: DERIVED with one human hint** ("counter says come back") → "wait 5 seconds, then 10, then 15" — the wait-longer-each-time idea produced unaided after the hint. Sharpened: multiplicative growth (5/10/20/40) = the exponential part.
- **Herd-persists-under-uniform-backoff: presented.** Learner stuck ("I have no clue") when asked how to break up a wave where everyone waits the same 5s. Jitter PRESENTED plainly (random extra per caller smears the wave into a trickle), then re-explained once on request ("that's a lot simpler than I thought" = recognized). Owed: cold re-probe of jitter's purpose.
- **Closing two-piece check: PARTIAL.** Learner named the herd + "all at once" but couldn't cleanly separate backoff's job vs jitter's job. Re-presented: backoff gives the provider time; jitter spreads the crowd.

## Evidence level summary

Thundering-herd effect: derived unaided (applied-grade intuition, no delay yet). Backoff mechanism: derived with hint. Jitter: presented + recognized. No delayed recall yet — nothing counts as retained.

## Owed

- Cold re-probe (fold into 2026-10-10..14 pings): what is jitter for / why does the random part matter; two-piece split (backoff vs jitter).
- Previously owed unchanged: five-question audit, precondition + reconciliation-job names, provider-lookup-by-request-ID, post-debate outcomes question (provider has record → never resend / no record → safe retry).

## Next session

Re-open with the cold jitter probe if pings haven't run; otherwise continue lesson thread if learner wants more (e.g., tight-loop costs from the same map node, or cap on backoff).

Model: Alvar (pi).
