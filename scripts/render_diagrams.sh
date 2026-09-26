#!/usr/bin/env bash

# Render the Mermaid diagrams in docs/diagrams as PNG images, once for light and
# once for dark themes. Markdown viewers without Mermaid, such as the GitHub app
# and HACS, show these images instead of raw diagram code.

set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_BIN="${DOCKER_BIN:-docker}"
IMAGE="ghcr.io/mermaid-js/mermaid-cli/mermaid-cli:11.12.0@sha256:bad64c9d9ad917c8dfbe9d9e9c162b96f6615ff019b37058638d16eb27ce7783"
# Keep container paths unchanged and mount the Windows path when running from Git Bash.
export MSYS_NO_PATHCONV=1
MOUNT="$(cd "${ROOT}" && (pwd -W 2>/dev/null || pwd))"

for source in "${ROOT}"/docs/diagrams/*.mmd; do
	name="$(basename "${source}" .mmd)" # for example architecture.en
	diagram="${name%.*}"
	language="${name##*.}"
	for theme in light dark; do
		background="#ffffff"
		[[ "${theme}" == "dark" ]] && background="#0d1117"
		"${DOCKER_BIN}" run --rm --volume "${MOUNT}:/data" "${IMAGE}" \
			--input "/data/docs/diagrams/${name}.mmd" \
			--output "/data/docs/images/${language}/${diagram}-${theme}.png" \
			--configFile "/data/docs/diagrams/${theme}.json" \
			--backgroundColor "${background}" --scale 2 --width 900
		echo "rendered docs/images/${language}/${diagram}-${theme}.png"
	done
done
