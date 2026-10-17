# 2026-10-17 — rule-2 ping: state-machine name (3 exchanges)

Unprompted ping (routing rule 2: aging `known` nodes; rule 1 had nothing due — Q5 receipt-half window opens 2026-10-19).

**Ping:** payment flow has states like PENDING, COMPLETE, FAILED — what's the name of the thing listing the allowed states and legal moves?

**Exchange 1 — learner:** "that is called a state machine, and the legal moves between them are the crash windows... each of those 'steps'... are the durable steps."
- NAME recalled UNAIDED ~2 days after the 10-15 fade ('state manager'), after 2 prior name fades — RETENTION WIN.
- CONFLATION: crash windows ≠ transitions; states ≠ durable steps. Corrected plainly: moves = transitions; crash window = gap between two durable steps where a crash leaves the outcome unknown; durable steps = the moments something got permanently recorded.
- Mini-check posed: name one transition and one crash window in the payment flow.

**Exchange 2 — learner:** "I know of the transition to open and closing, but I don't know of a specific crash window."
- Transition named correctly (OPEN→CLOSING, pulled from the session-registry machine — accepted, same idea).
- Crash window in the payment flow: FADED at ~11 days since the 10-06 retention win. Re-presented: after the charge request leaves for the provider / before the result is recorded — unweldable, only survivable via write-PENDING-before-send (request ID exists so the provider can be asked afterward).

**Exchange 3 — learner:** "that's where the *reconciliation job* kicks in."
- SELF-CONNECTION unaided: reconciliation-job name recalled ~4 days after the 10-13 win AND linked cross-node to the crash window — RETENTION WIN. Confirmed: the job takes the request ID off the PENDING record and asks the provider what happened.

**Evidence summary:** state-machine name = recalled unaided ~2d (win); reconciliation-job name + crash-window link = recalled unaided ~4d (win); crash-window location in payment flow = faded at ~11d, re-presented (recognized only).

**Owed:** Q5 receipt-half re-ping ~2026-10-19..20 (fold in crash-window re-probe); full five-question audit re-ping ~2026-10-22..23 (learner standing request).

**Next node per routing:** owed recall pings (rule 1) — Q5 receipt half ~2026-10-19..20.

Model: Alvar (pi).
