# Phase 2 Summary

## Files Created or Modified

Created:

- `requirements.txt`
- `scripts/validation_common.py`
- `scripts/validate_rdf.py`
- `scripts/validate_jsonld.py`
- `scripts/validate_shacl.py`
- `scripts/validate_jsonschema.py`
- `scripts/validate_openapi.py`
- `scripts/run_all_validations.py`
- `validation/expected-results.md`
- root `Dockerfile.validation`
- root `docker-compose.validation.yml`

Modified:

- root `Makefile`
- root `make.cmd`
- `model/v0.3/energy-reading-record-shapes.ttl`

## Validation Harness Behavior

The Phase 2 harness now performs independent local validation without Semantic Treehouse:

- RDF/Turtle syntax validation with `rdflib`
- JSON-LD JSON parsing and expansion with `pyld`
- SHACL validation with `pyshacl`
- JSON Schema validation with `jsonschema`
- OpenAPI parsing and optional `openapi-spec-validator` validation

Reports are written to:

- `validation/rdf-validation-report.md`
- `validation/jsonld-validation-report.md`
- `validation/pyshacl-validation-report.md`
- `validation/jsonschema-validation-report.md`
- `validation/openapi-validation-report.md`
- `validation/all-validations-report.md`

Expected invalid examples are treated as harness success when they fail for the intended constraints.

## Commands Run

- `python -m pip install -r C_Semantic_Treehouse\requirements.txt`
- `cmd /c make validate-shacl`
- `cmd /c make validate`
- `docker compose -f docker-compose.validation.yml run --rm validation`

Docker note:

- The first direct Docker Compose build failed because the local Docker credential helper `docker-credential-desktop` was not available in `%PATH%`.
- Running once with a temporary empty `DOCKER_CONFIG` allowed Docker to pull/build the validation image.
- After the image was built, the required command `docker compose -f docker-compose.validation.yml run --rm validation` ran successfully.

## Pass/Fail Status

Passed:

- `cmd /c make validate` runs end to end locally.
- Docker Compose validation runs end to end.
- All validation reports are created.
- `v0.2` invalid metadata fails as expected for:
  - missing `providerName`
  - `unit = MWh` instead of `kWh`
  - missing `temporalEnd`
- `v0.3` invalid record fails as expected under JSON Schema.

Adjusted:

- `model/v0.3/energy-reading-record-shapes.ttl` now checks `energyKWh` as a non-negative numeric literal instead of requiring strict `xsd:decimal`. This avoids JSON-LD numeric datatype differences while JSON Schema still enforces a JSON number.

Deferred:

- SPARQL tests remain a stub until Phase 3.
- Quality metrics remain a stub until Phase 4.
- Semantic Treehouse evidence remains a stub until Phase 6.

## Remaining Risks

- The Docker credential helper issue may recur on a clean machine before the image is built. The repository Docker setup is valid, but the local Docker Desktop credential configuration may need repair or a temporary `DOCKER_CONFIG` workaround.
- The current workspace is not a git repository, so no commit was created.
