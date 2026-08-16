# v0.4 Core Validation Results

Deterministic rendering of `core-results.json` (Phase 09 §6.6).
This report records stable contract bindings and upstream suite gate
outcomes only. It does **not** embed deliverables content hash,
Phase 09 final-QA self-check results, timestamps, commit SHA, or CI
run metadata.

## Contract bindings

- validation-suites path: `C_Semantic_Treehouse/manifests/validation-suites.json`
- validation-suites schema: `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`
- contract_version: `1.6.0`
- validation-suites manifest SHA-256: `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`
- validation-suites schema SHA-256: `70d436cd0509da2fcec8b602c1bffc5f00490d24c13c2ee47caf84791199802a`
- lock: `requirements.lock` SHA-256 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2`
- deliverables path (stable path only): `C_Semantic_Treehouse/manifests/deliverables.json`

## Upstream manifests

| Path | SHA-256 |
|---|---|
| `C_Semantic_Treehouse/manifests/release-manifest.json` | `35b194fe0c280c9a01067d2c9eac205c9e178da235ba06596719144b975111d8` |
| `C_Semantic_Treehouse/manifests/baseline-test-cases.json` | `e8fb57fe2f609c48c0340cf8e3b78d2e8f81d0fe0fd3ab505468cfe315767e43` |
| `C_Semantic_Treehouse/manifests/v0.4-requirements.json` | `53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e` |
| `C_Semantic_Treehouse/manifests/v0.4-test-cases.json` | `87e367ea285ddc7feb5fa7f3f4b6c0035be0b768de5e56398ac422abaf494e5a` |

## Suite `all` gate

- program_status: **SUCCESS**
- exit_code: `0`
- counts: discovered=17, executed=17, passed=17, failed=0, skipped=0
- required_skipped: `0`

### Components

| Component | Suite | Program status | Status |
|---|---|---|---|
| `frozen.manifest` | `frozen` | SUCCESS | PASS |
| `environment.doctor` | `environment` | SUCCESS | PASS |
| `baseline.reproduction` | `baseline` | SUCCESS | PASS |
| `traceability.contract-audit` | `traceability` | SUCCESS | PASS |
| `v0.4-model.release-contract` | `v0.4-model` | SUCCESS | PASS |
| `v0.4.test-case-schema` | `v0.4` | SUCCESS | PASS |
| `v0.4.manifest-semantics` | `v0.4` | SUCCESS | PASS |
| `v0.4.fixture-hashes` | `v0.4` | SUCCESS | PASS |
| `v0.4.four-state` | `v0.4` | SUCCESS | PASS |
| `v0.4.report-assertions` | `v0.4` | SUCCESS | PASS |
| `v0.4.target-activation` | `v0.4` | SUCCESS | PASS |
| `v0.4.fault-injection` | `v0.4` | SUCCESS | PASS |
| `all.composition` | `all` | SUCCESS | PASS |
| `all.semantic-sparql` | `all` | SUCCESS | PASS |
| `all.quality` | `all` | SUCCESS | PASS |
| `all.governance` | `all` | SUCCESS | PASS |
| `all.documentation` | `all` | SUCCESS | PASS |

## Platforms

| Platform | Profile | Status | Result content SHA-256 |
|---|---|---|---|
| host | `host` | SUCCESS | `5a1504a1bfb00d4fde676d101298a6d4db5afc4f143332a664ef569629edd34f` |
| container | `container` | SUCCESS | `fa72bc651c705b74f3984ff03912118d247b77d6d810fe0ce461628559bef28c` |

Raw environment inventories and full suite result JSON remain under
ignored `build/**` paths referenced only as runtime fingerprints.

## Source hashes

- validator/harness source files recorded: **39**
- source_hash_policy: `must-match-disk`
- source_hash_issues: `[]`

Full path→SHA-256 map is normative in `core-results.json`.

## Explicit exclusions (no self-reference)

- `deliverables_content_hash`: excluded
- `phase09_deliverables_checker_result`: excluded
- `phase09_publication_safety_checker_result`: excluded
- `phase09_evidence_freshness_checker_result`: excluded
- `realtime_timestamp`: excluded
- `current_commit_sha`: excluded
- `ci_run_id`: excluded
- `ci_run_url`: excluded
- `remote_clone_binding`: excluded
