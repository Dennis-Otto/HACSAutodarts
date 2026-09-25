# Contributing

Contributions are welcome through issues and pull requests.
Participation follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and project decision-making is described in [GOVERNANCE.md](GOVERNANCE.md).
Use [SUPPORT.md](SUPPORT.md) to choose the correct public support channel and [SECURITY.md](SECURITY.md) for private vulnerability reports.

All changes, including release version commits, reach the protected `main` branch through pull requests. Pull requests must pass every required check before they are merged.

## Requirements for changes

- New functionality and bug fixes must include automated tests. Use pytest for integration behavior and extend the Docker end-to-end test in `tests/e2e/` when a user-visible Home Assistant flow changes.
- Code must pass Ruff with the rules configured in `pyproject.toml` and remain compatible with the Home Assistant version used by the tests.
- User-facing text belongs in `strings.json` and the English and German translations.
- Update the README or `docs/` when behavior, setup, or supported versions change.
- Local Board Manager communication must not log, store, or expose the board API key. Cloud tokens remain in the config entry.

Before opening a pull request, run:

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements-test.txt
.venv/bin/pytest -q
.venv/bin/ruff check custom_components tests .github/scripts
bash tests/e2e/run.sh
```

The end-to-end test requires Docker with Compose.

Do not include real credentials, board IDs, API keys, private network addresses, or logs containing personal data. Use reserved documentation addresses such as `192.0.2.10` and clearly synthetic values in tests and documentation.
