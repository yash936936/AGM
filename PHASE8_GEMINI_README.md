# AGM Phase 8 — Gemini provider patch

This patch adds an optional Gemini provider to `examples/phase8_agent_demo.py` while preserving `offline` and `openai`.

## Install

```bash
python -m pip install -e ".[gemini]"
```

## Configure in Git Bash

Create a key in Google AI Studio: https://aistudio.google.com/app/apikey

```bash
export GEMINI_API_KEY='PASTE_YOUR_KEY_LOCALLY'
export GEMINI_MODEL='gemini-3.8-flash'
```

Do not paste your key into source code, commit it, or share it in logs/chat. Gemini Free Tier inputs/outputs may be used to improve Google products, so use only the synthetic Phase 8 database for this test and check the current model and rate limits in AI Studio.

## Test

```bash
python -m compileall -q src tests eval scripts examples
python -m pytest -q tests/test_phase8_gemini.py
python -m pytest -q
```

The tests mock the Google SDK and do not call the network. After they pass, run paired calls using the same query and synthetic database:

```bash
python examples/phase8_agent_demo.py --db ./phase8-memory.db --tenant phase8-demo --project phase8 --mode flat --query "Who owns billing-api?" --provider gemini --include-content --log logs/phase8-agent-gemini-flat.jsonl
python examples/phase8_agent_demo.py --db ./phase8-memory.db --tenant phase8-demo --project phase8 --mode graph --query "Who owns billing-api?" --provider gemini --include-content --log logs/phase8-agent-gemini-graph.jsonl
```

`GEMINI_MODEL` overrides the default model. The API call has not been run as part of building this patch because no user's API key is available in this workspace.
