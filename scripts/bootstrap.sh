#!/usr/bin/env bash
# Create or refresh the repository .venv from the hash-locked requirements.
# Strict shell; resolves repository root from this script's location.
# Does not modify the user's shell profile. Does not require GNU Make.

set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUTF8=1
export PYTHONNOUSERSITE=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_CONFIG_FILE=/dev/null
unset PIP_TARGET PIP_PREFIX PIP_ROOT PIP_USER

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"
cd "${REPO_ROOT}"

EXPECTED="$(tr -d '[:space:]' < "${REPO_ROOT}/.python-version")"
if [[ -z "${EXPECTED}" ]]; then
  echo "ERROR: .python-version missing or empty" >&2
  exit 1
fi

LOCK_FILE="${REPO_ROOT}/requirements.lock"
BOOT_LOCK="${REPO_ROOT}/requirements-bootstrap.lock"
VENV_DIR="${REPO_ROOT}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"
VENV_CONTRACT="${REPO_ROOT}/scripts/dssc_validation/venv_contract.py"

if [[ ! -f "${LOCK_FILE}" ]]; then
  echo "ERROR: requirements.lock missing" >&2
  exit 1
fi
if [[ ! -f "${BOOT_LOCK}" ]]; then
  echo "ERROR: requirements-bootstrap.lock missing" >&2
  exit 1
fi

find_base_python() {
  if [[ -n "${PYTHON_PATH:-}" ]]; then
    echo "${PYTHON_PATH}"
    return 0
  fi
  local candidates=()
  if command -v "python${EXPECTED}" >/dev/null 2>&1; then
    candidates+=("python${EXPECTED}")
  fi
  if command -v python3.12 >/dev/null 2>&1; then
    candidates+=("python3.12")
  fi
  if command -v python3 >/dev/null 2>&1; then
    candidates+=("python3")
  fi
  local cand ver
  for cand in "${candidates[@]}"; do
    ver="$("${cand}" -I -S -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || true)"
    if [[ "${ver}" == "${EXPECTED}" ]]; then
      "${cand}" -I -S -c 'import sys; print(sys.executable)'
      return 0
    fi
  done
  echo "ERROR: Could not find CPython ${EXPECTED}. Set PYTHON_PATH to the interpreter." >&2
  return 1
}

assert_version() {
  local exe="$1"
  local ver impl bits
  ver="$("${exe}" -I -S -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  if [[ "${ver}" != "${EXPECTED}" ]]; then
    echo "ERROR: Interpreter version mismatch: got ${ver}, expected ${EXPECTED} (${exe})" >&2
    exit 1
  fi
  impl="$("${exe}" -I -S -c 'import platform; print(platform.python_implementation())')"
  if [[ "${impl}" != "CPython" ]]; then
    echo "ERROR: Expected CPython, got ${impl}" >&2
    exit 1
  fi
  bits="$("${exe}" -I -S -c 'import struct; print(struct.calcsize("P") * 8)')"
  if [[ "${bits}" != "64" ]]; then
    echo "ERROR: Expected a 64-bit interpreter, got ${bits}-bit (${exe})" >&2
    exit 1
  fi
}

echo "Repository root: ${REPO_ROOT}"
echo "Expected CPython: ${EXPECTED}"

BASE_PYTHON="$(find_base_python)"
echo "Base interpreter: ${BASE_PYTHON}"
assert_version "${BASE_PYTHON}"

ENSUREPIP_VERSION="$("${BASE_PYTHON}" -I -S -c 'import ensurepip; print(ensurepip.version())')"
if [[ "${ENSUREPIP_VERSION}" != "25.0.1" ]]; then
  echo "ERROR: CPython ensurepip mismatch: got ${ENSUREPIP_VERSION}, expected 25.0.1" >&2
  exit 1
fi

CREATED_VENV=0
if [[ -e "${VENV_DIR}" || -L "${VENV_DIR}" ]]; then
  if [[ ! -d "${VENV_DIR}" || -L "${VENV_DIR}" ]]; then
    echo "ERROR: Refusing to use .venv because it is not a real, non-link directory" >&2
    exit 1
  fi
  VENV_REAL="$(cd "${VENV_DIR}" && pwd -P)"
  if [[ "${VENV_REAL}" != "${REPO_ROOT}/.venv" ]]; then
    echo "ERROR: Refusing to use .venv outside the repository root" >&2
    exit 1
  fi
  if [[ ! -x "${VENV_PYTHON}" ]]; then
    echo "ERROR: Existing .venv is incomplete; follow docs/environment.md safe rebuild steps" >&2
    exit 1
  fi
  echo "Reusing existing .venv"
else
  echo "Creating virtual environment at .venv ..."
  "${BASE_PYTHON}" -I -S -m venv "${VENV_DIR}"
  CREATED_VENV=1
