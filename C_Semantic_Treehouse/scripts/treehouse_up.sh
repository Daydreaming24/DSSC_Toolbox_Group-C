#!/usr/bin/env sh
set -eu
umask 077

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
LOCK_FILE="$ROOT_DIR/tools/semantic-treehouse/upstream.lock.json"
PYTHON="$ROOT_DIR/.venv/bin/python"
RUNTIME_DIR="$ROOT_DIR/build/phase-08/treehouse-runtime"
EVIDENCE_DIR="$ROOT_DIR/build/evidence/treehouse"
ENV_FILE="$RUNTIME_DIR/synthetic.env"
PINNED_DOCKERFILE="$RUNTIME_DIR/Dockerfile.runtime"
OVERLAY_FILE="$RUNTIME_DIR/compose.runtime.yml"
STATE_FILE="$RUNTIME_DIR/runtime-state.json"
PENDING_STATE_FILE="$RUNTIME_DIR/.runtime-state.pending.json"
SAFE_PROJECTION_FILE="$RUNTIME_DIR/runtime-boundary.json"
REALIZED_INGRESS_FILE="$RUNTIME_DIR/.realized-ingress.json"
REALIZED_NETWORK_OPTIONS_EVIDENCE="$EVIDENCE_DIR/runtime-network-options.json"
RAW_LOG="$RUNTIME_DIR/up.raw.log"
CLEAN_LOG="$EVIDENCE_DIR/treehouse-up.log"
DETAILS_FILE="$RUNTIME_DIR/up-details.json"
LAST_OUTPUT_FILE="$RUNTIME_DIR/.last-command.out"
EFFECTIVE_CONFIG_FILE="$RUNTIME_DIR/.effective-config.json"
CONFIG_ERROR_FILE="$RUNTIME_DIR/.effective-config.err"
BUILD_PLAN_FILE="$RUNTIME_DIR/.build-plan.json"
BUILD_PLAN_ERROR_FILE="$RUNTIME_DIR/.build-plan.err"
FINAL_BAKE_FILE="$RUNTIME_DIR/.final-bake-plan.json"
FINAL_BAKE_ERROR_FILE="$RUNTIME_DIR/.final-bake-plan.err"
ROOT_SMOKE_HEADER_FILE="$RUNTIME_DIR/.root-smoke-headers.tmp"
API_SMOKE_HEADER_FILE="$RUNTIME_DIR/.api-smoke-headers.tmp"
AUTH_COOKIE_JAR="$RUNTIME_DIR/.local-review-auth.cookies.tmp"
AUTH_LOGIN_HEADER_FILE="$RUNTIME_DIR/.local-review-login-headers.tmp"
AUTH_ACCOUNT_BODY_FILE="$RUNTIME_DIR/.local-review-account-info.tmp"
PREPARE_ONLY=false
HTTP_PORT=""
STAGE=initialize
FAILURE_MESSAGE=""
WORKLOAD_ATTEMPTED=false
CONTAINER_START_ATTEMPTED=false
EVIDENCE_WRITTEN=false
CLEANUP_ATTEMPTED=false
CLEANUP_EXIT_CODE=""
FRESH_DEPLOYMENT_STARTED=false
APP_VOLUME_CREATED=false
DB_VOLUME_CREATED=false
CLEANUP_VOLUMES_REMOVED=false
CLEANUP_VERIFICATION_ERROR=""
CLEANUP_REMAINING_PROJECT_CONTAINERS=""
CLEANUP_REMAINING_NAMED_CONTAINERS=""
CLEANUP_REMAINING_PROJECT_NETWORKS=""
CLEANUP_REMAINING_NAMED_NETWORKS=""
CLEANUP_REMAINING_PROJECT_VOLUMES=""
CLEANUP_REMAINING_NAMED_VOLUMES=""
CLEANUP_COMPLETE=""

usage() {
  echo "Usage: $0 [--prepare-only] [--http-port PORT]" >&2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --prepare-only) PREPARE_ONLY=true; shift ;;
    --http-port)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      HTTP_PORT=$2
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) usage; echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [ "$PREPARE_ONLY" = true ]; then
  RAW_LOG="$RUNTIME_DIR/prepare-only.raw.log"
  CLEAN_LOG="$EVIDENCE_DIR/treehouse-prepare-only.log"
  if [ -e "$STATE_FILE" ] || [ -e "$PENDING_STATE_FILE" ]; then
    echo "PrepareOnly refuses an existing runtime state marker." >&2
    exit 1
  fi
fi

[ -x "$PYTHON" ] || { echo "Repository .venv Python is required: .venv/bin/python" >&2; exit 1; }
command -v timeout >/dev/null 2>&1 || { echo "GNU timeout is required for bounded Docker operations." >&2; exit 1; }
mkdir -p "$RUNTIME_DIR" "$EVIDENCE_DIR"
rm -f -- "$DETAILS_FILE" "$LAST_OUTPUT_FILE" "$EFFECTIVE_CONFIG_FILE" "$CONFIG_ERROR_FILE" "$BUILD_PLAN_FILE" "$BUILD_PLAN_ERROR_FILE" "$FINAL_BAKE_FILE" "$FINAL_BAKE_ERROR_FILE" "$ROOT_SMOKE_HEADER_FILE" "$API_SMOKE_HEADER_FILE" "$AUTH_COOKIE_JAR" "$AUTH_LOGIN_HEADER_FILE" "$AUTH_ACCOUNT_BODY_FILE"
: > "$RAW_LOG"

lock_value() {
  "$PYTHON" -I -c '
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
for part in sys.argv[2].split("."):
    value = value[part]
if isinstance(value, bool): print("true" if value else "false")
elif isinstance(value, (str, int)): print(value)
else: raise SystemExit("requested lock value is not scalar")
' "$LOCK_FILE" "$1"
}

scrub_log() {
  "$PYTHON" -I - "$RAW_LOG" "$CLEAN_LOG" "$ROOT_DIR" "$ENV_FILE" <<'PY'
import os, pathlib, re, sys
raw_path, clean_path, root, env_path = map(pathlib.Path, sys.argv[1:])
text = raw_path.read_text(encoding="utf-8", errors="replace") if raw_path.is_file() else ""
secrets = []
if env_path.is_file():
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if any(marker in key.lower() for marker in ("password", "secret", "api_key")) and value:
                secrets.append(value)
for value in secrets:
    text = text.replace(value, "<redacted>")
text = text.replace(str(root), "<repo>")
home = str(pathlib.Path.home())
if home:
    text = text.replace(home, "<user-home>")
text = re.sub(r"(?i)(authorization|bearer|password|passwd|token|secret|api[_-]?key|credential)(\s*[=:]\s*)(\S+)", r"\1\2<redacted>", text)
for value in secrets:
    if value and value in text:
        raise SystemExit("secret scrub failed")
if str(root) in text or (home and home in text):
    raise SystemExit("absolute path scrub failed")
clean_path.parent.mkdir(parents=True, exist_ok=True)
clean_path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
if raw_path.is_file():
    raw_path.unlink()
PY
}

write_evidence() {
  status=$1
  code=$2
  error_text=$3
  if [ "$PREPARE_ONLY" = true ] && [ "$WORKLOAD_ATTEMPTED" = false ]; then
    evidence_file="$EVIDENCE_DIR/runtime-control-preflight.json"
    schema="dssc.semantic-treehouse.runtime-control-preflight.v1"
  else
    evidence_file="$EVIDENCE_DIR/runtime-up.json"
    schema="dssc.semantic-treehouse.runtime-up.v1"
  fi
  "$PYTHON" -I - "$evidence_file" "$schema" "$status" "$code" "$STAGE" "$error_text" "$LOCK_FILE" "$STATE_FILE" "$DETAILS_FILE" "$REALIZED_NETWORK_OPTIONS_EVIDENCE" "$ROOT_DIR" "$WORKLOAD_ATTEMPTED" "$CLEANUP_ATTEMPTED" "$CLEANUP_EXIT_CODE" "$CLEANUP_VOLUMES_REMOVED" "$CLEANUP_VERIFICATION_ERROR" "$CLEANUP_REMAINING_PROJECT_CONTAINERS" "$CLEANUP_REMAINING_NAMED_CONTAINERS" "$CLEANUP_REMAINING_PROJECT_NETWORKS" "$CLEANUP_REMAINING_NAMED_NETWORKS" "$CLEANUP_REMAINING_PROJECT_VOLUMES" "$CLEANUP_REMAINING_NAMED_VOLUMES" "$CLEANUP_COMPLETE" <<'PY'
import hashlib, json, os, pathlib, re, sys
(out, schema, status, code, stage, error, lock_path, state_path, details_path, network_options_path,
 root, workload, cleanup, cleanup_code, cleanup_volumes_removed, cleanup_verification_error,
 remaining_project_containers, remaining_named_containers, remaining_project_networks,
 remaining_named_networks, remaining_project_volumes, remaining_named_volumes, cleanup_complete) = sys.argv[1:]
lock = json.load(open(lock_path, encoding="utf-8"))
state_file = pathlib.Path(state_path)
state = {"present": state_file.is_file(), "sha256": hashlib.sha256(state_file.read_bytes()).hexdigest() if state_file.is_file() else None, "content_recorded": False}
details = json.load(open(details_path, encoding="utf-8")) if pathlib.Path(details_path).is_file() else {}
network_options_file=pathlib.Path(network_options_path)
network_options = {"path":"build/evidence/treehouse/runtime-network-options.json","sha256":hashlib.sha256(network_options_file.read_bytes()).hexdigest()} if workload == "true" and network_options_file.is_file() else None
def scrub(value):
    text = str(value or "").replace(root, "<repo>")
    home = os.path.expanduser("~")
    if home and home != "~": text = text.replace(home, "<user-home>")
    return re.sub(r"(?i)(authorization|bearer|password|passwd|token|secret|api[_-]?key|credential)(\s*[=:]\s*)(\S+)", r"\1\2<redacted>", text)
payload = {
  "schema": schema,
  "status": status,
  "exit_code": int(code),
  "stage": stage,
  "workload_executed": workload == "true",
  "project_name": lock["compose"]["project_name"],
  "upstream_commit": lock["upstream"]["commit"],
  "lock_sha256": hashlib.sha256(pathlib.Path(lock_path).read_bytes()).hexdigest(),
  "runtime_state": state,
  "realized_network_options_evidence": network_options,
  "details": details,
  "cleanup": {
    "attempted": cleanup == "true",
    "exit_code": int(cleanup_code) if cleanup_code else None,
    "volumes_removed": cleanup_volumes_removed == "true",
    "verification_error": scrub(cleanup_verification_error) if cleanup_verification_error else None,
    "remaining_project_containers": int(remaining_project_containers) if remaining_project_containers else None,
    "remaining_named_containers": int(remaining_named_containers) if remaining_named_containers else None,
    "remaining_project_networks": int(remaining_project_networks) if remaining_project_networks else None,
    "remaining_named_networks": int(remaining_named_networks) if remaining_named_networks else None,
    "remaining_project_volumes": int(remaining_project_volumes) if remaining_project_volumes else None,
    "remaining_named_volumes": int(remaining_named_volumes) if remaining_named_volumes else None,
    "complete": cleanup_complete == "true" if cleanup_complete else None,
  },
  "error": scrub(error),
}
pathlib.Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
PY
  EVIDENCE_WRITTEN=true
}

