#!/usr/bin/env python3
"""Print a saved demo prompt so it can be piped into any Copilot surface.

    python scripts/demo_prompt.py 03           # print prompt 03
    python scripts/demo_prompt.py --list       # name, surface, and why
    copilot -p "$(python scripts/demo_prompt.py 05)"

The prompts live in ``.github/prompts/`` and are named ``NN-<surface>-<topic>``.
This strips the YAML frontmatter so what you get is exactly the prompt text,
ready to paste into github.com, the Copilot app, or the CLI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / ".github" / "prompts"


def available() -> list[Path]:
    return sorted(PROMPTS_DIR.glob("*.prompt.md"))


def find(number: str) -> Path:
    key = number.zfill(2)
    matches = [path for path in available() if path.name.startswith(f"{key}-")]
    if not matches:
        raise SystemExit(f"no prompt numbered {key!r}; try --list")
    return matches[0]


def name_of(path: Path) -> str:
    return path.name.removesuffix(".prompt.md")


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, _, remainder = text.partition("---\n")
    block, _, _ = remainder.partition("---\n")
    fields: dict[str, str] = {}
    for line in block.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"')
    return fields


def body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        _, _, remainder = text.partition("---\n")
        _, _, text = remainder.partition("---\n")
    return text.strip()


def listing() -> int:
    """The surface cheat-sheet: which surface, and the argument it makes."""
    width = max(len(name_of(path)) for path in available())
    for path in available():
        print(f"{name_of(path):<{width}}  {frontmatter(path).get('description', '')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("number", nargs="?", help="prompt number, e.g. 03")
    parser.add_argument("--list", action="store_true", help="list prompts with their surface")
    parser.add_argument("--all", action="store_true", help="print every prompt in order")
    args = parser.parse_args(argv)

    if args.list or (not args.number and not args.all):
        return listing()

    if args.all:
        for path in available():
            print(f"\n{'=' * 78}\n{name_of(path)}\n{'=' * 78}\n")
            print(body(path))
        return 0

    print(body(find(args.number)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
