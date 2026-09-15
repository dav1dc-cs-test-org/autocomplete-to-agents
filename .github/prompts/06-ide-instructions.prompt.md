---
name: 06-ide-instructions
description: "IDE — diff beside the rule: conventions applied without being asked"
agent: agent
---

Operations want to catch shipments that are about to breach their service
commitment.

Add a way to find shipments that are still in transit and have been in their
current status for longer than a threshold, and expose it on the CLI as
`freightline at-risk --hours 48`.

That is the whole brief. Everything else — where the code goes, what the query
looks like, how errors are raised, how the tests are named, what gets a comment
— you already know, because it is written down in this repository.

So before you write a line of code:

**List every instruction file that applies to the files you are about to touch,
and the specific rule from each that will change what you write.** Quote the
rule. Then implement it, and afterwards point at each place in your diff where
one of those rules is visible in the output.

Finish with `make check`.

Then tell me the honest version: which of those rules would you have followed
anyway, and which ones only happened because this repository wrote them down?
