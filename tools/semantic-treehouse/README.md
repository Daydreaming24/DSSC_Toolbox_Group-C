# Semantic Treehouse local evidence track

This directory holds the Phase 08 lock and the Git-ignored upstream checkout for the optional Semantic Treehouse evidence track. It does not participate in the required `all` suite.

## Historical Phase 08 controlled-attempt result (observed 2026-08-11)

| Stage | Historical status | Observed boundary |
|---|---|---|
| Upstream lock | `PINNED` | Tag `v4.3.0`, full commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf`, Apache-2.0, root `docker-compose.yml`. |
| Fixed checkout/materialization | `PASS` | Bounded sparse materialization of `frontend`, `backend`, `deployment` and `.dockerignore`; detached clean worktree; locked hashes verified; enumerated generated/secret paths absent. |
| Raw upstream Compose preflight | `BLOCKED` | 33 blocking and 46 review findings; `execution_authorized=false`. This canonical raw result remains unchanged. |
| Human risk decision | `APPROVED` | The user approved the presented findings, prerequisite repairs, bounded fixed-commit materialization and the narrower production runtime attempt. |
| `PrepareOnly` runtime boundary | `PASS` | Effective target closure is `sth` + `sth-db2`; loopback UI port `127.0.0.1:18014`; no database host port, bind mount, extra host, privileged mode, added capability or device; production app mode; internal network; project-scoped volumes; zero pull/build/up/container/volume/migration/smoke operations. |
| Application image build | `BLOCKED` | The final controlled retry received only 2,407,954 of 20,064,658 bytes for a digest-pinned Docker Hub FrankenPHP layer, then short read/unexpected EOF. |
| Deployment/workload | `NOT DEPLOYED / NOT RUN` | No application or database container started. Cleanup left zero project containers, networks, volumes and target application images. |
| UI/API/migration/import/export/publication | `NOT RUN` | No capability-level evidence was produced. Import/export were outside the approved scope. |

The image-build attempt is preserved as the transport-failure result observed on 2026-08-11. The later recovery is recorded separately below.

## Locked source and checkout

The authority file is [`upstream.lock.json`](upstream.lock.json). The checkout path is `tools/semantic-treehouse/upstream/` and remains Git-ignored. The clone/materialization wrappers accept no user-supplied repository URL, ref, checkout path or sparse scope. They verify the exact lock, set repository-local `core.autocrlf=false`, require a detached clean worktree and reject ignored contamination such as `.env`, backend runtime/vendor files and frontend dependency/cache directories.

From the repository root:

```powershell
.\C_Semantic_Treehouse\scripts\treehouse_clone_or_update.ps1
```

```sh
./C_Semantic_Treehouse/scripts/treehouse_clone_or_update.sh
```

## Raw preflight

The checker is read-only. It performs no clone, pull, build, container or network operation.

```powershell
.\.venv\Scripts\python.exe -I scripts\check_treehouse_compose.py `
  --upstream-root tools/semantic-treehouse/upstream `
  --compose tools/semantic-treehouse/upstream/docker-compose.yml `
  --expected-commit e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf `
  --project-name dssc-semantic-treehouse-v04 `
  --output build/evidence/treehouse/preflight.json
```

The canonical exit code is non-zero because the raw upstream compose file contains unresolved runtime risks. The independent human decision authorized a narrower generated production boundary and never converts this result to passing.

## Runtime wrappers

The generated runtime boundary targets the explicit production service only. It forces `APP_ENV=prod` and `APP_DEBUG=0`, uses synthetic local-only values, disables optional notification/AI/validator integrations, publishes only `127.0.0.1:18014:80`, removes the database host port, and uses an internal network plus two exact project volumes. Generated environment values are private runtime material and are excluded from sanitized evidence.

For browser use, routine container pause/resume, full shutdown and data-protection guidance, see the [Semantic Treehouse user guide](../../C_Semantic_Treehouse/C_semantic_treehouse_user_guide.md).

Preparation without external Docker mutations:

```powershell
.\C_Semantic_Treehouse\scripts\treehouse_up.ps1 -HttpPort 18014 -PrepareOnly
```

An authorized deployment attempt uses the same command without `-PrepareOnly`. Status and cleanup are exact-project operations:

```powershell
.\C_Semantic_Treehouse\scripts\treehouse_status.ps1
.\C_Semantic_Treehouse\scripts\treehouse_down.ps1
```

The POSIX wrappers use the matching `.sh` filenames. Default cleanup does not remove volumes. Failure cleanup removes only resources created by the exact failed attempt after label verification; it never adopts unrelated containers, networks or volumes.

## Evidence meaning

Checkout success proves source identity and materialization. `PrepareOnly` success proves the generated configuration boundary and zero-operation counters. A completed image build would still provide no workload evidence. Deployment, database migration, UI, API, import, export and publication each require their own actual result before their status can change.

The independent manifest-driven validation harness remains the authoritative release path when this optional deployment is unavailable:

```powershell
.\scripts\validate.ps1 -Suite all
```

```sh
./scripts/validate.sh --suite all
```

## Recovery addendum (2026-08-12)

The approved recovery completed for the fixed `v4.3.0` / `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf` checkout. Earlier blocked build-attempt evidence remains historical evidence.

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`.

`SHACL validator manifest digest=sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`; `SHACL validator security boundary=non-root/internal-only/zero-host-port/read-only-rootfs/drop-all/no-new-privileges/resource-bounded`; `SHACL validation controls=positive-pass/negative-fail/idempotent-recheck-pass/EasyRDF-4-pattern-local-review-patch`; `PAUSED persistence=containers-networks-app-db-volumes-preserved`.

The retained `sth`, `shacl-validator` and `sth-db2` containers are paused as exited containers bound to the exact project and evidence state. While running, the application listener is `http://127.0.0.1:18014/`; the database and validator have no host port. The production admin-only local-review authentication and `/app/var/user_data` persistence boundary is recorded in `build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json`.

The authenticated loopback API imported the canonical six-asset v0.4 set. Import evidence is `build/evidence/treehouse/v0.4-import-2026-08-12.json`; `build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json` records retained inventory and relationships plus an ontology TTL export whose parsed RDF graph is isomorphic to the canonical source. A real browser login followed by imported inventory and model views is recorded in `build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json`.

The validator is fixed to upstream manifest digest `sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b` and runs through a derived non-root image with internal-network-only access, zero host ports/bind mounts, read-only rootfs, dropped capabilities, no-new-privileges and resource limits. The canonical positive control passed; an in-memory `datasetId` removal failed with one violation. The EasyRDF four-`sh:pattern` lexical-change issue is contained by a local-review derived-app patch that forwards raw canonical Turtle only when generated schema is disabled and does not alter canonical bytes. First-run and idempotent evidence are `build/evidence/treehouse/shacl-validator-execution-2026-08-12.json` and `build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json`. Application, validator and database were then stopped in order while containers, networks and both named data volumes were preserved; see `build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json`. Publication remains unperformed.
