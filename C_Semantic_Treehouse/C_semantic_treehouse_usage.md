# C Semantic Treehouse Usage — v0.4 Evidence Plan

## Tool positioning

Semantic Treehouse is an optional governance, modelling and publication evidence track for this package. The v0.4 semantic truth sources are the frozen D-group Shape, accepted decisions and machine-readable manifests. The independent repository harness validates the release without Semantic Treehouse, hosted services, a database, credentials or network access.

Treehouse evidence can show that a named upstream build was deployed and that selected UI/API/import/export workflows were actually exercised. It cannot replace the D-group SHACL contract, release manifest, test oracle, semantic/domain review or human release authorization.

## Historical v0 evidence

The repository retains a v0 evidence snapshot under `archive/`. It records upstream commit `33cf285c187f58c773f4e0d8c2826eeb2f6b3778`, a historical frontend smoke response `HTTP/1.1 200 OK` at port 4200, and a backend-root timeout at port 8014. The primary surviving files are:

- [historical upstream revision](../archive/v0_evidence/C_Semantic_Treehouse/evidence/semantic-treehouse-upstream-version.txt);
- [historical container status](../archive/v0_evidence/C_Semantic_Treehouse/evidence/treehouse-docker-ps.txt);
- [historical smoke check](../archive/v0_evidence/C_Semantic_Treehouse/evidence/treehouse-smoke-check.txt);
- [v0 evidence collection notes](../archive/v0_evidence/C_Semantic_Treehouse/evidence/README.md).

This is `HISTORICAL/PARTIAL` evidence. It belongs to another machine and release state, lacks a stable current upstream/compose lock, did not complete the full UI workflow or screenshot capture, and does not prove any v0.4 Treehouse behavior. The migration boundary is recorded in [v0-errata.md](../docs/v0.4/v0-errata.md).

## Historical v0.4 controlled-attempt status (observed 2026-08-11)

