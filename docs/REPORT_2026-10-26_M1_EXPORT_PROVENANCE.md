# Report — 2026-10-26 M1 Obsidian export provenance

## Files changed
- `src/agm/local_hub.py`: select source episode and span columns and include them in exported Markdown frontmatter.
- `tests/test_local_hub.py`: verify source episode ID and span coordinates survive export.
- `context.md`, `docs/status.md`, `docs/debug.md`: record the acceptance gap and follow-up status.

## What the test proves
A memory written with a source span exports the source episode identifier and start/end offsets into its Markdown frontmatter alongside the memory ID.

## Validation
- Local tests: NOT RUN in this remote editing environment.
- Exact-head CI, repository hygiene, whitespace checks, and wheel/package inspection: PENDING.
- No merge should occur until all required checks pass on the exact PR head.

## Contract concerns and assumptions
- Export frontmatter additions are additive; existing keys and deterministic filename behavior remain unchanged.
- Source provenance is represented by the existing `source_episode`, `span_start`, and `span_end` node columns. A missing source span is emitted as YAML `null`.
- Export remains a snapshot copy; deletion of the source memory does not delete previously exported files.

## Unfinished items
- Exact-head CI and review pending.
- M1 remains PARTIAL / VERIFY; M0 remains IN PROGRESS.
- Held-out consented real-history evaluation and independent security/privacy review remain open release gates.
