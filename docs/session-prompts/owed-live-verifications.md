# Session: teaching-agent owed live-verifications

**Suggested session name:** `teaching-agent: owed live-verifications`

Roadmap: `Automations/ops/session-prompts/README.md` (#2).

Copy everything below the line into the new session.

---

# Audit and close the teaching agent's "NOT yet live-verified" debt, running on the droplet

**Read first:** `AGENTS.md`, `docs/current-state.md` (top entry only;
the "Prior:" chain is long, so skim), `docs/decision-log.md`,
`docs/deployment.md`, and the ops `RUNBOOK.md`
(`C:\Users\cedgo\Documents\Coding\Automations\ops\RUNBOOK.md`; the
server runs this agent, not the laptop). **Pull first:** the cloud agent
commits to this repo itself.

## Step 1: inventory (read-only)

`grep -n -i "not yet live-verified\|live-verify owed\|pending live" docs/decision-log.md docs/current-state.md`
Build a table: feature | what's owed | already proven by real use since?
Many may have been proven incidentally. Example: pings have fired real
slots since 10-10 (check `data/` + session logs on the server). Known
candidates as of 2026-10-16:
- pings: `/pings status`, a real slot fire, `/pings off`, catch-up after
  downtime (several of these happened, so mark them with evidence)
- session registry: crash-restart reattach, live `/close` rotation
- voice: edge-tts blip recovering via retry, filler cadence, two-part
  utterance during a filler, mid-call bridge restart, live
  `/voice action:transport` swap each way
- lesson threads: auto-created thread opening with its brief, lesson
  wrap-up

Present the table and STOP. The user picks which to verify.

## Step 2: verify the chosen ones

Live tests use the 🧪 LAB channels + `/mode test` where possible, so the
KB is not written. Anything that needs the learner (voice, real
lessons) is done WITH the user, scheduled around his learning. Crash
drills on the server use the RUNBOOK commands (restart/stop via
compose). Never `docker kill` during an open lesson.

## Rules

- No code changes unless a verification FAILS. Then: tests first (agree
  a failing test with the user, stop, approve, then fix).
- Record each result in `docs/decision-log.md` (hypothesis → evidence →
  verdict), per AGENTS.md.

## Success =

Every owed item is either verified with evidence, explicitly dropped by
the user, or has a failing test + fix merged. Tick #2 in the roadmap.
