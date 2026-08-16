"""Phase 1 syntax and artifact validation.

This is intentionally small. Phase 2 replaces it with report-producing
validation scripts and Dockerized harness commands.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker, ValidationError
from rdflib import Graph
import yaml


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"


def validate_rdf() -> None:
    files = sorted(MODEL_DIR.glob("v*/**/*.ttl"))
    if not files:
        raise SystemExit("No Turtle files found.")

    for path in files:
        graph = Graph()
        graph.parse(path, format="turtle")
        print(f"RDF OK: {path.relative_to(ROOT)} ({len(graph)} triples)")


def validate_jsonld() -> None:
    files = sorted(MODEL_DIR.glob("v*/**/*.jsonld"))
    if not files:
        raise SystemExit("No JSON-LD files found.")

    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
        print(f"JSON-LD JSON syntax OK: {path.relative_to(ROOT)}")

    print("JSON-LD expansion is deferred to Phase 2 because pyld is not required in Phase 1.")


def validate_jsonschema() -> None:
    files = sorted(MODEL_DIR.glob("v*/**/*.schema.json"))
    if not files:
        raise SystemExit("No JSON Schema files found.")

    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        Draft7Validator.check_schema(schema)
        print(f"JSON Schema OK: {path.relative_to(ROOT)}")

    schema_path = MODEL_DIR / "v0.3" / "energy-reading-record.schema.json"
    valid_path = MODEL_DIR / "v0.3" / "energy-reading-record-valid.jsonld"
    invalid_path = MODEL_DIR / "v0.3" / "energy-reading-record-invalid.jsonld"
    if schema_path.exists() and valid_path.exists() and invalid_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        valid_record = json.loads(valid_path.read_text(encoding="utf-8"))
        invalid_record = json.loads(invalid_path.read_text(encoding="utf-8"))

        errors = sorted(validator.iter_errors(valid_record), key=lambda e: list(e.path))
        if errors:
            messages = "; ".join(error.message for error in errors)
            raise SystemExit(f"Valid record failed JSON Schema: {messages}")
        print("JSON Schema example OK: model/v0.3/energy-reading-record-valid.jsonld")

        try:
            validator.validate(invalid_record)
        except ValidationError as error:
            print(f"JSON Schema expected invalid example failed: {error.message}")
        else:
            raise SystemExit("Invalid record unexpectedly passed JSON Schema.")


def validate_openapi() -> None:
    files = sorted(MODEL_DIR.glob("v*/**/openapi*.yaml"))
    if not files:
        raise SystemExit("No OpenAPI YAML files found.")

    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        for key in ("openapi", "info", "paths"):
            if key not in data:
                raise SystemExit(f"{path.relative_to(ROOT)} missing top-level key: {key}")
        print(f"OpenAPI YAML OK: {path.relative_to(ROOT)}")


COMMANDS = {
    "rdf": validate_rdf,
    "jsonld": validate_jsonld,
    "jsonschema": validate_jsonschema,
    "openapi": validate_openapi,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print("Usage: phase1_validate.py [rdf|jsonld|jsonschema|openapi]", file=sys.stderr)
        return 2

    COMMANDS[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
