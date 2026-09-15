#!/usr/bin/env python3
"""Audit every published rate card with the Copilot SDK.

The same agent runtime that powers Copilot CLI, driven from our own script, with
a custom tool that hands the model our real rate cards. The model reasons; the
data comes from `freightline.rating.tables`, not from the model's memory.

    pip install github-copilot-sdk
    python -m copilot download-runtime          # first run only
    python tools/copilot_sdk/rate_card_auditor.py --carrier atlas

Billing: every prompt counts against your Copilot usage, the same as a CLI turn.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pydantic import BaseModel, Field  # noqa: E402

from freightline.carriers import all_carrier_codes  # noqa: E402
from freightline.rating.tables import RATE_CARDS  # noqa: E402

try:
    from copilot import CopilotClient, define_tool
    from copilot.rpc import PermissionDecisionApproveOnce, PermissionDecisionReject
    from copilot.session_events import AssistantMessageData, SessionIdleData
    from copilot.session_events import PermissionRequestShell
except ImportError:  # pragma: no cover - the SDK is an optional dev dependency
    print(
        "The Copilot SDK is not installed.\n"
        "  pip install github-copilot-sdk\n"
        "  python -m copilot download-runtime",
        file=sys.stderr,
    )
    raise SystemExit(1) from None


SYSTEM_RULES = """
<rules>
- Use the get_rate_card tool. Never state a price you have not read from it.
- A rate card is complete only if every advertised service has a multiplier for
  every zone 1 through 8.
- Report monetary values exactly as the tool returned them. Do not re-round.
</rules>
""".strip()

PROMPT = """
Audit the rate card for carrier `{carrier}`.

Call `get_rate_card` for it, then report:

1. Every service it publishes, and for each, the zone-1 and zone-8 price for a
   5 kg parcel. Show the arithmetic: base + per_kg * weight, times the zone
   multiplier, floored at the minimum.
2. Any service where the zone-8 price is less than 1.4x the zone-1 price. That
   is a flat-looking curve and is usually a data-entry mistake.
3. Any service whose minimum charge is above its own zone-1 price, which means
   the minimum is doing all the work and the per-kg rate is decorative.
4. Any gap: a missing zone, a missing service, a non-monotonic multiplier.

Finish with one line: `VERDICT: OK` or `VERDICT: REVIEW` followed by the single
most important thing to look at.
""".strip()


class RateCardQuery(BaseModel):
    carrier_code: str = Field(description="Carrier code, e.g. 'atlas'")


@define_tool(
    description="Return the published rate card for a carrier: base, per-kg, dim divisor, "
    "minimum charge, and the zone multipliers.",
    skip_permission=True,
)
async def get_rate_card(params: RateCardQuery) -> str:
    """Read the rate card out of the codebase so the model never has to guess."""
    card = RATE_CARDS.get(params.carrier_code)
    if card is None:
        return f"No rate card published for {params.carrier_code!r}. Known: {sorted(RATE_CARDS)}"

    lines = [f"carrier: {params.carrier_code}"]
    for service, rate in card.items():
        multipliers = ", ".join(f"{zone}={value}" for zone, value in sorted(rate.zone_multipliers.items()))
        lines.append(
            f"service={service.value} base={rate.base} per_kg={rate.per_kg} "
            f"dim_divisor={rate.dim_divisor} minimum={rate.minimum_charge}\n"
            f"  zone_multipliers: {multipliers}"
        )
    return "\n".join(lines)


def deny_shell(request: object, invocation: dict) -> object:
    """This process audits data. It has no reason to run a shell command."""
    if isinstance(request, PermissionRequestShell):
        return PermissionDecisionReject(
            feedback="Shell access is not available in the rate card auditor. "
            "Use the get_rate_card tool."
        )
    return PermissionDecisionApproveOnce()


async def audit(carrier_code: str, model: str) -> str:
    transcript: list[str] = []
    async with CopilotClient() as client:
        async with await client.create_session(
            model=model,
            tools=[get_rate_card],
            on_permission_request=deny_shell,
            system_message={"mode": "append", "content": SYSTEM_RULES},
        ) as session:
            finished = asyncio.Event()

            def on_event(event: object) -> None:
                match getattr(event, "data", None):
                    case AssistantMessageData() as data:
                        transcript.append(data.content)
                    case SessionIdleData():
                        finished.set()

            session.on(on_event)
            await session.send(PROMPT.format(carrier=carrier_code))
            await finished.wait()

    return "\n".join(transcript)


async def run(carriers: list[str], model: str) -> int:
    failures = 0
    for carrier_code in carriers:
        print(f"\n{'=' * 72}\n{carrier_code}\n{'=' * 72}")
        report = await audit(carrier_code, model)
        print(report)
        if "VERDICT: REVIEW" in report:
            failures += 1
    print(f"\n{failures} of {len(carriers)} carriers need review")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--carrier",
        action="append",
        dest="carriers",
        help="carrier code; repeatable. Defaults to every registered carrier.",
    )
    parser.add_argument("--model", default="gpt-5")
    args = parser.parse_args(argv)

    carriers = args.carriers or all_carrier_codes()
    return asyncio.run(run(carriers, args.model))


if __name__ == "__main__":
    sys.exit(main())
