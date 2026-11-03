# 2026-11-02 — Lesson: what tests buy (sd/purpose-of-tests)

Model: Alvar (pi). Channel: Discord lesson thread "what tests buy", text.

## Context

Routing rule 3 (highest unblock-count edge cluster): Correctness & testing strand, R4-Q1 edge since the original probe — learner had a strong AI-authorization frame but muddy on regression-vs-correctness. Opening probe: "when the teaching-agent suite goes green, what has it actually bought you?"

## What happened

1. Initial answer: green = the simulated slice of the world passed; real-world tail events unaccountable; right tests buy generality, iterate when edge cases hit; suspected suite is overfit; honestly said "I don't know how to answer specifically." Tripwire metaphor initially confused him ("used to work" phrasing).
2. Re-explained tripwire: a test freezes a behavior that held when written; failure = a pinned behavior *moved*; green = no pinned behavior moved, not correctness. His "iterate on edge cases" was mapped onto the accumulate-one-wire-per-scar loop. He got it cleanly.
3. He then extended the metaphor unaided: red bar = an *inflection point* — an alert that a change happened and a human must judge whether it's an accident (regression) or a deliberate rules-of-the-game change (test now wrong, needs rewrite). Suite can't tell the two apart; the human is the evaluation.
4. He anchored it himself to Grove's *Only the Paranoid Survive* ("that analogy will help it stick"). Logged in learner.md.
5. Final synthesis probe (green after an AI rewrite — what does it tell you, what can't it): he answered green = no inflection point, the static worldview holds until a test fails; what tests don't buy = "the judgement of what I should have, when" — i.e., coverage judgment, which behaviors deserve wires. Also generalized the authorization frame beyond AI-written code unprompted.

## Evidence

- sd/purpose-of-tests — explained (unaided), delay_days 0. Appended to kb/events.jsonl; current-state regenerated. Retention re-probe owed ~2026-11-06..09 (tripwire semantics + coverage judgment).

## Open threads

- Follow-up lesson offered, learner's call: given coverage judgment is the scarce resource, how do you decide which behaviors deserve wires (in teaching-agent)? Natural next node in the strand; sibling edges: sd/mock-assumptions (R4-Q2), sd/fake-nondeterminism (R4-Q3).
- Owed from before: sd/keyed-receipt cold playback (asked 11-01, unanswered, window to 11-05); sd/timeout-unknown-state retention re-probe ~11-07..10 (executed-vs-pending distinction).
- Derive grading gaps still open (needs code session, not teacher-fixable).
