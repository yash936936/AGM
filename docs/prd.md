# PRD — AGM prototype

## Problem
Agents lose context between sessions and models, return stale facts next to
current ones, and have no way to tell verified memory from guesses. Draft v5
proposes a memory layer outside any LLM to fix this. We need something that
runs now, so real agents can use it and so the design gets tested against
real use instead of staying a document.

## Goals
- A working local service any agent can connect to within minutes: REST API,
  MCP server (stdio and HTTP) and a Python library, all over one core.
- Write and retrieve memory with provenance, confidence and writer identity.
- Supersede changed facts so "current" answers exclude stale ones, while
  history stays queryable.
- Save a task as a handoff packet in one agent and resume it in another model.
- Keep a **flat retrieval baseline** switchable beside graph expansion, so the
  design's central bet can be checked, not assumed.

## Non-goals (prototype)
- Calibrated confidence, tuned decay, or any claim about H1–H7 (v5 requires
  pre-registered thresholds first; see D-007).
- Server-side LLM extraction. The calling agent supplies structured facts.
- Community detection, derived hierarchy, reflection, learning loop (v5 section 8 defers these).
- Multi-user production hosting, billing, UI.
- Million-item scale. Target is a few thousand items on SQLite.

## Users / use cases
1. A local coding agent writes decisions and facts, retrieves them next session.
2. User stops in Claude Code, resumes the same task in Codex or ChatGPT via a handoff packet.
3. Two agents write to one store; a conflicting write shows as contested, not overwritten.
4. A user corrects a fact ("we moved to Postgres"); the old value stops appearing as current.

## Success criteria (testable)
- Phase tests pass: `pytest` green on a clean checkout.
- Event-log replay rebuilds identical graph state (test).
- Supersession: after a correction, `retrieve` current mode never returns the old value; `include_superseded` returns it.
- Abstention: an unanswerable query returns `abstain=true`, not a nearest-neighbour guess.
- Delete removes content, embedding, FTS row and edges, and the item no longer surfaces.
- Real connection demonstrated from at least: a Python agent over REST, and one MCP client (Claude Code or Claude Desktop) over stdio.
- Mini eval (Phase 5) reports flat vs graph numbers with the caveat in D-007.

## Constraints
- Urgent: working prototype first, polish later.
- Code written by a ChatGPT model under Claude's supervision, so contracts must be explicit.
- Single developer, local machine (Delhi NCR), Python-comfortable.

---
**Next:** Return to [`context.md`](../context.md) before starting a new task —
it routes you to the right file for what you are about to do.
