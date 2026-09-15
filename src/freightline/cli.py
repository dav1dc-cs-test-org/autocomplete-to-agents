"""Command line interface.

    freightline carriers
    freightline quote --carrier atlas --service ground --from 94105 --to 10001 --weight 2.5 ...
    freightline ship  ... --reference PO-4471
    freightline track <shipment-id>
    freightline report
    freightline migrate

Stdlib only: the CLI has to work in a container that does not have the ``api``
extra installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation

from . import __version__
from .carriers import all_carriers, get_carrier
from .config import get_settings
from .errors import FreightlineError
from .models import Address, Parcel, QuoteRequest, ServiceLevel
from .reporting import summarize_by_carrier, summarize_by_status
from .service import FreightlineService
from .storage.db import apply_migrations, connect
from .storage.repository import SearchFilters

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_DOMAIN_ERROR = 3


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a number") from exc


def _open_service(args: argparse.Namespace) -> FreightlineService:
    path = args.db or get_settings().database_path
    conn = connect(path)
    apply_migrations(conn)
    return FreightlineService(conn)


def _address(postal_code: str, *, residential: bool = False, country: str = "US") -> Address:
    """A rating-only address: the engine needs the postal code and country."""
    return Address(
        line1="-",
        city="-",
        region="-",
        postal_code=postal_code,
        country=country,
        residential=residential,
    )


def _build_request(args: argparse.Namespace) -> QuoteRequest:
    parcel = Parcel(
        weight_kg=args.weight,
        length_cm=args.length,
        width_cm=args.width,
        height_cm=args.height,
    )
    return QuoteRequest(
        origin=_address(getattr(args, "from"), country=args.origin_country),
        destination=_address(
            args.to, residential=args.residential, country=args.destination_country
        ),
        parcel=parcel,
        carrier_code=args.carrier,
        service=ServiceLevel(args.service),
        currency=args.currency,
        saturday_delivery=args.saturday,
    )


def _add_quote_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--carrier", required=True, help="carrier code, e.g. atlas")
    parser.add_argument(
        "--service", required=True, choices=[s.value for s in ServiceLevel], help="service level"
    )
    parser.add_argument("--from", required=True, metavar="POSTAL", help="origin postal code")
    parser.add_argument("--to", required=True, metavar="POSTAL", help="destination postal code")
    parser.add_argument("--weight", required=True, type=_decimal, metavar="KG")
    parser.add_argument("--length", default=Decimal("30"), type=_decimal, metavar="CM")
    parser.add_argument("--width", default=Decimal("20"), type=_decimal, metavar="CM")
    parser.add_argument("--height", default=Decimal("15"), type=_decimal, metavar="CM")
    parser.add_argument("--origin-country", default="US")
    parser.add_argument("--destination-country", default="US")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--residential", action="store_true", help="deliver to a home address")
    parser.add_argument("--saturday", action="store_true", help="request Saturday delivery")


def cmd_carriers(args: argparse.Namespace) -> int:
    print(f"{'CODE':<10} {'NAME':<16} {'SERVICES':<34} INTL  SAT")
    for carrier in all_carriers():
        profile = carrier.profile
        services = ", ".join(service.value for service in profile.services)
        intl = "yes" if profile.supports_international else "no"
        sat = "yes" if profile.supports_saturday_delivery else "no"
        print(f"{profile.code:<10} {profile.name:<16} {services:<34} {intl:<5} {sat}")
    return EXIT_OK


def cmd_quote(args: argparse.Namespace) -> int:
    service = _open_service(args)
    priced = service.quote(_build_request(args))

    if args.format == "json":
        print(
            json.dumps(
                {
                    "carrier_code": priced.carrier_code,
                    "service": priced.service.value,
                    "zone": priced.zone,
                    "billable_weight_kg": f"{priced.billable_weight_kg:.2f}",
                    "currency": priced.currency,
                    "lines": [
                        {
                            "code": line.code,
                            "label": line.label,
                            "amount": f"{line.amount.amount:.2f}",
                            "kind": line.kind,
                        }
                        for line in priced.lines
                    ],
                    "total": f"{priced.total.amount:.2f}",
                }
            )
        )
        return EXIT_OK

    print(f"{priced.carrier_code} / {priced.service.value}")
    print(f"zone {priced.zone}, billable {priced.billable_weight_kg} kg")
    print("-" * 46)
    for line in priced.lines:
        print(f"  {line.label:<30} {str(line.amount.amount):>10}")
    print("-" * 46)
    print(f"  {'TOTAL':<30} {str(priced.total.amount):>10} {priced.currency}")
    return EXIT_OK


def cmd_ship(args: argparse.Namespace) -> int:
    service = _open_service(args)
    shipment = service.create_shipment(_build_request(args), reference=args.reference)
    print(f"created  {shipment.id}")
    print(f"tracking {shipment.tracking_number}")
    print(f"total    {shipment.total.amount} {shipment.currency}")
    return EXIT_OK


def cmd_track(args: argparse.Namespace) -> int:
    service = _open_service(args)
    shipment = service.get(args.shipment_id)
    carrier = get_carrier(shipment.carrier_code)
    print(f"{shipment.tracking_number}  ({carrier.profile.name})")
    print(f"status: {shipment.status.value}")
    events = service.repo.events_for(shipment.id)
    if not events:
        print("  no scan events yet")
    for event in events:
        where = f"  {event.location}" if event.location else ""
        print(f"  {event.occurred_at.isoformat()}  {event.status.value:<18}{event.description}{where}")
    return EXIT_OK


def cmd_report(args: argparse.Namespace) -> int:
    service = _open_service(args)
    shipments = service.repo.search(SearchFilters(), limit=args.limit)
    if not shipments:
        print("no shipments recorded")
        return EXIT_OK

    print(f"{'CARRIER':<10} {'COUNT':>6} {'TOTAL':>12} {'AVG':>10} {'EXC%':>7}")
    for summary in summarize_by_carrier(shipments):
        print(
            f"{summary.carrier_code:<10} {summary.shipment_count:>6} "
            f"{str(summary.total.amount):>12} {str(summary.average.amount):>10} "
            f"{summary.exception_rate * 100:>6.2f}%"
        )
    print()
    for status, count in summarize_by_status(shipments).items():
        print(f"  {status:<18} {count}")
    return EXIT_OK


def cmd_migrate(args: argparse.Namespace) -> int:
    path = args.db or get_settings().database_path
    conn = connect(path)
    applied = apply_migrations(conn)
    if applied:
        for version in applied:
            print(f"applied {version}")
    else:
        print("database is up to date")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="freightline", description="Freightline operations CLI")
    parser.add_argument("--version", action="version", version=f"freightline {__version__}")
    parser.add_argument("--db", default=None, help="path to the SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("carriers", help="list configured carriers").set_defaults(
        handler=cmd_carriers
    )

    quote_parser = subparsers.add_parser("quote", help="price a parcel without booking it")
    _add_quote_arguments(quote_parser)
    quote_parser.add_argument("--format", choices=("table", "json"), default="table")
    quote_parser.set_defaults(handler=cmd_quote)

    ship_parser = subparsers.add_parser("ship", help="book a shipment")
    _add_quote_arguments(ship_parser)
    ship_parser.add_argument("--reference", default=None, help="your order or PO reference")
    ship_parser.set_defaults(handler=cmd_ship)

    track_parser = subparsers.add_parser("track", help="show a shipment and its scan history")
    track_parser.add_argument("shipment_id")
    track_parser.set_defaults(handler=cmd_track)

    report_parser = subparsers.add_parser("report", help="spend and exception summary")
    report_parser.add_argument("--limit", type=int, default=200)
    report_parser.set_defaults(handler=cmd_report)

    subparsers.add_parser("migrate", help="apply pending database migrations").set_defaults(
        handler=cmd_migrate
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except FreightlineError as exc:
        print(f"error [{exc.code}]: {exc.message}", file=sys.stderr)
        if exc.details:
            print(f"  details: {exc.details}", file=sys.stderr)
        return EXIT_DOMAIN_ERROR


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
