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

---

## 2026-09-22 — /mode command: test mode flippable from Discord

Hypothesis: Operational toggles (test/live) belong in code as commands, not as prompts to pi — mode is a safety boundary, and a safety boundary must not depend on model cooperation. Pedagogy stays prompt-owned; operations stay code-owned. (Principle transferable to socratic-partner.)

Intervention: Added /mode test|live slash command. Toggling rebuilds pi's system prompt and restarts the subprocess; the RPC client resumes the same session file, so conversation continuity survives. Restricted to the allowed user; bad values rejected without side effects.

Evidence: 3 new black-box tests (toggle restarts pi with rebuilt prompt, bad value rejected, stranger rejected); 11/11 green, ruff clean.

Verdict: keep.
## 2026-09-30 — Voice: full-duplex conversation layer

- **Hypothesis:** the hub's Stage-2 duplex stream (per-speaker PCM + speaking events) is enough transport for a walk-and-talk teaching conversation with real interruption; STT/TTS/model stay swappable layers on this project's side, per the integration ask.
- **What was built:** `src/teaching_agent/voice/` — Deepgram streaming STT (endpointing = utterance boundaries) → same pi session as text (spoken-turn wrapper) → ElevenLabs streaming TTS, paced ~300 ms ahead of playback so barge-in (hub `speaking started` → cancel turn) leaves almost nothing buffered. Auto-join via `voice_events` registration; `/voice` command swaps ears/voice/voice-id/model live. Spoken exchanges post 🎙 transcripts to the text channel (configurable).
- **Decisions:** (1) brain = the same pi session, not a parallel fast LLM — teaching continuity beats latency for a teacher; (2) interruption policy lives here, hub events are transport signals only; (3) resampling is naive decimate/duplicate — no filter state, inaudible at speech quality; (4) a latent crash in `build_system_prompt` (append vs extend, test-mode branch) was found and fixed — the runtime had never actually booted live.
- **Evidence:** 17 tests green; build smoke-tested. NOT yet evidence: first live conversation, blocked on DEEPGRAM_API_KEY + ELEVENLABS_API_KEY.
- **Verdict:** pending live run — the 2026-09-03 prosody hypothesis becomes testable then.
## 2026-09-29 — Voice live: first real conversation (verdict: WORKS)

- **Evidence:** live full-duplex conversation in teaching-voice — Deepgram transcribed the learner, pi (openrouter/moonshotai/kimi-k3) answered, ElevenLabs George spoke back, echo-probe confirmed 21.8s of continuous decrypted receive audio. Learner heard the reply ("no way it responded back").
- **What it took to unbreak receive (discord-hub side, NO repo edits):** Discord voice is now mandatory E2EE (DAVE); the hub's discord-ext-voice-recv 0.5.3a181 (latest PyPI) cannot decrypt inbound frames. Installed porgeeratad's PR #58 branch (@dave-decrypt) into the hub venv, PLUS a local drop-frame guard in the venv's opus.py: packets arriving before the ssrc→user map skip DAVE decryption, and without the guard ONE such packet raised OpusError and killed voice_recv's router thread permanently — this was the true starvation cause. FRAGILE: venv-level patch; any pip upgrade reverts it. Needs a discord-hub session to land properly (pin the fork / vendor). Log signature for reference: 'WS payload has extra keys {seq}', 'unknown ssrc', opus 'corrupted stream'.
- **Also fixed en route:** Deepgram 1011 idle-timeout (keepalive every 8s + auto-reconnect — voice sessions are mostly silence); /status renamed /progress (socratic-partner owns 'status'; hub command names are global — first real multi-client collision, predicted in integrations §6); latent build_system_prompt crash (append vs extend).
- **Still true:** barge-in untested deliberately (speaking events flow now); pi turn latency ~2-6s (kimi-k3); George is the voice until a paid tier unlocks a real Jarvis.
## 2026-09-29 (late) — First real voice session: learner feedback

- **What happened:** a real multi-turn voice lesson ("why is the sky blue, why red at sunset"). Agent identity held ("I'm Alvar, your personal teacher..."). Transcript posting to #learning proved genuinely useful (re-reading after zoning out).
- **Learner verdict:** success as a first conversation; audio quality 'good and professional'; turn-taking 'chunky', NOT professionally reliable yet. Potential confirmed.
- **Faults logged (evidence, not vibes):** (1) barge-in fires while the learner is mid-thought — speaking-started cancels the turn with no grace period; needs debounce/grace (e.g. only interrupt after 300-500ms of sustained speech, or only while agent audio is actually playing). (2) pi turn latency reads as 10-20s of dead air — learner asks 'hello, did you hear me', which becomes a new utterance, which interrupts the pending reply; needs a fast ack ('hm, let me think') or lower-latency brain for voice. (3) endpointing raised 300->900ms (mid-sentence splits) — untested until next session.
- **Next session candidates:** interruption grace period; spoken ack-before-thinking; measure pi turn time; consider per-turn fast model.
## 2026-09-30 (late) — Turn-taking: PTT boundary + thinking fillers

