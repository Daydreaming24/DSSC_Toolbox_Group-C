"""Fail-closed loading and semantic preflight for the v0.1-v0.3 baseline.

The JSON Schema describes individual records.  This module adds the fixed
Phase 02 suite contract, cross-record checks, repository path confinement,
and byte-level artifact verification.  It deliberately does not execute any
validator or write evidence.
"""

from __future__ import annotations

import json
import re
import stat
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping

from dssc_validation.hashing import sha256_file
from dssc_validation.paths import repository_root


MANIFEST_RELATIVE_PATH = Path(
    "C_Semantic_Treehouse/manifests/baseline-test-cases.json"
)
SCHEMA_RELATIVE_PATH = Path(
    "C_Semantic_Treehouse/manifests/schemas/baseline-test-cases.schema.json"
)
FIXED_SCHEMA_REFERENCE = "schemas/baseline-test-cases.schema.json"
FIXED_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
FIXED_MANIFEST_SCHEMA_VERSION = "1.0.0"

EXPECTED_RELEASE_IDS = ("v0.1", "v0.2", "v0.3")
EXPECTED_VALIDATORS = (
    ("rdflib-turtle", "rdf"),
    ("pyld-jsonld", "jsonld"),
    ("pyshacl", "shacl"),
    ("jsonschema-draft7", "jsonschema"),
    ("openapi-spec-validator", "openapi"),
    ("rdflib-sparql", "sparql"),
)

# id, release, validator, category, expected business status
EXPECTED_CASE_SPECS = (
    ("rdf-v0-1-ontology", "v0.1", "rdflib-turtle", "rdf", "PASS"),
    ("rdf-v0-1-metadata-shapes", "v0.1", "rdflib-turtle", "rdf", "PASS"),
    ("rdf-v0-2-ontology", "v0.2", "rdflib-turtle", "rdf", "PASS"),
    ("rdf-v0-2-metadata-shapes", "v0.2", "rdflib-turtle", "rdf", "PASS"),
    ("rdf-v0-3-ontology", "v0.3", "rdflib-turtle", "rdf", "PASS"),
    ("rdf-v0-3-metadata-shapes", "v0.3", "rdflib-turtle", "rdf", "PASS"),
    ("rdf-v0-3-record-shapes", "v0.3", "rdflib-turtle", "rdf", "PASS"),
    ("jsonld-v0-1-metadata-context", "v0.1", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-1-metadata-valid", "v0.1", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-2-metadata-context", "v0.2", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-2-metadata-valid", "v0.2", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-2-metadata-invalid", "v0.2", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-3-metadata-context", "v0.3", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-3-metadata-valid", "v0.3", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-3-record-context", "v0.3", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-3-record-valid", "v0.3", "pyld-jsonld", "jsonld", "PASS"),
    ("jsonld-v0-3-record-invalid", "v0.3", "pyld-jsonld", "jsonld", "PASS"),
    ("shacl-v0-1-metadata-valid", "v0.1", "pyshacl", "shacl", "PASS"),
    ("shacl-v0-2-metadata-valid", "v0.2", "pyshacl", "shacl", "PASS"),
    ("shacl-v0-2-metadata-invalid", "v0.2", "pyshacl", "shacl", "FAIL"),
    ("shacl-v0-3-metadata-valid", "v0.3", "pyshacl", "shacl", "PASS"),
    ("shacl-v0-3-record-valid", "v0.3", "pyshacl", "shacl", "PASS"),
    (
        "jsonschema-v0-3-record-valid",
        "v0.3",
        "jsonschema-draft7",
        "jsonschema",
        "PASS",
    ),
    (
        "jsonschema-v0-3-record-invalid",
        "v0.3",
        "jsonschema-draft7",
        "jsonschema",
        "FAIL",
    ),
    (
        "openapi-v0-3-fragment-valid",
        "v0.3",
        "openapi-spec-validator",
        "openapi",
        "PASS",
    ),
    ("sparql-cq01-dataset-id", "v0.3", "rdflib-sparql", "sparql", "PASS"),
    ("sparql-cq02-provider", "v0.3", "rdflib-sparql", "sparql", "PASS"),
    ("sparql-cq03-endpoint", "v0.3", "rdflib-sparql", "sparql", "PASS"),
    (
        "sparql-cq04-format-frequency",
        "v0.3",
        "rdflib-sparql",
        "sparql",
        "PASS",
    ),
    ("sparql-cq05-unit", "v0.3", "rdflib-sparql", "sparql", "PASS"),
    ("sparql-cq06-coverage", "v0.3", "rdflib-sparql", "sparql", "PASS"),
    ("sparql-cq07-conforms-to", "v0.3", "rdflib-sparql", "sparql", "PASS"),
    ("sparql-cq08-record-fields", "v0.3", "rdflib-sparql", "sparql", "PASS"),
)
EXPECTED_CASE_IDS = tuple(spec[0] for spec in EXPECTED_CASE_SPECS)
_EXPECTED_CASE_BY_ID = MappingProxyType(
    {
        case_id: {
            "release": release,
            "validator": validator,
            "category": category,
            "expected_business_status": business_status,
        }
        for case_id, release, validator, category, business_status in EXPECTED_CASE_SPECS
    }
)

