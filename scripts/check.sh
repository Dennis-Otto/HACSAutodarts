#!/usr/bin/env bash

# Run the same checks as the CI test job: pytest with the coverage gate, Ruff,
# strict mypy and the Node tests. The Docker end-to-end tests run separately
# (see docs/development.md).

set -euo pipefail

cd "$(dirname -- "${BASH_SOURCE[0]}")/.."

pytest -q --timeout=30 --cov
ruff check custom_components tests .github/scripts scripts
ruff format --check custom_components tests .github/scripts scripts
mypy
npm test
echo "All local checks passed."
