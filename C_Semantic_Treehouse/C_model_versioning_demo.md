# C Model Versioning Demo — v0.1 to v0.4

## Version identity and compatibility meaning

The project release sequence is `v0.1`, `v0.2`, `v0.3`, `v0.4`, identified by `https://w3id.org/dssc-demo/building-energy/v0.x`. These labels order this repository's semantic-model releases. They do not promise Semantic Versioning compatibility. In particular, the decimal label `v0.4` does not make the v0.3 → v0.4 migration “minor” or backward compatible. This is both a `wire-profile breaking` and `wire profile breaking` transition（不兼容 wire profile 迁移）.

The stable Dataset ID `building-energy-hourly-v1` is a business identifier and does not change with the model release. Release identity belongs in the [release manifest](manifests/release-manifest.json) and [provenance record](governance/provenance.jsonld). The v0.4 Closed Dataset payload omits `dct:conformsTo` under [ADR-001](../docs/v0.4/decisions/ADR-001-dct-conforms-to.md).

## Evolution

### v0.1 — initial metadata contract

v0.1 introduced `be:DataProductMetadata`, a JSON-LD context, SHACL metadata Shape and a valid example. Its baseline metadata covered identifier, provider, format, frequency and spatial coverage. The release manifest classifies it as `initial`.

### v0.2 — validation tightening

v0.2 added endpoint, unit and temporal start/end requirements; constrained `format = "JSON"`, `frequency = "hourly"` and `unit = "kWh"`; and added an intentional negative example. Existing v0.1-style metadata may fail the new required-field and value rules. The release manifest classifies the transition as `validation-tightening`.

### v0.3 — additive record layer

v0.3 retained the v0.2 metadata wire contract and added `be:EnergyReadingRecord`, its JSON-LD context, SHACL Shape, Draft 7 JSON Schema, positive/negative records and an OpenAPI fragment. The release manifest classifies the transition as `additive`.

### v0.4 — D-group metadata wire profile

v0.4 replaces the metadata wire profile with the frozen D-group `dcat:Dataset` contract. Type, namespace, paths, one value, required/optional distinction, exact lexical values, HTTPS rules, blank-string handling, temporal ordering, graph cardinality and Closed Shape behavior all participate in compatibility. The release manifest classifies v0.3 → v0.4 as `wire-profile-breaking`.

The Energy Reading Record does not change. Five record-specific v0.3 artifacts are inherited at their original path and SHA-256 with `change: none`, as approved by [ADR-003](../docs/v0.4/decisions/ADR-003-energy-record-inheritance.md).

## Compatibility matrix

| Release / transition | Manifest classification | Metadata compatibility | Record compatibility | Required consumer action |
|---|---|---|---|---|
| v0.1 | `initial` | Initial baseline | No record contract | Adopt the baseline fields and version identity. |
| v0.1 → v0.2 | `validation-tightening` | Older metadata can fail added required fields and fixed values | No record contract | Add endpoint, unit and temporal coverage; satisfy exact values. |
| v0.2 → v0.3 | `additive` | v0.2 metadata contract retained | New record contract introduced | Metadata consumers may remain unchanged; record consumers adopt the new schema/Shape if used. |
| v0.3 → v0.4 | `wire-profile-breaking` | Incompatible without explicit transformation | Five record artifacts remain unchanged | Transform every metadata payload; preserve record bytes and semantics. |

The detailed reviewed comparison is [compatibility-v0.3-v0.4.md](../docs/v0.4/compatibility-v0.3-v0.4.md). The D-group TTL and requirements manifest remain the constraint truth sources.

## v0.3 → v0.4 namespace, path and value migration

`be:` remains `https://w3id.org/dssc-demo/building-energy#` for historical releases and the inherited record. v0.4 metadata uses `ex:` = `https://example.org/dssc-energy#` exactly as received, plus direct DCAT/DCTERMS reuse. No alias or dual-profile adapter is implied.

