from __future__ import annotations

from pathlib import Path

try:
    from pyshacl import validate
except ModuleNotFoundError as exc:
    from validation_common import dependency_error

    raise dependency_error("pyshacl") from exc

from rdflib import Graph

from validation_common import CheckResult, MODEL_DIR, VALIDATION_DIR, relative, write_report


def parse_graph(path: Path, fmt: str) -> Graph:
    graph = Graph()
    graph.parse(path.as_uri(), format=fmt)
    return graph


def run_case(name: str, data_path: Path, shape_path: Path, expect_conforms: bool) -> CheckResult:
    try:
        data_graph = parse_graph(data_path, "json-ld")
        shape_graph = parse_graph(shape_path, "turtle")
        conforms, report_graph, report_text = validate(
            data_graph=data_graph,
            shacl_graph=shape_graph,
            inference="rdfs",
            advanced=False,
            meta_shacl=False,
            debug=False,
        )
        expected = conforms == expect_conforms
        expectation = "conforms" if expect_conforms else "does not conform"
        detail = [
            f"Data graph: `{relative(data_path)}`",
            f"Shapes graph: `{relative(shape_path)}`",
            f"Expected: {expectation}",
            f"Actual conforms: {conforms}",
            "",
            "```text",
            report_text.strip(),
            "```",
        ]
        return CheckResult(name, expected, "\n".join(detail))
    except Exception as exc:
        return CheckResult(name, False, f"{exc.__class__.__name__}: {exc}")


def main() -> int:
    cases = [
        (
            "v0.1 valid metadata conforms",
            MODEL_DIR / "v0.1" / "data-product-valid.jsonld",
            MODEL_DIR / "v0.1" / "data-product-metadata-shapes.ttl",
            True,
        ),
        (
            "v0.2 valid metadata conforms",
            MODEL_DIR / "v0.2" / "data-product-valid.jsonld",
            MODEL_DIR / "v0.2" / "data-product-metadata-shapes.ttl",
            True,
        ),
        (
            "v0.2 invalid metadata fails as expected",
            MODEL_DIR / "v0.2" / "data-product-invalid.jsonld",
            MODEL_DIR / "v0.2" / "data-product-metadata-shapes.ttl",
            False,
        ),
        (
            "v0.3 data product metadata conforms",
            MODEL_DIR / "v0.3" / "data-product-valid.jsonld",
            MODEL_DIR / "v0.3" / "data-product-metadata-shapes.ttl",
            True,
        ),
        (
            "v0.3 energy reading record conforms",
            MODEL_DIR / "v0.3" / "energy-reading-record-valid.jsonld",
            MODEL_DIR / "v0.3" / "energy-reading-record-shapes.ttl",
            True,
        ),
    ]
    results = [run_case(*case) for case in cases]
    ok = write_report(
        VALIDATION_DIR / "pyshacl-validation-report.md",
        "pySHACL Validation Report",
        results,
        notes=[
            "Invalid metadata is expected to fail because providerName is missing, unit is MWh, and temporalEnd is missing.",
            "Expected invalid cases count as harness success when they fail for the intended constraints.",
        ],
    )
    print(f"pySHACL validation report: {relative(VALIDATION_DIR / 'pyshacl-validation-report.md')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