fi

if [[ ! -d "${VENV_DIR}" || -L "${VENV_DIR}" || "$(cd "${VENV_DIR}" && pwd -P)" != "${REPO_ROOT}/.venv" ]]; then
  echo "ERROR: Created .venv failed the repository boundary check" >&2
  exit 1
fi
if [[ ! -f "${VENV_DIR}/pyvenv.cfg" || -L "${VENV_DIR}/pyvenv.cfg" ]]; then
  echo "ERROR: Repository .venv is missing a real pyvenv.cfg" >&2
  exit 1
fi
if [[ "$(readlink -f "${VENV_PYTHON}")" != "$(readlink -f "${BASE_PYTHON}")" ]]; then
  echo "ERROR: Repository .venv interpreter does not resolve to the selected base Python" >&2
  exit 1
fi
if [[ "${CREATED_VENV}" == "1" ]]; then
  PREFLIGHT_MODE=created-preflight
  RUNTIME_MARKER_ARGS=(--allow-missing-marker)
else
  PREFLIGHT_MODE=reuse-preflight
  RUNTIME_MARKER_ARGS=()
fi
"${BASE_PYTHON}" -I -S "${VENV_CONTRACT}" --mode "${PREFLIGHT_MODE}" --venv "${VENV_DIR}" --expected-version "${EXPECTED}" --expected-pip-version 25.0.1 --base-python "${BASE_PYTHON}" --bootstrap-source-file "${BASH_SOURCE[0]}" --runtime-lock-file "${LOCK_FILE}" --bootstrap-lock-file "${BOOT_LOCK}" || {
  echo "ERROR: Repository .venv static trust preflight failed before launching its interpreter" >&2
  exit 1
}
"${VENV_PYTHON}" -I "${VENV_CONTRACT}" --venv "${VENV_DIR}" --expected-version "${EXPECTED}" --expected-pip-version 25.0.1 "${RUNTIME_MARKER_ARGS[@]}" || {
  echo "ERROR: Repository .venv isolation contract failed before package installation" >&2
  exit 1
}

assert_version "${VENV_PYTHON}"

echo "Normalizing bootstrap toolchain from requirements-bootstrap.lock ..."
"${VENV_PYTHON}" -I -m pip --isolated --disable-pip-version-check install --upgrade --index-url https://pypi.org/simple --require-hashes -r "${BOOT_LOCK}"
"${VENV_PYTHON}" -I -c 'from importlib.metadata import version; expected={"pip":"25.0.1","pip-tools":"7.4.1","setuptools":"75.8.2","wheel":"0.45.1"}; bad={k:(version(k),v) for k,v in expected.items() if version(k)!=v}; print("bootstrap-tools=" + ",".join(k+"=="+version(k) for k in sorted(expected))); raise SystemExit(1 if bad else 0)'

echo "Installing runtime dependencies from requirements.lock (--require-hashes) ..."
"${VENV_PYTHON}" -I -m pip --isolated --disable-pip-version-check install --index-url https://pypi.org/simple --require-hashes -r "${LOCK_FILE}"

echo "Running pip check ..."
"${VENV_PYTHON}" -I -m pip --isolated --disable-pip-version-check check

echo "pip: $("${VENV_PYTHON}" -I -m pip --isolated --version)"

# Re-pin and re-assert bootstrap pip after the runtime lock install so hosts
# that ship a newer ensurepip/default pip cannot drift past the lock pin.
"${VENV_PYTHON}" -I -m pip --isolated --disable-pip-version-check install --upgrade --index-url https://pypi.org/simple --require-hashes -r "${BOOT_LOCK}"
"${VENV_PYTHON}" -I -c 'from importlib.metadata import version; v=version("pip"); print("installed-pip="+v); raise SystemExit(0 if v=="25.0.1" else 1)'
echo "pip(after-repin): $("${VENV_PYTHON}" -I -m pip --isolated --version)"

echo "Writing hash-bound .venv trust marker ..."
"${BASE_PYTHON}" -I -S "${VENV_CONTRACT}" --mode write-marker --venv "${VENV_DIR}" --expected-version "${EXPECTED}" --expected-pip-version 25.0.1 --base-python "${BASE_PYTHON}" --bootstrap-source-file "${BASH_SOURCE[0]}" --runtime-lock-file "${LOCK_FILE}" --bootstrap-lock-file "${BOOT_LOCK}"

if [[ "${SKIP_DOCTOR:-0}" != "1" ]]; then
  echo "Running doctor --profile host ..."
  "${VENV_PYTHON}" -I "${REPO_ROOT}/scripts/doctor.py" --profile host
fi

echo "Bootstrap complete."