docker_call() {
  allow_failure=$1
  shift
  printf '[%s] docker' "$STAGE" >> "$RAW_LOG"
  for arg in "$@"; do printf ' %s' "$arg" >> "$RAW_LOG"; done
  printf '\n' >> "$RAW_LOG"
  set +e
  timeout_seconds=${DOCKER_TIMEOUT_SECONDS:-120}
  timeout --foreground "$timeout_seconds" docker "$@" > "$LAST_OUTPUT_FILE" 2>&1
  LAST_CODE=$?
  set -e
  cat "$LAST_OUTPUT_FILE" >> "$RAW_LOG"
  printf '\n[%s] exit=%s\n' "$STAGE" "$LAST_CODE" >> "$RAW_LOG"
  LAST_OUTPUT=$(cat "$LAST_OUTPUT_FILE")
  if [ "$LAST_CODE" -ne 0 ] && [ "$allow_failure" != true ]; then
    FAILURE_MESSAGE="docker command failed at $STAGE with exit code $LAST_CODE"
    exit "$LAST_CODE"
  fi
}

compose_call() {
  allow_failure=$1
  shift
  DB2_TEST_DB_PASSWORD=placeholder docker_call "$allow_failure" compose \
    --project-name "$PROJECT_NAME" \
    --project-directory "$UPSTREAM_DIR" \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    -f "$OVERLAY_FILE" \
    "$@"
}

volume_check_strict() {
  logical=$1
  name=$2
  STAGE=volume-name-preflight
  docker_call false volume ls --quiet --filter "name=$name"
  if printf '%s\n' "$LAST_OUTPUT" | grep -Fxq "$name"; then
    docker_call false volume inspect --format '{{json .Labels}}' "$name"
    "$PYTHON" -I - "$LAST_OUTPUT" "$PROJECT_NAME" "$logical" "$COMMIT" <<'PY' || {
import json, sys
labels = json.loads(sys.argv[1]) or {}
expected = {
  "com.docker.compose.project": sys.argv[2],
  "com.docker.compose.volume": sys.argv[3],
  "dssc.semantic-treehouse.managed": "true",
  "dssc.semantic-treehouse.project": sys.argv[2],
  "dssc.semantic-treehouse.upstream-commit": sys.argv[4],
  "dssc.semantic-treehouse.logical-volume": sys.argv[3],
  "dssc.semantic-treehouse.runtime-contract": "v1",
}
if any(str(labels.get(k)) != v for k, v in expected.items()):
    raise SystemExit(1)
PY
      FAILURE_MESSAGE="Existing volume $name has missing or mismatched project labels."
      exit 1
    }
    FAILURE_MESSAGE="Fresh deployment refuses pre-existing project volume: $name"
    exit 1
  fi
}

verify_created_volume() {
  logical=$1
  name=$2
  docker_call false volume inspect --format '{{json .Labels}}' "$name"
  "$PYTHON" -I - "$LAST_OUTPUT" "$PROJECT_NAME" "$logical" "$COMMIT" <<'PY' || return 1
import json, sys
labels = json.loads(sys.argv[1]) or {}
expected = {
  "com.docker.compose.project": sys.argv[2],
  "com.docker.compose.volume": sys.argv[3],
  "dssc.semantic-treehouse.managed": "true",
  "dssc.semantic-treehouse.project": sys.argv[2],
  "dssc.semantic-treehouse.upstream-commit": sys.argv[4],
  "dssc.semantic-treehouse.logical-volume": sys.argv[3],
  "dssc.semantic-treehouse.runtime-contract": "v1",
}
assert all(str(labels.get(k)) == v for k, v in expected.items())
PY
}

remove_created_volume_safely() {
  logical=$1
  name=$2
  docker_call true volume inspect --format '{{json .Labels}}' "$name"
  [ "$LAST_CODE" -eq 0 ] || return 1
  "$PYTHON" -I - "$LAST_OUTPUT" "$PROJECT_NAME" "$logical" "$COMMIT" <<'PY' || return 1
import json, sys
labels = json.loads(sys.argv[1]) or {}
expected = {
  "com.docker.compose.project": sys.argv[2],
  "com.docker.compose.volume": sys.argv[3],
  "dssc.semantic-treehouse.managed": "true",
  "dssc.semantic-treehouse.project": sys.argv[2],
  "dssc.semantic-treehouse.upstream-commit": sys.argv[4],
  "dssc.semantic-treehouse.logical-volume": sys.argv[3],
  "dssc.semantic-treehouse.runtime-contract": "v1",
}
if any(str(labels.get(k)) != v for k, v in expected.items()):
    raise SystemExit(1)
PY
  docker_call true volume rm "$name"
  [ "$LAST_CODE" -eq 0 ]
}

finalize() {
  code=$?
  original_stage=$STAGE
  set +e
  if [ "$code" -ne 0 ] && [ "$CONTAINER_START_ATTEMPTED" = true ] && [ "$CLEANUP_ATTEMPTED" = false ]; then
    CLEANUP_ATTEMPTED=true
    STAGE=failure-cleanup
    DOCKER_TIMEOUT_SECONDS=180 compose_call true down
    CLEANUP_EXIT_CODE=$LAST_CODE
  fi
  if [ "$code" -ne 0 ] && [ "$FRESH_DEPLOYMENT_STARTED" = true ]; then
    rm -f -- "$STATE_FILE" "$PENDING_STATE_FILE"
    cleanup_volume_code=0
    if [ "$APP_VOLUME_CREATED" = true ]; then
      CLEANUP_ATTEMPTED=true
      STAGE=failure-volume-cleanup
      remove_created_volume_safely sth-app-data "$APP_VOLUME" || cleanup_volume_code=1
    fi
    if [ "$DB_VOLUME_CREATED" = true ]; then
      CLEANUP_ATTEMPTED=true
      STAGE=failure-volume-cleanup
      remove_created_volume_safely sth-db2-data "$DB_VOLUME" || cleanup_volume_code=1
    fi
    if [ "$APP_VOLUME_CREATED" = true ] || [ "$DB_VOLUME_CREATED" = true ]; then
      [ "$cleanup_volume_code" -ne 0 ] || CLEANUP_VOLUMES_REMOVED=true
      if [ -z "$CLEANUP_EXIT_CODE" ] || [ "$CLEANUP_EXIT_CODE" -eq 0 ]; then CLEANUP_EXIT_CODE=$cleanup_volume_code; fi
    fi
  fi
  if [ "$code" -ne 0 ] && { [ "$FRESH_DEPLOYMENT_STARTED" = true ] || [ "$WORKLOAD_ATTEMPTED" = true ] || [ "$CLEANUP_ATTEMPTED" = true ]; }; then
    CLEANUP_ATTEMPTED=true
    STAGE=failure-cleanup-verification
    set +e
    project_containers=$(timeout --foreground 30 docker ps -a --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{.ID}}' 2>/dev/null)
    verify_code=$?
    project_networks=$(timeout --foreground 30 docker network ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{.Name}}' 2>/dev/null)
    [ "$?" -eq 0 ] || verify_code=1
    project_volumes=$(timeout --foreground 30 docker volume ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{.Name}}' 2>/dev/null)
    [ "$?" -eq 0 ] || verify_code=1
    named_containers=0
    for name in "$PROJECT_NAME-sth" "$PROJECT_NAME-sth-db2"; do
      rows=$(timeout --foreground 30 docker ps -a --filter "name=^/$name$" --format '{{.Names}}' 2>/dev/null)
      query_code=$?
      [ "$query_code" -eq 0 ] || verify_code=1
      named_containers=$((named_containers + $(printf '%s\n' "$rows" | awk -v target="$name" '$0==target{n++} END{print n+0}')))
    done
    named_networks=0
    for name in "$NETWORK_NAME" "$INGRESS_NETWORK_NAME"; do
      rows=$(timeout --foreground 30 docker network ls --filter "name=^$name$" --format '{{.Name}}' 2>/dev/null)
      query_code=$?
      [ "$query_code" -eq 0 ] || verify_code=1
      named_networks=$((named_networks + $(printf '%s\n' "$rows" | awk -v target="$name" '$0==target{n++} END{print n+0}')))
    done
    named_volumes=0
    for name in "$APP_VOLUME" "$DB_VOLUME"; do
      rows=$(timeout --foreground 30 docker volume ls --filter "name=^$name$" --format '{{.Name}}' 2>/dev/null)
      query_code=$?
      [ "$query_code" -eq 0 ] || verify_code=1
      named_volumes=$((named_volumes + $(printf '%s\n' "$rows" | awk -v target="$name" '$0==target{n++} END{print n+0}')))
    done
    set +e
    CLEANUP_REMAINING_PROJECT_CONTAINERS=$(printf '%s\n' "$project_containers" | awk 'NF{n++} END{print n+0}')
    CLEANUP_REMAINING_PROJECT_NETWORKS=$(printf '%s\n' "$project_networks" | awk 'NF{n++} END{print n+0}')
    CLEANUP_REMAINING_PROJECT_VOLUMES=$(printf '%s\n' "$project_volumes" | awk 'NF{n++} END{print n+0}')
    CLEANUP_REMAINING_NAMED_CONTAINERS=$named_containers
    CLEANUP_REMAINING_NAMED_NETWORKS=$named_networks
    CLEANUP_REMAINING_NAMED_VOLUMES=$named_volumes
    if [ "$verify_code" -eq 0 ] && [ "$CLEANUP_REMAINING_PROJECT_CONTAINERS" -eq 0 ] && [ "$named_containers" -eq 0 ] && [ "$CLEANUP_REMAINING_PROJECT_NETWORKS" -eq 0 ] && [ "$named_networks" -eq 0 ] && [ "$CLEANUP_REMAINING_PROJECT_VOLUMES" -eq 0 ] && [ "$named_volumes" -eq 0 ] && { [ -z "$CLEANUP_EXIT_CODE" ] || [ "$CLEANUP_EXIT_CODE" -eq 0 ]; }; then
      CLEANUP_COMPLETE=true
    else
      CLEANUP_COMPLETE=false
      [ "$verify_code" -eq 0 ] || CLEANUP_VERIFICATION_ERROR="Docker cleanup verification could not complete."
    fi
  fi
  STAGE=$original_stage
  scrub_code=0
  if [ -f "$RAW_LOG" ]; then
    scrub_log >/dev/null 2>&1
    scrub_code=$?
  fi
  if [ "$code" -eq 0 ] && [ "$scrub_code" -ne 0 ]; then
    code=1
    FAILURE_MESSAGE="Evidence log scrub failed."
  fi
  if [ "$EVIDENCE_WRITTEN" = false ]; then
    [ -n "$FAILURE_MESSAGE" ] || FAILURE_MESSAGE="Treehouse wrapper stopped unexpectedly at $STAGE."
    write_evidence FAILED "$code" "$FAILURE_MESSAGE" >/dev/null 2>&1
  fi
  rm -f -- "$LAST_OUTPUT_FILE" "$EFFECTIVE_CONFIG_FILE" "$CONFIG_ERROR_FILE" "$BUILD_PLAN_FILE" "$BUILD_PLAN_ERROR_FILE" "$FINAL_BAKE_FILE" "$FINAL_BAKE_ERROR_FILE" "$ROOT_SMOKE_HEADER_FILE" "$API_SMOKE_HEADER_FILE" "$AUTH_COOKIE_JAR" "$AUTH_LOGIN_HEADER_FILE" "$AUTH_ACCOUNT_BODY_FILE" "$PENDING_STATE_FILE" "$REALIZED_INGRESS_FILE"
  trap - 0
  exit "$code"
}
trap finalize 0

