"""Domain error hierarchy.

Every error carries a stable ``code`` so the HTTP layer and the CLI can map
failures without string-matching messages.
"""

from __future__ import annotations


class FreightlineError(Exception):
    """Base class for every error raised by this package."""

    code = "freightline_error"
    http_status = 500

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code, "message": self.message, "details": self.details}


class ValidationError(FreightlineError):
    code = "validation_error"
    http_status = 422


class UnknownCarrierError(FreightlineError):
    code = "unknown_carrier"
    http_status = 404


class UnsupportedServiceError(FreightlineError):
    code = "unsupported_service"
    http_status = 422


class RateUnavailableError(FreightlineError):
    code = "rate_unavailable"
    http_status = 422


class ShipmentNotFoundError(FreightlineError):
    code = "shipment_not_found"
    http_status = 404


class SignatureVerificationError(FreightlineError):
    code = "signature_verification_failed"
    http_status = 401


class CarrierUnavailableError(FreightlineError):
    """Raised when an upstream carrier integration fails after retries."""

    code = "carrier_unavailable"
    http_status = 502
