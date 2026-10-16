# Session: knowledge log — build

**Suggested session name:** `teaching-agent: knowledge log — build`

**Gate:** session #5 produced an APPROVED design
(`docs/proposals/knowledge-storage.md`) and learner-approved tests in
`tests/` (currently xfail/skipped). Roadmap: `Automations/ops/session-prompts/README.md` (#6).

Copy everything below the line into the new session.

---

# Implement the approved knowledge event log until the approved tests pass, migrate the history, cut the agent over

**Read first:** `AGENTS.md`, `docs/proposals/knowledge-storage.md`
(approved design), the approved tests, `docs/decision-log.md`,
`src/teaching_agent/` (especially `pi_rpc.py`, `engine.py`,
`sessions.py`, and the write-boundary extension), and the ops
`RUNBOOK.md` (deploys are automatic on merge to main; the agent runs on
the droplet). **Pull first.**

## Rules

- The approved tests are the spec. Un-skip them one at a time. If a test
  seems wrong, STOP and ask; don't edit an approved test silently.
- Work on a branch and open a PR with an intent section. This touches
  the KB write path (a core constraint), so the learner merges.
- Never lose evidence: migrate into the log, verify, and keep the
  markdown history files untouched as the archive.

## Order

1. Event log + append API (the write boundary) + derived-view
   regeneration. Approved tests go green.
2. Migration script over the "Prior:" chain + session logs. The learner
   reviews flagged lossy spots.
3. Cut over: pi records evidence through the new path; `current-state.md`
   becomes a generated view (header says GENERATED, don't hand-edit).
   Update `docs/session-handoff.md` + `AGENTS.md` session-discipline
   wording ONLY with explicit learner approval (spine rule).
4. Merge → deploy → watch one real ping + one `/close` on the server.
5. Decision-log entry: what changed, evidence, verdict.

## Success =

All approved tests green; history migrated with zero silent loss; one
real ping and one real close recorded through the event log on the
droplet; the agent no longer hand-edits current-state. Tick #6 in the
roadmap.
