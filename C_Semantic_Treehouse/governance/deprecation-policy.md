# Deprecation and Migration Policy

## Historical Retention

v0.1, v0.2, and v0.3 remain immutable historical releases. Their ontology, contexts, Shapes, examples, schemas, OpenAPI fragment, competency questions, and expected results retain their original paths and SHA-256 bindings. Historical terms continue to document the meaning of archived payloads and provide regression oracles.

Deprecation documentation never removes a released term. A later removal, datatype change, semantic change, or validation-sensitive lexical change requires a versioned decision, explicit compatibility classification, transformed fixtures, and regression evidence.

## v0.3 to v0.4 Metadata Migration

The metadata transition is a wire-profile breaking migration. Implementers must transform type, paths, values, and behavior as follows:

| v0.3 contract | v0.4 contract | Migration guidance |
|---|---|---|
| `be:DataProductMetadata` | `dcat:Dataset` | Emit exactly one Dataset and give it an IRI. |
| `dct:identifier` | `ex:datasetId` | Move the single non-blank string value to the D-group path. |
| `be:providerName` | `ex:providerName` | Move one non-blank string value. |
| `be:endpointUrl` | `dcat:endpointURL` | Rename the path and emit one HTTPS IRI. |
| `be:format = "JSON"` | `dct:format = "application/json"` | Rename the path and normalize the exact case-sensitive media-type literal. |
| `be:frequency` | `dct:accrualPeriodicity` | Rename the path and emit exactly `hourly`. |
| metadata `be:unit` | metadata `ex:unit` | Rename the metadata path and emit exactly `kWh`. |
| `be:spatialCoverage` | `dct:spatial` | Rename the path and emit one non-blank string. |
| `be:temporalStart` | `ex:temporalStart` | Rename the path and emit one `xsd:date`. |
| `be:temporalEnd` | `ex:temporalEnd` | Rename the path, emit one `xsd:date`, and preserve start ≤ end. |
| payload `dct:conformsTo` | release manifest and provenance | Remove it from the Closed v0.4 Dataset payload and carry release identity outside that payload. |
| no explicit optional rule | `dct:description` / `dct:license` | Omit or emit at most one valid value; license requires an HTTPS IRI. |

The transformation also enforces single-value constraints, blank-string rejection, case-sensitive enumerations, HTTPS, temporal ordering, and the Closed Shape inventory. Extra Dataset properties produce the approved Warning and may yield `INAPPLICABLE`.

No implicit alias equates the historical `be:` paths with the D-group `ex:/dct:/dcat:` paths. A dual-profile adapter requires a new requirement and independent tests.

## Energy Reading Record

The five record-specific v0.3 artifacts are inherited in v0.4 with `change: none`:

- `energy-reading-record.schema.json`
- `energy-reading-record-context.jsonld`
- `energy-reading-record-shapes.ttl`
- `energy-reading-record-valid.jsonld`
- `energy-reading-record-invalid.jsonld`

Record terms such as `be:buildingId`, `be:meterId`, `be:timestamp`, `be:energyKWh`, record `be:unit`, and `be:location` retain v0.3 meaning. The metadata `ex:unit` and record `be:unit` are distinct properties. The historical v0.3 OpenAPI fragment remains frozen inventory and is outside the exact five-artifact inheritance set.

## Change Proposal Requirements

A proposal that deprecates or replaces a field must record:

- old and replacement IRI;
- affected versions and artifacts;
- reason and semantic transformation;
- first deprecated and last supported version when known;
- validation, fixture, mapping, quality, and downstream impact;
- A/B/D group handoff effect;
- human review status and release evidence.

D Group receives updated normative Shapes before new enforcement. A Group receives transformation guidance before new connector metadata is expected. B Group receives the release identity and publication boundary when credential or offering references are affected.
