"""Inbound webhook authentication.

Carriers sign each delivery with an HMAC over the raw request body. We verify
before parsing, in constant time, and we reject replays outside a tolerance
window.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta

from ..errors import SignatureVerificationError
from ..util.dates import parse_iso8601, utcnow

SIGNATURE_PREFIX = "sha256="
REPLAY_TOLERANCE = timedelta(minutes=5)


def compute_signature(secret: str, body: bytes) -> str:
    """The value a carrier is expected to send in ``X-Freightline-Signature``."""
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def verify_signature(secret: str, body: bytes, signature: str) -> None:
    """Raise :class:`SignatureVerificationError` unless the signature matches."""
    if not secret:
        raise SignatureVerificationError("webhook secret is not configured")
    if not signature:
        raise SignatureVerificationError("missing signature header")

    expected = compute_signature(secret, body)
    if not hmac.compare_digest(expected, signature):
        raise SignatureVerificationError("signature mismatch")


def verify_timestamp(sent_at: str, *, tolerance: timedelta = REPLAY_TOLERANCE) -> None:
    """Reject webhook deliveries that are too old or implausibly future-dated."""
    delta = abs(utcnow() - parse_iso8601(sent_at))
    if delta > tolerance:
        raise SignatureVerificationError(
            "webhook timestamp outside tolerance window",
            details={"skew_seconds": int(delta.total_seconds())},
        )
