#!/usr/bin/env sh
set -eu
umask 077

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
LOCK_FILE="$ROOT_DIR/tools/semantic-treehouse/upstream.lock.json"
PYTHON="$ROOT_DIR/.venv/bin/python"
RUNTIME_DIR="$ROOT_DIR/build/phase-08/treehouse-runtime"
EVIDENCE_DIR="$ROOT_DIR/build/evidence/treehouse"
STATE_FILE="$RUNTIME_DIR/runtime-state.json"
ENV_FILE="$RUNTIME_DIR/synthetic.env"
OVERLAY_FILE="$RUNTIME_DIR/compose.runtime.yml"
BOUNDARY_FILE="$RUNTIME_DIR/runtime-boundary.json"
RAW_LOG="$RUNTIME_DIR/down.raw.log"
CLEAN_LOG="$EVIDENCE_DIR/treehouse-down.log"
EVIDENCE_FILE="$EVIDENCE_DIR/runtime-down.json"
NETWORK_OPTIONS_EVIDENCE_FILE="$EVIDENCE_DIR/runtime-network-options.json"
BEFORE_FILE="$RUNTIME_DIR/.down-before.json"
AFTER_FILE="$RUNTIME_DIR/.down-after.json"
STATE_HASH_FILE="$RUNTIME_DIR/.down-state-sha256"
STAGE=initialize
FAILURE_MESSAGE=""
DOWN_ATTEMPTED=false
DOWN_EXIT=""

[ -x "$PYTHON" ] || { echo "Repository .venv Python is required: .venv/bin/python" >&2; exit 1; }
command -v timeout >/dev/null 2>&1 || { echo "GNU timeout is required for bounded Docker operations." >&2; exit 1; }
mkdir -p "$RUNTIME_DIR" "$EVIDENCE_DIR"
rm -f -- "$BEFORE_FILE" "$AFTER_FILE" "$STATE_HASH_FILE"
: > "$RAW_LOG"

lock_value() {
  "$PYTHON" -I -c 'import json,sys; v=json.load(open(sys.argv[1],encoding="utf-8"));
for p in sys.argv[2].split("."): v=v[p]
print(v)' "$LOCK_FILE" "$1"
}

docker_capture() {
  outfile=$1; allow=$2; shift 2
  printf '[%s] docker' "$STAGE" >> "$RAW_LOG"; for arg in "$@"; do printf ' %s' "$arg" >> "$RAW_LOG"; done; printf '\n' >> "$RAW_LOG"
  set +e; timeout --foreground 120 docker "$@" > "$outfile" 2>> "$RAW_LOG"; LAST_CODE=$?; set -e
  printf '[%s] exit=%s\n' "$STAGE" "$LAST_CODE" >> "$RAW_LOG"
  if [ "$LAST_CODE" -ne 0 ] && [ "$allow" != true ]; then FAILURE_MESSAGE="Docker command failed at $STAGE with exit code $LAST_CODE"; exit "$LAST_CODE"; fi
}

capture_boundary() {
  output=$1
  containers="$RUNTIME_DIR/.down-containers.tmp"
  networks="$RUNTIME_DIR/.down-networks.tmp"
  volumes="$RUNTIME_DIR/.down-volumes.tmp"
  STAGE=filtered-resource-query
  docker_capture "$containers" false ps -a --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{json .}}'
  docker_capture "$networks" false network ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{json .}}'
  docker_capture "$volumes" false volume ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{json .}}'
  "$PYTHON" -I - "$containers" "$networks" "$volumes" "$output" "$LOCK_FILE" "$PROJECT_NAME" "$COMMIT" "$NETWORK_NAME" "$INGRESS_NETWORK_NAME" "$APP_VOLUME" "$DB_VOLUME" <<'PY' || { FAILURE_MESSAGE="Project resource label boundary failed."; exit 1; }
