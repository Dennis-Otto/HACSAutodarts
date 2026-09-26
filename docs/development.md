# Development

[← Documentation](README.md)

## Project layout

| Path | Contents |
| --- | --- |
| `custom_components/autodarts/` | The integration |
| `custom_components/autodarts/frontend/autodarts-card.js` | The six dashboard cards, served by the integration |
| `blueprints/automation/autodarts/` | Automation blueprints |
| `tests/` | Unit and integration tests with `pytest-homeassistant-custom-component` |
| `tests/frontend/` | Node tests of the card logic, including property-based tests with fast-check |
| `tests/e2e/` | Docker end-to-end test, demo instance, browser test and screenshot tool |
| `docs/` | Documentation, with German translations in `docs/de/` |

## Tests

Python 3.14 and Node.js 24:

```sh
python3.14 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements-test.txt
.venv/bin/pytest --cov          # fails below 95 % coverage
.venv/bin/ruff check custom_components tests .github/scripts
.venv/bin/ruff format --check custom_components tests .github/scripts
.venv/bin/mypy                  # strict typing of the integration
npm ci
npm test                        # includes property-based fuzzing with fast-check
```

Without a local Python, run the same in Docker:

```sh
docker run --rm -v "$PWD:/src:ro" python:3.14 sh -c \
  "cp -r /src /work && cd /work && pip install -q -r requirements-test.txt && pytest --cov"
```

The test suite covers:

- config flows, discovery, migration and reauthentication;
- realtime and poll reconciliation, both Board Manager generations and failure recovery;
- the training rules and every platform;
- repairs, diagnostics and the dashboard card registration;
- every blueprint, run by Home Assistant's automation engine.

The card logic is also fuzzed with [fast-check](https://fast-check.dev/): thousands of random and hostile inputs per run check that escaping, bed geometry, the heatmap and the history parser never break.

## Docker end-to-end test

The [end-to-end test](../tests/e2e/README.md) starts a real Home Assistant container with this integration and a simulated Board Manager. It runs onboarding, setup, all controls, realtime darts, persistence, diagnostics and removal:

```sh
BOARD_MANAGER=1 bash tests/e2e/run.sh
BOARD_MANAGER=2 bash tests/e2e/run.sh   # includes discovery by mDNS
```

## Demo instance and browser test

`tests/e2e/demo.sh` starts Home Assistant with a simulated board, a finished training session and a dashboard with all cards at <http://127.0.0.1:18124/autodarts-demo/board>. Login is not needed from the local network.

`tests/e2e/browser.sh` checks the cards in Chromium against the demo:

- the card is registered on every load;
- the live visit, highlights and controls with confirmation;
- the training heatmap and history, and the status card;
- all editors and the light theme.

## Screenshots

`tests/e2e/screenshots.sh` regenerates every image in `docs/images/en` and `docs/images/de` from the demo, including the animated GIF. Every image shows the simulated board, so no personal data can appear. The tool never opens the network search, which would list real boards.

## Diagrams

The architecture diagram is written in Mermaid in `docs/diagrams/` and rendered as PNG images for light and dark themes, because the GitHub app and HACS do not render Mermaid. After changing a diagram, run:

```sh
bash scripts/render_diagrams.sh
```

## Continuous integration

Every pull request runs:

- pytest with a coverage gate, Ruff, strict mypy and the Node tests;
- the Docker end-to-end test against both Board Manager generations, and the browser test;
- HACS validation and hassfest;
- actionlint, CodeQL and dependency review;
- Gitleaks and an SPDX SBOM.

OpenSSF Scorecard evaluates the repository weekly and on every push to `main`.

Every dependency is pinned:

- Actions and container images by commit hash or digest.
- Python tools with hashes, in `requirements-test.txt` (compiled from `requirements-test.in` with `pip-compile --generate-hashes`) and `tests/e2e/requirements-browser.txt`.
- Node tools by `package-lock.json`.

Dependabot keeps all of them current.

## Releases

See the [release guide](releases.md).

## Conventions

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/), for example `feat:`, `fix:` and `docs:`.
- User-facing text goes into `strings.json` and both translations; `strings.json` equals `translations/en.json`.
- New behaviour needs tests, and new user-facing features need documentation in English and German.
