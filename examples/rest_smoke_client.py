#!/usr/bin/env python3
"""Acceptance smoke test for the AGM REST API, as a plain local Python agent would use it.

Starts `python -m agm serve-api` on loopback with a temporary key file and database, then
talks to it over real HTTP (no in-process shortcuts). Exit code 0 means every check passed.

Run:  python examples/rest_smoke_client.py
"""
from __future__ import annotations

import json
import os
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
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        keys = tmp_path / "keys.json"
        keys.write_text(json.dumps({"keys": [
            {"api_key": KEY, "tenant_id": "smoke", "writer_id": "agent-1", "trust_tier": "trusted_agent",
             "scopes": ["memory:read", "memory:write", "memory:delete"]},
            {"api_key": OTHER, "tenant_id": "other", "writer_id": "agent-2", "trust_tier": "trusted_agent",
             "scopes": ["memory:read", "memory:write"]},
        ]}))
        port = free_port()
        env = {**os.environ, "AGM_KEYS_FILE": str(keys), "AGM_DB_PATH": str(tmp_path / "smoke.db")}
        proc = subprocess.Popen(
            [sys.executable, "-m", "agm", "serve-api", "--host", "127.0.0.1", "--port", str(port)],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(60):
                try:
                    if httpx.get(base + "/healthz", timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    time.sleep(0.25)
            else:
                print("server did not start")
                return 2
            h = {"Authorization": f"Bearer {KEY}"}
            with httpx.Client(base_url=base, timeout=10) as c:
                check("no key -> 401", c.post("/v1/memory/retrieve", json={"query": "x"}).status_code == 401)
                check("OpenAPI document is served", "/v1/memory" in c.get("/openapi.json").json()["paths"])
                a = c.post("/v1/memory", headers=h, json={"kind": "fact", "entity": "billing", "attribute": "owner",
                                                           "value": "team-a", "text": "billing owner is team-a"}).json()
                check("write -> added", a["status"] == "added")
                b = c.post("/v1/memory", headers=h, json={"kind": "fact", "entity": "billing", "attribute": "owner",
                                                           "value": "team-b", "text": "billing owner is team-b"}).json()
                check("correction -> superseded", b["status"] == "superseded")
                s = c.post("/v1/memory", headers=h, json={"kind": "episode", "text": f"token {SECRET}"}).json()
                check("secret redacted over HTTP", s["redactions"] >= 1)
                r = c.post("/v1/memory/retrieve", headers=h, json={"query": "who owns billing"}).json()
                vals = [i.get("value") for i in r["items"]]
                check("retrieve returns current owner only", "team-b" in vals and "team-a" not in vals)
                r2 = c.post("/v1/memory/retrieve", headers=h, json={"query": "who owns billing", "include_superseded": True}).json()
                check("include_superseded returns history", {"team-a", "team-b"} <= {i.get("value") for i in r2["items"]})
                u = c.post("/v1/memory/retrieve", headers=h, json={"query": "zebra quantum lighthouse"}).json()
                check("unanswerable query abstains", u["abstain"] is True)
                o = c.post("/v1/memory/retrieve", headers={"Authorization": f"Bearer {OTHER}"}, json={"query": "who owns billing"}).json()
                check("other tenant sees nothing", o["items"] == [])
                d = c.delete(f"/v1/memory/{b['item_id']}", headers=h)
                check("delete -> 200", d.status_code == 200)
                gone = c.post("/v1/memory/retrieve", headers=h, json={"query": "billing owner team-b", "include_superseded": True}).json()
                check("deleted item never returns", all(i["id"] != b["item_id"] for i in gone["items"]))
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    failed = [n for n, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
