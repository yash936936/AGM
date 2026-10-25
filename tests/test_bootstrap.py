from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agm.bootstrap import bootstrap_owner
from agm.config import load_key_registry


def test_bootstrap_owner_creates_authenticated_scoped_admin_key(tmp_path: Path) -> None:
    path = tmp_path / "private" / "agm.keys.json"
    key = bootstrap_owner(path, tenant_id="owner-tenant", writer_id="owner-writer", project="work")
    assert key.startswith("agm_")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["keys"]) == 1
    identity = load_key_registry(path).authenticate(key)
    assert identity is not None
    assert identity.ctx.tenant_id == "owner-tenant"
    assert identity.ctx.writer_id == "owner-writer"
    assert identity.ctx.project == "work"
    assert identity.allows("admin")
    assert key not in repr(identity)
    if os.name == "posix":
        assert path.stat().st_mode & 0o077 == 0


def test_bootstrap_owner_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "agm.keys.json"
    path.write_text('{"keys": []}\n', encoding="utf-8")
    with pytest.raises(FileExistsError):
        bootstrap_owner(path, tenant_id="owner-tenant")
    assert path.read_text(encoding="utf-8") == '{"keys": []}\n'


def test_bootstrap_owner_rejects_blank_identity(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        bootstrap_owner(tmp_path / "agm.keys.json", tenant_id="  ")


def test_cli_bootstrap_owner_creates_file_without_printing_key(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    keys = tmp_path / "agm.keys.json"
    env = os.environ.copy()
    src = str(root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(
        [sys.executable, "-m", "agm", "bootstrap-owner", "--keys", str(keys), "--tenant", "cli-owner"],
        cwd=root, env=env, capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert keys.exists()
    key = json.loads(keys.read_text(encoding="utf-8"))["keys"][0]["api_key"]
    assert key not in result.stdout
    assert "Owner key file created" in result.stdout
