# Copilot SDK

[`rate_card_auditor.py`](rate_card_auditor.py) runs the same agent that powers
Copilot CLI, from our own process, over our own data.

## Run it

```bash
pip install github-copilot-sdk
python -m copilot download-runtime          # first run only
python tools/copilot_sdk/rate_card_auditor.py --carrier atlas
```

Authentication reuses whatever `copilot` is already signed in as. It also accepts
`COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, or `GITHUB_TOKEN`.

## The three things worth pointing at

**A custom tool, not a bigger prompt.** `get_rate_card` is registered with
`@define_tool` and reads `freightline.rating.tables` directly. The model asks for
the data it needs instead of being handed a wall of pasted context it might
paraphrase. Change a rate card and the auditor is correct on the next run with no
edit here.

**A permission handler you control.** `deny_shell` rejects every shell request
with feedback the model can read and act on. The agent has real tools; the host
process decides which ones it actually gets. That is the difference between
"agentic" and "unsupervised".

**An exit code.** The script returns non-zero when any carrier reports
`VERDICT: REVIEW`, so it composes with everything else that runs in CI.

## Where this goes next

The same shape covers most internal automation: a scheduled job that drafts
release notes from the commit range, a bot that triages incoming issues against
the labels your repo actually uses, a pre-merge check that reads a diff and
answers one narrow question. The agent brings planning and tool use; you bring
the boundary, the data, and the decision about what it is allowed to touch.

Not every job needs an agent. If the answer is a `SELECT`, write the `SELECT`.
