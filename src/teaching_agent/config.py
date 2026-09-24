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
    recall_check_interval_seconds: int

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
        recall_check_interval_seconds = _positive_int_with_default(
            environment, "TEACHING_AGENT_RECALL_CHECK_INTERVAL_SECONDS", default=3600
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
            recall_check_interval_seconds=recall_check_interval_seconds,
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
