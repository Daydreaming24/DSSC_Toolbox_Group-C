# Release Policy

## Scope

This policy applies cumulatively to v0.1–v0.4. Historical releases remain frozen. v0.4 release eligibility is derived from machine-readable manifests, actual model and fixture bytes, deterministic validation evidence, and explicit human approval.

## D-Group Input Gate

The normative v0.4 input is `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`, SHA-256 `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`. The explanatory change note and accepted ADRs are bound through `release-manifest.json`.

The gate requires:

- the received D Shape, the v0.4 model Shape, and the release-manifest binding to share the declared hash;
- all D04 requirements to trace to actual named Shape/path/severity/constraint/message semantics;
- the derived v0.4 artifacts and the five inherited v0.3 record artifacts to match their manifest hashes;
- the D Shape bytes, model, fixtures, oracle, and historical releases to remain unchanged during Phase 06.

## Four-State Gate

The v0.4 test manifest must discover and execute all required cases with no skip. Expected and actual business status must match:

- `PASS`: validation succeeds with no Violation or Warning.
- `FAIL`: validation succeeds and at least one Violation exists.
- `INAPPLICABLE`: validation succeeds, no Violation exists, and the approved Closed Shape Warning exists.
- `UNTESTABLE`: authority and harness preflight succeed, then a controlled SUT parse/load or validator/infrastructure fault prevents a trustworthy business judgment.

Harness failures, missing tests, stale hashes, malformed authority records, and oracle mismatches produce program `ERROR` and a non-zero exit.

## Manifest Gate

Every run validates JSON Schema and cross-record semantics for these fixed authorities before governance assertions:

1. `C_Semantic_Treehouse/manifests/release-manifest.json`
2. `C_Semantic_Treehouse/manifests/baseline-test-cases.json`
3. `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
4. `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
5. `C_Semantic_Treehouse/manifests/validation-suites.json`

Checks include duplicate identifiers, repository-relative paths, cross-references, byte hashes, version relations, dependency cycles, fixed entrypoints, non-empty composition, and required coverage. The v0.4 SPARQL test manifest and schema are also validated by the semantic-test component.

The seven public suite names remain `frozen`, `environment`, `baseline`, `traceability`, `v0.4-model`, `v0.4`, and `all`. Phase 06 internal SPARQL, quality, and governance checks run under `all`. Contract composition changes require a version bump and release-manifest hash binding.

## Semantic and Quality Gate

- All eight historical competency questions retain their established query and expected-result semantics.
- Every required v0.4 query is discovered, executed, and compared with its exact deterministic oracle.
- Quality conclusions state numerator, denominator, source, and exclusion rule.
- Requirement implementation/test coverage, required/optional fields, constraint-component distribution, four-state cases, direct reuse/local mapping, breaking-change risk, and release/provenance completeness are computed from actual sources.
- The v0.3-to-v0.4 metadata conclusion remains `wire-profile breaking`; the v0.3 Energy Reading Record inheritance remains `change: none`.

## Cross-Platform Gate

Release evidence must show the same locked Python core running successfully on:

- the certified Windows host route;
- the fixed Linux validation route;
- the pinned Docker validation image and digest;
- the actual GitHub Actions workflow before publication.

Platform-specific environment metadata is stored separately from normalized deterministic results. Unsupported native platforms use the fixed Docker route until separately certified.

## Evidence Gate

Required evidence includes:

- deterministic machine JSON and generated Markdown for SPARQL, quality, and governance;
- independent environment sidecars;
- consumed manifest/schema hashes and the validation-suites contract version/hash;
- dispatcher, adapter, checker, reporter, and loaded helper source hashes;
- query/fixture/Shape/input hashes and freshness checks;
- negative controls proving missing, duplicate, dangling, tampered, skipped, zero-discovery, shell-payload, stale-report, and false-completion conditions fail closed;
- command exit codes, discovered/executed/passed/failed/skipped counts, and diff/frozen audits.

Live timestamps, personal absolute paths, and machine-local interpreter paths stay outside normalized cross-platform result JSON.

## Approval and Publication Gate

The three accepted ADRs document earlier group-level migration decisions. The maintainer has accepted the P00-R14 final human-governance responsibilities, including Release Approver responsibility; item-level semantic/domain/D review records remain `pending` and are retained as a known limitation.

CI and GitHub repository publication are separately evidenced Phase 09 activities and have confirmed candidate-bound records in `docs/v0.4/publication-record.md`. Semantic Treehouse publication remains `pending`. Local automated success cannot create any of those records; Phase 08 optional external evidence and Phase 09 publication decisions follow their own authorized workflows.

## Rollback Policy

- Keep v0.1–v0.3 artifacts and hashes available.
- Keep failed evidence for diagnosis.
- Restore downstream references to the last approved release when a release candidate fails.
- Document the reason and rerun gates from the earliest affected Phase.
- Obtain explicit authority before destructive Git, remote, tag, publication, or release actions.