import hashlib,json,pathlib,subprocess,sys
containers,networks,volumes,out,lock_p,project,commit,network_name,ingress_name,app_volume,db_volume=sys.argv[1:]
lock=json.load(open(lock_p,encoding="utf-8"));expected_options=lock["runtime"]["realized_network_options"]
container_expected={"com.docker.compose.project":project,"dssc.semantic-treehouse.project":project,"dssc.semantic-treehouse.upstream-commit":commit,"dssc.semantic-treehouse.runtime-contract":"v1"}
network_expected={"com.docker.compose.project":project,"dssc.semantic-treehouse.project":project,"dssc.semantic-treehouse.upstream-commit":commit,"dssc.semantic-treehouse.runtime-contract":"v1"}
allowed_containers={project+"-sth",project+"-sth-db2"};allowed_networks={network_name,ingress_name};allowed_volumes={app_volume,db_volume}
payload={"containers":[],"networks":[],"volumes":[]}
def run_json(command):
 p=subprocess.run(command,text=True,capture_output=True,timeout=30)
 if p.returncode:raise SystemExit(1)
 return json.loads(p.stdout)
for line in pathlib.Path(containers).read_text(encoding="utf-8").splitlines():
  if not line.strip():continue
  item=json.loads(line);ident=item.get("ID") or item.get("Id");name=item.get("Names") or item.get("Name")
  if name not in allowed_containers:raise SystemExit(1)
  labels=run_json(["docker","inspect","--format","{{json .Config.Labels}}",ident]) or {}
  if any(str(labels.get(k))!=v for k,v in container_expected.items()):raise SystemExit(1)
  dssc_keys={str(k) for k in labels if str(k).lower().startswith("dssc.semantic-treehouse.")}
  allowed_dssc={"dssc.semantic-treehouse.project","dssc.semantic-treehouse.upstream-commit","dssc.semantic-treehouse.runtime-contract","dssc.semantic-treehouse.managed"}
  if not dssc_keys.issubset(allowed_dssc):raise SystemExit(1)
  if "dssc.semantic-treehouse.managed" in labels and labels.get("dssc.semantic-treehouse.managed")!="true":raise SystemExit(1)
  service="sth" if name==project+"-sth" else "sth-db2"
  if labels.get("com.docker.compose.service")!=service:raise SystemExit(1)
  attached=run_json(["docker","inspect","--format","{{json .NetworkSettings.Networks}}",ident]) or {}
  expected_attached={network_name,ingress_name} if service=="sth" else {network_name}
  if set(attached)!=expected_attached:raise SystemExit(1)
  ports=run_json(["docker","inspect","--format","{{json .NetworkSettings.Ports}}",ident]) or {}
  requested=run_json(["docker","inspect","--format","{{json .HostConfig.PortBindings}}",ident]) or {}
  if service=="sth":
    if set(ports)!={"80/tcp"} or set(requested)!={"80/tcp"}:raise SystemExit(1)
    realized=ports["80/tcp"] or [];wanted=requested["80/tcp"] or []
    if len(realized)!=1 or len(wanted)!=1:raise SystemExit(1)
    if any(str(binding.get("HostIp"))!="127.0.0.1" for binding in (realized[0],wanted[0])):raise SystemExit(1)
    binding={"realized":realized[0],"requested":wanted[0]}
  else:
    if sum(len(v or []) for v in ports.values()) or sum(len(v or []) for v in requested.values()):raise SystemExit(1)
    binding=None
  payload["containers"].append({"id":ident,"name":name,"service":service,"networks":sorted(expected_attached),"port_binding":binding,"labels_verified":True})
if len({x["name"] for x in payload["containers"]})!=len(payload["containers"]):raise SystemExit(1)
direct=set()
for name in allowed_containers:
 p=subprocess.run(["docker","container","inspect","--format","{{.Id}}",name],text=True,capture_output=True,timeout=30)
 if p.returncode==0:direct.add(name)
if direct!={x["name"] for x in payload["containers"]}:raise SystemExit(1)
for line in pathlib.Path(networks).read_text(encoding="utf-8").splitlines():
  if not line.strip():continue
  item=json.loads(line);ident=item.get("ID") or item.get("Id");name=item.get("Name")
  if name not in allowed_networks:raise SystemExit(1)
  expected_internal,role=(True,"internal") if name==network_name else (False,"ingress")
  labels=run_json(["docker","network","inspect","--format","{{json .Labels}}",ident]) or {}
  internal=run_json(["docker","network","inspect","--format","{{json .Internal}}",ident])
  driver=run_json(["docker","network","inspect","--format","{{json .Driver}}",ident])
  options=run_json(["docker","network","inspect","--format","{{json .Options}}",ident])
  expected_labels=dict(network_expected);expected_labels["dssc.semantic-treehouse.network-role"]=role
  if any(str(labels.get(k))!=v for k,v in expected_labels.items()):raise SystemExit(1)
  if internal is not expected_internal or driver!="bridge" or not isinstance(options,dict) or options!=expected_options:raise SystemExit(1)
  payload["networks"].append({"id":ident,"name":name,"role":role,"internal":internal,"driver":driver,"options":options,"labels_verified":True})
