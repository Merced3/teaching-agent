# 2026-11-05 — keyed-receipt blank-page rep (1 day after rebuild lecture)

## The rep (learner's four moves, unaided)

1. Save the receipt before the send.
2. Send the API call.
3. Save the request ID (if provided).
4. Present the state of the world (order completed) to the customer/user.

## Grade: recalled (partial), unaided, delay 1d

- WON: move 1 — receipt-before-send timing. This is exactly the detail that failed in the 11-04 cold playback; the lecture rebuilt it and it survived a day. Real progress.
- GAP A (biggest): no check-the-store move. The handler never looks anything up on arrival — so a retry would sail straight through moves 1–2 and re-execute. The whole dedup entry point is missing.
- GAP B: keying inverted. Learner saves the request ID after the send, and treats it as optional ("if provided"). In the pattern the ID is caller-supplied, mandatory, and it is the lookup key — the receipt is written under it.
- GAP C: move 4 is about showing the user the outcome, not about the retry. The pattern's fourth move is: retry arrives → receipt found → return the recorded result without re-executing.

## Teaching move

Credited the timing win, then probed the biggest gap socratically rather than correcting: "your four moves describe the first attempt — what happens when the retry arrives?"

## Evidence appended

- sd/keyed-receipt — recalled, delay 1d, unaided, 2026-11-05 (partial detail in notes).

## Owed queue (unchanged)

- sd/purpose-of-tests retention re-probe due 11-06..09 (tripwire semantics + coverage judgment).
- sd/timeout-unknown-state re-check due 11-07..10 (executed-vs-pending).

Model: Alvar (pi).
