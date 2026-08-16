#!/usr/bin/env sh
set -eu
umask 077

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
LOCK_FILE="$ROOT_DIR/tools/semantic-treehouse/upstream.lock.json"
PYTHON="$ROOT_DIR/.venv/bin/python"
EVIDENCE_DIR="$ROOT_DIR/build/evidence/treehouse"
EVIDENCE_FILE="$EVIDENCE_DIR/checkout-wrapper.json"
STAGE=initialize
LOCK_LOADED=false
FETCH_OUT=""
SCOPES_FILE=""
HASHES_FILE=""

if [ ! -x "$PYTHON" ]; then
  echo "Repository .venv Python is required: .venv/bin/python" >&2
  exit 1
fi

mkdir -p "$EVIDENCE_DIR"

cleanup_tmp() {
  [ -z "$FETCH_OUT" ] || rm -f -- "$FETCH_OUT"
  [ -z "$SCOPES_FILE" ] || rm -f -- "$SCOPES_FILE"
  [ -z "$HASHES_FILE" ] || rm -f -- "$HASHES_FILE"
}
trap cleanup_tmp 0
trap 'cleanup_tmp; exit 130' INT TERM HUP

lock_value() {
  "$PYTHON" -I -c '
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
value = data
for part in sys.argv[2].split("."):
    value = value[part]
if isinstance(value, bool):
    print("true" if value else "false")
elif isinstance(value, (str, int)):
    print(value)
else:
    raise SystemExit("requested lock value is not scalar")
' "$LOCK_FILE" "$1"
}

write_evidence() {
  status=$1
  code=$2
  error_text=$3
  head_value=${4:-}
  hashes_file=${5:-}
  "$PYTHON" -I - "$EVIDENCE_FILE" "$ROOT_DIR" "$LOCK_FILE" "$status" "$code" "$STAGE" "$error_text" "$head_value" "$hashes_file" <<'PY'
import json, os, pathlib, re, sys
out, root, lock_path, status, code, stage, error, head, hashes_path = sys.argv[1:]
lock = None
try:
    lock = json.load(open(lock_path, encoding="utf-8"))
except Exception:
    pass
def scrub(value):
    text = str(value or "").replace(root, "<repo>")
    home = os.path.expanduser("~")
    if home and home != "~":
        text = text.replace(home, "<user-home>")
    return re.sub(r"(?i)(authorization|bearer|password|passwd|token|secret|api[_-]?key|credential)(\s*[=:]\s*)(\S+)", r"\1\2<redacted>", text)
hashes = {}
if hashes_path and pathlib.Path(hashes_path).is_file():
    hashes = json.load(open(hashes_path, encoding="utf-8"))
payload = {
    "schema": "dssc.semantic-treehouse.checkout-wrapper.v1",
    "status": status,
    "exit_code": int(code),
    "stage": stage,
    "network_scope": "exact locked reference only",
    "workload_executed": False,
    "upstream": None if lock is None else {
        "url": lock["upstream"]["url"],
        "reference": lock["upstream"]["reference"],
        "expected_commit": lock["upstream"]["commit"],
        "checkout_path": lock["checkout"]["path"],
    },
    "observed": {
        "head": head or None,
        "detached": status == "PASS",
        "clean_worktree": status == "PASS",
        "sparse_mode": "cone" if status == "PASS" else None,
        "core_autocrlf": "false" if status == "PASS" else None,
        "ignored_material_absent": True if status == "PASS" else None,
        "forbidden_paths_absent": [
            ".env", "backend/.env.local", "backend/.env.local.php", "backend/.env.*.local",
            "backend/config/secrets/prod/prod.decrypt.private.php", "backend/vendor", "backend/var",
            "backend/user_data", "frontend/node_modules", "frontend/.pnpm-store",
            "frontend/.angular/cache"
        ] if status == "PASS" else [],
        "file_sha256": hashes,
        "upstream_env_present": False if status == "PASS" else None,
    },
    "error": scrub(error),
}
pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
PY
}

fail() {
  code=$1
  shift
  message=$*
  write_evidence FAILED "$code" "$message" "" "" || true
  printf '%s\n' "$message" >&2
  exit "$code"
}

run_git() {
  set +e
  GIT_OUTPUT=$(git "$@" 2>&1)
  GIT_CODE=$?
  set -e
  if [ "$GIT_CODE" -ne 0 ]; then
    fail "$GIT_CODE" "git command failed at $STAGE: $GIT_OUTPUT"
  fi
  printf '%s' "$GIT_OUTPUT"
}