| Capability or evidence | Historical status | Evidence boundary |
|---|---|---|
| Independent v0.4 validation harness | `RUN / PASS` | Phase 05 executed 66/66 four-state cases; Phase 06 added 20/20 SPARQL questions, quality and governance checks. |
| Semantic Treehouse fixed checkout/materialization | `PASS` | Upstream tag `v4.3.0` is locked to commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf`. The bounded sparse checkout materialized `frontend`, `backend`, `deployment` and `.dockerignore`, verified the lock hashes, a detached clean worktree, `core.autocrlf=false`, and absence of the enumerated generated/secret paths. |
| Semantic Treehouse raw upstream compose preflight | `BLOCKED` | The canonical read-only result remains 33 `BLOCK`, 46 `REVIEW`, `execution_authorized=false`. The raw result was preserved after the checker gained safe support for upstream `!override`/`!reset` tags. |
| Semantic Treehouse finding-specific human opt-in | `APPROVED` | After the raw findings and the GitLab materialization failure were presented, the user approved the recorded risks, prerequisite repairs, bounded fixed-commit materialization and the narrower production runtime attempt. This decision does not change the raw preflight result. |
| Semantic Treehouse PrepareOnly runtime boundary | `PASS` | Static Compose/config/build-graph checks confirmed target closure `sth` + `sth-db2`, `APP_ENV=prod`, loopback `127.0.0.1:18014`, no database host port, no bind mounts, no extra hosts, an internal network, digest-pinned third-party bases, and zero pull/build/up/container/volume/migration/smoke operations. |
| Semantic Treehouse image build attempt | `BLOCKED` | The approved build path was attempted and repaired through bounded diagnostics. The final controlled retry still failed while downloading a digest-pinned Docker Hub FrankenPHP layer: 2,407,954 of 20,064,658 bytes arrived, followed by a short read/unexpected EOF. Further automatic retry was not authorized. |
| Semantic Treehouse deployment | `NOT DEPLOYED` | The application image never completed. Cleanup left zero project containers, networks, volumes and target application images. |
| Semantic Treehouse workload/container execution | `NOT RUN` | No Treehouse application or database container started. Image-build activity is recorded separately and supplies no workload evidence. |
| Semantic Treehouse database migration | `NOT RUN` | No database container started and no migration command executed. |
| Semantic Treehouse UI workflow | `NOT RUN` | No current page existed to inspect; no UI interaction or screenshot is claimed. |
| Semantic Treehouse API | `NOT RUN` | No current service endpoint existed; no request/response evidence is claimed. |
| Semantic Treehouse model import | `NOT RUN` | Import was outside the approved scope; no receipt or semantic comparison exists. |
| Semantic Treehouse export | `NOT RUN` | Export was outside the approved scope; no export bytes or comparison report exists. |
| Semantic Treehouse publication | `NOT RUN` | No current publication identifier or human authorization exists. |
| SEMIC external validation | `NOT RUN` | This track is `DEFERRED`: no data-egress authorization was granted, and zero files and zero bytes were uploaded. Decision: `build/evidence/itb-semic/decision.json`. |
| DSSC ITB execution | `NOT RUN` | This track is `DEFERRED`: no data-egress authorization was granted, and zero files and zero bytes were uploaded. Decision: `build/evidence/itb-semic/decision.json`. |
| GitHub Actions / remote publication (2026-08-11 snapshot) | `NOT RUN` | Phase 09 尚未在该历史时点执行实际 CI 与 repository publication。 |

This table freezes the controlled attempt observed on 2026-08-11. Each status is stage-specific. Checkout and PrepareOnly success provide preparation evidence only. The blocked raw preflight and blocked build attempt remain visible, while `NOT DEPLOYED` and `NOT RUN` contribute no deployment or workload evidence. The 2026-08-12 recovery is recorded separately below.

## Independent validation harness（独立验证 harness）

The Windows host entrypoint is:

```powershell
.\scripts\validate.ps1 -Suite all
```

The Linux entrypoint is:

```sh
./scripts/validate.sh --suite all
```

Both wrappers select the controlled Python environment and call the same root dispatcher. The suite validates frozen inputs, environment, historical baseline, traceability, v0.4 model artifacts, the four-state v0.4 harness, SPARQL semantics, quality, governance and registered documentation checks. A required check that is missing, skipped, stale, empty or inconsistent returns a non-zero program result.

Current deterministic evidence is written under `build/validation/`; [v0.4 results](../build/validation/v0.4/results.json), [SPARQL results](../build/validation/sparql/results.json), [quality results](../build/validation/quality/results.json) and [governance results](../build/validation/governance/results.json) are generated evidence, not editable oracle sources.

## Phase 08 optional deployment path

Phase 08 exercised the authorized preparation and build-attempt boundary. The static entrypoint [`check_treehouse_compose.py`](../scripts/check_treehouse_compose.py) passed its deterministic self-test and inspected the fixed upstream compose file. Its canonical result remains `BLOCKED` with 33 blocking and 46 review findings. Human opt-in then authorized a narrower project-side production overlay; the decision was recorded independently so the raw checker result stayed unchanged.

The fixed checkout and materialization wrapper completed. `PrepareOnly` validated the effective runtime and build graph while its operation counters stayed at zero. The actual application-image build stopped before container start. After wrapper repairs and one controlled transport retry, Docker Hub again returned a short read/unexpected EOF for the digest-pinned FrankenPHP layer. Cleanup confirmed zero project containers, networks, volumes and target application images. A new workload attempt now requires fresh human approval after registry transport is stable.

The repository retains PowerShell and POSIX helpers as candidate wrappers:

- [treehouse_clone_or_update.ps1](scripts/treehouse_clone_or_update.ps1) / [treehouse_clone_or_update.sh](scripts/treehouse_clone_or_update.sh);
- [treehouse_up.ps1](scripts/treehouse_up.ps1) / [treehouse_up.sh](scripts/treehouse_up.sh);
- [treehouse_status.ps1](scripts/treehouse_status.ps1) / [treehouse_status.sh](scripts/treehouse_status.sh);
- [treehouse_down.ps1](scripts/treehouse_down.ps1) / [treehouse_down.sh](scripts/treehouse_down.sh).

The PowerShell clone/materialization and up/PrepareOnly/build-attempt path was exercised under the approved lock and evidence boundary. The POSIX counterparts remain cross-platform entrypoints governed by the same lock and project/resource-label checks. Status, cleanup and evidence commands are scoped to the exact project. The archived `make`/`make.cmd` commands are historical and are not current entrypoints.

The approved Windows sequence from the repository root is:

```powershell
.\C_Semantic_Treehouse\scripts\treehouse_clone_or_update.ps1
.\C_Semantic_Treehouse\scripts\treehouse_up.ps1
.\C_Semantic_Treehouse\scripts\treehouse_status.ps1
.\C_Semantic_Treehouse\scripts\treehouse_down.ps1
```

The POSIX counterparts use the same filenames with `.sh`. In this Phase 08 attempt, checkout/materialization and PrepareOnly ran successfully, the image build failed, and the later status/UI/API/migration stages were consequently not executed.

## UI, API, import（导入） and export（导出） evidence gates

A current Treehouse claim requires evidence for the specific capability being claimed:

| Gate | Minimum capability evidence |
|---|---|
| Deployment | Approved command, upstream commit, selected compose path, pinned image identities, command exit codes, container status and sanitized logs. |
| UI | Current URL, actual interactive page state, screenshot with capture context, and the exact workflow exercised. A port-200 smoke test proves availability only. |
| API | Route and method, sanitized request, status code, response body/schema, server log correlation and actual tool revision. |
| Import | Input artifact ID/path/hash from the release manifest, import settings, receipt/job ID, tool diagnostics and post-import semantic inventory. |
| Export | Export format, raw bytes/hash, tool/version/job identity, parser result and a semantic comparison against the manifest-bound source. Byte equality is required only where the claimed operation promises byte preservation. |
| Version/review | Model version identity, actor, action, date, state transition and evidence reference. |
| Publication | Human authorization plus actual publication identifier and retrievable artifact identity. |

Screenshots alone do not prove import/export fidelity. An export comparison must detect changed IRIs, missing triples, datatype/cardinality changes and altered SHACL constraints. Any Treehouse-generated artifact remains candidate evidence until it is reviewed and, when released, entered into a manifest.

## Artifact comparison set

The following table is a checked projection of the current release entry in [release-manifest.json](manifests/release-manifest.json). It identifies the bytes against which a future Treehouse import/export may be compared; the manifest remains the artifact truth source.

| artifact_id | version | role | path | sha256 |
|---|---|---|---|---|
| v04-release-readme | v0.4 | release-documentation | C_Semantic_Treehouse/model/v0.4/README.md | 388e4dd823c60b55772946eb7fa37e90c2e5cf52e8300b784bba29ae4364873c |
| v04-ontology | v0.4 | ontology | C_Semantic_Treehouse/model/v0.4/building-energy-ontology.ttl | c2139583d8b2c92fbd805db49f9a30e883c1aea27cb704063c3ea9d0456df5d9 |
| v04-metadata-context | v0.4 | metadata-context | C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld | f46d3056239cc1cb7d678707e749b33e336564e5fce23ffcccd528eae6cbe391 |
| v04-metadata-shapes | v0.4 | metadata-shapes | C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl | a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda |
| v04-metadata-valid | v0.4 | metadata-valid-example | C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld | 9acc287ae274e549becd15852231b325c43e1dbddc14e9f2459f4c490420f239 |
| v04-checksums | v0.4 | checksum-manifest | C_Semantic_Treehouse/model/v0.4/SHA256SUMS | 66cd79dd5cd05299c6a07010b087b4da87b138045223aa39449548ea7c46484a |
| v04-inherited-record-schema | v0.4 | record-json-schema | C_Semantic_Treehouse/model/v0.3/energy-reading-record.schema.json | dd07414e3752bf582bf5e721009064e16d7be3e1e06d60daaad08000869ccfa9 |
| v04-inherited-record-context | v0.4 | record-context | C_Semantic_Treehouse/model/v0.3/energy-reading-record-context.jsonld | 9727da9b8650dc444d719113a6978a3a26a59bfd1fde011a98e4c1f4b476f748 |
| v04-inherited-record-shapes | v0.4 | record-shapes | C_Semantic_Treehouse/model/v0.3/energy-reading-record-shapes.ttl | 84d1eee9cfeecd1791117552611e83d36af7df4f3b4c783ddbd75d45bae66c9a |
| v04-inherited-record-valid | v0.4 | record-valid-example | C_Semantic_Treehouse/model/v0.3/energy-reading-record-valid.jsonld | 8f7509ad08fb9a62cdff1d6c904801c9421c3ce768bdd9ecb651cd480aa158e1 |
| v04-inherited-record-invalid | v0.4 | record-invalid-example | C_Semantic_Treehouse/model/v0.3/energy-reading-record-invalid.jsonld | e516f6a8e4ea811170c72e922b86ac7ea46594046704d01a55a2c8e13cd8f358 |

## Risks and fallback（回退）

The principal risks are upstream drift, mutable images, dependency downloads, unavailable services, port conflicts, local secrets, model round-trip loss and tool-specific semantics. A current run should isolate its project name and volumes, sanitize logs, bound timeouts, record every failure and shut down only the exact approved deployment.

The fallback is the independent manifest-driven harness. Treehouse failure or absence leaves the core validation path available and auditable. Its status remains the observed status; it is never translated into a local harness PASS. SEMIC and ITB follow the same evidence rule and currently remain `NOT RUN`.

## Semantic Treehouse recovery addendum (2026-08-12)

The approved recovery completed against upstream `v4.3.0` / commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf`. The retained historical failure records describe earlier attempts. The current recovery truth is:

