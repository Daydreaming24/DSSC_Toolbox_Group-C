# Phase 1 Summary

## Files Created or Modified

Created v0.1 artifacts:

- `model/v0.1/building-energy-ontology.ttl`
- `model/v0.1/data-product-metadata-shapes.ttl`
- `model/v0.1/data-product-context.jsonld`
- `model/v0.1/data-product-valid.jsonld`

Created v0.2 artifacts:

- `model/v0.2/building-energy-ontology.ttl`
- `model/v0.2/data-product-metadata-shapes.ttl`
- `model/v0.2/data-product-context.jsonld`
- `model/v0.2/data-product-valid.jsonld`
- `model/v0.2/data-product-invalid.jsonld`

Created v0.3 artifacts:

- `model/v0.3/building-energy-ontology.ttl`
- `model/v0.3/data-product-metadata-shapes.ttl`
- `model/v0.3/energy-reading-record-shapes.ttl`
- `model/v0.3/data-product-context.jsonld`
- `model/v0.3/energy-reading-record-context.jsonld`
- `model/v0.3/data-product-valid.jsonld`
- `model/v0.3/energy-reading-record-valid.jsonld`
- `model/v0.3/energy-reading-record-invalid.jsonld`
- `model/v0.3/energy-reading-record.schema.json`
- `model/v0.3/openapi-fragment.yaml`

Created validation support:

- `scripts/phase1_validate.py`

Modified:

- root `Makefile`
- root `make.cmd`

## Version Evolution

v0.1 defines the baseline `be:DataProductMetadata` model with:

- `datasetId` mapped to `dct:identifier`
- `providerName`
- `format`
- `frequency`
- `spatialCoverage`

v0.2 adds stricter metadata constraints:

- `endpointUrl`
- `unit`
- `temporalStart`
- `temporalEnd`
- controlled values for `format = JSON`, `frequency = hourly`, and `unit = kWh`
- invalid example missing `providerName`, using `MWh`, and missing `temporalEnd`

v0.3 keeps the v0.2 metadata model and adds:

- `be:EnergyReadingRecord`
- record-level SHACL shape
- JSON-LD context for record payloads
- JSON Schema for API record payloads
- OpenAPI fragment for `GET /energy/buildings/hourly`

## Commands Run

- `cmd /c make validate-rdf`
- `cmd /c make validate-jsonld`
- `cmd /c make validate-jsonschema`
- `cmd /c make validate-openapi`
- `cmd /c make validate`

## Pass/Fail Status

Passed:

- All Turtle files parsed with `rdflib`.
- All JSON-LD files parsed as valid JSON.
- `energy-reading-record.schema.json` passed JSON Schema Draft 7 schema checks.
- `energy-reading-record-valid.jsonld` passed the JSON Schema.
- `energy-reading-record-invalid.jsonld` failed as expected because `meterId` is missing.
- `openapi-fragment.yaml` parsed with PyYAML and contains required top-level `openapi`, `info`, and `paths` keys.
- The combined `cmd /c make validate` command exits successfully.

Deferred:

- Full JSON-LD expansion is deferred to Phase 2 because `pyld` is not installed in this environment.
- Real SHACL conformance checking is deferred to Phase 2. The current `validate-shacl` target remains a stub until the pySHACL harness is added.
- SPARQL tests, quality metrics, and evidence collection remain stubs for later phases.

## Remaining Risks

- The v0.3 `unit` property uses a simple literal token `kWh`; richer QUDT/UCUM URI alignment is documented as a later mapping/governance concern.
- The local Semantic Treehouse evidence track has not started yet.
- The current workspace is not a git repository, so no commit was created.
