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

## Addendum 2026-10-16 (design conversation, continued)

### Vocabulary, in plain terms (from FSRS)

- **Retrievability**: the chance the learner could recall node X right now.
  Starts at 100% when learned, drains over time (forgetting curve).
- **Stability**: how slowly it drains. Grows with each successful DELAYED
  recall (the 6-week atomicity win made that memory's hole smaller), shrinks
  on a fade. In the event-log design this is a **derived** field: recomputed
  from the node's events, never hand-written. If it were stored directly it
  would go stale the moment a new event arrived — this is why the event log
  is the only thing that must be protected; every number is rebuildable.
- **The 90% rule**: schedule a re-verification when retrievability is
  predicted to hit ~90%. Ping at 99% = free pass, strengthens nothing,
  wastes a ping. Ping at ~0% = re-teach from zero, expensive. ~90% is the
  cheapest strengthening point. Today the LLM picks windows by feel in prose
  ("re-ping ~Oct 19-20"); the proposal is that stability math SUGGESTS the
  when, the LLM keeps the what and the override.

### Why FSRS and this system schedule differently

FSRS's constraint: millions of users, zero semantic input (one button press
per card). Pure math is its best possible scheduler. This system's
constraint: ONE learner, an LLM already reading the whole history. Judgment
beats math when you can afford it: the agent picks WHAT to probe (fuzz
points, cross-node links, mnemonic reps after repeat fades), not just WHEN.
Trade-off: LLM judgment is inconsistent; math is consistent but shallow.

### Learner idea (2026-10-16): discipline-agnostic nodes

Nodes shouldn't know what discipline they hold. A generic record —
`{ id, statement, prerequisite edges, evidence events }` — so ONE structure
grows trees for any subject, and the map becomes data instead of prose.
Close prior art: Knowledge Space Theory (ALEKS): items + prerequisite
relations, discipline-agnostic.

**The hard part (why the wording felt off): node identity.** What counts as
ONE node is a judgment call no algorithm escapes ("keyed receipt": one node
or five? "backoff/jitter split": a node or an edge?). Design answer: nodes
are cheap, many, and rewritable. The agent PROPOSES nodes and edges from
session evidence; the map stays a "current best theory" (AGENTS.md), never
authoritative. This is the actual open problem in learner modeling, not a
mistake in the idea.

## Addendum 2 (2026-10-16): learner decisions + homework results

### Learner decisions

1. **Storage must be project-agnostic.** The knowledge record should outlive
   and out-travel this project — e.g. it should be able to feed a public
   "star-system" visualization (nodes as stars, subjects as systems,
   cross-subject links) without redesign. Constraint on the design: the
   record is data + explicit edges; any UI is a replaceable viewer.
2. **No vocabulary renaming.** The project's existing terms (evidence
   levels, fades, retention win, edge node, owed pings) stay. FSRS terms
   (stability, retrievability) are INTERNAL machinery — derived fields an
   implementation may compute, never words the learner or docs must adopt.

### Homework: how do graph-visualization apps store their data?

- **Obsidian**: plain markdown files are the source of truth; `[[links]]`
  live inside the text. A metadata cache (IndexedDB) is DERIVED from the
  files and powers the graph view. Its Canvas feature = a JSON file with
  `nodes` and `edges` arrays. (obsidian.md/help/data-storage)
- **org-roam / Arcology**: org files parsed into SQLite tables —
  `nodes(id, title, ...)`, `links(from_node, to_node, type)` — again:
  files as truth, DB as a queryable derived index.
- **Pattern**: the "Jarvis star-map" UI is ALWAYS a derived view over a
  simple nodes+edges structure. Nobody stores the visualization. Force-
  directed graph UIs just read nodes/edges JSON. This validates the
  proposal's shape: nodes + edges + events as data, UIs and views as
  replaceable projections.

### Homework: has anyone worked on "what counts as one node"?

Yes — it's a named, unsolved research problem: **knowledge-component (KC)
granularity**.
- KLI framework (Koedinger, Corbett, Perfetti 2012): a KC is "an acquired
  unit of cognitive function inferred from performance on a set of related
  tasks." KCs form hierarchies; granularity is a deliberate choice.
- The trade-off is documented (Pelanek 2020; JEDM 2026 language-tutoring
  study): finer KCs = more precise model but more maintenance, less data
  per KC, noisier estimates; mid-level "semantically grounded" KCs
  generalize best to new content. Best granularity depends on the goal —
  there is no universal answer.
- Multiple skills per task => the "credit assignment problem" (if the
  learner fails, which KC is to blame?). Relevant to us: one probe answer
  often touches several nodes; our coached/unaided + level annotations are
  our credit-assignment data.
- Practical guidance from the literature matches our instinct: start
  coarse, SPLIT a node when errors show a hidden sub-skill (SimStudent
  does exactly this automatically), MERGE when a fine node never changes
  a decision. Nodes stay cheap and rewritable.
