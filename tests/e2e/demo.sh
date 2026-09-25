#!/usr/bin/env bash

# Start a disposable demo instance with a simulated board and the Autodarts card.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_BIN="${DOCKER_BIN:-docker}"
E2E_PORT="${E2E_PORT:-18124}"
PROJECT_NAME="${E2E_PROJECT_NAME:-autodarts_demo}"
COMPOSE=("${DOCKER_BIN}" compose --project-name "${PROJECT_NAME}" --file compose.yaml --file compose.demo.yaml)

export E2E_PORT
export DEMO_LANGUAGE="${DEMO_LANGUAGE:-en}"
# Keep container paths such as /e2e unchanged when running from Git Bash on Windows.
export MSYS_NO_PATHCONV=1

cd "${SCRIPT_DIR}"
"${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
"${COMPOSE[@]}" up --detach --wait --wait-timeout 300
if ! "${COMPOSE[@]}" exec -T homeassistant python3 /e2e/demo.py; then
	"${COMPOSE[@]}" logs --no-color --tail 200 || true
	exit 1
fi

echo "Demo ready: http://127.0.0.1:${E2E_PORT}/autodarts-demo/board"
echo "Stop it with: docker compose --project-name ${PROJECT_NAME} --file ${SCRIPT_DIR}/compose.yaml down --volumes"
