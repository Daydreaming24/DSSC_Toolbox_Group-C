#!/usr/bin/env bash
# Bootstrap the repository environment and run the frozen all suite.
# Thin orchestration only; this command accepts no arguments.

set -euo pipefail

if [[ "$#" -ne 0 ]]; then
  echo "Usage: ./scripts/reproduce.sh (no arguments)" >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
BOOTSTRAP="${REPO_ROOT}/scripts/bootstrap.sh"
VALIDATE="${REPO_ROOT}/scripts/validate.sh"

"${BOOTSTRAP}" || {
  exit_code=$?
  exit "${exit_code}"
}

exec "${VALIDATE}" --suite all
