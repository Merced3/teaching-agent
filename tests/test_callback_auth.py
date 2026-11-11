"""Offline wire tests for authenticated discord-hub callbacks."""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock

import httpx
import pytest

from teaching_agent.callback_server import create_callback_app

TOKEN = "test-project-token"
NOW = 1_700_000_000.0


def _headers(body: bytes, *, timestamp: str | None = None, project: str = "teaching-agent"):
    ts = str(int(NOW)) if timestamp is None else timestamp
    signature = hmac.new(TOKEN.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return {
        "X-Discord-Hub-Timestamp": ts,
        "X-Discord-Hub-Signature": f"v1={signature}",
        "X-Discord-Hub-Project": project,
        "Content-Type": "application/json",
    }


async def _post(app, body: bytes, headers: dict[str, str] | None = None):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.post("/discord", content=body, headers=headers or {})


def _app(dispatch: AsyncMock):
    return create_callback_app(dispatch, TOKEN, now=lambda: NOW)


async def test_valid_exact_raw_body_dispatches_once() -> None:
    dispatch = AsyncMock(return_value={"text": "ok"})
    body = b'{ "type": "message", "text": "hello" }'
    response = await _post(_app(dispatch), body, _headers(body))
    assert response.status_code == 200
    assert response.json() == {"text": "ok"}
    dispatch.assert_awaited_once_with({"type": "message", "text": "hello"})


async def test_missing_auth_rejected_without_dispatch() -> None:
    dispatch = AsyncMock()
    response = await _post(_app(dispatch), b"{}")
    assert response.status_code == 401
    dispatch.assert_not_awaited()


async def test_forged_signature_rejected_without_dispatch() -> None:
    dispatch = AsyncMock()
    headers = _headers(b"{}") | {"X-Discord-Hub-Signature": "v1=" + "0" * 64}
    response = await _post(_app(dispatch), b"{}", headers)
    assert response.status_code == 401
    dispatch.assert_not_awaited()


async def test_tampered_raw_body_rejected_without_dispatch() -> None:
    dispatch = AsyncMock()
    signed = b'{"text":"original"}'
    response = await _post(_app(dispatch), b'{"text":"tampered"}', _headers(signed))
    assert response.status_code == 401
    dispatch.assert_not_awaited()


async def test_stale_timestamp_rejected_without_dispatch() -> None:
    dispatch = AsyncMock()
    body = b"{}"
    headers = _headers(body, timestamp=str(int(NOW) - 301))
    response = await _post(_app(dispatch), body, headers)
    assert response.status_code == 401
    dispatch.assert_not_awaited()


async def test_wrong_project_rejected_even_with_valid_signature() -> None:
    dispatch = AsyncMock()
    body = b"{}"
    response = await _post(_app(dispatch), body, _headers(body, project="socratic-partner"))
    assert response.status_code == 401
    dispatch.assert_not_awaited()


@pytest.mark.parametrize("timestamp", ["", "not-a-number"])
async def test_invalid_timestamp_rejected_without_dispatch(timestamp: str) -> None:
    dispatch = AsyncMock()
    body = json.dumps({}).encode()
    response = await _post(_app(dispatch), body, _headers(body, timestamp=timestamp))
    assert response.status_code == 401
    dispatch.assert_not_awaited()


async def test_health_remains_public() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_app(AsyncMock())), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