run_git_bounded() {
  command -v timeout >/dev/null 2>&1 || fail 1 "The timeout utility is required before a network fetch."
  if [ -z "$FETCH_OUT" ]; then
    FETCH_OUT=$(mktemp "$EVIDENCE_DIR/.git-bounded.XXXXXX")
  fi
  set +e
  GIT_TERMINAL_PROMPT=0 timeout --foreground 180 git "$@" >"$FETCH_OUT" 2>&1
  GIT_CODE=$?
  set -e
  GIT_OUTPUT=$(cat "$FETCH_OUT")
  if [ "$GIT_CODE" -ne 0 ]; then
    [ "$GIT_CODE" -ne 124 ] || fail 124 "Bounded Git operation exceeded the 180 second wall-clock limit."
    fail "$GIT_CODE" "Bounded Git operation failed: $GIT_OUTPUT"
  fi
}

assert_no_ignored_residue() {
  for rel in \
    .env backend/.env.local backend/.env.local.php \
    backend/config/secrets/prod/prod.decrypt.private.php \
    backend/vendor backend/var backend/user_data \
    frontend/node_modules frontend/.pnpm-store frontend/.angular/cache
  do
    [ ! -e "$UPSTREAM_DIR/$rel" ] || fail 1 "Ignored build residue is forbidden: $rel"
  done
  for path in "$UPSTREAM_DIR"/backend/.env.*.local; do
    [ ! -e "$path" ] || fail 1 "Ignored build residue is forbidden: backend/$(basename "$path")"
  done
}

STAGE=read-lock
[ -f "$LOCK_FILE" ] || fail 1 "Missing upstream lock file."
"$PYTHON" -I - "$LOCK_FILE" <<'PY' || fail 1 "Invalid Semantic Treehouse upstream lock."
import json, re, sys
lock = json.load(open(sys.argv[1], encoding="utf-8"))
assert lock["schema"] == "dssc.semantic-treehouse.upstream-lock.v1"
assert re.fullmatch(r"[0-9a-f]{40}", lock["upstream"]["commit"])
assert re.fullmatch(r"refs/tags/\S+", lock["upstream"]["reference"])
assert lock["checkout"]["path"] == "tools/semantic-treehouse/upstream"
assert lock["checkout"]["mode"] == "exact-detached-commit"
assert lock["checkout"]["follow_default_branch"] is False
assert lock["source_materialization"]["mode"] == "bounded-sparse-fixed-commit"
assert lock["source_materialization"]["required_scopes"]
assert lock["source_materialization"]["required_files"]
for scope in lock["source_materialization"]["required_scopes"]:
    parts = scope.replace("\\", "/").split("/")
    assert scope and not scope.startswith(("/", "-")) and ".." not in parts
PY
LOCK_LOADED=true

REPO_URL=$(lock_value upstream.url)
REFERENCE=$(lock_value upstream.reference)
COMMIT=$(lock_value upstream.commit)
CHECKOUT_PATH=$(lock_value checkout.path)
UPSTREAM_DIR="$ROOT_DIR/$CHECKOUT_PATH"
TOOLS_DIR=$(dirname "$UPSTREAM_DIR")
mkdir -p "$TOOLS_DIR"

STAGE=initialize-checkout
if [ -e "$UPSTREAM_DIR" ]; then
  [ -d "$UPSTREAM_DIR/.git" ] || fail 1 "Refusing to overwrite a non-Git upstream path."
  DIRTY=$(run_git -C "$UPSTREAM_DIR" status --porcelain=v1 --untracked-files=all)
  [ -z "$DIRTY" ] || fail 1 "Pinned upstream worktree is dirty before materialization."
  ORIGIN=$(run_git -C "$UPSTREAM_DIR" remote get-url origin)
  [ "$ORIGIN" = "$REPO_URL" ] || fail 1 "Existing origin URL differs from the lock."
  assert_no_ignored_residue
else
  mkdir -p "$UPSTREAM_DIR"
  run_git -C "$UPSTREAM_DIR" init >/dev/null
  run_git -C "$UPSTREAM_DIR" remote add origin "$REPO_URL" >/dev/null
  run_git -C "$UPSTREAM_DIR" config remote.origin.promisor true >/dev/null
  run_git -C "$UPSTREAM_DIR" config remote.origin.partialclonefilter blob:none >/dev/null
fi
run_git -C "$UPSTREAM_DIR" config --local core.autocrlf false >/dev/null
AUTOCRLF=$(run_git -C "$UPSTREAM_DIR" config --local --get core.autocrlf)
[ "$AUTOCRLF" = false ] || fail 1 "Pinned upstream checkout requires core.autocrlf=false."

