# AGM — verified capabilities

What is true today, by evidence level. The public overview and quick start are in the root `README.md`; this file says how far each claim has been checked. Update it when a gate closes, not before.

Levels: **Implemented** (code exists) · **Tests** (automated tests, CI on Ubuntu and Windows, Python 3.11–3.13) · **Real evidence** (run on real usage data) · **Accepted** (owner or independent sign-off).

| Capability | Implemented | Tests | Real evidence | Accepted |
|---|---|---|---|---|
| Event log, replay, `rebuild_views` | yes | yes | n/a | no |
| Secret redaction and instruction-text quarantine in the core | yes | yes (direct library and REST) | n/a | no |
| Flat retrieval (FTS5 plus hash-embedding vectors) | yes | yes | NOT RUN | no |
| Graph expansion | yes | yes | NOT RUN; synthetic result: not justified (v3) | no |
| Contested handling, flat and graph agree (D-046) | yes | yes | n/a | no |
| Supersede, history, idempotent writes | yes | yes | n/a | no |
| Hard delete (nothing readable on disk), expiry, writer revocation | yes | yes | n/a | no |
| Handoff save, resume, readback | yes | yes | NOT RUN | no |
| REST API, hashed keys, hot reload, body limit (D-045) | yes | yes (CI smoke client) | n/a | no |
| Python client and CLI (`mem`, `handoff`, `active`, `connect`) | yes | yes | one manual end-to-end CLI run on 2026-11-04 | no |
| Read-only active-memory routes (D-044) | yes | yes | NOT RUN | no |
| Windows | yes | CI Windows green on #642; local runs pass | n/a | no |

## Not verified or not supported
- Real-history evaluation: NOT RUN (needs your frozen cases, R2.2).
- Independent security and privacy review: NOT PERFORMED.
- Third-party host integration (Claude Code, ChatGPT Action): NOT VERIFIED; CI smoke tests do not count.
- Remote access: not supported. The server refuses non-loopback hosts.
- Scale: not measured. Vector search scans every embedding for a tenant and project (R5.1).
- Paraphrase handling with the default hash embedder is weak (R2.1, R5.2).
- Abstention for unknown entities or missing attributes rarely fires (R2.6c).

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