STAGE=read-lock
[ -f "$LOCK_FILE" ] || { FAILURE_MESSAGE="Missing upstream lock file."; exit 1; }
"$PYTHON" -I - "$LOCK_FILE" <<'PY' || { FAILURE_MESSAGE="Invalid upstream lock contract."; exit 1; }
import json, re, sys
lock = json.load(open(sys.argv[1], encoding="utf-8"))
assert lock["schema"] == "dssc.semantic-treehouse.upstream-lock.v1"
assert re.fullmatch(r"[0-9a-f]{40}", lock["upstream"]["commit"])
assert lock["compose"]["execution_mode"] == "production-explicit-service"
assert lock["compose"]["profiles"] == []
assert re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,62}", lock["compose"]["project_name"])
assert lock["runtime"]["platform"] == "linux/amd64"
assert lock["runtime"]["target_service"] == "sth"
assert lock["runtime"]["dependency_services"] == ["sth-db2"]
assert lock["runtime"]["bind_address"] == "127.0.0.1"
assert lock["runtime"]["network_topology"] == "dual-network-app-ingress"
assert lock["runtime"]["internal_network"] is True
assert lock["runtime"]["app_outbound_access"] is True
assert lock["runtime"]["ingress_network_internal"] is False
assert lock["runtime"]["ingress_services"] == ["sth"]
assert isinstance(lock["runtime"]["network_name"], str) and lock["runtime"]["network_name"]
assert isinstance(lock["runtime"]["ingress_network_name"], str) and lock["runtime"]["ingress_network_name"]
assert lock["runtime"]["network_name"] != lock["runtime"]["ingress_network_name"]
assert lock["runtime"]["realized_network_options"] == {
    "com.docker.network.enable_ipv4": "true",
    "com.docker.network.enable_ipv6": "false",
}
assert lock["runtime"]["project_scoped_volumes"] is True
assert lock["runtime"]["automatic_env_copy"] is False
assert set(lock["runtime"]["volume_names"]) == {"sth-app-data", "sth-db2-data"}
for image in lock["images"]:
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", image["linux_amd64_digest"])
PY

PROJECT_NAME=$(lock_value compose.project_name)
COMMIT=$(lock_value upstream.commit)
UPSTREAM_DIR="$ROOT_DIR/$(lock_value checkout.path)"
COMPOSE_FILE="$UPSTREAM_DIR/$(lock_value compose.path)"
BIND_ADDRESS=$(lock_value runtime.bind_address)
CONTAINER_HTTP_PORT=$(lock_value runtime.container_http_port)
NETWORK_NAME=$(lock_value runtime.network_name)
INGRESS_NETWORK_NAME=$(lock_value runtime.ingress_network_name)
APP_VOLUME=$(lock_value runtime.volume_names.sth-app-data)
DB_VOLUME=$(lock_value runtime.volume_names.sth-db2-data)
[ -n "$HTTP_PORT" ] || HTTP_PORT=$(lock_value runtime.default_http_port)
case "$HTTP_PORT" in *[!0-9]*|'') FAILURE_MESSAGE="HTTP port must be numeric."; exit 2;; esac
[ "$HTTP_PORT" -ge 1024 ] && [ "$HTTP_PORT" -le 65535 ] || { FAILURE_MESSAGE="HTTP port must be 1024..65535."; exit 2; }

STAGE=local-docker-boundary
"$PYTHON" -I - <<'PY' || { FAILURE_MESSAGE="Remote Docker context/daemon is forbidden."; exit 1; }
import os
for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
    if os.environ.get(key): raise SystemExit(1)
PY
set +e
CURRENT_DOCKER_CONTEXT=$(timeout --foreground 30 docker context show 2>> "$RAW_LOG")
CONTEXT_SHOW_CODE=$?
CONTEXT_HOST=$(timeout --foreground 30 docker context inspect --format '{{json .Endpoints.docker.Host}}' "$CURRENT_DOCKER_CONTEXT" 2>> "$RAW_LOG")
CONTEXT_CODE=$?
SERVER_PLATFORM=$(timeout --foreground 30 docker info --format '{{.OSType}}|{{.Architecture}}' 2>> "$RAW_LOG")
SERVER_CODE=$?
set -e
[ "$CONTEXT_SHOW_CODE" -eq 0 ] && [ "$CONTEXT_CODE" -eq 0 ] && [ "$SERVER_CODE" -eq 0 ] || { FAILURE_MESSAGE="Docker context/server inspection failed."; exit 1; }
"$PYTHON" -I - "$CURRENT_DOCKER_CONTEXT" "$CONTEXT_HOST" "$SERVER_PLATFORM" <<'PY' || { FAILURE_MESSAGE="Docker must use a named local-socket context and a linux/amd64 server."; exit 1; }
import json,sys
context=sys.argv[1];host=json.loads(sys.argv[2]);platform=sys.argv[3]
assert context and not any(ord(char)<32 for char in context)
assert host.startswith(("unix://", "npipe://"))
assert platform in {"linux|amd64", "linux|x86_64"}
PY

STAGE=docker-read-only-preflight
docker_call false --version
DOCKER_VERSION=$LAST_OUTPUT
docker_call false compose version
COMPOSE_VERSION=$LAST_OUTPUT
docker_call false ps -a --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{.ID}}'
[ -z "$LAST_OUTPUT" ] || { FAILURE_MESSAGE="Fresh deployment refuses existing project-labeled containers."; exit 1; }
  docker_call false network ls --quiet --filter "label=com.docker.compose.project=$PROJECT_NAME"
  [ -z "$LAST_OUTPUT" ] || { FAILURE_MESSAGE="Fresh deployment refuses existing project-labeled networks."; exit 1; }
  docker_call false volume ls --quiet --filter "label=com.docker.compose.project=$PROJECT_NAME"
  [ -z "$LAST_OUTPUT" ] || { FAILURE_MESSAGE="Fresh deployment refuses existing project-labeled volumes."; exit 1; }
for network_name in "$NETWORK_NAME" "$INGRESS_NETWORK_NAME"; do
  docker_call false network ls --quiet --filter "name=$network_name"
  [ -z "$LAST_OUTPUT" ] || { FAILURE_MESSAGE="Fresh deployment refuses an existing locked project network: $network_name"; exit 1; }
done
for container_name in "$PROJECT_NAME-sth" "$PROJECT_NAME-sth-db2"; do
  docker_call true container inspect --format '{{.Id}}' "$container_name"
  [ "$LAST_CODE" -ne 0 ] || { FAILURE_MESSAGE="Fresh deployment refuses existing target container name: $container_name"; exit 1; }
done
"$PYTHON" -I - "$BIND_ADDRESS" "$HTTP_PORT" <<'PY' || { FAILURE_MESSAGE="Approved loopback HTTP port is already occupied."; exit 1; }
import socket,sys
s=socket.socket(); s.bind((sys.argv[1],int(sys.argv[2]))); s.close()
PY
volume_check_strict sth-app-data "$APP_VOLUME"
volume_check_strict sth-db2-data "$DB_VOLUME"

