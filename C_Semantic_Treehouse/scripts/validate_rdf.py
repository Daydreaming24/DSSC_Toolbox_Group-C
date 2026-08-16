from __future__ import annotations

from rdflib import Graph

from validation_common import CheckResult, MODEL_DIR, VALIDATION_DIR, relative, write_report


def main() -> int:
    results: list[CheckResult] = []
    ttl_files = sorted(MODEL_DIR.glob("v*/**/*.ttl"))
    if not ttl_files:
        results.append(CheckResult("Turtle artifact discovery", False, "No `.ttl` files found."))
    for path in ttl_files:
        try:
            graph = Graph()
            graph.parse(path, format="turtle")
            results.append(CheckResult(relative(path), True, f"Parsed successfully with {len(graph)} triples."))
        except Exception as exc:
            results.append(CheckResult(relative(path), False, f"{exc.__class__.__name__}: {exc}"))

    ok = write_report(VALIDATION_DIR / "rdf-validation-report.md", "RDF Syntax Validation Report", results)
    print(f"RDF validation report: {relative(VALIDATION_DIR / 'rdf-validation-report.md')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
