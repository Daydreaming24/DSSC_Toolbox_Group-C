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
RAW_LOG="$RUNTIME_DIR/status.raw.log"
CLEAN_LOG="$EVIDENCE_DIR/treehouse-status.log"
EVIDENCE_FILE="$EVIDENCE_DIR/runtime-status.json"
NETWORK_OPTIONS_EVIDENCE_FILE="$EVIDENCE_DIR/runtime-network-options.json"
CONTAINERS_FILE="$RUNTIME_DIR/.status-containers.jsonl"
NETWORKS_FILE="$RUNTIME_DIR/.status-networks.jsonl"
VOLUMES_FILE="$RUNTIME_DIR/.status-volumes.json"
PROJECT_VOLUMES_FILE="$RUNTIME_DIR/.status-project-volumes.jsonl"
STATE_PROJECTION_FILE="$RUNTIME_DIR/.status-state-projection.json"
ROOT_SMOKE_HEADER_FILE="$RUNTIME_DIR/.status-root-smoke-headers.tmp"
API_SMOKE_HEADER_FILE="$RUNTIME_DIR/.status-api-smoke-headers.tmp"
STAGE=initialize
FAILURE_MESSAGE=""
FINALIZED=false
PROJECTION_READY=false
RUNTIME_STATUS=UNKNOWN
HTTP_STATUS=NOT_RUN
ROOT_HTTP_STATUS=NOT_RUN
API_HTTP_STATUS=NOT_RUN

[ -x "$PYTHON" ] || { echo "Repository .venv Python is required: .venv/bin/python" >&2; exit 1; }
command -v timeout >/dev/null 2>&1 || { echo "GNU timeout is required for bounded Docker operations." >&2; exit 1; }
mkdir -p "$RUNTIME_DIR" "$EVIDENCE_DIR"
rm -f -- "$CONTAINERS_FILE" "$NETWORKS_FILE" "$VOLUMES_FILE" "$PROJECT_VOLUMES_FILE" "$STATE_PROJECTION_FILE" "$ROOT_SMOKE_HEADER_FILE" "$API_SMOKE_HEADER_FILE"
: > "$RAW_LOG"
: > "$CONTAINERS_FILE"
: > "$NETWORKS_FILE"
: > "$PROJECT_VOLUMES_FILE"

lock_value() {
  "$PYTHON" -I -c 'import json,sys
v=json.load(open(sys.argv[1],encoding="utf-8"))
for p in sys.argv[2].split("."): v=v[p]
print(v)' "$LOCK_FILE" "$1"
}

docker_capture() {
  outfile=$1
  shift
  printf '[%s] docker' "$STAGE" >> "$RAW_LOG"
  for arg in "$@"; do printf ' %s' "$arg" >> "$RAW_LOG"; done
  printf '\n' >> "$RAW_LOG"
  set +e
  timeout --foreground 120 docker "$@" > "$outfile" 2>> "$RAW_LOG"
  code=$?
  set -e
  printf '[%s] exit=%s\n' "$STAGE" "$code" >> "$RAW_LOG"
  if [ "$code" -ne 0 ]; then FAILURE_MESSAGE="Docker status query failed at $STAGE with exit code $code"; exit "$code"; fi
}

