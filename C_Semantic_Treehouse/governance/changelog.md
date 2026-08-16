# Changelog

## v0.4 - D-Group Metadata Wire Profile

Classification: `wire-profile breaking` for metadata and `change: none` for the inherited v0.3 Energy Reading Record sub-contract.

Added and changed:

- Metadata target changes from v0.3 `be:DataProductMetadata` to `dcat:Dataset`.
- Dataset identity changes from `dct:identifier` to `ex:datasetId`.
- The metadata paths use the normative D-group `ex:/dct:/dcat:` contract, with `ex:` fixed to `https://example.org/dssc-energy#`.
- `be:providerName`, `be:endpointUrl`, `be:format`, `be:frequency`, `be:unit`, `be:spatialCoverage`, `be:temporalStart`, and `be:temporalEnd` migrate to the D-group paths documented in the deprecation policy.
- Format changes from the historical literal `JSON` to the exact v0.4 literal `application/json`.
- The submission graph must contain exactly one Dataset, and that Dataset must be an IRI.
- Required properties are single-valued; required strings reject empty and whitespace-only values.
- Frequency, unit, and format use exact case-sensitive enumerations.
- Endpoint and optional license values require HTTPS IRIs.
- `temporalStart` must not be later than `temporalEnd`.
- Description and license are explicitly optional and single-valued.
- Closed Shape warnings identify properties outside the allowed Dataset inventory and support the approved `INAPPLICABLE` mapping.
- Version identity and conformance are carried by release manifest and provenance; the constrained Dataset payload omits `dct:conformsTo`.
- v0.4 fixtures and the four-state harness cover `PASS`, `FAIL`, `INAPPLICABLE`, and `UNTESTABLE` outcomes.
- Phase 06 adds versioned SPARQL tests, calculated quality metrics, cumulative governance, and PROV-O-inspired provenance checks under the existing `all` suite.

Downstream impact:

- A Group must transform v0.3 metadata type, paths, format literal, and validation-sensitive values before emitting v0.4 metadata. The v0.3 record payload remains usable through the explicit inherited contract.
- B Group should reference the project v0.4 release IRI in offering or credential material outside the Closed Dataset payload and keep publication claims aligned with actual evidence.
- D Group retains its received Shape as the normative executable contract. The v0.4 model Shape is a byte-identical copy, and report assertions preserve source Shape, path, severity, constraint component, message, and result counts.

Compatibility boundary:

- Historical v0.1–v0.3 artifacts remain available and hash-frozen.
- The v0.3 metadata payload does not pass the v0.4 contract without transformation.
- The five record-specific v0.3 artifacts are inherited without copying or semantic change.

## v0.3 - Record Payload Schema Extension

Added:

- `be:EnergyReadingRecord` class.
- Energy Reading Record fields: `buildingId`, `meterId`, `timestamp`, `energyKWh`, `unit`, `location`.
- Record-level SHACL shape.
- Energy Reading Record JSON-LD context.
- Energy Reading Record JSON Schema.
- OpenAPI fragment for `GET /energy/buildings/hourly`.
- SPARQL competency questions covering metadata and record fields.

Compatibility:

- Additive extension from v0.2.
- Metadata constraints remain compatible with v0.2.
- A Group can attach the record schema to API/offering documentation.
- D Group can optionally validate record payloads without changing metadata validation.

## v0.2 - Stricter Metadata Constraints

Added:

- `endpointUrl`
- `unit`
- `temporalStart`
- `temporalEnd`
- controlled values for `format = JSON`, `frequency = hourly`, and `unit = kWh`
- invalid metadata example for validation failure demonstration

Compatibility:

- Stricter minor change from v0.1 with validation impact.
- A Group must include endpoint, unit, and temporal coverage in offering metadata.
- D Group must update SHACL shapes to reject incomplete v0.1-style metadata.

## v0.1 - Baseline Metadata

Added:

- `be:DataProductMetadata` class.
- baseline fields: `datasetId`, `providerName`, `format`, `frequency`, `spatialCoverage`.
- baseline metadata SHACL shape.
- JSON-LD context and valid metadata example.

Compatibility:

- Initial version.
