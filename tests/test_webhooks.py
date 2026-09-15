from __future__ import annotations

from datetime import timedelta

import pytest

from freightline.errors import SignatureVerificationError
from freightline.tracking.webhooks import compute_signature, verify_signature, verify_timestamp
from freightline.util.dates import to_iso8601, utcnow

SECRET = "s3cret-rotating-value"
BODY = b'{"shipment_id":"abc","status":"DELIVERED"}'


def test_a_correct_signature_verifies():
    verify_signature(SECRET, BODY, compute_signature(SECRET, BODY))


def test_a_tampered_body_is_rejected():
    signature = compute_signature(SECRET, BODY)
    with pytest.raises(SignatureVerificationError):
        verify_signature(SECRET, BODY + b" ", signature)


def test_a_signature_from_a_different_secret_is_rejected():
    with pytest.raises(SignatureVerificationError):
        verify_signature(SECRET, BODY, compute_signature("other-secret", BODY))


def test_a_missing_signature_is_rejected():
    with pytest.raises(SignatureVerificationError):
        verify_signature(SECRET, BODY, "")


def test_an_unconfigured_secret_fails_closed():
    with pytest.raises(SignatureVerificationError):
        verify_signature("", BODY, compute_signature("", BODY))


def test_signature_is_prefixed():
    assert compute_signature(SECRET, BODY).startswith("sha256=")


def test_a_fresh_timestamp_is_accepted():
    verify_timestamp(to_iso8601(utcnow()))


def test_a_stale_timestamp_is_rejected():
    stale = to_iso8601(utcnow() - timedelta(hours=2))
    with pytest.raises(SignatureVerificationError):
        verify_timestamp(stale)


def test_a_future_timestamp_is_rejected():
    future = to_iso8601(utcnow() + timedelta(hours=2))
    with pytest.raises(SignatureVerificationError):
        verify_timestamp(future)
