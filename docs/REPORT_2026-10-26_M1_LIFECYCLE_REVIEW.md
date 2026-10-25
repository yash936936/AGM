# Report — 2026-10-26 M1 lifecycle context review follow-up

## Files changed
- `src/agm/active_memory.py`: normalize untrusted context values to one line, escape angle-bracket delimiters, and include provenance in rendered records.
- `src/agm/lifecycle.py`: append `token_budget` after existing fields to preserve positional construction.
- `tests/test_lifecycle.py`: cover positional compatibility, source provenance, delimiter escaping, and bounded context.
- `context.md`, `docs/status.md`, `docs/debug.md`: record findings and current validation state.

## Test intent
- Preserve the pre-existing positional mapping for `BeforeTurnRequest` arguments.
- Retain source episode/span metadata in the prompt context.
- Ensure memory content cannot add a new prompt line or literal closing record tag.
- Ensure bounded context still omits an oversized record while reporting only included IDs.

## Validation
- PR #32 prior exact-head CI: [run 40221564276](https://github.com/yash936936/AGM/actions/runs/40221564276), all six Ubuntu/Windows Python 3.11–3.13 jobs passed on the previous merged head.
- Current-main follow-up tests: NOT RUN locally in this remote editing environment.
- Current-main exact-head CI and review: PENDING.

## Contract concerns and assumptions
- `BeforeTurnRequest` positional argument order is treated as a public compatibility contract.
- Existing `Node.provenance` is the source-span metadata carrier.
- Escaping is defense in depth, not a substitute for the untrusted-memory notice.

## Unfinished items
- Wait for exact-head CI and review before merging.
- M0 remains IN PROGRESS and M1 remains PARTIAL / VERIFY.
- Local Windows smoke clients, held-out consented real-history evaluation, and independent security/privacy review remain open.
