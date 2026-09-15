from __future__ import annotations

import json
from decimal import Decimal

import pytest

from freightline.cli import main


@pytest.fixture()
def db(tmp_path):
    return str(tmp_path / "cli.db")


def run(capsys, *args):
    code = main(list(args))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_carriers_lists_every_registered_carrier(capsys):
    code, out, _ = run(capsys, "carriers")
    assert code == 0
    for carrier_code in ("atlas", "borealis", "pigeon"):
        assert carrier_code in out


def test_migrate_is_idempotent(capsys, db):
    first_code, first_out, _ = run(capsys, "--db", db, "migrate")
    second_code, second_out, _ = run(capsys, "--db", db, "migrate")
    assert first_code == second_code == 0
    assert "0001_initial" in first_out
    assert "up to date" in second_out


@pytest.mark.parametrize("format_args", [(), ("--format", "table")])
def test_quote_table_format_is_unchanged(capsys, db, format_args):
    code, out, _ = run(
        capsys,
        "--db", db,
        "quote",
        "--carrier", "atlas",
        "--service", "ground",
        "--from", "94105",
        "--to", "10001",
        "--weight", "2.5",
        *format_args,
    )
    assert code == 0
    # Atlas zone 7 ground is a $20.00 base plus its configured $3.10 fuel charge.
    assert out == (
        "atlas / ground\n"
        "zone 7, billable 2.50 kg\n"
        "----------------------------------------------\n"
        "  Ground linehaul                     20.00\n"
        "  Fuel surcharge                       3.10\n"
        "----------------------------------------------\n"
        "  TOTAL                               23.10 USD\n"
    )


def test_quote_json_format_prints_the_domain_quote_as_one_object(capsys, db):
    code, out, err = run(
        capsys,
        "--db", db,
        "quote",
        "--carrier", "atlas",
        "--service", "ground",
        "--from", "94105",
        "--to", "10001",
        "--weight", "2.5",
        "--format", "json",
    )

    assert code == 0
    assert err == ""
    quote = json.loads(out)
    assert set(quote) == {
        "carrier_code",
        "service",
        "zone",
        "billable_weight_kg",
        "currency",
        "lines",
        "total",
    }
    assert quote == {
        "carrier_code": "atlas",
        "service": "ground",
        "zone": 7,
        "billable_weight_kg": "2.50",
        "currency": "USD",
        "lines": [
            {"code": "base", "label": "Ground linehaul", "amount": "20.00", "kind": "base"},
            {
                "code": "fuel",
                "label": "Fuel surcharge",
                "amount": "3.10",
                "kind": "surcharge",
            },
        ],
        "total": "23.10",
    }
    assert isinstance(quote["zone"], int)
    assert isinstance(quote["lines"], list)
    assert all(set(line) == {"code", "label", "amount", "kind"} for line in quote["lines"])
    assert Decimal(quote["total"]) == sum(Decimal(line["amount"]) for line in quote["lines"])


def test_quote_reports_a_domain_error_without_a_traceback(capsys, db):
    code, out, err = run(
        capsys,
        "--db", db,
        "quote",
        "--carrier", "borealis",
        "--service", "ground",
        "--from", "94105",
        "--to", "10001",
        "--weight", "2.5",
        "--format", "json",
    )
    assert code == 3
    assert out == ""
    assert err.startswith("error [unsupported_service]:")


def test_ship_then_track(capsys, db):
    code, out, _ = run(
        capsys,
        "--db", db,
        "ship",
        "--carrier", "atlas",
        "--service", "ground",
        "--from", "94105",
        "--to", "10001",
        "--weight", "2.5",
        "--reference", "PO-4471",
    )
    assert code == 0
    shipment_id = out.splitlines()[0].split()[1]

    code, out, _ = run(capsys, "--db", db, "track", shipment_id)
    assert code == 0
    assert "no scan events yet" in out


def test_report_on_an_empty_database(capsys, db):
    code, out, _ = run(capsys, "--db", db, "report")
    assert code == 0
    assert "no shipments recorded" in out


def test_unknown_carrier_is_a_domain_error(capsys, db):
    code, out, err = run(
        capsys,
        "--db", db,
        "quote",
        "--carrier", "teleport",
        "--service", "ground",
        "--from", "94105",
        "--to", "10001",
        "--weight", "1",
        "--format", "json",
    )
    assert code == 3
    assert out == ""
    assert err.startswith("error [unknown_carrier]:")


def test_quote_rejects_an_unknown_format(capsys, db):
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "--db", db,
                "quote",
                "--carrier", "atlas",
                "--service", "ground",
                "--from", "94105",
                "--to", "10001",
                "--weight", "2.5",
                "--format", "xml",
            ]
        )

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert captured.out == ""
    assert "invalid choice" in captured.err


@pytest.mark.parametrize(
    "args",
    [
        (
            "ship",
            "--carrier", "atlas",
            "--service", "ground",
            "--from", "94105",
            "--to", "10001",
            "--weight", "2.5",
            "--format", "json",
        ),
        ("track", "shipment-id", "--format", "json"),
        ("report", "--format", "json"),
    ],
)
def test_other_subcommands_do_not_accept_format(capsys, args):
    with pytest.raises(SystemExit) as excinfo:
        main(list(args))

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert captured.out == ""
    assert "unrecognized arguments: --format json" in captured.err


def test_missing_subcommand_exits_with_usage(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2
