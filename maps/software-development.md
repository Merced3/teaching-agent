# Map — Software Development (coarse competency map)

Updated: 2026-09-16
Goal: Locate the learner's known/edge/unknown across the major strands of software
development, anchored to projects he built (socratic-partner, this learning system).

Method note: questions are anchored to the learner's own code where possible (thesis H8).
Status: `known` | `edge` | `unknown` | `blocked`. Evidence levels per AGENTS.md.

## Strands

| strand | status | evidence |
| --- | --- | --- |
| Data & state — state machines (why CLOSING exists) / crash windows | known (explained) | 2026-09-16: node 4 taught — middle-state-as-crash-witness lock-in passed applied-level unaided ("OPEN too general to pick the failure mode"); pizza transfer with one sharpening. Crash-window recall fading: recognizable-only at 13 days, 2nd re-presentation 2026-09-16 |
| Data & state — transactions / atomicity | known (explained) | 2026-09-01: explained all-or-nothing/rollback + "unit, harmless not smaller" framing after lock-in (initial answer correct but self-flagged as guess); boundary selection correct unaided (money writes in, Discord out); placement before/after point-of-no-return needed coaching; final ordering check mixed → explained, applied not yet clean |
| Data & state — constraints at the DB boundary (races, enforcement at write) | known (explained+) | 2026-09-03: node 3 taught grounded in store.py guarded writes; race mechanism explained unaided after plain re-teach; invariant (one-step transitions OPEN→CLOSING→COMPLETE) stated with corrections; transferred guarded write to wallet scenario with one correction round. Clean applied grade deferred |
| Failure & reliability — transient vs permanent failure classification | known | R2-Q3: derived retry-only-what-time-can-fix policy unaided |
| Failure & reliability — unknown process state after timeout, reset-to-known-state | edge | R2-Q1: grasped session-integrity risk, missed protocol desync/unknown-state reasoning |
| Failure & reliability — backoff, thundering herd, tight-loop costs | edge | R2-Q2 "I don't know"; 2026-08-31 recall: confused with fail-fast → edge |
| Failure & reliability — idempotency, delivery semantics, supervision | edge | 2026-09-01: idempotency re-presented inside node 2 after failed 1-day unaided recall (learner asked what it means, then re-derived instantly); delivery semantics surfaced in ordering check (duplication-vs-loss at Discord send, recognized via node 1) |
| Interfaces & boundaries — decoupling via protocol/ports | known | R3-Q2: named decoupling + swap-channel benefit unaided |
| Interfaces & boundaries — layer separation (policy vs mechanism) | edge | R3-Q1: answered active-conversation rule instead of reusability/coupling concern |
| Correctness & testing — what tests buy (regression detection not proof; AI-output authorization) | edge | R4-Q1: original AI-authorization frame (valuable), muddy on regression-vs-correctness |
| Correctness & testing — mock theater / assumption reflection | edge | R4-Q2 "infrastructure theater" instinct; 2026-08-31 recall: could not recall mechanism → edge |
| Correctness & testing — fake the nondeterministic, keep real semantics | edge | R4-Q3: data-isolation axis correct (temp real SQLite ≠ live DB); determinism-vs-semantics axis unaddressed |
| Scale & performance — fail-fast vs queueing, UX of waiting | edge | R3-Q3: complexity-avoidance answer, missed invisible-hang UX concern |
| Scale & performance — queues, backpressure, concurrency models | unprobed | |
| Security — least privilege / blast radius | edge | R5-Q1 insurance analogy correct shape; 2026-08-31 recall: could not recall re-presented principle → edge |
| Process — git, failed-experiment preservation | known | R5-Q2: stable main + don't-repeat-the-lesson, unaided |
| Data modeling & schema evolution — old-shape migration fixtures | known | R5-Q3: deployed data IS the contract, unaided |
| Process — rollout/rollback, review discipline | unprobed | (strong prior: lived the scheduler rollback) |
| Reading & auditing code (the "direct and review AI output" skill) | unprobed | |

## Probe log

