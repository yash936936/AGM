#!/usr/bin/env python3
"""Concurrent end-to-end HTTP benchmark for the local AGM REST API.

Uses synthetic records and loopback HTTP. Diagnostic only, not production capacity evidence.
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


def process_rss_bytes(pid: int) -> int | None:
    """Return RSS/working-set bytes where the OS exposes a process interface."""
    try:
        if sys.platform.startswith("linux"):
            for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
        elif sys.platform == "darwin":
            output = subprocess.check_output(
                ["ps", "-o", "rss=", "-p", str(pid)], text=True, timeout=2
            ).strip()
            return int(output) * 1024 if output else None
        elif os.name == "nt":
            script = f"(Get-Process -Id {pid} -ErrorAction Stop).WorkingSet64"
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                text=True, timeout=3,
            ).strip()
            return int(output) if output else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return None


async def main_async(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="agm-rest-bench-", ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        key_file, db_file = root / "keys.json", root / "bench.db"
        key_file.write_text(json.dumps({"keys": [{
            "api_key": API_KEY, "tenant_id": "bench", "writer_id": "bench-agent",
            "trust_tier": "trusted_agent", "scopes": ["memory:read", "memory:write"],
        }]}), encoding="utf-8")
        port = free_port()
        env = {**os.environ, "AGM_KEYS_FILE": str(key_file), "AGM_DB_PATH": str(db_file)}
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        proc = subprocess.Popen(
            [sys.executable, "-m", "agm", "serve-api", "--host", "127.0.0.1", "--port", str(port)],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags,
        )
        headers = {"Authorization": f"Bearer {API_KEY}"}
        try:
            async with httpx.AsyncClient(
                base_url=f"http://127.0.0.1:{port}", headers=headers, timeout=10.0
            ) as client:
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

                for i in range(args.seed_items):
                    response = await client.post("/v1/memory", json={
                        "kind": "fact", "entity": f"service-{i}", "attribute": "owner",
                        "value": f"team-{i % 7}", "text": f"service-{i} owner is team-{i % 7}",
                    })
                    response.raise_for_status()

                payload = {"query": "service owner team"}
                for _ in range(args.warmup):
                    (await client.post("/v1/memory/retrieve", json=payload)).raise_for_status()

                latencies: list[float] = []
                errors: list[str] = []
                rss_samples: list[int] = []
                lock = asyncio.Lock()
                stop_sampling = asyncio.Event()

                async def sample_rss() -> None:
                    while not stop_sampling.is_set():
                        # Off the event loop: on Windows this spawns PowerShell (can take >1 s) and would
                        # otherwise freeze the load workers and distort the measured latencies.
                        rss = await asyncio.to_thread(process_rss_bytes, proc.pid)
                        if rss is not None:
                            rss_samples.append(rss)
                        try:
                            await asyncio.wait_for(stop_sampling.wait(), timeout=args.sample_interval)
                        except asyncio.TimeoutError:
                            pass

                sampler = asyncio.create_task(sample_rss())
                start = time.perf_counter()
                deadline = start + args.duration_seconds if args.duration_seconds is not None else None

                async def worker(count: int | None) -> None:
                    local_latencies: list[float] = []
                    local_errors: list[str] = []
                    completed = 0
                    # Each worker makes at least one request even if the duration window is already over.
                    while (count is None or completed < count) and (
                        completed == 0 or deadline is None or time.perf_counter() < deadline
                    ):
                        began = time.perf_counter()
                        try:
                            response = await client.post("/v1/memory/retrieve", json=payload)
                            elapsed = (time.perf_counter() - began) * 1000
                            if response.status_code != 200:
                                local_errors.append(f"http_{response.status_code}")
                            else:
                                response.json()
                                local_latencies.append(elapsed)
                        except (httpx.HTTPError, ValueError) as exc:
                            local_errors.append(type(exc).__name__)
                        completed += 1
                    async with lock:
                        latencies.extend(local_latencies)
                        errors.extend(local_errors)

                workers = args.concurrency
                if deadline is None:
                    workers = min(args.concurrency, args.requests)
                    base_count, extra = divmod(args.requests, workers)
                    tasks = [worker(base_count + (1 if i < extra else 0)) for i in range(workers)]
                else:
                    tasks = [worker(None) for _ in range(workers)]
                try:
                    await asyncio.gather(*tasks)
                finally:
                    stop_sampling.set()
                    await sampler
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
                        "endpoint": "POST /v1/memory/retrieve",
                        "requests_requested": args.requests,
                        "duration_seconds": args.duration_seconds,
                        "sample_interval_seconds": args.sample_interval,
                        "requests_succeeded": len(latencies), "errors": len(errors),
                        "concurrency": workers, "warmup_requests": args.warmup,
                        "seed_items": args.seed_items, "timeout_seconds": 10,
                    },
                    "latency_ms": {
                        "p50": percentile(latencies, 50), "p95": percentile(latencies, 95),
                        "p99": percentile(latencies, 99),
                        "min": round(min(latencies), 3) if latencies else None,
                        "max": round(max(latencies), 3) if latencies else None,
                        "mean": round(statistics.fmean(latencies), 3) if latencies else None,
                    },
                    "throughput": {
                        "elapsed_seconds": round(elapsed_s, 4),
                        "successful_requests_per_second": round(len(latencies) / elapsed_s, 3) if elapsed_s else 0,
                    },
                    "error_types": {kind: errors.count(kind) for kind in sorted(set(errors))},
                    "server_rss_bytes": {
                        "samples": len(rss_samples),
                        "min": min(rss_samples) if rss_samples else None,
                        "max": max(rss_samples) if rss_samples else None,
                        "mean": round(statistics.fmean(rss_samples)) if rss_samples else None,
                        "measurement": "periodic process RSS/working-set samples; null when OS query unavailable",
                    },
                    "limitations": [
                        "Synthetic data and loopback HTTP only; no network, model inference, or real host.",
                        "Measures retrieval endpoint latency, not full assistant-turn latency.",
                        "Single local server process and SQLite; results depend on machine and OS.",
                        "RSS/working-set sampling is approximate and OS-dependent.",
                        "No performance threshold or production-readiness claim is implied.",
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
    parser.add_argument("--duration-seconds", type=float)
    parser.add_argument("--sample-interval", type=float, default=1.0)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1 or args.warmup < 0 or args.seed_items < 0:
        parser.error("requests/concurrency must be positive; warmup/seed-items must be non-negative")
    if args.duration_seconds is not None and args.duration_seconds <= 0:
        parser.error("duration-seconds must be positive")
    if args.sample_interval <= 0:
        parser.error("sample-interval must be positive")
    try:
        return asyncio.run(main_async(args))
    except (RuntimeError, httpx.HTTPError) as exc:
        print(f"benchmark failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
