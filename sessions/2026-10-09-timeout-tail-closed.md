# 2026-10-09 — unknown-state-after-timeout: the tail (lesson closed)

Thread: "unknown state after timeout — the tail". Lesson self-requested by learner (saw the owed fuzz point, said "do I remember — I don't. Let's ingrain it").

## Evidence events

1. **Reconciliation mechanism recalled unaided, ~1 day** (from 2026-10-08 restatement): request ID rides with the call, job queries provider by it. Holds.
2. **Three-outcome probe (first attempt, mixed):** went-through branch correct unaided (record result, skip on retry). Never-happened branch roughly right (retry the action) but unsharpened. Unknown branch MISSING — learner re-explained the *query mechanism* instead of handling the unknown answer; drift corrected by coach question ("is it safe to retry?").
3. **Unknown branch derived with coaching:** retry unsafe (double-charge risk) — learner answered the coached question correctly.
4. **Pending-forever problem:** learner stuck ("what do I do in its place?") — TAUGHT: bounded re-asking on delay, human escalation at limit; user sees honest "confirming your payment," not a spinner lie. Presented.
5. **Full restatement (learner-written, ~15 min):** branch 1 correct; branch 2 WRONG (put confirmed-never-happened on a "check later" list instead of retrying now); branch 3 correct (pending + bounded re-ask + human escalation). One coach prompt → learner self-corrected branch 2 UNAIDED ("ohhh branch 2 is retry safe because the provider told us it didn't go through") and stated the principle: retry-safety comes from knowing the real state of the world.
6. **Final sharpening given (presented):** reconciliation job is the star of branch 3, not absent — safe to repeat a QUESTION when unsure, only safe to repeat an ACTION when sure.

## Level

Mechanism: recalled unaided at ~1 day. Three-outcome tail: explained, same-day, with coaching on the unknown branch and one self-correction on never-happened. NOT retention — cold re-probe owed.

## Owed

- Cold re-probe of the three-outcome tail in the 2026-10-10..14 window (folds into existing cold pings). This re-probe is also the current routing item (the unanswered probe is now answered).
- Learner noted this was their first text-based lesson (previously voice-only).

Model: Alvar (pi).
