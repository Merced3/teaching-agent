# Proposal (SHELVED): how learner knowledge is stored

Status: **shelved, not approved.** Written 2026-10-16 from an ops/design
conversation. Do not implement without explicit learner approval (AGENTS.md
approval boundary). Pick it up when a session is dedicated to it.

## The trigger (surface issue, already fixed)

Pi on the droplet couldn't `git commit` the knowledge base: "dubious
ownership". `/kb` is owned by host user `ops` (uid 1000) and the container
runs as root. Fixed in ops `compose.yml` with env-scoped
`safe.directory=/kb` (see ops RUNBOOK, 2026-10-16). That fixed the symptom.
The question below is about the cause.

## The underlying problem (hypothesis)

The repo mixes three kinds of data with different write patterns:

| Kind | Examples | Write pattern | Fit |
|---|---|---|---|
| Append-only evidence | `sessions/*.md`, `decision-log.md` | write once | files are fine |
| Mutable state | `current-state.md`, `data/*.json` | rewritten every session/ping | **bad fit** for a commit-per-change git flow |
| Curated theory | `thesis.md`, `routing.md`, `maps/`, `learner.md` | rare, deliberate | markdown is ideal |

Evidence:
1. Commit ceremony friction: the agent's write path goes through git, a
   process designed for human-paced, deliberate commits, ~10x/day.
2. `current-state.md`'s "Prior: ... Prior: ..." chain is a hand-rolled
   event log packed into one mutable file. Every session the LLM re-reads
   it to work out routing (what's owed, what faded, what's aging). That's
   expensive and lossy.

## Candidate direction

Borrowed from Anthropic's Scion data model (changesets in a write-ahead log
plus "derived data" computed from it), and from spaced-repetition review logs:

- **Source of truth = an append-only log of evidence events**: what
  actually happened (node, evidence level, delay, coached?, channel,
  session, quote/notes as free-form JSON so the "schema" can grow).
- **Everything else is derived and can be regenerated**: current-state,
  owed pings, fade patterns. `current-state.md` becomes a generated *view*
  that the agent still reads, not a file it hand-edits.
- **Friction goes where losing data is irreversible**: agent writes are a
  plain append (SQLite or JSONL), with no commit ceremony. Losing evidence
  is the one irreversible failure, so protect it: append-only + nightly
  backup. Git becomes a snapshot/history tool run by cron *outside* pi,
  not the write path.

## Open questions (unresolved, learner pushback)

- **Learner rejected the framing "the record predicts what you can
  remember."** Unresolved. Candidate reframe: the *record* is evidence
  (what happened); prediction is just one *derived* use of it (scheduling).
  Needs a real conversation, not an assumption.
- **FSRS** (open-source spaced-repetition model; Anki uses it): implement it,
  or copy its best parts? Leaning toward copying its review-log format and
  its stability/recall-probability idea, but not adopting cards as the unit,
  since this system's evidence levels (presented → transferred) are richer
  than right/wrong.
- Prior art to read before designing: FSRS review logs, Bayesian Knowledge
  Tracing, Knowledge Space Theory (ALEKS), xAPI / Learning Record Store.
- Meta-rule check: this counts as new machinery (a database). The two
  needs are (1) commit friction and (2) routing done by re-reading prose.
  Log it in `decision-log.md` if adopted.

## Related idea: the learner's thesis on friction

From the same conversation. Learner's revised version lives in his notes.
- Put friction where mistakes are irreversible. Where recovery is cheap and
  fast, prevent less and invest in detection and repair.
- Already in the curriculum: precondition / write-before-send (irreversible
  double charge) vs reconciliation job (repair after the fact).
