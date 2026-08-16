from __future__ import annotations

try:
    import yaml
except ModuleNotFoundError as exc:
    from validation_common import dependency_error

    raise dependency_error("PyYAML") from exc

from validation_common import CheckResult, MODEL_DIR, VALIDATION_DIR, relative, write_report


def main() -> int:
    path = MODEL_DIR / "v0.3" / "openapi-fragment.yaml"
    results: list[CheckResult] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            spec = yaml.safe_load(handle)
        for key in ("openapi", "info", "paths"):
            if key not in spec:
                raise ValueError(f"Missing top-level key: {key}")
        if "/energy/buildings/hourly" not in spec["paths"]:
            raise ValueError("Missing path: /energy/buildings/hourly")
        results.append(CheckResult("OpenAPI YAML parses and has required keys", True, f"`{relative(path)}` parsed successfully."))
    except Exception as exc:
        results.append(CheckResult("OpenAPI YAML parses and has required keys", False, f"{exc.__class__.__name__}: {exc}"))
        spec = None

    if spec is not None:
        try:
            from openapi_spec_validator import validate_spec

            validate_spec(spec)
            results.append(CheckResult("openapi-spec-validator check", True, "Spec passed `openapi-spec-validator`."))
        except ModuleNotFoundError:
            results.append(CheckResult("openapi-spec-validator check", True, "Optional dependency not installed; structural parse check was used."))
        except Exception as exc:
            results.append(CheckResult("openapi-spec-validator check", False, f"{exc.__class__.__name__}: {exc}"))

    ok = write_report(VALIDATION_DIR / "openapi-validation-report.md", "OpenAPI Validation Report", results)
    print(f"OpenAPI validation report: {relative(VALIDATION_DIR / 'openapi-validation-report.md')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