EXPECTED_CATEGORY_COUNTS = MappingProxyType(
    {"rdf": 7, "jsonld": 10, "shacl": 5, "jsonschema": 2, "openapi": 1, "sparql": 8}
)
EXPECTED_CASE_RELEASE_COUNTS = MappingProxyType({"v0.1": 5, "v0.2": 7, "v0.3": 21})
EXPECTED_VALIDATOR_COUNTS = MappingProxyType(
    {
        "rdflib-turtle": 7,
        "pyld-jsonld": 10,
        "pyshacl": 5,
        "jsonschema-draft7": 2,
        "openapi-spec-validator": 1,
        "rdflib-sparql": 8,
    }
)

# id, release, kind.  Paths and hashes remain manifest data, then receive
# strict repository confinement and byte verification below.
EXPECTED_ARTIFACT_SPECS = (
    ("baseline-expected-results", "baseline", "reference"),
    ("sparql-competency-questions", "baseline", "reference"),
    ("v01-ontology", "v0.1", "ontology"),
    ("v01-metadata-context", "v0.1", "context"),
    ("v01-metadata-shapes", "v0.1", "shapes"),
    ("v01-metadata-valid", "v0.1", "data"),
    ("v02-ontology", "v0.2", "ontology"),
    ("v02-metadata-context", "v0.2", "context"),
    ("v02-metadata-invalid", "v0.2", "data"),
    ("v02-metadata-shapes", "v0.2", "shapes"),
    ("v02-metadata-valid", "v0.2", "data"),
    ("v03-ontology", "v0.3", "ontology"),
    ("v03-metadata-context", "v0.3", "context"),
    ("v03-metadata-shapes", "v0.3", "shapes"),
    ("v03-metadata-valid", "v0.3", "data"),
    ("v03-record-schema", "v0.3", "json-schema"),
    ("v03-record-context", "v0.3", "context"),
    ("v03-record-invalid", "v0.3", "data"),
    ("v03-record-shapes", "v0.3", "shapes"),
    ("v03-record-valid", "v0.3", "data"),
    ("v03-openapi", "v0.3", "openapi"),
    ("cq01-query", "v0.3", "sparql-query"),
    ("cq01-expected", "v0.3", "expected-tsv"),
    ("cq02-query", "v0.3", "sparql-query"),
    ("cq02-expected", "v0.3", "expected-tsv"),
    ("cq03-query", "v0.3", "sparql-query"),
    ("cq03-expected", "v0.3", "expected-tsv"),
    ("cq04-query", "v0.3", "sparql-query"),
    ("cq04-expected", "v0.3", "expected-tsv"),
    ("cq05-query", "v0.3", "sparql-query"),
    ("cq05-expected", "v0.3", "expected-tsv"),
    ("cq06-query", "v0.3", "sparql-query"),
    ("cq06-expected", "v0.3", "expected-tsv"),
    ("cq07-query", "v0.3", "sparql-query"),
    ("cq07-expected", "v0.3", "expected-tsv"),
    ("cq08-query", "v0.3", "sparql-query"),
    ("cq08-expected", "v0.3", "expected-tsv"),
)
EXPECTED_ARTIFACT_IDS = tuple(spec[0] for spec in EXPECTED_ARTIFACT_SPECS)
_EXPECTED_ARTIFACT_BY_ID = MappingProxyType(
    {
        artifact_id: {"release": release, "kind": kind}
        for artifact_id, release, kind in EXPECTED_ARTIFACT_SPECS
    }
)
EXPECTED_REFERENCE_ARTIFACT_IDS = (
    "baseline-expected-results",
    "sparql-competency-questions",
)
EXPECTED_ARTIFACT_KIND_COUNTS = MappingProxyType(
    {
        "ontology": 3,
        "shapes": 4,
        "context": 4,
        "data": 6,
        "json-schema": 1,
        "openapi": 1,
        "sparql-query": 8,
        "expected-tsv": 8,
        "reference": 2,
    }
)
EXPECTED_ARTIFACT_RELEASE_COUNTS = MappingProxyType(
    {"baseline": 2, "v0.1": 4, "v0.2": 5, "v0.3": 26}
)

