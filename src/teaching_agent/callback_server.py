"""Local HTTP endpoint that receives discord-hub deliveries.

The hub POSTs inbound messages and command invocations here. For commands,
the HTTP response IS the Discord interaction response: a dict such as
``{"text": ..., "ephemeral": True}`` or ``{"defer": True, "ephemeral": True}``.
For messages, any 2xx acknowledges delivery.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from .voice.ptt import RemotePTT

Dispatch = Callable[[dict[str, Any]], Awaitable[dict[str, Any] | None]]

_PTT_PAGE = """<!doctype html>
<html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>Alvar PTT</title>
<style>
  body { margin:0; height:100vh; display:flex; flex-direction:column; gap:16px;
         align-items:center; justify-content:center; background:#1e1f22; color:#dbdee1;
         font-family:system-ui,sans-serif; }
  #btn { width:70vw; max-width:320px; aspect-ratio:1; border-radius:50%; border:none;
         font-size:1.4rem; font-weight:600; background:#5865f2; color:white;
         touch-action:none; user-select:none; -webkit-user-select:none; }
  #btn.down { background:#23a55a; }
  #status { opacity:.7; font-size:.9rem; }
</style></head><body>
<button id="btn">Hold to talk</button>
<div id="status">connecting…</div>
<script>
const token = new URLSearchParams(location.search).get("token") || "";
const btn = document.getElementById("btn");
const status = document.getElementById("status");
let down = false;
async function send(state) {
  try {
    const r = await fetch("/voice/ptt", {method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({state, token})});
    status.textContent = r.ok ? (down ? "listening…" : "connected") : "rejected (" + r.status + ")";
  } catch { status.textContent = "unreachable"; }
}
function press(e) { e.preventDefault(); if (!down) { down = true;
  btn.classList.add("down"); btn.textContent = "Talking…"; send("down"); } }
function release(e) { e.preventDefault(); if (down) { down = false;
  btn.classList.remove("down"); btn.textContent = "Hold to talk"; send("up"); } }
btn.addEventListener("pointerdown", press);
addEventListener("pointerup", release);
addEventListener("pointercancel", release);
setInterval(() => fetch("/voice/ptt/heartbeat", {method:"POST",
  headers:{"Content-Type":"application/json"}, body: JSON.stringify({token})}), 3000);
</script></body></html>"""


def create_callback_app(
    dispatch: Dispatch,
    *,
    remote_ptt: RemotePTT | None = None,
    ptt_token: str = "",
) -> FastAPI:
    app = FastAPI(title="teaching-agent-callback")

    def _authorized(payload: dict[str, Any]) -> bool:
        # Empty configured token = local-only trust; set one before the
        # button leaves the LAN (Tailscale/VPS).
        return not ptt_token or payload.get("token") == ptt_token

    @app.post("/discord")
    async def discord_callback(request: Request) -> Response:
        payload = await request.json()
        result = await dispatch(payload)
        if result is None:
            return Response(status_code=204)
        return JSONResponse(result)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    if remote_ptt is not None:

        @app.get("/ptt", response_class=HTMLResponse)
        async def ptt_page() -> HTMLResponse:
            return HTMLResponse(_PTT_PAGE)

        @app.post("/voice/ptt")
        async def ptt_event(request: Request) -> Response:
            payload = await request.json()
            if not _authorized(payload):
                return Response(status_code=403)
            state = payload.get("state")
            if state == "down":
                remote_ptt.press()
            elif state == "up":
                remote_ptt.release()
            else:
                return Response(status_code=400)
            return Response(status_code=204)

        @app.post("/voice/ptt/heartbeat")
        async def ptt_heartbeat(request: Request) -> Response:
            payload = await request.json()
            if not _authorized(payload):
                return Response(status_code=403)
            remote_ptt.heartbeat()
            return Response(status_code=204)

    return app
