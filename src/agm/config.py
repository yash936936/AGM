"""Runtime configuration and API-key identity loading.

API keys are read from a local JSON file. Key values are never logged or
included in repr output. The service defaults to loopback-only binding.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_LOG = logging.getLogger(__name__)

from .models import Ctx, Tier

VALID_TIERS = {"human_verified", "tool_verified", "trusted_agent", "untrusted"}
DEFAULT_SCOPES = ("memory:read", "memory:write", "memory:delete")


def key_digest(api_key: str) -> str:
    """SHA-256 hex digest of an API key. Keys are 48 random bytes, so a fast hash is sufficient."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def format_key_hash(api_key: str) -> str:
    return "sha256:" + key_digest(api_key)


@dataclass(frozen=True)
class KeyIdentity:
    api_key: str = field(repr=False)  # legacy plaintext records only; empty when stored hashed
    ctx: Ctx
    scopes: frozenset[str]
    key_hash: str = field(default="", repr=False)  # sha256 hex digest; derived from api_key when empty

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
        digest = key_digest(candidate)
        # Iterate all configured keys; do not use the raw key as a logged/error value.
        for identity in self.identities:
            expected = identity.key_hash or key_digest(identity.api_key)
            if hmac.compare_digest(expected, digest):
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
        stored_hash = record.get("api_key_hash")
        tenant_id = record.get("tenant_id")
        writer_id = record.get("writer_id")
        tier = record.get("trust_tier", record.get("tier", "untrusted"))
        if not all(isinstance(value, str) and value.strip() for value in (tenant_id, writer_id)):
            raise ValueError(f"API key record {index} needs non-empty api_key, tenant_id, and writer_id fields.")
        if bool(api_key) == bool(stored_hash):
            raise ValueError(f"API key record {index} needs exactly one of api_key or api_key_hash.")
        if stored_hash:
            if not (isinstance(stored_hash, str) and stored_hash.startswith("sha256:")
                    and len(stored_hash) == 71 and all(c in "0123456789abcdef" for c in stored_hash[7:])):
                raise ValueError(f"API key record {index} has an invalid api_key_hash (expected sha256:<64 hex>).")
            digest, api_key = stored_hash[7:], ""
        elif isinstance(api_key, str) and api_key.strip():
            digest = key_digest(api_key)
        else:
            raise ValueError(f"API key record {index} needs non-empty api_key, tenant_id, and writer_id fields.")
        if digest in seen:
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
        identities.append(KeyIdentity(api_key=api_key, ctx=ctx, scopes=scopes, key_hash=digest))
        seen.add(digest)
    return KeyRegistry(tuple(identities))


def keys_path(path: str | Path | None = None) -> Path:
    return Path(path or os.environ.get("AGM_KEYS_FILE", "agm.keys.json")).expanduser()


def load_key_registry(path: str | Path | None = None) -> KeyRegistry:
    key_path = keys_path(path)
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


class ReloadingKeyRegistry:
    """Key registry that re-reads its file when it changes, so new keys work and removed keys stop
    working without a server restart.

    Failure policy: a missing file fails closed (no key authenticates); a malformed or invalid file
    keeps the last good registry and logs a warning, so a typo cannot lock out every agent.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = keys_path(path)
        self._lock = threading.Lock()
        self._registry = load_key_registry(self._path)  # raises on a malformed file at startup
        self._signature = self._stat()

    def _stat(self) -> tuple[int, int] | None:
        try:
            info = self._path.stat()
        except OSError:
            return None
        return (info.st_mtime_ns, info.st_size)

    @property
    def identities(self) -> tuple[KeyIdentity, ...]:
        self._refresh()
        return self._registry.identities

    def _refresh(self) -> None:
        signature = self._stat()
        if signature == self._signature:
            return
        with self._lock:
            if signature == self._signature:
                return
            try:
                self._registry = load_key_registry(self._path)  # missing file -> empty registry
            except RuntimeError as exc:
                _LOG.warning("API key file changed but is invalid; keeping the previous keys: %s", exc)
            self._signature = signature

    def authenticate(self, candidate: str | None) -> KeyIdentity | None:
        self._refresh()
        return self._registry.authenticate(candidate)


def ensure_loopback_host(host: str) -> None:
    if host.strip().lower() not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError(
            "AGM services are restricted to loopback addresses until a separate security review "
            "approves remote exposure. Use 127.0.0.1, localhost, or ::1."
        )


def database_path(path: str | None = None) -> str:
    return path or os.environ.get("AGM_DB_PATH", "./agm.db")
