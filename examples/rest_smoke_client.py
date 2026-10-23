#!/usr/bin/env python3
"""Acceptance smoke test for the AGM REST API.

Starts `python -m agm serve-api` on loopback with a temporary key file and
database, then tests the API over real HTTP.

Run: python examples/rest_smoke_client.py
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx


KEY = "k-smoke-agent-1234567890abcdef"
OTHER = "k-smoke-other-1234567890abcdef"
SECRET = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

CHECKS: list[tuple[str, bool]] = []


def check(name: str, ok: bool) -> None:
    CHECKS.append((name, bool(ok)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}", flush=True)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def stop_server(proc: subprocess.Popen[bytes]) -> None:
    """Stop the API server and wait for its process handle to close."""
    if proc.poll() is not None:
        return

    try:
        if os.name == "nt":
            # Popen must use CREATE_NEW_PROCESS_GROUP for this to work.
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proc.send_signal(signal.SIGINT)
    except (OSError, ValueError):
        if proc.poll() is None:
            proc.terminate()

    try:
        proc.wait(timeout=10)
        return
    except subprocess.TimeoutExpired:
        pass

    proc.terminate()
    try:
        proc.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass

    proc.kill()
    proc.wait(timeout=5)


def cleanup_temp_directory(tmp: tempfile.TemporaryDirectory[str]) -> None:
    """Retry cleanup because Windows may briefly retain a file handle."""
    last_error: PermissionError | None = None

    for attempt in range(20):
        try:
            tmp.cleanup()
            return
        except PermissionError as exc:
            last_error = exc
            if attempt < 19:
                time.sleep(0.25)

    # Do not silently hide a persistent file-locking error.
    if last_error is not None:
        raise last_error


def main() -> int:
    tmp = tempfile.TemporaryDirectory(prefix="agm-rest-smoke-")
    tmp_path = Path(tmp.name)
    proc: subprocess.Popen[bytes] | None = None

    try:
        keys = tmp_path / "keys.json"
        db_path = tmp_path / "smoke.db"

        keys.write_text(
            json.dumps(
                {
                    "keys": [
                        {
                            "api_key": KEY,
                            "tenant_id": "smoke",
                            "writer_id": "agent-1",
                            "trust_tier": "trusted_agent",
                            "scopes": [
                                "memory:read",
                                "memory:write",
                                "memory:delete",
                            ],
                        },
                        {
                            "api_key": OTHER,
                            "tenant_id": "other",
                            "writer_id": "agent-2",
                            "trust_tier": "trusted_agent",
                            "scopes": ["memory:read", "memory:write"],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        port = free_port()
        env = {
            **os.environ,
            "AGM_KEYS_FILE": str(keys),
            "AGM_DB_PATH": str(db_path),
        }

        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP
            if os.name == "nt"
            else 0
        )

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "agm",
                "serve-api",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

        base = f"http://127.0.0.1:{port}"

        # Wait until the API is responding.
        for _ in range(60):
            if proc.poll() is not None:
                print(
                    f"server exited early with code {proc.returncode}",
                    file=sys.stderr,
                )
                return 2

            try:
                response = httpx.get(base + "/healthz", timeout=1)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass

            time.sleep(0.25)
        else:
            print("server did not start", file=sys.stderr)
            return 2

        headers = {"Authorization": f"Bearer {KEY}"}

        with httpx.Client(base_url=base, timeout=10) as client:
            # Authentication and API discovery.
            response = client.post(
                "/v1/memory/retrieve",
                json={"query": "x"},
            )
            check("no key -> 401", response.status_code == 401)

            openapi = client.get("/openapi.json").json()
            check(
                "OpenAPI document is served",
                "/v1/memory" in openapi["paths"],
            )

            # Write a fact, then correct it.
            first = client.post(
                "/v1/memory",
                headers=headers,
                json={
                    "kind": "fact",
                    "entity": "billing",
                    "attribute": "owner",
                    "value": "team-a",
                    "text": "billing owner is team-a",
                },
            ).json()
            check("write -> added", first["status"] == "added")

            corrected = client.post(
                "/v1/memory",
                headers=headers,
                json={
                    "kind": "fact",
                    "entity": "billing",
                    "attribute": "owner",
                    "value": "team-b",
                    "text": "billing owner is team-b",
                },
            ).json()
            check(
                "correction -> superseded",
                corrected["status"] == "superseded",
            )

            # Verify secret redaction.
            secret_result = client.post(
                "/v1/memory",
                headers=headers,
                json={
                    "kind": "episode",
                    "text": f"token {SECRET}",
                },
            ).json()
            check(
                "secret redacted over HTTP",
                secret_result["redactions"] >= 1,
            )

            # Current retrieval must not return the corrected-away value.
            result = client.post(
                "/v1/memory/retrieve",
                headers=headers,
                json={"query": "who owns billing"},
            ).json()
            values = [item.get("value") for item in result["items"]]
            check(
                "retrieve returns current owner only",
                "team-b" in values and "team-a" not in values,
            )

            # Explicit history retrieval includes both versions.
            history = client.post(
                "/v1/memory/retrieve",
                headers=headers,
                json={
                    "query": "who owns billing",
                    "include_superseded": True,
                },
            ).json()
            history_values = {
                item.get("value") for item in history["items"]
            }
            check(
                "include_superseded returns history",
                {"team-a", "team-b"} <= history_values,
            )

            # An unanswerable query must abstain.
            unknown = client.post(
                "/v1/memory/retrieve",
                headers=headers,
                json={"query": "zebra quantum lighthouse"},
            ).json()
            check(
                "unanswerable query abstains",
                unknown["abstain"] is True,
            )

            # Tenant isolation.
            other_tenant = client.post(
                "/v1/memory/retrieve",
                headers={"Authorization": f"Bearer {OTHER}"},
                json={"query": "who owns billing"},
            ).json()
            check(
                "other tenant sees nothing",
                other_tenant["items"] == [],
            )

            # Delete the replacement and verify it cannot be retrieved.
            item_id = corrected["item_id"]
            deleted = client.delete(
                f"/v1/memory/{item_id}",
                headers=headers,
            )
            check("delete -> 200", deleted.status_code == 200)

            after_delete = client.post(
                "/v1/memory/retrieve",
                headers=headers,
                json={
                    "query": "billing owner team-b",
                    "include_superseded": True,
                },
            ).json()
            check(
                "deleted item never returns",
                all(item["id"] != item_id
                    for item in after_delete["items"]),
            )

    finally:
        # Shut down the server before attempting to remove its SQLite files.
        try:
            if proc is not None:
                stop_server(proc)
        finally:
            cleanup_temp_directory(tmp)

    failed = [name for name, passed in CHECKS if not passed]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())