if len({x["name"] for x in payload["networks"]})!=len(payload["networks"]):raise SystemExit(1)
direct=set()
for name in allowed_networks:
 p=subprocess.run(["docker","network","inspect","--format","{{.Id}}",name],text=True,capture_output=True,timeout=30)
 if p.returncode==0:direct.add(name)
if direct!={x["name"] for x in payload["networks"]}:raise SystemExit(1)
listed=[]
for line in pathlib.Path(volumes).read_text(encoding="utf-8").splitlines():
  if not line.strip():continue
  item=json.loads(line);name=item.get("Name") or item.get("Names")
  if name not in allowed_volumes or name in listed:raise SystemExit(1)
  listed.append(name)
for logical,name in (("sth-app-data",app_volume),("sth-db2-data",db_volume)):
  p=subprocess.run(["docker","volume","inspect","--format","{{json .Labels}}",name],text=True,capture_output=True,timeout=30)
  if p.returncode:continue
  labels=json.loads(p.stdout) or {};expected={"com.docker.compose.project":project,"com.docker.compose.volume":logical,"dssc.semantic-treehouse.managed":"true","dssc.semantic-treehouse.project":project,"dssc.semantic-treehouse.upstream-commit":commit,"dssc.semantic-treehouse.logical-volume":logical,"dssc.semantic-treehouse.runtime-contract":"v1"}
  if set(labels)!=set(expected) or any(str(labels.get(k))!=v for k,v in expected.items()):raise SystemExit(1)
  encoded=json.dumps(labels,sort_keys=True,separators=(",",":"))
  payload["volumes"].append({"name":name,"logical_name":logical,"labels_verified":True,"labels_sha256":hashlib.sha256(encoded.encode()).hexdigest()})
if set(listed)!={x["name"] for x in payload["volumes"]}:raise SystemExit(1)
pathlib.Path(out).write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8",newline="\n")
PY
  rm -f -- "$containers" "$networks" "$volumes"
}

finalize() {
  code=$?
  set +e
  "$PYTHON" -I - "$RAW_LOG" "$CLEAN_LOG" "$ROOT_DIR" "$ENV_FILE" <<'PY'
import pathlib,re,sys
raw,clean,root,env=map(pathlib.Path,sys.argv[1:]);text=raw.read_text(encoding="utf-8",errors="replace") if raw.is_file() else ""
vals=[]
if env.is_file():
  for line in env.read_text(encoding="utf-8",errors="replace").splitlines():
    if "=" in line:
      k,v=line.split("=",1)
      if any(x in k.lower() for x in ("password","secret","api_key")) and v:vals.append(v)
for v in vals:text=text.replace(v,"<redacted>")
home=str(pathlib.Path.home());text=text.replace(str(root),"<repo>").replace(home,"<user-home>")
text=re.sub(r"(?i)(password|secret|token|credential)(\s*[=:]\s*)(\S+)",r"\1\2<redacted>",text)
if any(v and v in text for v in vals) or str(root) in text or (home and home in text): raise SystemExit(1)
clean.write_text(text.rstrip()+"\n",encoding="utf-8",newline="\n")
if raw.is_file():raw.unlink()
PY
  scrub=$?; [ "$code" -ne 0 ] || code=$scrub
  "$PYTHON" -I - "$EVIDENCE_FILE" "$LOCK_FILE" "$BEFORE_FILE" "$AFTER_FILE" "$code" "$STAGE" "$FAILURE_MESSAGE" "$DOWN_ATTEMPTED" "$DOWN_EXIT" "$ROOT_DIR" <<'PY'
import hashlib,json,os,pathlib,re,sys
out,lock_p,before_p,after_p,code,stage,error,attempted,down_exit,root=sys.argv[1:]
lock=json.load(open(lock_p,encoding="utf-8"));load=lambda p:json.load(open(p,encoding="utf-8")) if pathlib.Path(p).is_file() else None
home=os.path.expanduser("~");error=str(error or "").replace(root,"<repo>").replace(home,"<user-home>");error=re.sub(r"(?i)(password|secret|token|credential)(\s*[=:]\s*)(\S+)",r"\1\2<redacted>",error)
payload={"schema":"dssc.semantic-treehouse.runtime-down.v1","status":"PASS" if int(code)==0 else "FAILED","exit_code":int(code),"stage":stage,"project_name":lock["compose"]["project_name"],"upstream_commit":lock["upstream"]["commit"],"lock_sha256":hashlib.sha256(pathlib.Path(lock_p).read_bytes()).hexdigest(),"before":load(before_p),"after":load(after_p),"down_attempted":attempted=="true","down_exit_code":int(down_exit) if down_exit else None,"volumes_removed":False,"error":error}
pathlib.Path(out).write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8",newline="\n")
PY
  rm -f -- "$BEFORE_FILE" "$AFTER_FILE" "$STATE_HASH_FILE" "$RUNTIME_DIR/.down-containers.tmp" "$RUNTIME_DIR/.down-networks.tmp" "$RUNTIME_DIR/.down-volumes.tmp"
  trap - 0
  exit "$code"
}
trap finalize 0

