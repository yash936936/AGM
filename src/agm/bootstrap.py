"""One-time local owner bootstrap for AGM API-key authentication.

The generated key is returned once (the CLI prints it once); only its SHA-256 hash is
persisted in a private local configuration file. This is local bootstrap, not a hosted login/OAuth implementation.
"""
from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

from .config import format_key_hash


def bootstrap_owner(
    path: str | Path,
    *,
    tenant_id: str,
    writer_id: str = "owner",
    project: str = "default",
) -> str:
    target = Path(path).expanduser()
    if not tenant_id.strip() or not writer_id.strip() or not project.strip():
        raise ValueError("tenant_id, writer_id and project must be non-empty")
    target.parent.mkdir(parents=True, exist_ok=True)
    key = "agm_" + secrets.token_urlsafe(48)
    document = {
        "keys": [{
            "api_key_hash": format_key_hash(key),
            "tenant_id": tenant_id.strip(),
            "writer_id": writer_id.strip(),
            "trust_tier": "human_verified",
            "project": project.strip(),
            "agent": "local-owner",
            "scopes": ["admin"],
        }]
    }
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(str(target), flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            target.unlink()
        except OSError:
            pass
        raise
    try:
        target.chmod(0o600)
    except OSError:
        # Windows ACLs are authoritative there; do not claim POSIX mode guarantees.
        pass
    return key
