# TRD — AGM prototype

## Stack
- Python 3.11+, SQLite (stdlib `sqlite3`, FTS5 required; check at startup and fail clearly if missing).
- pydantic v2 (models), FastAPI + uvicorn (REST), official `mcp` Python SDK using `FastMCP` (MCP server), numpy (vectors), pytest + httpx (tests).
- Embeddings: pluggable `Embedder` interface. Default `HashEmbedder` (character n-gram hashing, 256 dims, model id `hash-256-v1`, no downloads). Optional `SentenceTransformerEmbedder` behind an extra. One embedder per store; the model id is stored per vector so a swap triggers re-embed.
- No other dependencies without a decisions.md entry.

## System requirements
- Runs on a laptop, no GPU, no internet needed for the default config.
- Latency target for the prototype: retrieve p95 under 200 ms at 5k items (measured in Phase 5, not promised).

## Integration points (connection surfaces)
All three share one core, so behaviour is identical:
| Surface | Transport | Who connects |
|---|---|---|
| Python library | in-process | local agents written in Python |
| REST API | HTTP + OpenAPI at `/openapi.json` | any local agent; ChatGPT Custom GPT Actions; scripts |
| MCP server | stdio, and streamable HTTP | Claude Code, Codex CLI, Claude Desktop, other MCP clients |

Remote clients (web Claude, ChatGPT) cannot reach localhost. They need a public HTTPS URL
(a tunnel such as cloudflared or ngrok, or a small hosted deploy), and whether a given
plan supports custom connectors or MCP is (open — confirm with user, check current docs
for each product before relying on it). Local stdio and REST work without that.

Auth: API key per writer, mapped in `agm.keys.json` to `tenant_id`, `writer_id`, `trust_tier`, `scopes`.
For MCP stdio the identity comes from env vars `AGM_TENANT`, `AGM_WRITER`, `AGM_TIER`.

## Non-functional requirements
- Security: parameterized SQL only; secrets redacted before storage and embedding; no network exposure beyond localhost until Phase 3 auth plus redaction are done and reviewed; retrieved text always returned with the untrusted-data notice.
- Reliability: every mutation is an event first (idempotency key honoured); views rebuildable by replay.
- Observability: each retrieve returns its route (seed count, expanded count, widened, abstained); structured logs to stderr (stdout is reserved for MCP stdio).

## Known technical constraints
- The hash embedder is weak semantically; results will look worse than a real embedding model. That limits what the demo shows and is a known bias in any eval (see D-003).
- Token budgets use a rough estimate (chars / 4), not a real tokenizer.
- Server does no extraction: quality depends on the calling agent's structured input (v5's "extraction is the ceiling" risk is sidestepped here, not solved).

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