finalize() {
  code=$?
  set +e
  if [ -f "$RAW_LOG" ]; then
  "$PYTHON" -I - "$RAW_LOG" "$CLEAN_LOG" "$ROOT_DIR" "$ENV_FILE" <<'PY'
import os, pathlib, re, sys
raw, clean, root, env = map(pathlib.Path, sys.argv[1:])
text = raw.read_text(encoding="utf-8", errors="replace") if raw.is_file() else ""
values=[]
if env.is_file():
  for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
    if "=" in line:
      key,value=line.split("=",1)
      if any(x in key.lower() for x in ("password","secret","api_key")) and value: values.append(value)
for value in values: text=text.replace(value,"<redacted>")
text=text.replace(str(root),"<repo>")
home=str(pathlib.Path.home())
if home: text=text.replace(home,"<user-home>")
text=re.sub(r"(?i)(authorization|bearer|password|passwd|token|secret|api[_-]?key|credential)(\s*[=:]\s*)(\S+)",r"\1\2<redacted>",text)
if any(value in text for value in values if value) or str(root) in text or (home and home in text): raise SystemExit(1)
clean.write_text(text.rstrip()+"\n",encoding="utf-8",newline="\n")
if raw.is_file(): raw.unlink()
PY
  scrub_code=$?
  else
    scrub_code=0
  fi
  [ "$code" -ne 0 ] || code=$scrub_code
  if [ "$FINALIZED" = false ]; then
    "$PYTHON" -I - "$EVIDENCE_FILE" "$LOCK_FILE" "$STATE_PROJECTION_FILE" "$CONTAINERS_FILE" "$NETWORKS_FILE" "$VOLUMES_FILE" "$ROOT_DIR" "$code" "$STAGE" "$FAILURE_MESSAGE" "$PROJECTION_READY" <<'PY'
import hashlib,json,os,pathlib,re,sys
out,lock_p,state_p,containers_p,networks_p,volumes_p,root,code,stage,error,ready=sys.argv[1:]
lock=json.load(open(lock_p,encoding="utf-8")); state=json.load(open(state_p,encoding="utf-8")) if ready=="true" and pathlib.Path(state_p).is_file() else None
def lines(path):
  return [json.loads(x) for x in pathlib.Path(path).read_text(encoding="utf-8",errors="replace").splitlines() if x.strip()]
containers_out=lines(containers_p) if ready=="true" else []
networks_out=lines(networks_p) if ready=="true" else []
volumes=json.load(open(volumes_p,encoding="utf-8")) if ready=="true" and pathlib.Path(volumes_p).is_file() else {}
home=os.path.expanduser("~")
error=str(error or "").replace(root,"<repo>").replace(home,"<user-home>")
error=re.sub(r"(?i)(password|secret|token|credential)(\s*[=:]\s*)(\S+)",r"\1\2<redacted>",error)
payload={"schema":"dssc.semantic-treehouse.runtime-status.v1","status":"PASS" if int(code)==0 else "FAILED","exit_code":int(code),"stage":stage,
"project_name":lock["compose"]["project_name"],"upstream_commit":lock["upstream"]["commit"],"lock_sha256":hashlib.sha256(pathlib.Path(lock_p).read_bytes()).hexdigest(),
"runtime_state":state,"containers":containers_out,"networks":networks_out,"volumes":volumes,"config_env_inspected":False,"error":error}
pathlib.Path(out).write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8",newline="\n")
PY
  fi
  rm -f -- "$CONTAINERS_FILE" "$NETWORKS_FILE" "$VOLUMES_FILE" "$PROJECT_VOLUMES_FILE" "$STATE_PROJECTION_FILE" "$ROOT_SMOKE_HEADER_FILE" "$API_SMOKE_HEADER_FILE"
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
NETWORK_NAME=$(lock_value runtime.network_name)
INGRESS_NETWORK_NAME=$(lock_value runtime.ingress_network_name)
APP_VOLUME=$(lock_value runtime.volume_names.sth-app-data)
DB_VOLUME=$(lock_value runtime.volume_names.sth-db2-data)
"$PYTHON" -I - "$LOCK_FILE" <<'PY' || { FAILURE_MESSAGE="Invalid locked dual-network runtime contract."; exit 1; }
import json,sys
lock=json.load(open(sys.argv[1],encoding="utf-8"));runtime=lock["runtime"]
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
for key in ("DOCKER_HOST","DOCKER_CONTEXT","DOCKER_TLS","DOCKER_TLS_VERIFY","DOCKER_CERT_PATH"):
  assert key not in os.environ
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

STAGE=filtered-container-query
docker_capture "$CONTAINERS_FILE" ps -a --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{json .}}'
STAGE=filtered-network-query
docker_capture "$NETWORKS_FILE" network ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{json .}}'
STAGE=filtered-volume-query
docker_capture "$PROJECT_VOLUMES_FILE" volume ls --filter "label=com.docker.compose.project=$PROJECT_NAME" --format '{{json .}}'

