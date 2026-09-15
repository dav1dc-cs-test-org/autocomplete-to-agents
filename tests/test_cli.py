from __future__ import annotations

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


def test_quote_prints_a_breakdown_and_a_total(capsys, db):
    code, out, _ = run(
        capsys,
        "--db", db,
        "quote",
        "--carrier", "atlas",
        "--service", "ground",
        "--from", "94105",
        "--to", "10001",
        "--weight", "2.5",
    )
    assert code == 0
    assert "TOTAL" in out
    assert "Fuel surcharge" in out


def test_quote_reports_a_domain_error_without_a_traceback(capsys, db):
    code, _, err = run(
        capsys,
        "--db", db,
        "quote",
        "--carrier", "borealis",
        "--service", "ground",
        "--from", "94105",
        "--to", "10001",
        "--weight", "2.5",
    )
    assert code == 3
    assert "unsupported_service" in err


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
    code, _, err = run(
        capsys,
        "--db", db,
        "quote",
        "--carrier", "teleport",
        "--service", "ground",
        "--from", "94105",
        "--to", "10001",
        "--weight", "1",
    )
    assert code == 3
    assert "teleport" in err


def test_missing_subcommand_exits_with_usage(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2
