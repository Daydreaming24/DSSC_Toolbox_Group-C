#!/usr/bin/env bash
# Thin Linux wrapper: select repository .venv Python and run validate.py.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUTF8=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"
VALIDATE_PY="${REPO_ROOT}/scripts/validate.py"

SUITE=""
VERBOSE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --suite|-s)
      SUITE="${2:-}"
      shift 2
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: ./scripts/validate.sh --suite <name> [--verbose]" >&2
      exit 2
      ;;
  esac
done

if [[ -z "${SUITE}" ]]; then
  echo "ERROR: --suite is required" >&2
  exit 2
fi

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "ERROR: Repository .venv not found. Run ./scripts/bootstrap.sh first." >&2
  exit 1
fi

args=("${VALIDATE_PY}" --suite "${SUITE}" --profile host)
if [[ "${VERBOSE}" -eq 1 ]]; then
  args+=(--verbose)
fi

exec "${VENV_PYTHON}" -I "${args[@]}"
