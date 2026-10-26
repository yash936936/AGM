# REST concurrent retrieval benchmark

**Status:** Diagnostic workload, not a production capacity or release-acceptance test.

Run from an installed development environment at the repository root:

```bash
python eval/rest_concurrent_benchmark.py --requests 200 --concurrency 8 --warmup 10 --seed-items 100 > rest-concurrent.json
# Optional 60-second sustained local load with periodic server RSS samples:
python eval/rest_concurrent_benchmark.py --duration-seconds 60 --concurrency 8 --warmup 10 --seed-items 100 > rest-soak.json
```

The script launches the AGM REST API in a separate local process, seeds synthetic facts through the public write endpoint, warms retrieval, and sends concurrent HTTP requests to `POST /v1/memory/retrieve`. It emits JSON with client-observed p50/p95/p99/min/max/mean latency, successful-request throughput, request/error counts, concurrency, elapsed time, environment metadata, and limitations. Optional duration mode keeps workers active for the requested number of seconds rather than stopping at a fixed request count. Server RSS/working-set is sampled periodically where the operating system supports querying the child process; readings are approximate and may be unavailable.

Run the integration checks with:

```bash
python -m pytest -q tests/test_rest_concurrent_benchmark.py
```

## Interpretation and limitations

- Measures retrieval endpoint latency over loopback HTTP, including response transfer and JSON decoding. It is not full assistant-turn latency and includes no model inference or external network.
- Uses synthetic facts and one local server process backed by SQLite. It is not a real-user-history benchmark or a third-party-host integration.
- A run exits nonzero if a measured request fails. Preserve the JSON report and stderr when investigating failures.
- RSS/working-set readings are approximate and OS-dependent. This is not a cross-machine, multi-process or production load test.
- No universal latency SLO is implied and this diagnostic does not validate AGM hypotheses H1–H7.

Held-out explicitly consented real-history evaluation, independent security/privacy review, real third-party-host integration, and independent acceptance-matrix sign-off remain separate release gates. Passing this benchmark or CI does not close them.
