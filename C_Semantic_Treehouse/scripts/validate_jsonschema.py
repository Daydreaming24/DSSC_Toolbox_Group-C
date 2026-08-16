from __future__ import annotations

from jsonschema import Draft7Validator, FormatChecker, ValidationError

from validation_common import CheckResult, MODEL_DIR, VALIDATION_DIR, load_json, relative, write_report


def main() -> int:
    schema_path = MODEL_DIR / "v0.3" / "energy-reading-record.schema.json"
    valid_path = MODEL_DIR / "v0.3" / "energy-reading-record-valid.jsonld"
    invalid_path = MODEL_DIR / "v0.3" / "energy-reading-record-invalid.jsonld"
    results: list[CheckResult] = []

    try:
        schema = load_json(schema_path)
        Draft7Validator.check_schema(schema)
        results.append(CheckResult("Energy Reading Record schema is valid", True, f"`{relative(schema_path)}` is a valid Draft 7 schema."))
    except Exception as exc:
        results.append(CheckResult("Energy Reading Record schema is valid", False, f"{exc.__class__.__name__}: {exc}"))
        schema = None

    if schema is not None:
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        try:
            valid_record = load_json(valid_path)
            errors = sorted(validator.iter_errors(valid_record), key=lambda error: list(error.path))
            if errors:
                detail = "\n".join(f"- {list(error.path)}: {error.message}" for error in errors)
                results.append(CheckResult("Valid Energy Reading Record passes", False, detail))
            else:
                results.append(CheckResult("Valid Energy Reading Record passes", True, f"`{relative(valid_path)}` conforms."))
        except Exception as exc:
            results.append(CheckResult("Valid Energy Reading Record passes", False, f"{exc.__class__.__name__}: {exc}"))

        try:
            invalid_record = load_json(invalid_path)
            validator.validate(invalid_record)
            results.append(CheckResult("Invalid Energy Reading Record fails as expected", False, "`energy-reading-record-invalid.jsonld` unexpectedly passed."))
        except ValidationError as exc:
            results.append(
                CheckResult(
                    "Invalid Energy Reading Record fails as expected",
                    True,
                    f"`{relative(invalid_path)}` failed as expected. First error: {exc.message}",
                )
            )
        except Exception as exc:
            results.append(CheckResult("Invalid Energy Reading Record fails as expected", False, f"{exc.__class__.__name__}: {exc}"))

    ok = write_report(
        VALIDATION_DIR / "jsonschema-validation-report.md",
        "JSON Schema Validation Report",
        results,
        notes=[
            "The invalid record intentionally violates required field, type/format, and unit constraints.",
            "JSON Schema reports the first validation error for the expected invalid example.",
        ],
    )
    print(f"JSON Schema validation report: {relative(VALIDATION_DIR / 'jsonschema-validation-report.md')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
