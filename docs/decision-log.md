# Decision Log

Append-only. Newest at the bottom. Never edit old entries except to append `OUTCOME:`. An entry is an experiment: hypothesis → intervention → evidence → verdict.

Format:

```text
## <date> — <short name>
Hypothesis: <what we believed>
Intervention: <what we did>
Evidence: <what we observed; mark unverified claims>
Verdict: keep | change | revert | inconclusive
```

---

## 2026-08-26 — Founding structure

Hypothesis: A small, explicitly-mutable documentation seed (spine + thesis + learner model + state + log + handoff) preserves direction across sessions better than a large, rigid documentation system for a project whose methods are expected to churn.

Intervention: Created 6-file seed; parked all machinery (schedulers, databases, knowledge trees) behind the "second real need" rule.

Evidence: Prior session showed a mature project (socratic-partner) where thesis-first docs prevented drift; learner rejected that full structure as too heavy for this stage.

Verdict: keep until the first teaching loop produces counter-evidence.

---

## 2026-08-26 — Audio retained as a modality, demoted as a method

Hypothesis: Long-form audio lessons orient (vocabulary, mental map) but do not retain.

Intervention: Kept `tools/make_audio.py` and `lessons/`; thesis H1 requires any future audio lesson to pair with at least one retrieval check before retention is claimed.

Evidence: Learner's self-report. No delayed-recall measurement exists yet.

Verdict: inconclusive → first teaching loop must include a delayed recall check.

---

## 2026-08-26 — Session audit (model switch: Kimi → Claude)

Hypothesis: The founding seed survives a fresh-eyes audit by a different model without
structural change.

Intervention: Full re-read of all six docs. Fixed: stray `*` in thesis H6; evidence ladder
corrected (delay is a dimension, not a top rung); added Bloom 2-sigma anchor to H2 (marked
not-live-verified); added autonomous-spend budget rule to AGENTS; named the intake-reporting
gap in current-state; recorded real-world landscape (Math Academy, ALEKS, Execute Program,
Anki/FSRS, Orbit, 2024–25 AI tutors) and the apparent niche: no known system tracks the
epistemic axis.

Evidence: Cross-model doc review; landscape from training knowledge (web search tool had no
credentials — flagged inside the notes themselves).

Verdict: keep — structure held; only content-level corrections were needed. First teaching
loop remains the next milestone.

---

## 2026-08-26 — First manual loop: probe phase complete

Hypothesis: A manual probe → map → plan loop produces usable competency evidence and valid
teaching targets without any new software.

Intervention: Ran 5 probe rounds (14 nodes) anchored to socratic-partner; wrote
maps/software-development.md; froze the "State, invariants, and crashes" deep-dive plan;
learner chose to close the session before teaching node 1 to test the handoff docs.

Evidence: 4 known / 8 edge / 2 unknown. Pattern finding: learner answers "one layer up" —
grasps what mechanisms do, not why they live at that layer (root gap: invariants and
enforcement boundaries). Learner lost the session goal mid-probe → recorded in learner.md;
future sessions should re-anchor periodically. Teacher made one map-editing error (dropped a
table row) — caught, restored, logged in map notes.

Verdict: inconclusive until node 1 is taught and the ~2026-08-29 recall check runs. The
handoff test (can a fresh session resume from docs alone?) is the next gate.

---

## 2026-08-29 — Session closeout: conventions, model label, format question, new session policy

Hypothesis: Handoffs stay robust when conventions (file form, session policy, model labels)
are recorded instead of discovered per failure.

Intervention: Fixed mislabeled Model: in session file (Claude vs Kimi mixed). Recorded a
paragraph-storage convention in docs/session-handoff.md (unwrapped lines for exact-match).
Added "markdown storage sufficiency" as an open decision in current-state.md — to be
answered after handoff-test evidence, not by default.

Evidence: Live session showed three long-line vs wrapped-paragraph edit failures before a
read/correction; the user asked if markdown is professional for evolving knowledge; model
used was mixed (Claude one round, Kimi otherwise).

Verdict: keep. Next session uses the updated handoff and convention explicitly.

---

