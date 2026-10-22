"""Runtime configuration and API-key identity loading.

API keys are read from a local JSON file. Key values are never logged or
included in repr output. The service defaults to loopback-only binding.
"""
from __future__ import annotations

import hmac
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import Ctx, Tier

VALID_TIERS = {"human_verified", "tool_verified", "trusted_agent", "untrusted"}
DEFAULT_SCOPES = ("memory:read", "memory:write", "memory:delete")


@dataclass(frozen=True)
class KeyIdentity:
    api_key: str = field(repr=False)
    ctx: Ctx
    scopes: frozenset[str]

    def allows(self, scope: str) -> bool:
        return "*" in self.scopes or "admin" in self.scopes or scope in self.scopes


@dataclass(frozen=True)
class KeyRegistry:
    identities: tuple[KeyIdentity, ...]

    def authenticate(self, candidate: str | None) -> KeyIdentity | None:
        if not candidate:
            # Still do a fixed dummy comparison to avoid a trivial missing-key fast path.
            hmac.compare_digest("agm-missing-key-dummy", "agm-another-dummy-key")
            return None
        matched: KeyIdentity | None = None
        # Iterate all configured keys; do not use the raw key as a logged/error value.
        for identity in self.identities:
            if hmac.compare_digest(identity.api_key, candidate):
                matched = identity
        return matched


def _load_records(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict) and isinstance(raw.get("keys"), list):
        return [item for item in raw["keys"] if isinstance(item, dict)]
    if isinstance(raw, dict) and isinstance(raw.get("keys"), dict):
        records = []
        for key, value in raw["keys"].items():
            if isinstance(value, dict):
                records.append({"api_key": key, **value})
        return records
    # Also accept the simple mapping {"api-key": {"tenant_id": ...}}.
    if isinstance(raw, dict):
        return [
            {"api_key": key, **value}
            for key, value in raw.items()
            if isinstance(value, dict) and "tenant_id" in value
        ]
    raise ValueError("API key configuration must be a JSON object containing a 'keys' list or mapping.")


def registry_from_data(raw: Any) -> KeyRegistry:
    identities: list[KeyIdentity] = []
    seen: set[str] = set()
    for index, record in enumerate(_load_records(raw)):
        api_key = record.get("api_key")
        tenant_id = record.get("tenant_id")
        writer_id = record.get("writer_id")
        tier = record.get("trust_tier", record.get("tier", "untrusted"))
        if not all(isinstance(value, str) and value.strip() for value in (api_key, tenant_id, writer_id)):
            raise ValueError(f"API key record {index} needs non-empty api_key, tenant_id, and writer_id fields.")
        if api_key in seen:
            raise ValueError(f"Duplicate API key in record {index}.")
        if tier not in VALID_TIERS:
            raise ValueError(f"API key record {index} has an invalid trust tier.")
        scopes_value = record.get("scopes", list(DEFAULT_SCOPES))
        if not isinstance(scopes_value, list) or not all(isinstance(s, str) and s for s in scopes_value):
            raise ValueError(f"API key record {index} scopes must be a list of strings.")
        scopes = frozenset(scopes_value)
        ctx = Ctx(
            tenant_id=tenant_id,
            writer_id=writer_id,
            tier=tier,
            project=str(record.get("project", "default")),
            agent=str(record.get("agent", "")),
        )
        identities.append(KeyIdentity(api_key=api_key, ctx=ctx, scopes=scopes))
        seen.add(api_key)
    return KeyRegistry(tuple(identities))


def load_key_registry(path: str | Path | None = None) -> KeyRegistry:
    configured = path or os.environ.get("AGM_KEYS_FILE", "agm.keys.json")
    key_path = Path(configured).expanduser()
    try:
        data = json.loads(key_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        # An unconfigured server remains closed: every request receives 401.
        return KeyRegistry(())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in API key file {key_path}.") from exc
    except OSError as exc:
        raise RuntimeError(f"Cannot read API key file {key_path}.") from exc
    try:
        return registry_from_data(data)
    except ValueError as exc:
        raise RuntimeError(f"Invalid API key configuration in {key_path}: {exc}") from exc


def runtime_identity_from_env() -> tuple[Ctx, frozenset[str]]:
    """Resolve the explicitly configured identity for a local MCP process."""
    tenant = os.environ.get("AGM_TENANT", "").strip()
    writer = os.environ.get("AGM_WRITER", "").strip()
    tier = os.environ.get("AGM_TIER", "").strip()
    missing = [name for name, value in (("AGM_TENANT", tenant), ("AGM_WRITER", writer), ("AGM_TIER", tier)) if not value]
    if missing:
        raise RuntimeError("MCP identity is not configured; set " + ", ".join(missing) + ".")
    if tier not in VALID_TIERS:
        raise RuntimeError("AGM_TIER must be one of: " + ", ".join(sorted(VALID_TIERS)) + ".")
    scopes_raw = os.environ.get("AGM_SCOPES", ",".join(DEFAULT_SCOPES))
    scopes = frozenset(value.strip() for value in scopes_raw.split(",") if value.strip())
    return Ctx(
        tenant_id=tenant,
        writer_id=writer,
        tier=tier,  # type: ignore[arg-type]
        project=os.environ.get("AGM_PROJECT", "default"),
        agent=os.environ.get("AGM_AGENT", ""),
    ), scopes


def ensure_loopback_host(host: str) -> None:
    if host.strip().lower() not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError(
            "AGM services are restricted to loopback addresses until a separate security review "
            "approves remote exposure. Use 127.0.0.1, localhost, or ::1."
        )


def database_path(path: str | None = None) -> str:
    return path or os.environ.get("AGM_DB_PATH", "./agm.db")
