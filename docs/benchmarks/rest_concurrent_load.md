# REST concurrent retrieval benchmark

**Status:** Diagnostic workload, not a production capacity or release-acceptance test.

Run from an installed development environment at the repository root:

```bash
python eval/rest_concurrent_benchmark.py --requests 200 --concurrency 8 --warmup 10 --seed-items 100 > rest-concurrent.json\n# Optional 60-second sustained local load with periodic server RSS samples:\npython eval/rest_concurrent_benchmark.py --duration-seconds 60 --concurrency 8 --warmup 10 --seed-items 100 > rest-soak.json
```

The script launches the actual AGM REST API in a separate local process, seeds synthetic facts through the public write endpoint, warms retrieval, and sends concurrent HTTP requests to `POST /v1/memory/retrieve`. It emits JSON with client-observed p50/p95/p99/min/max/mean latency, successful-request throughput, request/error counts, concurrency, elapsed time, environment metadata, and explicit limitations. Optional duration mode keeps concurrent workers active for the requested number of seconds rather than stopping at a fixed request count. Server RSS/working-set is sampled periodically when the operating system supports querying the child process; values are approximate and may be unavailable. Use the same machine, dependency set, commit, workload and server configuration for comparisons.

For a small integration check, run:

```bash
python -m pytest -q tests/test_rest_concurrent_benchmark.py
```

## Interpretation and limitations

- This measures retrieval endpoint latency over loopback HTTP, including HTTP handling, response transfer and JSON decoding. It is not full assistant-turn latency and includes no model inference or external network.
- The test uses synthetic facts and one local server process backed by SQLite. It is not a real-user history benchmark or a third-party host integration.
- A run exits nonzero if any measured request fails; preserve the JSON report and stderr when investigating errors.
- No memory/RSS, cold-start, multi-process, long-duration soak, cross-machine, or production load measurement is included.
- This diagnostic has no universal latency SLO and does not validate AGM hypotheses H1–H7. Do not infer production readiness from a successful run.

The repeated-run synthetic retrieval benchmark remains a separate sequential microbenchmark. For external release acceptance, held-out explicitly consented real-history evaluation, independent security/privacy review, and an actual third-party-host integration remain required.
