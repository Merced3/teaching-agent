# Ping reliability investigation and future improvements — 2026-11-16

Session: `teaching-agent: fix pings + Annotate future improvements`. This note is a running engineering record, not learning evidence; it does not alter the generated `docs/current-state.md`.

## Reported symptom and acceptance target

The learner configured `/pings 3` and expected **three visible pedagogical Discord messages per day**. `/pings status` reported 08:23, 12:53, and 14:25 in `America/Chicago`; no visible message appeared at 08:23. Production runs in the pull-only `teaching-agent` DigitalOcean droplet, not locally. Acceptance means each configured slot produces one useful visible ping, downtime does not create a nag backlog, settings survive every tick, delivery failures remain retryable, and failures have useful logs.

## Evidence collected before editing

Read the scheduler, main service loop, engine tick/command handlers, JSON/Postgres stores, tests, deployment Compose file, relevant historical ping decisions, and the ops build/deploy/runbook path. Inspected the live container, five days of process activity, errors, restart/OOM state, managed operational state, and the exact live Pi turn.

Live facts:

- Container healthy, zero restarts, not OOM-killed, current deployed source `b906ef8`; host and Chicago clocks agree.
- At `2026-11-16T14:23:16Z` (08:23:16 Chicago), the scheduled tick called Pi successfully; Pi returned exactly `SILENT` because it inferred that the earlier session had ended at fatigue. No Discord post followed. This was a visible-message policy mismatch, not a missed timer.
- Persisted `last_fired` became 08:23:20, proving the slot was consumed.
- Before the tick, the saved custom window was 08:00–22:00. `mark_fired()` constructed a new `_State` without the window fields, resetting them to null. Environment defaults (08:00–23:00) then generated a different same-day schedule (08:57 / 12:22 / 18:17), an unintended immediate redraw and duplicate nearby slot.
- `ping_delay_seconds()` subtracted naive UTC `datetime.now()` from a naive Chicago next slot, forcing the minimum one-second delay instead of sleeping until the slot/five-minute cap.
- The tick marked the slot fired before the Discord post; a failed post could therefore suppress retries even though the main-loop message says failures retry.
- Non-recall exceptions from delay/state evaluation were outside the main loop's `try`, so a transient store error could permanently end the otherwise-unobserved nested recall task while HTTP health stayed green.
- Recent production logs showed no exception, and `/pings status` only describes future slots, so neither silent outcomes nor these scheduler faults were observable without database/session inspection.

## Fix being implemented

1. Preserve all existing state with `replace()` when marking a slot fired.
2. Calculate delay with an injectable learner-wall-clock `now` inside `PingController`.
3. Keep the whole recall-loop iteration inside its error boundary; add due, delivered, silent-contract-violation, and failure logs.
4. Mark a slot only after Pi has completed and any required Discord delivery succeeds. Preserve collapse-to-one catch-up behavior.
5. Change the ping prompt to match the learner's explicit 2026-11-16 direction: a configured slot is a visible ping, not an invisible model turn. Keep one question outstanding by briefly re-asking it rather than opening a stack; recall/re-verification/lesson offers remain the only permitted content.
6. Add regression tests for state/schedule preservation, timezone delay math, and failed-delivery retry eligibility.

## Future improvements (annotated, not silently bundled)

- **Status observability:** `/pings status` should distinguish scheduled slots, fired slots, and the last outcome (`delivered`, `silent`, `failed`) with timestamps. Current `last_fired` alone cannot explain a quiet day. Add structured outcome state only after choosing backward-compatible migration semantics.
- **Delivery receipts:** store the hub message ID or a small delivery record per slot. That would support exact once-only delivery after ambiguous network failures; simply retrying can duplicate if the hub accepted a message but its response was lost. This is a real idempotency boundary, not just a logging issue.
- **Health distinction:** expose scheduler liveness (last successful wake and last tick result) separately from callback `/health`, with bounded staleness. Avoid triggering an outage merely because the next random slot is hours away.
- **Catch-up observability:** report when multiple missed slots collapse into one, including which slot the catch-up represents. Preserve the learner-approved no-backlog policy.
- **DST coverage:** current naive local times intentionally follow wall clock, but America/Chicago DST fold/gap behavior is untested. Define expected behavior before adding tests or timezone-aware persisted timestamps.
- **State-store efficiency:** a single scheduling check performs several synchronous managed-Postgres reads. After correcting the UTC/Chicago delay bug, measure before considering one-state-read-per-iteration, async I/O, or caching; do not optimize the former one-second loop by hiding it.
- **JSON atomicity regression:** the legacy local store previously used temp-file replacement; the Postgres refactor changed it to direct `write_text`. Restore atomic local writes independently if local JSON remains a supported runtime backend.
- **Prompt/context cost:** live pings reuse a large session; the observed silent turn paid to read a large context only to emit `SILENT`. Visible-ping policy prevents that exact waste, but a bounded fresh ping session or compact routing snapshot deserves measurement before redesign.
- **Cadence evidence:** the earlier one-visible-question-per-day conduct rule was a learner-behavior hypothesis, now superseded by the learner's explicit visible-slots request. Watch response burden and re-evaluate from evidence rather than preserving silent slots by default.