STAGE=label-verification
"$PYTHON" -I - "$CONTAINERS_FILE" "$NETWORKS_FILE" "$LOCK_FILE" "$PROJECT_NAME" "$COMMIT" "$NETWORK_NAME" "$INGRESS_NETWORK_NAME" "$APP_VOLUME" "$DB_VOLUME" <<'PY' || { FAILURE_MESSAGE="Project resource label verification failed."; exit 1; }
import json,pathlib,subprocess,sys
containers,networks,lock_p,project,commit,network_name,ingress_name,app_volume,db_volume=sys.argv[1:]
lock=json.load(open(lock_p,encoding="utf-8"));expected_options=lock["runtime"]["realized_network_options"]
container_expected={"com.docker.compose.project":project,"dssc.semantic-treehouse.project":project,"dssc.semantic-treehouse.upstream-commit":commit,"dssc.semantic-treehouse.runtime-contract":"v1"}
allowed={project+"-sth",project+"-sth-db2"}; projected=[]
for line in pathlib.Path(containers).read_text(encoding="utf-8").splitlines():
  if not line.strip(): continue
  item=json.loads(line); ident=item.get("ID") or item.get("Id"); name=item.get("Names") or item.get("Name")
  if name not in allowed: raise SystemExit(1)
  lp=subprocess.run(["docker","inspect","--format","{{json .Config.Labels}}",ident],text=True,capture_output=True,timeout=30)
  sp=subprocess.run(["docker","inspect","--format","{{json .State}}",ident],text=True,capture_output=True,timeout=30)
  np=subprocess.run(["docker","inspect","--format","{{json .NetworkSettings.Networks}}",ident],text=True,capture_output=True,timeout=30)
  mp=subprocess.run(["docker","inspect","--format","{{json .Mounts}}",ident],text=True,capture_output=True,timeout=30)
  pp=subprocess.run(["docker","inspect","--format","{{json .NetworkSettings.Ports}}",ident],text=True,capture_output=True,timeout=30)
  hp=subprocess.run(["docker","inspect","--format","{{json .HostConfig.PortBindings}}",ident],text=True,capture_output=True,timeout=30)
  if lp.returncode or sp.returncode or np.returncode or mp.returncode or pp.returncode or hp.returncode: raise SystemExit(1)
  labels=json.loads(lp.stdout) or {}; state=json.loads(sp.stdout) or {}; attached=json.loads(np.stdout) or {}; mounts=json.loads(mp.stdout) or []
  ports=json.loads(pp.stdout) or {}; requested=json.loads(hp.stdout) or {}
  if any(str(labels.get(k))!=v for k,v in container_expected.items()): raise SystemExit(1)
  dssc_keys={str(k) for k in labels if str(k).lower().startswith("dssc.semantic-treehouse.")}
  allowed_dssc={"dssc.semantic-treehouse.project","dssc.semantic-treehouse.upstream-commit","dssc.semantic-treehouse.runtime-contract","dssc.semantic-treehouse.managed"}
  if not dssc_keys.issubset(allowed_dssc): raise SystemExit(1)
  if "dssc.semantic-treehouse.managed" in labels and labels.get("dssc.semantic-treehouse.managed")!="true": raise SystemExit(1)
  expected_service="sth" if name==project+"-sth" else "sth-db2"
  if labels.get("com.docker.compose.service")!=expected_service: raise SystemExit(1)
  expected_networks={network_name,ingress_name} if expected_service=="sth" else {network_name}
  if set(attached)!=expected_networks: raise SystemExit(1)
  expected_mount=(app_volume,"/var/www/data") if expected_service=="sth" else (db_volume,"/var/lib/mysql")
  if len(mounts)!=1 or mounts[0].get("Type")!="volume" or (mounts[0].get("Name"),mounts[0].get("Destination"))!=expected_mount or mounts[0].get("RW") is not True: raise SystemExit(1)
  if expected_service=="sth":
    if set(ports)!={"80/tcp"} or set(requested)!={"80/tcp"}: raise SystemExit(1)
    realized=ports["80/tcp"] or []; wanted=requested["80/tcp"] or []
    if len(realized)!=1 or len(wanted)!=1: raise SystemExit(1)
    port_projection={"realized":realized[0],"requested":wanted[0]}
  else:
    if sum(len(v or []) for v in ports.values()) or sum(len(v or []) for v in requested.values()): raise SystemExit(1)
    port_projection=None
  projected.append({"id":ident,"name":name,"service":labels.get("com.docker.compose.service"),"running":state.get("Running") is True,"status":state.get("Status"),"health":(state.get("Health") or {}).get("Status"),"networks":sorted(expected_networks),"port_binding":port_projection,"mount":{"name":expected_mount[0],"destination":expected_mount[1],"rw":True},"labels_verified":True,"config_env_inspected":False})
