# Deployment notes (for the VPS session)

Everything here is portable by design: localhost HTTP between processes,
env-var configuration, relative data paths. Moving to a VPS is assembly,
not redesign.

## Topology

Three repos, two long-running processes, one Discord connection:

```text
Discord ⇄ discord-hub (owns the bot connection; HTTP API :8100)
              ⇅ localhost HTTP (or LAN/private IP on the VPS)
          teaching-agent (callback :9200; spawns pi RPC subprocess)
              ⇅ file tools
          teaching-agent repo working copy (the knowledge base)
socratic-partner (callback :9100) — independent, same hub
```

automation-harness is a library installed into each app, not a process.

## Order of operations

1. Python 3.11+, `git`, and `pi` (the CLI harness) installed; pi's model
   provider configured (OpenRouter key in pi's own config — the agent
   inherits it).
2. Clone `automation-harness`, `discord-hub`, `teaching-agent`
   (and `socratic-partner` if deployed).
3. Per app: `pip install -e ../automation-harness && pip install -e .`,
   write `.env` from `.env.example`.
4. Start discord-hub first (teaching-agent registers with it at startup).
5. Start teaching-agent. Verify: `GET localhost:8100/health`,
   `GET localhost:9200/health`, then a Discord message round-trip.

## Environment deltas vs. local dev

- `TEACHING_AGENT_HUB_URL` — stays localhost if both processes share the
  VPS; otherwise the hub's private address.
- `TEACHING_AGENT_CALLBACK_URL` — must be reachable FROM the hub process;
  on one host the default localhost URL is correct.
- `TEACHING_AGENT_PI_EXECUTABLE` — absolute path to pi on the VPS.
- Firewall: no inbound ports need exposing. All traffic is outbound
  (Discord gateway, model API) plus localhost HTTP.

## Data that must survive redeploys

- The repo working copy: `docs/`, `maps/`, `sessions/`, `lessons/` ARE the
  knowledge base. The agent git-commits at session close; push to origin
  is the backup. (Consider a periodic `git push` cron until pushes are
  automatic.)
- `data/` (pi sessions, harness state) — disposable; recreate freely.

## Known follow-ups

- Process supervision on the VPS: the harness handles app-level recovery;
  OS-level autostart (systemd units per app) is the deploy session's call.
- Multi-client hub operation is unverified — see
  `docs/integrations/discord-hub.md` §6; verify before socratic-partner
  and teaching-agent run side by side.
