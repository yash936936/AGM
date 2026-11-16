# Components

One guide per area. Read the guide before changing the area; each lists files, behaviour that is easy to break, tests and open work. Contracts and the REST map are in `../architecture.md`; rules every change must respect are in `../../AGENTS.md`.

| Guide | Files |
|---|---|
| [core.md](core.md) | `store.py`, `events.py`, `db.py`, `models.py`, `bootstrap.py` |
| [retrieval.md](retrieval.md) | `retrieve.py`, `embed.py`, the retrieval path inside `store.py` |
| [trust-and-lifecycle.md](trust-and-lifecycle.md) | `guard.py`, `trust.py`, `lifecycle.py`, delete, expiry and revocation in `store.py` |
| [interfaces.md](interfaces.md) | `api.py`, `client.py`, `cli.py`, `cli_client.py`, `config.py`, `agent_keys.py`, `hub_state.py`, `local_hub.py`, `diagnostics.py` |
| [handoff-and-active-memory.md](handoff-and-active-memory.md) | `handoff.py`, `active_memory*.py`, `turn_loop.py`, `reference_host.py` |
| [evaluation.md](evaluation.md) | `eval/`, `scripts/`, `tests/`, `examples/` |

Keep these in step with the code: when a change adds, removes or renames a file, update the table and the guide in the same patch.

---
**Next:** Return to [`context.md`](../../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