STAGE=generate-runtime
"$PYTHON" -I - "$LOCK_FILE" "$UPSTREAM_DIR" "$RUNTIME_DIR" "$ENV_FILE" "$PINNED_DOCKERFILE" "$OVERLAY_FILE" "$HTTP_PORT" <<'PY' || { FAILURE_MESSAGE="Runtime generation or source verification failed."; exit 1; }
import base64, hashlib, json, os, pathlib, re, secrets, stat, subprocess, sys
lock_path, upstream_s, runtime_s, env_s, pinned_s, overlay_s, port_s = sys.argv[1:]
lock = json.load(open(lock_path, encoding="utf-8"))
upstream = pathlib.Path(upstream_s).resolve(); runtime = pathlib.Path(runtime_s).resolve()
env_path = pathlib.Path(env_s); pinned_path = pathlib.Path(pinned_s); overlay_path = pathlib.Path(overlay_s)
runtime.mkdir(parents=True, exist_ok=True)
head = subprocess.run(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
if head != lock["upstream"]["commit"]: raise SystemExit("HEAD mismatch")
dirty = subprocess.run(["git", "-C", str(upstream), "status", "--porcelain=v1", "--untracked-files=all"], text=True, capture_output=True, check=True).stdout
if dirty: raise SystemExit("dirty upstream")
forbidden = [
 ".env", "backend/.env.local", "backend/.env.local.php", "backend/config/secrets/prod/prod.decrypt.private.php",
 "backend/vendor", "backend/var", "backend/user_data", "frontend/node_modules", "frontend/.pnpm-store", "frontend/.angular/cache"
]
for rel in forbidden:
    if (upstream / rel).exists(): raise SystemExit(f"forbidden residue: {rel}")
if list((upstream / "backend").glob(".env.*.local")): raise SystemExit("forbidden backend .env.*.local")
for rel in lock["source_materialization"]["required_files"]:
    path = (upstream / rel).resolve()
    if upstream not in path.parents or not path.is_file(): raise SystemExit(f"missing source: {rel}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != lock["source_materialization"]["sha256"][rel]: raise SystemExit(f"hash mismatch: {rel}")
keys = [
 "APP_SECRET", "DB2_DBNAME", "DB2_PASSWORD", "DB2_ROOT_PASSWORD", "DB2_USER", "MAILER_DSN",
 "SERVER_HOST_NAME", "STH_ENV_NAME", "STH_FRONTEND_CONFIG", "STH_GCS_PATH_PREFIX", "STH_NOTIFICATIONS_ENABLED",
 "STH_LOCAL_REVIEW_LOGIN",
 "STH_VALIDATOR_ENDPOINT", "STH_JSON_VALIDATOR_ENDPOINT", "STH_SHACL_VALIDATOR_ENDPOINT", "STH_AI_GATEWAY_ENDPOINT",
 "STH_AI_GATEWAY_DEFAULT_MODEL_PROVIDER", "STH_AI_GATEWAY_DEFAULT_MODEL", "STH_AI_GATEWAY_DEFAULT_API_KEY", "APP_ENV", "APP_DEBUG"
]
for key in keys + ["DB2_TEST_DB_PASSWORD", "COMPOSE_PROJECT_NAME", "COMPOSE_FILE", "COMPOSE_PROFILES", "COMPOSE_ENV_FILES", "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"]:
    if key in os.environ: raise SystemExit(f"forbidden process env override: {key}")
if any(key.startswith("COMPOSE_") for key in os.environ): raise SystemExit("forbidden COMPOSE_* process env override")
if env_path.exists():
    if env_path.is_symlink(): raise SystemExit("runtime env symlink forbidden")
    if stat.S_IMODE(env_path.stat().st_mode) & 0o077: raise SystemExit("runtime env permissions must exclude group/other")
    rows = [line.split("=", 1) for line in env_path.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
    env = dict(rows)
    if len(rows) != len(env): raise SystemExit("runtime env contains duplicate keys")
    legacy_keys = set(keys) - {"STH_LOCAL_REVIEW_LOGIN"}
    if set(env) == legacy_keys:
        env["STH_LOCAL_REVIEW_LOGIN"] = "1"
    elif set(env) != set(keys):
        raise SystemExit("runtime env allowlist mismatch")
    if env["STH_LOCAL_REVIEW_LOGIN"] != "1": raise SystemExit("local review login requires the explicit value 1")
    env["SERVER_HOST_NAME"] = f"http://127.0.0.1:{port_s}"
    pending_env = env_path.with_name(f".{env_path.name}.{os.getpid()}.pending")
    try:
        fd = os.open(pending_env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(f"{key}={env[key]}" for key in keys) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(pending_env, env_path)
    finally:
        pending_env.unlink(missing_ok=True)
else:
    env = {
      "APP_SECRET": secrets.token_hex(32), "DB2_DBNAME": "app", "DB2_PASSWORD": secrets.token_hex(32),
      "DB2_ROOT_PASSWORD": secrets.token_hex(32), "DB2_USER": "sth_local", "MAILER_DSN": "null://null",
      "SERVER_HOST_NAME": f"http://127.0.0.1:{port_s}", "STH_ENV_NAME": "dssc-local", "STH_FRONTEND_CONFIG": "default",
      "STH_GCS_PATH_PREFIX": "", "STH_NOTIFICATIONS_ENABLED": "0", "STH_LOCAL_REVIEW_LOGIN": "1",
      "STH_VALIDATOR_ENDPOINT": "http://127.0.0.1:9",
      "STH_JSON_VALIDATOR_ENDPOINT": "http://127.0.0.1:9", "STH_SHACL_VALIDATOR_ENDPOINT": "http://127.0.0.1:9",
      "STH_AI_GATEWAY_ENDPOINT": "http://127.0.0.1:9", "STH_AI_GATEWAY_DEFAULT_MODEL_PROVIDER": "disabled",
      "STH_AI_GATEWAY_DEFAULT_MODEL": "disabled", "STH_AI_GATEWAY_DEFAULT_API_KEY": "disabled-local-only",
      "APP_ENV": "prod", "APP_DEBUG": "0"
    }
    fd = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(f"{key}={env[key]}" for key in keys) + "\n")
expected_server_host = f"http://127.0.0.1:{port_s}"
if env["APP_ENV"] != "prod" or env["APP_DEBUG"] != "0" or not re.fullmatch(r"[0-9a-f]{64}", env["APP_SECRET"]): raise SystemExit("production env invariant failed")
if env["SERVER_HOST_NAME"] != expected_server_host: raise SystemExit("loopback server host invariant failed")
if env["STH_LOCAL_REVIEW_LOGIN"] != "1": raise SystemExit("local review login invariant failed")
for key in ("DB2_PASSWORD", "DB2_ROOT_PASSWORD"):
    if not re.fullmatch(r"[0-9a-f]{64}", env[key]): raise SystemExit("synthetic DB secret invariant failed")
pins = {item["reference"]: item["linux_amd64_digest"] for item in lock["images"]}
project = lock["compose"]["project_name"]; commit = lock["upstream"]["commit"]; short = commit[:12]
source = (upstream / "Dockerfile").read_text(encoding="utf-8").replace("\r\n", "\n")
original_tokens = {
  "${STH_APP_VERSION_BUILD}": 1,
  "$STH_FRONTEND_CONFIG": 1,
  "$PHP_INI_DIR": 3,
}
for token, expected_count in original_tokens.items():
    if source.count(token) != expected_count: raise SystemExit(f"Dockerfile token cardinality changed: {token}")
source = source.replace("${STH_APP_VERSION_BUILD}", short)
source = source.replace("$STH_FRONTEND_CONFIG", "default")
source = source.replace("$PHP_INI_DIR", "/usr/local/etc/php")
replacements = {
 "FROM node:22 AS frontend-builder": f"FROM node:22@{pins['node:22']} AS frontend-builder",
 "FROM composer:2 AS backend-builder": f"FROM composer:2@{pins['composer:2']} AS backend-builder",
 "FROM dunglas/frankenphp:php8.4": f"FROM dunglas/frankenphp:php8.4@{pins['dunglas/frankenphp:php8.4']}",
}
for old, new in replacements.items():
    if source.splitlines().count(old) != 1: raise SystemExit(f"FROM replacement cardinality: {old}")
    source = source.replace(old, new)
security_relative = "backend/src/Controller/SecurityController.php"
security_container = "/app/src/Controller/SecurityController.php"
security_source_sha256 = "14332816e463349182363e2446799e88ce2f7c78bfdf2b63487e12d7f2a1c06d"
security_patched_sha256 = "f694f53157af74fc706fda6a36dd63e4d033d7f3620703290246edbaac0312b1"
security_path = upstream / security_relative
security_bytes = security_path.read_bytes()
if hashlib.sha256(security_bytes).hexdigest() != security_source_sha256: raise SystemExit("SecurityController source hash mismatch")
security_text = security_bytes.decode("utf-8")
security_before = """    ): Response {
        $this->denyUnlessDev($kernel);

        // Save login timestamp"""
security_after = """    ): Response {
        if ($kernel->getEnvironment() !== 'dev' && (getenv('STH_LOCAL_REVIEW_LOGIN') !== '1' || $account->getId() !== 'admin')) {
            throw $this->createAccessDeniedException('Only for development or explicit admin local review');
        }

        // Save login timestamp"""
if security_text.count(security_before) != 1: raise SystemExit("SecurityController devLogin patch cardinality changed")
if security_text.count("$this->denyUnlessDev($kernel);") != 2: raise SystemExit("SecurityController development guard cardinality changed")
json_login_body = security_text.split("public function jsonLogin", 1)[1].split("#[Route('/account_info'", 1)[0]
if json_login_body.count("$this->denyUnlessDev($kernel);") != 1: raise SystemExit("jsonLogin development guard changed")
security_patched = security_text.replace(security_before, security_after)
if hashlib.sha256(security_patched.encode("utf-8")).hexdigest() != security_patched_sha256: raise SystemExit("SecurityController patched hash mismatch")
if security_patched.count("STH_LOCAL_REVIEW_LOGIN") != 1 or security_patched.count("$this->denyUnlessDev($kernel);") != 1: raise SystemExit("SecurityController patched scope mismatch")
if security_patched.count("$account->getId() !== 'admin'") != 1: raise SystemExit("SecurityController admin-only local-review scope mismatch")
security_before_b64 = base64.b64encode(security_before.encode("utf-8")).decode("ascii")
security_after_b64 = base64.b64encode(security_after.encode("utf-8")).decode("ascii")
runtime_copy_anchor = "COPY --from=backend-builder /app /app"
if source.splitlines().count(runtime_copy_anchor) != 1: raise SystemExit("runtime backend COPY cardinality changed")
security_patch_layer = f'''{runtime_copy_anchor}

# DSSC derived-runtime patch: explicit loopback-only local-review login in prod.
RUN printf '%s  %s\\n' '{security_source_sha256}' '{security_container}' | sha256sum -c - \\
 && php -r "file_put_contents('{security_container}', str_replace(base64_decode('{security_before_b64}'), base64_decode('{security_after_b64}'), file_get_contents('{security_container}')));" \\
 && printf '%s  %s\\n' '{security_patched_sha256}' '{security_container}' | sha256sum -c -'''
source = source.replace(runtime_copy_anchor, security_patch_layer)
if any("@sha256:" not in line for line in source.splitlines() if line.startswith("FROM ")): raise SystemExit("unpinned FROM remains")
if "$" in source: raise SystemExit("derived runtime Dockerfile must contain zero dollar tokens")
pinned_path.write_text(source.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
compose_inline = source
indent = "\n".join("    " + line for line in compose_inline.rstrip("\n").split("\n"))
images = {item["reference"]: item for item in lock["images"]}
mariadb = f"mariadb:11.4@{images['mariadb:11.4']['linux_amd64_digest']}"
app_image = f"{project}-sth:{short}"
vols = lock["runtime"]["volume_names"]
overlay = f'''name: "{project}"
x-dssc-pinned-build: &dssc-pinned-build
  context: .
  dockerfile_inline: |
{indent}
services:
  sth:
    container_name: "{project}-sth"
    image: "{app_image}"
    platform: "linux/amd64"
    build: *dssc-pinned-build
    environment: !override
      APP_ENV: "prod"
      APP_DEBUG: "0"
      APP_SECRET: "${{APP_SECRET}}"
      APP_DBUSER: "${{DB2_USER}}"
      APP_DBPASS: "${{DB2_PASSWORD}}"
      APP_DBHOST: "sth-db2"
      APP_DBNAME: "${{DB2_DBNAME}}"
      APP_DBVERSION: "11.4.10-MariaDB"
      SERVER_NAME: ":80"
      SERVER_HOST_NAME: "${{SERVER_HOST_NAME}}"
      MAILER_DSN: "${{MAILER_DSN}}"
      STH_GCS_PATH_PREFIX: ""
      STH_NOTIFICATIONS_ENABLED: "0"
      STH_LOCAL_REVIEW_LOGIN: "${{STH_LOCAL_REVIEW_LOGIN}}"
      STH_AI_GATEWAY_ENABLED: "0"
    depends_on: !override
      sth-db2:
        condition: service_healthy
        required: true
    ports: !override
      - target: {lock['runtime']['container_http_port']}
        published: "{port_s}"
        host_ip: "{lock['runtime']['bind_address']}"
        protocol: tcp
    security_opt:
      - no-new-privileges:true
    volumes: !override
      - "sth-app-data:/app/var/user_data"
    networks: !override
      - treehouse-internal
      - treehouse-ingress
    restart: "no"
    extra_hosts: !reset []
    privileged: false
    labels:
      dssc.semantic-treehouse.managed: "true"
      dssc.semantic-treehouse.project: "{project}"
      dssc.semantic-treehouse.upstream-commit: "{commit}"
      dssc.semantic-treehouse.runtime-contract: "v1"
  sth-db2:
    container_name: "{project}-sth-db2"
    platform: "linux/amd64"
    image: "{mariadb}"
    environment: !override
      MARIADB_DATABASE: "${{DB2_DBNAME}}"
      MARIADB_ROOT_PASSWORD: "${{DB2_ROOT_PASSWORD}}"
      MARIADB_USER: "${{DB2_USER}}"
      MARIADB_PASSWORD: "${{DB2_PASSWORD}}"
    ports: !override []
    volumes: !override
      - "sth-db2-data:/var/lib/mysql"
    security_opt:
      - no-new-privileges:true
    networks: !override
      - treehouse-internal
    restart: "no"
    extra_hosts: !reset []
    privileged: false
    healthcheck: !override
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 5s
      timeout: 5s
      retries: 30
      start_period: 20s
    labels:
      dssc.semantic-treehouse.managed: "true"
      dssc.semantic-treehouse.project: "{project}"
      dssc.semantic-treehouse.upstream-commit: "{commit}"
      dssc.semantic-treehouse.runtime-contract: "v1"
volumes:
  sth-app-data:
    external: true
    name: "{vols['sth-app-data']}"
  sth-db2-data:
    external: true
    name: "{vols['sth-db2-data']}"
networks:
  treehouse-internal:
    name: "{lock['runtime']['network_name']}"
    driver: bridge
    internal: true
    labels:
      dssc.semantic-treehouse.project: "{project}"
      dssc.semantic-treehouse.upstream-commit: "{commit}"
      dssc.semantic-treehouse.runtime-contract: "v1"
      dssc.semantic-treehouse.network-role: "internal"
  treehouse-ingress:
    name: "{lock['runtime']['ingress_network_name']}"
    driver: bridge
    internal: false
    labels:
      dssc.semantic-treehouse.project: "{project}"
      dssc.semantic-treehouse.upstream-commit: "{commit}"
      dssc.semantic-treehouse.runtime-contract: "v1"
      dssc.semantic-treehouse.network-role: "ingress"
'''
overlay_path.write_text(overlay, encoding="utf-8", newline="\n")
PY

STAGE=compose-static-validation
set +e
DB2_TEST_DB_PASSWORD=placeholder timeout --foreground 120 docker compose --project-name "$PROJECT_NAME" --project-directory "$UPSTREAM_DIR" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -f "$OVERLAY_FILE" config --format json > "$EFFECTIVE_CONFIG_FILE" 2> "$CONFIG_ERROR_FILE"
CONFIG_CODE=$?
set -e
cat "$CONFIG_ERROR_FILE" >> "$RAW_LOG"
[ "$CONFIG_CODE" -eq 0 ] || { FAILURE_MESSAGE="Effective Compose config failed with exit code $CONFIG_CODE."; exit "$CONFIG_CODE"; }
"$PYTHON" -I - "$CONFIG_ERROR_FILE" <<'PY' || { FAILURE_MESSAGE="Compose reported an unset-variable interpolation warning."; exit 1; }
import pathlib,re,sys
text=pathlib.Path(sys.argv[1]).read_text(encoding="utf-8",errors="replace").lower()
assert not re.search(r"\bvariable\b.*\bis not set\b",text,re.MULTILINE)
PY
"$PYTHON" -I - "$EFFECTIVE_CONFIG_FILE" "$SAFE_PROJECTION_FILE" "$LOCK_FILE" "$HTTP_PORT" "$PINNED_DOCKERFILE" "$ENV_FILE" "$OVERLAY_FILE" "$COMPOSE_FILE" "$CURRENT_DOCKER_CONTEXT" "$CONTEXT_HOST" "$SERVER_PLATFORM" "$PREPARE_ONLY" <<'PY' || { FAILURE_MESSAGE="Effective Compose safety projection failed."; exit 1; }
import json, pathlib, sys
config = json.load(open(sys.argv[1], encoding="utf-8")); lock = json.load(open(sys.argv[3], encoding="utf-8")); port = int(sys.argv[4])
services = config["services"]
closure = set(); pending = ["sth"]
while pending:
    name = pending.pop()
    if name in closure: continue
    if name not in services: raise SystemExit(f"missing service: {name}")
    closure.add(name)
    deps = services[name].get("depends_on", {})
    pending.extend(deps.keys() if isinstance(deps, dict) else deps)
if closure != {"sth", "sth-db2"}: raise SystemExit(f"unexpected target closure: {sorted(closure)}")
sth, db = services["sth"], services["sth-db2"]
if sth.get("container_name") != lock["compose"]["project_name"]+"-sth": raise SystemExit("sth container name invariant")
if db.get("container_name") != lock["compose"]["project_name"]+"-sth-db2": raise SystemExit("database container name invariant")
ports = sth.get("ports", [])
if len(ports) != 1: raise SystemExit("sth must publish exactly one port")
p = ports[0]
if str(p.get("host_ip")) != "127.0.0.1" or int(p.get("published")) != port or int(p.get("target")) != 80: raise SystemExit("loopback port invariant")
if db.get("ports"): raise SystemExit("database port publication forbidden")
expected_networks = {"sth": {"treehouse-internal", "treehouse-ingress"}, "sth-db2": {"treehouse-internal"}}
for name, svc in (("sth", sth), ("sth-db2", db)):
    if set(svc.get("networks", {})) != expected_networks[name]: raise SystemExit(f"network invariant: {name}")
    for forbidden in ("extra_hosts", "privileged", "cap_add", "devices"):
        if svc.get(forbidden): raise SystemExit(f"forbidden {forbidden}: {name}")
    if svc.get("security_opt") != ["no-new-privileges:true"]: raise SystemExit(f"security_opt invariant: {name}")
app_env=sth.get("environment", {})
app_keys={"APP_ENV","APP_DEBUG","APP_SECRET","APP_DBUSER","APP_DBPASS","APP_DBHOST","APP_DBNAME","APP_DBVERSION","SERVER_NAME","SERVER_HOST_NAME","MAILER_DSN","STH_GCS_PATH_PREFIX","STH_NOTIFICATIONS_ENABLED","STH_LOCAL_REVIEW_LOGIN","STH_AI_GATEWAY_ENABLED"}
if set(app_env)!=app_keys: raise SystemExit("application env allowlist invariant")
if str(app_env.get("APP_ENV")) != "prod" or str(app_env.get("APP_DEBUG")) != "0": raise SystemExit("prod env invariant")
if str(app_env.get("SERVER_HOST_NAME")) != f"http://127.0.0.1:{port}": raise SystemExit("server host invariant")
if str(app_env.get("STH_LOCAL_REVIEW_LOGIN")) != "1": raise SystemExit("explicit local review login invariant")
if len(str(app_env.get("APP_SECRET","")))!=64: raise SystemExit("APP_SECRET invariant")
db_env=db.get("environment", {})
if set(db_env)!={"MARIADB_DATABASE","MARIADB_ROOT_PASSWORD","MARIADB_USER","MARIADB_PASSWORD"}: raise SystemExit("database env allowlist invariant")
if any("TEST" in key for key in set(app_env)|set(db_env)): raise SystemExit("test environment forbidden")
expected_service_labels={"dssc.semantic-treehouse.managed":"true","dssc.semantic-treehouse.project":lock["compose"]["project_name"],"dssc.semantic-treehouse.upstream-commit":lock["upstream"]["commit"],"dssc.semantic-treehouse.runtime-contract":"v1"}
for name,svc in (("sth",sth),("sth-db2",db)):
    labels=svc.get("labels",{}) or {}
    if any(str(labels.get(k))!=v for k,v in expected_service_labels.items()): raise SystemExit(f"service label invariant: {name}")
def mounts(svc):
    return svc.get("volumes", []) or []
for mount in mounts(sth) + mounts(db):
    if isinstance(mount, dict) and mount.get("type") == "bind": raise SystemExit("host bind forbidden")
db_targets = {m.get("target") for m in mounts(db) if isinstance(m, dict)}
if db_targets != {"/var/lib/mysql"}: raise SystemExit("database mount invariant")
app_targets = {m.get("target") for m in mounts(sth) if isinstance(m, dict)}
if app_targets != {"/app/var/user_data"}: raise SystemExit("application mount invariant")
expected_db = next(i for i in lock["images"] if i["reference"] == "mariadb:11.4")
expected_db_ref = "mariadb:11.4@" + expected_db["linux_amd64_digest"]
if db.get("image") != expected_db_ref: raise SystemExit("MariaDB digest invariant")
build = sth.get("build", {})
inline = build.get("dockerfile_inline", "")
if len([line for line in inline.splitlines() if line.startswith("FROM ") and "@sha256:" in line]) != 3: raise SystemExit("pinned inline Dockerfile invariant")
pinned=pathlib.Path(sys.argv[5]).read_text(encoding="utf-8").replace("\r\n","\n").rstrip("\n")+"\n"
inline=inline.replace("\r\n","\n").rstrip("\n")+"\n"
functional=lambda text:[line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
if functional(inline) != functional(pinned) or "$" in inline or "$" in pinned: raise SystemExit("effective Compose config differs from the zero-dollar runtime Dockerfile")
auth_patch_source_sha256="14332816e463349182363e2446799e88ce2f7c78bfdf2b63487e12d7f2a1c06d"
auth_patch_target_sha256="f694f53157af74fc706fda6a36dd63e4d033d7f3620703290246edbaac0312b1"
if inline.count(auth_patch_source_sha256) != 1 or inline.count(auth_patch_target_sha256) != 1: raise SystemExit("auth patch hash checks missing or duplicated")
if inline.count("/app/src/Controller/SecurityController.php") != 4: raise SystemExit("auth patch target path cardinality")
if inline.count("sha256sum -c -") != 2: raise SystemExit("auth patch build hash check cardinality")
networks = config.get("networks", {})
if set(networks) != {"treehouse-internal", "treehouse-ingress"}: raise SystemExit("network definition invariant")
network_specs = {
 "treehouse-internal": (lock["runtime"]["network_name"], True, "internal"),
 "treehouse-ingress": (lock["runtime"]["ingress_network_name"], False, "ingress"),
}
for logical, (physical, internal, role) in network_specs.items():
    net = networks.get(logical, {})
    if net.get("internal") is not internal or net.get("name") != physical: raise SystemExit(f"{role} network invariant")
    if net.get("driver") != "bridge" or (net.get("driver_opts") or {}) != {}: raise SystemExit(f"{role} bridge invariant")
    if "external" in net: raise SystemExit(f"{role} network must be project managed")
    network_labels = net.get("labels", {}) or {}
    expected_network_labels = {
      "dssc.semantic-treehouse.project": lock["compose"]["project_name"],
      "dssc.semantic-treehouse.upstream-commit": lock["upstream"]["commit"],
      "dssc.semantic-treehouse.runtime-contract": "v1",
      "dssc.semantic-treehouse.network-role": role,
    }
    if any(str(network_labels.get(key)) != value for key, value in expected_network_labels.items()): raise SystemExit(f"{role} network label invariant")
for logical,name in lock["runtime"]["volume_names"].items():
    volume=config.get("volumes",{}).get(logical,{})
    if volume.get("external") is not True or volume.get("name")!=name: raise SystemExit("external volume invariant")
import hashlib
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
docker_host=json.loads(sys.argv[10]);server_os,server_arch=sys.argv[11].split("|",1)
if server_arch=="x86_64":server_arch="amd64"
projection = {
 "schema": "dssc.semantic-treehouse.runtime-boundary.v1", "status": "PASS", "prepare_only": sys.argv[12] == "true",
 "project_name": lock["compose"]["project_name"], "upstream_commit": lock["upstream"]["commit"],
 "lock_sha256": sha(sys.argv[3]), "synthetic_env_sha256": sha(sys.argv[6]),
 "overlay_sha256": sha(sys.argv[7]), "compose_sha256": sha(sys.argv[8]),
 "docker": {"context":sys.argv[9],"endpoint_scheme":docker_host.split(":",1)[0],"server_os":server_os,"server_architecture":server_arch,"remote_daemon":False},
 "boundary": {
   "dependency_closure": sorted(closure), "target_service": "sth", "dependency_service": "sth-db2",
   "http_binding": f"127.0.0.1:{port}:80", "published_ports": [{"host_ip": "127.0.0.1", "published": port, "target": 80}],
   "database_published_ports": 0, "network_topology": "dual-network-app-ingress",
   "internal_network": lock["runtime"]["network_name"], "ingress_network": lock["runtime"]["ingress_network_name"],
   "application_networks": [lock["runtime"]["network_name"], lock["runtime"]["ingress_network_name"]],
   "database_networks": [lock["runtime"]["network_name"]],
   "networks": [
     {"name": lock["runtime"]["network_name"], "internal": True, "driver": "bridge", "role": "internal"},
     {"name": lock["runtime"]["ingress_network_name"], "internal": False, "driver": "bridge", "role": "ingress"},
   ],
   "app_outbound_access": True, "configured_driver_options": {},
   "expected_realized_network_options": lock["runtime"]["realized_network_options"],
   "host_binds": [], "forbidden_privilege_features": [], "security_opt": ["no-new-privileges:true"],
   "known_review": {"user": "image-default/empty accepted by finding-specific opt-in", "read_only": "not forced; upstream compatibility preserved"},
   "target_closure_test_interpolation_sentinel_effective": False,
   "app_environment": {"APP_ENV": "prod", "APP_DEBUG": "0", "APP_SECRET": "present-redacted", "SERVER_HOST_NAME": f"http://127.0.0.1:{port}", "STH_LOCAL_REVIEW_LOGIN": "1"},
   "application_environment_allowlist": sorted(app_keys),
   "database_environment_allowlist": sorted(db_env),
   "local_review_login_enabled": True,
   "local_review_login": True,
   "local_review_login_scope": "loopback-fake-admin-devLogin-only",
   "auth_patch_source_sha256": auth_patch_source_sha256,
   "auth_patch_target_sha256": auth_patch_target_sha256,
   "auth_patch_scope": "devLogin-only",
   "json_login_policy": "dev-only-unchanged",
   "security_controller_patch": {
     "source_path": "backend/src/Controller/SecurityController.php",
     "container_path": "/app/src/Controller/SecurityController.php",
     "source_sha256": auth_patch_source_sha256,
     "patched_sha256": auth_patch_target_sha256,
     "exact_replacement_count": 1,
     "build_preimage_hash_check": True,
     "build_postimage_hash_check": True,
     "runtime_flag": "STH_LOCAL_REVIEW_LOGIN",
     "required_runtime_value": "1",
     "dev_login_policy": "dev-or-explicit-admin-local-review",
     "json_login_policy": "dev-only-unchanged",
     "mutation_scope": "derived-runtime-image-only",
     "upstream_checkout_modified": False,
   },
   "mariadb_image": expected_db_ref, "dockerfile_from_digest_count": 3,
   "volumes": sorted(lock["runtime"]["volume_names"].values()), "app_volume_target": "/app/var/user_data",
 }
}
pathlib.Path(sys.argv[2]).write_text(json.dumps(projection, indent=2) + "\n", encoding="utf-8", newline="\n")
PY

STAGE=build-plan-static-validation
set +e
DB2_TEST_DB_PASSWORD=placeholder timeout --foreground 120 docker compose --project-name "$PROJECT_NAME" --project-directory "$UPSTREAM_DIR" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -f "$OVERLAY_FILE" build --print sth > "$BUILD_PLAN_FILE" 2> "$BUILD_PLAN_ERROR_FILE"
BUILD_PLAN_CODE=$?
set -e
cat "$BUILD_PLAN_ERROR_FILE" >> "$RAW_LOG"
[ "$BUILD_PLAN_CODE" -eq 0 ] || { FAILURE_MESSAGE="Compose build plan failed with exit code $BUILD_PLAN_CODE."; exit "$BUILD_PLAN_CODE"; }
"$PYTHON" -I - "$BUILD_PLAN_FILE" "$BUILD_PLAN_ERROR_FILE" "$PINNED_DOCKERFILE" <<'PY' || { FAILURE_MESSAGE="BuildKit input plan differs from the verified pinned Dockerfile."; exit 1; }
import json,pathlib,re,sys
plan=json.load(open(sys.argv[1],encoding="utf-8")); stderr=pathlib.Path(sys.argv[2]).read_text(encoding="utf-8",errors="replace").lower()
assert not re.search(r"\bvariable\b.*\bis not set\b",stderr,re.MULTILINE)
inline=plan["target"]["sth"]["dockerfile-inline"].replace("\r\n","\n").rstrip("\n")+"\n"
pinned=pathlib.Path(sys.argv[3]).read_text(encoding="utf-8").replace("\r\n","\n").rstrip("\n")+"\n"
functional=lambda text:[line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
assert functional(inline)==functional(pinned)
assert "$" not in inline and "$" not in pinned
PY

STAGE=buildx-final-plan-validation
set +e
timeout --foreground 120 docker buildx bake --print -f - < "$BUILD_PLAN_FILE" > "$FINAL_BAKE_FILE" 2> "$FINAL_BAKE_ERROR_FILE"
FINAL_BAKE_CODE=$?
set -e
cat "$FINAL_BAKE_ERROR_FILE" >> "$RAW_LOG"
[ "$FINAL_BAKE_CODE" -eq 0 ] || { FAILURE_MESSAGE="Buildx final plan failed with exit code $FINAL_BAKE_CODE."; exit "$FINAL_BAKE_CODE"; }
"$PYTHON" -I - "$FINAL_BAKE_FILE" "$FINAL_BAKE_ERROR_FILE" "$PINNED_DOCKERFILE" <<'PY' || { FAILURE_MESSAGE="Final BuildKit functional Dockerfile projection differs from the verified runtime Dockerfile."; exit 1; }
import json,pathlib,re,sys
plan=json.load(open(sys.argv[1],encoding="utf-8")); stderr=pathlib.Path(sys.argv[2]).read_text(encoding="utf-8",errors="replace").lower()
assert not re.search(r"\bvariable\b.*\bis not set\b",stderr,re.MULTILINE)
final=plan["target"]["sth"]["dockerfile-inline"].replace("\r\n","\n").rstrip("\n")+"\n"
runtime=pathlib.Path(sys.argv[3]).read_text(encoding="utf-8").replace("\r\n","\n").rstrip("\n")+"\n"
functional=lambda text:[line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
assert functional(final)==functional(runtime)
assert "$" not in final and "$" not in runtime
PY
"$PYTHON" -I - "$SAFE_PROJECTION_FILE" <<'PY' || { FAILURE_MESSAGE="Safe boundary evidence could not record the three-layer Dockerfile validation."; exit 1; }
import json,pathlib,sys
path=pathlib.Path(sys.argv[1]); projection=json.load(open(path,encoding="utf-8"))
projection["derived_dockerfile_validation"]={"source_token_counts":{"version":1,"frontend_config":1,"php_ini_dir":3},"derived_runtime_source_patch":1,"auth_patch_source_sha256":"14332816e463349182363e2446799e88ce2f7c78bfdf2b63487e12d7f2a1c06d","auth_patch_target_sha256":"f694f53157af74fc706fda6a36dd63e4d033d7f3620703290246edbaac0312b1","version_literal":"locked-commit-short","frontend_config_literal":"default","php_ini_dir_literal":"/usr/local/etc/php","compose_config":"zero-dollar-functional-pass","compose_build_print":"zero-dollar-functional-pass","buildx_bake_print":"zero-dollar-functional-pass","final_dollar_count":0,"unset_variable_warning_count":0}
path.write_text(json.dumps(projection,indent=2)+"\n",encoding="utf-8",newline="\n")
PY
rm -f -- "$EFFECTIVE_CONFIG_FILE" "$CONFIG_ERROR_FILE" "$BUILD_PLAN_FILE" "$BUILD_PLAN_ERROR_FILE" "$FINAL_BAKE_FILE" "$FINAL_BAKE_ERROR_FILE"

"$PYTHON" -I - "$DETAILS_FILE" "$SAFE_PROJECTION_FILE" "$DOCKER_VERSION" "$COMPOSE_VERSION" "$PREPARE_ONLY" <<'PY'
import json, pathlib, sys
projection = json.load(open(sys.argv[2], encoding="utf-8"))
details = {"prepare_only": sys.argv[5] == "true", "safe_projection": projection, "docker_version": sys.argv[3], "compose_version": sys.argv[4], "upstream_env_copied": False, "volumes_created": False}
pathlib.Path(sys.argv[1]).write_text(json.dumps(details, indent=2) + "\n", encoding="utf-8", newline="\n")
PY

if [ "$PREPARE_ONLY" = true ]; then
  scrub_log
  write_evidence PASS 0 ""
  echo "Treehouse runtime preparation passed; no Docker workload was executed."
  exit 0
fi

# The fresh-resource boundary has passed.  A stale prior-success marker cannot
# describe this new invocation; only the post-smoke atomic promotion below may
# recreate it.
rm -f -- "$STATE_FILE" "$PENDING_STATE_FILE" "$REALIZED_INGRESS_FILE" "$REALIZED_NETWORK_OPTIONS_EVIDENCE"
FRESH_DEPLOYMENT_STARTED=true

STAGE=pull-pinned-database
WORKLOAD_ATTEMPTED=true
DOCKER_TIMEOUT_SECONDS=600 compose_call false pull sth-db2

STAGE=build-pinned-application
DOCKER_TIMEOUT_SECONDS=1800 compose_call false build sth

STAGE=inspect-built-images
APP_IMAGE=$(lock_value compose.project_name)-sth:$(printf '%s' "$COMMIT" | cut -c1-12)
DB_IMAGE="mariadb:11.4@$("$PYTHON" -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next(x["linux_amd64_digest"] for x in d["images"] if x["reference"]=="mariadb:11.4"))' "$LOCK_FILE")"
docker_call false image inspect --format '{{.Os}}/{{.Architecture}}|{{.Id}}|{{json .RepoDigests}}|{{json .Config.WorkingDir}}|{{json .Config.User}}|{{json .Config.Entrypoint}}|{{json .Config.Cmd}}' "$APP_IMAGE"
APP_INSPECT=$LAST_OUTPUT
docker_call false image inspect --format '{{.Os}}/{{.Architecture}}|{{.Id}}|{{json .RepoDigests}}|{{json .Config.WorkingDir}}|{{json .Config.User}}|{{json .Config.Entrypoint}}|{{json .Config.Cmd}}' "$DB_IMAGE"
DB_INSPECT=$LAST_OUTPUT
"$PYTHON" -I - "$APP_INSPECT" "$DB_INSPECT" "$LOCK_FILE" <<'PY' || { FAILURE_MESSAGE="Built image inspection failed."; exit 1; }
import json, sys
app, db, lock_path = sys.argv[1:]
if not app.startswith("linux/amd64|") or not db.startswith("linux/amd64|"): raise SystemExit(1)
lock = json.load(open(lock_path, encoding="utf-8")); pin = next(x for x in lock["images"] if x["reference"] == "mariadb:11.4")
repo = db.split("|", 3)[2]
if pin["linux_amd64_digest"] not in repo: raise SystemExit(1)
ap=app.split("|",6); dp=db.split("|",6)
if json.loads(ap[3]) != "/app": raise SystemExit(1)
for parts in (ap, dp):
    user=json.loads(parts[4])
    if user not in ("", "root", "0", "0:0"): raise SystemExit(1)
if "docker-php-entrypoint" not in json.dumps(json.loads(ap[5])) or "frankenphp" not in json.dumps(json.loads(ap[6])): raise SystemExit(1)
if "docker-entrypoint.sh" not in json.dumps(json.loads(dp[5])) or "mariadbd" not in json.dumps(json.loads(dp[6])): raise SystemExit(1)
PY

STAGE=create-fresh-labeled-volumes
for pair in "sth-app-data:$APP_VOLUME" "sth-db2-data:$DB_VOLUME"; do
  logical=${pair%%:*}; name=${pair#*:}
  docker_call false volume create \
    --label "com.docker.compose.project=$PROJECT_NAME" \
    --label "com.docker.compose.volume=$logical" \
    --label "dssc.semantic-treehouse.managed=true" \
    --label "dssc.semantic-treehouse.project=$PROJECT_NAME" \
    --label "dssc.semantic-treehouse.upstream-commit=$COMMIT" \
    --label "dssc.semantic-treehouse.logical-volume=$logical" \
    --label "dssc.semantic-treehouse.runtime-contract=v1" \
    "$name"
  if [ "$logical" = sth-app-data ]; then APP_VOLUME_CREATED=true; else DB_VOLUME_CREATED=true; fi
  verify_created_volume "$logical" "$name"
done

STAGE=compose-up-no-build-no-pull
CONTAINER_START_ATTEMPTED=true
DOCKER_TIMEOUT_SECONDS=300 compose_call false up -d --no-build --pull never sth

STAGE=realized-ingress-boundary
"$PYTHON" -I - "$REALIZED_INGRESS_FILE" "$REALIZED_NETWORK_OPTIONS_EVIDENCE" "$LOCK_FILE" "$SAFE_PROJECTION_FILE" "$PROJECT_NAME" "$COMMIT" "$NETWORK_NAME" "$INGRESS_NETWORK_NAME" "$HTTP_PORT" "$ROOT_DIR" "$ENV_FILE" <<'PY' || { FAILURE_MESSAGE="Realized Docker ingress/network boundary failed before migration."; exit 1; }
import hashlib, json, os, pathlib, re, subprocess, sys
out, options_out, lock_path, boundary_path, project, commit, internal_name, ingress_name, port, root, env_path = sys.argv[1:]
def inspect_json(kind, name, template):
    command = ["docker"] + (["network", "inspect"] if kind == "network" else ["inspect"]) + ["--format", template, name]
    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise SystemExit(1)
    return json.loads(result.stdout)
def published_count(mapping):
    return sum(len(value or []) for value in (mapping or {}).values())
lock = json.load(open(lock_path, encoding="utf-8"))
expected_options = lock["runtime"]["realized_network_options"]
approved_options = {
    "com.docker.network.enable_ipv4": "true",
    "com.docker.network.enable_ipv6": "false",
}
if expected_options != approved_options:
    raise SystemExit(1)
expected_common = {
 "com.docker.compose.project": project,
 "dssc.semantic-treehouse.project": project,
 "dssc.semantic-treehouse.upstream-commit": commit,
 "dssc.semantic-treehouse.runtime-contract": "v1",
}
secret_values=[]
env_file=pathlib.Path(env_path)
if env_file.is_file():
    for line in env_file.read_text(encoding="utf-8",errors="replace").splitlines():
        if "=" in line:
            key,value=line.split("=",1)
            if any(marker in key.lower() for marker in ("password","secret","api_key")) and value:secret_values.append(value)
home=str(pathlib.Path.home());username=os.environ.get("USER") or os.environ.get("USERNAME") or ""
def safe_scalar(value):
    text=str(value)
    for secret in secret_values:text=text.replace(secret,"<redacted-secret>")
    text=text.replace(root,"<repo>")
    if home:text=text.replace(home,"<user-home>")
    if len(username)>=3:text=text.replace(username,"<redacted-user>")
    text=re.sub(r"(?i)[A-Z]:\\Users\\[^\\\s\"']+", "<redacted-home>", text)
    text=re.sub(r"(?i)/(?:home/[^/\s\"']+|root)(?:/[^\s\"']*)?", "<redacted-home>", text)
    text=re.sub(r"(?i)(password|secret|token|credential)(\s*[=:]\s*)(\S+)",r"\1\2<redacted>",text)
    if len(text)>512 or any(ord(char)<32 for char in text):return "<redacted-unsafe-option>"
    return text
networks = []
network_boundary_pass = True
options_boundary_pass = True
for name, expected_internal, role in ((internal_name, True, "internal"), (ingress_name, False, "ingress")):
    actual_internal = inspect_json("network", name, "{{json .Internal}}")
    driver = inspect_json("network", name, "{{json .Driver}}")
    options = inspect_json("network", name, "{{json .Options}}")
    labels = inspect_json("network", name, "{{json .Labels}}") or {}
    expected_labels = dict(expected_common); expected_labels["dssc.semantic-treehouse.network-role"] = role
    labels_match = all(str(labels.get(key)) == value for key, value in expected_labels.items())
    options_match = isinstance(options, dict) and options == expected_options
    network_pass = actual_internal is expected_internal and driver == "bridge" and options_match and labels_match
    network_boundary_pass = network_boundary_pass and network_pass
    options_boundary_pass = options_boundary_pass and options_match
    safe_options={safe_scalar(key):safe_scalar(value) for key,value in sorted(options.items())} if isinstance(options,dict) else {}
    networks.append({
      "name": name,
      "role": role,
      "internal": actual_internal,
      "driver": safe_scalar(driver),
      "options": safe_options,
      "options_match": options_match,
    })
options_projection = {
  "schema": "dssc.semantic-treehouse.runtime-network-options.v1",
  "status": "PASS" if options_boundary_pass and len(networks)==2 else "REJECTED",
  "upstream_commit": commit,
  "project_name": project,
  "lock_sha256": hashlib.sha256(pathlib.Path(lock_path).read_bytes()).hexdigest(),
  "runtime_boundary_sha256": hashlib.sha256(pathlib.Path(boundary_path).read_bytes()).hexdigest(),
  "compose_driver_options": "EMPTY",
  "expected_options": expected_options,
  "networks": networks,
}
options_path = pathlib.Path(options_out)
options_path.parent.mkdir(parents=True, exist_ok=True)
with open(options_path, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(options_projection, fh, indent=2, sort_keys=True)
    fh.write("\n")
    fh.flush()
    os.fsync(fh.fileno())
evidence_text=options_path.read_text(encoding="utf-8")
if any(value and value in evidence_text for value in secret_values) or root in evidence_text or (home and home in evidence_text) or (len(username)>=3 and username in evidence_text):
    raise SystemExit(1)
if not network_boundary_pass:
    raise SystemExit(1)
app_name, db_name = project + "-sth", project + "-sth-db2"
app_networks = inspect_json("container", app_name, "{{json .NetworkSettings.Networks}}") or {}
db_networks = inspect_json("container", db_name, "{{json .NetworkSettings.Networks}}") or {}
if set(app_networks) != {internal_name, ingress_name} or set(db_networks) != {internal_name}:
    raise SystemExit(1)
app_ports = inspect_json("container", app_name, "{{json .NetworkSettings.Ports}}") or {}
app_requested = inspect_json("container", app_name, "{{json .HostConfig.PortBindings}}") or {}
db_ports = inspect_json("container", db_name, "{{json .NetworkSettings.Ports}}") or {}
db_requested = inspect_json("container", db_name, "{{json .HostConfig.PortBindings}}") or {}
if set(app_ports) != {"80/tcp"} or set(app_requested) != {"80/tcp"}:
    raise SystemExit(1)
realized, requested = app_ports["80/tcp"] or [], app_requested["80/tcp"] or []
if len(realized) != 1 or len(requested) != 1:
    raise SystemExit(1)
for binding in (realized[0], requested[0]):
    if str(binding.get("HostIp")) != "127.0.0.1" or str(binding.get("HostPort")) != port:
        raise SystemExit(1)
if published_count(db_ports) != 0 or published_count(db_requested) != 0:
    raise SystemExit(1)
projection = {
 "status": "PASS", "binding": "127.0.0.1:" + port + ":80",
 "network_settings_ports_programmed": True, "host_config_binding_matches": True,
 "application_networks": [internal_name, ingress_name], "database_networks": [internal_name],
 "database_published_ports": 0, "application_outbound_access": True, "networks": networks,
 "realized_network_options_evidence_sha256": hashlib.sha256(options_path.read_bytes()).hexdigest(),
}
pathlib.Path(out).write_text(json.dumps(projection, indent=2) + "\n", encoding="utf-8", newline="\n")
PY

STAGE=database-readiness
DB_READY=false
DB_ATTEMPTS=0
while [ "$DB_ATTEMPTS" -lt 20 ]; do
  DB_ATTEMPTS=$((DB_ATTEMPTS + 1))
  DOCKER_TIMEOUT_SECONDS=2 compose_call true exec -T sth-db2 sh -c 'mariadb-admin ping -h 127.0.0.1 -uroot --password="$MARIADB_ROOT_PASSWORD" --silent'
  if [ "$LAST_CODE" -eq 0 ]; then DB_READY=true; break; fi
  sleep 1
done
[ "$DB_READY" = true ] || { FAILURE_MESSAGE="Database readiness failed within 60 seconds."; exit 1; }

STAGE=production-migration
DOCKER_TIMEOUT_SECONDS=300 compose_call false exec -T --workdir /app sth php bin/console --env=prod doctrine:migrations:sync-metadata-storage --no-interaction
DOCKER_TIMEOUT_SECONDS=600 compose_call false exec -T --workdir /app sth php bin/console --env=prod doctrine:migrations:migrate --no-interaction

STAGE=write-pending-runtime-state
"$PYTHON" -I - "$PENDING_STATE_FILE" "$LOCK_FILE" "$ENV_FILE" "$OVERLAY_FILE" "$COMPOSE_FILE" "$SAFE_PROJECTION_FILE" "$REALIZED_INGRESS_FILE" "$HTTP_PORT" "$APP_VOLUME" "$DB_VOLUME" <<'PY' || { FAILURE_MESSAGE="Pending runtime state could not be written after migration."; exit 1; }
import hashlib,json,os,pathlib,sys
pending,lock_p,env_p,overlay_p,compose_p,boundary_p,realized_p,port,app_volume,db_volume=sys.argv[1:]
lock=json.load(open(lock_p,encoding="utf-8"));sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
state={"schema":"dssc.semantic-treehouse.runtime-state.v1","upstream_commit":lock["upstream"]["commit"],"project_name":lock["compose"]["project_name"],
"lock_sha256":sha(lock_p),"runtime_boundary_sha256":sha(boundary_p),"compose_sha256":sha(compose_p),"overlay_sha256":sha(overlay_p),"synthetic_env_sha256":sha(env_p),
"volumes":[app_volume,db_volume],"bind_address":"127.0.0.1","http_port":int(port),"network_topology":"dual-network-app-ingress",
"server_host_name":f"http://127.0.0.1:{port}","local_review_login":True,"local_review_login_scope":"loopback-fake-admin-devLogin-only","application_volume_target":"/app/var/user_data",
"internal_network":lock["runtime"]["network_name"],"ingress_network":lock["runtime"]["ingress_network_name"],"application_outbound_access":True,
"realized_ingress":json.load(open(realized_p,encoding="utf-8")),"deployment":"PENDING_SMOKE","first_migration":"PASS","production_migration":"PASS",
"smoke":"PENDING","root_smoke":"PENDING","api_smoke":"PENDING","local_review_login_smoke":"PENDING","success_state":False}
with open(pending,"x",encoding="utf-8",newline="\n") as fh:
  json.dump(state,fh,indent=2);fh.write("\n");fh.flush();os.fsync(fh.fileno())
PY

run_loopback_smoke() {
  smoke_url=$1; smoke_headers=$2; smoke_attempt=0
  while [ "$smoke_attempt" -lt 20 ]; do
    smoke_attempt=$((smoke_attempt + 1)); set +e
    candidate=$(curl --noproxy '*' --silent --show-error --output /dev/null --dump-header "$smoke_headers" --write-out '%{http_code}' --max-time 5 "$smoke_url" 2>> "$RAW_LOG"); curl_code=$?
    set -e; accepted=false
    case "$candidate" in
      2??) [ "$curl_code" -eq 0 ] && accepted=true ;;
      301|302|303|307|308)
        if [ "$curl_code" -eq 0 ] && "$PYTHON" -I - "$smoke_headers" "$smoke_url" <<'PY'
import pathlib,sys,urllib.parse
headers=pathlib.Path(sys.argv[1]).read_text(encoding="iso-8859-1",errors="replace").splitlines();base=urllib.parse.urlsplit(sys.argv[2]);locations=[]
for line in headers:
  if line.lower().startswith("location:"):locations.append(line.split(":",1)[1].strip())
assert locations
target=urllib.parse.urlsplit(urllib.parse.urljoin(sys.argv[2],locations[-1]))
assert target.scheme=="http" and target.hostname in {"127.0.0.1","localhost"} and target.port==base.port
assert target.username is None and target.password is None
PY
        then accepted=true; fi ;;
    esac
    if [ "$accepted" = true ]; then printf '%s|%s\n' "$candidate" "$smoke_attempt"; return 0; fi
    sleep 2
  done
  return 1
}

run_local_review_login_smoke() (
  auth_base_url=$1
  trap 'rm -f -- "$AUTH_COOKIE_JAR" "$AUTH_LOGIN_HEADER_FILE" "$AUTH_ACCOUNT_BODY_FILE"' 0
  rm -f -- "$AUTH_COOKIE_JAR" "$AUTH_LOGIN_HEADER_FILE" "$AUTH_ACCOUNT_BODY_FILE"
  [ "$BIND_ADDRESS" = "127.0.0.1" ] || return 1
  login_url="${auth_base_url%/}/api/security/dev_login/admin"
  account_url="${auth_base_url%/}/api/security/account_info"

  set +e
  login_status=$(curl --noproxy '*' --silent --show-error --output /dev/null \
    --dump-header "$AUTH_LOGIN_HEADER_FILE" --cookie-jar "$AUTH_COOKIE_JAR" \
    --write-out '%{http_code}' --max-time 15 "$login_url" 2>> "$RAW_LOG")
  login_code=$?
  set -e
  [ "$login_code" -eq 0 ] || return 1
  case "$login_status" in 301|302|303|307|308) ;; *) return 1 ;; esac
  [ -f "$AUTH_COOKIE_JAR" ] && [ -f "$AUTH_LOGIN_HEADER_FILE" ] || return 1

  "$PYTHON" -I - "$AUTH_LOGIN_HEADER_FILE" "$login_url" "$auth_base_url" <<'PY' || return 1
import pathlib, sys, urllib.parse
headers = pathlib.Path(sys.argv[1]).read_text(encoding="iso-8859-1", errors="replace").splitlines()
login = urllib.parse.urlsplit(sys.argv[2]); base = urllib.parse.urlsplit(sys.argv[3])
locations = [line.split(":", 1)[1].strip() for line in headers if line.lower().startswith("location:")]
assert locations
target = urllib.parse.urlsplit(urllib.parse.urljoin(sys.argv[2], locations[-1]))
assert base.scheme == "http" and base.hostname == "127.0.0.1" and base.port is not None
assert login.scheme == "http" and login.hostname == "127.0.0.1" and login.port == base.port
assert target.scheme == "http" and target.hostname in {"127.0.0.1", "localhost"} and target.port == base.port
assert target.username is None and target.password is None
PY

  set +e
  account_status=$(curl --noproxy '*' --silent --show-error --output "$AUTH_ACCOUNT_BODY_FILE" \
    --cookie "$AUTH_COOKIE_JAR" --write-out '%{http_code}' --max-time 15 \
    "$account_url" 2>> "$RAW_LOG")
  account_code=$?
  set -e
  [ "$account_code" -eq 0 ] && [ "$account_status" = "200" ] && [ -f "$AUTH_ACCOUNT_BODY_FILE" ] || return 1

  "$PYTHON" -I - "$AUTH_LOGIN_HEADER_FILE" "$AUTH_ACCOUNT_BODY_FILE" "$login_url" "$auth_base_url" "$login_status" "$account_status" <<'PY'
import json, pathlib, sys, urllib.parse
headers_path, account_path, login_url, base_url, login_status, account_status = sys.argv[1:]
headers = pathlib.Path(headers_path).read_text(encoding="iso-8859-1", errors="replace").splitlines()
locations = [line.split(":", 1)[1].strip() for line in headers if line.lower().startswith("location:")]
assert locations
base = urllib.parse.urlsplit(base_url)
redirect = urllib.parse.urlsplit(urllib.parse.urljoin(login_url, locations[-1]))
account = json.loads(pathlib.Path(account_path).read_text(encoding="utf-8"))
assert account.get("id") == "admin" and account.get("username") == "admin"
roles = account.get("roles")
assert isinstance(roles, list) and "ROLE_ADMINISTRATOR" in roles
projection = {
  "name": "local-review-admin-login",
  "status": "PASS",
  "login_path": "/api/security/dev_login/admin",
  "login_status_code": int(login_status),
  "login_redirect": {"scheme": redirect.scheme, "host": redirect.hostname, "port": redirect.port, "path": redirect.path},
  "account_info_path": "/api/security/account_info",
  "account_info_status_code": int(account_status),
  "account_id": "admin",
  "account_username": "admin",
  "administrator_role_present": True,
  "cookie_aware": True,
  "cookie_values_recorded": False,
  "client_session_material_persisted": False,
  "app_env": "prod",
  "explicit_opt_in": True,
  "json_login_policy": "dev-only-unchanged-static-hash-verified",
}
assert base.scheme == "http" and base.hostname == "127.0.0.1" and redirect.port == base.port
print(json.dumps(projection, separators=(",", ":")))
PY
)

STAGE=loopback-root-and-api-smoke
command -v curl >/dev/null 2>&1 || { FAILURE_MESSAGE="curl is required for the loopback smoke checks."; exit 1; }
ROOT_SMOKE_URL="http://$BIND_ADDRESS:$HTTP_PORT/"; API_SMOKE_URL="http://$BIND_ADDRESS:$HTTP_PORT/api/environment/info"
set +e; ROOT_SMOKE_RESULT=$(run_loopback_smoke "$ROOT_SMOKE_URL" "$ROOT_SMOKE_HEADER_FILE"); ROOT_SMOKE_CODE=$?; set -e
[ "$ROOT_SMOKE_CODE" -eq 0 ] || { FAILURE_MESSAGE="Root loopback GET smoke failed within the bounded window."; exit 1; }
set +e; API_SMOKE_RESULT=$(run_loopback_smoke "$API_SMOKE_URL" "$API_SMOKE_HEADER_FILE"); API_SMOKE_CODE=$?; set -e
[ "$API_SMOKE_CODE" -eq 0 ] || { FAILURE_MESSAGE="API loopback GET smoke failed within the bounded window."; exit 1; }
ROOT_HTTP_STATUS=${ROOT_SMOKE_RESULT%%|*}; ROOT_SMOKE_ATTEMPTS=${ROOT_SMOKE_RESULT#*|}
API_HTTP_STATUS=${API_SMOKE_RESULT%%|*}; API_SMOKE_ATTEMPTS=${API_SMOKE_RESULT#*|}

STAGE=loopback-local-review-login-smoke
set +e; LOCAL_REVIEW_LOGIN_SMOKE=$(run_local_review_login_smoke "$ROOT_SMOKE_URL"); LOCAL_REVIEW_LOGIN_SMOKE_CODE=$?; set -e
[ "$LOCAL_REVIEW_LOGIN_SMOKE_CODE" -eq 0 ] || { FAILURE_MESSAGE="Cookie-aware local-review admin login smoke failed."; exit 1; }
[ ! -e "$AUTH_COOKIE_JAR" ] && [ ! -e "$AUTH_LOGIN_HEADER_FILE" ] && [ ! -e "$AUTH_ACCOUNT_BODY_FILE" ] || { FAILURE_MESSAGE="Local-review authentication session material was not removed."; exit 1; }

STAGE=commit-success-state
"$PYTHON" -I - "$PENDING_STATE_FILE" "$STATE_FILE" <<'PY' || { FAILURE_MESSAGE="Successful runtime state could not be committed atomically."; exit 1; }
import json,os,pathlib,sys
pending=pathlib.Path(sys.argv[1]);target=pathlib.Path(sys.argv[2]);state=json.load(open(pending,encoding="utf-8"))
assert state["deployment"]=="PENDING_SMOKE" and state["smoke"]=="PENDING" and state["local_review_login_smoke"]=="PENDING" and state["success_state"] is False
state.update({"deployment":"PASS","smoke":"PASS","root_smoke":"PASS","api_smoke":"PASS","local_review_login_smoke":"PASS","success_state":True})
with open(pending,"w",encoding="utf-8",newline="\n") as fh:
  json.dump(state,fh,indent=2);fh.write("\n");fh.flush();os.fsync(fh.fileno())
if target.exists():raise SystemExit("stale success state appeared")
os.replace(pending,target)
PY

STAGE=capture-filtered-status
docker_call false ps -a --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{json .}}'
FILTERED_STATUS=$LAST_OUTPUT
"$PYTHON" -I - "$DETAILS_FILE" "$SAFE_PROJECTION_FILE" "$REALIZED_INGRESS_FILE" "$DOCKER_VERSION" "$COMPOSE_VERSION" "$APP_INSPECT" "$DB_INSPECT" "$ROOT_SMOKE_URL" "$ROOT_HTTP_STATUS" "$ROOT_SMOKE_ATTEMPTS" "$API_SMOKE_URL" "$API_HTTP_STATUS" "$API_SMOKE_ATTEMPTS" "$LOCAL_REVIEW_LOGIN_SMOKE" "$DB_ATTEMPTS" "$FILTERED_STATUS" <<'PY'
import json, pathlib, sys
(out,projection_path,realized_path,docker_version,compose_version,app_inspect,db_inspect,root_url,
 root_status,root_attempts,api_url,api_status,api_attempts,local_review_login_smoke,db_attempts,filtered)=sys.argv[1:]
details = {
 "deployment": "PASS", "ui_smoke": "PASS", "api": "PASS", "authentication": "PASS", "import": "NOT RUN", "export": "NOT RUN",
 "safe_projection": json.load(open(projection_path, encoding="utf-8")), "docker_version": docker_version,
 "compose_version": compose_version, "app_image_projection": app_inspect, "database_image_projection": db_inspect,
 "realized_ingress":json.load(open(realized_path,encoding="utf-8")),"database_readiness_attempts":int(db_attempts),
 "root_smoke":{"url":root_url,"http_status":int(root_status),"attempts":int(root_attempts)},
 "api_smoke":{"url":api_url,"http_status":int(api_status),"attempts":int(api_attempts)},
 "local_review_login_smoke":json.loads(local_review_login_smoke),
 "filtered_container_status": filtered, "volumes_created": True,
}
pathlib.Path(out).write_text(json.dumps(details, indent=2) + "\n", encoding="utf-8", newline="\n")
PY

scrub_log
rm -f -- "$ROOT_SMOKE_HEADER_FILE" "$API_SMOKE_HEADER_FILE" "$AUTH_COOKIE_JAR" "$AUTH_LOGIN_HEADER_FILE" "$AUTH_ACCOUNT_BODY_FILE" "$REALIZED_INGRESS_FILE"
write_evidence PASS 0 ""
echo "Semantic Treehouse is running at $ROOT_SMOKE_URL"
exit 0
