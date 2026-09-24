# Current State

Last updated: 2026-09-18 (2-day recall checks run — rowcount/invariant recalled, keyed receipt faded 2nd time; node 5 idempotency taught to explained — deep-dive COMPLETE 5/5).

## What exists

- **The runtime (2026-09-22):** `src/teaching_agent/` — the agent hosted in automation-harness, Discord via discord-hub, thinking via pi RPC with file tools on (cwd = this repo, system prompt built from the handoff doc). Design: pi is the teacher, code is plumbing; pedagogy changes are doc edits. Slash commands `/recall` `/close` `/status` are prompts, not logic. Test mode + recall pings default off. Identity: display name "Alvar" + avatar, both `.env` values. 8 black-box tests green; NOT yet run live against the real hub — first live round-trip is the gate. Voice (pipeline: STT→LLM→TTS, swappable layers) is designed and blocked on the hub's streaming-audio contract; see `docs/integrations/discord-hub.md`.
- **Integration contracts (`docs/integrations/`, 2026-09-22):** one file per dependency stating what this project needs from it, agnostically, with explicit "all needs met" when silent. discord-hub: open requests (voice, streaming audio, speaking events, history export, deletion primitives, multi-client verification). automation-harness: nothing needed.
- This documentation seed (6 files) — the spine, thesis, learner model, state, decision log, handoff.
- `lessons/` + `tools/make_audio.py` — the audio-lesson modality (from earlier work). Proven to generate; **unproven to retain** (see thesis H1).
- First loop artifacts: `maps/software-development.md` (14 nodes scored: 4 known / 8 edge / 2 unknown) and `sessions/2026-08-26-software-development-probe.md`. Deep-dive plan "State, invariants, and crashes": node 1 (crash windows) `known` at `applied` (unaided, 2026-08-31; recalled unaided 2026-09-03); node 2 (transactions/atomicity) `known` at `explained` + proof-chain now demonstrated unaided (2026-09-03); node 3 (races/write-boundary enforcement) `known` at `explained`+ — guarded-write mechanism re-derivable at 13 days, rowcount/invariant/enforcement names gone at 13 days and re-presented (2026-09-16); node 4 (state machines) `known` at `explained` (taught 2026-09-16, transfer with one sharpening); node 5 (idempotency) `known` at `explained` (taught 2026-09-18 — unweldable-outside-world insight derived unaided; Stripe-webhook transfer with scaffolding, applied grade open). **Deep-dive "State, invariants, and crashes" COMPLETE: 5/5 nodes.** Node 1 fading on schedule: recognizable-only at 13 days (2026-09-16), 2nd re-presentation done. Session logs: `sessions/2026-08-31-node1-crash-windows.md`, `sessions/2026-09-01-node2-transactions.md`, `sessions/2026-09-03-node3-races-write-boundary.md`, `sessions/2026-09-16-recall-checks-node4-state-machines.md`, `sessions/2026-09-18-recall-checks-node5-idempotency.md`.

## What has been tried (outside this system)

- Long-form audio lesson on the `socratic-partner` project (~50 min, `en-US-GuyNeural`). Result: useful orientation, weak retention → motivated this project.

## The next smallest milestone

Deep-dive complete (2026-09-18). Next session: recall checks ~2026-09-21 (3-day interval): (1) keyed-receipt trick — 3rd attempt, switch to PRODUCTION rep (write the handler pseudocode cold, not verbal recall); (2) invariant / enforcement-at-write-boundary names; (3) idempotent-vs-retry-safe distinction; (4) crash-window general form (between 2 durable steps; duplication-vs-loss is chosen). Also owed: node-5 applied-grade via one no-scaffold transfer in a new domain (email send / CI deploy) — fold into the 09-21 checks. Then a learner decision: pick the next deep-dive from the map's remaining edge nodes, or consolidate with a small project using all five nodes. Retention pattern re-confirmed 2026-09-18: mechanisms stick, lookup details (keyed receipt's target) fade fastest — keyed receipt has faded twice at short intervals.

## Known risks / open decisions

- Repo renamed `learning-library` → `teaching-agent` (2026-09-22): the name describes what runs. If the knowledge base ever splits into its own repo, that repo reclaims `learning-library`.
- Multi-client hub operation (two projects, one hub) is unverified — test before running alongside socratic-partner (see `docs/integrations/discord-hub.md` §6).
- One persistent pi session serves the whole channel; if threads need isolated contexts, per-thread pi sessions are the follow-up (open question, not yet a need).
- Knowledge-tree / public-skill-graph idea is parked (thesis H4) until the private loop works.
- No knowledge representation format is chosen beyond plain markdown. When a second use case demands it (e.g., syncing to an external tool), add an **adapter**, don't migrate the core.
- Communication: Discord is the expected first channel and the learner's home for agents, but it is an adapter. Socratic-partner may later act as a questioning surface; evaluate after the private loop works, not before.
- Unprompted spaced-retrieval pings (thesis H5) are the planned retention engine — defaults off, low frequency first, learner-tolerance is itself an experiment.
- **Intake gap (open):** the thesis promises stress-testing of *whatever the learner consumed*, but there is no defined way yet for the learner to report outside intake ("I read/watched X today") so the system can probe it. Not needed for the first loop (the agent is the intake); required before the "read ten books" scenario works. This is need #1 — build on need #2.
- Voice conversation (walk-and-talk: interrupt the agent, ask, debate) is a confirmed-wanted synchronous modality — the opposite end of the spectrum from async pings. Likely future adapter: Discord voice or a speech-to-text loop over the same teaching core. Second in-session evidence point (2026-09-03): text ambiguity caused a describing-vs-prescribing misread; learner hypothesizes voice prosody/tone would help disambiguate and slow phrasing where needed. Still parked as need #1 until a live test is run.
- DHH "two weeks" claim is motivation, not evidence — the learner explicitly endorsed treating it that way. One Eero Alvar video (`ciC6ffUqI8k`) not yet reviewed.
- "Is markdown a professional knowledge store?" is now an open decision (2026-08-29) with live
  evidence. Answer it after the handoff test; options range from stay-on-markdown to a
  deliberate entity/schema/DB upgrade. Don't settle by default.
- Real-world landscape (audited 2026-08-26, from training knowledge, not live-verified): closest existing systems are Math Academy and ALEKS (knowledge-graph mastery learning), Execute Program (retention-gated progression), Anki+FSRS (adopt FSRS for review scheduling when needed — do not invent one), Orbit/mnemonic medium (retrieval woven into intake), and 2024–2025 AI tutors (ChatGPT Study Mode, Khanmigo, LearnLM). No known system tracks the epistemic axis (knowledge rotting under the learner) — that integration appears to be this project's distinctive ground. Academic field for the mastery axis: "knowledge tracing."
