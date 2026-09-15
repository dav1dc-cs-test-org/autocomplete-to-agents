"""Runtime configuration, read once from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB_PATH = Path("var") / "freightline.db"
MAX_PAGE_SIZE = 200


@dataclass(frozen=True)
class Settings:
    database_path: Path = DEFAULT_DB_PATH
    webhook_secret: str = ""
    admin_token: str = ""
    default_currency: str = "USD"
    carrier_timeout_seconds: float = 5.0
    max_page_size: int = MAX_PAGE_SIZE

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        source = env if env is not None else dict(os.environ)
        return cls(
            database_path=Path(source.get("FREIGHTLINE_DB", str(DEFAULT_DB_PATH))),
            webhook_secret=source.get("FREIGHTLINE_WEBHOOK_SECRET", ""),
            admin_token=source.get("FREIGHTLINE_ADMIN_TOKEN", ""),
            default_currency=source.get("FREIGHTLINE_CURRENCY", "USD"),
            carrier_timeout_seconds=float(source.get("FREIGHTLINE_CARRIER_TIMEOUT", "5.0")),
            max_page_size=int(source.get("FREIGHTLINE_MAX_PAGE_SIZE", str(MAX_PAGE_SIZE))),
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reset_settings() -> None:
    """Drop the cached settings. Used by tests and by the CLI when --db is passed."""
    global _settings
    _settings = None