## Verification and deployment record

The operational window override was restored to 08:00–22:00; the remaining live slots are 12:53 and 14:25, and the accidental 08:57 slot is gone. This repairs only today's redraw, not the deployed code or visible-ping policy.

Offline implementation checks: **136 passed, 2 skipped** (both opt-in managed-Postgres integrations, not configured locally); Ruff passed. The new regressions failed against the old behavior before the fix. Pre-existing asyncmock resource warnings remain; no new warning classes were introduced. Whole-repo `ruff format --check` reports pre-existing drift in 15 files, so it is not being used as a new gate or bundled into this narrow change.

Pending PR/CI, merge, automatic image build/digest deploy, and production acceptance. Do not claim live code repair before the deployed source and a real visible slot or controlled delivery path are verified.

## Recurring CI credential failure and durable migration (same session)

PR #9's required checks failed before Ruff/pytest: `actions/checkout` of the private `automation-harness` returned `Bad credentials`. The existing local/server `GH_PAT` also returned HTTP 401 for `/user` and the repository endpoint (credential values were never printed). GitHub shows `AUTOMATIONS_PAT` was last updated 2026-10-16; failure on 2026-11-16 is consistent with the default 30-day PAT lifetime. This is an infrastructure blocker, not evidence against the ping change. The learner redirected the work from another repeated rotation to a durable, project-agnostic solution.

Decision approved by the learner: use the new `automations-ci-reader` GitHub App for ALL consumer projects and future standard project onboarding, not a teaching-specific exception. The learner created it with Contents:read, no active webhook, only-this-account installation, and installation ONLY on `Merced3/automation-harness`. Redirect URI, user-token expiry, post-installation, IP allow list, display settings, and Save changes were not needed. Client ID and PEM were stored only in ignored local paths (`ops/env/ci-app.env`, `ops/secrets/*.pem`); PEM validation passed, and no credential values were entered into this note.

Implementation: the shared `automations-ci` reusable workflow mints a one-hour installation access token through `actions/create-github-app-token@v3`, explicitly limited to `Merced3/automation-harness` and Contents:read. Consumer projects store the same App Client ID variable and private-key secret for Actions AND Dependabot (the secret fan-out was completed and names verified, values suppressed). `automation-harness` itself needs no App credentials because it does not check itself out. A new `ops/setup-ci-app-auth.sh OWNER/REPO ...` automates future per-project setup, while one shared reusable workflow owns the actual behavior. App private keys avoid scheduled PAT expiration but still require rotation after compromise.

PRs awaiting ordered owner review/merge: `automations-ci#1` (shared workflow FIRST), then `discord-hub#10`, `socratic-partner#6`, `voice-bridge#15`, and `teaching-agent#9` (the ping change plus its caller migration). Until these merge and checks pass, CI repair and live ping deployment are not complete.

Scope boundary: CI is only the first PAT use. `GH_PAT` still supports server Git pushes and dev-agent API operations; `GH_ACTIONS_TOKEN` separately dispatches deployments; hub auth tokens are unrelated. Server App/deploy-key migration must be separately designed/reviewed, not bundled into this CI fix. Old `AUTOMATIONS_PAT` repo secrets should be removed only after every project has passed through the App path.

Documentation added across projects: the ops RUNBOOK now records the App architecture, ignored credential locations, repeatable onboarding, Dependabot distinction, recovery scope, and later secret-removal gate. At the learner's request it also records a cross-project PR-authoring lesson: `gh pr create --body` needs a real multiline body or stdin, not literal `\\n` escapes. That avoids the manual PR-body cleanup he had to perform here.
