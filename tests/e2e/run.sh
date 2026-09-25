#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_BIN="${DOCKER_BIN:-docker}"
E2E_PORT="${E2E_PORT:-18123}"
PROJECT_NAME="${E2E_PROJECT_NAME:-autodarts_e2e}"
COMPOSE=("${DOCKER_BIN}" compose --project-name "${PROJECT_NAME}" --file compose.yaml)

export E2E_PORT
# Keep container paths such as /e2e unchanged when running from Git Bash on Windows.
export MSYS_NO_PATHCONV=1

cleanup() {
	status=$?
	trap - EXIT
	if [[ "${status}" -ne 0 ]]; then
		"${COMPOSE[@]}" ps || true
		"${COMPOSE[@]}" logs --no-color --tail 300 || true
		"${COMPOSE[@]}" exec -T homeassistant tail -n 300 /config/home-assistant.log || true
	fi
	if [[ "${KEEP_E2E:-0}" != "1" ]]; then
		"${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
	else
		echo "E2E environment kept at http://127.0.0.1:${E2E_PORT} (project ${PROJECT_NAME})."
	fi
	exit "${status}"
}
trap cleanup EXIT

cd "${SCRIPT_DIR}"
"${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
"${COMPOSE[@]}" up --detach --wait --wait-timeout 300
"${COMPOSE[@]}" exec -T homeassistant python3 /e2e/scenario.py
