"""Remote push-to-talk: an out-of-band turn boundary.

Discord cannot tell a bot when the learner's PTT key is down (client-side
only, by design). So the exact "I'm done" signal comes from a button we
own — a phone web page today, a BLE remote later — POSTing press/release
to the agent's callback server.

This object is the shared state between that HTTP surface and the voice
conversation. Mode selection is presence-based, never a setting: while
heartbeats are fresh the conversation runs in MANUAL mode (button events
draw turn boundaries exactly); when they lapse it falls back to AUTO
(hub speaking events + grace). The device being there IS the mode.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class RemotePTT:
    def __init__(self, *, heartbeat_timeout_seconds: float = 6.0) -> None:
        self._heartbeat_timeout = heartbeat_timeout_seconds
        self._last_heartbeat: float | None = None
        self._pressed = False
        # Wired by the voice conversation; no-ops until a session is live.
        self.on_press: Callable[[], None] = lambda: None
        self.on_release: Callable[[], None] = lambda: None

    @property
    def connected(self) -> bool:
        """A heartbeat within the timeout means the button is in hand."""
        return self._last_heartbeat is not None and (
            time.monotonic() - self._last_heartbeat < self._heartbeat_timeout
        )

    @property
    def pressed(self) -> bool:
        return self._pressed

    def heartbeat(self) -> None:
        self._last_heartbeat = time.monotonic()

    def press(self) -> None:
        self.heartbeat()
        if not self._pressed:
            self._pressed = True
            self.on_press()

    def release(self) -> None:
        self.heartbeat()
        if self._pressed:
            self._pressed = False
            self.on_release()
