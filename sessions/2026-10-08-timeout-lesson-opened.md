# 2026-10-08 — unknown-state-after-timeout lesson OPENED (text), probe in flight

Learner message opened the recommended strand himself ("it's good that we're trying to get me to better know how other applications should work... the timeout and state that can't be observed"). He asked what the protocol should be.

EVIDENCE: unprompted, he aimed yesterday's keyed-receipt trick at the timeout problem: "store some kind of ID of receipt that it was already sent and to not send again until we confirm the user hasn't been charged, then try again." Right shape, aimed cold at a new scenario — transfer-in-progress, one hole: HOW to confirm. Also honest self-flag: "Idk I know I'm not answering this correctly."

Teacher move: affirmed the derivation, did NOT re-teach; posed the one missing probe — how do you confirm? Hint given: you wrote something durable before the call; what's in that record, and who else knows about it (points at precondition record + provider query by action ID = reconciliation).

Lesson thread opened ([lesson: start | unknown-state-after-timeout]). Learner ran /close before answering the probe.

OWED / NEXT:
- Re-open with the probe: "how do you confirm whether the charge happened? You wrote a record before the call — what's in it, and who else knows about it?" (targets: query provider by your action ID; the receipt written BEFORE send is what makes the retry safe).
- Recall pings still owed 2026-10-10..14: five-question audit Q2–Q5 + precondition/reconciliation names.
Model: Alvar (pi).
