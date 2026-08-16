# Model Quality Assessment — v0.4

> This assessment is generated deterministically from validated manifests, the release-selected RDF/SHACL graphs, and the cumulative SSSOM table.

## Executive conclusion

The v0.4 D-group metadata contract has complete normative implementation, automated requirement, declared-field, requested constraint-category, and four-state case coverage in the current machine-readable authorities.

Compatibility classification: **INCOMPATIBLE_WIRE_PROFILE**.

v0.4 metadata is a wire-profile-breaking migration from the prior release; producers and consumers must migrate class, predicates, values, cardinality, HTTPS, blank-value, temporal-order, and closed-shape behavior.

The Energy Reading Record remains byte-bound to the inherited prior-release contract with change=none.

## Metric summary

| Metric | Numerator | Denominator | Ratio |
|---|---:|---:|---:|
| D-group normative requirement implementation coverage | 16 | 16 | 100.00% |
| Requirement automated-test coverage | 17 | 17 | 100.00% |
| Required and optional field coverage | 12 | 12 | 100.00% |
| Constraint-component distribution coverage | 8 | 8 | 100.00% |
| Four-state automated-case coverage | 4 | 4 | 100.00% |
| External-standard direct reuse and local-term mapping | 7 | 12 | 58.33% |
| Breaking-change fact coverage | 20 | 20 | 100.00% |
| Release and provenance metadata completeness | 15 | 15 | 100.00% |

## D-group normative requirement implementation coverage

Numerator: **16**

Denominator: **16**

Ratio: **100.00%**

Sources:

- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
- `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl`

Exclusions:

- D04-R017 is operational classification policy and is excluded from the normative SHACL denominator.

## Requirement automated-test coverage

Numerator: **17**

Denominator: **17**

Ratio: **100.00%**

Sources:

- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
- `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`

Exclusions:

- No registered requirement is excluded; operational classification D04-R017 remains in scope.

## Required and optional field coverage

Numerator: **12**

Denominator: **12**

Ratio: **100.00%**

Sources:

- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
- `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl`

Exclusions:

- Node-level cardinality, target, temporal-order, closed-shape, and operational-classification rules have no field path and are excluded.

Required fields: 10/10.

Optional fields: 2/2.

| Requirement | Shape | Path | Class | Represented |
|---|---|---|---|---|
| `D04-R003` | `ex:DatasetIdShape` | `ex:datasetId` | required | yes |
| `D04-R004` | `ex:TitleShape` | `dct:title` | required | yes |
| `D04-R005` | `ex:ProviderNameShape` | `ex:providerName` | required | yes |
| `D04-R006` | `ex:SpatialShape` | `dct:spatial` | required | yes |
| `D04-R007` | `ex:FrequencyShape` | `dct:accrualPeriodicity` | required | yes |
| `D04-R008` | `ex:UnitShape` | `ex:unit` | required | yes |
| `D04-R009` | `ex:FormatShape` | `dct:format` | required | yes |
| `D04-R010` | `ex:EndpointUrlShape` | `dcat:endpointURL` | required | yes |
| `D04-R011` | `ex:TemporalStartShape` | `ex:temporalStart` | required | yes |
| `D04-R012` | `ex:TemporalEndShape` | `ex:temporalEnd` | required | yes |
| `D04-R014` | `ex:DescriptionShape` | `dct:description` | optional | yes |
| `D04-R015` | `ex:LicenseShape` | `dct:license` | optional | yes |

## Constraint-component distribution coverage

Numerator: **8**

Denominator: **8**

Ratio: **100.00%**

Sources:

- `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl`

Exclusions:

- Target declarations, names, messages, severities, ignored properties, minLength, and nested sh:property wiring are outside the requested eight-category distribution.

| Constraint category | Occurrences | Distribution denominator | Share |
|---|---:|---:|---:|
| `closed` | 1 | 47 | 2.13% |
| `datatype` | 10 | 47 | 21.28% |
| `in` | 3 | 47 | 6.38% |
| `max_count` | 12 | 47 | 25.53% |
| `min_count` | 10 | 47 | 21.28% |
| `node_kind` | 3 | 47 | 6.38% |
| `pattern` | 6 | 47 | 12.77% |
| `sparql` | 2 | 47 | 4.26% |

## Four-state automated-case coverage

Numerator: **4**

Denominator: **4**

Ratio: **100.00%**

Sources:

- `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`

Exclusions:

- Harness PROGRAM ERROR controls are evidence for fail-closed execution and are excluded from the four business-state denominator.

Automated case counts:

- `PASS`: 6
- `FAIL`: 53
- `INAPPLICABLE`: 1
- `UNTESTABLE`: 6

## External-standard direct reuse and local-term mapping

Numerator: **7**

Denominator: **12**

Ratio: **58.33%**

Sources:

- `C_Semantic_Treehouse/mappings/external-standard-alignment.sssom.tsv`
- `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl`

Exclusions:

- RDF/SHACL vocabulary terms, rdf:type, ignored-properties inventory, and the inherited record contract are excluded from the v0.4 metadata field denominator.

