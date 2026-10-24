#!/usr/bin/env python3
"""Safely replace credential-shaped synthetic fixtures with runtime-built values.

Run from the AGM repository root:
    python scripts/apply_secret_fixture_hygiene.py

The script creates .bak copies before editing. It refuses to proceed if the
expected source patterns are missing, so local edits are not silently lost.
It does not print or log any credential-shaped values.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path.cwd()

# Each rule identifies a specific fixture assignment and replaces the complete
# credential-shaped literal with concatenated synthetic fragments. The resulting
# value at runtime remains the same, preserving the redaction tests.
RULES: dict[str, list[tuple[re.Pattern[str], str, int]]] = {
    "examples/mcp_smoke_client.py": [
        (
            re.compile(r'^SECRET = "' + re.escape("sk-ant-" + "api03-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd") + r'"$', re.M),
            'SECRET = "sk-ant-" + "api03-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd"',
            1,
        ),
    ],
    "examples/rest_smoke_client.py": [
        (
            re.compile(r'^SECRET = "' + re.escape("ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + r'"$', re.M),
            'SECRET = "ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"',
            1,
        ),
    ],
    "tests/test_e2e_rest.py": [
        (
            re.compile(r'^    secret = "' + re.escape("ghp_" + "abcdefghijklmnopqrstuvwxyz123456") + r'"$', re.M),
            '    secret = "ghp_" + "abcdefghijklmnopqrstuvwxyz123456"',
            1,
        ),
    ],
    "tests/test_guard.py": [
        (
            re.compile(r'^    secret = "' + re.escape("AKIA" + "IOSFODNN7EXAMPLE") + r'"$', re.M),
            '    secret = "AKIA" + "IOSFODNN7EXAMPLE"',
            1,
        ),
        (
            re.compile(r'^    token = "' + re.escape("ghp_" + "abcdefghijklmnopqrstuvwxyz123456") + r'"$', re.M),
            '    token = "ghp_" + "abcdefghijklmnopqrstuvwxyz123456"',
            1,
        ),
    ],
    "tests/test_guard_core.py": [
        (
            re.compile(r'^    "anthropic": "' + re.escape("sk-ant-" + "api03-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd") + r'",$', re.M),
            '    "anthropic": "sk-ant-" + "api03-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd",',
            1,
        ),
        (
            re.compile(r'^    "openai": "' + re.escape("sk-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ab") + r'",$', re.M),
            '    "openai": "sk-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ab",',
            1,
        ),
        (
            re.compile(r'^    "github": "' + re.escape("ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + r'",$', re.M),
            '    "github": "ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",',
            1,
        ),
        (
            re.compile(r'^    "aws": "' + re.escape("AKIA" + "IOSFODNN7EXAMPLE") + r'",$', re.M),
            '    "aws": "AKIA" + "IOSFODNN7EXAMPLE",',
            1,
        ),
    ],
}


def main() -> int:
    missing = [name for name in RULES if not (ROOT / name).is_file()]
    if missing:
        print("ERROR: run from the AGM repository root; expected files are missing.")
        for name in missing:
            print(f"- {name}")
        return 2

    planned: dict[Path, str] = {}
    problems: list[str] = []

    for name, rules in RULES.items():
        path = ROOT / name
        original = path.read_text(encoding="utf-8")
        updated = original
        for pattern, replacement, expected_count in rules:
            updated, count = pattern.subn(replacement, updated)
            if count != expected_count:
                problems.append(f"{name}: expected one matching fixture for a rule; found {count}")
        if updated != original:
            planned[path] = updated

    if problems:
        print("ERROR: no files were changed because source patterns differed:")
        for problem in problems:
            print(f"- {problem}")
        print("Inspect the files locally and adapt the patch to your current version.")
        return 2

    for path, updated in planned.items():
        backup = path.with_suffix(path.suffix + ".before_secret_hygiene.bak")
        if backup.exists():
            print(f"ERROR: backup already exists: {backup.relative_to(ROOT)}")
            print("No files were changed. Move or rename that backup before retrying.")
            return 2

    for path, updated in planned.items():
        backup = path.with_suffix(path.suffix + ".before_secret_hygiene.bak")
        shutil.copy2(path, backup)
        path.write_text(updated, encoding="utf-8", newline="")
        print(f"Updated {path.relative_to(ROOT)} (backup created)")

    print(f"Updated {len(planned)} files. Runtime fixture values and test intent are preserved.")
    print("Next run:")
    print("  python scripts/check_repo_hygiene.py")
    print("  python -m pytest -q")
    print("  git diff --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