| Semantic role | v0.3 wire | v0.4 wire / value | Required migration |
|---|---|---|---|
| RDF type | `be:DataProductMetadata` | `dcat:Dataset`, focus node is an IRI | Emit the direct type; do not depend on subclass inference. |
| Dataset ID | `dct:identifier` | `ex:datasetId` | Move one non-blank string to the new path. |
| Title | Not required by the old metadata Shape | `dct:title` | Add one non-blank string. |
| Provider | `be:providerName` | `ex:providerName` | Change path and retain one non-blank string. |
| Spatial coverage | `be:spatialCoverage` | `dct:spatial` | Change path and retain one non-blank string. |
| Frequency | `be:frequency = "hourly"` | `dct:accrualPeriodicity = "hourly"` | Change path; preserve exact case-sensitive value. |
| Metadata unit | `be:unit = "kWh"` | `ex:unit = "kWh"` | Change namespace; keep it separate from record `be:unit`. |
| Format | `be:format = "JSON"` | `dct:format = "application/json"` | Change both path and lexical value. |
| Endpoint | `be:endpointUrl`, IRI | `dcat:endpointURL`, HTTPS IRI | Change path and require one `https://` IRI. |
| Temporal range | `be:temporalStart` / `be:temporalEnd` | `ex:temporalStart` / `ex:temporalEnd` | Change paths, retain single `xsd:date` values and enforce start ≤ end. |
| Description | Undeclared | Optional `dct:description` | Omit or supply at most one `xsd:string`. |
| License | Undeclared | Optional `dct:license` | Omit or supply at most one HTTPS IRI. |
| Version marker | Dataset `dct:conformsTo` | Release manifest / provenance | Remove it from the Closed Dataset payload. |
| Submission boundary | No exact Dataset count or Closed Shape | Exactly one Dataset; twelve allowed property paths | Isolate the submitted graph and remove undeclared Dataset properties. |

An undeclared Dataset property produces the approved Closed Shape Warning. With no Violation it maps to `INAPPLICABLE`; with any Violation the result is `FAIL`. A SUT parse/load or controlled post-preflight runtime fault maps to `UNTESTABLE`. Authority, dependency, manifest, harness or oracle failure remains program `ERROR`.

## Record reuse and identity（继承）

The v0.4 release manifest references these existing v0.3 files directly:

- `energy-reading-record.schema.json`;
- `energy-reading-record-context.jsonld`;
- `energy-reading-record-shapes.ttl`;
- `energy-reading-record-valid.jsonld`;
- `energy-reading-record-invalid.jsonld`.

They remain `be:EnergyReadingRecord` artifacts with the v0.3 namespace and validation meaning. Copying them into `model/v0.4/` would create a misleading new identity without semantic change. The historical v0.3 ontology supplies record-term provenance; that does not make the whole v0.3 metadata bundle compatible with v0.4.

## Deprecation policy（弃用）

Historical releases remain immutable and addressable. Deprecation is documented through [deprecation-policy.md](governance/deprecation-policy.md) and [changelog.md](governance/changelog.md). A replacement proposal must identify the old and new IRI, affected releases/artifacts, transformation, compatibility impact, fixtures/tests, mappings and downstream owners.

Removal, datatype or cardinality change, namespace/path change, validation-sensitive lexical change and stronger Closed Shape behavior are evaluated as breaking risks. A future adapter or record revision requires its own requirement, decision, version, manifest entry and regression evidence.

## A/B/D-group impact

### A Group（A 组）

A Group must emit the v0.4 Dataset type, twelve allowed paths and strict values. It must transform legacy metadata, omit `dct:conformsTo` from the Dataset, use HTTPS endpoint/license IRIs and preserve the unchanged record contract when describing the API payload.

### B Group（B 组）

B Group may cite `https://w3id.org/dssc-demo/building-energy/v0.4`, release/artifact hashes and provenance in offering or credential material outside the Closed Dataset graph. Publication, trust and Gaia-X/legal compliance claims require their own authority and evidence; the model version alone proves none of them.

### D Group（D 组）

D Group continues to treat the received TTL as normative. C Group's release Shape is a byte-copy. D-group validation should assert focus node, path, source Shape, constraint component, severity, message/value and result counts against the test manifest, and keep expected business failures separate from harness errors.

## Release-manifest artifact projection

The table below is copied from the `v0.4` release entry in [release-manifest.json](manifests/release-manifest.json). It is automatically checkable and is not a second artifact registry.

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

## Evidence and current boundary

The frozen baseline suite protects v0.1–v0.3. Phase 05 executed all 66 v0.4 fixtures and Phase 06 calculated 20/20 verified breaking-change facts, concluding `INCOMPATIBLE_WIRE_PROFILE` for metadata and `change: none` for the record. The isolated Treehouse track has local deployment/import/SHACL evidence while its publication remains `NOT RUN`; SEMIC and ITB remain `DEFERRED` / `NOT RUN`. Confirmed Phase 09 candidates complete repository publication, candidate-bound CI and remote clean-clone validation; every candidate with changed tracked content must independently repeat §§6.9–6.11. The effective state follows the latest appended record in [`STATUS.md`](../docs/v0.4/STATUS.md). The maintainer accepted the P00-R14 final human-governance responsibilities; historical and artifact-level `PENDING` review values remain truthful limitations rather than completed item-level sign-offs.
