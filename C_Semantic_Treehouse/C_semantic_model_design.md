# C Semantic Model Design — v0.4

## Scope（范围）

This package governs the Building Energy Consumption Data Product identified by `building-energy-hourly-v1`. The Dataset ID is a business identifier and remains independent of the repository release sequence `v0.1`–`v0.4`.

The model has two deliberately separate layers:

1. a v0.4 `dcat:Dataset` metadata wire profile derived from the frozen D-group SHACL contract; and
2. the Energy Reading Record payload contract inherited byte-for-byte from v0.3.

The scope supports catalogue/offering metadata, semantic review, deterministic validation, provenance and A/B/D-group handoff. It does not define a complete building-energy ontology, a production catalogue protocol, credentials, access control, billing, or legal compliance.

## DSSC architecture position

The provider emits Dataset metadata and API records. C Group maintains the semantic release, mappings, manifests, tests and governance evidence. A Group consumes the v0.4 metadata paths when assembling an offering. B Group may cite the release IRI and provenance outside the Closed Dataset payload. D Group owns the normative Shape and reviews validation semantics. The repository validation harness supplies repeatable local evidence before any publication decision.

The model therefore connects four concerns without merging their authority:

- the D-group Shape defines executable metadata constraints;
- the release manifest defines artifact identity, version relations and hashes;
- the test manifests define expected validation behavior;
- human semantic, domain and release reviewers decide whether the evidence is acceptable for release.

## Two-layer model（两层模型）

### Layer 1 — v0.4 Dataset metadata

The v0.4 wire target is exactly `dcat:Dataset`. It uses the D-group contract namespace `ex:` = `https://example.org/dssc-energy#` together with direct DCAT and DCTERMS paths. The release identity is `https://w3id.org/dssc-demo/building-energy/v0.4`; that IRI identifies the project release and does not rewrite payload vocabulary.

### Layer 2 — inherited v0.3 Energy Reading Record

The D-group input contains no Energy Reading Record target or record-field constraints. Under [ADR-003](../docs/v0.4/decisions/ADR-003-energy-record-inheritance.md), v0.4 reuses five v0.3 record artifacts at their original paths and hashes. The record remains `be:EnergyReadingRecord` with required single values for `be:buildingId`, `be:meterId`, `be:timestamp`, `be:energyKWh`, `be:unit` and `be:location`. The JSON Schema also requires `location.city` and `location.district`, a date-time timestamp, non-negative numeric energy, and `unit = "kWh"`.

Metadata `ex:unit` and record `be:unit` are distinct IRIs. The frozen v0.3 OpenAPI fragment remains historical inventory; it is outside the exact five-artifact inheritance set.

## D-group contract and derivation

The normative input is `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`, SHA-256 `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`. C Group's released metadata Shape is a byte-copy with the same SHA-256. The machine-readable interpretation is [v0.4-requirements.json](manifests/v0.4-requirements.json); the human-readable projection is [requirements-traceability.md](../docs/v0.4/requirements-traceability.md).

The accepted decisions are:

- [ADR-001](../docs/v0.4/decisions/ADR-001-dct-conforms-to.md): omit `dct:conformsTo` from the Closed v0.4 Dataset payload and carry release identity in the release manifest and provenance;
- [ADR-002](../docs/v0.4/decisions/ADR-002-wire-profile-and-version-identity.md): preserve the D-group `ex:/dcat:/dct:` wire IRIs and classify v0.3 → v0.4 metadata as wire-profile breaking;
- [ADR-003](../docs/v0.4/decisions/ADR-003-energy-record-inheritance.md): inherit the five v0.3 record artifacts without copying or semantic change.

## v0.4 field, IRI, datatype and cardinality projection

This table is an explanatory projection of the D-group TTL and requirements manifest. Those machine-readable sources remain authoritative.

| JSON key | RDF IRI | RDF value kind / datatype | Cardinality | Allowed value or additional rule |
|---|---|---|---|---|
| `datasetId` | `ex:datasetId` | `xsd:string` | 1..1 | At least one non-whitespace character |
| `title` | `dct:title` | `xsd:string` | 1..1 | At least one non-whitespace character |
| `providerName` | `ex:providerName` | `xsd:string` | 1..1 | At least one non-whitespace character |
| `spatial` | `dct:spatial` | `xsd:string` | 1..1 | At least one non-whitespace character |
| `frequency` | `dct:accrualPeriodicity` | `xsd:string` | 1..1 | Exact, case-sensitive `hourly` |
| `unit` | `ex:unit` | `xsd:string` | 1..1 | Exact, case-sensitive `kWh` |
| `temporalStart` | `ex:temporalStart` | `xsd:date` | 1..1 | Must not be later than `temporalEnd` |
| `temporalEnd` | `ex:temporalEnd` | `xsd:date` | 1..1 | Must not be earlier than `temporalStart` |
| `endpointUrl` | `dcat:endpointURL` | IRI | 1..1 | IRI string must start with `https://` |
| `format` | `dct:format` | `xsd:string` | 1..1 | Exact `application/json` |
| `description` | `dct:description` | `xsd:string` | 0..1 | No minimum-length constraint in the received Shape |
| `license` | `dct:license` | IRI | 0..1 | If present, IRI string must start with `https://` |

The submission graph must contain exactly one `dcat:Dataset`, and that Dataset must be an IRI. `rdf:type` is ignored by the Closed Shape. The twelve paths above form the complete allowed Dataset-property inventory.

## JSON-LD serialization

[data-product-context.jsonld](model/v0.4/data-product-context.jsonld) maps compact JSON keys directly to the normative IRIs and assigns `@id` coercion to `license` and `endpointUrl` plus `xsd:date` coercion to the temporal keys. [data-product-valid.jsonld](model/v0.4/data-product-valid.jsonld) uses a repository-local sibling context, so the core harness expands it without a network request.

