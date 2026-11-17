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

Ordered rollout COMPLETE: `automations-ci#1` merged first; `discord-hub#10`, `socratic-partner#6`, `voice-bridge#15`, and `teaching-agent#9` all merged with owner approval. Every consumer passed both push and pull-request CI through real App-minted tokens. The ping merge commit on main is `aa212e3802f96e61c0c9936d1d6839fc7b4d41ff`.

Scope boundary after CI: `GH_PAT` still supports server Git pushes and dev-agent API operations, and hub auth tokens are unrelated. Those are not deleted. Deployment dispatch needed its own trust boundary, implemented below. Old `AUTOMATIONS_PAT` repo secrets are now safe to remove because every consumer passed through the App path; secret removal is cleanup, not a requirement for a successful token flow.

Documentation added across projects: the ops RUNBOOK now records the App architecture, ignored credential locations, repeatable onboarding, Dependabot distinction, recovery scope, and later secret-removal gate. At the learner's request it also records a cross-project PR-authoring lesson: `gh pr create --body` needs a real multiline body or stdin, not literal `\\n` escapes. That avoids the manual PR-body cleanup he had to perform here.

## Deployment-dispatch migration forced by live evidence

After the ping merge, the hub controller could not dispatch its image build: the old `GH_ACTIONS_TOKEN` returned HTTP 403. `build-images.yml` also still used `AUTOMATIONS_PAT` for private source checkouts, so fixing dispatch alone would have exposed another failure. Instead of widening the public-CI reader key, the learner created a second `automations-deployment` App, installed only on `Merced3/automations`, with Actions:read/write + Contents:read.

Validation caught that saving Actions permission on the App registration did NOT update the existing installation: token creation returned 422 until the separate installation permission review was accepted. The deployment and CI PEMs were renamed to explicit `automations-deployment.pem` / `automations-ci-reader.pem`, both OpenSSL-validated, with distinct Client IDs. Both Apps now mint real installation tokens. Private harness read returned HTTP 200; the deployment token's real Actions workflow-list endpoint returned HTTP 200. (The different Actions-permissions configuration endpoint is not the acceptance probe.)

The ops implementation adds a stdlib+openssl token minter with narrow repository/permission scopes, controller preference for the App with temporary legacy fallback, build workflow CI-reader/GITHUB_TOKEN source checkouts, and offline regressions for JWT claims, scope payloads, preference, failure cutoff, and role-impact scoping. The new token helper maps only to the hub and the onboarding script is non-runtime, avoiding unnecessary rebuilds/restarts of unrelated roles. All 22 focused token/dispatch tests passed before the final full suite.

The guarded deployment-auth PR merged. Manual bootstrap run `43904211044` built/deployed teaching in 1m40s; live source is `aa212e3802f9...`, digest `5a6f29f117...`, container healthy. Live `/pings` state remains 3/day, 08:00–22:00, next slots 12:53 and 14:25, and corrected delay math returns roughly 9,760 seconds rather than one second. Hub bootstrap run `43904607245` also passed and installed the new controller/token helper.

The first ordinary controller poll then exposed one more distinct PAT consumer before dispatch: private `git ls-remote` HEAD discovery returned `Invalid username or token` against the expired GH_PAT. Follow-ups pass the deployment App token for private automations HEAD and a CI reader token for private harness HEAD via process-scoped Git config, with public app reads unchanged. Live protocol checks then proved REST-style Bearer auth is NOT valid for these Git HTTPS reads and the legacy helper can conflict; correct Basic auth (`x-access-token` + App token) with that helper disabled succeeds. Server Git pushes/dev-agent API auth remain separate documented debt; no broad credential deletion or widening is included. Automatic controller dispatch then passed: rc=0 and runs `43907071532`, `43907076352`, `43907081943`, `43907087445`, `43907093628`. Four builds healthy; Teaching hit the pre-existing two-minute readiness gate during the concurrent hub redeploy and rolled back, but immediate deliberate retry on the exact digest became healthy and emitted the recovery alert. Teaching has now earned the same bounded 72-probe readiness budget as Socratic, with a delayed-success regression and first-attempt acceptance owed on the next new source. Obsolete AUTOMATIONS_PAT secrets were removed from all five repos for Actions/Dependabot after successful CI; hub GH_ACTIONS_TOKEN was removed after automatic dispatch passed. No unrelated GH_PAT uses were deleted.

## Final rollout status and remaining acceptance

The inventory classifier fix was necessary because the readiness PR initially advanced the baseline without delivering its runtime inventory. After that classifier merged, the ordinary controller dispatched all five services again: `43909456365`, `43909462256`, `43909467389`, `43909471434`, `43909476582`. ALL completed successfully; Teaching passed on its FIRST attempt with no force and no health-failed source marker. Its transient hub `ConnectError` retries during startup were the concrete readiness behavior covered by the new six-minute budget. Current Teaching source is `aa212e3802f9...`, current ops SHA `30f16291970a...`, image digest starts `08a5c165417c...`; container and HTTP health are green. Persisted pings remain 3/day, 08:00–22:00, next 12:53 / 14:25, delay math healthy.

Implementation/deployment is therefore complete. Deliberately NOT claimed yet: a natural visible Discord ping under the new prompt. Next organic slot is 12:53 America/Chicago; generating an extra fourth ping or rewriting slot state merely to claim acceptance would add noise and contaminate evidence. At that slot expect `Ping slot due; starting recall tick.` plus `Ping slot delivered to Discord.` in logs and a visible recall/re-verification/lesson offer in #learning. A model SILENT despite the new contract now logs an explicit warning instead of disappearing quietly. The remaining validation was observational, not a known code blocker. CLOSED by learner confirmation at end of day: BOTH natural pings posted and were answered.

## Natural ping and `/close` acceptance (end of day)

Production logs confirm the 12:53 slot produced a Pi turn, HTTP 201 Discord delivery, and `Ping slot delivered to Discord.`; the 14:25 slot independently produced the same successful delivery shape. The learner confirmed answering both. `last_fired` persisted as `2026-11-16 14:25:17...`, with count 3 and the custom 08:00–22:00 window preserved. This closes the original symptom and its real acceptance requirement.

`/close` also really rotates working memory: session `d547ec207188` became COMPLETE at 23:35:22Z after 33 turns/$8.9158; `b7848802d301` was created OPEN at 23:35:23Z with 0 turns/$0. The close appended six Postgres evidence events, regenerated the generated current-state view, updated learner/decision docs, and wrote `2026-11-16-ping-recall.md` + `NEXT-BOOT.md`. Evidence no longer needs one Markdown file per event; curated session narrative, learner/decision changes, generated views, and handoffs still belong in Git, with the nightly export/commit/push outside Pi's write path.

End-of-day cleanup exposed that nightly snapshot/push had NOT kept up: dedicated Teaching lacked the hub-only data-platform env file, and its working tree was behind our documentation merges with live close changes uncommitted. The guarded recovery moves export into the already-configured Teaching container and uses a Teaching-only SSH deploy key for publish, preserving the Postgres source and existing close files. Final snapshot/push VERIFIED: export reported 211 events/26 nodes, SHA-256 `0a6219b97e5a1f9ba565226ae0e2d4a2a532c3bb7c48fa6dee94deb081db4818`. Snapshot `c41d234` committed all close/session files. The reviewed merge `a3b1a68` preserved BOTH the 11-15 live entries and 11-16 reviewed entries in the two text conflicts; the Teaching-only deploy-key push returned 0 and the server KB ended clean on origin/main. No evidence was rewritten.
