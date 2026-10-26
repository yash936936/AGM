#!/usr/bin/env python3
"""Concurrent end-to-end HTTP benchmark for the local AGM REST API.

Measures client-observed POST /v1/memory/retrieve latency against a real local
AGM server process. Synthetic data only; not a production capacity test.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

API_KEY = "k-benchmark-agent-1234567890abcdef"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((p / 100) * len(ordered) + 0.999999) - 1))
    return round(ordered[index], 3)


async def main_async(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="agm-rest-bench-") as directory:
        root = Path(directory)
        key_file, db_file = root / "keys.json", root / "bench.db"
        key_file.write_text(json.dumps({"keys": [{
            "api_key": API_KEY, "tenant_id": "bench", "writer_id": "bench-agent",
            "trust_tier": "trusted_agent", "scopes": ["memory:read", "memory:write"]
        }]}), encoding="utf-8")
        port = free_port()
        env = {**os.environ, "AGM_KEYS_FILE": str(key_file), "AGM_DB_PATH": str(db_file)}
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        proc = subprocess.Popen(
            [sys.executable, "-m", "agm", "serve-api", "--host", "127.0.0.1", "--port", str(port)],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags,
        )
        base = f"http://127.0.0.1:{port}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        try:
            async with httpx.AsyncClient(base_url=base, headers=headers, timeout=10.0) as client:
                for _ in range(80):
                    if proc.poll() is not None:
                        raise RuntimeError(f"AGM API exited during startup ({proc.returncode})")
                    try:
                        response = await client.get("/healthz", timeout=0.5)
                        if response.status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(0.125)
                else:
                    raise RuntimeError("AGM API did not become healthy within 10 seconds")

                # Seed through the public API so benchmark setup exercises the supported contract.
                for i in range(args.seed_items):
                    response = await client.post("/v1/memory", json={
                        "kind": "fact", "entity": f"service-{i}", "attribute": "owner",
                        "value": f"team-{i % 7}", "text": f"service-{i} owner is team-{i % 7}",
                    })
                    response.raise_for_status()

                payload = {"query": "service owner team"}
                for _ in range(args.warmup):
                    response = await client.post("/v1/memory/retrieve", json=payload)
                    response.raise_for_status()

                latencies: list[float] = []
                errors: list[str] = []
                lock = asyncio.Lock()
                start = time.perf_counter()

                async def worker(count: int) -> None:
                    local_latencies: list[float] = []
                    local_errors: list[str] = []
                    for _ in range(count):
                        began = time.perf_counter()
                        try:
                            response = await client.post("/v1/memory/retrieve", json=payload)
                            elapsed = (time.perf_counter() - began) * 1000
                            if response.status_code != 200:
                                local_errors.append(f"http_{response.status_code}")
                            else:
                                # Parse the body so timings include response transfer and JSON decoding.
                                response.json()
                                local_latencies.append(elapsed)
                        except (httpx.HTTPError, ValueError) as exc:
                            local_errors.append(type(exc).__name__)
                    async with lock:
                        latencies.extend(local_latencies)
                        errors.extend(local_errors)

                workers = min(args.concurrency, args.requests)
                base_count, extra = divmod(args.requests, workers)
                await asyncio.gather(*(worker(base_count + (1 if i < extra else 0)) for i in range(workers)))
                elapsed_s = time.perf_counter() - start

                result = {
                    "benchmark": "agm_rest_concurrent_retrieval",
                    "status": "ok" if not errors else "completed_with_errors",
                    "environment": {
                        "python": sys.version.split()[0], "platform": platform.platform(),
                        "commit": os.environ.get("GITHUB_SHA", "not-injected"),
                        "transport": "HTTP loopback", "server": "separate AGM serve-api subprocess",
                    },
                    "workload": {
                        "endpoint": "POST /v1/memory/retrieve", "requests_requested": args.requests,
                        "requests_succeeded": len(latencies), "errors": len(errors),
                        "concurrency": workers, "warmup_requests": args.warmup,
                        "seed_items": args.seed_items, "timeout_seconds": 10,
                    },
                    "latency_ms": {
                        "p50": percentile(latencies, 50), "p95": percentile(latencies, 95),
                        "p99": percentile(latencies, 99), "min": round(min(latencies), 3) if latencies else None,
                        "max": round(max(latencies), 3) if latencies else None,
                        "mean": round(statistics.fmean(latencies), 3) if latencies else None,
                    },
                    "throughput": {
                        "elapsed_seconds": round(elapsed_s, 4),
                        "successful_requests_per_second": round(len(latencies) / elapsed_s, 3) if elapsed_s else 0,
                    },
                    "error_types": {kind: errors.count(kind) for kind in sorted(set(errors))},
                    "limitations": [
                        "Synthetic data and loopback HTTP only; no network, model inference, or real host.",
                        "Measures retrieval endpoint client-observed latency, not full assistant-turn latency.",
                        "Single local server process and SQLite database; results depend on machine and OS.",
                        "No memory/RSS, cold-start, multi-process, long-duration soak, or real-history measurement.",
                        "No pass/fail performance threshold is implied by this diagnostic.",
                    ],
                }
                print(json.dumps(result, indent=2, sort_keys=True))
                return 0 if not errors else 1
        finally:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--seed-items", type=int, default=100)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1 or args.warmup < 0 or args.seed_items < 0:
        parser.error("requests/concurrency must be positive; warmup/seed-items must be non-negative")
    try:
        return asyncio.run(main_async(args))
    except (RuntimeError, httpx.HTTPError) as exc:
        print(f"benchmark failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
