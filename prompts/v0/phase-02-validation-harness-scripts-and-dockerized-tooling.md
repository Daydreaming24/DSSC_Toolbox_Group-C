# Phase 2 Prompt — Validation Harness, Scripts, and Dockerized Tooling

Implement Phase 2 only.

Objective:
Create a robust independent local validation harness that can run without Semantic Treehouse. This phase should make validation reproducible on a machine with Docker.

Tasks:

1. Add requirements.txt or pyproject.toml with Python tooling:

   * rdflib
   * pyshacl
   * pyld
   * jsonschema
   * ruamel.yaml or pyyaml

2. Create scripts:

   * scripts/validate_rdf.py
   * scripts/validate_jsonld.py
   * scripts/validate_shacl.py
   * scripts/validate_jsonschema.py
   * scripts/validate_openapi.py
   * scripts/run_all_validations.py

3. scripts/validate_shacl.py must:

   * validate v0.1 valid metadata against v0.1 shape
   * validate v0.2 valid metadata against v0.2 shape
   * validate v0.2 invalid metadata against v0.2 shape and expect failure
   * validate v0.3 data product metadata against v0.3 metadata shape
   * validate v0.3 energy reading valid record against v0.3 record shape if the record is represented as JSON-LD/RDF
   * write validation/pyshacl-validation-report.md

4. scripts/validate_jsonschema.py must:

   * validate model/v0.3/energy-reading-record-valid.jsonld or a JSON fixture against energy-reading-record.schema.json
   * validate invalid record and expect failure
   * write validation/jsonschema-validation-report.md

5. scripts/validate_openapi.py must:

   * parse openapi-fragment.yaml
   * check required top-level fields exist
   * optionally use openapi-spec-validator if available
   * write validation/openapi-validation-report.md

6. Add Dockerfile.validation that installs Python tooling and runs make validate.

7. Add docker-compose.validation.yml with a validation service that mounts the repository and runs make validate.

8. Update Makefile targets:

   * make validate must run all local validation scripts.
   * make clean must remove generated caches but preserve final reports.

9. Add validation/expected-results.md documenting:

   * valid cases should pass
   * invalid metadata should fail for providerName, unit, temporalEnd
   * invalid record should fail for required field/type/unit constraints

Acceptance criteria:

* make validate runs end to end locally, or gives a precise missing-tool message.
* docker compose -f docker-compose.validation.yml run --rm validation runs the validation harness.
* validation reports are created.
* Invalid examples are expected failures, not harness failures.

Commands to run:

* make validate
* docker compose -f docker-compose.validation.yml run --rm validation

Stop after Phase 2.

