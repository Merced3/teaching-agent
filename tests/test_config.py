"""Black-box tests for configuration parsing — the failure mode that stops
the agent from booting is worth pinning; internals are not."""

from __future__ import annotations

import pytest

from teaching_agent.config import ConfigurationError, Settings

BASE_ENV = {
    "DISCORD_CHANNEL_ID": "1542316428193964032",
    "DISCORD_ALLOWED_USER_ID": "42",
}


def make_settings(extra: dict[str, str] | None = None) -> Settings:
    env = {**BASE_ENV, **(extra or {})}
    return Settings.from_environment(env, env_file=None)


def test_minimal_env_uses_safe_defaults() -> None:
    settings = make_settings()
    assert settings.discord_channel_id == 1542316428193964032
    assert settings.agent_name == "Teaching Agent"
    assert settings.test_mode is True
    assert settings.recall_pings_enabled is False
    assert settings.callback_port == 9200
    assert settings.callback_url == "http://localhost:9200/discord"


def test_agent_name_is_configuration() -> None:
    settings = make_settings({"TEACHING_AGENT_NAME": "Aristotle"})
    assert settings.agent_name == "Aristotle"


def test_missing_channel_id_fails_loudly() -> None:
    with pytest.raises(ConfigurationError):
        Settings.from_environment({"DISCORD_ALLOWED_USER_ID": "42"}, env_file=None)


def test_recall_pings_are_opt_in() -> None:
    settings = make_settings({"TEACHING_AGENT_RECALL_PINGS_ENABLED": "true"})
    assert settings.recall_pings_enabled is True