STAGE=materialize-locked-commit
set +e
git -C "$UPSTREAM_DIR" cat-file -e "$COMMIT^{commit}" >/dev/null 2>&1
HAS_COMMIT=$?
set -e
if [ "$HAS_COMMIT" -ne 0 ]; then
  FETCH_OUT=$(mktemp "$EVIDENCE_DIR/.git-fetch.XXXXXX")
  run_git_bounded -C "$UPSTREAM_DIR" \
    -c http.version=HTTP/1.1 \
    -c http.lowSpeedLimit=1024 \
    -c http.lowSpeedTime=60 \
    fetch --no-tags --depth=1 --filter=blob:none origin "$REFERENCE"
  FETCHED=$(run_git -C "$UPSTREAM_DIR" rev-parse 'FETCH_HEAD^{commit}')
  [ "$FETCHED" = "$COMMIT" ] || fail 1 "Fetched tag does not resolve to the locked commit."
fi

SCOPES_FILE=$(mktemp "$EVIDENCE_DIR/.checkout-scopes.XXXXXX")
"$PYTHON" -I - "$LOCK_FILE" "$SCOPES_FILE" <<'PY'
import json, pathlib, sys
lock = json.load(open(sys.argv[1], encoding="utf-8"))
pathlib.Path(sys.argv[2]).write_text("\n".join(lock["source_materialization"]["required_scopes"]) + "\n", encoding="utf-8")
PY
set --
while IFS= read -r scope; do
  [ -n "$scope" ] && set -- "$@" "$scope"
done < "$SCOPES_FILE"
rm -f "$SCOPES_FILE"
run_git_bounded -C "$UPSTREAM_DIR" -c http.lowSpeedLimit=1024 -c http.lowSpeedTime=60 sparse-checkout set --cone "$@"
run_git_bounded -C "$UPSTREAM_DIR" -c http.lowSpeedLimit=1024 -c http.lowSpeedTime=60 checkout --detach "$COMMIT"
run_git_bounded -C "$UPSTREAM_DIR" -c http.lowSpeedLimit=1024 -c http.lowSpeedTime=60 sparse-checkout set --cone "$@"

STAGE=verify-materialization
HEAD_VALUE=$(run_git -C "$UPSTREAM_DIR" rev-parse HEAD)
[ "$HEAD_VALUE" = "$COMMIT" ] || fail 1 "Upstream HEAD differs from the lock."
set +e
git -C "$UPSTREAM_DIR" symbolic-ref -q --short HEAD >/dev/null 2>&1
ATTACHED=$?
set -e
[ "$ATTACHED" -ne 0 ] || fail 1 "Upstream checkout must be detached."
[ ! -e "$UPSTREAM_DIR/.env" ] || fail 1 "Refusing an upstream .env file; runtime configuration must stay isolated."
assert_no_ignored_residue

HASHES_FILE=$(mktemp "$EVIDENCE_DIR/.checkout-hashes.XXXXXX.json")
"$PYTHON" -I - "$LOCK_FILE" "$UPSTREAM_DIR" "$HASHES_FILE" <<'PY' || fail 1 "Materialized source hash verification failed."
import hashlib, json, pathlib, sys
lock = json.load(open(sys.argv[1], encoding="utf-8"))
root = pathlib.Path(sys.argv[2]).resolve()
observed = {}
for rel in lock["source_materialization"]["required_files"]:
    if rel.startswith("/") or ".." in pathlib.PurePosixPath(rel).parts:
        raise SystemExit(f"unsafe locked path: {rel}")
    path = (root / rel).resolve()
    if root not in path.parents or not path.is_file():
        raise SystemExit(f"required file missing: {rel}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != lock["source_materialization"]["sha256"][rel]:
        raise SystemExit(f"SHA-256 mismatch: {rel}")
    observed[rel] = digest
pathlib.Path(sys.argv[3]).write_text(json.dumps(observed, sort_keys=True, indent=2) + "\n", encoding="utf-8")
PY

DIRTY=$(run_git -C "$UPSTREAM_DIR" status --porcelain=v1 --untracked-files=all)
[ -z "$DIRTY" ] || fail 1 "Pinned upstream worktree is dirty after materialization."
IGNORED=$(run_git -C "$UPSTREAM_DIR" status --porcelain=v1 --ignored=matching)
if printf '%s\n' "$IGNORED" | grep -q '^!![[:space:]]'; then
  fail 1 "Pinned upstream contains ignored residue after materialization."
fi
grep -q 'Apache License' "$UPSTREAM_DIR/$(lock_value license.reference_path)" || fail 1 "Materialized license does not match Apache-2.0."

write_evidence PASS 0 "" "$HEAD_VALUE" "$HASHES_FILE"
rm -f "$HASHES_FILE"
printf 'Semantic Treehouse pinned checkout verified: %s\n' "$HEAD_VALUE"
exit 0
