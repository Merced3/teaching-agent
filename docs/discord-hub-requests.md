# Requests for discord-hub (from consuming projects)

Hand this file to a discord-hub session. Every request is written agnostically:
the hub serves any project; no teaching-agent or socratic-partner concept
appears in the contracts. Reasons and example consumers are given so the hub
session can judge the design, not just the ask.

Principle the hub already follows, restated for alignment: the hub owns the
Discord connection and Discord primitives. Projects own their own databases,
their own session/thread meaning, and their own cleanup logic. The hub must
never need to know what a "session" or a "lesson" is.

---

## 1. Voice foundation (already on the hub roadmap as next-up #2)

- `POST /voice/join` — join a voice channel.
- `POST /voice/leave` — leave it.
- `POST /voice/play` — play an audio file into the channel.

**Reason:** any project that wants to speak (audio lessons, voice agents,
notifications) needs exactly this. Consumer: teaching-agent (voice lessons).
Potential consumer: socratic-partner (spoken dialogues).

## 2. Bidirectional streaming audio (design the transport for this from the start)

Join/leave/play covers outbound audio. Inbound (hearing the user) should be
designed as a **stream**, not as "record a segment, POST a file":

- Hub captures per-speaker audio and streams chunks to the registered project
  (e.g. a websocket between hub and project).
- The project streams outbound audio back over the same connection.

**Reason:** a file-drop interface permanently caps consumers at
record→transcribe→respond latency. A streaming transport supports BOTH
architectures a consumer might choose: a staged pipeline
(speech-to-text → model → text-to-speech, fed utterance-sized pieces) and,
later, a real-time speech-to-speech model bridged straight to Discord.
Consumers that only want utterances can buffer the stream themselves; the
reverse is not true of file-drop. Consumer: teaching-agent (voice
conversation). Any future voice project benefits identically.

## 3. Speaking activity events

When a user starts/stops speaking in a voice channel the project is joined
to, push an event to the project's callback:
`{ "type": "speaking", "user_id": "...", "state": "started" | "stopped" }`.

**Reason:** interruption. A consumer cannot implement "stop talking, the
human is speaking" without knowing that speaking started. Interruption is
the difference between a lecture and a conversation. Consumer:
teaching-agent (confirmed learner requirement). Generic to any voice
consumer.

## 4. Channel history export (read-only)

- `GET /channels/{channel_id}/history?limit=N&before=...` → ordered messages
  (author, timestamp, text, attachments metadata) as JSON.

**Reason, threefold:** (a) restructuring safety — Discord cannot move a
channel with its history, so "export before delete/recreate" is the only
way structural changes stay lossless; (b) server backup — the export
primitive is exactly what a periodic backup job needs; (c) data collection —
the server owner wants durable local records of their own Discord activity,
and the hub is the only process with the connection. This likely means
moving "message history/archiving" out of the roadmap's out-of-scope list:
the hub provides the read primitive; a separate tool (not the hub) decides
what to archive and where. Consumer: any project facing a restructure; a
future backup/archiver tool.

## 5. Deletion primitives (for test-session cleanup)

- `DELETE /threads/{thread_id}` (or `POST /threads/{thread_id}/delete`) —
  delete a thread the bot can manage.
- Optionally `DELETE /messages/{channel_id}/{message_id}` — delete a single
  bot/webhook message.

**Reason:** projects run test sessions constantly during development.
Desired flow, owned ENTIRELY by the consuming project: user runs e.g.
`/delete-session` → the project deletes its own database rows and local
state → the project calls the hub to delete the Discord thread. The hub's
part is only the Discord-side deletion primitive; it stays agnostic of what
a session is. Consumers: socratic-partner (requested), teaching-agent
(same pattern), any future project with per-thread state.

---

## Already exists, no work needed

`POST /messages` (chunking, replies, webhook identity), `POST /threads`,
`PUT /commands` (routing, defer, followups), channel registrations with
inbound callbacks and thread inheritance, typing indicators, permission
preflight, harness integration. The teaching-agent's entire text surface is
covered by the current contract.