if len({x["name"] for x in projected}) != len(projected): raise SystemExit(1)
direct_containers=set()
for expected_name in allowed:
  probe=subprocess.run(["docker","container","inspect","--format","{{.Id}}",expected_name],text=True,capture_output=True,timeout=30)
  if probe.returncode==0:direct_containers.add(expected_name)
if direct_containers!={x["name"] for x in projected}:raise SystemExit(1)
pathlib.Path(containers).write_text("".join(json.dumps(x)+"\n" for x in projected),encoding="utf-8",newline="\n")
network_expected={"com.docker.compose.project":project,"dssc.semantic-treehouse.project":project,"dssc.semantic-treehouse.upstream-commit":commit,"dssc.semantic-treehouse.runtime-contract":"v1"}; nproj=[]
for line in pathlib.Path(networks).read_text(encoding="utf-8").splitlines():
  if not line.strip(): continue
  item=json.loads(line); ident=item.get("ID") or item.get("Id"); name=item.get("Name")
  if name not in {network_name,ingress_name}: raise SystemExit(1)
  expected_internal,role=(True,"internal") if name==network_name else (False,"ingress")
  p=subprocess.run(["docker","network","inspect","--format","{{json .Labels}}",ident],text=True,capture_output=True,timeout=30)
  ip=subprocess.run(["docker","network","inspect","--format","{{json .Internal}}",ident],text=True,capture_output=True,timeout=30)
  dp=subprocess.run(["docker","network","inspect","--format","{{json .Driver}}",ident],text=True,capture_output=True,timeout=30)
  op=subprocess.run(["docker","network","inspect","--format","{{json .Options}}",ident],text=True,capture_output=True,timeout=30)
  if p.returncode or ip.returncode or dp.returncode or op.returncode: raise SystemExit(1)
  labels=json.loads(p.stdout) or {}; internal=json.loads(ip.stdout); driver=json.loads(dp.stdout); options=json.loads(op.stdout)
  expected_labels=dict(network_expected);expected_labels["dssc.semantic-treehouse.network-role"]=role
  if any(str(labels.get(k))!=v for k,v in expected_labels.items()): raise SystemExit(1)
  if internal is not expected_internal or driver!="bridge" or not isinstance(options,dict) or options!=expected_options: raise SystemExit(1)
  nproj.append({"id":ident,"name":name,"role":role,"internal":internal,"driver":driver,"options":options,"labels_verified":True})
if len({x["name"] for x in nproj})!=len(nproj) or len(nproj)>2: raise SystemExit(1)
direct_networks=set()
for expected_name in (network_name,ingress_name):
  probe=subprocess.run(["docker","network","inspect","--format","{{.Id}}",expected_name],text=True,capture_output=True,timeout=30)
  if probe.returncode==0:direct_networks.add(expected_name)
if direct_networks!={x["name"] for x in nproj}:raise SystemExit(1)
pathlib.Path(networks).write_text("".join(json.dumps(x)+"\n" for x in nproj),encoding="utf-8",newline="\n")
PY

STAGE=runtime-state-validation
if [ -e "$STATE_FILE" ]; then
  [ -f "$STATE_FILE" ] && [ ! -L "$STATE_FILE" ] || { FAILURE_MESSAGE="Runtime state must be a regular non-symlink file."; exit 1; }
  "$PYTHON" -I - "$STATE_FILE" "$STATE_PROJECTION_FILE" "$LOCK_FILE" "$ENV_FILE" "$OVERLAY_FILE" "$COMPOSE_FILE" "$BOUNDARY_FILE" "$NETWORK_OPTIONS_EVIDENCE_FILE" "$CURRENT_DOCKER_CONTEXT" "$CONTEXT_HOST" "$SERVER_PLATFORM" <<'PY'
import hashlib,json,pathlib,sys
(state_p,out_p,lock_p,env_p,overlay_p,compose_p,boundary_p,options_evidence_p,
 current_context,current_host_json,current_platform)=sys.argv[1:]
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write_projection(payload):
 pathlib.Path(out_p).write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8",newline="\n")
try:
 state=json.load(open(state_p,encoding="utf-8"))
except Exception:
 write_projection({"schema":"dssc.semantic-treehouse.runtime-state.v1","validated":False,"parseable":False,"success_state_context_required":False,"docker_context_match":None,"state_sha256":sha(state_p)})
 raise SystemExit(0)
