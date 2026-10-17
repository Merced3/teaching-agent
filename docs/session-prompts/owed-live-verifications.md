# Session: teaching-agent owed live-verifications — ✅ DONE 2026-10-17

**Suggested session name:** `teaching-agent: owed live-verifications`

Roadmap: `Automations/ops/session-prompts/README.md` (#2 — ticked 2026-10-17).

Copy everything below the line into the new session.

**COMPLETED 2026-10-17.** All 17 owed items closed: 16 verified, 1 explicitly dropped. Full evidence in `docs/decision-log.md` entry "2026-10-17 — Owed live-verifications audit" (+ same-day OUTCOME addendum). Outcome details at the bottom of this file. The text below the line is preserved as-run.

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

---

## Outcome — 2026-10-17 — SUCCESS (all items closed, zero code changes)

Inventoried every "not yet live-verified" claim in the decision log + current-state (17 items), then closed each with evidence rather than new tests where real use had already proven it.

**Verified incidentally / by real use (no drills needed):** first end-to-end run (09-22, weeks of traffic since); voice first live run + prosody hypothesis (09-29 entry); edge TTS in a real call (10-06 entry); live `/close` rotation (server registry: close 10-16 19:18:26, fresh session 1s later); real ping slot fires (reproduced the deterministic slot math — 10-16 slot 3 computed 19:17:19 vs `last_fired` 19:17:23 — plus answered-ping session logs 10-10..10-16 and 4 documented SILENTs); auto-created lesson thread + kickoff brief (10-09); lesson wrap-up human-only `/lesson end` (10-09 timeout-tail close); mid-call bridge restart reconnect ladder (10-09 night OUTCOME).

**Verified by unplanned live event:** crash-restart reattach + NEXT-BOOT boot consumption — the 10-16→17 ops session (`git-parity-and-credentials`) restarted the agent twice; boot logs show `Reattached session 04343b4fd30e (owner=main)` and the server KB has `NEXT-BOOT.consumed-2026-10-16.md`. The catch-up drill's tick was also the first functional turn on the reattached session, closing that residual.

**Verified live by the learner this session:** `/pings status` (reply matched `describe()`); `/pings off` (ack + persisted `pings_per_day: 0`; 11:44 + 12:37 UTC slots then passed unfired); filler cadence ("loading an answer" heard in real lessons); interruption/two-part utterance (rare in his usage, works); `/voice action:transport` both directions (used multiple times).

**Catch-up drill (scheduled, passed same day):** pings OFF across the 11:44 + 12:37 UTC slots → `/pings 3` at ~13:19 UTC → exactly ONE catch-up tick at 13:21 (turns 0→1, one pi run, `last_fired` updated) — missed slots collapsed to one, and it posted a real (non-SILENT) recall check.

**Dropped (1):** edge-tts blip recovering via retry — learner explicitly dropped; can't be forced safely and the retry/degrade paths are test-pinned (failure mode = posted ⚠️ notice, never a lost turn).

**Side finding (noted in the decision log, no action):** `PingController.due()` only inspects the current day's slots, so downtime crossing midnight silently drops unfired slots. Consistent with the "never a backlog" design; flagged so no future session mistakes it for a bug.

Everything recorded in `docs/decision-log.md` (2026-10-17 audit entry + OUTCOME addendum), pushed as commits `cdc49cc` and the wrap-up commit. Roadmap #2 ticked.