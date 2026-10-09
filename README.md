# Learning System (working name — rename freely)

A personal system for getting brought up to speed on anything, and staying current as it changes. One learner, one trusted interface, many verified sources.

**The opposite of brain rot.** Feeds give you content that washes over you and leaves nothing behind. This system is built so nothing washes over you: everything you consume gets stress-tested — retrieval, application, unannounced re-testing weeks later — and only what survives the stress counts as *known*. Evidence levels are recorded honestly; fluency is never mistaken for retention. Where brain rot optimizes for time-on-feed, this optimizes for durable capability per minute of effort.

**Start here:** `AGENTS.md`, then `docs/thesis.md`. **New session?** Use the prompt in `docs/session-handoff.md`.

## Layout

```text
AGENTS.md            # the stable spine + rules (read first)
docs/
  thesis.md          # the goal, the two-axis model of knowledge, hypotheses
  learner.md         # what we know about how this mind learns (editable by the learner)
  current-state.md   # what exists, what's next — always honest
  decision-log.md    # append-only experiments: hypothesis → evidence → verdict
  session-handoff.md # new-session prompt + closing checklist
lessons/             # audio/other lesson artifacts (one subfolder per topic)
maps/                # per-topic edge maps (created when first teaching happens)
sessions/            # per-topic teaching session logs (created when teaching happens)
tools/
  make_audio.py      # lesson.md → transcript.txt + lesson.mp3
src/teaching_agent/  # the runtime: Discord via discord-hub, thinking via pi RPC
tests/               # black-box tests for the routing boundary only
```

## The runtime

The agent runs inside the automation-harness and talks to Discord exclusively through discord-hub. Design: **pi is the teacher, the code is plumbing.** Pi runs in RPC mode with file tools, working directory = this repo, system prompt built from `docs/session-handoff.md` — so teaching behavior lives in the markdown and changes without code changes. The agent's name is a `.env` value (`TEACHING_AGENT_NAME`), never code.

```bash
pip install -e ../automation-harness   # sibling repo, not on PyPI
pip install -e ".[dev]"
cp .env.example .env                    # fill in your values
python -m teaching_agent.main
```

**Voice (2026-09-30):** full-duplex conversation over discord-hub's `/voice/stream` — Deepgram STT (ears) → the same pi session as text (brain) → TTS (voice), with barge-in: start talking and the agent stops instantly. Auto-joins whatever voice channel you enter. Every layer is swappable live from Discord: `/voice action:stt|tts value:<name>`, `/voice action:voice value:<voice-id>` (a Jarvis sound is a voice-id, not code), `/voice action:model value:<provider/model-id>`, and `/voice action:transport value:discord|bridge` — the carrier itself swaps without a restart (bridge at home, Discord in the car; swapping to discord joins the channel you're already in). Stream drops (bridge/hub restarts) reconnect on a backoff ladder instead of ending the session. Default TTS is **edge-tts** (free Microsoft neural voices, no key) since 2026-10-06; ElevenLabs remains an opt-in (`TEACHING_AGENT_VOICE_TTS=elevenlabs` + `ELEVENLABS_API_KEY`). Requires `DEEPGRAM_API_KEY`; see `.env.example`. While pi thinks, the voice says one fixed phrase ("Loading an answer.") every 2 s — a status signal, not personality — synthesized once per session with the active TTS.

**Lecture episodes:** `/lecture topic:<text>` generates a spoken audio episode for offline listening (sauna, walks, drives). Pi writes the markdown into `lessons/<slug>/lecture.md` (knowledge-base authoring), the code renders it to `lecture.mp3` with the existing `tools/` pipeline (`TEACHING_AGENT_LECTURE_TTS=elevenlabs|edge`), and posts a **link** — the file is served by the agent's own callback server at `/lectures/...`, so it plays on the phone over LAN/Tailscale (`TEACHING_AGENT_LECTURE_PUBLIC_URL`). Every generated episode is recorded in `docs/current-state.md` as UNPROBED so a later `/recall` probes its content — the agent generated the intake, so it knows what the learner consumed.

`TEACHING_AGENT_TEST_MODE=true` (the default) means the teacher never writes to the knowledge base. Flip live from Discord with `/mode test` / `/mode live` (restarts the pi subprocess with a rebuilt system prompt; the conversation session resumes). Unprompted recall pings are off by default (project spine); enable via `TEACHING_AGENT_RECALL_PINGS_ENABLED`.

Everything except `AGENTS.md` is a current best theory and may be rewritten — with the change logged in `docs/decision-log.md`.
