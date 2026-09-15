#!/usr/bin/env python3
"""Introduce one known defect so the Copilot CLI triage step has a red build.

    python scripts/demo_break.py --list
    python scripts/demo_break.py surcharge-order
    python scripts/demo_break.py --revert

``--revert`` is `git checkout --` on the affected files, so it discards *any*
uncommitted change to them. It refuses to run if those files have other edits
you have not committed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "freightline"

Edit = tuple[str, str]

BREAKAGES: dict[str, tuple[str, Path, list[Edit]]] = {
    "surcharge-order": (
        "Fuel is applied before the flat surcharges, so it stops compounding on them.",
        SRC / "rating" / "surcharges.py",
        [
            (
                "SURCHARGES: tuple[Surcharge, ...] = (\n    ResidentialSurcharge(),",
                "SURCHARGES: tuple[Surcharge, ...] = (\n    FuelSurcharge(),\n"
                "    ResidentialSurcharge(),",
            ),
            (
                "    HeavyweightSurcharge(),\n    FuelSurcharge(),\n)",
                "    HeavyweightSurcharge(),\n)",
            ),
        ],
    ),
    "money-rounding": (
        "Money rounds down instead of half-up, so every quote is a cent light.",
        SRC / "money.py",
        [
            ("from decimal import ROUND_HALF_UP, Decimal", "from decimal import ROUND_DOWN, Decimal"),
            (
                "quantized = amount.quantize(CENTS, rounding=ROUND_HALF_UP)",
                "quantized = amount.quantize(CENTS, rounding=ROUND_DOWN)",
            ),
        ],
    ),
    "zone-band": (
        "One US postal band is mis-mapped, so a whole region prices at the wrong zone.",
        SRC / "rating" / "zones.py",
        [('    "1": 1,\n', '    "1": 4,\n')],
    ),
}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def dirty(paths: list[Path]) -> list[str]:
    relative = [str(path.relative_to(ROOT)) for path in paths]
    changed = git("status", "--porcelain", "--", *relative).strip()
    return [line for line in changed.splitlines() if line]


def apply(name: str) -> int:
    description, path, edits = BREAKAGES[name]
    if dirty([path]):
        print(f"refusing to edit {path.relative_to(ROOT)}: it has uncommitted changes", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    for old, new in edits:
        if old not in text:
            print(f"anchor not found in {path.name}; the file has drifted", file=sys.stderr)
            return 1
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")

    print(f"broke: {name}")
    print(f"  {description}")
    print(f"  edited {path.relative_to(ROOT)}")
    print("\nrun the tests and let Copilot work out what happened:")
    print("  .venv/bin/python -m pytest -q")
    return 0


def revert() -> int:
    paths = sorted({path for _, path, _ in BREAKAGES.values()})
    git("checkout", "--", *[str(path.relative_to(ROOT)) for path in paths])
    print("reverted all demo breakages")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", choices=sorted(BREAKAGES), help="which defect to apply")
    parser.add_argument("--list", action="store_true", help="describe the available defects")
    parser.add_argument("--revert", action="store_true", help="restore the affected files")
    args = parser.parse_args(argv)

    if args.revert:
        return revert()
    if args.list or not args.name:
        for name, (description, path, _) in sorted(BREAKAGES.items()):
            print(f"{name:<18} {description}")
            print(f"{'':<18} -> {path.relative_to(ROOT)}")
        return 0
    return apply(args.name)


if __name__ == "__main__":
    sys.exit(main())
