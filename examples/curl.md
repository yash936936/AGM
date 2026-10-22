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

The API binds to loopback only. Do not place it on a public interface or tunnel it to the internet without a separate security review.
