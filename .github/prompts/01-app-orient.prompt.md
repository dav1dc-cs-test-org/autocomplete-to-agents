---
name: 01-app-orient
description: "APP — no clone, no venv: understand a repo you have never checked out"
agent: ask
---

I have never seen this codebase before and I am on call for it tomorrow.

Without changing anything, answer these five questions. Cite the specific files
and functions you used for each answer — I want to be able to check your work.

1. **What does this service do**, in two sentences, in the language the business
   would use rather than the language of the code?
2. **Trace one request end to end.** A customer calls `POST /v1/quotes`. Name
   every module the request passes through, in order, and say what each one
   contributes. Draw it as a Mermaid sequence diagram.
3. **Where is the money?** Which module decides what a shipment costs, and what
   stops a rounding error from reaching a customer invoice?
4. **What would break first?** Name the three files where a careless change would
   do the most damage, and say why for each.
5. **What is the oldest thing here?** Find the module that most obviously
   predates the rest of the codebase. What patterns does it use that nothing else
   does, and what is still depending on it?

Finish with the one question you would ask the previous maintainer if you could
only ask one.
