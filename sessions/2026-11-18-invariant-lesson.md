# 2026-11-18 — ping recalls + learner-requested invariant lesson

Model: Alvar (pi).

## What happened

- 11-17 ping slots: asked sd/jitter cold re-check (oldest known node, 24d); re-asked once same day per policy. No answer that day.
- 11-18 ping slots: asked sd/invariant cold re-check (due 11-18..19 per prior boot); re-asked once.
- 11-18 learner answered both in one message:
  - **sd/jitter — recalled unaided, 25d, PARTIAL.** Got protective effect (breathing room, spread traffic); framed it as slower/uneven per-client volume; MISSED lockstep (crowd fires in synchronized waves → re-crash). Corrected in chat.
  - **sd/invariant — recognized, coached, 2d. Distinction collapsed AGAIN.** Named receipt-storage-before-send (mechanism) as the invariant, then self-flagged ("right?"). Same collapse as 11-16.
- Learner then requested a lesson on sd/invariant ("how to distinguish it and describe it to myself"). Lesson opened (thread: sd/invariant — rule vs mechanism):
  - Taught **snapshot test**: invariant = checkable from a frozen DB photo; mechanism = needs video (happens over time).
  - Taught **grammar trick**: invariants stated with never/always/every/at-most-one (about data); mechanisms with action verbs (store, send, retry).
  - Exercise set: write ONE charge-flow invariant in never/every form. Initially unanswered at the first close.
- Lesson resumed in the thread. Learner asked how data represents an invariant. Taught the correction: data does not represent the invariant; data is what the invariant constrains. Example used: charges/usage records linked by request ID, with orphan rows visible in a snapshot; receipt-before-send needs sequence/video, not just final data.
- Learner's first production attempt described the retry/keyed-receipt flow, correctly self-flagging the verbs "store" and "retry" as mechanism language. Taught the noun-first template: Every/No + stored noun + required relationship. Clarified that a state variable is data, not the invariant; the invariant is the rule about the data. Separated data (`status=PENDING`), invariant (every receipt has exactly one allowed status), and mechanism (set PENDING before sending).
- Learner asked why naming invariants matters if the mechanism exists. Taught: an unnamed goal is not auditable; the invariant gives a pass/fail corruption test, write-path coverage check, freedom to swap mechanisms, and an AI-output review question. Listed the core charge/retry invariants: pairing, uniqueness, legal state, outcome completeness, queryability, and money boundary. No universal "all invariants" list exists; invariants derive from the system's data.
- Unprompted ping re-asked the same outstanding exercise. Learner answered: "Every request ID must have one status, pending." Verdict: wrong as uniqueness; it was a status rule and incorrectly frozen at PENDING. Learner clarified he meant initial status, which was accepted as a lifecycle rule, not uniqueness.
- Taught **uniqueness** plainly: one key names at most one thing; request ID is the key. Distinguished receipt uniqueness (at most one receipt per request ID) from money-safety uniqueness (at most one COMPLETED charge per request ID). Learner correctly identified two COMPLETED charges under one request ID as the violation.
- Learner then produced both invariants correctly: receipt uniqueness and money-safety uniqueness. Coached wording change: call the first "receipt uniqueness," not "uniqueness flow invariant."
- Asked for one guarding mechanism. Learner first reached for "state manger" (state machine name faded again), incorrectly allowed multiple charges under one keyed receipt, and forgot the fail-fast race-check name. Corrected: state machine governs lifecycle; precondition = check receipt before running; guarded write = DB condition rejects loser atomically, rowcount tells loser it lost; keyed receipt + unique request ID + atomic guarded write guard money safety.
- Learner recognized "guarded write" and produced the final pair: invariant = only one transaction per request; mechanism = atomic guarded write chooses the transactional winner via rowcount. Teacher sharpened overloaded "transaction" to the stored business fact: every request ID has at most one COMPLETED charge. This completed the coached lock-in.
- Learner asked how to mark the lesson complete; told to run `/lesson end`, optionally with a summary. Then `/close` arrived.

## Evidence events

Earlier 11-18 events (already appended before this continuation):

- sd/jitter: recalled, unaided, delay 25d, partial (missing lockstep).
- sd/invariant: recognized, coached, delay 2d (distinction collapsed again).
- sd/invariant: presented, coached, UNPROBED (snapshot-test lesson).

Events appended at this close:

- sd/invariant: explained, coached, delay 0d — after coaching, produced receipt uniqueness + money-safety uniqueness and connected atomic guarded write/rowcount as the mechanism.
- sd/state-machine: recognized, coached, delay 12d — incidental evidence; said "state manger," recognized correction to state machine, lifecycle concept partial.
- sd/write-boundary: recognized, coached, delay 9d — incidental evidence; guarded-write name initially forgotten, recognized when offered, rowcount-as-loser signal correctly connected.

## Learner observations

- The rule-vs-mechanism collapse persisted on the first production attempts, but noun-first templates, the photo test, and a concrete violation example got the learner to a coached correct pair in the same session. Cold retention remains unproven; do not upgrade the unaided grade.
- "Uniqueness" itself was new vocabulary as a named invariant category; the working definition that landed was "one key names at most one thing."
- The word "transaction" overloaded DB transaction vs customer charge; use "COMPLETED charge" for the business invariant.
- State-machine name faded again ("state manger") at 12d, while rough lifecycle meaning remained recognizable.
- Guarded-write name also faded, but rowcount-winner mechanics returned after recognition.
- Learner again needed the exact `/lesson end` command at lesson completion; keep stating it plainly in wrap-ups.

## Owed recall (in order)

1. sd/invariant — cold re-check of rule-vs-mechanism distinction + charge-flow invariant ~2026-11-20.
2. sd/keyed-receipt move-3 cold re-check ~2026-11-22 (retry returns recorded result; held unaided at 1d on 11-16).
3. sd/timeout-unknown-state cold check ~2026-11-23..24.
4. sd/jitter lockstep piece re-check ~2026-11-25 (partial recall 11-18).
5. sd/state-machine name re-check can ride a later ping; name faded again incidentally on 11-18.

## Next node per routing

sd/invariant (rule 1 — cold re-check due 2026-11-20).
