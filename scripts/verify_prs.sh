#!/usr/bin/env bash
# Verify the current heads of AGM PR #10 and PR #11 in isolated worktrees.
# Run from any checkout of yash936936/AGM with git + Python 3.11+ installed.
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

for cmd in git python; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing required command: $cmd" >&2; exit 2; }
done

VERIFY_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/agm-pr-verification.XXXXXX")"
cleanup() {
  git -C "$REPO_ROOT" worktree remove --force "$VERIFY_ROOT/pr10" >/dev/null 2>&1 || true
  git -C "$REPO_ROOT" worktree remove --force "$VERIFY_ROOT/pr11" >/dev/null 2>&1 || true
  rm -rf "$VERIFY_ROOT"
}
trap cleanup EXIT INT TERM

echo "Fetching PR head refs..."
git fetch --no-tags origin +refs/pull/10/head:refs/verify/pr10
git fetch --no-tags origin +refs/pull/11/head:refs/verify/pr11

verify_pr() {
  local number="$1"
  local ref="refs/verify/pr$number"
  local path="$VERIFY_ROOT/pr$number"

  echo
  echo "============================================================"
  echo "Verifying PR #$number at $(git rev-parse "$ref")"
  echo "============================================================"

  git worktree add --detach "$path" "$ref"
  python -m venv "$path/.verify-venv"

  local py="$path/.verify-venv/bin/python"
  local pip="$path/.verify-venv/bin/pip"
  if [[ ! -x "$py" ]]; then
    # Windows Python venvs expose executables under Scripts.
    py="$path/.verify-venv/Scripts/python.exe"
    pip="$path/.verify-venv/Scripts/pip.exe"
  fi
  if [[ ! -x "$py" ]]; then
    echo "Could not locate Python in verification venv: $path/.verify-venv" >&2
    return 2
  fi

  "$py" -m pip install --upgrade pip
  "$py" -m pip install -e "$path[dev]"

  if [[ -f "$path/scripts/check_repo_hygiene.py" ]]; then
    "$py" "$path/scripts/check_repo_hygiene.py"
  fi
  git -C "$path" diff --check
  "$py" -m pytest -q

  if [[ -f "$path/scripts/check_package.py" ]]; then
    "$py" "$path/scripts/check_package.py"
  else
    echo "NOTE: PR #$number does not contain scripts/check_package.py; wheel-content check not available on this ref."
  fi

  echo "PASS: test and available package checks completed for PR #$number."
  git worktree remove --force "$path"
}

verify_pr 10
verify_pr 11

echo
echo "PASS: verification completed for PR #10 and PR #11."
echo "This script does not replace held-out real-history evaluation or an independent security/privacy review."