Direct external field reuse: 7/12.

Direct-reuse SSSOM audit coverage: 7/7.

Local ex:* term mapping coverage: 5/5.

## Breaking-change fact coverage

Numerator: **20**

Denominator: **20**

Ratio: **100.00%**

Sources:

- `C_Semantic_Treehouse/manifests/release-manifest.json`
- `C_Semantic_Treehouse/mappings/external-standard-alignment.sssom.tsv`
- `C_Semantic_Treehouse/model/v0.3/data-product-context.jsonld`
- `C_Semantic_Treehouse/model/v0.3/data-product-valid.jsonld`
- `C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld`
- `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl`
- `C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld`

Exclusions:

- Business-domain acceptance and downstream deployment observations remain pending human/external evidence and are excluded from machine-verified facts.

## Release and provenance metadata completeness

Numerator: **15**

Denominator: **15**

Ratio: **100.00%**

Sources:

- `C_Semantic_Treehouse/manifests/release-manifest.json`
- `C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json`
- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
- `C_Semantic_Treehouse/manifests/validation-suites.json`

Exclusions:

- Pending human approvals, CI runs, external publication, and Semantic Treehouse execution are excluded because they have not occurred.

## Breaking-change facts

| ID | Verified fact | Status | Evidence basis |
|---|---|---|---|
| `BC-01` | be:DataProductMetadata migrates to dcat:Dataset. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-02` | dct:identifier migrates to ex:datasetId. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-03` | be:providerName migrates to ex:providerName. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-04` | be:endpointUrl migrates to dcat:endpointURL. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-05` | be:format migrates to dct:format. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-06` | be:frequency migrates to dct:accrualPeriodicity. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-07` | be:unit migrates to ex:unit. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-08` | be:spatialCoverage migrates to dct:spatial. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-09` | be:temporalStart migrates to ex:temporalStart. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-10` | be:temporalEnd migrates to ex:temporalEnd. | VERIFIED | Prior/current contexts plus the cumulative migration row. |
| `BC-11` | The format token changes from JSON to application/json. | VERIFIED | Prior/current release examples and ex:FormatShape sh:in list. |
| `BC-12` | Endpoint and supplied license IRIs require HTTPS. | VERIFIED | Actual v0.4 SHACL pattern constraints. |
| `BC-13` | Each submission graph must contain exactly one dcat:Dataset. | VERIFIED | Actual v0.4 DatasetCardinalityShape SPARQL constraint. |
| `BC-14` | All twelve declared metadata fields are single-valued. | VERIFIED | Actual v0.4 named PropertyShapes and sh:maxCount values. |
| `BC-15` | Required free-text identifiers and labels reject empty or whitespace-only values. | VERIFIED | Actual v0.4 minLength and non-whitespace pattern constraints. |
| `BC-16` | temporalStart must not be later than temporalEnd. | VERIFIED | Actual v0.4 TemporalOrderShape SPARQL constraint. |
| `BC-17` | Undeclared Dataset properties activate the closed-shape Warning behavior. | VERIFIED | Actual v0.4 DatasetClosedShape closed flag and severity. |
| `BC-18` | The Energy Reading Record contract remains the actual prior-release contract unchanged. | VERIFIED | Current release-manifest inherited record artifacts and their byte bindings. |
| `BC-19` | description and license are explicit optional single-valued fields. | VERIFIED | Actual v0.4 optional PropertyShapes. |
| `BC-20` | The release classifies the metadata migration as wire-profile-breaking. | VERIFIED | Validated release-manifest compatibilityClassification. |

## Cumulative SSSOM audit

The table contains 47 rows. It separates migration, direct reuse, local external alignment, and inherited record alignment. Review-state distribution is `{"PENDING_DOMAIN_REVIEW": 47}`.

Record-layer mappings cover SOSA, SSN, QUDT, UCUM-coded representation, and OWL-Time. Confidence values express curation confidence; they do not represent external approval.

## Release/provenance completeness

| ID | Assertion | Complete |
|---|---|---|
| `RP-01` | current release identifier | yes |
| `RP-02` | release status | yes |
| `RP-03` | version IRI | yes |
| `RP-04` | release root | yes |
| `RP-05` | prior release | yes |
| `RP-06` | compatibility classification | yes |
| `RP-07` | normative input references | yes |
| `RP-08` | applicable validator references | yes |
| `RP-09` | complete requirement binding | yes |
| `RP-10` | artifact identity/hash/media completeness | yes |
| `RP-11` | artifact provenance type | yes |
| `RP-12` | derived source path/hash provenance | yes |
| `RP-13` | inherited source/change provenance | yes |
| `RP-14` | source catalog path/hash provenance | yes |
| `RP-15` | suite registry version/hash binding | yes |

## Interpretation boundary

These ratios measure coverage of declared contracts and auditable mappings. Domain adequacy, external standards-body endorsement, deployment compatibility, human approval, CI publication, and Semantic Treehouse execution require their own evidence tracks.

All mapping rows remain pending domain review. The machine checks establish structural validity, traceability, selected predicate semantics, and complete coverage of the required migration inventory.