STAGE=read-lock
[ -f "$LOCK_FILE" ] || { FAILURE_MESSAGE="Missing upstream lock."; exit 1; }
PROJECT_NAME=$(lock_value compose.project_name)
COMMIT=$(lock_value upstream.commit)
UPSTREAM_DIR="$ROOT_DIR/$(lock_value checkout.path)"
COMPOSE_FILE="$UPSTREAM_DIR/$(lock_value compose.path)"
APP_VOLUME=$(lock_value runtime.volume_names.sth-app-data)
DB_VOLUME=$(lock_value runtime.volume_names.sth-db2-data)
NETWORK_NAME=$(lock_value runtime.network_name)
INGRESS_NETWORK_NAME=$(lock_value runtime.ingress_network_name)
"$PYTHON" -I - "$LOCK_FILE" <<'PY' || { FAILURE_MESSAGE="Invalid locked dual-network runtime contract."; exit 1; }
import json,sys
runtime=json.load(open(sys.argv[1],encoding="utf-8"))["runtime"]
assert runtime["network_topology"]=="dual-network-app-ingress"
assert runtime["internal_network"] is True and runtime["ingress_network_internal"] is False
assert runtime["app_outbound_access"] is True and runtime["ingress_services"]==["sth"]
assert runtime["network_name"]!=runtime["ingress_network_name"]
assert runtime["realized_network_options"]=={
 "com.docker.network.enable_ipv4":"true",
 "com.docker.network.enable_ipv6":"false",
}
PY

