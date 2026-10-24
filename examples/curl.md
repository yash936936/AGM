# Local REST calls

Copy `agm.keys.example.json` to `agm.keys.json`, replace each sample key with a long random value, and never commit the real file. Start the service in another terminal:

```bash
python -m agm serve-api --db ./agm.db --keys ./agm.keys.json
```

Set an environment variable to one of the keys you configured:

```bash
export AGM_API_KEY='your-local-development-key'
```

Write a fact (all request bodies are authenticated with `X-API-Key`):

```bash
curl -sS http://127.0.0.1:8765/v1/memory \
  -H "X-API-Key: $AGM_API_KEY" -H 'Content-Type: application/json' \
  -d '{"kind":"fact","text":"AGM stores its events in SQLite","entity":"AGM","attribute":"event_store","value":"SQLite"}'
```

Retrieve:

```bash
curl -sS http://127.0.0.1:8765/v1/memory/retrieve \
  -H "X-API-Key: $AGM_API_KEY" -H 'Content-Type: application/json' \
  -d '{"query":"AGM event store","entity":"AGM","expand":true,"k":8}'
```

History and deletion:

```bash
curl -sS 'http://127.0.0.1:8765/v1/memory/history?entity=AGM' -H "X-API-Key: $AGM_API_KEY"
curl -sS -X DELETE 'http://127.0.0.1:8765/v1/memory/n_REPLACE_WITH_ID' -H "X-API-Key: $AGM_API_KEY"
```

## Active memory endpoints

Build a bounded context pack before asking a model to answer:

```bash
curl -sS http://127.0.0.1:8765/v1/memory/context \
  -H "X-API-Key: $AGM_API_KEY" -H 'Content-Type: application/json' \
  -d '{"query":"Which database does AGM use?","entity":"AGM","k":8,"token_budget":1000}'
```

Save a directly stated preference after a user turn. The quote is required to occur in the submitted current-message string; an application-controlled host should supply that string rather than trusting a model to reconstruct it:

```bash
curl -sS http://127.0.0.1:8765/v1/memory/remember \
  -H "X-API-Key: $AGM_API_KEY" -H 'Content-Type: application/json' \
  -d '{"item":{"kind":"fact","entity":"user","attribute":"communication_preference","value":"concise","text":"The user prefers concise answers."},"current_user_message":"Please remember that I prefer concise answers.","evidence_quote":"I prefer concise answers","reason":"Durable user preference"}'
```

Use `POST /v1/memory/correct` for an explicit user correction, `POST /v1/memory/forget` for an explicit forget request, and `GET /v1/memory/health` for read-only integrity/index checks. Forget removes the target memory plus its connected supersede-history chain. The quote policy is not a platform-level authorization boundary in native MCP calls.
The API binds to loopback only. Do not place it on a public interface or tunnel it to the internet without a separate security review.
