"""Deterministic Phase 06 semantic-quality metrics and SSSOM validation.

The component reads the release authorities and their schemas before it reads
quality inputs.  Metrics are calculated from the validated manifests and the
actual RDF/SHACL graphs selected by the release manifest.  Cross-machine
results contain no timestamps or absolute paths; machine inventory is written
to a separate sidecar.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import platform
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_ROOT_SCRIPTS = REPOSITORY_ROOT / "scripts"
if str(_ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_ROOT_SCRIPTS))

from rdflib import Graph, Literal, Namespace, RDF, URIRef  # noqa: E402

from dssc_validation.baseline_manifest import (  # noqa: E402
    BaselineManifestError,
    load_and_validate_baseline_manifest,
)
from dssc_validation.evidence import (  # noqa: E402
    atomic_write_json,
    atomic_write_text,
    json_bytes,
)
from dssc_validation.hashing import sha256_file  # noqa: E402
from dssc_validation.release_manifest import (  # noqa: E402
    load_and_audit_release_manifest,
)
from dssc_validation.requirements_registry import (  # noqa: E402
    load_and_validate_requirements,
)
from dssc_validation.suite_registry import (  # noqa: E402
    load_and_validate_registry,
)
from dssc_validation.v04_manifest import (  # noqa: E402
    load_and_validate_v04_manifest,
)


SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.org/dssc-energy#")
BE = Namespace("https://w3id.org/dssc-demo/building-energy#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")

EXPECTED_CONTRACT_VERSION = "1.6.0"
MAPPING_RELPATH = (
    "C_Semantic_Treehouse/mappings/external-standard-alignment.sssom.tsv"
)
SPARQL_MANIFEST_RELPATH = (
    "C_Semantic_Treehouse/tests/sparql/sparql-test-cases.json"
)
SPARQL_SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/tests/sparql/sparql-test-cases.schema.json"
)
ASSESSMENT_RELPATH = "C_Semantic_Treehouse/quality/model-quality-assessment.md"
RESULT_RELPATH = "build/validation/quality/results.json"
REPORT_RELPATH = "build/validation/quality/report.md"
ENVIRONMENT_RELPATH = "build/validation/quality/run-environment.json"
NEGATIVE_CONTROL_RELPATH = "build/phase-06/quality/negative-controls.json"
DETERMINISM_RELPATH = "build/phase-06/quality/determinism.json"

EXPECTED_COLUMNS = (
    "subject_id",
    "subject_label",
    "predicate_id",
    "object_id",
    "object_label",
    "mapping_justification",
    "confidence",
    "author_id",
    "mapping_date",
    "review_status",
    "mapping_category",
    "source_version",
    "target_version",
    "comment",
)
ALLOWED_PREDICATES = frozenset(
    {
        "skos:exactMatch",
        "skos:closeMatch",
        "skos:relatedMatch",
        "rdfs:subClassOf",
    }
)
ALLOWED_REVIEW_STATUSES = frozenset(
    {"PENDING_DOMAIN_REVIEW", "REVIEWED", "REJECTED"}
)
ALLOWED_MAPPING_CATEGORIES = frozenset(
    {
        "migration",
        "direct_reuse",
        "external_alignment",
        "inherited_record_alignment",
    }
)
PREFIXES = {
    "be": str(BE),
    "ex": str(EX),
    "dcat": str(DCAT),
    "dct": str(DCT),
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "semapv": "https://w3id.org/semapv/vocab/",
    "schema": "https://schema.org/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "sosa": "http://www.w3.org/ns/sosa/",
    "ssn": "http://www.w3.org/ns/ssn/",
    "qudt": "http://qudt.org/schema/qudt/",
    "unit": "http://qudt.org/vocab/unit/",
    "time": "http://www.w3.org/2006/time#",
    "sh": str(SH),
}

EXPECTED_MIGRATIONS = frozenset(
    {
        ("be:DataProductMetadata", "dcat:Dataset"),
        ("dct:identifier", "ex:datasetId"),
        ("be:providerName", "ex:providerName"),
        ("be:endpointUrl", "dcat:endpointURL"),
        ("be:format", "dct:format"),
        ("be:frequency", "dct:accrualPeriodicity"),
        ("be:unit", "ex:unit"),
        ("be:spatialCoverage", "dct:spatial"),
        ("be:temporalStart", "ex:temporalStart"),
        ("be:temporalEnd", "ex:temporalEnd"),
    }
)
EXPECTED_DIRECT_REUSE = frozenset(
    {
        "dcat:Dataset",
        "dct:title",
        "dct:spatial",
        "dct:accrualPeriodicity",
        "dcat:endpointURL",
        "dct:format",
        "dct:description",
        "dct:license",
    }
)
EXPECTED_METRIC_IDS = (
    "normative_requirement_implementation_coverage",
    "requirement_automated_test_coverage",
    "required_optional_field_coverage",
    "constraint_component_distribution",
    "four_state_automated_case_coverage",
    "external_standard_reuse_and_mapping",
    "breaking_change_fact_coverage",
    "release_provenance_metadata_completeness",
)
SOURCE_CODE_RELPATHS = (
    "C_Semantic_Treehouse/scripts/governance_contract.py",
    "C_Semantic_Treehouse/scripts/quality_metrics.py",
    "C_Semantic_Treehouse/scripts/run_sparql_tests.py",
    "C_Semantic_Treehouse/scripts/sparql_manifest.py",
    "C_Semantic_Treehouse/scripts/sparql_report.py",
    "C_Semantic_Treehouse/scripts/validate_governance.py",
    "scripts/validate.py",
    "scripts/dssc_validation/__init__.py",
    "scripts/dssc_validation/baseline_manifest.py",
    "scripts/dssc_validation/checks_all.py",
    "scripts/dssc_validation/checks_phase06.py",
    "scripts/dssc_validation/entrypoint_catalog.py",
    "scripts/dssc_validation/evidence.py",
    "scripts/dssc_validation/hashing.py",
    "scripts/dssc_validation/paths.py",
    "scripts/dssc_validation/release_manifest.py",
    "scripts/dssc_validation/requirements_registry.py",
    "scripts/dssc_validation/suite_registry.py",
    "scripts/dssc_validation/v04_manifest.py",
)


class QualityFailure(RuntimeError):
    """A stable fail-closed quality failure with machine-readable details."""

    def __init__(
        self, code: str, message: str, details: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _repo_path(root: Path, relpath: str) -> Path:
    candidate = root.joinpath(*Path(relpath).parts)
    candidate.resolve().relative_to(root.resolve())
    return candidate


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_sha256(value: Any) -> str:
    return _sha256_bytes(json_bytes(value))


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise QualityFailure(
            "JSON_ROOT", "A consumed JSON authority must have an object root."
        )
    return value


def _hash_record(root: Path, relpath: str, roles: Iterable[str]) -> dict[str, Any]:
    path = _repo_path(root, relpath)
    if not path.is_file():
        raise QualityFailure(
            "MISSING_SOURCE", f"Consumed source is missing: {relpath}"
        )
    return {
        "path": relpath,
        "sha256": sha256_file(path),
        "roles": sorted(set(roles)),
    }


def _manifest_preflight(root: Path) -> dict[str, Any]:
    """Run all five existing schema/semantic checkers before quality work."""

    checks: list[dict[str, Any]] = []

    release = load_and_audit_release_manifest(root)
    checks.append(
        {
            "id": "release-manifest",
            "passed": release.ok,
            "issues": list(release.issues),
        }
    )

    baseline = None
    try:
        baseline = load_and_validate_baseline_manifest(root)
    except BaselineManifestError as exc:
        checks.append(
            {
                "id": "baseline-test-cases",
                "passed": False,
                "issues": [issue.as_dict() for issue in exc.issues],
            }
        )
    else:
        checks.append(
            {"id": "baseline-test-cases", "passed": True, "issues": []}
        )

    requirements = load_and_validate_requirements(root)
    checks.append(
        {
            "id": "v0.4-requirements",
            "passed": requirements.ok,
            "issues": list(requirements.issues),
        }
    )

    test_cases = load_and_validate_v04_manifest(root, verify_fixture_hashes=True)
    checks.append(
        {
            "id": "v0.4-test-cases",
            "passed": test_cases.ok,
            "issues": [issue.as_dict() for issue in test_cases.issues],
        }
    )

    registry = load_and_validate_registry(root)
    registry_issues = [
        {"code": issue.code, "message": issue.message} for issue in registry.issues
    ]
    if registry.contract_version != EXPECTED_CONTRACT_VERSION:
        registry_issues.append(
            {
                "code": "CONTRACT_VERSION",
                "message": (
                    "quality requires validation-suites contract "
                    f"{EXPECTED_CONTRACT_VERSION}"
                ),
            }
        )
    checks.append(
        {
            "id": "validation-suites",
            "passed": registry.ok and not registry_issues,
            "issues": registry_issues,
        }
    )

    if not all(check["passed"] for check in checks):
        raise QualityFailure(
            "MANIFEST_PREFLIGHT_FAILED",
            "A consumed manifest failed schema or cross-record semantic validation.",
            {"checks": checks},
        )
    if (
        release.manifest is None
        or baseline is None
        or requirements.manifest is None
        or test_cases.manifest is None
        or registry.registry is None
        or registry.registry_sha256 is None
    ):
        raise QualityFailure(
            "MANIFEST_PREFLIGHT_EMPTY",
            "A manifest checker returned no validated document.",
            {"checks": checks},
        )

    binding = release.manifest.get("validationSuiteRegistry", {})
    if (
        binding.get("contractVersion") != EXPECTED_CONTRACT_VERSION
        or binding.get("sha256") != registry.registry_sha256
    ):
        raise QualityFailure(
            "REGISTRY_BINDING",
            "Release manifest registry binding differs from validated registry bytes.",
            {
                "declared_contract_version": binding.get("contractVersion"),
                "actual_contract_version": registry.contract_version,
                "declared_sha256": binding.get("sha256"),
                "actual_sha256": registry.registry_sha256,
            },
        )

    manifest_records = [
        {
            "id": "release-manifest",
            "path": _relative(root, release.manifest_path),
            "sha256": release.manifest_sha256,
            "schema_path": _relative(root, release.schema_path),
            "schema_sha256": release.schema_sha256,
            "schema_version": release.manifest.get("manifest_schema_version"),
            "schema_validation": "PASS",
            "semantic_validation": "PASS",
        },
        {
            "id": "baseline-test-cases",
            "path": _relative(root, baseline.manifest_path),
            "sha256": baseline.manifest_sha256,
            "schema_path": _relative(root, baseline.schema_path),
            "schema_sha256": baseline.schema_sha256,
            "schema_version": baseline.manifest_schema_version,
            "schema_validation": "PASS",
            "semantic_validation": "PASS",
        },
        {
            "id": "v0.4-requirements",
            "path": _relative(root, requirements.manifest_path),
            "sha256": requirements.manifest_sha256,
            "schema_path": _relative(root, requirements.schema_path),
            "schema_sha256": requirements.schema_sha256,
            "schema_version": requirements.manifest.get("manifest_schema_version"),
            "schema_validation": "PASS",
            "semantic_validation": "PASS",
        },
        {
            "id": "v0.4-test-cases",
            "path": _relative(root, test_cases.manifest_path),
            "sha256": test_cases.manifest_sha256,
            "schema_path": _relative(root, test_cases.schema_path),
            "schema_sha256": test_cases.schema_sha256,
            "schema_version": test_cases.manifest.get("manifest_schema_version"),
            "schema_validation": "PASS",
            "semantic_validation": "PASS",
        },
        {
            "id": "validation-suites",
            "path": _relative(root, registry.path or _repo_path(root, "")),
            "sha256": registry.registry_sha256,
            "schema_path": "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json",
            "schema_sha256": sha256_file(
                _repo_path(
                    root,
                    "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json",
                )
            ),
            "schema_version": registry.registry.get("schema_version"),
            "contract_version": registry.contract_version,
            "schema_validation": "PASS",
            "semantic_validation": "PASS",
        },
    ]
    return {
        "release": release.manifest,
        "baseline": baseline,
        "requirements": requirements.manifest,
        "test_cases": test_cases.manifest,
        "registry": registry.registry,
        "registry_sha256": registry.registry_sha256,
        "manifest_records": manifest_records,
        "checks": checks,
    }


def _expand_curie(value: str) -> str | None:
    if value.startswith(("http://", "https://")):
        return value if " " not in value else None
    if ":" not in value:
        return None
    prefix, local = value.split(":", 1)
    namespace = PREFIXES.get(prefix)
    if namespace is None or not local or any(character.isspace() for character in local):
        return None
    return namespace + local


def _read_sssom(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return fieldnames, rows


def _sssom_issues(
    fieldnames: list[str], rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    def add(code: str, row: int | None, message: str) -> None:
        issues.append({"code": code, "row": row, "message": message})

    if tuple(fieldnames) != EXPECTED_COLUMNS:
        add(
            "COLUMN_CONTRACT",
            1,
            "SSSOM columns must exactly match the Phase 06 cumulative contract.",
        )
        return issues
    if not rows:
        add("ZERO_ROWS", None, "SSSOM table must contain at least one mapping.")
        return issues

    seen: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows, start=2):
        if None in row:
            add("MALFORMED_ROW", index, "row contains values beyond the declared columns")
            continue
        empty = [
            column
            for column in EXPECTED_COLUMNS
            if not isinstance(row.get(column), str) or not row[column].strip()
        ]
        if empty:
            add("EMPTY_REQUIRED_CELL", index, ", ".join(empty))
            continue
        for column in (
            "subject_id",
            "predicate_id",
            "object_id",
            "mapping_justification",
        ):
            if _expand_curie(row[column]) is None:
                add("INVALID_IRI_OR_CURIE", index, column)
        if row["predicate_id"] not in ALLOWED_PREDICATES:
            add("INVALID_MAPPING_PREDICATE", index, row["predicate_id"])
        if row["review_status"] not in ALLOWED_REVIEW_STATUSES:
            add("INVALID_REVIEW_STATUS", index, row["review_status"])
        if row["mapping_category"] not in ALLOWED_MAPPING_CATEGORIES:
            add("INVALID_MAPPING_CATEGORY", index, row["mapping_category"])
        try:
            confidence = float(row["confidence"])
        except ValueError:
            add("INVALID_CONFIDENCE", index, row["confidence"])
        else:
            if not math.isfinite(confidence) or confidence < 0.0 or confidence > 1.0:
                add("INVALID_CONFIDENCE", index, row["confidence"])
        try:
            date.fromisoformat(row["mapping_date"])
        except ValueError:
            add("INVALID_MAPPING_DATE", index, row["mapping_date"])

        key = (
            row["subject_id"],
            row["predicate_id"],
            row["object_id"],
        )
        if key in seen:
            add("DUPLICATE_MAPPING", index, "|".join(key))
        seen.add(key)

        subject_iri = _expand_curie(row["subject_id"])
        object_iri = _expand_curie(row["object_id"])
        if subject_iri is not None and subject_iri == object_iri:
            direct_reason = row["comment"].lower().startswith("direct reuse:")
            if row["mapping_category"] != "direct_reuse" or not direct_reason:
                add(
                    "UNJUSTIFIED_SELF_MAPPING",
                    index,
                    "Self mappings require direct_reuse and a Direct reuse comment.",
                )

    categories = Counter(row.get("mapping_category") for row in rows)
    for category in sorted(ALLOWED_MAPPING_CATEGORIES):
        if categories[category] == 0:
            add("MISSING_MAPPING_CATEGORY", None, category)

    migration_pairs = {
        (row.get("subject_id"), row.get("object_id"))
        for row in rows
        if row.get("mapping_category") == "migration"
    }
    for pair in sorted(EXPECTED_MIGRATIONS - migration_pairs):
        add("MISSING_MIGRATION", None, " -> ".join(pair))

    direct_terms = {
        row.get("subject_id")
        for row in rows
        if row.get("mapping_category") == "direct_reuse"
        and row.get("subject_id") == row.get("object_id")
    }
    for term in sorted(EXPECTED_DIRECT_REUSE - direct_terms):
        add("MISSING_DIRECT_REUSE", None, term)

    record_rows = [
        row for row in rows if row.get("mapping_category") == "inherited_record_alignment"
    ]
    standards = {
        "SOSA": any(row.get("object_id", "").startswith("sosa:") for row in record_rows),
        "SSN": any(row.get("object_id", "").startswith("ssn:") for row in record_rows),
        "QUDT": any(row.get("object_id", "").startswith(("qudt:", "unit:")) for row in record_rows),
        "UCUM": any(
            "ucum" in (row.get("object_id", "") + row.get("object_label", "") + row.get("comment", "")).lower()
            for row in record_rows
        ),
        "OWL-Time": any(row.get("object_id", "").startswith("time:") for row in record_rows),
    }
    for standard, represented in standards.items():
        if not represented:
            add("MISSING_RECORD_STANDARD", None, standard)
    return sorted(
        issues,
        key=lambda item: (
            item["code"],
            item["row"] if item["row"] is not None else -1,
            item["message"],
        ),
    )


def _validate_sssom(
    root: Path,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    path = _repo_path(root, MAPPING_RELPATH)
    fieldnames, rows = _read_sssom(path)
    issues = _sssom_issues(fieldnames, rows)
    if issues:
        raise QualityFailure(
            "SSSOM_VALIDATION_FAILED",
            "The cumulative SSSOM table failed structural or semantic validation.",
            {"issues": issues},
        )
    category_counts = Counter(row["mapping_category"] for row in rows)
    predicate_counts = Counter(row["predicate_id"] for row in rows)
    review_counts = Counter(row["review_status"] for row in rows)
    direct_rows = [
        row
        for row in rows
        if row["mapping_category"] == "direct_reuse"
        and row["subject_id"] == row["object_id"]
    ]
    local_rows = [
        row
        for row in rows
        if row["mapping_category"] == "external_alignment"
        and row["subject_id"].startswith("ex:")
    ]
    return rows, {
        "path": MAPPING_RELPATH,
        "sha256": sha256_file(path),
        "columns": list(EXPECTED_COLUMNS),
        "row_count": len(rows),
        "category_counts": dict(sorted(category_counts.items())),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "review_status_counts": dict(sorted(review_counts.items())),
        "direct_reuse_rows": len(direct_rows),
        "local_external_alignment_rows": len(local_rows),
        "duplicate_rows": 0,
        "unjustified_self_mappings": 0,
        "validation": "PASS",
    }


def _release_by_id(release_manifest: Mapping[str, Any], release_id: str) -> dict[str, Any]:
    for release in release_manifest.get("releases", []):
        if isinstance(release, dict) and release.get("id") == release_id:
            return release
    raise QualityFailure("RELEASE_REFERENCE", f"Release is missing: {release_id}")


def _artifact_by_role(release: Mapping[str, Any], role: str) -> dict[str, Any]:
    matches = [
        artifact
        for artifact in release.get("artifacts", [])
        if isinstance(artifact, dict) and artifact.get("role") == role
    ]
    if len(matches) != 1:
        raise QualityFailure(
            "ARTIFACT_ROLE",
            f"Release {release.get('id')} must expose exactly one {role} artifact.",
            {"count": len(matches)},
        )
    return matches[0]


def _parse_graph(root: Path, artifact: Mapping[str, Any]) -> Graph:
    path = _repo_path(root, str(artifact["path"]))
    graph = Graph()
    graph.parse(path.as_uri(), format="turtle")
    if len(graph) == 0:
        raise QualityFailure("EMPTY_RDF_GRAPH", f"RDF graph is empty: {artifact['path']}")
    return graph


def _context_map(root: Path, artifact: Mapping[str, Any]) -> dict[str, Any]:
    document = _load_json(_repo_path(root, str(artifact["path"])))
    context = document.get("@context")
    if not isinstance(context, dict):
        raise QualityFailure("CONTEXT_ROOT", f"Inline context is missing: {artifact['path']}")
    return context


def _context_term(context: Mapping[str, Any], term: str) -> str | None:
    value = context.get(term)
    if isinstance(value, dict):
        value = value.get("@id")
    if not isinstance(value, str):
        return None
    if value.startswith(("http://", "https://")):
        return value
    if ":" not in value:
        return None
    prefix, local = value.split(":", 1)
    namespace = context.get(prefix)
    if isinstance(namespace, str):
        return namespace + local
    return _expand_curie(value)


def _current_release_inputs(
    root: Path, release_manifest: Mapping[str, Any]
) -> dict[str, Any]:
    current_id = release_manifest.get("currentRelease")
    if not isinstance(current_id, str):
        raise QualityFailure("CURRENT_RELEASE", "currentRelease is invalid.")
    current = _release_by_id(release_manifest, current_id)
    prior_id = current.get("priorRelease")
    if not isinstance(prior_id, str):
        raise QualityFailure("PRIOR_RELEASE", "Current release priorRelease is invalid.")
    prior = _release_by_id(release_manifest, prior_id)
    artifacts = {
        "metadata_shapes": _artifact_by_role(current, "metadata-shapes"),
        "ontology": _artifact_by_role(current, "ontology"),
        "metadata_context": _artifact_by_role(current, "metadata-context"),
        "metadata_example": _artifact_by_role(current, "metadata-valid-example"),
        "record_shapes": _artifact_by_role(current, "record-shapes"),
        "prior_metadata_context": _artifact_by_role(prior, "metadata-context"),
        "prior_metadata_example": _artifact_by_role(prior, "metadata-valid-example"),
    }
    return {
        "current_id": current_id,
        "prior_id": prior_id,
        "current": current,
        "prior": prior,
        "artifacts": artifacts,
        "metadata_graph": _parse_graph(root, artifacts["metadata_shapes"]),
        "ontology_graph": _parse_graph(root, artifacts["ontology"]),
        "record_graph": _parse_graph(root, artifacts["record_shapes"]),
        "current_context": _context_map(root, artifacts["metadata_context"]),
        "prior_context": _context_map(root, artifacts["prior_metadata_context"]),
        "current_example": _load_json(
            _repo_path(root, str(artifacts["metadata_example"]["path"]))
        ),
        "prior_example": _load_json(
            _repo_path(root, str(artifacts["prior_metadata_example"]["path"]))
        ),
    }


def _metric(
    metric_id: str,
    label: str,
    numerator: int,
    denominator: int,
    sources: Iterable[str],
    exclusions: Iterable[str],
    details: Mapping[str, Any],
) -> dict[str, Any]:
    ratio = numerator / denominator if denominator else None
    return {
        "id": metric_id,
        "label": label,
        "numerator": numerator,
        "denominator": denominator,
        "ratio": round(ratio, 6) if ratio is not None else None,
        "sources": sorted(set(sources)),
        "exclusions": list(exclusions),
        "details": dict(details),
    }


def _normative_implementation_metric(
    requirements: Mapping[str, Any],
    graph: Graph,
    shape_path: str,
) -> dict[str, Any]:
    evaluated: list[dict[str, Any]] = []
    for requirement in requirements.get("requirements", []):
        if not isinstance(requirement, dict) or requirement.get("rule_kind") != "NORMATIVE_SHACL":
            continue
        evidence: list[str] = []
        passed = True
        locators = [
            source.get("locator", {})
            for source in requirement.get("sources", [])
            if isinstance(source, dict) and source.get("source_type") == "NORMATIVE"
        ]
        shape_locators = [locator for locator in locators if locator.get("shape")]
        if not shape_locators:
            passed = False
            evidence.append("no normative Shape locator")
        for locator in shape_locators:
            shape_value = _expand_curie(str(locator.get("shape")))
            if shape_value is None:
                passed = False
                evidence.append("invalid Shape CURIE")
                continue
            shape = URIRef(shape_value)
            if not any(graph.triples((shape, RDF.type, None))):
                passed = False
                evidence.append(f"missing {locator.get('shape')}")
                continue
            path_value = locator.get("path")
            if isinstance(path_value, str):
                expected_path = _expand_curie(path_value)
                actual_paths = {str(value) for value in graph.objects(shape, SH.path)}
                if expected_path not in actual_paths:
                    passed = False
                    evidence.append(f"path mismatch for {locator.get('shape')}")
            for constraint in locator.get("constraints", []):
                if not isinstance(constraint, dict):
                    continue
                predicate_value = _expand_curie(str(constraint.get("predicate")))
                if predicate_value is None or not any(
                    graph.triples((shape, URIRef(predicate_value), None))
                ):
                    passed = False
                    evidence.append(
                        f"missing constraint predicate {constraint.get('predicate')}"
                    )
        implemented_shape_ref = any(
            isinstance(ref, dict)
            and ref.get("status") == "IMPLEMENTED"
            and ref.get("path") == shape_path
            for ref in requirement.get("implementation", {}).get("artifact_refs", [])
        )
        if not implemented_shape_ref:
            passed = False
            evidence.append("no implemented release-Shape artifact reference")
        evaluated.append(
            {
                "requirement_id": requirement.get("id"),
                "implemented": passed,
                "evidence": evidence or ["normative Shape, path, constraints, and artifact binding present"],
            }
        )
    return _metric(
        EXPECTED_METRIC_IDS[0],
        "D-group normative requirement implementation coverage",
        sum(1 for item in evaluated if item["implemented"]),
        len(evaluated),
        [
            "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
            shape_path,
        ],
        ["D04-R017 is operational classification policy and is excluded from the normative SHACL denominator."],
        {"requirements": evaluated},
    )


def _automated_test_metric(
    requirements: Mapping[str, Any], test_cases: Mapping[str, Any]
) -> dict[str, Any]:
    requirement_ids = {
        item["id"]
        for item in requirements.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    coverage: dict[str, list[str]] = defaultdict(list)
    for case in test_cases.get("cases", []):
        if not isinstance(case, dict):
            continue
        for requirement_id in case.get("requirement_ids", []):
            coverage[str(requirement_id)].append(str(case.get("case_id")))
    details = {
        requirement_id: sorted(coverage.get(requirement_id, []))
        for requirement_id in sorted(requirement_ids)
    }
    return _metric(
        EXPECTED_METRIC_IDS[1],
        "Requirement automated-test coverage",
        sum(1 for requirement_id in requirement_ids if coverage.get(requirement_id)),
        len(requirement_ids),
        [
            "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
            "C_Semantic_Treehouse/manifests/v0.4-test-cases.json",
        ],
        ["No registered requirement is excluded; operational classification D04-R017 remains in scope."],
        {"cases_by_requirement": details},
    )


def _field_metric(requirements: Mapping[str, Any], graph: Graph, shape_path: str) -> dict[str, Any]:
    fields: list[dict[str, Any]] = []
    for requirement in requirements.get("requirements", []):
        if not isinstance(requirement, dict):
            continue
        for source in requirement.get("sources", []):
            if not isinstance(source, dict) or source.get("source_type") != "NORMATIVE":
                continue
            locator = source.get("locator", {})
            path_curie = locator.get("path")
            shape_curie = locator.get("shape")
            if not isinstance(path_curie, str) or not isinstance(shape_curie, str):
                continue
            path_iri = _expand_curie(path_curie)
            shape_iri = _expand_curie(shape_curie)
            required = "sh:MinCountConstraintComponent" in locator.get(
                "constraint_components", []
            )
            represented = bool(
                path_iri
                and shape_iri
                and (URIRef(shape_iri), SH.path, URIRef(path_iri)) in graph
            )
            fields.append(
                {
                    "requirement_id": requirement.get("id"),
                    "shape": shape_curie,
                    "path": path_curie,
                    "required": required,
                    "represented": represented,
                }
            )
    required_fields = [item for item in fields if item["required"]]
    optional_fields = [item for item in fields if not item["required"]]
    return _metric(
        EXPECTED_METRIC_IDS[2],
        "Required and optional field coverage",
        sum(1 for item in fields if item["represented"]),
        len(fields),
        [
            "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
            shape_path,
        ],
        ["Node-level cardinality, target, temporal-order, closed-shape, and operational-classification rules have no field path and are excluded."],
        {
            "required": {
                "numerator": sum(1 for item in required_fields if item["represented"]),
                "denominator": len(required_fields),
            },
            "optional": {
                "numerator": sum(1 for item in optional_fields if item["represented"]),
                "denominator": len(optional_fields),
            },
            "fields": fields,
        },
    )


def _constraint_metric(graph: Graph, shape_path: str) -> dict[str, Any]:
    predicates = {
        "min_count": SH.minCount,
        "max_count": SH.maxCount,
        "datatype": SH.datatype,
        "pattern": SH.pattern,
        "in": SH["in"],
        "node_kind": SH.nodeKind,
        "sparql": SH.sparql,
        "closed": SH.closed,
    }
    counts = {
        name: sum(1 for _ in graph.triples((None, predicate, None)))
        for name, predicate in predicates.items()
    }
    total = sum(counts.values())
    distribution = {
        name: {
            "numerator": count,
            "denominator": total,
            "ratio": round(count / total, 6) if total else None,
        }
        for name, count in sorted(counts.items())
    }
    return _metric(
        EXPECTED_METRIC_IDS[3],
        "Constraint-component distribution coverage",
        sum(1 for count in counts.values() if count > 0),
        len(predicates),
        [shape_path],
        ["Target declarations, names, messages, severities, ignored properties, minLength, and nested sh:property wiring are outside the requested eight-category distribution."],
        {"occurrence_total": total, "distribution": distribution},
    )


def _four_state_metric(test_cases: Mapping[str, Any]) -> dict[str, Any]:
    expected = ("PASS", "FAIL", "INAPPLICABLE", "UNTESTABLE")
    counts = Counter(
        case.get("expected_business_status")
        for case in test_cases.get("cases", [])
        if isinstance(case, dict)
    )
    return _metric(
        EXPECTED_METRIC_IDS[4],
        "Four-state automated-case coverage",
        sum(1 for status in expected if counts[status] > 0),
        len(expected),
        ["C_Semantic_Treehouse/manifests/v0.4-test-cases.json"],
        ["Harness PROGRAM ERROR controls are evidence for fail-closed execution and are excluded from the four business-state denominator."],
        {"case_counts": {status: counts[status] for status in expected}},
    )


def _external_standard_metric(
    field_metric: Mapping[str, Any], rows: list[dict[str, str]], shape_path: str
) -> dict[str, Any]:
    fields = field_metric["details"]["fields"]
    paths = {str(item["path"]) for item in fields}
    external_paths = {
        path for path in paths if path.startswith(("dct:", "dcat:"))
    }
    local_paths = {path for path in paths if path.startswith("ex:")}
    direct_rows = {
        row["subject_id"]
        for row in rows
        if row["mapping_category"] == "direct_reuse"
        and row["subject_id"] == row["object_id"]
    }
    mapped_local_paths = {
        row["subject_id"]
        for row in rows
        if row["mapping_category"] == "external_alignment"
        and row["subject_id"] in local_paths
        and not row["object_id"].startswith(("ex:", "be:"))
    }
    direct_audited = sorted(external_paths & direct_rows)
    return _metric(
        EXPECTED_METRIC_IDS[5],
        "External-standard direct reuse and local-term mapping",
        len(external_paths),
        len(paths),
        [shape_path, MAPPING_RELPATH],
        ["RDF/SHACL vocabulary terms, rdf:type, ignored-properties inventory, and the inherited record contract are excluded from the v0.4 metadata field denominator."],
        {
            "direct_external_reuse": {
                "numerator": len(external_paths),
                "denominator": len(paths),
                "paths": sorted(external_paths),
            },
            "direct_reuse_sssom_audit": {
                "numerator": len(direct_audited),
                "denominator": len(external_paths),
                "paths": direct_audited,
            },
            "local_term_external_mapping": {
                "numerator": len(mapped_local_paths),
                "denominator": len(local_paths),
                "paths": sorted(mapped_local_paths),
            },
        },
    )


def _has_mapping(
    rows: list[dict[str, str]], subject: str, object_id: str, category: str
) -> bool:
    return any(
        row["subject_id"] == subject
        and row["object_id"] == object_id
        and row["mapping_category"] == category
        for row in rows
    )


def _breaking_change_metric(
    release_inputs: Mapping[str, Any], rows: list[dict[str, str]]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    graph: Graph = release_inputs["metadata_graph"]
    current_context = release_inputs["current_context"]
    prior_context = release_inputs["prior_context"]
    current_example = release_inputs["current_example"]
    prior_example = release_inputs["prior_example"]
    shape_path = release_inputs["artifacts"]["metadata_shapes"]["path"]
    current = release_inputs["current"]
    prior_id = release_inputs["prior_id"]
    facts: list[dict[str, Any]] = []

    def add(fact_id: str, fact: str, verified: bool, evidence: str) -> None:
        facts.append(
            {
                "id": fact_id,
                "fact": fact,
                "verified": bool(verified),
                "evidence": evidence,
            }
        )

    add(
        "BC-01",
        "be:DataProductMetadata migrates to dcat:Dataset.",
        _context_term(prior_context, "DataProductMetadata") == str(BE.DataProductMetadata)
        and _context_term(current_context, "Dataset") == str(DCAT.Dataset)
        and _has_mapping(rows, "be:DataProductMetadata", "dcat:Dataset", "migration"),
        "Prior/current contexts plus the cumulative migration row.",
    )
    add(
        "BC-02",
        "dct:identifier migrates to ex:datasetId.",
        _context_term(prior_context, "datasetId") == str(DCT.identifier)
        and _context_term(current_context, "datasetId") == str(EX.datasetId)
        and _has_mapping(rows, "dct:identifier", "ex:datasetId", "migration"),
        "Prior/current contexts plus the cumulative migration row.",
    )
    transitions = (
        ("BC-03", "providerName", "providerName", "be:providerName", "ex:providerName"),
        ("BC-04", "endpointUrl", "endpointUrl", "be:endpointUrl", "dcat:endpointURL"),
        ("BC-05", "format", "format", "be:format", "dct:format"),
        ("BC-06", "frequency", "frequency", "be:frequency", "dct:accrualPeriodicity"),
        ("BC-07", "unit", "unit", "be:unit", "ex:unit"),
        ("BC-08", "spatialCoverage", "spatial", "be:spatialCoverage", "dct:spatial"),
        ("BC-09", "temporalStart", "temporalStart", "be:temporalStart", "ex:temporalStart"),
        ("BC-10", "temporalEnd", "temporalEnd", "be:temporalEnd", "ex:temporalEnd"),
    )
    for fact_id, prior_term, current_term, source, target in transitions:
        add(
            fact_id,
            f"{source} migrates to {target}.",
            _context_term(prior_context, prior_term) == _expand_curie(source)
            and _context_term(current_context, current_term) == _expand_curie(target)
            and _has_mapping(rows, source, target, "migration"),
            "Prior/current contexts plus the cumulative migration row.",
        )
    add(
        "BC-11",
        "The format token changes from JSON to application/json.",
        prior_example.get("format") == "JSON"
        and current_example.get("format") == "application/json"
        and any(graph.objects(EX.FormatShape, SH["in"]))
        and (None, RDF.first, Literal("application/json")) in graph,
        "Prior/current release examples and ex:FormatShape sh:in list.",
    )
    https_shapes = (EX.EndpointUrlShape, EX.LicenseShape)
    add(
        "BC-12",
        "Endpoint and supplied license IRIs require HTTPS.",
        all(
            any(str(value) == "^https://" for value in graph.objects(shape, SH.pattern))
            for shape in https_shapes
        ),
        "Actual v0.4 SHACL pattern constraints.",
    )
    add(
        "BC-13",
        "Each submission graph must contain exactly one dcat:Dataset.",
        any(graph.objects(EX.DatasetCardinalityShape, SH.sparql)),
        "Actual v0.4 DatasetCardinalityShape SPARQL constraint.",
    )
    field_shapes = {
        subject
        for subject in graph.subjects(RDF.type, SH.PropertyShape)
        if isinstance(subject, URIRef)
    }
    add(
        "BC-14",
        "All twelve declared metadata fields are single-valued.",
        len(field_shapes) == 12
        and all((shape, SH.maxCount, Literal(1)) in graph for shape in field_shapes),
        "Actual v0.4 named PropertyShapes and sh:maxCount values.",
    )
    non_blank_shapes = (
        EX.DatasetIdShape,
        EX.TitleShape,
        EX.ProviderNameShape,
        EX.SpatialShape,
    )
    add(
        "BC-15",
        "Required free-text identifiers and labels reject empty or whitespace-only values.",
        all(
            (shape, SH.minLength, Literal(1)) in graph
            and any(str(value) == "\\S" for value in graph.objects(shape, SH.pattern))
            for shape in non_blank_shapes
        ),
        "Actual v0.4 minLength and non-whitespace pattern constraints.",
    )
    add(
        "BC-16",
        "temporalStart must not be later than temporalEnd.",
        any(graph.objects(EX.TemporalOrderShape, SH.sparql)),
        "Actual v0.4 TemporalOrderShape SPARQL constraint.",
    )
    add(
        "BC-17",
        "Undeclared Dataset properties activate the closed-shape Warning behavior.",
        any(str(value).lower() == "true" for value in graph.objects(EX.DatasetClosedShape, SH.closed))
        and (EX.DatasetClosedShape, SH.severity, SH.Warning) in graph,
        "Actual v0.4 DatasetClosedShape closed flag and severity.",
    )
    inherited_records = [
        artifact
        for artifact in current.get("artifacts", [])
        if isinstance(artifact, dict)
        and str(artifact.get("role", "")).startswith("record-")
        and artifact.get("origin", {}).get("type") == "inherited"
    ]
    add(
        "BC-18",
        "The Energy Reading Record contract remains the actual prior-release contract unchanged.",
        len(inherited_records) == 5
        and all(
            artifact["origin"].get("inheritedFrom") == prior_id
            and artifact["origin"].get("change") == "none"
            for artifact in inherited_records
        ),
        "Current release-manifest inherited record artifacts and their byte bindings.",
    )
    add(
        "BC-19",
        "description and license are explicit optional single-valued fields.",
        all(
            (shape, SH.maxCount, Literal(1)) in graph
            and not any(graph.objects(shape, SH.minCount))
            for shape in (EX.DescriptionShape, EX.LicenseShape)
        ),
        "Actual v0.4 optional PropertyShapes.",
    )
    add(
        "BC-20",
        "The release classifies the metadata migration as wire-profile-breaking.",
        current.get("compatibilityClassification") == "wire-profile-breaking",
        "Validated release-manifest compatibilityClassification.",
    )
    conclusion = {
        "classification": "INCOMPATIBLE_WIRE_PROFILE",
        "metadata_profile": (
            "v0.4 metadata is a wire-profile-breaking migration from the prior release; "
            "producers and consumers must migrate class, predicates, values, cardinality, "
            "HTTPS, blank-value, temporal-order, and closed-shape behavior."
        ),
        "record_profile": (
            "The Energy Reading Record remains byte-bound to the inherited prior-release "
            "contract with change=none."
        ),
    }
    metric = _metric(
        EXPECTED_METRIC_IDS[6],
        "Breaking-change fact coverage",
        sum(1 for fact in facts if fact["verified"]),
        len(facts),
        [
            "C_Semantic_Treehouse/manifests/release-manifest.json",
            shape_path,
            release_inputs["artifacts"]["metadata_context"]["path"],
            release_inputs["artifacts"]["prior_metadata_context"]["path"],
            release_inputs["artifacts"]["metadata_example"]["path"],
            release_inputs["artifacts"]["prior_metadata_example"]["path"],
            MAPPING_RELPATH,
        ],
        ["Business-domain acceptance and downstream deployment observations remain pending human/external evidence and are excluded from machine-verified facts."],
        {"facts": facts, "conclusion": conclusion},
    )
    return metric, facts, conclusion


def _provenance_metric(
    release_manifest: Mapping[str, Any], requirements: Mapping[str, Any], registry_sha256: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    current = _release_by_id(release_manifest, str(release_manifest.get("currentRelease")))
    requirement_ids = {
        item.get("id")
        for item in requirements.get("requirements", [])
        if isinstance(item, dict)
    }
    declared_requirement_ids = {
        requirement_id
        for binding in current.get("requirementRegistryRefs", [])
        if isinstance(binding, dict)
        for requirement_id in binding.get("requirementIds", [])
    }
    artifacts = [item for item in current.get("artifacts", []) if isinstance(item, dict)]
    source_catalog = [
        item for item in release_manifest.get("sourceCatalog", []) if isinstance(item, dict)
    ]
    derived_sources = [
        source
        for artifact in artifacts
        if artifact.get("origin", {}).get("type") == "derived"
        for source in artifact.get("origin", {}).get("sources", [])
        if isinstance(source, dict)
    ]
    inherited = [
        artifact
        for artifact in artifacts
        if artifact.get("origin", {}).get("type") == "inherited"
    ]
    registry_binding = release_manifest.get("validationSuiteRegistry", {})
    checks = [
        ("RP-01", "current release identifier", release_manifest.get("currentRelease") == current.get("id")),
        ("RP-02", "release status", current.get("status") == "current"),
        ("RP-03", "version IRI", isinstance(current.get("versionIri"), str) and current["versionIri"].startswith("https://")),
        ("RP-04", "release root", isinstance(current.get("root"), str) and bool(current.get("root"))),
        ("RP-05", "prior release", isinstance(current.get("priorRelease"), str) and bool(current.get("priorRelease"))),
        ("RP-06", "compatibility classification", current.get("compatibilityClassification") == "wire-profile-breaking"),
        ("RP-07", "normative input references", bool(current.get("normativeInputRefs"))),
        ("RP-08", "applicable validator references", bool(current.get("applicableValidatorRefs"))),
        ("RP-09", "complete requirement binding", declared_requirement_ids == requirement_ids),
        ("RP-10", "artifact identity/hash/media completeness", bool(artifacts) and all(all(artifact.get(key) for key in ("id", "role", "path", "mediaType", "sha256")) for artifact in artifacts)),
        ("RP-11", "artifact provenance type", all(artifact.get("origin", {}).get("type") in {"derived", "inherited"} for artifact in artifacts)),
        ("RP-12", "derived source path/hash provenance", bool(derived_sources) and all(source.get("path") and source.get("sha256") for source in derived_sources)),
        ("RP-13", "inherited source/change provenance", bool(inherited) and all(origin.get("inheritedFrom") and origin.get("sourceArtifact") and origin.get("change") == "none" for origin in (artifact.get("origin", {}) for artifact in inherited))),
        ("RP-14", "source catalog path/hash provenance", bool(source_catalog) and all(item.get("id") and item.get("kind") and item.get("path") and item.get("sha256") for item in source_catalog)),
        ("RP-15", "suite registry version/hash binding", registry_binding.get("contractVersion") == EXPECTED_CONTRACT_VERSION and registry_binding.get("sha256") == registry_sha256),
    ]
    records = [
        {"id": check_id, "assertion": assertion, "complete": bool(complete)}
        for check_id, assertion, complete in checks
    ]
    return (
        _metric(
            EXPECTED_METRIC_IDS[7],
            "Release and provenance metadata completeness",
            sum(1 for item in records if item["complete"]),
            len(records),
            [
                "C_Semantic_Treehouse/manifests/release-manifest.json",
                "C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json",
                "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
                "C_Semantic_Treehouse/manifests/validation-suites.json",
            ],
            ["Pending human approvals, CI runs, external publication, and Semantic Treehouse execution are excluded because they have not occurred."],
            {"assertions": records},
        ),
        records,
    )


def _metric_issues(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    ids = [metric.get("id") for metric in metrics]
    if tuple(ids) != EXPECTED_METRIC_IDS:
        issues.append(
            {
                "code": "METRIC_SET",
                "message": "Metric IDs or deterministic order differ from the eight-item contract.",
            }
        )
    duplicates = sorted(
        str(metric_id) for metric_id, count in Counter(ids).items() if count > 1
    )
    if duplicates:
        issues.append({"code": "DUPLICATE_METRIC_ID", "message": ", ".join(duplicates)})
    for index, metric in enumerate(metrics):
        numerator = metric.get("numerator")
        denominator = metric.get("denominator")
        if not isinstance(numerator, int) or numerator < 0:
            issues.append({"code": "INVALID_NUMERATOR", "message": str(index)})
        if not isinstance(denominator, int) or denominator <= 0:
            issues.append({"code": "ZERO_DENOMINATOR", "message": str(index)})
        elif isinstance(numerator, int) and numerator > denominator:
            issues.append({"code": "NUMERATOR_EXCEEDS_DENOMINATOR", "message": str(index)})
        if not isinstance(metric.get("sources"), list) or not metric["sources"]:
            issues.append({"code": "MISSING_METRIC_SOURCES", "message": str(index)})
        if not isinstance(metric.get("exclusions"), list) or not metric["exclusions"]:
            issues.append({"code": "MISSING_METRIC_EXCLUSIONS", "message": str(index)})
    return sorted(issues, key=lambda item: (item["code"], item["message"]))


def _collect_sources(
    root: Path,
    preflight: Mapping[str, Any],
    release_inputs: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    roles: dict[str, set[str]] = defaultdict(set)
    for record in preflight["manifest_records"]:
        roles[record["path"]].add(f"manifest:{record['id']}")
        roles[record["schema_path"]].add(f"schema:{record['id']}")
    release_manifest = preflight["release"]
    for source in release_manifest.get("sourceCatalog", []):
        if isinstance(source, dict) and isinstance(source.get("path"), str):
            roles[source["path"]].add("release-source-catalog")
    for release in release_manifest.get("releases", []):
        if not isinstance(release, dict):
            continue
        for artifact in release.get("artifacts", []):
            if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
                roles[artifact["path"]].add(f"release-artifact:{release.get('id')}")
    baseline = preflight["baseline"]
    for artifact in baseline.artifacts:
        roles[artifact.path].add("baseline-preflight-artifact")
    for case in preflight["test_cases"].get("cases", []):
        fixture = case.get("fixture", {}) if isinstance(case, dict) else {}
        if isinstance(fixture, dict) and isinstance(fixture.get("path"), str):
            roles[fixture["path"]].add("v0.4-fixture-preflight")
    roles[MAPPING_RELPATH].add("quality-sssom")
    roles[SPARQL_MANIFEST_RELPATH].add("phase06-sparql-test-manifest")
    roles[SPARQL_SCHEMA_RELPATH].add("phase06-sparql-test-manifest-schema")
    for artifact in release_inputs["artifacts"].values():
        roles[str(artifact["path"])].add("quality-metric-input")

    consumed = [
        _hash_record(root, relpath, source_roles)
        for relpath, source_roles in sorted(roles.items())
    ]
    source_code = [
        _hash_record(root, relpath, ["quality-runner-or-helper"])
        for relpath in SOURCE_CODE_RELPATHS
    ]
    return consumed, source_code


def _freshness_issues(
    root: Path, result: Mapping[str, Any]
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    records = list(result.get("consumed_sources", [])) + list(
        result.get("source_code", [])
    )
    seen: set[str] = set()
    for record in records:
        path_value = record.get("path") if isinstance(record, dict) else None
        expected = record.get("sha256") if isinstance(record, dict) else None
        if not isinstance(path_value, str) or path_value in seen:
            issues.append({"code": "SOURCE_RECORD", "path": str(path_value)})
            continue
        seen.add(path_value)
        path = _repo_path(root, path_value)
        actual = sha256_file(path) if path.is_file() else None
        if actual != expected:
            issues.append({"code": "STALE_SOURCE_HASH", "path": path_value})
    return sorted(issues, key=lambda item: (item["code"], item["path"]))


def _negative_controls(
    root: Path,
    preflight: Mapping[str, Any],
    fieldnames: list[str],
    rows: list[dict[str, str]],
    metrics: list[dict[str, Any]],
    result_for_freshness: Mapping[str, Any],
) -> dict[str, Any]:
    controls: list[dict[str, Any]] = []

    def append_control(
        control_id: str, expected_code: str, observed_codes: Iterable[str]
    ) -> None:
        observed = sorted(set(observed_codes))
        controls.append(
            {
                "id": control_id,
                "expected_code": expected_code,
                "observed_codes": observed,
                "passed": expected_code in observed,
            }
        )

    def mapping_control(
        control_id: str, mutate: Any, expected_code: str
    ) -> None:
        candidate = copy.deepcopy(rows)
        mutate(candidate)
        observed = sorted({issue["code"] for issue in _sssom_issues(fieldnames, candidate)})
        append_control(control_id, expected_code, observed)

    mapping_control(
        "sssom.invalid-iri",
        lambda candidate: candidate[0].__setitem__("subject_id", "invalid term"),
        "INVALID_IRI_OR_CURIE",
    )
    mapping_control(
        "sssom.invalid-predicate",
        lambda candidate: candidate[0].__setitem__("predicate_id", "skos:broadMatch"),
        "INVALID_MAPPING_PREDICATE",
    )
    mapping_control(
        "sssom.duplicate-row",
        lambda candidate: candidate.append(copy.deepcopy(candidate[0])),
        "DUPLICATE_MAPPING",
    )

    def unmark_self(candidate: list[dict[str, str]]) -> None:
        index = next(
            position
            for position, row in enumerate(candidate)
            if row["subject_id"] == row["object_id"]
        )
        candidate[index]["mapping_category"] = "external_alignment"

    mapping_control(
        "sssom.unjustified-self-mapping",
        unmark_self,
        "UNJUSTIFIED_SELF_MAPPING",
    )
    mapping_control(
        "sssom.empty-justification",
        lambda candidate: candidate[0].__setitem__("mapping_justification", ""),
        "EMPTY_REQUIRED_CELL",
    )
    mapping_control(
        "sssom.invalid-confidence",
        lambda candidate: candidate[0].__setitem__("confidence", "1.5"),
        "INVALID_CONFIDENCE",
    )
    mapping_control(
        "sssom.missing-review-status",
        lambda candidate: candidate[0].__setitem__("review_status", ""),
        "EMPTY_REQUIRED_CELL",
    )

    duplicate_metrics = copy.deepcopy(metrics)
    duplicate_metrics.append(copy.deepcopy(duplicate_metrics[0]))
    observed = sorted({issue["code"] for issue in _metric_issues(duplicate_metrics)})
    append_control("metrics.duplicate-id", "DUPLICATE_METRIC_ID", observed)
    zero_metrics = copy.deepcopy(metrics)
    zero_metrics[0]["denominator"] = 0
    observed = sorted({issue["code"] for issue in _metric_issues(zero_metrics)})
    append_control("metrics.zero-denominator", "ZERO_DENOMINATOR", observed)
    stale = copy.deepcopy(result_for_freshness)
    stale["consumed_sources"][0]["sha256"] = "0" * 64
    observed = sorted(
        {issue["code"] for issue in _freshness_issues(root, stale)}
    )
    append_control("freshness.stale-source-hash", "STALE_SOURCE_HASH", observed)

    work_parent = _repo_path(root, "build/phase-06/quality")
    work_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="manifest-negative-", dir=str(work_parent)
    ) as temporary:
        temporary_root = Path(temporary)

        def candidate_path(name: str, value: Mapping[str, Any]) -> Path:
            path = temporary_root / name
            atomic_write_json(path, value)
            return path

        release_schema = _repo_path(
            root,
            "C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json",
        )
        for control_id, expected_code, mutate in (
            (
                "manifest.release.duplicate-id",
                "DUPLICATE_RELEASE_ID",
                lambda value: value["releases"][1].__setitem__(
                    "id", value["releases"][0]["id"]
                ),
            ),
            (
                "manifest.release.dangling-reference",
                "DANGLING_SOURCE_REFERENCE",
                lambda value: value["releases"][-1]["normativeInputRefs"].__setitem__(
                    0, "missing-source"
                ),
            ),
        ):
            candidate = copy.deepcopy(preflight["release"])
            mutate(candidate)
            audit = load_and_audit_release_manifest(
                root,
                manifest_path=candidate_path(f"{control_id}.json", candidate),
                schema_path=release_schema,
            )
            append_control(
                control_id,
                expected_code,
                [str(issue.get("code")) for issue in audit.issues],
            )

        baseline_schema = preflight["baseline"].schema_path
        baseline_document = preflight["baseline"].manifest
        for control_id, expected_code, mutate in (
            (
                "manifest.baseline.duplicate-id",
                "duplicate_case_id",
                lambda value: value["cases"][1].__setitem__(
                    "id", value["cases"][0]["id"]
                ),
            ),
            (
                "manifest.baseline.dangling-reference",
                "dangling_artifact_reference",
                lambda value: value["cases"][0]["artifact_refs"].__setitem__(
                    "input", "missing-artifact"
                ),
            ),
        ):
            candidate = copy.deepcopy(baseline_document)
            mutate(candidate)
            observed_codes: list[str] = []
            try:
                load_and_validate_baseline_manifest(
                    root,
                    manifest_path=candidate_path(f"{control_id}.json", candidate),
                    schema_path=baseline_schema,
                )
            except BaselineManifestError as exc:
                observed_codes = [issue.code for issue in exc.issues]
            append_control(control_id, expected_code, observed_codes)

        requirements_schema = _repo_path(
            root,
            "C_Semantic_Treehouse/manifests/schemas/v0.4-requirements.schema.json",
        )
        for control_id, expected_code, mutate in (
            (
                "manifest.requirements.duplicate-id",
                "DUPLICATE_REQUIREMENT_ID",
                lambda value: value["requirements"][1].__setitem__(
                    "id", value["requirements"][0]["id"]
                ),
            ),
            (
                "manifest.requirements.dangling-reference",
                "DANGLING_DECISION_REFERENCE",
                lambda value: value["requirements"][0]["decision_refs"].__setitem__(
                    0, "docs/v0.4/decisions/missing.md"
                ),
            ),
        ):
            candidate = copy.deepcopy(preflight["requirements"])
            mutate(candidate)
            validation = load_and_validate_requirements(
                root,
                manifest_path=candidate_path(f"{control_id}.json", candidate),
                schema_path=requirements_schema,
            )
            append_control(
                control_id,
                expected_code,
                [str(issue.get("code")) for issue in validation.issues],
            )

        test_schema = _repo_path(
            root,
            "C_Semantic_Treehouse/manifests/schemas/v0.4-test-cases.schema.json",
        )
        for control_id, expected_code, mutate in (
            (
                "manifest.v0.4-test-cases.duplicate-id",
                "DUPLICATE_CASE_ID",
                lambda value: value["cases"][1].__setitem__(
                    "case_id", value["cases"][0]["case_id"]
                ),
            ),
            (
                "manifest.v0.4-test-cases.dangling-reference",
                "DANGLING_REQUIREMENT_REFERENCE",
                lambda value: value["cases"][0]["requirement_ids"].__setitem__(
                    0, "D04-R999"
                ),
            ),
        ):
            candidate = copy.deepcopy(preflight["test_cases"])
            mutate(candidate)
            validation = load_and_validate_v04_manifest(
                root,
                manifest_path=candidate_path(f"{control_id}.json", candidate),
                schema_path=test_schema,
                verify_fixture_hashes=False,
            )
            append_control(
                control_id,
                expected_code,
                [issue.code for issue in validation.issues],
            )

        registry_schema = _repo_path(
            root,
            "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json",
        )
        for control_id, expected_code, mutate in (
            (
                "manifest.validation-suites.duplicate-id",
                "duplicate_suite_id",
                lambda value: value["suites"][1].__setitem__(
                    "id", value["suites"][0]["id"]
                ),
            ),
            (
                "manifest.validation-suites.dangling-reference",
                "dangling_dependency",
                lambda value: value["suites"][1].__setitem__(
                    "depends_on", ["missing-suite"]
                ),
            ),
        ):
            candidate = copy.deepcopy(preflight["registry"])
            mutate(candidate)
            validation = load_and_validate_registry(
                root,
                registry_path=candidate_path(f"{control_id}.json", candidate),
                schema_path=registry_schema,
            )
            append_control(
                control_id,
                expected_code,
                [issue.code for issue in validation.issues],
            )
    return {
        "schema": "dssc.phase06.quality.negative-controls.v1",
        "status": "PASS" if all(item["passed"] for item in controls) else "FAIL",
        "control_count": len(controls),
        "passed_count": sum(1 for item in controls if item["passed"]),
        "failed_count": sum(1 for item in controls if not item["passed"]),
        "controls": controls,
    }


def _calculate_quality(
    root: Path, preflight: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows, sssom = _validate_sssom(root)
    release_inputs = _current_release_inputs(root, preflight["release"])
    shape_path = str(release_inputs["artifacts"]["metadata_shapes"]["path"])
    graph: Graph = release_inputs["metadata_graph"]
    metrics: list[dict[str, Any]] = []
    metrics.append(
        _normative_implementation_metric(preflight["requirements"], graph, shape_path)
    )
    metrics.append(
        _automated_test_metric(preflight["requirements"], preflight["test_cases"])
    )
    field_metric = _field_metric(preflight["requirements"], graph, shape_path)
    metrics.append(field_metric)
    metrics.append(_constraint_metric(graph, shape_path))
    metrics.append(_four_state_metric(preflight["test_cases"]))
    metrics.append(_external_standard_metric(field_metric, rows, shape_path))
    breaking_metric, breaking_facts, conclusion = _breaking_change_metric(
        release_inputs, rows
    )
    metrics.append(breaking_metric)
    provenance_metric, provenance_assertions = _provenance_metric(
        preflight["release"], preflight["requirements"], preflight["registry_sha256"]
    )
    metrics.append(provenance_metric)

    metric_issues = _metric_issues(metrics)
    if metric_issues:
        raise QualityFailure(
            "METRIC_CONTRACT_FAILED",
            "Generated metrics failed numerator, denominator, source, exclusion, or ID checks.",
            {"issues": metric_issues},
        )
    if any(metric["numerator"] != metric["denominator"] for metric in metrics[:5]):
        raise QualityFailure(
            "QUALITY_COVERAGE_GAP",
            "A required implementation, test, field, constraint-category, or four-state coverage metric is incomplete.",
            {"metrics": metrics[:5]},
        )
    external_details = metrics[5]["details"]
    if (
        external_details["direct_reuse_sssom_audit"]["numerator"]
        != external_details["direct_reuse_sssom_audit"]["denominator"]
        or external_details["local_term_external_mapping"]["numerator"]
        != external_details["local_term_external_mapping"]["denominator"]
    ):
        raise QualityFailure(
            "ALIGNMENT_COVERAGE_GAP",
            "An external direct-reuse path or local v0.4 term lacks SSSOM audit coverage.",
            external_details,
        )
    if breaking_metric["numerator"] != breaking_metric["denominator"]:
        raise QualityFailure(
            "BREAKING_FACT_GAP",
            "The required breaking-change fact inventory is incomplete.",
            {"facts": breaking_facts},
        )
    if provenance_metric["numerator"] != provenance_metric["denominator"]:
        raise QualityFailure(
            "PROVENANCE_COMPLETENESS_GAP",
            "Release/provenance metadata is incomplete.",
            {"assertions": provenance_assertions},
        )

    consumed_sources, source_code = _collect_sources(root, preflight, release_inputs)
    source_by_path = {record["path"]: record for record in consumed_sources}
    status_counts = metrics[4]["details"]["case_counts"]
    preliminary: dict[str, Any] = {
        "schema": "dssc.phase06.quality.results.v1",
        "suite": "quality",
        "release": release_inputs["current_id"],
        "status": "PASS",
        "program_status": "SUCCESS",
        "message": "Eight semantic-quality metric families passed with fresh deterministic evidence.",
        "manifest_preflight": {
            "status": "PASS",
            "checks": preflight["checks"],
            "manifests": preflight["manifest_records"],
        },
        "validation_suite_registry": {
            "path": "C_Semantic_Treehouse/manifests/validation-suites.json",
            "contract_version": EXPECTED_CONTRACT_VERSION,
            "sha256": preflight["registry_sha256"],
        },
        "sparql_test_manifest": {
            "path": SPARQL_MANIFEST_RELPATH,
            "sha256": source_by_path[SPARQL_MANIFEST_RELPATH]["sha256"],
            "schema_path": SPARQL_SCHEMA_RELPATH,
            "schema_sha256": source_by_path[SPARQL_SCHEMA_RELPATH]["sha256"],
        },
        "sssom": sssom,
        "metric_count": len(metrics),
        "metrics": metrics,
        "breaking_change": {
            "facts": breaking_facts,
            "conclusion": conclusion,
        },
        "release_provenance": {"assertions": provenance_assertions},
        "four_state_case_counts": status_counts,
        "consumed_sources": consumed_sources,
        "source_code": source_code,
        "freshness": {"status": "PENDING", "issue_count": None},
        "negative_controls": {
            "path": NEGATIVE_CONTROL_RELPATH,
            "status": "PENDING",
            "control_count": None,
        },
        "outputs": {
            "results": RESULT_RELPATH,
            "report": REPORT_RELPATH,
            "assessment": ASSESSMENT_RELPATH,
            "environment": ENVIRONMENT_RELPATH,
            "determinism": DETERMINISM_RELPATH,
        },
        "checks": [],
    }
    fieldnames, _ = _read_sssom(_repo_path(root, MAPPING_RELPATH))
    controls = _negative_controls(
        root, preflight, fieldnames, rows, metrics, preliminary
    )
    if controls["status"] != "PASS":
        raise QualityFailure(
            "NEGATIVE_CONTROL_FAILED",
            "A quality fail-closed negative control did not detect its mutation.",
            controls,
        )
    preliminary["negative_controls"] = {
        "path": NEGATIVE_CONTROL_RELPATH,
        "sha256": _json_sha256(controls),
        "status": "PASS",
        "control_count": controls["control_count"],
        "passed_count": controls["passed_count"],
    }
    preliminary["freshness"] = {"status": "PASS", "issue_count": 0}
    preliminary["checks"] = [
        {"id": "manifest-schema-and-semantics", "status": "PASS"},
        {"id": "sssom-structure-and-semantics", "status": "PASS"},
        {"id": "eight-metric-contract", "status": "PASS"},
        {"id": "breaking-change-fact-inventory", "status": "PASS"},
        {"id": "release-provenance-completeness", "status": "PASS"},
        {"id": "source-hash-freshness", "status": "PASS"},
        {"id": "negative-controls", "status": "PASS"},
    ]
    freshness_issues = _freshness_issues(root, preliminary)
    if freshness_issues:
        raise QualityFailure(
            "SOURCE_FRESHNESS_FAILED",
            "A consumed input or source-code hash changed during quality calculation.",
            {"issues": freshness_issues},
        )
    return preliminary, controls


def _percent(metric: Mapping[str, Any]) -> str:
    ratio = metric.get("ratio")
    return "n/a" if ratio is None else f"{float(ratio):.2%}"


def _report_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 06 Quality Validation Report",
        "",
        f"Overall status: **{result['status']}**",
        "",
        f"Program status: **{result['program_status']}**",
        "",
        "## Checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in result["checks"]:
        lines.append(f"| `{check['id']}` | {check['status']} |")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "| Metric | Numerator | Denominator | Ratio |",
            "|---|---:|---:|---:|",
        ]
    )
    for metric in result["metrics"]:
        lines.append(
            f"| {metric['label']} | {metric['numerator']} | {metric['denominator']} | {_percent(metric)} |"
        )
    lines.extend(
        [
            "",
            "## Manifest preflight bindings",
            "",
            "| Manifest | Manifest SHA-256 | Schema | Schema SHA-256 |",
            "|---|---|---|---|",
        ]
    )
    for manifest in result["manifest_preflight"]["manifests"]:
        lines.append(
            f"| `{manifest['path']}` | `{manifest['sha256']}` | `{manifest['schema_path']}` | `{manifest['schema_sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## Contract and artifacts",
            "",
            f"- Registry contract: `{result['validation_suite_registry']['contract_version']}`",
            f"- Registry SHA-256: `{result['validation_suite_registry']['sha256']}`",
            f"- SPARQL test manifest: `{result['sparql_test_manifest']['path']}` / `{result['sparql_test_manifest']['sha256']}`",
            f"- SPARQL test schema: `{result['sparql_test_manifest']['schema_path']}` / `{result['sparql_test_manifest']['schema_sha256']}`",
            f"- SSSOM rows: {result['sssom']['row_count']}",
            f"- SSSOM SHA-256: `{result['sssom']['sha256']}`",
            f"- Negative controls: {result['negative_controls']['passed_count']}/{result['negative_controls']['control_count']}",
            f"- Negative-control SHA-256: `{result['negative_controls']['sha256']}`",
            f"- Consumed source records: {len(result['consumed_sources'])}",
            f"- Runner/helper source records: {len(result['source_code'])}",
            "",
            "## Runner, checker, reporter, and helper source hashes",
            "",
            "| Source | SHA-256 |",
            "|---|---|",
        ]
    )
    for source in result["source_code"]:
        lines.append(f"| `{source['path']}` | `{source['sha256']}` |")
    lines.extend(
        [
            "",
            "## Consumed source hash inventory",
            "",
            "| Source | Roles | SHA-256 |",
            "|---|---|---|",
        ]
    )
    for source in result["consumed_sources"]:
        lines.append(
            f"| `{source['path']}` | {', '.join(source['roles'])} | `{source['sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## Compatibility conclusion",
            "",
            f"**{result['breaking_change']['conclusion']['classification']}**",
            "",
            result["breaking_change"]["conclusion"]["metadata_profile"],
            "",
            result["breaking_change"]["conclusion"]["record_profile"],
            "",
        ]
    )
    return "\n".join(lines)


def _assessment_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# Model Quality Assessment — v0.4",
        "",
        "> This assessment is generated deterministically from validated manifests, the release-selected RDF/SHACL graphs, and the cumulative SSSOM table.",
        "",
        "## Executive conclusion",
        "",
        "The v0.4 D-group metadata contract has complete normative implementation, automated requirement, declared-field, requested constraint-category, and four-state case coverage in the current machine-readable authorities.",
        "",
        f"Compatibility classification: **{result['breaking_change']['conclusion']['classification']}**.",
        "",
        result["breaking_change"]["conclusion"]["metadata_profile"],
        "",
        result["breaking_change"]["conclusion"]["record_profile"],
        "",
        "## Metric summary",
        "",
        "| Metric | Numerator | Denominator | Ratio |",
        "|---|---:|---:|---:|",
    ]
    for metric in result["metrics"]:
        lines.append(
            f"| {metric['label']} | {metric['numerator']} | {metric['denominator']} | {_percent(metric)} |"
        )
    for metric in result["metrics"]:
        lines.extend(
            [
                "",
                f"## {metric['label']}",
                "",
                f"Numerator: **{metric['numerator']}**",
                "",
                f"Denominator: **{metric['denominator']}**",
                "",
                f"Ratio: **{_percent(metric)}**",
                "",
                "Sources:",
                "",
            ]
        )
        lines.extend(f"- `{source}`" for source in metric["sources"])
        lines.extend(["", "Exclusions:", ""])
        lines.extend(f"- {exclusion}" for exclusion in metric["exclusions"])

        if metric["id"] == "required_optional_field_coverage":
            details = metric["details"]
            lines.extend(
                [
                    "",
                    f"Required fields: {details['required']['numerator']}/{details['required']['denominator']}.",
                    "",
                    f"Optional fields: {details['optional']['numerator']}/{details['optional']['denominator']}.",
                    "",
                    "| Requirement | Shape | Path | Class | Represented |",
                    "|---|---|---|---|---|",
                ]
            )
            for field in details["fields"]:
                lines.append(
                    f"| `{field['requirement_id']}` | `{field['shape']}` | `{field['path']}` | {'required' if field['required'] else 'optional'} | {'yes' if field['represented'] else 'no'} |"
                )
        elif metric["id"] == "constraint_component_distribution":
            lines.extend(
                [
                    "",
                    "| Constraint category | Occurrences | Distribution denominator | Share |",
                    "|---|---:|---:|---:|",
                ]
            )
            for name, item in metric["details"]["distribution"].items():
                lines.append(
                    f"| `{name}` | {item['numerator']} | {item['denominator']} | {float(item['ratio']):.2%} |"
                )
        elif metric["id"] == "four_state_automated_case_coverage":
            lines.extend(["", "Automated case counts:", ""])
            for status, count in metric["details"]["case_counts"].items():
                lines.append(f"- `{status}`: {count}")
        elif metric["id"] == "external_standard_reuse_and_mapping":
            direct = metric["details"]["direct_external_reuse"]
            local = metric["details"]["local_term_external_mapping"]
            audit = metric["details"]["direct_reuse_sssom_audit"]
            lines.extend(
                [
                    "",
                    f"Direct external field reuse: {direct['numerator']}/{direct['denominator']}.",
                    "",
                    f"Direct-reuse SSSOM audit coverage: {audit['numerator']}/{audit['denominator']}.",
                    "",
                    f"Local ex:* term mapping coverage: {local['numerator']}/{local['denominator']}.",
                ]
            )

    lines.extend(
        [
            "",
            "## Breaking-change facts",
            "",
            "| ID | Verified fact | Status | Evidence basis |",
            "|---|---|---|---|",
        ]
    )
    for fact in result["breaking_change"]["facts"]:
        lines.append(
            f"| `{fact['id']}` | {fact['fact']} | {'VERIFIED' if fact['verified'] else 'MISSING'} | {fact['evidence']} |"
        )
    lines.extend(
        [
            "",
            "## Cumulative SSSOM audit",
            "",
            f"The table contains {result['sssom']['row_count']} rows. It separates migration, direct reuse, local external alignment, and inherited record alignment. Review-state distribution is `{json.dumps(result['sssom']['review_status_counts'], sort_keys=True)}`.",
            "",
            "Record-layer mappings cover SOSA, SSN, QUDT, UCUM-coded representation, and OWL-Time. Confidence values express curation confidence; they do not represent external approval.",
            "",
            "## Release/provenance completeness",
            "",
            "| ID | Assertion | Complete |",
            "|---|---|---|",
        ]
    )
    for assertion in result["release_provenance"]["assertions"]:
        lines.append(
            f"| `{assertion['id']}` | {assertion['assertion']} | {'yes' if assertion['complete'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "These ratios measure coverage of declared contracts and auditable mappings. Domain adequacy, external standards-body endorsement, deployment compatibility, human approval, CI publication, and Semantic Treehouse execution require their own evidence tracks.",
            "",
            "All mapping rows remain pending domain review. The machine checks establish structural validity, traceability, selected predicate semantics, and complete coverage of the required migration inventory.",
            "",
        ]
    )
    return "\n".join(lines)


def _verify_assessment_contract(path: Path, expected_text: str) -> dict[str, Any]:
    """Validate the tracked assessment without writing to the source tree."""

    if "\r" in expected_text or not expected_text.endswith("\n"):
        raise QualityFailure(
            "ASSESSMENT_EXPECTATION_INVALID",
            "The generated assessment must use UTF-8/LF with a trailing newline.",
            {"path": ASSESSMENT_RELPATH},
        )
    expected_bytes = expected_text.encode("utf-8")
    try:
        actual_bytes = path.read_bytes()
    except OSError as exc:
        raise QualityFailure(
            "ASSESSMENT_BYTE_CONTRACT",
            "The tracked model quality assessment cannot be read.",
            {
                "path": ASSESSMENT_RELPATH,
                "expected_sha256": _sha256_bytes(expected_bytes),
                "actual_sha256": None,
                "reason": exc.__class__.__name__,
            },
        ) from exc
    expected_sha256 = _sha256_bytes(expected_bytes)
    actual_sha256 = _sha256_bytes(actual_bytes)
    if actual_bytes != expected_bytes:
        raise QualityFailure(
            "ASSESSMENT_BYTE_CONTRACT",
            "The tracked model quality assessment differs from canonical generated bytes.",
            {
                "path": ASSESSMENT_RELPATH,
                "contract": "UTF-8 without BOM, LF line endings, exact trailing newline",
                "expected_sha256": expected_sha256,
                "actual_sha256": actual_sha256,
                "expected_size_bytes": len(expected_bytes),
                "actual_size_bytes": len(actual_bytes),
            },
        )
    return {
        "path": ASSESSMENT_RELPATH,
        "sha256": actual_sha256,
        "size_bytes": len(actual_bytes),
        "status": "PASS",
    }


def _environment(root: Path, result_path: Path) -> dict[str, Any]:
    packages: dict[str, str | None] = {}
    for package in ("pip", "rdflib", "jsonschema"):
        try:
            packages[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            packages[package] = None
    return {
        "schema": "dssc.phase06.quality.environment.v1",
        "component": "quality",
        "result_path": RESULT_RELPATH,
        "result_sha256": sha256_file(result_path),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_executable": "<PYTHON_EXECUTABLE>",
        "packages": packages,
        "command": "python C_Semantic_Treehouse/scripts/quality_metrics.py",
        "repository": "<REPO_ROOT>",
    }


def _write_failure(root: Path, failure: QualityFailure) -> dict[str, Any]:
    result = {
        "schema": "dssc.phase06.quality.results.v1",
        "suite": "quality",
        "release": "v0.4",
        "status": "FAIL",
        "program_status": "ERROR",
        "message": failure.message,
        "error": {"code": failure.code, "details": failure.details},
        "metric_count": 0,
        "metrics": [],
    }
    result_path = _repo_path(root, RESULT_RELPATH)
    atomic_write_json(result_path, result)
    atomic_write_text(
        _repo_path(root, REPORT_RELPATH),
        "\n".join(
            [
                "# Phase 06 Quality Validation Report",
                "",
                "Overall status: **FAIL**",
                "",
                "Program status: **ERROR**",
                "",
                f"Error code: `{failure.code}`",
                "",
                failure.message,
                "",
            ]
        ),
    )
    atomic_write_json(
        _repo_path(root, ENVIRONMENT_RELPATH), _environment(root, result_path)
    )
    return result


def run_component(context: dict[str, Any]) -> dict[str, Any]:
    """Run the controlled Phase 06 quality component."""

    root_value = context.get("repository_root")
    if not isinstance(root_value, Path):
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "quality checker requires repository_root",
            "details": {"error_code": "CONTEXT_ROOT"},
            "machine_details": {},
        }
    root = root_value.resolve()
    try:
        # Contract requirement: these five manifest validators are the first
        # data-dependent action on every run.  No quality source is read first.
        preflight = _manifest_preflight(root)

        first_result, first_controls = _calculate_quality(root, preflight)
        second_result, second_controls = _calculate_quality(root, preflight)
        first_hash = _json_sha256(first_result)
        second_hash = _json_sha256(second_result)
        controls_first_hash = _json_sha256(first_controls)
        controls_second_hash = _json_sha256(second_controls)
        if first_hash != second_hash or controls_first_hash != controls_second_hash:
            raise QualityFailure(
                "NONDETERMINISTIC_RERUN",
                "Two independent quality calculations produced different normalized bytes.",
                {
                    "first_sha256": first_hash,
                    "second_sha256": second_hash,
                    "controls_first_sha256": controls_first_hash,
                    "controls_second_sha256": controls_second_hash,
                },
            )
        result = first_result
        result["determinism"] = {
            "status": "PASS",
            "rerun_count": 2,
            "first_calculation_sha256": first_hash,
            "second_calculation_sha256": second_hash,
            "identical": True,
        }
        result["checks"].append(
            {"id": "deterministic-rerun", "status": "PASS"}
        )

        freshness_issues = _freshness_issues(root, result)
        if freshness_issues:
            raise QualityFailure(
                "SOURCE_FRESHNESS_FAILED",
                "A source changed between calculation and evidence serialization.",
                {"issues": freshness_issues},
            )

        assessment_path = _repo_path(root, ASSESSMENT_RELPATH)
        assessment_contract = _verify_assessment_contract(
            assessment_path, _assessment_markdown(result)
        )
        result["checks"].append(
            {"id": "tracked-assessment-byte-contract", "status": "PASS"}
        )

        negative_path = _repo_path(root, NEGATIVE_CONTROL_RELPATH)
        atomic_write_json(negative_path, first_controls)
        result_path = _repo_path(root, RESULT_RELPATH)
        report_path = _repo_path(root, REPORT_RELPATH)
        atomic_write_json(result_path, result)
        atomic_write_text(report_path, _report_markdown(result))

        determinism = {
            "schema": "dssc.phase06.quality.determinism.v1",
            "status": "PASS",
            "rerun_count": 2,
            "first_calculation_sha256": first_hash,
            "second_calculation_sha256": second_hash,
            "controls_first_sha256": controls_first_hash,
            "controls_second_sha256": controls_second_hash,
            "identical": True,
            "results_path": RESULT_RELPATH,
            "results_sha256": sha256_file(result_path),
            "report_path": REPORT_RELPATH,
            "report_sha256": sha256_file(report_path),
            "assessment_path": ASSESSMENT_RELPATH,
            "assessment_sha256": assessment_contract["sha256"],
        }
        atomic_write_json(_repo_path(root, DETERMINISM_RELPATH), determinism)
        atomic_write_json(
            _repo_path(root, ENVIRONMENT_RELPATH), _environment(root, result_path)
        )
        return {
            "status": "PASS",
            "program_status": "SUCCESS",
            "message": "Phase 06 quality metrics, SSSOM, and breaking-change checks passed.",
            "details": {
                "result_path": RESULT_RELPATH,
                "result_sha256": sha256_file(result_path),
                "report_path": REPORT_RELPATH,
                "assessment_path": ASSESSMENT_RELPATH,
                "assessment_sha256": assessment_contract["sha256"],
                "negative_controls_path": NEGATIVE_CONTROL_RELPATH,
                "determinism_path": DETERMINISM_RELPATH,
                "metric_count": result["metric_count"],
                "sssom_rows": result["sssom"]["row_count"],
                "source_freshness": "PASS",
                "wire_profile_classification": result["breaking_change"]["conclusion"]["classification"],
            },
            "machine_details": {"environment_path": ENVIRONMENT_RELPATH},
        }
    except QualityFailure as failure:
        _write_failure(root, failure)
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": failure.message,
            "details": {"error_code": failure.code, **failure.details},
            "machine_details": {"environment_path": ENVIRONMENT_RELPATH},
        }
    except Exception as exc:  # noqa: BLE001 - unexpected faults fail closed
        failure = QualityFailure(
            "UNEXPECTED_QUALITY_ERROR",
            f"{exc.__class__.__name__}: quality calculation failed closed.",
        )
        _write_failure(root, failure)
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": failure.message,
            "details": {"error_code": failure.code},
            "machine_details": {"environment_path": ENVIRONMENT_RELPATH},
        }


def main() -> int:
    result = run_component({"repository_root": REPOSITORY_ROOT})
    print(f"Quality result: {RESULT_RELPATH}")
    print(f"Quality report: {REPORT_RELPATH}")
    print(f"Quality assessment: {ASSESSMENT_RELPATH}")
    print(f"Status: {result.get('status')} / {result.get('program_status')}")
    if result.get("status") != "PASS":
        print(f"Error: {result.get('details', {}).get('error_code', 'UNKNOWN')}")
    return 0 if result.get("program_status") == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
