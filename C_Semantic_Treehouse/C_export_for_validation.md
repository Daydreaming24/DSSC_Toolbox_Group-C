# C Export for Validation — v0.4

## Validation package boundary

This report defines the package D Group and other validators consume for the Building Energy v0.4 metadata profile. The frozen D-group Shape is the executable authority. C Group supplies a byte-identical release Shape, an offline JSON-LD context and example, machine-readable release/requirement/test manifests, independent fixtures, a deterministic pySHACL harness and normalized reports.

Expected results are reviewed oracle data. Actual results never rewrite the test manifest. A validation run proves that the current bytes behave as expected; it does not itself approve publication or legal compliance.

## D source and C-derived Shape

- Normative D-group source: `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`; SHA-256: `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`.
- C-group release Shape: `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl`; SHA-256: `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`.
- Derivation: byte-copy; any byte difference is a release-contract error.

[ADR-001](../docs/v0.4/decisions/ADR-001-dct-conforms-to.md), [ADR-002](../docs/v0.4/decisions/ADR-002-wire-profile-and-version-identity.md) and [ADR-003](../docs/v0.4/decisions/ADR-003-energy-record-inheritance.md) define the approved payload, version and record-inheritance boundaries. They do not modify the D Shape.

## Release-manifest artifact projection

The following table is copied from the `v0.4` entry in [release-manifest.json](manifests/release-manifest.json). It is a checked projection for handoff; the release manifest remains the only artifact registry.

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

## Manifests and oracle

The validation flow consumes these authorities before any SUT case executes:

- [release-manifest.json](manifests/release-manifest.json): release identity, artifact paths/hashes, origin and five inherited record artifacts;
- [v0.4-requirements.json](manifests/v0.4-requirements.json): D04-R001–D04-R017, source Shape/path/severity/message/components and test obligations; current SHA-256 `53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e`;
- [v0.4-test-cases.json](manifests/v0.4-test-cases.json): 66 fixture paths/hashes and expected business/report assertions; current SHA-256 `87e367ea285ddc7feb5fa7f3f4b6c0035be0b768de5e56398ac422abaf494e5a`;
- [baseline-test-cases.json](manifests/baseline-test-cases.json): frozen v0.1–v0.3 regression oracle;
- [validation-suites.json](manifests/validation-suites.json): the versioned suite composition consumed by the root dispatcher.

Each manifest is checked against its schema and cross-record semantics. Checks cover unique IDs, repository-relative paths, reference integrity, SHA-256 freshness, release/requirement/fixture bindings, allowed entrypoints and non-empty deterministic suite composition. The release manifest's own current hash and suite-registry binding are recorded by each formal run, so this report does not maintain a duplicate mutable binding.

## Fixtures

The test manifest binds every fixture individually. Directory names aid navigation and do not determine the expected status:

- [pass/](fixtures/v0.4/pass/) — 6 cases;
- [fail/](fixtures/v0.4/fail/) — 53 cases;
- [inapplicable/](fixtures/v0.4/inapplicable/) — 1 case;
- [untestable/](fixtures/v0.4/untestable/) — 6 cases.

Coverage includes the canonical Dataset, optional values, equal temporal bounds, zero/two/blank-node Datasets, missing/multiple/wrong-type/blank fields, case-sensitive enumerations, HTTP or literal endpoint/license values, reversed dates, Closed Shape Warning alone and with a Violation, malformed JSON/JSON-LD, missing local context and controlled post-preflight runtime faults.

## Four business statuses and program status

Classification follows this deterministic priority:

1. `UNTESTABLE`: authority, manifest, harness and dependencies passed preflight, then the SUT could not parse/load or a manifest-allowlisted validator/service fault prevented a trustworthy judgment.
2. `FAIL`: validation completed and at least one `sh:Violation` exists; any simultaneous Warning does not lower the result.
3. `INAPPLICABLE`: validation completed with no Violation and the approved `ex:DatasetClosedShape` Warning exists.
4. `PASS`: input and Shape loaded, required targets were evaluated, and no Violation or Warning exists.

Business status is distinct from program status:

- `SUCCESS` means the harness completed and every actual business status/report assertion matched the test manifest;
- `ERROR` means authority or dependency preflight failed, zero/required tests were missing or skipped, a report was malformed, an oracle mismatched, or orchestration/evidence writing failed. It returns non-zero and supplies no fabricated business conclusion.

## SHACL report graph fields

For report-producing cases, the harness normalizes and asserts each `sh:ValidationResult`:

| SHACL meaning | Normalized result key | Validation use |
|---|---|---|
| `sh:focusNode` | `focus_node` | Identifies the Dataset or fixed submission node evaluated. |
| `sh:resultPath` | `result_path` | Identifies the property path; node-level/SPARQL submission results may have no path. |
| `sh:sourceShape` | `source_shape` | Must match the named Shape required by the oracle. |
| `sh:sourceConstraintComponent` | `source_constraint_component` | Distinguishes count, datatype, node kind, pattern, `sh:in`, Closed and SPARQL constraints. |
| `sh:resultSeverity` | `severity` / `severity_name` | Drives Violation-versus-Warning classification. |
| `sh:resultMessage` | `message` | Compared according to the manifest's exact or declared message policy. |
| `sh:value` | `value` | Preserves the offending RDF term when the report supplies one. |

