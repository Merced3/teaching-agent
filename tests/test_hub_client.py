"""Offline wire tests for Teaching Agent's authenticated hub client."""

from __future__ import annotations

import httpx

from teaching_agent.hub_client import HubClient


async def test_bearer_token_sent_on_health_and_api_requests() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/voice/status":
            return httpx.Response(200, json={"connected": False})
        return httpx.Response(201, json={"id": "message-id"})

    client = HubClient(
        "http://hub.test",
        "test-project-token",
        transport=httpx.MockTransport(handler),
    )
    await client.health()
    await client.post_message(123, "hello")
    await client.voice_status()
    await client.close()

    assert len(requests) == 3
    assert all(
        request.headers.get("Authorization") == "Bearer test-project-token"
        for request in requests
    )


async def test_network_errors_remain_typed() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    client = HubClient(
        "http://hub.test",
        "test-project-token",
        transport=httpx.MockTransport(refuse),
    )
    try:
        await client.health()
    except Exception as exc:
        assert type(exc).__name__ == "HubError"
    else:
        raise AssertionError("Expected HubError")
    await client.close()
