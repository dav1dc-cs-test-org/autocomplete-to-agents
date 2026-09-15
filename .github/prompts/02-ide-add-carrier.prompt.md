---
name: 02-ide-add-carrier
description: "IDE — per-edit approval: a goal that ripples across the repo, self-corrected"
agent: agent
---

Onboard a new carrier: **Cascade Logistics**.

What the carrier agreement says:

- Code `cascade`, display name `Cascade Logistics`.
- Services: ground and express. No overnight, no international, no Saturday.
- Tracking numbers are `CSC` followed by 10 digits.
- Pricing, per their rate sheet:
  - ground — base `7.95`, `1.10` per kg, dim divisor `5500`, minimum `10.50`,
    zone multipliers starting at `1.00` and stepping `0.11`;
  - express — base `16.50`, `2.05` per kg, dim divisor `5500`, minimum `22.00`,
    zone multipliers starting at `1.00` and stepping `0.16`.
- Their scan codes are: `CREATED`, `COLLECTED`, `AT_DEPOT`, `LINEHAUL`,
  `OUT_FOR_DEL`, `DELIVERED`, `FAILED_ATTEMPT`, `DAMAGED`, `RETURN_TO_SENDER`.

Do the whole thing, not just the adapter. Run
`pytest tests/test_carrier_contract.py` early — it is parameterised over the
registry, so as soon as you register the carrier it will tell you what is still
missing. Keep going until `make check` is green.

When you are done, show me:

- every file you touched and why;
- the output of `freightline carriers`;
- a ground quote from `94105` to `10001` for a 2.5 kg parcel on Cascade next to
  the same quote on Atlas, so I can see the price difference;
- anything the carrier contract made you do that you would not have thought of.