_EXPECTED_CASE_ARTIFACT_REFS: dict[str, dict[str, Any]] = {
    "rdf-v0-1-ontology": {"input": "v01-ontology"},
    "rdf-v0-1-metadata-shapes": {"input": "v01-metadata-shapes"},
    "rdf-v0-2-ontology": {"input": "v02-ontology"},
    "rdf-v0-2-metadata-shapes": {"input": "v02-metadata-shapes"},
    "rdf-v0-3-ontology": {"input": "v03-ontology"},
    "rdf-v0-3-metadata-shapes": {"input": "v03-metadata-shapes"},
    "rdf-v0-3-record-shapes": {"input": "v03-record-shapes"},
    "jsonld-v0-1-metadata-context": {"input": "v01-metadata-context", "local_contexts": []},
    "jsonld-v0-1-metadata-valid": {
        "input": "v01-metadata-valid",
        "local_contexts": ["v01-metadata-context"],
    },
    "jsonld-v0-2-metadata-context": {"input": "v02-metadata-context", "local_contexts": []},
    "jsonld-v0-2-metadata-valid": {
        "input": "v02-metadata-valid",
        "local_contexts": ["v02-metadata-context"],
    },
    "jsonld-v0-2-metadata-invalid": {
        "input": "v02-metadata-invalid",
        "local_contexts": ["v02-metadata-context"],
    },
    "jsonld-v0-3-metadata-context": {"input": "v03-metadata-context", "local_contexts": []},
    "jsonld-v0-3-metadata-valid": {
        "input": "v03-metadata-valid",
        "local_contexts": ["v03-metadata-context"],
    },
    "jsonld-v0-3-record-context": {"input": "v03-record-context", "local_contexts": []},
    "jsonld-v0-3-record-valid": {
        "input": "v03-record-valid",
        "local_contexts": ["v03-record-context"],
    },
    "jsonld-v0-3-record-invalid": {
        "input": "v03-record-invalid",
        "local_contexts": ["v03-record-context"],
    },
    "shacl-v0-1-metadata-valid": {
        "data": "v01-metadata-valid",
        "shapes": "v01-metadata-shapes",
        "local_contexts": ["v01-metadata-context"],
    },
    "shacl-v0-2-metadata-valid": {
        "data": "v02-metadata-valid",
        "shapes": "v02-metadata-shapes",
        "local_contexts": ["v02-metadata-context"],
    },
    "shacl-v0-2-metadata-invalid": {
        "data": "v02-metadata-invalid",
        "shapes": "v02-metadata-shapes",
        "local_contexts": ["v02-metadata-context"],
    },
    "shacl-v0-3-metadata-valid": {
        "data": "v03-metadata-valid",
        "shapes": "v03-metadata-shapes",
        "local_contexts": ["v03-metadata-context"],
    },
    "shacl-v0-3-record-valid": {
        "data": "v03-record-valid",
        "shapes": "v03-record-shapes",
        "local_contexts": ["v03-record-context"],
    },
    "jsonschema-v0-3-record-valid": {
        "instance": "v03-record-valid",
        "schema": "v03-record-schema",
    },
    "jsonschema-v0-3-record-invalid": {
        "instance": "v03-record-invalid",
        "schema": "v03-record-schema",
    },
    "openapi-v0-3-fragment-valid": {"document": "v03-openapi"},
}
for _cq_number, _cq_name in (
    ("01", "dataset-id"),
    ("02", "provider"),
    ("03", "endpoint"),
    ("04", "format-frequency"),
    ("05", "unit"),
    ("06", "coverage"),
    ("07", "conforms-to"),
    ("08", "record-fields"),
):
    _EXPECTED_CASE_ARTIFACT_REFS[f"sparql-cq{_cq_number}-{_cq_name}"] = {
        "graph_inputs": ["v03-ontology", "v03-metadata-valid", "v03-record-valid"],
        "local_contexts": ["v03-metadata-context", "v03-record-context"],
        "query": f"cq{_cq_number}-query",
        "expected": f"cq{_cq_number}-expected",
    }
_EXPECTED_CASE_ARTIFACT_REFS = dict(_EXPECTED_CASE_ARTIFACT_REFS)

_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True, order=True)
class BaselineManifestIssue:
    """One stable, machine-readable preflight failure."""

    location: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "location": self.location, "message": self.message}