- **Hypothesis:** (1) "when is the learner done talking" is unsolvable by silence-guessing but trivially solved by an explicit signal — Discord push-to-talk release; (2) dead air is a *communication* problem, not a latency problem — a pre-generated "Mm." tells the learner to wait without touching pi latency or TTS prosody.
- **What was built:** hub `speaking stopped` → `STTProvider.finalize()` (new seam; Deepgram sends `Finalize` to endpoint immediately — the button draws the boundary, endpointing stays as non-PTT fallback). `_ask_with_fillers`: ~2s of pi silence plays a pre-generated hub-format PCM clip from `out/fillers/` (rotating, ~3s apart); missing folder = silently off. `_speak` refactored into a shared paced `_stream_pcm` used by both TTS and fillers. `tools/make_filler_audio.py` generates the clips with the George voice; `TEACHING_AGENT_VOICE_FILLER_DIR` configures the dir.
- **Deliberately NOT built:** sentence-streaming TTS into pi's token stream — per-sentence prosody loss is real, and the filler already solves the actual problem (learner knowing to wait). Revisit only with evidence. Also not built: the turn-accumulator grace period — PTT makes it unnecessary; endpointing remains the fallback path when PTT is off.
- **Evidence:** 22 tests green (5 new: finalize routing, filler timing, missing-dir no-op). NOT yet evidence: live PTT conversation; filler clips not yet generated — ElevenLabs quota exhausted (0 credits, likely the 22MB thesis mp3). Per the autonomy rule, no retry until the learner intervenes; re-run `python tools/make_filler_audio.py` after quota reset/upgrade.
- **Verdict:** built, awaiting live test with Discord push-to-talk enabled.
- **Parked:** join greeting ("At your service.") hook in `join()` — one shot TTS on session start, deferred until turn-taking is verified live.
## 2026-10-01 — Turn-taking fix: hold-the-floor accumulation (live test 1 failure)

- **Evidence (live):** first PTT test failed exactly at the predicted seam — Deepgram endpointing (900ms) fired mid-hold during a thinking pause; "Why is the sky / blue?" split into two turns and the agent replied while the learner still held Caps Lock. The finalize-on-release half worked; nothing gated turns *during* the hold.
- **Fix:** turns no longer fire from STT utterances at all. `_on_utterance` only accumulates fragments; the turn fires on the hub's `speaking stopped` + 0.8s grace (final transcript fragment landing). `speaking started` re-holds (cancels a pending flush) and still barge-in interrupts. The speaking key is now the one true turn boundary; endpointing is demoted to text segmentation. Provider-agnostic: policy in conversation.py, hub events stay transport signals.
- **Evidence:** 25 tests green (2 new: merge-and-fire-on-release, re-press-during-grace cancels). NOT yet evidence: live retest.
- **Verdict:** built, awaiting live test 1 retry.
## 2026-10-01 (late) — Dual-mode turn boundary: remote PTT + auto fallback

- **Evidence (live retest):** turn fired during a thinking pause even with Caps Lock held — Discord's client VADs transmitted audio, so hub speaking events are audio-activity guesses, NOT key state. Discord exposes no PTT key state to bots (privacy/bandwidth, confirmed by learner's own research). The "Discord PTT = exact button" premise is dead; logged as replaced, not erased.
- **What was built:** pluggable turn-boundary source. `voice/ptt.py` RemotePTT (heartbeat = presence; press/release callbacks) shared between the callback server and the conversation. Callback server gains `GET /ptt` (phone hold-to-talk page, token in URL) + `POST /voice/ptt` (down/up) + heartbeat route, token-gated via TEACHING_AGENT_VOICE_PTT_TOKEN. MANUAL mode (heartbeat fresh): press = hold floor + interrupt, release = finalize + flush — zero tuned seconds. AUTO mode (heartbeat lapsed): previous speaking-event + grace behavior. Hub speaking events are ignored as boundaries while manual.
- **Rejected:** public tunnel (attack surface for nothing); VPS relay deferred — deployment.md already parks VPS hosting, which will serve the page directly when it happens. Tailscale is the off-LAN answer meanwhile.
- **Evidence:** 31 tests green (heartbeat mode-switching, press/release semantics, manual hold/fire, hub events ignored in manual, route auth). NOT yet evidence: live phone-button conversation.
- **Verdict:** built, awaiting live test on LAN; Tailscale setup is the learner's off-LAN step.
- **Parked:** BLE physical button listener (same /voice/ptt endpoint, new client) — only if the phone page proves out and physical is wanted.
