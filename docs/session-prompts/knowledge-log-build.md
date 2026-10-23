# Session: knowledge log — build — ✅ DONE 2026-10-23 (merged, deployed, live-verified: real close + real ping through the event log; roadmap #6 ticked)

**Suggested session name:** `teaching-agent: knowledge log — build`

**Gate:** session #5 produced an APPROVED design
(`docs/proposals/knowledge-storage.md`) and learner-approved tests in
`tests/` (currently xfail/skipped). Roadmap: `Automations/ops/session-prompts/README.md` (#6).

Copy everything below the line into the new session.

**STATUS 2026-10-23.** Steps 1–3 done on branch `knowledge-log-build`, PR #1 open
(learner merges — KB write path): `scripts/kb_append.py` (write boundary),
`scripts/kb_derive.py`, `scripts/kb_migrate.py` built; the 4 approved tests
un-xfailed and green (115 passed, ruff clean, approved test bodies untouched);
real Prior-chain migration run — 3 confident events + 40 flags in
`kb/events.jsonl` awaiting learner review; cutover DONE with explicit learner
approval (AGENTS.md + session-handoff.md wording, current-state.md now the
GENERATED view, prose archived in docs/archive/); decision-log entry written.
MERGED + DEPLOYED + LIVE-VERIFIED 2026-10-23: PR #1 (squash `0a13f6d`) + cutover-fix
PR #5 (squash `9c4a97f`) merged; nightly `kb-snapshot.sh` cron installed (03:20,
kb-push ships it); real `/close` recorded events 44–50 and a real answered ping
recorded event 51 (`sd/reconciliation-job`, recalled unaided, 4 days) through
`kb_append.py` on the droplet; `current-state.md` is GENERATED. Roadmap #6
TICKED. Still owed (follow-ups, not gates): learner review of the 40 migration
flags. Outcome details at the bottom of this file. The text below the line is
preserved as-run.

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

---

## Outcome (2026-10-23, build session)

1. **Step 1 (event log + append API + derived views) — DONE.**
   `scripts/kb_lib.py` (schema, canonical JSON, sha256 hash chain, append),
   `scripts/kb_append.py` (the ONLY write path: validates + verifies the chain
   on every write; tamper → nonzero exit, log untouched), `scripts/kb_derive.py`
   (`grades` JSON + `current-state` markdown, deterministic, `kb/derived/`
   disposable + gitignored). Grading enforces never-upgrade-past-evidence:
   coached ≠ unaided, retention requires `delay_days > 0`.
2. **Approved tests un-xfailed one at a time — all 4 green** (they XPASSed on
   the first run, then the xfail marks were removed). Test bodies NOT edited —
   only the xfail mark and the stale "nothing is implemented yet" docstring
   line. Full suite: **115 passed / 0 xfailed**, ruff clean.
3. **Step 2 (migration) — DONE as candidate, review owed.** `scripts/kb_migrate.py`
   over the real `docs/current-state.md` Prior chain: **3 confident evidence
   events + 40 migration flags** (`unverified: true`), committed as
   `kb/events.jsonl`. The flags are mostly multi-node entries needing the human
   credit-assignment split (one event per node touched) — as the design
   predicted. Markdown history untouched (stays the archive).
4. **Step 3 (cutover) — DONE 2026-10-23 with explicit learner approval (spine rule
   satisfied).** `AGENTS.md` session discipline rewritten (evidence = events via
   `kb_append.py`; current-state = generated view, never hand-edited);
   `docs/session-handoff.md` open/close + conventions updated (UNPROBED episodes
   now `presented` events); prose current-state archived untouched at
   `docs/archive/current-state-2026-10-23.md`; `docs/current-state.md` is now
   GENERATED. 115 passed, ruff clean.
5. **Step 4 (merge/deploy/watch) — DONE 2026-10-23.** PR #1 merged (squash
   `0a13f6d`); droplet OOMed during build (1 GB warning), power-cycled, recovered;
   live-agent uncommitted state snapshotted + merged with zero loss. First live
   `/close` exposed stale engine prompts + extension blocking the kb CLIs →
   cutover-fix PR #5 (squash `9c4a97f`). Nightly `kb-snapshot.sh` cron installed
   (03:20; `kb-push.sh` ships it). SECOND live `/close`: events 44–50 appended
   via `kb_append.py`, view regenerated, no git ceremony. Live answered ping:
   event 51 (`sd/reconciliation-job`, recalled unaided, delay 4d). SUCCESS BAR MET.
6. **Step 5 (decision log) — DONE.** `docs/decision-log.md` "2026-10-23 —
   Knowledge log BUILT", verdict PENDING learner.
7. **Roadmap #6 TICKED 2026-10-23** — full success bar met (tests green, history
   migrated with zero silent loss, real close + real ping through the event log,
   agent no longer hand-edits current-state).
8. Pre-existing uncommitted files (`sessions/NEXT-BOOT*.md`) resolved: droplet is
   the live KB (cron commits nightly); the local duplicate NEXT-BOOT copy was
   verified identical (CRLF/LF only) and deleted — do not commit such residue.