STAGE=local-docker-boundary
"$PYTHON" -I - <<'PY' || { FAILURE_MESSAGE="Remote Docker context/daemon is forbidden."; exit 1; }
import os
keys=("APP_SECRET","DB2_DBNAME","DB2_PASSWORD","DB2_ROOT_PASSWORD","DB2_TEST_DB_PASSWORD","DB2_USER","MAILER_DSN","SERVER_HOST_NAME","STH_ENV_NAME","STH_FRONTEND_CONFIG","STH_GCS_PATH_PREFIX","STH_NOTIFICATIONS_ENABLED","STH_VALIDATOR_ENDPOINT","STH_JSON_VALIDATOR_ENDPOINT","STH_SHACL_VALIDATOR_ENDPOINT","STH_AI_GATEWAY_ENDPOINT","STH_AI_GATEWAY_DEFAULT_MODEL_PROVIDER","STH_AI_GATEWAY_DEFAULT_MODEL","STH_AI_GATEWAY_DEFAULT_API_KEY","APP_ENV","APP_DEBUG","COMPOSE_PROJECT_NAME","COMPOSE_FILE","COMPOSE_PROFILES","COMPOSE_ENV_FILES","DOCKER_HOST","DOCKER_CONTEXT","DOCKER_TLS","DOCKER_TLS_VERIFY","DOCKER_CERT_PATH")
assert all(k not in os.environ for k in keys)
assert not any(k.startswith("COMPOSE_") for k in os.environ)
PY
set +e
CURRENT_DOCKER_CONTEXT=$(timeout --foreground 30 docker context show 2>> "$RAW_LOG"); CONTEXT_SHOW_CODE=$?
CONTEXT_HOST=$(timeout --foreground 30 docker context inspect --format '{{json .Endpoints.docker.Host}}' "$CURRENT_DOCKER_CONTEXT" 2>> "$RAW_LOG"); CONTEXT_CODE=$?
SERVER_PLATFORM=$(timeout --foreground 30 docker info --format '{{.OSType}}|{{.Architecture}}' 2>> "$RAW_LOG"); SERVER_CODE=$?
set -e
[ "$CONTEXT_SHOW_CODE" -eq 0 ] && [ "$CONTEXT_CODE" -eq 0 ] && [ "$SERVER_CODE" -eq 0 ] || { FAILURE_MESSAGE="Docker context/server inspection failed."; exit 1; }
"$PYTHON" -I - "$CURRENT_DOCKER_CONTEXT" "$CONTEXT_HOST" "$SERVER_PLATFORM" <<'PY' || { FAILURE_MESSAGE="Docker must use a named local-socket context and a linux/amd64 server."; exit 1; }
import json,sys
assert sys.argv[1] and not any(ord(char)<32 for char in sys.argv[1])
assert json.loads(sys.argv[2]).startswith(("unix://","npipe://"))
assert sys.argv[3] in {"linux|amd64","linux|x86_64"}
PY

