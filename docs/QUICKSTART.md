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

The owner key is printed once by `bootstrap-owner`; the key file stores only hashes, so copy keys when they are shown. `connect` adds a scoped agent key (`memory:read/write/delete`, tier `trusted_agent`, same workspace as the owner, never admin) and prints the environment variables plus a block of instructions to paste into the agent's `CLAUDE.md`, `AGENTS.md` or system prompt. Use `--read-only` for an agent that must not write. The key file is gitignored; never commit it. An older plaintext key file still works; run `python -m agm hash-keys --keys agm.keys.json` to convert it (irreversible, so keep your keys elsewhere first).

## 2. Start the server (loopback only)

```bash
python -m agm serve-api --keys agm.keys.json --db agm.db
```

You do not need to restart it after `connect`: the server notices key-file changes on the next request. Removing a key from the file revokes it immediately; deleting the file locks everyone out.

## 3. Use memory

In a second terminal, set the two variables `connect` printed (`AGM_BASE_URL`, `AGM_API_KEY`), then:

```bash
python -m agm mem write --kind fact --text "Atlas deadline is 2026-12-01" --entity Atlas --attribute deadline --value 2026-12-01
python -m agm mem retrieve "when is the Atlas deadline" --brief
python -m agm mem history --entity Atlas
python -m agm mem supersede <id> --kind fact --text "Atlas deadline moved to 2027-01-15" --entity Atlas --attribute deadline --value 2027-01-15 --reason "client request"
python -m agm mem delete <id>
```

`--brief` prints compact text for agents; without it you get JSON. If a low-trust or stale-base write conflicts with a current fact, retrieval returns the current fact with a `contested_with` flag and withholds the conflicting claim; add `--include-contested` to see both. Retrieval always starts with the notice that memory is untrusted data. A fact needs `--entity`; use `--kind episode` for free text. For retrieval, `--entity X` narrows where the search starts; with graph expansion (the default) the result may still include facts about entities linked to X. Use `--no-expand` for a strict single-entity result.

## From Python

```python
from agm import AgmClient
c = AgmClient.from_env()          # AGM_BASE_URL, AGM_API_KEY
c.write({"kind": "fact", "text": "Atlas deadline is 2026-12-01", "entity": "Atlas", "attribute": "deadline", "value": "2026-12-01"})
print(c.retrieve("Atlas deadline", entity="Atlas")["items"])
```

The client uses only the standard library, never follows redirects, and refuses plain `http://` to non-loopback hosts.

## Active-memory helpers (read-only)

```bash
python -m agm active context "what should I work on next?" --goal-query "active goals" --brief   # context pack for the prompt
python -m agm active review --message "<the user's message>" --file proposals.json                # advisory policy check
```
`review` only tells you whether a proposed write/correct/delete is grounded in the user's actual message. It does not write anything and is not a security boundary; the real controls are key scopes, the guard and trust tiers.

## Handoff between models

```bash
echo '{"goal": "finish R1", "open_questions": ["windows ok?"]}' > state.json
python -m agm handoff save --session s1 --file state.json     # prints a packet id
python -m agm handoff resume <packet-id> --model other-model --budget 4000
```

## Agents that cannot run shell commands

Use the REST API directly (`/docs` on the running server shows the OpenAPI schema; see `examples/chatgpt_actions.md` and `examples/curl.md`). ChatGPT Actions and other web agents cannot reach a loopback server, and the server deliberately refuses non-loopback binds until the security review (R3.5) is done.

### Temporary private test through a tunnel (at your own risk)

A tunnel (for example Cloudflare Tunnel or ngrok) connects to `127.0.0.1`, so the bind guard is not bypassed, but your memory API becomes reachable from the internet through a third party. Only do this with throwaway data, a `--read-only` key made for the test, and remove the key (or delete the file) afterwards. There are no rate limits or audit logs yet, and the tunnel provider can see the traffic. Do not use real personal or client data.