success_context_required=isinstance(state,dict) and state.get("success_state") is True
projection={"schema":"dssc.semantic-treehouse.runtime-state.v1","validated":False,"parseable":True,"success_state_context_required":success_context_required,"docker_context_match":False if success_context_required else None,"state_sha256":sha(state_p)}
try:
 lock=json.load(open(lock_p,encoding="utf-8"));runtime=lock["runtime"]
 controlled=all(pathlib.Path(p).is_file() and not pathlib.Path(p).is_symlink() for p in (env_p,overlay_p,compose_p,boundary_p,options_evidence_p))
 boundary=json.load(open(boundary_p,encoding="utf-8")) if pathlib.Path(boundary_p).is_file() and not pathlib.Path(boundary_p).is_symlink() else {}
 docker_boundary=boundary.get("docker") if isinstance(boundary.get("docker"),dict) else {}
 current_host=json.loads(current_host_json);server_os,server_arch=current_platform.split("|",1)
 if server_arch=="x86_64":server_arch="amd64"
 context_match=(
  state.get("runtime_boundary_sha256")==sha(boundary_p)
  and docker_boundary.get("context")==current_context
 ) if pathlib.Path(boundary_p).is_file() and not pathlib.Path(boundary_p).is_symlink() else False
 projection["docker_context_match"]=context_match if success_context_required else None
 boundary_valid=(
   boundary.get("schema")=="dssc.semantic-treehouse.runtime-boundary.v1" and boundary.get("status")=="PASS" and boundary.get("prepare_only") is False
  and boundary.get("project_name")==lock["compose"]["project_name"] and boundary.get("upstream_commit")==lock["upstream"]["commit"]
  and boundary.get("lock_sha256")==sha(lock_p) and boundary.get("synthetic_env_sha256")==sha(env_p)
  and boundary.get("overlay_sha256")==sha(overlay_p) and boundary.get("compose_sha256")==sha(compose_p)
  and docker_boundary.get("context")==current_context and docker_boundary.get("endpoint_scheme")==current_host.split(":",1)[0]
   and docker_boundary.get("server_os")==server_os and docker_boundary.get("server_architecture")==server_arch and docker_boundary.get("remote_daemon") is False
   and isinstance(boundary.get("boundary"),dict)
   and boundary["boundary"].get("network_topology")=="dual-network-app-ingress"
   and boundary["boundary"].get("configured_driver_options")=={}
   and boundary["boundary"].get("expected_realized_network_options")==runtime["realized_network_options"]
 )
 expected_volumes=sorted(runtime["volume_names"].values())
 status_fields=("deployment","first_migration","production_migration","smoke","root_smoke","api_smoke")
 ingress=state.get("realized_ingress") if isinstance(state.get("realized_ingress"),dict) else {}
 rows=ingress.get("networks") if isinstance(ingress.get("networks"),list) else []
 network_specs={runtime["network_name"]:("internal",True),runtime["ingress_network_name"]:("ingress",False)}
 network_rows_valid=(
  len(rows)==2 and {row.get("name") for row in rows if isinstance(row,dict)}==set(network_specs)
  and all(isinstance(row,dict) and row.get("name") in network_specs
   and row.get("role")==network_specs[row["name"]][0] and row.get("internal") is network_specs[row["name"]][1]
   and row.get("driver")=="bridge" and row.get("options_match") is True
   and isinstance(row.get("options"),dict) and row.get("options")==runtime["realized_network_options"] for row in rows)
 )
 app_networks=ingress.get("application_networks") if isinstance(ingress.get("application_networks"),list) else []
 db_networks=ingress.get("database_networks") if isinstance(ingress.get("database_networks"),list) else []
 ingress_valid=(
  ingress.get("status")=="PASS" and ingress.get("binding")==f"127.0.0.1:{state.get('http_port')}:80"
  and ingress.get("network_settings_ports_programmed") is True and ingress.get("host_config_binding_matches") is True
  and sorted(app_networks)==sorted(network_specs) and db_networks==[runtime["network_name"]]
  and isinstance(ingress.get("database_published_ports"),int) and not isinstance(ingress.get("database_published_ports"),bool)
  and ingress.get("database_published_ports")==0 and ingress.get("application_outbound_access") is True and network_rows_valid
 )
 network_evidence_valid=(pathlib.Path(options_evidence_p).is_file() and not pathlib.Path(options_evidence_p).is_symlink() and ingress.get("realized_network_options_evidence_sha256")==sha(options_evidence_p))
 valid=(
  controlled and boundary_valid and state.get("schema")=="dssc.semantic-treehouse.runtime-state.v1"
  and all(state.get(key)=="PASS" for key in status_fields) and state.get("success_state") is True and context_match
  and state.get("project_name")==lock["compose"]["project_name"] and state.get("upstream_commit")==lock["upstream"]["commit"]
  and state.get("lock_sha256")==sha(lock_p) and state.get("synthetic_env_sha256")==sha(env_p)
  and state.get("runtime_boundary_sha256")==sha(boundary_p)
  and state.get("overlay_sha256")==sha(overlay_p) and state.get("compose_sha256")==sha(compose_p)
  and state.get("compose_sha256")==lock["source_materialization"]["sha256"][lock["compose"]["path"]]
  and state.get("network_topology")=="dual-network-app-ingress"
  and state.get("internal_network")==runtime["network_name"] and state.get("ingress_network")==runtime["ingress_network_name"]
  and state.get("application_outbound_access") is True and state.get("bind_address")=="127.0.0.1"
  and isinstance(state.get("http_port"),int) and not isinstance(state.get("http_port"),bool) and 1024<=state["http_port"]<=65535
  and sorted(state.get("volumes",[]))==expected_volumes and ingress_valid and network_evidence_valid
 )
 projection["validated"]=valid
 if valid:
  projection.update({"project_name":state["project_name"],"upstream_commit":state["upstream_commit"],"lock_sha256":state["lock_sha256"],"runtime_boundary_sha256":state["runtime_boundary_sha256"],"compose_sha256":state["compose_sha256"],"overlay_sha256":state["overlay_sha256"],"synthetic_env_sha256":state["synthetic_env_sha256"],"docker_context":current_context,"bind_address":"127.0.0.1","http_port":state["http_port"],"network_topology":state["network_topology"],"internal_network":state["internal_network"],"ingress_network":state["ingress_network"],"application_outbound_access":True,"realized_ingress":ingress,"volumes":expected_volumes,"deployment":"PASS","first_migration":"PASS","production_migration":"PASS","smoke":"PASS","root_smoke":"PASS","api_smoke":"PASS","success_state":True})
