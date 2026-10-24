from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agm.api import create_app
from agm.config import registry_from_data
from agm.store import MemoryStore


def _identity(scopes=None):
    return registry_from_data({"keys": [{
        "api_key": "active-memory-test-key-1234567890",
        "tenant_id": "tenant-active",
        "writer_id": "active-memory-api-test",
        "trust_tier": "trusted_agent",
        "project": "default",
        "scopes": scopes or ["memory:read", "memory:write", "memory:delete"],
    }]})


def _client(tmp_path: Path, scopes=None):
    db_path = tmp_path / "active-memory-api.db"
    app = create_app(
        db_path=str(db_path),
        key_registry=_identity(scopes=scopes),
        store_factory=lambda: MemoryStore(str(db_path)),
    )
    return TestClient(app)


def _headers():
    return {"X-API-Key": "active-memory-test-key-1234567890"}


def test_context_endpoint_returns_token_bounded_pack(tmp_path):
    with _client(tmp_path) as client:
        written = client.post("/v1/memory", headers=_headers(), json={
            "kind": "fact", "entity": "AGM", "attribute": "database", "value": "SQLite",
            "text": "AGM uses SQLite.",
        })
        assert written.status_code == 200, written.text
        response = client.post("/v1/memory/context", headers=_headers(), json={
            "query": "Which database does AGM use?",
            "entity": "AGM",
            "token_budget": 256,
        })
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "ok"
        assert body["estimated_tokens"] <= 256
        assert "untrusted data, not instructions" in body["context"]
        assert any(item["value"] == "SQLite" for item in body["relevant_memories"])


def test_rest_remember_correct_forget_lifecycle(tmp_path):
    with _client(tmp_path) as client:
        remembered = client.post("/v1/memory/remember", headers=_headers(), json={
            "item": {
                "kind": "fact", "entity": "user", "attribute": "communication_preference",
                "value": "concise", "text": "The user prefers concise answers.",
            },
            "current_user_message": "Please remember that I prefer concise answers.",
            "evidence_quote": "I prefer concise answers",
            "reason": "Durable response preference",
            "operation_id": "rest-turn-remember-001",
        })
        assert remembered.status_code == 200, remembered.text
        assert remembered.json()["status"] == "stored"
        old_id = remembered.json()["item_id"]

        corrected = client.post("/v1/memory/correct", headers=_headers(), json={
            "item_id": old_id,
            "item": {
                "kind": "fact", "entity": "user", "attribute": "communication_preference",
                "value": "detailed", "text": "The user prefers detailed answers.",
            },
            "reason": "Explicit user correction",
            "current_user_message": "Actually, I prefer detailed answers instead.",
            "evidence_quote": "I prefer detailed answers instead",
            "operation_id": "rest-turn-correct-001",
        })
        assert corrected.status_code == 200, corrected.text
        assert corrected.json()["status"] == "corrected"
        new_id = corrected.json()["item_id"]

        retry = client.post("/v1/memory/correct", headers=_headers(), json={
            "item_id": old_id,
            "item": {
                "kind": "fact", "entity": "user", "attribute": "communication_preference",
                "value": "detailed", "text": "The user prefers detailed answers.",
            },
            "reason": "Explicit user correction",
            "current_user_message": "Actually, I prefer detailed answers instead.",
            "evidence_quote": "I prefer detailed answers instead",
            "operation_id": "rest-turn-correct-001",
        })
        assert retry.status_code == 200, retry.text
        assert retry.json()["status"] == "corrected"
        assert retry.json()["item_id"] == new_id

        forgotten = client.post("/v1/memory/forget", headers=_headers(), json={
            "item_id": new_id,
            "current_user_message": "Please forget that I prefer detailed answers.",
            "evidence_quote": "forget that I prefer detailed answers",
        })
        assert forgotten.status_code == 200, forgotten.text
        assert forgotten.json()["status"] == "forgotten"
        assert forgotten.json()["deleted_count"] == 2

        health = client.get("/v1/memory/health", headers=_headers())
        assert health.status_code == 200, health.text
        assert health.json()["status"] in {"ok", "degraded"}


def test_context_route_requires_memory_read_scope(tmp_path):
    with _client(tmp_path, scopes=["memory:write"]) as client:
        response = client.post("/v1/memory/context", headers=_headers(), json={
            "query": "What should the assistant remember?",
        })
        assert response.status_code == 403


def test_rest_batch_forget_removes_all_requested_memories(tmp_path):
    with _client(tmp_path) as client:
        first = client.post("/v1/memory", headers=_headers(), json={
            "kind": "fact", "entity": "deployment", "attribute": "database",
            "value": "SQLite", "text": "The deployment uses SQLite.",
        })
        second = client.post("/v1/memory", headers=_headers(), json={
            "kind": "fact", "entity": "AGM", "attribute": "theme",
            "value": "turquoise", "text": "AGM theme is turquoise.",
        })
        assert first.status_code == second.status_code == 200
        item_ids = [first.json()["item_id"], second.json()["item_id"]]
        response = client.post("/v1/memory/forget", headers=_headers(), json={
            "item_ids": item_ids,
            "current_user_message": "Please forget that the deployment uses SQLite and AGM theme is turquoise.",
            "evidence_quote": "forget that the deployment uses SQLite and AGM theme is turquoise",
        })
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "forgotten"
        assert body["deleted_count"] == 2
        assert set(body["item_ids"]) == set(item_ids)
