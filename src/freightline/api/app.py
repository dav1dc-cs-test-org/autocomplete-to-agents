"""FastAPI application factory.

Domain errors carry their own HTTP status and stable error code, so the single
exception handler below is the only place that translates between the two.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .. import __version__
from ..errors import FreightlineError
from . import routes_admin, routes_quotes, routes_shipments

DESCRIPTION = """
Freightline rates, books, and tracks parcel shipments across our carrier panel.

* `POST /v1/quotes` prices a parcel without booking it.
* `POST /v1/shipments` books and returns a tracking number.
* `POST /v1/webhooks/{carrier_code}` accepts signed carrier scan events.
""".strip()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Freightline API",
        version=__version__,
        description=DESCRIPTION,
        openapi_tags=[
            {"name": "rating", "description": "Pricing and carrier capability."},
            {"name": "shipments", "description": "Booking and tracking."},
            {"name": "admin", "description": "Reporting. Requires a bearer token."},
        ],
    )

    @app.exception_handler(FreightlineError)
    async def handle_domain_error(_: Request, exc: FreightlineError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.get("/healthz", tags=["ops"], summary="Liveness probe")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(routes_quotes.router)
    app.include_router(routes_shipments.router)
    app.include_router(routes_admin.router)
    return app


app = create_app()
