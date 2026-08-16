# Expected Validation Results

## RDF

All Turtle artifacts in `model/v0.1`, `model/v0.2`, and `model/v0.3` should parse successfully.

## JSON-LD

All JSON-LD contexts and examples should parse as JSON and expand through JSON-LD processing. Local sibling context files are inlined by the validation harness so validation does not depend on network access.

## SHACL

Expected conforming cases:

- `model/v0.1/data-product-valid.jsonld` conforms to `model/v0.1/data-product-metadata-shapes.ttl`.
- `model/v0.2/data-product-valid.jsonld` conforms to `model/v0.2/data-product-metadata-shapes.ttl`.
- `model/v0.3/data-product-valid.jsonld` conforms to `model/v0.3/data-product-metadata-shapes.ttl`.
- `model/v0.3/energy-reading-record-valid.jsonld` conforms to `model/v0.3/energy-reading-record-shapes.ttl`.

Expected failing case:

- `model/v0.2/data-product-invalid.jsonld` must fail because:
  - `providerName` is missing.
  - `unit` is `MWh` instead of `kWh`.
  - `temporalEnd` is missing.

This expected failure is a successful harness outcome.

## JSON Schema

Expected conforming case:

- `model/v0.3/energy-reading-record-valid.jsonld` conforms to `model/v0.3/energy-reading-record.schema.json`.

Expected failing case:

- `model/v0.3/energy-reading-record-invalid.jsonld` must fail because it violates required field, type/format, and unit constraints:
  - `meterId` is missing.
  - `timestamp` is not a valid `date-time`.
  - `energyKWh` is a string instead of a number.
  - `unit` is `MWh` instead of `kWh`.

This expected failure is a successful harness outcome.

## OpenAPI

`model/v0.3/openapi-fragment.yaml` should parse as YAML and pass the complete `openapi-spec-validator` validation. A missing or failed validator is a program error; a shallow YAML/top-level-key check is insufficient.

## Baseline Execution Contract

`manifests/baseline-test-cases.json` and its schema are the machine-readable execution contract for the frozen v0.1-v0.3 baseline. Expected values are reviewed inputs and are never generated or rewritten from actual validator output.

- The required set is exactly 7 RDF, 10 JSON-LD, 5 SHACL, 2 JSON Schema, 1 OpenAPI, and 8 SPARQL cases. Zero discovery, a disabled required case, or any skipped case is a program error.
- Business `PASS`/`FAIL` is recorded separately from program `SUCCESS`/`ERROR`. The two intended negative examples have business `FAIL` and program `SUCCESS` only when every declared oracle matches with no unexpected critical result.
- JSON-LD processing uses only manifest-bound sibling contexts through a network-denying document loader.
- Every SHACL case uses explicit `inference=none`, `advanced=false`, `abort_on_first=false`, `meta_shacl=true`, and Warning/Info policy. A conforming case requires at least one target activation and zero `sh:ValidationResult`. The v0.2 negative case requires the three stable path/component/severity/message assertions and no extra result.
- JSON Schema uses Draft 7 plus `FormatChecker`. The negative record must produce exactly the required, date-time format, number type, and unit enum errors.
- SPARQL compares variable order, row count, and all TSV cell values exactly after deterministic row sorting. An empty result is accepted only when the expected TSV explicitly contains zero data rows.
- Artifact existence and SHA-256 are checked before case execution. Parser, dependency, configuration, report-structure, or evidence-write exceptions are program `ERROR` and cannot satisfy an expected business failure.
