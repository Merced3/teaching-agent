"""Fetch Discord channel/thread history via discord-hub, newest-first pages
reassembled chronologically and filtered by a local-time lower bound.

Read-only diagnostics — the hub keeps no history itself; this paginates
GET /channels/{id}/history (threads are read as their own channel ids).

Usage (always with the venv interpreter):

    ./.venv/Scripts/python scripts/fetch_history.py 1234567890 --after "2026-10-09 12:00"
    ./.venv/Scripts/python scripts/fetch_history.py 111 222 333 --after "2026-10-09 12:00" --json out.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows cp1252 console

HUB = os.environ.get("DISCORD_HUB_URL", "http://localhost:8100")
PAGE = 100


async def history(client: httpx.AsyncClient, channel_id: str, after: datetime) -> list[dict]:
    """All messages in one channel/thread at or after `after` (aware dt)."""
    kept: list[dict] = []
    before: str | None = None
    while True:
        params: dict[str, str | int] = {"limit": PAGE}
        if before:
            params["before"] = before
        resp = await client.get(f"{HUB}/channels/{channel_id}/history", params=params)
        resp.raise_for_status()
        body = resp.json()
        messages = body.get("messages", [])
        for msg in messages:
            ts = datetime.fromisoformat(msg["created_at"])
            if ts >= after:
                kept.append(msg)
        # Pages are newest-first; stop when the page ran older than `after`.
        oldest_is_before_cutoff = messages and (
            datetime.fromisoformat(messages[-1]["created_at"]) < after
        )
        next_before = body.get("next_before")
        if not next_before or oldest_is_before_cutoff:
            break
        before = next_before
    kept.sort(key=lambda m: m["created_at"])
    return kept


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("channels", nargs="+", help="channel or thread ids")
    parser.add_argument(
        "--after",
        required=True,
        help='local-time lower bound, e.g. "2026-10-09 12:00"',
    )
    parser.add_argument("--json", help="also write the raw result to this file")
    args = parser.parse_args()

    naive = datetime.fromisoformat(args.after)
    after = naive.astimezone()  # interpret as local time -> aware

    async with httpx.AsyncClient(timeout=30) as client:
        result: dict[str, list[dict]] = {}
        for channel_id in args.channels:
            result[channel_id] = await history(client, channel_id, after)

    for channel_id, messages in result.items():
        print(f"\n===== {channel_id} — {len(messages)} message(s) since {after} =====")
        for msg in messages:
            author = msg.get("author") or {}
            name = author.get("name", "?")
            bot = " [bot]" if author.get("bot") else ""
            ts = msg["created_at"][:19].replace("T", " ")
            text = (msg.get("text") or "").replace("\n", "\n    ")
            print(f"[{ts}] {name}{bot} ({msg['id']}):\n    {text}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"\nraw JSON -> {args.json}")


if __name__ == "__main__":
    asyncio.run(main())