The harness also asserts result counts, requirement scope, target activation, `report_conforms`, graph separation and unchanged data/Shape graphs. A default engine message is never promoted to a normative D-group message when the TTL supplies none.

## Unified commands and exit semantics

Run from the repository root on Windows:

```powershell
.\scripts\validate.ps1 -Suite v0.4
```

Run the full registered contract with:

```powershell
.\scripts\validate.ps1 -Suite all
```

The Linux equivalents are:

```sh
./scripts/validate.sh --suite v0.4
./scripts/validate.sh --suite all
```

Exit `0` means program `SUCCESS`: every required case was discovered and executed, expected and actual business statuses matched, and all declared assertions passed. An expected `FAIL`, `INAPPLICABLE` or `UNTESTABLE` case contributes to exit `0` only when its complete oracle matches. Program `ERROR` returns non-zero.

The normalized v0.4 evidence is [results.json](../build/validation/v0.4/results.json), with a human-readable [report.md](../build/validation/v0.4/report.md) and separate [run-environment.json](../build/validation/v0.4/run-environment.json). Phase 05's established result was 66 discovered/executed/passed, zero failed/skipped, distributed as 6 `PASS`, 53 `FAIL`, 1 `INAPPLICABLE`, and 6 `UNTESTABLE`.

## Expected outcomes

- Canonical and boundary-positive fixtures produce their manifest-declared `PASS` with non-zero target activation and no report result.
- Constraint-negative fixtures produce `FAIL` only when source Shape, path where applicable, component, Violation severity, message policy, requirement and counts all match.
The boundary and controlled-fault cases project directly from the test-case manifest:

| case_id | expected_business_status | scope |
|---|---|---|
| `D04-PC059` | `INAPPLICABLE` | Closed Shape Warning only. |
| `D04-PC060` | `FAIL` | Closed Shape Warning plus provider-name Violation. |
| `D04-PC061` | `UNTESTABLE` | Declared controlled failure stage/reason after preflight. |
| `D04-PC062` | `UNTESTABLE` | Declared controlled failure stage/reason after preflight. |
| `D04-PC063` | `UNTESTABLE` | Declared controlled failure stage/reason after preflight. |
| `D04-PC064` | `UNTESTABLE` | Declared controlled failure stage/reason after preflight. |
| `D04-PC065` | `UNTESTABLE` | Declared controlled failure stage/reason after preflight. |
| `D04-PC066` | `UNTESTABLE` | Declared controlled failure stage/reason after preflight. |

- Authority Shape, manifest, dependency or harness failures remain program `ERROR`; they cannot satisfy an expected business failure.

## pySHACL, SEMIC, ITB and Treehouse responsibilities

| Component | Responsibility | Current status |
|---|---|---|
| pySHACL | Locked local SHACL engine used by the independent harness; returns the report graph consumed by C-group classification and oracle checks. It does not approve releases. | `RUN / PASS` in current local evidence |
| SEMIC Validator | Optional external interoperability/validator evidence. A future run must record endpoint/tool version, request, response, report and mapping differences. | `NOT RUN` |
| DSSC ITB | Optional orchestration layer mapping test suite, test case, SUT and validation service; it may present the four business statuses after applying the agreed mapping. | `NOT RUN` |
| Semantic Treehouse | Optional modelling/import/export/publication evidence; independent from the required harness. | `NOT RUN` |

External output is supporting evidence. It does not silently replace the manifest oracle or change expected values. A disagreement is retained and reviewed by C/D/domain owners.

## Suggested ITB mapping

- ITB test suite: v0.4 Building Energy Metadata Profile, bound to the release and Shape hashes.
- ITB test case: one `D04-PCxxx` manifest record, preserving requirement IDs and expected business status.
- SUT: exactly the fixture or submitted Dataset graph bytes recorded for the run.
- Validation service: the selected pySHACL adapter or separately identified SEMIC service.
- Test outcome: program success/failure remains separate from `PASS`, `FAIL`, `INAPPLICABLE`, `UNTESTABLE` business status.

## D-group handoff checklist

- [ ] Verify the received D Shape path and SHA-256 above.
- [ ] Verify `v04-metadata-shapes` has the identical path/hash projection in the release manifest.
- [ ] Review [v0.4-requirements.json](manifests/v0.4-requirements.json) and [requirements-traceability.md](../docs/v0.4/requirements-traceability.md) for D04-R001–D04-R017.
- [ ] Review [v0.4-test-cases.json](manifests/v0.4-test-cases.json) and all 66 fixture hash bindings.
- [ ] Run the root `v0.4` command and confirm exit `0`, 66 discovered/executed, zero failed/skipped, and all four business statuses.
- [ ] Inspect focus node, result path, source Shape, constraint component, severity, message/value and count assertions for expected negative cases.
- [ ] Confirm target activation for every report-producing case and exact-one Dataset behavior for 0/1/2+ Dataset graphs.
- [ ] Confirm expected `FAIL` means a matched business oracle with program `SUCCESS`; harness `ERROR` remains non-zero.
- [ ] Confirm ADR-001 Closed Shape handling and ADR-003 record inheritance.
- [ ] Record any SEMIC or ITB execution only after it occurs; both currently remain `NOT RUN`.
- [ ] Preserve the D source, C release Shape, manifests and failed evidence unchanged while reviewing discrepancies.