class BaselineManifestError(RuntimeError):
    """Raised whenever baseline manifest preflight cannot be trusted."""

    def __init__(self, issues: list[BaselineManifestIssue] | tuple[BaselineManifestIssue, ...]):
        ordered = tuple(sorted(issues))
        if not ordered:
            ordered = (
                BaselineManifestIssue(
                    "<root>", "unknown_preflight_error", "baseline preflight failed",
                ),
            )
        self.issues = ordered
        summary = "; ".join(
            f"{issue.code}@{issue.location}: {issue.message}" for issue in ordered
        )
        super().__init__(f"baseline manifest preflight failed: {summary}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": "BASELINE_MANIFEST_PREFLIGHT_FAILED",
            "issues": [issue.as_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class BaselineArtifact:
    id: str
    release: str
    kind: str
    path: str
    absolute_path: Path
    sha256: str
    size_bytes: int

    def deterministic_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "release": self.release,
            "kind": self.kind,
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class BaselineManifestPreflight:
    root: Path
    manifest_path: Path
    schema_path: Path
    manifest_schema_version: str
    manifest_sha256: str
    schema_sha256: str
    manifest: dict[str, Any]
    artifacts: tuple[BaselineArtifact, ...]
    cases: tuple[dict[str, Any], ...]
    artifact_by_id: Mapping[str, BaselineArtifact]
    case_by_id: Mapping[str, dict[str, Any]]
    reference_artifact_ids: tuple[str, ...]
    required_case_ids: tuple[str, ...]
    category_counts: Mapping[str, int]
    release_counts: Mapping[str, int]
    validator_counts: Mapping[str, int]
    artifact_kind_counts: Mapping[str, int]
    artifact_release_counts: Mapping[str, int]

    def deterministic_record(self) -> dict[str, Any]:
        """Return a JSON-safe preflight record without machine-specific paths."""
        return {
            "manifest_schema_version": self.manifest_schema_version,
            "manifest_sha256": self.manifest_sha256,
            "schema_sha256": self.schema_sha256,
            "case_ids": list(self.required_case_ids),
            "case_count": len(self.cases),
            "category_counts": dict(self.category_counts),
            "release_counts": dict(self.release_counts),
            "validator_counts": dict(self.validator_counts),
            "artifact_count": len(self.artifacts),
            "artifact_kind_counts": dict(self.artifact_kind_counts),
            "artifact_release_counts": dict(self.artifact_release_counts),
            "artifacts": [artifact.deterministic_record() for artifact in self.artifacts],
        }

    def runner_input(self) -> dict[str, Any]:
        """Return the wrapper shape accepted by ``run_baseline_cases``."""
        return {
            "manifest": self.manifest,
            "preflight": self.deterministic_record(),
        }


def baseline_manifest_path(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / MANIFEST_RELATIVE_PATH


def baseline_manifest_schema_path(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / SCHEMA_RELATIVE_PATH


def _json_pointer(parts: Any) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(encoded) if encoded else "<root>"


def _read_json_document(path: Path, role: str) -> tuple[Any, str]:
    if not path.exists():
        raise BaselineManifestError(
            [BaselineManifestIssue(str(path), f"missing_{role}", f"{role} file is missing")]
        )
    try:
        mode = path.stat(follow_symlinks=False).st_mode
    except OSError as exc:
        raise BaselineManifestError(
            [
                BaselineManifestIssue(
                    str(path),
                    f"unreadable_{role}",
                    f"cannot stat {role}: {exc.__class__.__name__}: {exc}",
                )
            ]
        ) from exc
    if not stat.S_ISREG(mode):
        raise BaselineManifestError(
            [
                BaselineManifestIssue(
                    str(path), f"non_regular_{role}", f"{role} must be a regular file"
                )
            ]
        )
    try:
        digest = sha256_file(path)
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BaselineManifestError(
            [
                BaselineManifestIssue(
                    str(path),
                    f"{role}_parse_error",
                    f"cannot parse {role}: {exc.__class__.__name__}: {exc}",
                )
            ]
        ) from exc
    return value, digest


def _schema_issues(instance: Any, schema: Any) -> list[BaselineManifestIssue]:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from jsonschema.exceptions import SchemaError
    except ImportError as exc:
        return [
            BaselineManifestIssue(
                "<schema>",
                "schema_engine_missing",
                f"jsonschema Draft 2020-12 engine unavailable: {exc}",
            )
        ]

    if not isinstance(schema, dict):
        return [
            BaselineManifestIssue(
                "<schema>", "schema_type", "baseline manifest schema root must be an object"
            )
        ]
    issues: list[BaselineManifestIssue] = []
    if schema.get("$schema") != FIXED_SCHEMA_DIALECT:
        issues.append(
            BaselineManifestIssue(
                "/$schema",
                "schema_dialect",
                f"schema must declare {FIXED_SCHEMA_DIALECT!r}",
            )
        )
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        issues.append(
            BaselineManifestIssue(
                _json_pointer(exc.absolute_path),
                "invalid_schema",
                exc.message,
            )
        )
        return issues
    if issues:
        return issues

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: (
            tuple(str(item) for item in error.absolute_path),
            tuple(str(item) for item in error.absolute_schema_path),
            str(error.validator),
            error.message,
        ),
    )
    for error in errors:
        issues.append(
            BaselineManifestIssue(
                _json_pointer(error.absolute_path),
                "schema_violation",
                error.message,
            )
        )
    return issues


def _duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _counter_mapping(values: list[str], expected_order: Mapping[str, int]) -> Mapping[str, int]:
    counts = Counter(values)
    return MappingProxyType({key: counts.get(key, 0) for key in expected_order})


def _compare_counter(
    issues: list[BaselineManifestIssue],
    location: str,
    code: str,
    actual_values: list[str],
    expected: Mapping[str, int],
) -> None:
    actual = Counter(actual_values)
    if dict(actual) != dict(expected):
        issues.append(
            BaselineManifestIssue(
                location,
                code,
                f"expected {dict(expected)!r}; actual {dict(sorted(actual.items()))!r}",
            )
        )


def _validate_repo_path(value: str, location: str) -> list[BaselineManifestIssue]:
    issues: list[BaselineManifestIssue] = []
    if not value:
        return [BaselineManifestIssue(location, "empty_path", "artifact path is empty")]
    if "\\" in value:
        issues.append(
            BaselineManifestIssue(
                location,
                "path_backslash",
                "artifact path must use POSIX separators",
            )
        )
    if value.startswith("/") or _WINDOWS_DRIVE.match(value):
        issues.append(
            BaselineManifestIssue(
                location,
                "absolute_path",
                "artifact path must be repository-relative",
            )
        )
    if "\x00" in value:
        issues.append(BaselineManifestIssue(location, "path_nul", "artifact path contains NUL"))
    if "//" in value or value.endswith("/"):
        issues.append(
            BaselineManifestIssue(
                location,
                "noncanonical_path",
                "artifact path is not canonical POSIX",
            )
        )
    parts = PurePosixPath(value).parts
    if ".." in parts:
        issues.append(
            BaselineManifestIssue(location, "path_escape", "artifact path contains '..'")
        )
    if "." in parts:
        issues.append(
            BaselineManifestIssue(location, "noncanonical_path", "artifact path contains '.'")
        )
    return issues


def _flatten_artifact_refs(refs: dict[str, Any]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for key in sorted(refs):
        value = refs[key]
        if isinstance(value, str):
            result.append((key, value))
        elif isinstance(value, list):
            result.extend((f"{key}/{index}", item) for index, item in enumerate(value))
    return result


def _count_oracle_contains(oracle: dict[str, int], count: int) -> bool:
    if "exact" in oracle:
        return oracle["exact"] == count
    return oracle["minimum"] <= count <= oracle["maximum"]


def _oracle_semantic_issues(case: dict[str, Any], index: int) -> list[BaselineManifestIssue]:
    issues: list[BaselineManifestIssue] = []
    category = case["category"]
    business_status = case["expected_business_status"]
    oracle = case["oracle"]
    base = f"/cases/{index}/oracle"

    if category == "shacl" and business_status == "FAIL":
        expected_results = oracle["expected_results"]
        total = sum(result["count"] for result in expected_results)
        if not _count_oracle_contains(oracle["expected_result_count"], total):
            issues.append(
                BaselineManifestIssue(
                    f"{base}/expected_result_count",
                    "shacl_result_count_mismatch",
                    f"result count oracle does not contain declared result total {total}",
                )
            )
        keys = [
            json.dumps(
                {key: value for key, value in result.items() if key != "count"},
                sort_keys=True,
                separators=(",", ":"),
            )
            for result in expected_results
        ]
        if _duplicates(keys):
            issues.append(
                BaselineManifestIssue(
                    f"{base}/expected_results",
                    "duplicate_shacl_result_oracle",
                    "SHACL expected result identities must be unique",
                )
            )

    if category == "jsonschema" and business_status == "FAIL":
        expected_errors = oracle["expected_errors"]
        total = sum(error["count"] for error in expected_errors)
        if not _count_oracle_contains(oracle["expected_error_count"], total):
            issues.append(
                BaselineManifestIssue(
                    f"{base}/expected_error_count",
                    "jsonschema_error_count_mismatch",
                    f"error count oracle does not contain declared error total {total}",
                )
            )
        keys = [
            json.dumps(
                {key: value for key, value in error.items() if key != "count"},
                sort_keys=True,
                separators=(",", ":"),
            )
            for error in expected_errors
        ]
        if _duplicates(keys):
            issues.append(
                BaselineManifestIssue(
                    f"{base}/expected_errors",
                    "duplicate_jsonschema_error_oracle",
                    "JSON Schema expected error identities must be unique",
                )
            )

    if category == "sparql":
        variables = oracle["expected_variables"]
        if _duplicates(variables):
            issues.append(
                BaselineManifestIssue(
                    f"{base}/expected_variables",
                    "duplicate_sparql_variable",
                    "SPARQL expected variables must be unique",
                )
            )
    return issues


def _semantic_issues(
    manifest: dict[str, Any], root: Path
) -> tuple[list[BaselineManifestIssue], tuple[BaselineArtifact, ...]]:
    issues: list[BaselineManifestIssue] = []

    if manifest.get("$schema") != FIXED_SCHEMA_REFERENCE:
        issues.append(
            BaselineManifestIssue(
                "/$schema",
                "schema_reference",
                f"manifest $schema must equal {FIXED_SCHEMA_REFERENCE!r}",
            )
        )
    if manifest.get("manifest_schema_version") != FIXED_MANIFEST_SCHEMA_VERSION:
        issues.append(
            BaselineManifestIssue(
                "/manifest_schema_version",
                "manifest_schema_version",
                f"supported manifest schema version is {FIXED_MANIFEST_SCHEMA_VERSION!r}",
            )
        )
    if manifest.get("suite") != "baseline":
        issues.append(BaselineManifestIssue("/suite", "suite", "suite must be 'baseline'"))

    releases = manifest["releases"]
    release_ids = [release["id"] for release in releases]
    duplicate_releases = _duplicates(release_ids)
    if duplicate_releases:
        issues.append(
            BaselineManifestIssue(
                "/releases",
                "duplicate_release_id",
                f"duplicate release IDs: {duplicate_releases!r}",
            )
        )
    if tuple(release_ids) != EXPECTED_RELEASE_IDS:
        issues.append(
            BaselineManifestIssue(
                "/releases",
                "release_set",
                f"release IDs/order must equal {list(EXPECTED_RELEASE_IDS)!r}",
            )
        )

    validators = manifest["validators"]
    validator_ids = [validator["id"] for validator in validators]
    duplicate_validators = _duplicates(validator_ids)
    if duplicate_validators:
        issues.append(
            BaselineManifestIssue(
                "/validators",
                "duplicate_validator_id",
                f"duplicate validator IDs: {duplicate_validators!r}",
            )
        )
    declared_validators = tuple((item["id"], item["category"]) for item in validators)
    if declared_validators != EXPECTED_VALIDATORS:
        issues.append(
            BaselineManifestIssue(
                "/validators",
                "validator_set",
                f"validator ID/category/order must equal {list(EXPECTED_VALIDATORS)!r}",
            )
        )

    artifacts = manifest["artifacts"]
    artifact_ids = [artifact["id"] for artifact in artifacts]
    duplicate_artifacts = _duplicates(artifact_ids)
    if duplicate_artifacts:
        issues.append(
            BaselineManifestIssue(
                "/artifacts",
                "duplicate_artifact_id",
                f"duplicate artifact IDs: {duplicate_artifacts!r}",
            )
        )
    if tuple(artifact_ids) != EXPECTED_ARTIFACT_IDS:
        missing = sorted(set(EXPECTED_ARTIFACT_IDS) - set(artifact_ids))
        extra = sorted(set(artifact_ids) - set(EXPECTED_ARTIFACT_IDS))
        issues.append(
            BaselineManifestIssue(
                "/artifacts",
                "artifact_set",
                f"artifact IDs/order mismatch; missing={missing!r}; extra={extra!r}",
            )
        )
    _compare_counter(
        issues,
        "/artifacts",
        "artifact_kind_counts",
        [artifact["kind"] for artifact in artifacts],
        EXPECTED_ARTIFACT_KIND_COUNTS,
    )
    _compare_counter(
        issues,
        "/artifacts",
        "artifact_release_counts",
        [artifact["release"] for artifact in artifacts],
        EXPECTED_ARTIFACT_RELEASE_COUNTS,
    )

    artifact_map: dict[str, dict[str, Any]] = {}
    path_hashes: dict[str, str] = {}
    for index, artifact in enumerate(artifacts):
        artifact_id = artifact["id"]
        artifact_map.setdefault(artifact_id, artifact)
        expected_artifact = _EXPECTED_ARTIFACT_BY_ID.get(artifact_id)
        if expected_artifact is not None:
            for field in ("release", "kind"):
                if artifact[field] != expected_artifact[field]:
                    issues.append(
                        BaselineManifestIssue(
                            f"/artifacts/{index}/{field}",
                            "artifact_contract",
                            f"artifact {artifact_id!r} {field} must be "
                            f"{expected_artifact[field]!r}",
                        )
                    )
        path = artifact["path"]
        issues.extend(_validate_repo_path(path, f"/artifacts/{index}/path"))
        previous_hash = path_hashes.get(path)
        if previous_hash is not None and previous_hash != artifact["sha256"]:
            issues.append(
                BaselineManifestIssue(
                    f"/artifacts/{index}/sha256",
                    "same_path_hash_conflict",
                    f"path {path!r} is bound to conflicting SHA-256 values",
                )
            )
        path_hashes.setdefault(path, artifact["sha256"])

    reference_ids = manifest["reference_artifact_ids"]
    if tuple(reference_ids) != EXPECTED_REFERENCE_ARTIFACT_IDS:
        issues.append(
            BaselineManifestIssue(
                "/reference_artifact_ids",
                "reference_artifact_set",
                f"reference IDs/order must equal {list(EXPECTED_REFERENCE_ARTIFACT_IDS)!r}",
            )
        )
    for index, artifact_id in enumerate(reference_ids):
        artifact = artifact_map.get(artifact_id)
        if artifact is None:
            issues.append(
                BaselineManifestIssue(
                    f"/reference_artifact_ids/{index}",
                    "dangling_reference_artifact",
                    f"unknown artifact ID {artifact_id!r}",
                )
            )
        elif artifact["kind"] != "reference" or artifact["release"] != "baseline":
            issues.append(
                BaselineManifestIssue(
                    f"/reference_artifact_ids/{index}",
                    "reference_artifact_contract",
                    f"artifact {artifact_id!r} must have release='baseline' and kind='reference'",
                )
            )

    required_case_ids = manifest["required_case_ids"]
    if tuple(required_case_ids) != EXPECTED_CASE_IDS:
        missing = sorted(set(EXPECTED_CASE_IDS) - set(required_case_ids))
        extra = sorted(set(required_case_ids) - set(EXPECTED_CASE_IDS))
        issues.append(
            BaselineManifestIssue(
                "/required_case_ids",
                "required_case_set",
                f"required case IDs/order mismatch; missing={missing!r}; extra={extra!r}",
            )
        )

    cases = manifest["cases"]
    case_ids = [case["id"] for case in cases]
    duplicate_cases = _duplicates(case_ids)
    if duplicate_cases:
        issues.append(
            BaselineManifestIssue(
                "/cases", "duplicate_case_id", f"duplicate case IDs: {duplicate_cases!r}"
            )
        )
    if tuple(case_ids) != EXPECTED_CASE_IDS:
        missing = sorted(set(EXPECTED_CASE_IDS) - set(case_ids))
        extra = sorted(set(case_ids) - set(EXPECTED_CASE_IDS))
        issues.append(
            BaselineManifestIssue(
                "/cases",
                "case_set",
                f"case IDs/order mismatch; missing={missing!r}; extra={extra!r}",
            )
        )
    _compare_counter(
        issues,
        "/cases",
        "category_counts",
        [case["category"] for case in cases],
        EXPECTED_CATEGORY_COUNTS,
    )
    _compare_counter(
        issues,
        "/cases",
        "case_release_counts",
        [case["release"] for case in cases],
        EXPECTED_CASE_RELEASE_COUNTS,
    )
    _compare_counter(
        issues,
        "/cases",
        "validator_counts",
        [case["validator"] for case in cases],
        EXPECTED_VALIDATOR_COUNTS,
    )

    all_case_refs: set[str] = set()
    for index, case in enumerate(cases):
        case_id = case["id"]
        expected_case = _EXPECTED_CASE_BY_ID.get(case_id)
        if expected_case is not None:
            for field, expected_value in expected_case.items():
                if case[field] != expected_value:
                    issues.append(
                        BaselineManifestIssue(
                            f"/cases/{index}/{field}",
                            "case_contract",
                            f"case {case_id!r} {field} must be {expected_value!r}",
                        )
                    )
        if case["enabled"] is not True:
            issues.append(
                BaselineManifestIssue(
                    f"/cases/{index}/enabled",
                    "disabled_case",
                    f"required case {case_id!r} is disabled",
                )
            )
        if case["required"] is not True:
            issues.append(
                BaselineManifestIssue(
                    f"/cases/{index}/required",
                    "non_required_case",
                    f"fixed baseline case {case_id!r} must be required",
                )
            )
        if case["expected_program_status"] != "SUCCESS":
            issues.append(
                BaselineManifestIssue(
                    f"/cases/{index}/expected_program_status",
                    "program_status",
                    f"case {case_id!r} must expect program SUCCESS",
                )
            )

        expected_refs = _EXPECTED_CASE_ARTIFACT_REFS.get(case_id)
        if expected_refs is not None and case["artifact_refs"] != expected_refs:
            issues.append(
                BaselineManifestIssue(
                    f"/cases/{index}/artifact_refs",
                    "case_artifact_contract",
                    f"case {case_id!r} artifact references differ from the fixed baseline contract",
                )
            )
        for ref_location, artifact_id in _flatten_artifact_refs(case["artifact_refs"]):
            all_case_refs.add(artifact_id)
            artifact = artifact_map.get(artifact_id)
            if artifact is None:
                issues.append(
                    BaselineManifestIssue(
                        f"/cases/{index}/artifact_refs/{ref_location}",
                        "dangling_artifact_reference",
                        f"case {case_id!r} references unknown artifact {artifact_id!r}",
                    )
                )
            elif artifact["release"] != case["release"]:
                issues.append(
                    BaselineManifestIssue(
                        f"/cases/{index}/artifact_refs/{ref_location}",
                        "artifact_release_mismatch",
                        f"case release {case['release']!r} references artifact "
                        f"release {artifact['release']!r}",
                    )
                )
        issues.extend(_oracle_semantic_issues(case, index))

    unreferenced = sorted(
        set(artifact_ids) - all_case_refs - set(reference_ids)
    )
    if unreferenced:
        issues.append(
            BaselineManifestIssue(
                "/artifacts",
                "unreferenced_artifact",
                f"artifact IDs are not consumed by cases or references: {unreferenced!r}",
            )
        )

    verified_artifacts: list[BaselineArtifact] = []
    root_resolved = root.resolve()
    for index, artifact in enumerate(artifacts):
        relative = artifact["path"]
        if _validate_repo_path(relative, f"/artifacts/{index}/path"):
            continue
        lexical_path = root_resolved.joinpath(*PurePosixPath(relative).parts)
        try:
            resolved_path = lexical_path.resolve(strict=False)
            resolved_path.relative_to(root_resolved)
        except (OSError, ValueError) as exc:
            issues.append(
                BaselineManifestIssue(
                    f"/artifacts/{index}/path",
                    "path_escape",
                    f"artifact {artifact['id']!r} resolves outside the repository: {exc}",
                )
            )
            continue
        if not lexical_path.exists():
            issues.append(
                BaselineManifestIssue(
                    f"/artifacts/{index}/path",
                    "artifact_missing",
                    f"artifact {artifact['id']!r} does not exist",
                )
            )
            continue
        try:
            file_stat = lexical_path.stat(follow_symlinks=False)
        except OSError as exc:
            issues.append(
                BaselineManifestIssue(
                    f"/artifacts/{index}/path",
                    "artifact_unreadable",
                    f"cannot stat artifact {artifact['id']!r}: {exc.__class__.__name__}: {exc}",
                )
            )
            continue
        if not stat.S_ISREG(file_stat.st_mode):
            issues.append(
                BaselineManifestIssue(
                    f"/artifacts/{index}/path",
                    "artifact_not_regular_file",
                    f"artifact {artifact['id']!r} is not a regular file",
                )
            )
            continue
        try:
            actual_hash = sha256_file(lexical_path)
        except OSError as exc:
            issues.append(
                BaselineManifestIssue(
                    f"/artifacts/{index}/path",
                    "artifact_unreadable",
                    f"cannot hash artifact {artifact['id']!r}: {exc.__class__.__name__}: {exc}",
                )
            )
            continue
        if actual_hash != artifact["sha256"]:
            issues.append(
                BaselineManifestIssue(
                    f"/artifacts/{index}/sha256",
                    "artifact_hash_mismatch",
                    f"artifact {artifact['id']!r} expected {artifact['sha256']}; "
                    f"actual {actual_hash}",
                )
            )
            continue
        verified_artifacts.append(
            BaselineArtifact(
                id=artifact["id"],
                release=artifact["release"],
                kind=artifact["kind"],
                path=relative,
                absolute_path=lexical_path,
                sha256=actual_hash,
                size_bytes=file_stat.st_size,
            )
        )

    return issues, tuple(verified_artifacts)


def load_and_validate_baseline_manifest(
    root: Path | None = None,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
) -> BaselineManifestPreflight:
    """Load, schema-check, semantically check, and hash every baseline input.

    Schema validation completes successfully before semantic validation begins.
    Every failure raises :class:`BaselineManifestError`; callers never receive a
    partially trusted manifest.
    """

    base = (root if root is not None else repository_root()).resolve()
    if not base.is_dir():
        raise BaselineManifestError(
            [BaselineManifestIssue("<root>", "invalid_root", "repository root is not a directory")]
        )
    manifest_file = manifest_path if manifest_path is not None else baseline_manifest_path(base)
    schema_file = schema_path if schema_path is not None else baseline_manifest_schema_path(base)
    if not manifest_file.is_absolute():
        manifest_file = base / manifest_file
    if not schema_file.is_absolute():
        schema_file = base / schema_file

    schema, schema_sha256 = _read_json_document(schema_file, "schema")
    manifest, manifest_sha256 = _read_json_document(manifest_file, "manifest")

    schema_issues = _schema_issues(manifest, schema)
    if schema_issues:
        raise BaselineManifestError(schema_issues)
    if not isinstance(manifest, dict):
        raise BaselineManifestError(
            [BaselineManifestIssue("<root>", "manifest_type", "manifest root must be an object")]
        )

    semantic_issues, verified_artifacts = _semantic_issues(manifest, base)
    if semantic_issues:
        raise BaselineManifestError(semantic_issues)

    artifacts = manifest["artifacts"]
    cases = manifest["cases"]
    artifact_by_id = MappingProxyType(
        {artifact.id: artifact for artifact in verified_artifacts}
    )
    case_by_id = MappingProxyType({case["id"]: case for case in cases})
    return BaselineManifestPreflight(
        root=base,
        manifest_path=manifest_file,
        schema_path=schema_file,
        manifest_schema_version=manifest["manifest_schema_version"],
        manifest_sha256=manifest_sha256,
        schema_sha256=schema_sha256,
        manifest=manifest,
        artifacts=verified_artifacts,
        cases=tuple(cases),
        artifact_by_id=artifact_by_id,
        case_by_id=case_by_id,
        reference_artifact_ids=tuple(manifest["reference_artifact_ids"]),
        required_case_ids=tuple(manifest["required_case_ids"]),
        category_counts=_counter_mapping(
            [case["category"] for case in cases], EXPECTED_CATEGORY_COUNTS
        ),
        release_counts=_counter_mapping(
            [case["release"] for case in cases], EXPECTED_CASE_RELEASE_COUNTS
        ),
        validator_counts=_counter_mapping(
            [case["validator"] for case in cases], EXPECTED_VALIDATOR_COUNTS
        ),
        artifact_kind_counts=_counter_mapping(
            [artifact["kind"] for artifact in artifacts], EXPECTED_ARTIFACT_KIND_COUNTS
        ),
        artifact_release_counts=_counter_mapping(
            [artifact["release"] for artifact in artifacts],
            EXPECTED_ARTIFACT_RELEASE_COUNTS,
        ),
    )


def preflight_baseline_manifest(
    root: Path | None = None,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
) -> BaselineManifestPreflight:
    """Short alias for :func:`load_and_validate_baseline_manifest`."""

    return load_and_validate_baseline_manifest(root, manifest_path, schema_path)


__all__ = [
    "BaselineArtifact",
    "BaselineManifestError",
    "BaselineManifestIssue",
    "BaselineManifestPreflight",
    "EXPECTED_ARTIFACT_IDS",
    "EXPECTED_CASE_IDS",
    "baseline_manifest_path",
    "baseline_manifest_schema_path",
    "load_and_validate_baseline_manifest",
    "preflight_baseline_manifest",
]
