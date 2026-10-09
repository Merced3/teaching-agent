# Session Handoff

> **Why this file exists (provenance, 2026-08-26; noted 2026-10-07):** it predates
> the runtime. In the manual era this project was only markdown — the learner
> pasted the prompt below into a fresh pi session by hand to carry context
> between lessons (originally anchored on the socratic-partner codebase). The
> prompt survives because the *runtime* also builds pi's system prompt from
> this file. If you are a future session wondering whether some section still
> earns its place: check whether its premise ("a human pastes this") is still
> true before keeping it. Every doc except the spine is a current best theory.

## Opening a new session — paste this

```text
We are working on my personal learning system in:

<absolute path to this folder>

Before teaching, planning, or changing anything:

1. Read AGENTS.md completely — especially the spine, the meta-rule, and the evidence rules.
2. Read docs/thesis.md, docs/learner.md, docs/current-state.md, docs/decision-log.md,
   docs/goal.md (what the learner is shooting for), and docs/routing.md (how the next
   node is computed).
3. Check for any maps/ or sessions/ folders and read the most recent files.
4. Summarize back to me: the purpose, the loop, my current known state, and the next milestone — in under 10 sentences. If anything conflicts or is stale, say so.

Then:

- If I asked to learn something: probe first. Do not teach from assumption.
- If I asked to change the system: present a plan and STOP for approval.

Today's goal: <one sentence>
```

## Closing a session — the agent must do this

1. Update `docs/current-state.md`: what was taught, what was demonstrated (unaided vs. coached), what's next, and which model(s) were used (files must not mislabel the model).
2. Update `docs/learner.md` if anything true was learned about this mind — with status (`confirmed` / `observed` / `hypothesis`) and evidence.
3. Append any experiments or approach changes to `docs/decision-log.md`.
4. If any taught claim is time-sensitive, note its `current as of` date.
5. Record the next delayed-recall check that is owed, and when.
5b. State the **next node per docs/routing.md** ("next node per routing: <node> —
   <which rule fired>"). A close that ends on "learner picks" is drift; the only
   exception is an explicit learner override, which is recorded as data.
6. Write `sessions/NEXT-BOOT.md` (≤10 lines, consumed once): current date, one-line learner state, owed recall checks with due dates, active lesson/thread if any, next milestone. The next fresh session reads this FIRST (before current-state.md) — the recall-check queue is the easiest thing to drop between sessions and pedagogically the most important. After it is read, the file is renamed/deleted so it cannot be consumed twice.
7. Leave the folder resumable by a different model with zero access to this conversation.

## Date awareness (learner rule, 2026-09-16)

At every session start — and always when the learner says "it's been a while" — get the real current date (run `date`) and compute elapsed time since the last session before trusting `current-state.md`. Delay length changes what recall results mean; record evidence as level + elapsed time.

## Conventions

- Paragraphs in `maps/`, `sessions/`, and `docs/current-state.md` are stored as single
  unwrapped lines — robust for the exact-match scripted edits agents use. Wrapped prose is
  human-nicer; check file form before scripted edits either way.
- The handoff prompt omits a `Model:` line on purpose; fill it at close with the actual
  model(s).
- Lecture episodes (`/lecture`) are recorded in `docs/current-state.md` as
  `episode generated (<date>), UNPROBED` plus one line on what it covers, the moment they
  are generated. Listening is `presented` — nothing more. An episode stays UNPROBED until a
  recall check probes its content; then record the result as level + elapsed time and drop
  the UNPROBED mark.

## Drift test

A session has "drifted" if it: teaches without probing when no fresh map exists, claims retention without evidence, adds machinery without a second demonstrated need, or rewrites old decisions without logging them. If you notice drift, stop and say so.
