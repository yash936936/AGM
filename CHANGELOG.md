# Changelog

All notable changes to AGM are documented here. This project is a local-only research prototype; an entry does not imply production readiness or a PyPI release.

## Unreleased

### Added
- BM25-only, vector-only cosine, whole-log-in-context, flat, iterative-flat and graph retrieval comparisons in the synthetic v3 evaluation.
- Optional, lazily imported sentence-transformer evaluation adapter via the `eval-sentence-transformer` extra.
- Python 3.14 to the Ubuntu and Windows CI matrix.

### Changed
- Flat and graph retrieval scope explicitly named entities using hyphen-aware canonical-name and alias boundaries.
- Retrieval recognizes common owner and on-call answer-slot paraphrases.
- The v3 report includes p50, p95 and p99 retrieval latency, calls per query, abstention correctness, and whole-log context-size estimates.

### Fixed
- Named-entity retrieval abstains when the requested answer attribute is absent.
- Relation retrieval can use eligible answer-slot evidence from reached entities rather than relying only on lexical similarity.
- Regression coverage removes the two historical strict xfail marks for the two-hop dependency-owner test.
- The Windows duration-mode benchmark smoke test uses a 2-second window after CI #641 exposed a 0.5-second timing flake.

## 0.7.0

Version recorded in `pyproject.toml`; no release tag or package publication is claimed.

### Included
- Event-sourced SQLite memory store with replay and rebuildable views.
- Flat and bounded graph retrieval, provenance, trust tiers and contested-memory handling.
- Memory lifecycle operations including supersede, hard delete, expiry and writer revocation.
- Task handoff, REST API, standard-library client and CLI.
- Loopback-only server behavior and synthetic evaluation tooling.
