# Real third-party host integration validation

Status: **NOT VERIFIED.** Repository REST smoke clients passing in CI prove only that the repository's own test clients can exercise the adapters. They do not establish interoperability with an independently maintained host.

## Required test record

- Host product and version:
- Host runtime / OS:
- AGM commit SHA and package version:
- Adapter and transport:
- Test date and operator:
- Host configuration (secrets omitted):
- Logs/artifacts location and redaction check:
- Disposition: NOT STARTED / PASS / FAIL / BLOCKED

## Safe test setup

1. Use a disposable test environment and synthetic, non-sensitive memory records only.
2. Keep AGM bound to loopback unless the security review explicitly approves another topology.
3. Use a dedicated test credential with minimum permissions. Never put credentials in the repository, command output, test fixtures, or report.
4. Record host and adapter versions and the exact configuration. Do not connect a production account or import real user histories for this smoke test.
5. Confirm logs and screenshots do not expose tokens or memory content before sharing artifacts.

## Minimum interoperability matrix

- [ ] Host can discover/connect to the selected AGM adapter using its documented transport.
- [ ] Authentication succeeds with the intended credential and fails with an invalid credential.
- [ ] A synthetic fact can be written and retrieved in a new host session.
- [ ] A corrected fact returns the current value and does not prefer the stale value.
- [ ] Deletion is respected after host reconnect and AGM view rebuild/reopen.
- [ ] Untrusted retrieved text is presented as data and does not override host/system instructions.
- [ ] Scope boundaries are enforced for the configured identity and project.
- [ ] Timeouts, disconnects, malformed responses, and server shutdown produce safe, understandable failures.
- [ ] Host restart and AGM restart behavior are documented.
- [ ] No secrets or sensitive payloads appear in logs, errors, telemetry, or host UI unexpectedly.

Identify the concrete host integration that calls the documented endpoints. Testing a custom script against AGM is not an external-host test.

## Evidence and acceptance

Attach sanitized logs or screenshots, exact steps, expected/actual outcomes, and any limitations. Mark each matrix row PASS, FAIL, BLOCKED, or NOT RUN. A successful run against one named host validates only that host/version/configuration, not all third-party hosts.

**Gate remains OPEN until a real independently maintained host is tested and evidence is reviewed.**
