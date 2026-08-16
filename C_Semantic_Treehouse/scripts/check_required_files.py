from __future__ import annotations

from pathlib import Path

from validation_common import CheckResult, ROOT, VALIDATION_DIR, relative, write_report


REPO_ROOT = ROOT.parent


def package(path: str) -> Path:
    return ROOT / path


def repo(path: str) -> Path:
    return REPO_ROOT / path


REQUIRED_GROUPS: dict[str, list[tuple[str, Path]]] = {
    "minimum checklist": [
        ("README", package("README.md")),
        ("semantic model design report", package("C_semantic_model_design.md")),
        ("Semantic Treehouse usage report", package("C_semantic_treehouse_usage.md")),
        ("model versioning demo report", package("C_model_versioning_demo.md")),
        ("export for validation report", package("C_export_for_validation.md")),
        ("metadata-record relationship diagram", package("diagrams/metadata-record-model.mmd")),
        ("v0.1 ontology", package("model/v0.1/building-energy-ontology.ttl")),
        ("v0.1 metadata SHACL", package("model/v0.1/data-product-metadata-shapes.ttl")),
        ("v0.2 ontology", package("model/v0.2/building-energy-ontology.ttl")),
        ("v0.2 metadata SHACL", package("model/v0.2/data-product-metadata-shapes.ttl")),
        ("v0.2 invalid metadata example", package("model/v0.2/data-product-invalid.jsonld")),
        ("v0.3 ontology", package("model/v0.3/building-energy-ontology.ttl")),
        ("v0.3 metadata SHACL", package("model/v0.3/data-product-metadata-shapes.ttl")),
        ("v0.3 record SHACL", package("model/v0.3/energy-reading-record-shapes.ttl")),
        ("Semantic Treehouse deployment evidence", package("evidence/semantic-treehouse-local-deployment.md")),
    ],
    "excellent checklist": [
        ("DCAT/SOSA/QUDT/OWL-Time SSSOM alignment", package("mappings/external-standard-alignment.sssom.tsv")),
        ("v0.3 data product JSON-LD context", package("model/v0.3/data-product-context.jsonld")),
        ("v0.3 record JSON-LD context", package("model/v0.3/energy-reading-record-context.jsonld")),
        ("v0.3 Energy Reading Record JSON Schema", package("model/v0.3/energy-reading-record.schema.json")),
        ("v0.3 OpenAPI fragment", package("model/v0.3/openapi-fragment.yaml")),
        ("pySHACL validation report", package("validation/pyshacl-validation-report.md")),
        ("JSON Schema validation report", package("validation/jsonschema-validation-report.md")),
        ("A Group handoff", package("handoff/handoff-to-A-offering-metadata.md")),
        ("D Group handoff", package("handoff/handoff-to-D-shacl-validation.md")),
        ("B Group model URI/provenance handoff", package("handoff/handoff-to-B-model-uri-provenance.md")),
        ("model changelog", package("governance/changelog.md")),
        ("namespace policy", package("governance/namespace-policy.md")),
        ("release policy", package("governance/release-policy.md")),
    ],
    "top-tier checklist": [
        ("GitHub Actions validation workflow", repo(".github/workflows/validate.yml")),
        ("SPARQL competency question report", package("validation/sparql-competency-question-report.md")),
        ("SPARQL competency question definitions", package("tests/sparql/competency-questions.md")),
        ("provenance JSON-LD", package("governance/provenance.jsonld")),
        ("governance validation report", package("validation/governance-validation-report.md")),
        ("independent local validation report", package("validation/all-validations-report.md")),
        ("model quality assessment", package("quality/model-quality-assessment.md")),
        ("quality metrics validation report", package("validation/quality-metrics-report.md")),
        ("AI-assisted human-governed modeling chapter", package("docs/ai-assisted-human-governed-semantic-modeling.md")),
        ("semantic governance flow diagram", package("diagrams/semantic-governance-flow.mmd")),
        ("demo script", package("docs/demo-script.md")),
        ("final checklist", package("docs/final-checklist.md")),
        ("final grading summary", package("FINAL_SUMMARY.md")),
    ],
}


VERSION_ARTIFACTS = {
    "v0.1": [
        "building-energy-ontology.ttl",
        "data-product-metadata-shapes.ttl",
        "data-product-context.jsonld",
        "data-product-valid.jsonld",
    ],
    "v0.2": [
        "building-energy-ontology.ttl",
        "data-product-metadata-shapes.ttl",
        "data-product-context.jsonld",
        "data-product-valid.jsonld",
        "data-product-invalid.jsonld",
    ],
    "v0.3": [
        "building-energy-ontology.ttl",
        "data-product-metadata-shapes.ttl",
        "energy-reading-record-shapes.ttl",
        "data-product-context.jsonld",
        "energy-reading-record-context.jsonld",
        "data-product-valid.jsonld",
        "energy-reading-record-valid.jsonld",
        "energy-reading-record-invalid.jsonld",
        "energy-reading-record.schema.json",
        "openapi-fragment.yaml",
    ],
}


def display(path: Path) -> str:
    try:
        return relative(path)
    except ValueError:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def group_result(group_name: str, files: list[tuple[str, Path]]) -> CheckResult:
    missing = [(label, path) for label, path in files if not path.exists()]
    detail_lines = []
    for label, path in files:
        status = "present" if path.exists() else "missing"
        detail_lines.append(f"- {label}: {status} - `{display(path)}`")
    return CheckResult(
        group_name,
        not missing,
        "\n".join(detail_lines),
    )


def version_result(version: str, filenames: list[str]) -> CheckResult:
    files = [(filename, package(f"model/{version}/{filename}")) for filename in filenames]
    return group_result(f"{version} artifacts", files)


def main() -> int:
    results: list[CheckResult] = []
    for group_name, files in REQUIRED_GROUPS.items():
        results.append(group_result(group_name, files))
    for version, filenames in VERSION_ARTIFACTS.items():
        results.append(version_result(version, filenames))

    report_path = VALIDATION_DIR / "required-files-report.md"
    ok = write_report(
        report_path,
        "Required Files Report",
        results,
        notes=[
            "This check covers minimum, excellent, and top-tier file presence for the C Group package.",
            "Content correctness is validated by the dedicated RDF, SHACL, JSON-LD, JSON Schema, OpenAPI, SPARQL, quality, and governance checks.",
        ],
    )
    print(f"Required files report: {relative(report_path)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
