"""Entry point: runs the teaching agent inside the automation-harness,
which owns the lifecycle — single-instance lock, graceful shutdown,
supervision with restart, structured logs, status.json.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress

import uvicorn
from automation_harness import Harness, HarnessConfig, ServiceContext

from .callback_server import create_callback_app
from .config import Settings
from .engine import TeachingEngine, build_system_prompt
from .hub_client import HubClient
from .pi_rpc import PiRpcClient
from .voice.ptt import RemotePTT
from .voice.runtime import VoiceRuntime

logger = logging.getLogger(__name__)


def build_engine(settings: Settings) -> TeachingEngine:
    hub = HubClient(settings.hub_url)
    pi = PiRpcClient(
        executable=settings.pi_executable,
        working_directory=settings.knowledge_root,
        session_directory=settings.pi_session_directory,
        session_name=settings.agent_name.lower().replace(" ", "-"),
        model=settings.pi_model,
        system_prompt=build_system_prompt(settings, test_mode=settings.test_mode),
        timeout_seconds=settings.pi_timeout_seconds,
    )
    engine = TeachingEngine(settings, hub, pi)
    if settings.voice_enabled:
        # Remote PTT is an out-of-band turn boundary needed only because
        # Discord hides the learner's PTT key state; the bridge delivers
        # exact press/release edges inside the voice stream itself.
        remote_ptt = (
            RemotePTT() if settings.voice_transport == "discord" else None
        )
        engine.remote_ptt = remote_ptt
        engine.set_voice(
            VoiceRuntime(
                settings,
                hub,
                ask_pi=engine.ask_pi,
                transcript=(
                    engine.transcript_sink()
                    if settings.voice_post_transcript
                    else None
                ),
                remote_ptt=remote_ptt,
            )
        )
    return engine


async def agent_service(ctx: ServiceContext) -> None:
    """The agent as a harness-supervised service: runs until the harness
    requests shutdown via ctx.stop_event."""
    settings = Settings.from_environment()
    engine = build_engine(settings)
    await engine.start()

    app = create_callback_app(
        engine.dispatch,
        remote_ptt=getattr(engine, "remote_ptt", None),
        ptt_token=settings.voice_ptt_token,
    )
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=settings.callback_host,
            port=settings.callback_port,
            log_level=settings.log_level.lower(),
        )
    )

    async def recall_loop() -> None:
        while not ctx.stop_event.is_set():
            try:
                await engine.recall_tick()
            except Exception:
                logger.exception("Recall tick failed; will retry next interval.")
            with suppress(TimeoutError):
                await asyncio.wait_for(
                    ctx.stop_event.wait(), timeout=settings.recall_check_interval_seconds
                )

    async def shutdown_when_asked() -> None:
        await ctx.stop_event.wait()
        logger.info("shutdown requested by harness")
        server.should_exit = True

    logger.info(
        "Starting teaching agent callback on %s:%s",
        settings.callback_host,
        settings.callback_port,
    )
    tasks = [
        asyncio.create_task(server.serve()),
        asyncio.create_task(shutdown_when_asked()),
    ]
    if settings.recall_pings_enabled:
        tasks.append(asyncio.create_task(recall_loop()))
    await asyncio.gather(*tasks)


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("TEACHING_AGENT_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    harness = Harness(HarnessConfig(data_dir="data"), name="teaching-agent")
    harness.add_service("teaching-agent", agent_service)
    harness.run()  # async runtime: harness owns the event loop


if __name__ == "__main__":
    main()
