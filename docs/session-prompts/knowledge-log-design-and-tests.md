# Session: knowledge log — design + tests (no src changes)

**Suggested session name:** `teaching-agent: knowledge log — design + tests`

Roadmap: `Automations/ops/session-prompts/README.md` (#5).

Copy everything below the line into the new session.

---

# Turn the shelved knowledge-storage proposal into an approved design and an approved test suite. Do NOT touch src.

**Read first, in order:** `AGENTS.md` (spine, meta-rule, approval
boundary), `docs/proposals/knowledge-storage.md` (**the whole thing,
including both 2026-10-16 addenda.** This session exists because of it),
`docs/thesis.md`, `docs/routing.md`, `docs/current-state.md` (top entry
+ skim the "Prior:" chain; that chain is the raw material),
`docs/decision-log.md`, `maps/software-development.md`. **Pull first.**

## Decisions already made by the learner (don't reopen without cause)

- Source of truth = append-only evidence events (changeset-style).
  Everything else (current-state, owed pings, fades) is derived and can
  be regenerated.
- Storage must be **project-agnostic**: nodes + explicit edges + events
  as plain data, so a future UI (e.g. a public "star-system" graph
  viewer) can read it without redesign. Any UI is a replaceable viewer.
- **No vocabulary renaming.** The project's own terms stay. Stability /
  retrievability are internal derived machinery only.
- Math SUGGESTS when (the ~90% retrievability idea); the LLM keeps the
  what + override.
- Nodes are cheap, many, rewritable; split when errors reveal a hidden
  sub-skill, merge when a node never changes a decision (KC-granularity
  literature, in the proposal).

## Open questions to resolve WITH the learner

1. The learner rejected "the record predicts what you remember." The
   working reframe is "record = evidence; prediction = one derived use."
   Confirm or replace it.
2. Credit assignment: one probe answer often touches several nodes. How
   does an event attribute blame? Candidates: one event per node touched
   with per-node outcome; probe design that isolates one node.
3. Storage tech: SQLite vs JSONL. Where it lives (`/kb` is a git repo
   the agent commits to; `/app/data` is backed up nightly). Does git
   leave the agent's write path (nightly snapshot instead)?
4. How pi writes events: a tool/CLI the agent calls, vs pi editing a
   file. The repo already has a write-boundary extension; the event log
   should BE a write boundary (the invariant is enforced on every write
   path, which the learner was taught).
5. Migration: parse the existing "Prior:" chain + session logs into
   events (script + human review pass). Lossy spots get flagged, not
   guessed.
6. Meta-rule: log the adoption in `docs/decision-log.md` with the two
   needs (commit friction; routing done by re-reading prose).

## Deliverables

1. Design written into the proposal doc (status → APPROVED, or revised),
   decision-log entry.
2. **Tests written WITH the learner**: few, behavior-level, black-box
   (house style: `tests/` tests the boundary, not internals). At minimum:
   append-only is enforced; derived current-state regenerates
   identically from the log; an evidence level is never upgraded past
   its evidence; a migrated sample round-trips. The tests should FAIL
   now (nothing is implemented). Commit them marked xfail/skipped so
   CI stays green.
3. STOP. The build is session #6, after the learner approves the tests.
