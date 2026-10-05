"""Environment-based application configuration.

The agent's display name is configuration, not code — renaming the agent
across the project's lifetime is a .env edit, never a refactor.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigurationError(ValueError):
    """Raised when deployment configuration is missing or unsafe."""


@dataclass(frozen=True, slots=True)
class Settings:
    agent_name: str
    discord_channel_id: int
    discord_allowed_user_id: int
    hub_url: str
    callback_host: str
    callback_port: int
    callback_url: str
    avatar_url: str | None
    test_mode: bool
    log_level: str
    knowledge_root: Path
    pi_executable: str
    pi_session_directory: Path
    pi_model: str | None
    pi_timeout_seconds: int
    recall_pings_enabled: bool
    text_require_address: bool
    lesson_state_file: Path
    recall_check_interval_seconds: int
    lecture_public_url: str
    lecture_tts: str
    voice_enabled: bool
    voice_autojoin: bool
    voice_transport: str
    voice_bridge_url: str
    voice_stt_provider: str
    voice_tts_provider: str
    voice_tts_voice_id: str
    voice_tts_model_id: str
    voice_post_transcript: bool
    voice_filler_dir: Path
    voice_ptt_token: str
    deepgram_api_key: str
    elevenlabs_api_key: str

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        *,
        env_file: Path | str | None = ".env",
    ) -> Settings:
        if environment is None:
            if env_file is not None:
                load_dotenv(dotenv_path=env_file, override=False)
            environment = os.environ

        agent_name = environment.get("TEACHING_AGENT_NAME", "Teaching Agent").strip()
        channel_id = _required_positive_int(environment, "DISCORD_CHANNEL_ID")
        user_id = _required_positive_int(environment, "DISCORD_ALLOWED_USER_ID")
        hub_url = environment.get("TEACHING_AGENT_HUB_URL", "http://localhost:8100").strip()
        callback_host = environment.get("TEACHING_AGENT_CALLBACK_HOST", "127.0.0.1").strip()
        callback_port = _positive_int_with_default(
            environment, "TEACHING_AGENT_CALLBACK_PORT", default=9200
        )
        callback_url = environment.get("TEACHING_AGENT_CALLBACK_URL", "").strip()
        if not callback_url:
            callback_url = f"http://localhost:{callback_port}/discord"
        avatar_url = environment.get("TEACHING_AGENT_AVATAR_URL", "").strip() or None
        test_mode = _parse_bool(environment.get("TEACHING_AGENT_TEST_MODE", "true"))
        log_level = environment.get("TEACHING_AGENT_LOG_LEVEL", "INFO").strip().upper()
        knowledge_root = Path(
            environment.get("TEACHING_AGENT_KNOWLEDGE_ROOT", ".").strip() or "."
        ).resolve()
        pi_executable = environment.get("TEACHING_AGENT_PI_EXECUTABLE", "pi").strip()
        pi_session_directory = Path(
            environment.get(
                "TEACHING_AGENT_PI_SESSION_DIRECTORY", "data/pi-sessions"
            ).strip()
        )
        pi_model = environment.get("TEACHING_AGENT_PI_MODEL", "").strip() or None
        pi_timeout_seconds = _positive_int_with_default(
            environment, "TEACHING_AGENT_PI_TIMEOUT_SECONDS", default=300
        )
        recall_pings_enabled = _parse_bool(
            environment.get("TEACHING_AGENT_RECALL_PINGS_ENABLED", "false")
        )
        text_require_address = _parse_bool(
            environment.get("TEACHING_AGENT_TEXT_REQUIRE_ADDRESS", "true")
        )
        lesson_state_file = Path(
            environment.get(
                "TEACHING_AGENT_LESSON_STATE_FILE", "data/lesson-state.json"
            ).strip()
            or "data/lesson-state.json"
        )
        recall_check_interval_seconds = _positive_int_with_default(
            environment, "TEACHING_AGENT_RECALL_CHECK_INTERVAL_SECONDS", default=3600
        )
        # Where generated lecture audio is linked from. The file is served by
        # this agent's own callback server; the default only works on this
        # machine — set the LAN/Tailscale URL for phone listening.
        lecture_public_url = environment.get(
            "TEACHING_AGENT_LECTURE_PUBLIC_URL", ""
        ).strip()
        if not lecture_public_url:
            lecture_public_url = f"http://{callback_host}:{callback_port}"
        lecture_tts = environment.get(
            "TEACHING_AGENT_LECTURE_TTS", "elevenlabs"
        ).strip()
        if lecture_tts not in ("elevenlabs", "edge"):
            raise ConfigurationError(
                "TEACHING_AGENT_LECTURE_TTS must be 'elevenlabs' or 'edge'."
            )
        voice_enabled = _parse_bool(environment.get("TEACHING_AGENT_VOICE_ENABLED", "false"))
        voice_autojoin = _parse_bool(
            environment.get("TEACHING_AGENT_VOICE_AUTOJOIN", "true")
        )
        voice_transport = environment.get(
            "TEACHING_AGENT_VOICE_TRANSPORT", "discord"
        ).strip()
        if voice_transport not in ("discord", "bridge"):
            raise ConfigurationError(
                "TEACHING_AGENT_VOICE_TRANSPORT must be 'discord' or 'bridge'."
            )
        voice_bridge_url = environment.get(
            "TEACHING_AGENT_VOICE_BRIDGE_URL", "http://localhost:8200"
        ).strip()
        voice_stt_provider = environment.get("TEACHING_AGENT_VOICE_STT", "deepgram").strip()
        voice_tts_provider = environment.get("TEACHING_AGENT_VOICE_TTS", "elevenlabs").strip()
        voice_tts_voice_id = environment.get("TEACHING_AGENT_VOICE_TTS_VOICE_ID", "").strip()
        voice_tts_model_id = environment.get(
            "TEACHING_AGENT_VOICE_TTS_MODEL", "eleven_turbo_v2_5"
        ).strip()
        voice_post_transcript = _parse_bool(
            environment.get("TEACHING_AGENT_VOICE_POST_TRANSCRIPT", "true")
        )
        voice_filler_dir = Path(
            environment.get("TEACHING_AGENT_VOICE_FILLER_DIR", "out/fillers").strip()
            or "out/fillers"
        )
        voice_ptt_token = environment.get("TEACHING_AGENT_VOICE_PTT_TOKEN", "").strip()
        deepgram_api_key = environment.get("DEEPGRAM_API_KEY", "").strip()
        elevenlabs_api_key = environment.get("ELEVENLABS_API_KEY", "").strip()
        if voice_enabled and not deepgram_api_key:
            raise ConfigurationError("DEEPGRAM_API_KEY is required when voice is enabled.")
        if voice_enabled and not elevenlabs_api_key:
            raise ConfigurationError("ELEVENLABS_API_KEY is required when voice is enabled.")
        if voice_enabled and not voice_tts_voice_id:
            raise ConfigurationError(
                "TEACHING_AGENT_VOICE_TTS_VOICE_ID is required when voice is enabled."
            )

        if log_level not in _VALID_LOG_LEVELS:
            raise ConfigurationError(
                f"TEACHING_AGENT_LOG_LEVEL must be one of {sorted(_VALID_LOG_LEVELS)}."
            )
        if not agent_name:
            raise ConfigurationError("TEACHING_AGENT_NAME cannot be empty.")
        if not pi_executable:
            raise ConfigurationError("TEACHING_AGENT_PI_EXECUTABLE cannot be empty.")

        return cls(
            agent_name=agent_name,
            discord_channel_id=channel_id,
            discord_allowed_user_id=user_id,
            hub_url=hub_url,
            callback_host=callback_host,
            callback_port=callback_port,
            callback_url=callback_url,
            avatar_url=avatar_url,
            test_mode=test_mode,
            log_level=log_level,
            knowledge_root=knowledge_root,
            pi_executable=pi_executable,
            pi_session_directory=pi_session_directory,
            pi_model=pi_model,
            pi_timeout_seconds=pi_timeout_seconds,
            recall_pings_enabled=recall_pings_enabled,
            text_require_address=text_require_address,
            lesson_state_file=lesson_state_file,
            recall_check_interval_seconds=recall_check_interval_seconds,
            lecture_public_url=lecture_public_url,
            lecture_tts=lecture_tts,
            voice_enabled=voice_enabled,
            voice_autojoin=voice_autojoin,
            voice_transport=voice_transport,
            voice_bridge_url=voice_bridge_url,
            voice_stt_provider=voice_stt_provider,
            voice_tts_provider=voice_tts_provider,
            voice_tts_voice_id=voice_tts_voice_id,
            voice_tts_model_id=voice_tts_model_id,
            voice_post_transcript=voice_post_transcript,
            voice_filler_dir=voice_filler_dir,
            voice_ptt_token=voice_ptt_token,
            deepgram_api_key=deepgram_api_key,
            elevenlabs_api_key=elevenlabs_api_key,
        )


def _required_positive_int(environment: Mapping[str, str], name: str) -> int:
    raw_value = environment.get(name, "").strip()
    if not raw_value:
        raise ConfigurationError(f"{name} is required.")
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be positive.")
    return value


def _positive_int_with_default(
    environment: Mapping[str, str], name: str, *, default: int
) -> int:
    raw_value = environment.get(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be positive.")
    return value


def _parse_bool(raw_value: str) -> bool:
    return raw_value.strip().lower() in _TRUE_VALUES
