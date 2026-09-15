"""Timestamp parsing and formatting.

Every datetime that crosses a module boundary is timezone-aware UTC.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..errors import ValidationError


def parse_iso8601(value: str) -> datetime:
    """Parse an ISO-8601 timestamp into an aware UTC datetime."""
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(
            f"not a valid ISO-8601 timestamp: {value!r}", details={"value": value}
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def to_iso8601(value: datetime) -> str:
    """Render an aware datetime as ``...Z``. Naive inputs are assumed UTC."""
    aware = value if value.tzinfo else value.replace(tzinfo=UTC)
    return aware.astimezone(UTC).isoformat().replace("+00:00", "Z")


def utcnow() -> datetime:
    return datetime.now(UTC)