except Exception:
 projection["validated"]=False
write_projection(projection)
PY
else
  printf 'null\n' > "$STATE_PROJECTION_FILE"
fi
PROJECTION_READY=true

STAGE=volume-label-verification
"$PYTHON" -I - "$VOLUMES_FILE" "$PROJECT_VOLUMES_FILE" "$PROJECT_NAME" "$COMMIT" "$APP_VOLUME" "$DB_VOLUME" <<'PY' || { FAILURE_MESSAGE="Project volume label verification failed."; exit 1; }
import json,pathlib,subprocess,sys
out,project_rows,project,commit,*names=sys.argv[1:]
expected_names=set(names);listed=[]
for line in pathlib.Path(project_rows).read_text(encoding="utf-8").splitlines():
  if not line.strip():continue
  row=json.loads(line);name=row.get("Name") or row.get("Names")
  if name not in expected_names or name in listed:raise SystemExit(1)
  listed.append(name)
result={}
for logical,name in zip(("sth-app-data","sth-db2-data"),names):
  p=subprocess.run(["docker","volume","inspect","--format","{{json .Labels}}",name],text=True,capture_output=True,timeout=30)
  if p.returncode:
    result[logical]={"name":name,"exists":False}; continue
  labels=json.loads(p.stdout) or {}; expected={"com.docker.compose.project":project,"com.docker.compose.volume":logical,"dssc.semantic-treehouse.managed":"true","dssc.semantic-treehouse.project":project,"dssc.semantic-treehouse.upstream-commit":commit,"dssc.semantic-treehouse.logical-volume":logical,"dssc.semantic-treehouse.runtime-contract":"v1"}
  if set(labels)!=set(expected) or any(str(labels.get(k))!=v for k,v in expected.items()): raise SystemExit(1)
  result[logical]={"name":name,"exists":True,"labels_verified":True}
if set(listed)!={item["name"] for item in result.values() if item.get("exists")}:
  raise SystemExit(1)