capture_boundary "$BEFORE_FILE"
RESOURCE_STATE=$("$PYTHON" -I -c 'import json,sys
d=json.load(open(sys.argv[1]));project,internal,ingress,app_volume,db_volume=sys.argv[2:]
containers={x["name"] for x in d["containers"]};networks={x["name"] for x in d["networks"]};volumes={x["name"] for x in d["volumes"]}
expected_containers={project+"-sth",project+"-sth-db2"};expected_networks={internal,ingress};expected_volumes={app_volume,db_volume}
if not containers and not networks and volumes in (set(),expected_volumes):print("ZERO")
elif containers==expected_containers and len(d["containers"])==2 and networks==expected_networks and len(d["networks"])==2 and volumes==expected_volumes and len(d["volumes"])==2:print("ACTIVE")
else:print("PARTIAL")' "$BEFORE_FILE" "$PROJECT_NAME" "$NETWORK_NAME" "$INGRESS_NETWORK_NAME" "$APP_VOLUME" "$DB_VOLUME")
if [ "$RESOURCE_STATE" = ZERO ]; then
  STAGE=zero-runtime-context-state-guard
  "$PYTHON" -I - "$STATE_FILE" "$BOUNDARY_FILE" "$CURRENT_DOCKER_CONTEXT" <<'PY' || { FAILURE_MESSAGE="A retained successful runtime state belongs to a different or unverifiable Docker context."; exit 1; }
import hashlib,json,pathlib,sys
state_p,boundary_p,current_context=sys.argv[1:]
state_path=pathlib.Path(state_p)
if not state_path.is_file() or state_path.is_symlink():raise SystemExit(0)
try:state=json.load(open(state_path,encoding="utf-8"))
except Exception:raise SystemExit(0)
if not isinstance(state,dict) or state.get("success_state") is not True:raise SystemExit(0)
boundary_path=pathlib.Path(boundary_p)
assert boundary_path.is_file() and not boundary_path.is_symlink()
boundary=json.load(open(boundary_path,encoding="utf-8"));docker_boundary=boundary.get("docker") if isinstance(boundary.get("docker"),dict) else {}
assert boundary.get("schema")=="dssc.semantic-treehouse.runtime-boundary.v1" and boundary.get("status")=="PASS"
assert state.get("runtime_boundary_sha256")==hashlib.sha256(boundary_path.read_bytes()).hexdigest()
assert docker_boundary.get("context")==current_context
PY
  STAGE=no-op-zero-project-runtime
  cp "$BEFORE_FILE" "$AFTER_FILE"
  exit 0
fi
[ "$RESOURCE_STATE" = ACTIVE ] || { FAILURE_MESSAGE="Project runtime is partial or differs from the exact dual-network resource set."; exit 1; }

STAGE=validate-runtime-state
for path in "$STATE_FILE" "$ENV_FILE" "$OVERLAY_FILE" "$COMPOSE_FILE" "$BOUNDARY_FILE" "$NETWORK_OPTIONS_EVIDENCE_FILE"; do
  [ -f "$path" ] && [ ! -L "$path" ] || { FAILURE_MESSAGE="Required controlled runtime file is missing or a symlink."; exit 1; }
done
"$PYTHON" -I - "$STATE_FILE" "$LOCK_FILE" "$OVERLAY_FILE" "$ENV_FILE" "$COMPOSE_FILE" "$BOUNDARY_FILE" "$NETWORK_OPTIONS_EVIDENCE_FILE" "$CURRENT_DOCKER_CONTEXT" "$CONTEXT_HOST" "$SERVER_PLATFORM" "$BEFORE_FILE" "$STATE_HASH_FILE" <<'PY' || { FAILURE_MESSAGE="Runtime state or controlled runtime hashes do not match."; exit 1; }
import hashlib,json,pathlib,sys
state_p,lock_p,overlay_p,env_p,compose_p,boundary_p,options_evidence_p,current_context,current_host_json,current_platform,before_p,state_hash_p=sys.argv[1:]
state=json.load(open(state_p,encoding="utf-8"));lock=json.load(open(lock_p,encoding="utf-8"));runtime=lock["runtime"]
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert state["schema"]=="dssc.semantic-treehouse.runtime-state.v1"
for key in ("deployment","first_migration","production_migration","smoke","root_smoke","api_smoke"):assert state.get(key)=="PASS"
assert state.get("success_state") is True
assert state["project_name"]==lock["compose"]["project_name"] and state["upstream_commit"]==lock["upstream"]["commit"]
assert state["lock_sha256"]==sha(lock_p) and state["overlay_sha256"]==sha(overlay_p)
assert state["runtime_boundary_sha256"]==sha(boundary_p)
assert state["synthetic_env_sha256"]==sha(env_p) and state["compose_sha256"]==sha(compose_p)
assert state["compose_sha256"]==lock["source_materialization"]["sha256"][lock["compose"]["path"]]
assert state.get("network_topology")=="dual-network-app-ingress"
assert state.get("internal_network")==runtime["network_name"] and state.get("ingress_network")==runtime["ingress_network_name"]
assert state.get("application_outbound_access") is True and state.get("bind_address")=="127.0.0.1"
assert isinstance(state.get("http_port"),int) and not isinstance(state.get("http_port"),bool) and 1024<=state["http_port"]<=65535
assert sorted(state.get("volumes",[]))==sorted(runtime["volume_names"].values())
ingress=state.get("realized_ingress");assert isinstance(ingress,dict)
rows=ingress.get("networks");assert isinstance(rows,list)
network_specs={runtime["network_name"]:("internal",True),runtime["ingress_network_name"]:("ingress",False)}
assert len(rows)==2 and {row.get("name") for row in rows if isinstance(row,dict)}==set(network_specs)
for row in rows:
 assert isinstance(row,dict) and row.get("name") in network_specs
 role,internal=network_specs[row["name"]]
 assert row.get("role")==role and row.get("internal") is internal and row.get("driver")=="bridge"
 assert row.get("options_match") is True and isinstance(row.get("options"),dict) and row.get("options")==runtime["realized_network_options"]
assert ingress.get("status")=="PASS" and ingress.get("binding")==f"127.0.0.1:{state['http_port']}:80"
assert ingress.get("network_settings_ports_programmed") is True and ingress.get("host_config_binding_matches") is True
assert sorted(ingress.get("application_networks",[]))==sorted(network_specs) and ingress.get("database_networks")==[runtime["network_name"]]
assert isinstance(ingress.get("database_published_ports"),int) and not isinstance(ingress.get("database_published_ports"),bool) and ingress.get("database_published_ports")==0
assert ingress.get("application_outbound_access") is True
assert ingress.get("realized_network_options_evidence_sha256")==sha(options_evidence_p)
before=json.load(open(before_p,encoding="utf-8"));app=next(x for x in before["containers"] if x["service"]=="sth")
for binding in (app["port_binding"]["realized"],app["port_binding"]["requested"]):
 assert str(binding.get("HostIp"))=="127.0.0.1" and str(binding.get("HostPort"))==str(state["http_port"])
boundary=json.load(open(boundary_p,encoding="utf-8"));assert boundary.get("schema")=="dssc.semantic-treehouse.runtime-boundary.v1" and boundary.get("status")=="PASS" and boundary.get("prepare_only") is False
assert boundary.get("upstream_commit")==lock["upstream"]["commit"] and boundary.get("lock_sha256")==sha(lock_p)
assert boundary.get("compose_sha256")==sha(compose_p) and boundary.get("overlay_sha256")==sha(overlay_p) and boundary.get("synthetic_env_sha256")==sha(env_p)
docker_boundary=boundary.get("docker");assert isinstance(docker_boundary,dict)
current_host=json.loads(current_host_json);server_os,server_arch=current_platform.split("|",1)
if server_arch=="x86_64":server_arch="amd64"
assert docker_boundary.get("context")==current_context and docker_boundary.get("endpoint_scheme")==current_host.split(":",1)[0]
assert docker_boundary.get("server_os")==server_os and docker_boundary.get("server_architecture")==server_arch and docker_boundary.get("remote_daemon") is False
contract=boundary.get("boundary") or {}
assert contract.get("network_topology")=="dual-network-app-ingress"
assert contract.get("configured_driver_options")=={} and contract.get("expected_realized_network_options")==runtime["realized_network_options"]
assert sorted(contract.get("application_networks",[]))==sorted((runtime["network_name"],runtime["ingress_network_name"]))
assert contract.get("database_networks")==[runtime["network_name"]] and sorted(contract.get("volumes",[]))==sorted(runtime["volume_names"].values())
assert contract.get("internal_network")==runtime["network_name"] and contract.get("ingress_network")==runtime["ingress_network_name"] and contract.get("app_outbound_access") is True
assert contract.get("http_binding")==f"127.0.0.1:{state['http_port']}:80"
pathlib.Path(state_hash_p).write_text(sha(state_p)+"\n",encoding="ascii",newline="\n")
PY

STAGE=compose-down
DOWN_ATTEMPTED=true
set +e
DB2_TEST_DB_PASSWORD=placeholder timeout --foreground 180 docker compose --project-name "$PROJECT_NAME" --project-directory "$UPSTREAM_DIR" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -f "$OVERLAY_FILE" down >> "$RAW_LOG" 2>&1
DOWN_EXIT=$?
set -e
[ "$DOWN_EXIT" -eq 0 ] || { FAILURE_MESSAGE="Compose down failed with exit code $DOWN_EXIT"; exit "$DOWN_EXIT"; }

STAGE=post-down-verification
capture_boundary "$AFTER_FILE"
"$PYTHON" -I - "$BEFORE_FILE" "$AFTER_FILE" "$STATE_FILE" "$STATE_HASH_FILE" "$APP_VOLUME" "$DB_VOLUME" <<'PY' || { FAILURE_MESSAGE="Post-down exact resource verification failed."; exit 1; }
import hashlib,json,pathlib,sys
before,after,state_p,state_hash_p,app_volume,db_volume=sys.argv[1:]
b=json.load(open(before,encoding="utf-8"));a=json.load(open(after,encoding="utf-8"))
assert not a["containers"] and not a["networks"]
assert {x["name"] for x in a["volumes"]}=={app_volume,db_volume}
before_volumes={x["name"]:(x["logical_name"],x["labels_sha256"]) for x in b["volumes"]}
after_volumes={x["name"]:(x["logical_name"],x["labels_sha256"]) for x in a["volumes"]}
assert after_volumes==before_volumes
expected=pathlib.Path(state_hash_p).read_text(encoding="ascii").strip()
assert hashlib.sha256(pathlib.Path(state_p).read_bytes()).hexdigest()==expected
PY
echo "Semantic Treehouse project stopped; external volumes preserved."
exit 0
