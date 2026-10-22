"""Minimal authenticated REST round-trip. Start `agm serve-api` first."""
from __future__ import annotations

import os
import uuid

import httpx

BASE_URL = os.environ.get("AGM_BASE_URL", "http://127.0.0.1:8765")
API_KEY = os.environ.get("AGM_API_KEY")
if not API_KEY:
    raise SystemExit("Set AGM_API_KEY to a key from agm.keys.json before running this example.")

headers = {"X-API-Key": API_KEY}
item = {
    "kind": "fact",
    "text": "The AGM REST client example is configured for local testing.",
    "entity": "AGM REST example",
    "attribute": "status",
    "value": "configured",
    "idempotency_key": f"example-{uuid.uuid4().hex}",
}

with httpx.Client(base_url=BASE_URL, headers=headers, timeout=10.0) as client:
    write = client.post("/v1/memory", json=item)
    write.raise_for_status()
    print("write:", write.json())
    retrieved = client.post("/v1/memory/retrieve", json={
        "query": "AGM REST client status",
        "entity": "AGM REST example",
        "expand": True,
        "k": 5,
    })
    retrieved.raise_for_status()
    print("retrieve:", retrieved.json())
