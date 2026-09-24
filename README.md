# Learning System (working name — rename freely)

A personal system for getting brought up to speed on anything, and staying current as it changes. One learner, one trusted interface, many verified sources.

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

`TEACHING_AGENT_TEST_MODE=true` (the default) means the teacher never writes to the knowledge base. Flip to `false` for real sessions. Unprompted recall pings are off by default (project spine); enable via `TEACHING_AGENT_RECALL_PINGS_ENABLED`.

Everything except `AGENTS.md` is a current best theory and may be rewritten — with the change logged in `docs/decision-log.md`.
