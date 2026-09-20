"""Environment-boundary configuration. Do not read os.environ elsewhere."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"
DEFAULT_PORT = 8000
DEFAULT_LOG_LEVEL = "info"
DEFAULT_DATABASE_PATH = "data/hn.db"


@dataclass(frozen=True)
class Settings:
    database_path: str
    port: int
    log_level: str
    hn_base_url: str


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    env = environ if environ is not None else os.environ
    port_raw = env.get("PORT", str(DEFAULT_PORT))
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError(f"PORT must be an integer, got {port_raw!r}") from exc
    if port < 1 or port > 65535:
        raise ValueError(f"PORT must be in 1..65535, got {port}")
    return Settings(
        database_path=env.get("DATABASE_PATH", DEFAULT_DATABASE_PATH),
        port=port,
        log_level=env.get("LOG_LEVEL", DEFAULT_LOG_LEVEL),
        hn_base_url=env.get("HN_BASE_URL", DEFAULT_HN_BASE_URL).rstrip("/"),
    )
