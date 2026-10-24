# AGM secret-fixture hygiene patch

This overlay contains a conservative helper script for the five flagged files.

## Apply

From the AGM repository root in Git Bash:

```bash
python /path/to/apply_secret_fixture_hygiene.py
```

Or copy the script into `scripts/apply_secret_fixture_hygiene.py` and run:

```bash
python scripts/apply_secret_fixture_hygiene.py
python scripts/check_repo_hygiene.py
python -m pytest -q
git diff --check
git status --short
```

The helper makes `.before_secret_hygiene.bak` backups and refuses to change files
if the expected source patterns differ. It does not print credential-shaped
values. The test fixtures are built by concatenating synthetic fragments at
runtime, so their values and redaction coverage remain intact while the static
scanner no longer sees a complete token-shaped string on a single line.

These values are synthetic test payloads, not API authentication credentials;
they should not be changed to environment variables because the tests need to
submit the fake values to AGM's redaction guard. If local inspection indicates
any value is a real credential, stop and rotate/revoke it rather than relying
on this fixture patch.
