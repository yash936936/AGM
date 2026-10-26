# M2 Reference Host Integration Report

**Status:** INTEGRATION HARNESS CANDIDATE / NOT ACCEPTED  
**Date:** 2026-10-26

## Purpose

Provide a small, dependency-free example of how an external host can connect authenticated identity, scoped AGM context, proposal review, host-verified mutation confirmation, and the library-only proposal executor. This is a test harness, not a production authentication implementation.

## Files

- `src/agm/reference_host.py`: reference orchestration. It resolves an opaque authenticated session handle to a trusted `HostPrincipal`; derives `Ctx` and scopes only from that principal; reviews proposals against the current message; requires a host confirmation verifier for mutations; then calls the library executor.
- `tests/test_reference_host.py`: integration regressions for trusted identity resolution, confirmation denial, tenant isolation, and rejected proposals leaving the event log unchanged.
- `docs/decisions.md`: records the harness boundary and assumptions.
- `docs/status.md`, `docs/debug.md`, `context.md`: records implementation and validation status.

## Security boundary

The harness does not authenticate users itself. The host must provide a resolver backed by its actual session/auth system and a confirmation verifier backed by trusted UI/workflow state. Do not construct `HostPrincipal` from client-controlled identity or scope fields. The sample does not expose a network listener or change REST/MCP contracts.

## Validation

- Local pytest: **NOT RUN** in this remote editing session.
- Exact-head GitHub Actions: **PENDING** for the latest branch head; the lifecycle test was added after the initial CI trigger.
- Real third-party host validation: **NOT RUN**. A local reference harness is preparation for, not proof of, the external-host release gate.

## Acceptance still required

- Exact-head CI passes on Ubuntu and Windows, Python 3.11–3.13.
- Review confirms identity and confirmation callbacks are wired only to trusted host mechanisms.
- A real third-party host runs the acceptance scenarios with synthetic data and produces a reproducible report.
- Held-out consented real-history evaluation and independent security/privacy review remain separate open gates.
