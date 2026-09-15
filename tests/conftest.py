from __future__ import annotations

from decimal import Decimal

import pytest

from freightline.models import Address, Parcel, QuoteRequest, ServiceLevel
from freightline.service import FreightlineService
from freightline.storage.db import in_memory
from freightline.storage.repository import ShipmentRepository


@pytest.fixture()
def conn():
    connection = in_memory()
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture()
def repo(conn) -> ShipmentRepository:
    return ShipmentRepository(conn)


@pytest.fixture()
def service(conn) -> FreightlineService:
    return FreightlineService(conn)


@pytest.fixture()
def sf() -> Address:
    return Address(line1="1 Market St", city="San Francisco", region="CA", postal_code="94105")


@pytest.fixture()
def nyc() -> Address:
    return Address(line1="20 W 34th St", city="New York", region="NY", postal_code="10001")


@pytest.fixture()
def nyc_home() -> Address:
    return Address(
        line1="12 Elm St",
        city="Brooklyn",
        region="NY",
        postal_code="11201",
        residential=True,
    )


@pytest.fixture()
def anchorage() -> Address:
    return Address(line1="5 Ice Rd", city="Anchorage", region="AK", postal_code="99501")


@pytest.fixture()
def small_parcel() -> Parcel:
    return Parcel(
        weight_kg=Decimal("2.5"),
        length_cm=Decimal("30"),
        width_cm=Decimal("20"),
        height_cm=Decimal("15"),
    )


@pytest.fixture()
def quote_request(sf, nyc, small_parcel) -> QuoteRequest:
    return QuoteRequest(
        origin=sf,
        destination=nyc,
        parcel=small_parcel,
        carrier_code="atlas",
        service=ServiceLevel.GROUND,
    )