pathlib.Path(out).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
PY

RUNTIME_STATUS=$("$PYTHON" -I -c 'import json,pathlib,sys
rows=[json.loads(x) for x in pathlib.Path(sys.argv[1]).read_text().splitlines() if x.strip()]
by={x["name"]:x for x in rows}; expected={sys.argv[2]+"-sth",sys.argv[2]+"-sth-db2"}
net=[json.loads(x) for x in pathlib.Path(sys.argv[3]).read_text().splitlines() if x.strip()]
vol=json.load(open(sys.argv[4],encoding="utf-8")); state=json.load(open(sys.argv[5],encoding="utf-8"))
present={item["name"] for item in vol.values() if item.get("exists")}; expected_volumes={item["name"] for item in vol.values()}
network_names={x["name"] for x in net}; expected_networks={sys.argv[6],sys.argv[7]}
state_valid=isinstance(state,dict) and state.get("validated") is True
success_context_ok=(not isinstance(state,dict) or state.get("success_state_context_required") is not True or state.get("docker_context_match") is True)
ports_ok=False
if state_valid and sys.argv[2]+"-sth" in by:
 p=by[sys.argv[2]+"-sth"].get("port_binding") or {};realized=p.get("realized") or {};requested=p.get("requested") or {}
 ports_ok=all(str(binding.get("HostIp"))=="127.0.0.1" and str(binding.get("HostPort"))==str(state["http_port"]) for binding in (realized,requested))
zero_runtime=not rows and not net
volumes_stopped=present in (set(),expected_volumes)
active=(set(by)==expected and len(rows)==2 and all(by[n]["running"] for n in expected)
 and by[sys.argv[2]+"-sth-db2"]["health"]=="healthy" and network_names==expected_networks and len(net)==2
 and present==expected_volumes and state_valid and ports_ok)
if zero_runtime and volumes_stopped and success_context_ok: print("STOPPED")
elif active: print("RUNNING")
else: print("REVIEW_REQUIRED")' "$CONTAINERS_FILE" "$PROJECT_NAME" "$NETWORKS_FILE" "$VOLUMES_FILE" "$STATE_PROJECTION_FILE" "$NETWORK_NAME" "$INGRESS_NETWORK_NAME")

status_smoke() {
  smoke_url=$1;header_file=$2
  set +e
  candidate=$(curl --noproxy '*' --silent --show-error --output /dev/null --dump-header "$header_file" --write-out '%{http_code}' --max-time 5 "$smoke_url" 2>> "$RAW_LOG")
  curl_code=$?
  set -e
  case "$candidate" in
    2??) [ "$curl_code" -eq 0 ] || return 1 ;;
    301|302|303|307|308)
      [ "$curl_code" -eq 0 ] || return 1
      "$PYTHON" -I - "$header_file" "$smoke_url" <<'PY' || return 1
import pathlib,sys,urllib.parse
headers=pathlib.Path(sys.argv[1]).read_text(encoding="iso-8859-1",errors="replace").splitlines();base=urllib.parse.urlsplit(sys.argv[2]);locations=[]
for line in headers:
  if line.lower().startswith("location:"):locations.append(line.split(":",1)[1].strip())
assert locations
target=urllib.parse.urlsplit(urllib.parse.urljoin(sys.argv[2],locations[-1]))
assert target.scheme=="http" and target.hostname in {"127.0.0.1","localhost"} and target.port==base.port
assert target.username is None and target.password is None
PY
      ;;
    *) return 1 ;;
  esac
  printf '%s\n' "$candidate"
}

if [ "$RUNTIME_STATUS" = RUNNING ] && [ -f "$STATE_FILE" ]; then
  STAGE=loopback-status-smoke
  HTTP_PORT=$("$PYTHON" -I -c 'import json,sys;s=json.load(open(sys.argv[1],encoding="utf-8"));assert s["bind_address"]=="127.0.0.1";print(int(s["http_port"]))' "$STATE_FILE")
  ROOT_SMOKE_URL="http://127.0.0.1:$HTTP_PORT/"
  API_SMOKE_URL="http://127.0.0.1:$HTTP_PORT/api/environment/info"
  command -v curl >/dev/null 2>&1 || { FAILURE_MESSAGE="curl is required for status smoke."; exit 1; }
  if ROOT_HTTP_STATUS=$(status_smoke "$ROOT_SMOKE_URL" "$ROOT_SMOKE_HEADER_FILE") && API_HTTP_STATUS=$(status_smoke "$API_SMOKE_URL" "$API_SMOKE_HEADER_FILE"); then
    HTTP_STATUS="PASS"
  else
    HTTP_STATUS="FAILED"
    RUNTIME_STATUS="REVIEW_REQUIRED"
  fi
  printf '[loopback-status-smoke] root_http=%s api_http=%s result=%s\n' "$ROOT_HTTP_STATUS" "$API_HTTP_STATUS" "$HTTP_STATUS" >> "$RAW_LOG"