- R1-Q1 [state machines] — partial recovery intuition, missed crash window → edge
- R1-Q2 [transactions] — "I do not know" → unknown
- R1-Q3 [DB constraint vs code check] — durability answer, missed race enforcement → edge
- R2-Q1 [timeout/reset] — session-duplication intuition, missed unknown-process-state → edge
- R2-Q2 [backoff] — "I don't know" → unknown
- R2-Q3 [billing vs rate-limit] — transient/permanent classification derived unaided → known
- R3-Q1 [scheduler/content split] — answered eligibility instead of coupling/reuse → edge
- R3-Q2 [protocol decoupling] — swap-channel benefit, correct unaided → known
- R3-Q3 [fail-fast] — complexity answer, missed UX-of-wait → edge
- R4-Q1 [purpose of tests] — AI-authorization frame + "good enough" → edge
- R4-Q2 [mock lie] — theater instinct, vague mechanism → edge
- R4-Q3 [fake clocks/real SQLite] — proximity instinct, faked/kept parts inverted → edge
- R5-Q1 [least privilege] — insurance/bounded-cost intuition, unnamed principle → edge
- R5-Q2 [preserve failed experiments] — stability + lesson-preservation, correct → known
- R5-Q3 [migration fixtures] — deployed-data-is-the-contract, correct → known
- REGRADE R4-Q3 — learner clarified "fake" meant temp-instance-not-live-DB (correct); strand row updated, status stays edge (determinism axis still unaddressed)
- 2026-08-31 RECALL CHECK (5 presented-only concepts, ~5 day delay): 0/5 recalled unaided; crash window partial-shape only; atomicity / least privilege / mocks-assumptions gone; thundering herd confused with fail-fast. All five re-presented → edge nodes; see sessions/2026-08-31-node1-crash-windows.md
- 2026-09-03 NODE 3 (races/write-boundary enforcement) taught; see sessions/2026-09-03-node3-races-write-boundary.md. Race in check-then-act gap located after wrong-layer first answer (self-flagged); guarded-write fix (check+act collapsed, DB serializes) grasped unaided; rowcount guard = loser is told it lost. Names taught: race condition / invariant / enforcement at write boundary. Recall checks: node 1 crash window recalled unaided; idempotency recalled unaided (first re-presentation→delayed-recall success); keyed-usage-record trick re-derivable only.
- 2026-09-16 RECALL CHECKS (13-day delay) + NODE 4 taught; see sessions/2026-09-16-recall-checks-node4-state-machines.md. Atomicity recalled unaided at 13 days; guarded-write re-derivable; rowcount/invariant-names/keyed-receipt gone → re-presented; crash window recognizable-only (2nd fade). Node 4: state machine = states + allowed transitions + guarded writes; witness reasoning transferred to pizza domain.
- 2026-09-01 NODE 2 (transactions/atomicity) taught; see sessions/2026-09-01-node2-transactions.md. Lock-in 1 (rollback shows neither write) correct but guess-flagged, mechanism then explained unaided; credits design: boundary correct, placement before/after unresolved ("I really don't know") → taught charge-before-point-of-no-return + keyed retry; ordering check: archive gap mislabeled unrecoverable (it is retry-safe), Discord-send gap correctly flagged unknown-delivery. Idempotency failed 1-day unaided recall. Repo-verified: real socratic-partner code already uses transaction boundaries + CLOSING/reopen reset + guarded writes (`WHERE status='OPEN'`). Same-day applied re-test: damage modes per boundary correct (applied-level), envelope scope wrong, retry walk double-charged; proof chain not unaided before fatigue → grade stays `explained`; fresh proof re-run owed next session.

## Project anchors (added 2026-10-09 — scope expansion beyond socratic-partner)

The learner's goal (docs/goal.md) is to know EVERY system in the Automations folder,
not just socratic-partner. H8 anchoring applies per-project. Use these when probing
or teaching the strand — read the real code first, never teach from assumption.

| strand | anchor project | what to ground probes in |
| --- | --- | --- |
| Data & state (all nodes) | socratic-partner, teaching-agent | store.py guarded writes; session-registry OPEN→CLOSING→COMPLETE |
| Failure & reliability — backoff/timeouts/retries | voice-bridge, teaching-agent voice | reconnect backoff ladders; stream-drop recovery; STT/TTS retry |
| Scale & performance — queues, backpressure, concurrency | automation-harness, voice-bridge | scheduler + long-running runtime supervision; paced PCM playback, full-duplex audio buffering |
| Interfaces & boundaries — protocol decoupling | discord-hub, voice-bridge | "transport only" rule; projects never import Discord libs, one hub owns the connection |
| Interfaces & boundaries — policy vs mechanism | automation-harness | harness owns runtime concerns; app owns workflow |
| Security — least privilege / blast radius | discord-hub, socratic-partner | single token ownership; explicit allowlisting; hub caretaker permissions opt-in |
| Correctness & testing — fakes/real semantics | teaching-agent, discord-hub | black-box routing-boundary tests; bridge vs discord transport fakes |
| Process — rollout/rollback, migrations | socratic-partner, all | SQLite schema migrations; v0.1.0 release discipline; scheduler rollback (lived) |
| Real-time systems (NEW candidate strand) | voice-bridge, discord-hub | RTP/DAVE breakage as unsanctioned-API risk lesson; PTT as exact turn boundaries vs VAD guesses |
| Process supervision & recovery (NEW candidate strand) | automation-harness | restart recovery, durable schedules, health reporting |

Rule: when a strand is taught from an anchor, record which project anchored it in
the evidence column — cross-project transfer is itself evidence (applied → transferred).

## Notes

- Learner flags uncertainty himself reliably ("I do not truly know") — high-quality probe
  signal; do not over-question to extract admissions he volunteers.
- Learner assumes questions are scoped to the current project unless told otherwise —
  signpost scope explicitly ("thinking beyond this project...") when a question goes general.
- **File convention**: paragraphs stored as single unwrapped lines make exact-match scripted
  edits robust; wrapping is nicer for human eyes. Either is fine for AI context-reading.
  New files should default to unwrapped paragraphs (as current-state.md already does);
  existing wrapped files stay until deliberately rewritten. Record the choice once here.
- Teacher error log: R3 map edit accidentally dropped the Correctness & testing row
  (overbroad replacement); caught and restored at R4. Verify table integrity after edits.
  A second recurring error: guessing wrapped-paragraph text when the file stores one line
  per paragraph — prefer `read`/`grep` before scripted edits on non-code files.
