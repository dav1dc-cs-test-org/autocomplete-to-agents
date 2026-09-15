---
name: 07-cli-skill-surcharge
description: "CLI — same SKILL.md, no editor: the customization that travels"
agent: agent
---

Compliance has signed off on carrying dangerous goods. Add the surcharge.

- Flat `42.00` per shipment.
- Applies when the shipper declares a UN hazard class on the parcel.
- It is subject to fuel, like every other flat surcharge.

Use the `add-surcharge` skill. Follow it exactly, in order, and tell me at each
step which step you are on. You are running outside the editor, so print each
change as a unified diff as you make it — I have no diff view here.

The point of this one is not the surcharge. It is that this change touches the
rating engine, the domain model, the API schema, the mapper, the CLI, the tests,
the architecture doc and the changelog — and that the skill, not your memory, is
what makes sure none of those get missed.

So when you finish, show me the checklist from the skill with each item ticked
and the file that satisfies it, and call out explicitly: **is
`QuoteIn.dangerous_goods_class` an additive or a breaking API change, and why?**

Then run `make check` and price the same parcel with and without the declaration
so I can see the line appear.