The canonical example emits one IRI-identified Dataset, Dataset ID `building-energy-hourly-v1`, exact values `hourly`, `kWh`, and `application/json`, HTTPS endpoint and license IRIs, and ordered dates. It does not emit `dct:conformsTo`, following ADR-001.

## SHACL constraint strategy

The released Shape combines property, node and graph constraints:

- `ex:DatasetCardinalityShape` uses SHACL-SPARQL to require exactly one Dataset in the submitted graph;
- `ex:BuildingEnergyDatasetShape` targets `dcat:Dataset`, requires an IRI focus node and attaches twelve named PropertyShapes;
- required strings combine `sh:minCount`, `sh:maxCount`, `sh:datatype`, `sh:minLength` and `sh:pattern`;
- fixed values use single-value `sh:in` lists, preventing a valid extra value from hiding an invalid value;
- endpoint and license rules combine IRI node kind with an HTTPS pattern;
- `ex:TemporalOrderShape` uses SHACL-SPARQL and permits equal start/end dates;
- `ex:DatasetClosedShape` allows only the twelve declared paths plus ignored `rdf:type`; its `sh:Warning` maps to `INAPPLICABLE` only when no Violation exists.

The deterministic business-status precedence is `UNTESTABLE`, `FAIL`, `INAPPLICABLE`, `PASS`. Program `SUCCESS` means the harness completed and actual status matched the reviewed oracle. Missing tests, skipped required cases, authority or manifest failure, report-structure failure, or an expected/actual mismatch yields program `ERROR` and a non-zero exit.

## Record contract

The inherited v0.3 record contract remains a separate validation target. SHACL requires one value for each record field, `xsd:dateTime` for `timestamp`, non-negative `energyKWh`, `unit = "kWh"`, and a blank-node-or-IRI `location`. Draft 7 JSON Schema additionally closes the JSON object, validates the timestamp format and closes the nested location object. Record examples may retain their v0.3 `dct:conformsTo` value because `ex:DatasetClosedShape` targets only `dcat:Dataset`.

## Standards reuse and mappings

The wire profile directly reuses `dcat:Dataset`, `dcat:endpointURL`, `dct:title`, `dct:spatial`, `dct:accrualPeriodicity`, `dct:format`, `dct:description` and `dct:license`. Local D-contract terms remain exact `ex:*` paths. The inherited record retains the project `be:*` namespace.

[external-standard-alignment.sssom.tsv](mappings/external-standard-alignment.sssom.tsv) records migration, direct reuse and reviewed-strength mappings to DCTERMS, DCAT, SOSA/SSN, QUDT/UCUM, OWL-Time and schema.org. Phase 06 machine evidence validated 47 rows with no duplicate or unjustified self-mapping. All 47 rows remain `PENDING_DOMAIN_REVIEW`; mapping confidence does not upgrade them to approved domain semantics.

## Competency questions

The semantic test manifest is [sparql-test-cases.json](tests/sparql/sparql-test-cases.json). Phase 06 executed 20/20 required questions with no failure or skip:

- eight frozen v0.3 questions cover identifier, provider, endpoint, format/frequency, unit, coverage, v0.3 conformance and record fields;
- twelve v0.4 questions cover Dataset count and IRI identity, core metadata, distribution values, temporal values/order, optional fields, profile/version binding, named Shapes, constraint components, Closed Shape inventory and inherited record behavior.

The deterministic result is `build/validation/sparql/results.json`. That generated file is current machine evidence; the query manifest and expected files remain the oracle.

## Release-manifest artifact projection

The following five-column table is copied from the `v0.4` release entry in [release-manifest.json](manifests/release-manifest.json). It is a checked projection; the manifest remains the only artifact truth source.

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

## Current evidence and limitations（局限）

Phase 05 executed 66/66 v0.4 cases: 6 `PASS`, 53 `FAIL`, 1 `INAPPLICABLE`, and 6 `UNTESTABLE`, all with program `SUCCESS`. Phase 06 executed 20/20 SPARQL questions, eight calculated quality metrics and 21/21 governance checks. These are local machine results, not a final release approval.

Current limitations are explicit:

- provider and spatial coverage remain flat strings;
- `kWh` is a constrained literal rather than a QUDT or UCUM identifier;
- temporal coverage uses two dates rather than an OWL-Time interval node;
- the metadata profile models a direct endpoint property and does not introduce a full DCAT Distribution/DataService graph;
- the contract namespace `https://example.org/dssc-energy#` is retained exactly from D Group and is not presented as a production namespace decision;
- SSSOM domain review, final C/D review, Domain Reviewer review and release approval remain pending;
- the current v0.4 Semantic Treehouse projection records deployment, workload, import, export and SHACL execution as `PASS`, runtime as `PAUSED`, and only Treehouse publication as `NOT RUN`; external SEMIC and ITB remain `DEFERRED` / `NOT RUN`.

## Future work（后续工作）

Future changes require a new reviewed contract and release identity. Candidate work includes richer organization and place nodes, QUDT/UCUM unit resources, OWL-Time intervals, DCAT Distribution/DataService modeling, a new record contract if requirements change, approved domain mappings, and explicit adapters for legacy payloads. Phase 08 preserves optional external-tool evidence boundaries. Confirmed Phase 09 candidates complete the technical clean-room, CI and repository-publication chain; every candidate with changed tracked content must independently repeat §§6.9–6.11, and its effective state follows the latest appended record in [`STATUS.md`](../docs/v0.4/STATUS.md). The maintainer has accepted P00-R14's final human-governance responsibilities, so the risk is an `ACCEPTED_LIMITATION`; the pending item-level review records remain future work.
