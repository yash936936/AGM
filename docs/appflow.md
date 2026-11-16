# App flow — AGM prototype

How an agent or a person moves through AGM today (v0.7.x, local-only, loopback). REST paths are in `architecture.md`; commands are in `QUICKSTART.md`.

## 1. Connect an agent
1. Owner runs `python -m agm bootstrap-owner --keys agm.keys.json --tenant <workspace>`; the owner key is shown once and only hashes are stored.
2. Owner runs `python -m agm connect --name <agent> --keys agm.keys.json` (add `--read-only` for a reader). It prints `AGM_BASE_URL`, `AGM_API_KEY` and an instruction block for the agent's `CLAUDE.md`, `AGENTS.md` or system prompt.
3. Owner starts `python -m agm serve-api --keys agm.keys.json --db agm.db`. Key-file changes are picked up on the next request; removing a key revokes it at once.

## 2. Agent remembers, corrects and forgets
1. Agent writes a fact (`mem write` or `POST /v1/memory`) with entity, attribute, value and text. The core redacts secrets and quarantines instruction-like text before storing, whatever the caller.
2. Later the fact changes: same value from the same writer is a no-op; a new value supersedes the old one (`mem supersede` with a reason); the old fact keeps its history.
3. Next session the agent retrieves (`mem retrieve`). Output starts with the notice that memory is untrusted data, then only current facts, each with provenance and confidence. If evidence is insufficient the result abstains.
4. To remove something, `mem delete <id>` hard-purges the content, derived data and the original event payload.

## 3. A low-trust or stale write conflicts
1. A writer in a lower trust tier, or one using a stale `base_version`, sends a different value for an existing fact.
2. The new claim is stored as `contested`; the current fact stays active.
3. Retrieval returns the current fact with `contested_with` set and withholds the claim. `--include-contested` returns both, each flagged.

## 4. Switch models mid-task
1. Agent A saves task state (`handoff save`, `POST /v1/handoff`) and gets a packet id.
2. Agent B resumes (`handoff resume <id> --model <name> --budget <tokens>`) and receives assembled context within its token budget plus a readback prompt.
3. B answers via `POST /v1/handoff/{id}/readback`; mismatches show before work continues.

## 5. Context before a model call (read-only)
1. The host calls `active context` (`POST /v1/active/context`) with the user's query and optional goal query.
2. It gets a bounded context pack: selected records, conflict notices and the untrusted-data notice.
3. Before applying a proposed write or delete, the host may call `active review` for an advisory check that it is grounded in the user's message. It writes nothing and is not a security boundary.

## 6. Revoking a writer or letting data expire
1. Admin calls `POST /v1/admin/revoke` for a writer: that writer's views are cleared and events are kept for audit. This is a rollback, not a delete.
2. `python -m agm lifecycle --dry-run` shows what expiry would remove before it runs.
3. `python -m agm rebuild` regenerates all views from the event log; results must be identical.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
