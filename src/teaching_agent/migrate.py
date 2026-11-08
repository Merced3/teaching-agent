"""Apply the owning Alembic migration without an ini file or logged secrets."""

from __future__ import annotations

import argparse
import os
from configparser import RawConfigParser
from pathlib import Path

from alembic import command
from alembic.config import Config

_MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def upgrade(database: str, database_url: str) -> None:
    if database not in {"teaching", "knowledge"}:
        raise ValueError("database must be teaching or knowledge")
    script_location = _MIGRATIONS / database
    config = Config(configparser=RawConfigParser())
    config.set_main_option("script_location", str(script_location))
    sqlalchemy_url = database_url
    if sqlalchemy_url.startswith("postgresql://"):
        sqlalchemy_url = "postgresql+psycopg://" + sqlalchemy_url.removeprefix("postgresql://")
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)
    command.upgrade(config, "head")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", choices=["teaching", "knowledge"])
    parser.add_argument("--url-env", required=True, help="environment variable holding the URL")
    args = parser.parse_args(argv)
    url = os.environ.get(args.url_env, "").strip()
    if not url:
        parser.error(f"{args.url_env} is required; credentials are never command arguments")
    upgrade(args.database, url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