| Repository publication evidence | Current status | Evidence boundary |
|---|---|---|
| GitHub Actions / remote publication（上一已确认候选） | `PASS` | 已确认候选完成公开 push、候选绑定的 Ubuntu/Windows/Docker CI 与 canonical URL remote clean clone；每个发生 tracked 内容变化的新候选均须独立重验，最新动态绑定见 [`publication-record.md`](../docs/v0.4/publication-record.md)。 |

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`.

`SHACL validator manifest digest=sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`; `SHACL validator security boundary=non-root/internal-only/zero-host-port/read-only-rootfs/drop-all/no-new-privileges/resource-bounded`; `SHACL validation controls=positive-pass/negative-fail/idempotent-recheck-pass/EasyRDF-4-pattern-local-review-patch`; `PAUSED persistence=containers-networks-app-db-volumes-preserved`.

The retained runtime uses `APP_ENV=prod`, `APP_DEBUG=0`, an explicit admin-only local-review login gate and the persistent application-data target `/app/var/user_data`; its cookie-aware authentication evidence records no cookie values or client session material. The runtime boundary is recorded in `build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json`.

The authenticated loopback API import covered the canonical six-asset v0.4 set and preserved the manifest-bound source identities. The import receipt is `build/evidence/treehouse/v0.4-import-2026-08-12.json`; the retained inventory, relationships and ontology export were checked again after restart in `build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json`. The exported ontology TTL parsed successfully and its RDF graph is isomorphic to the canonical source graph.

A real browser session completed login, opened the imported inventory and viewed the imported model after the API import; `build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json` records that UI workflow.

The SHACL validator was deployed from the fixed upstream manifest digest `sha256:208dc8b9…2b0b` as a derived non-root image; the exact digest is recorded in the execution evidence. Its runtime uses UID/GID `65532:65532`, an internal network, zero host ports and bind mounts, a read-only root filesystem, `cap_drop=ALL`, `no-new-privileges`, and bounded memory, CPU and PID resources. The canonical positive control returned `syntax_valid=true` and `schema_valid=true`; the in-memory negative control removed `datasetId` and returned `schema_valid=false` with one violation. `build/evidence/treehouse/shacl-validator-execution-2026-08-12.json` records the first pass, and `build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json` records the identical successful result with the binding reused.

EasyRDF changed the lexical form of four `sh:pattern` literals during Turtle-to-RDF/XML conversion. A bounded local-review derived-app patch therefore forwards the raw canonical Turtle only when generated schema is disabled; it leaves the canonical SHACL bytes unchanged. After validation, the application, validator and database were stopped in that order. All three containers and networks remain present, and the application/database named volumes remain preserved; `build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json` records the resulting `PAUSED` state. No publication action or identifier exists.