fi

scrub_log_status=0
set +e
"$PYTHON" -I - "$RAW_LOG" "$CLEAN_LOG" "$ROOT_DIR" "$ENV_FILE" <<'PY'
import pathlib,re,sys
raw,clean,root,env=map(pathlib.Path,sys.argv[1:]); text=raw.read_text(encoding="utf-8",errors="replace")
values=[]
if env.is_file():
  for line in env.read_text(encoding="utf-8",errors="replace").splitlines():
    if "=" in line:
      k,v=line.split("=",1)
      if any(x in k.lower() for x in ("password","secret","api_key")) and v: values.append(v)
for v in values:text=text.replace(v,"<redacted>")
home=str(pathlib.Path.home());text=text.replace(str(root),"<repo>").replace(home,"<user-home>")
text=re.sub(r"(?i)(password|secret|token|credential)(\s*[=:]\s*)(\S+)",r"\1\2<redacted>",text)
if any(v and v in text for v in values) or str(root) in text or (home and home in text): raise SystemExit(1)
clean.write_text(text.rstrip()+"\n",encoding="utf-8",newline="\n");raw.unlink()
PY
scrub_log_status=$?
set -e
[ "$scrub_log_status" -eq 0 ] || { FAILURE_MESSAGE="Status log scrub failed."; exit 1; }
"$PYTHON" -I - "$EVIDENCE_FILE" "$LOCK_FILE" "$STATE_PROJECTION_FILE" "$CONTAINERS_FILE" "$NETWORKS_FILE" "$VOLUMES_FILE" "$RUNTIME_STATUS" "$HTTP_STATUS" "$ROOT_HTTP_STATUS" "$API_HTTP_STATUS" <<'PY'
import hashlib,json,pathlib,sys
out,lock_p,state_p,containers_p,networks_p,volumes_p,runtime_status,http_status,root_http,api_http=sys.argv[1:]
lock=json.load(open(lock_p,encoding="utf-8")); state=json.load(open(state_p,encoding="utf-8")) if pathlib.Path(state_p).is_file() else None
lines=lambda p:[json.loads(x) for x in pathlib.Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]
exit_code=0 if runtime_status in {"RUNNING","STOPPED"} else 1
payload={"schema":"dssc.semantic-treehouse.runtime-status.v1","status":"PASS" if exit_code==0 else "FAILED","exit_code":exit_code,"runtime_status":runtime_status,"http_status":http_status,"root_http_status":root_http,"api_http_status":api_http,"project_name":lock["compose"]["project_name"],"upstream_commit":lock["upstream"]["commit"],"lock_sha256":hashlib.sha256(pathlib.Path(lock_p).read_bytes()).hexdigest(),"runtime_state":state,"containers":lines(containers_p),"networks":lines(networks_p),"volumes":json.load(open(volumes_p,encoding="utf-8")),"config_env_inspected":False}
pathlib.Path(out).write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8",newline="\n")
PY
FINALIZED=true
EVIDENCE_WRITTEN=true
echo "Semantic Treehouse status: $RUNTIME_STATUS; containers=$(wc -l < "$CONTAINERS_FILE" | tr -d ' ') networks=$(wc -l < "$NETWORKS_FILE" | tr -d ' ')"
rm -f -- "$CONTAINERS_FILE" "$NETWORKS_FILE" "$VOLUMES_FILE" "$PROJECT_VOLUMES_FILE" "$STATE_PROJECTION_FILE" "$ROOT_SMOKE_HEADER_FILE" "$API_SMOKE_HEADER_FILE"
trap - 0
[ "$RUNTIME_STATUS" != REVIEW_REQUIRED ] || exit 1
exit 0
