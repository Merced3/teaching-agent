# Session: knowledge log — design + tests (no src changes) — ✅ DONE 2026-10-21

**Suggested session name:** `teaching-agent: knowledge log — design + tests`

Roadmap: `Automations/ops/session-prompts/README.md` (#5 — ticked 2026-10-21).

Copy everything below the line into the new session.

**COMPLETED 2026-10-21.** Proposal approved (status flipped in `docs/proposals/knowledge-storage.md`), decision logged (`docs/decision-log.md` "2026-10-21 — Knowledge-storage design APPROVED"), and all 4 behavioral tests approved by the learner, committed xfail in `tests/test_knowledge_log.py` (111 passed / 4 xfailed). #6's gate ("after #5's tests are approved") is now satisfied. Outcome details at the bottom of this file. The text below the line is preserved as-run.

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

---

# Outcome — 2026-10-21 — SUCCESS (design approved, 4 tests approved by the learner, committed xfail; no src changes). Instructions above untouched.

## What happened

1. **Pulled, then read the required docs in order** (AGENTS.md, the full
   proposal incl. both addenda, thesis, routing, current-state top + Prior:
   chain, decision-log, maps/software-development.md).
2. **Resolved the five open questions WITH the learner** (one at a time,
   learner picked each):
   - Q1 framing → **confirmed**: record = evidence; prediction = one derived use.
   - Q2 credit assignment → **one event per node touched** with per-node
     outcome; coached/unaided is the credit-assignment data.
   - Q3 storage → **JSONL in /kb; git leaves the agent's write path**
     (nightly cron snapshot + nightly backup).
   - Q4 write path → **CLI tool the agent calls** (`scripts/kb_append.py` is
     the only write path; the log IS a write boundary).
   - Q5 migration → **script + human review pass**; lossy spots flagged, not
     guessed.
   - Q6 meta-rule → adoption logged in `docs/decision-log.md` with the two
     needs (commit friction; routing by re-reading prose).
3. **Deliverable 1 — design written in**: `docs/proposals/knowledge-storage.md`
   status flipped SHELVED → **APPROVED 2026-10-21**, with an "Adopted design"
   addendum (data model: append-only hash-chained `kb/events.jsonl` +
   `kb/nodes.jsonl`; event types evidence/node_created/node_split/node_merge/
   claim_asserted/claim_rechecked/routing_override; project vocabulary kept —
   `presented|recognized|recalled|explained|applied|transferred`, delay as a
   separate field; stability/retrievability = internal derived machinery only;
   four invariants). Decision-log entry appended.
4. **Deliverable 2 — tests written WITH the learner's decisions encoded**:
   `tests/test_knowledge_log.py`, 4 black-box subprocess-CLI tests (append-only
   enforced via hash-chain tamper refusal; derived current-state regenerates
   byte-identically; level never upgraded past evidence incl. coached ≠
   unaided and delay required for retention; migrated Prior:-chain sample
   round-trips with gibberish flagged `unverified`). They FAIL now and are
   committed `xfail(strict=False)` — verified: **111 passed, 4 xfailed**,
   ruff clean.
5. **No src touched.** Stopped before the build (that's session #6, gated on
   the learner approving the xfail tests).
6. **Session discipline**: `docs/current-state.md` top entry written;
   committed as `06ca176`.

## For the next session (#6, the build)

- Gate first: learner approves `tests/test_knowledge_log.py`.
- Then build `scripts/kb_append.py`, `scripts/kb_derive.py`,
  `scripts/kb_migrate.py` until the 4 xfails flip to passes (remove the
  xfail marks), plus the nightly git-snapshot cron (outside pi's write path).
- Uncommitted pre-existing files (`sessions/NEXT-BOOT*.md`) were left alone.