## 2026-08-31 — First retention measurement + node 1 taught (model: moonshotai/kimi-k3)

Hypothesis: (a) Presented-only concepts (2026-08-26 scoring feedback) would show some unaided recall after ~5 days; (b) the frozen deep-dive node 1 (crash windows) could be taught to `applied` level in one step-locked session.

Intervention: Ran the owed delayed recall check on all five presented-only concepts BEFORE teaching (learner chose this over teaching directly). Then taught node 1 anchored to socratic-partner's /done flow: definition → lock-in check → learner located the real crash window at the message-send step (duplication-vs-loss trade-off) → second lock-in on why naive retry fails → learner spontaneously generalized to idempotency-as-result-invariant and inferred atomicity's role (node 2) unprompted.

Evidence: Recall check: 0/5 recalled unaided. Crash window partial (kept scope, lost time-gap mechanism); atomicity, least privilege, mocks-reflect-assumptions gone; thundering herd confused with fail-fast queueing. Node 1: learner demonstrated `applied` level unaided (located the window, named the damage mode, explained why retry is wrong, extended to exactly-once semantics in own words). Learner noticed the meta-loop ("repetitions... this is what we're running") — engagement high.

Verdict: keep. (a) Consistent with thesis H1 at n=1 — presentation alone did not retain; logged as evidence, not verdict. The four failed concepts are now `edge` nodes; re-present inside their deep-dive nodes (atomicity = node 2) and re-check with delay. (b) Step-locked teaching to `applied` worked; keep the method. Owed: node-1 recall check ~2026-09-03.

---

## 2026-09-01 — Node 2 taught (transactions/atomicity) + grounding examples in the real codebase (model: moonshotai/kimi-k3)

Hypothesis: (a) Node 2 could be anchored on the learner's own 2026-08-31 inference ("crash can't split the write") and brought to at least `explained` in one step-locked session; (b) a self-generated concept (idempotency, coined by the learner on 2026-08-31) would survive ~1 day unaided.

Intervention: Probed first (crash between CLOSING-write and billing-write; learner correctly predicted duplication/loss, guessed transaction = smaller window). Taught atomicity as "harmless, not smaller" (rollback makes the crash window unable to split the pair). Lock-in 1: what the DB shows after a crash mid-transaction. Lock-in 2: credit-charge design (boundary + placement). Final check: order COMPLETE / archive / Discord-post with per-gap damage modes. On learner request, verified all claims against the real socratic-partner repo before grading.

Evidence: (a) Succeeded at `explained`: lock-in 1 answered correctly but self-flagged as a protective guess, then mechanism explained in own words; boundary selection correct unaided; placement before/after the point-of-no-return needed coaching (clean "I really don't know" edge signal); final ordering check mixed — mislabeled the retry-safe archive gap as unrecoverable, correctly flagged the Discord-send gap as unknown-delivery. (b) FAILED: learner asked "what does idempotency mean again?" after ~1 day, then re-derived instantly on re-presentation. New observed bias: treats "gap has bad outcome" as "wrong answer" — logged in learner.md. Repo grounding: store.py uses `with self._connection()` transaction boundaries (rollback on exception); CLOSING + reopen_conversation is the reset/retry mechanism; real /done order is CLOSING → LLM → send message → final DB write, with reopen-on-failure.

Verdict: keep. Node 2 graded `known (explained)`; applied not yet clean → re-check with delay ~2026-09-03 alongside node-1 recheck. Idempotency failure is n=2 against "self-generation retains" — consistent with H1/H5; re-present idempotency at node 5 with delayed check. Grounding synthetic examples in the real repo is cheap and high-trust; adopt as default whenever a real anchor exists.

OUTCOME (same-day addendum): Learner chose to keep pushing node 2 toward `applied` in the same session. Applied re-test (order the full /done sequence with damage modes, scope the charge transaction, walk the crash-retry): damage-mode naming was correct per boundary (applied-level); envelope scope wrong (put CLOSING + LLM call inside the transaction); retry walk double-charged (missed the keyed skip-check). Corrections: rollback only reaches the DB (outside-world actions can never live in a transaction); each DB step is its own envelope; guarded writes (`WHERE status='OPEN'`) as the real-code idempotency pattern; record-exists → balance-was-decremented proof chain. Final proof question not answered unaided — learner hit a fatigue wall and stopped ("Im pretty spent"). Diagram-first explanation (one boxed 5-step picture) landed where paragraphs hadn't. Grade stays `explained`; fresh proof re-run owed next session before node 3. Fatigue wall + interrupt desire logged in learner.md.

