#!/usr/bin/env python3
"""Check tracked AGM files for common accidental secret/data artifacts.

Uses `git ls-files`; it never prints file contents or matched secret values.
Exit 0 means no configured indicators were found, not a guarantee that no
secret exists. Run from any directory inside a Git checkout.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SUSPICIOUS_NAMES = re.compile(
    r"(^|/)(\.env(?:\..*)?|id_rsa(?:\.pub)?|id_ed25519(?:\.pub)?|"
    r"credentials?(?:\.json)?|secrets?\.(?:json|ya?ml)|.*\.(?:pem|p12|pfx|key))$",
    re.IGNORECASE,
)
DATABASE_NAME = re.compile(r"(^|/)[^/]*\.(?:db|sqlite|sqlite3)(?:-(?:wal|shm|journal))?$", re.I)
SECRET_PATTERNS = [
    ("private-key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("OpenAI-style API key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
]
TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".ini", ".cfg", ".txt", ".sh", ".ps1", ".example"}


def git_files() -> list[str]:
    proc = subprocess.run(["git", "ls-files", "-z"], check=False, capture_output=True)
    if proc.returncode:
        print("ERROR: run this script from inside the AGM Git checkout (git ls-files failed).", file=sys.stderr)
        raise SystemExit(2)
    return [p.decode("utf-8", "surrogateescape") for p in proc.stdout.split(b"\0") if p]


def main() -> int:
    findings: list[tuple[str, str]] = []
    paths = git_files()
    for rel in paths:
        normalized = rel.replace("\\", "/")
        base = Path(normalized).name.lower()
        # A committed example template is allowed only for .env.example.
        if SUSPICIOUS_NAMES.search(normalized) and base != ".env.example":
            findings.append((rel, "suspicious credential/config filename"))
        if DATABASE_NAME.search(normalized):
            findings.append((rel, "tracked local database or SQLite sidecar"))
        p = Path(rel)
        if p.suffix.lower() not in TEXT_SUFFIXES or base == ".env.example":
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                findings.append((rel, f"possible {label}"))
    if findings:
        print("Repository hygiene scan: FINDINGS")
        for rel, label in sorted(set(findings)):
            print(f"- {rel}: {label}")
        print("Inspect findings locally. This scanner never prints matched secret values.")
        return 1
    print(f"Repository hygiene scan: PASS ({len(paths)} tracked paths checked; configured patterns only).")
    print("Note: this is a heuristic scan, not proof that the repository contains no secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
