# M0 release-gate addendum

Update this table with actual evidence from the target checkout. Do not mark remote CI passed based only on a local run.

| Gate | Evidence command / artifact | Status until evidence is attached |
|---|---|---|
| Local full suite | `python -m pytest -q` | User reported 149 passed before this addendum's acceptance tests; rerun after applying this overlay |
| Persistent cross-session recall | `python -m pytest -v tests/test_m0_history_acceptance.py` | Pending rerun |
| Tenant isolation | Same test file, tenant-boundary case | Pending rerun |
| Correction/current-history behavior | Same test file, correction case | Pending rerun |
| Delete after reopen/rebuild | Same test file, deletion case | Pending rerun |
| Repository hygiene | `python scripts/check_repo_hygiene.py` | Pending run on the actual checkout |
| Patch whitespace | `git diff --check` | Pending run |
| Tracked secret/database scan | `git ls-files` plus manual review of scanner findings | Pending run; automated scan is heuristic |
| Remote CI Python 3.11 | Successful GitHub Actions job URL and commit SHA | Pending remote run |
| Remote CI Python 3.12 | Successful GitHub Actions job URL and commit SHA | Pending remote run |
| Remote CI Python 3.13 | Successful GitHub Actions job URL and commit SHA | Pending remote run |
| Consented, de-identified held-out real-history evaluation | Dataset version/hash, preregistered protocol, aggregate report, reviewer sign-off | Not run; no eligible dataset supplied |
| Production security/privacy review | Review artifact covering authz, retention, deletion, backup/WAL, incident response | Not established |

## Repository hygiene scanner limitations

The scanner checks tracked filenames and a small set of high-confidence token patterns. It cannot detect every secret, credential format, binary artifact, or historical secret in Git history. If a secret was ever committed, removing it from the current tree is not sufficient; revoke/rotate it and follow the repository's history-remediation process.
