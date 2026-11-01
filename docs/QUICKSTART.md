# Quickstart: connect an agent in 5 minutes

Works in Git Bash, macOS and Linux. PowerShell notes are in brackets.

```bash
python -m venv .venv && source .venv/bin/activate     # [PowerShell: .venv\Scripts\Activate.ps1]
python -m pip install -e ".[dev]"
```

## 1. Create keys

```bash
python -m agm bootstrap-owner --keys agm.keys.json --tenant my-workspace
python -m agm connect --name claude-code --keys agm.keys.json
```

`connect` adds a scoped agent key (`memory:read/write/delete`, tier `trusted_agent`, same workspace as the owner, never admin) and prints the environment variables plus a block of instructions to paste into the agent's `CLAUDE.md`, `AGENTS.md` or system prompt. Use `--read-only` for an agent that must not write. The key file is gitignored; never commit it.

## 2. Start the server (loopback only)

```bash
python -m agm serve-api --keys agm.keys.json --db agm.db
```

Restart it after every `connect`, because keys are loaded at startup.

## 3. Use memory

In a second terminal, set the two variables `connect` printed (`AGM_BASE_URL`, `AGM_API_KEY`), then:

```bash
python -m agm mem write --kind fact --text "Atlas deadline is 2026-12-01" --entity Atlas --attribute deadline --value 2026-12-01
python -m agm mem retrieve "when is the Atlas deadline" --brief
python -m agm mem history --entity Atlas
python -m agm mem supersede <id> --kind fact --text "Atlas deadline moved to 2027-01-15" --entity Atlas --attribute deadline --value 2027-01-15 --reason "client request"
python -m agm mem delete <id>
```

`--brief` prints compact text for agents; without it you get JSON. Retrieval always starts with the notice that memory is untrusted data. A fact needs `--entity`; use `--kind episode` for free text.

## From Python

```python
from agm import AgmClient
c = AgmClient.from_env()          # AGM_BASE_URL, AGM_API_KEY
c.write({"kind": "fact", "text": "Atlas deadline is 2026-12-01", "entity": "Atlas", "attribute": "deadline", "value": "2026-12-01"})
print(c.retrieve("Atlas deadline", entity="Atlas")["items"])
```

The client uses only the standard library, never follows redirects, and refuses plain `http://` to non-loopback hosts.

## Handoff between models

```bash
echo '{"goal": "finish R1", "open_questions": ["windows ok?"]}' > state.json
python -m agm handoff save --session s1 --file state.json     # prints a packet id
python -m agm handoff resume <packet-id> --model other-model --budget 4000
```

## Agents that cannot run shell commands

Use the REST API directly (`/docs` on the running server shows the OpenAPI schema; see `examples/chatgpt_actions.md` and `examples/curl.md`). ChatGPT Actions and other web agents cannot reach a loopback server; that needs the remote deployment work in `docs/ROADMAP.md` (R3).
