# 2026-10-06 — Voice drill reps: unknown-state-after-timeout

Model: Alvar (pi). Modality: live voice, learner-led ("reps of software dev stuff, you lead me").

## What happened

No fresh map edge was planned; learner asked for open drill reps and the agent led a back-and-forth on the map edge node **unknown-state-after-timeout**, via two scenarios: (1) webhook → DB write → external API call, crashable anywhere; (2) payment charge API with no idempotency key and no status endpoint, timeout after send.

## Evidence events

- **Retained (unaided, same-day):** the 2026-10-06 sharpening "durable STEPS, not states" — learner self-corrected with it unprompted ("which is something I got wrong last time").
- **Applied unaided:** unweldable-outside-world — "once it's sent out... we don't know what's gonna happen," used to reason about why duplication can't be freely chosen.
- **Explained/applied:** chose fail-loudly + honest "timed out, status unknown" UX over guessing success/failure; stated the invariant unprompted — "the thing we don't do at all costs is double charge the user." Invariant-as-rule (node 3) is holding.
- **Recognized after probe:** keyed receipt's role when the API confirms execution (record the confirmation, retry returns it); also surfaced idempotency-key-sent-with-request as the better option (agent sharpening).
- **FUZZ POINT (corrected):** asked what saves a crash *after send, before any record exists*, learner answered "the keyed receipt" — but no receipt exists in that window. Corrected: the write-"attempting"-BEFORE-send record is what saves the refresh-retry; the gap between the outside call and your own record is an unweldable crash window. New watch item: **the keyed receipt's precondition (the receipt must exist first)** — classic lookup-detail fade risk per the established pattern.

## Owed recall checks (next)

1. Probe the receipt-precondition point cold: "crash after the charge went out, before your DB write — customer hits retry. What saves you?" (target: write-before-send, not keyed receipt).
2. Consolidation lecture episode (`lessons/state-invariants-crashes-consolidation/lecture.md`) still UNPROBED — probe when some delay has passed (generated 2026-10-06).
3. Earlier lecture episodes (crash-window, invariant/write-boundary, keyed-receipt) — partially probed via this session's drill (unweldable insight, invariant usage held); keyed-receipt episode's core point (receipt stores the RESULT) not directly probed today.

## Session notes

- One mid-session derail: learner had a stray unrecorded voice thread; resolved without cost.
- Learner ended the drill cleanly ("let's call it done"); agent summarized and logged.
- Verdict-first habit maintained throughout (each turn opened with right/wrong before sharpening).