---

## 2026-09-01 — Recall-state taxonomy adopted (learner + Socratic Partner co-authored)

Hypothesis: A failure-to-recall taxonomy with per-state actions keeps the retention gate honest without inflating beyond the loop.

Intervention: Socratic Partner asked what counts as retained without on-demand recall. Answer drafted here, sharpened by the learner (with Socratic Partner's help): unaided recall stays the gate for `known`; failure splits into recallable/re-derivable/recognizable/gone, each routing a distinct agent action. Collapse rule: merge any two states that ever route to the same action.

Evidence: Node-2 idempotency failure (gone at 1 day, re-derived instantly) and the 2026-08-31 0/5 recall check supplied the motivating cases.

Verdict: keep, with the learner's amendment recorded: the system's test is improving the ability to USE knowledge, not name it; the taxonomy is subordinate to the loop.

---

## 2026-09-03 — Node 3 taught (races / write-boundary enforcement) + first re-presentation→delayed-recall success (model: moonshotai/kimi-k3)

Hypothesis: (a) node-2 proof re-run would pass fast when rested (retention datapoint, not re-teach); (b) node 3 could be taught to explained+ in one session grounded in real store.py guarded writes; (c) the 09-01 idempotency re-presentation would show up in delayed recall (~2 days).

Intervention: Proof re-run first (unaided, chat): passed clean — record-exists → charge-applied, atomicity "impossible to lie," retry skip via keyed record. Then node 3 in three step-locked steps: (1) race in naive check-then-act close (learner first answered wrong layer — fail-fast/load — and self-flagged; retaught plain: two moments, time between, collapse into guarded write; DB serializes row writes; loser writes nothing); (2) names: race condition / invariant / enforcement-at-write-boundary, exercised on reopen_conversation's guard (two wrong invariant formulations, then correct); (3) transfer: wallet spend race, guarded write produced in plain words after one correction round. Owed recall checks folded in mid-session: node 1 crash window recalled unaided; idempotency recalled unaided; keyed-usage-record trick re-derivable only (~5-10 min effortful retrieval, order misremembered — Discord-send vs COMPLETE swapped).

Evidence: (a) passed unaided — consistent with "fatigue, not learning" for the 09-01 failure. (b) taught to explained+; transfer achieved with one correction; learner self-reported low confidence at first landing (logged in learner.md). (c) SUCCEEDED — first evidence in-system that re-presentation converts `gone` → `recallable` with delay (contrast: 0/5 and 1-day idempotency failures earlier). Learner asked for lead-with-the-plain-version after blanking on a dense lock-in question; rule adopted: one new word per sentence on first presentation.

Verdict: keep. Node 3 strand edge → known (explained+); clean applied grade deferred until a no-correction transfer. Owed ~2026-09-06: guarded-write-as-race-fix, invariant/enforcement names, keyed trick, node-1 crash window second interval. Next: node 4 (state machines) — learner's own OPEN→CLOSING→COMPLETE rail is the anchor.

---

## 2026-09-02 — Audio format experiment: dialogue + prediction pauses vs narration

Hypothesis: A two-voice interview lesson with built-in prediction pauses ("answer before
the tape does") will retain better on delayed recall than the 2026-08-26 narration-style
lesson, which scored 0/5 at 5 days. Secondary hypothesis (learner-articulated): content
density beats runtime targets — the learner asked for 30 min (his sauna-session length),
got 13 min of dense material, and identified his own length request as the same incentive
error as essay word-count requirements ("length targets incentivize fluff").

Intervention: Built lessons/crash-proofing-dialogue/ — interviewer/guest dialogue (Guy +
Christopher voices) replaying the learner's ACTUAL wrong answers and self-flags from nodes
1–3, with 5 prediction pauses. Content: crash windows, transactions, races/guarded writes,
idempotency recovery story, wallet transfer. Script pauses are retrieval reps if the
listener answers (even silently); presentation if he lets them wash past.

Engineering note: edge-tts dropped segments mid-render twice (flaky); the lesson's
make_audio.py now retries with backoff and concatenates raw MP3 frames (no ffmpeg on this
machine). tools/make_audio.py stays the generic single-voice narrator; the dialogue script
stays lesson-local until a second dialogue lesson creates the second real need for
extraction.

Evidence: pending — measured at the ~2026-09-06 recall checks (node 1–3 concepts) vs the
0/5 narration baseline. Learner must report whether he answered the pauses or let them pass.

Verdict: pending.

OUTCOME (2026-09-03, learner report after 2 listens): (a) Spoken "take a second" prompts did
NOT function as pauses — verbal instructions don't create retrieval space; real dead air
would. Rendering bug also dropped one of five intended beats (4 in transcript). Fix path:
ffmpeg + true silence segments. (b) First listen retained nothing and "felt performative"
(presentation-only, consistent with H1). (c) Second listen (driving): recalled
"harmless, not smaller" — but that phrase was the node-2 lock-in phrase, so this is
re-presentation refreshing prior teaching, not audio creating retention. (d) Learner's
own inference "it gets better the more I listen" is the recognition-fluency trap in his
own words — logged as a teachable moment, not evidence of retention. (e) Format verdict
refined: audio = re-presentation layer, not teaching or retention layer. True recall
verdict still owed at the 2026-09-06 checks; the no-real-pauses flaw means the
dialogue+pauses hypothesis was NOT cleanly tested this round.

---

## 2026-09-16 — 13-day recall checks + node 4 taught (state machines) (model: moonshotai/kimi-k3)

Hypothesis: (a) the ~3-day recall checks, accidentally run at 13 days after a learner break, would show what actually survives a real-world gap; (b) node 4 (state machines) could be taught to explained in one session anchored on the learner's own OPEN→CLOSING→COMPLETE rail.

Intervention: Ran all four owed checks unaided first (graded honestly, re-presented failures), then probed node 4 ("why does CLOSING exist?") and taught middle-state-as-crash-witness in two step-locked steps with a pizza-domain transfer check. Also adopted the learner's standing rule: agent checks the real date and computes elapsed time whenever he says "it's been a while" (recorded in session-handoff.md).

Evidence: (a) Split result — manipulated mechanisms survived (atomicity recalled unaided at 13 days; guarded-write race fix re-derivable from one scaffold); names and lookup details did not (invariant/enforcement names, keyed-receipt trick, rowcount detail all `gone`; crash window recognizable-only, same fade pattern as 2026-08-31 — second identical fade). Wrong-layer "fail fast" reflex re-appeared under cold recall but self-corrected with one scaffold (previously needed full re-teach). (b) Node 4 graded known (explained): lock-in passed applied-level unaided ("OPEN is too general to tell you which failure mode to run"); pizza transfer with one sharpening.

Verdict: keep. Retrieval reps should target names + lookup details (the fading layer), not re-teach mechanisms. Crash window gets a short-interval rep and a natural re-appearance inside node 5. Owed ~2026-09-19: rowcount guard, invariant/enforcement names, keyed-receipt trick, crash-window specifics.

---

## 2026-09-18 — 2-day recall checks + node 5 taught (idempotency); deep-dive complete (model: moonshotai/kimi-k3)

Hypothesis: (a) the ~3-day checks (run at 2 days) would show whether the 2026-09-16 re-presentations converted `gone` → `recallable`; (b) node 5 could be taught to explained anchored on the learner's own recalled idempotency definition, with crash-window specifics folded in.

Intervention: Ran all four owed checks unaided first (graded honestly, re-presented failures). Then probed node 5 ("is /done idempotent? what makes a step re-runnable?"), taught the dividing line (naturally-repeatable vs receipt vs neither), and ran a Stripe-webhook transfer.

Evidence: (a) Split again — rowcount guard and invariant recalled unaided at 2 days; enforcement name re-derivable; keyed-receipt trick faded a SECOND time (wrong lookup target: conversation state instead of receipt); crash window partial (project-specific framing, general form needed re-statement). Idempotency definition recalled unaided for the 3rd consecutive session. (b) Node 5 graded known (explained): learner derived the unweldable-outside-world insight UNAIDED (talked himself out of his own Discord-receipt proposal mid-answer); locked idempotent-vs-retry-safe as distinct names; Stripe transfer needed two plain-it-down rounds then succeeded, including the atomic grant+receipt reasoning and (sharpened) both mirror crash gaps.

Verdict: keep. Deep-dive "State, invariants, and crashes" COMPLETE 5/5. Keyed receipt has faded twice verbally → next rep switches form to PRODUCTION (write the handler pseudocode cold) per the evidence that manipulated mechanisms stick. Owed ~2026-09-21: keyed-receipt production rep, invariant/enforcement names, idempotent-vs-retry-safe, crash-window general form, plus one no-scaffold node-5 transfer for the applied grade. Open learner decision: next deep-dive vs consolidation project.

---

## 2026-09-22 — Runtime built: pi-as-teacher over discord-hub; repo renamed teaching-agent (model: varies — pi harness)

Hypothesis: The teaching behavior should live in the markdown knowledge base, not in code. If pi (RPC mode, file tools on, cwd = this repo, system prompt built from docs/session-handoff.md) is the teacher and the new code is pure plumbing (hub registration, message routing, command translation), then changing pedagogy never requires a code change — the maximally-changeable architecture the learner asked for.

Intervention: Renamed repo learning-library → teaching-agent (name describes what runs; knowledge-base repo can reclaim the old name if the docs ever split). Built src/teaching_agent/: env config (agent name is a .env value), hub client (same contract as socratic-partner's), pi RPC client adapted from socratic-partner's proven one — with tools/context-files ENABLED (socrates runs tool-less; the teacher must read/write the knowledge base), FastAPI callback server, thin engine (messages → pi; /recall /close /status → prompts), harness-hosted entrypoint matching discord-hub's pattern. Test mode (default on) forbids knowledge-base writes. Recall pings wired but off by default per the spine. Voice planned as pipeline (STT→LLM→TTS) with streaming-capable hub transport requested so a realtime bridge stays a drop-in upgrade. Hub feature requests documented in docs/discord-hub-requests.md (agnostic: voice foundation, bidirectional streaming audio, speaking events, history export, deletion primitives).

Evidence: 8 black-box tests pass; ruff clean. Not yet run live against the real hub/Discord — first live run is the next gate.

Verdict: keep, pending live verification. Owed: first end-to-end run (register #learning, send a message, run /status), then decide whether the single-persistent-pi-session model holds or threads need per-thread pi sessions.

---

## 2026-09-22 — Integration contracts doc type + identity + deployment notes; ADR question answered

Hypothesis: (a) A dedicated doc type — one file per dependency, stating this project's needs agnostically, with explicit "all needs met" when silent — communicates across sessions better than ad-hoc messages. (b) The existing decision-log format (hypothesis → evidence → verdict) suffices for architecture decisions too; ADRs would be a second format to maintain before a demonstrated need.

Intervention: Created docs/integrations/ (README defining the type; discord-hub.md with open requests incl. multi-client verification; automation-harness.md at "all needs met"). Chose identity: display name "Alvar" (the Alvar method, thesis H2) + committed avatar, both .env values. Wrote docs/deployment.md for the future VPS session. Kept the decision log as the single decision record; ADR adoption deferred until decisions start needing "superseded-by" chains.

Evidence: learner requested the doc type ("nothing is needed currently, all needs met" framing is his). ADR-vs-log: one format serves both experiment and architecture entries so far; discord-hub's ADRs exist because it makes protocol decisions with consumers — this project's decisions are mostly self-contained.

Verdict: keep. Voice code remains blocked on the hub's streaming-audio contract (documented as the blocking item in docs/integrations/discord-hub.md §2); Phase B implementation resumes when the hub ships it.
