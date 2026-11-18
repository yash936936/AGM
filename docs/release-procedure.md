# AGM local prototype release procedure

This procedure describes a source tag and locally installable wheel. It does not authorize remote deployment or PyPI publication. Those remain blocked by the independent security review, real-history evidence and release gates in `docs/ROADMAP.md` and `docs/acceptance/`.

## Before creating a release

1. Merge the release candidate only after exact-head CI passes on Ubuntu and Windows for Python 3.11, 3.12, 3.13 and 3.14.
2. Review `docs/STATE.md`, the newest `docs/status.md` entry, open defects and decisions. No unexplained xfails or known failing tests may remain.
3. For a retrieval release, inspect the full before/after benchmark JSON and confirm the roadmap thresholds. Record the exact source SHA, seeds, embedder/model identity, and limitations in `docs/benchmarks/`. Synthetic results must not be described as real-user evidence.
4. Confirm all changes intended for the release are merged to `main` and the working tree is clean.
5. Update `pyproject.toml` version and `CHANGELOG.md` together. Move the completed Unreleased notes into a dated version heading only after the release contents are accepted.

## Build and verify locally

Run from the repository root in a clean virtual environment:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/check_repo_hygiene.py
git diff --check
python -m pip install build
python -m build
python scripts/check_package.py
```

Inspect the generated `dist/` files. Install the wheel into a separate clean environment and run a minimal import/CLI smoke check. Do not commit build outputs, local databases, keys or benchmark histories containing private data.

## Tag the accepted source

After the checks above pass and the version/changelog are committed:

```bash
git checkout main
git pull --ff-only
git status --short
git tag -a v0.7.0 -m "AGM v0.7.0 local prototype"
git push origin v0.7.0
```

Replace the tag name and message when cutting a later version. Never move or overwrite an existing published tag. Create a GitHub release from the tag with the matching changelog notes and attach the verified wheel/sdist only if distribution is approved.

## Explicitly out of scope

- Do not publish to PyPI or enable non-loopback access based only on a green CI run.
- Do not claim production readiness, real-history performance, third-party host compatibility or independent security approval without their separate evidence and sign-offs.
