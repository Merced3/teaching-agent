"""Black-box tests for the lecture-file serving route: episodes are links,
not uploads, so the callback server must serve them safely."""

from __future__ import annotations

import httpx

from teaching_agent.callback_server import create_callback_app


async def _get(app, path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        return await client.get(path)


async def _dispatch(payload):  # noqa: ANN001, ANN202 — minimal dispatch stub
    return None


async def test_lecture_file_is_served(tmp_path) -> None:
    episode = tmp_path / "crash-proofing"
    episode.mkdir()
    (episode / "lecture.mp3").write_bytes(b"fake-mp3-bytes")
    app = create_callback_app(_dispatch, lectures_dir=tmp_path)
    response = await _get(app, "/lectures/crash-proofing/lecture.mp3")
    assert response.status_code == 200
    assert response.content == b"fake-mp3-bytes"


async def test_missing_lecture_file_is_404(tmp_path) -> None:
    app = create_callback_app(_dispatch, lectures_dir=tmp_path)
    response = await _get(app, "/lectures/nope/lecture.mp3")
    assert response.status_code == 404


async def test_path_traversal_is_rejected(tmp_path) -> None:
    (tmp_path / "secret.txt").write_text("nope", encoding="utf-8")
    served = tmp_path / "lessons"
    served.mkdir()
    app = create_callback_app(_dispatch, lectures_dir=served)
    response = await _get(app, "/lectures/..%2Fsecret.txt")
    assert response.status_code == 404


async def test_lectures_route_absent_without_dir() -> None:
    app = create_callback_app(_dispatch)
    response = await _get(app, "/lectures/x/lecture.mp3")
    assert response.status_code == 404
