"""Fail-closed schema and cross-record validation for SPARQL test cases."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from types import MappingProxyType
from typing import Any, Iterable, Mapping


MANIFEST_RELPATH = "C_Semantic_Treehouse/tests/sparql/sparql-test-cases.json"
SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/tests/sparql/sparql-test-cases.schema.json"
)
AUTHORITY_RELPATHS = MappingProxyType(
    {
        "release_manifest": "C_Semantic_Treehouse/manifests/release-manifest.json",
        "baseline_test_cases": "C_Semantic_Treehouse/manifests/baseline-test-cases.json",
        "requirements": "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
        "v0_4_test_cases": "C_Semantic_Treehouse/manifests/v0.4-test-cases.json",
        "validation_suites": "C_Semantic_Treehouse/manifests/validation-suites.json",
    }
)
AUTHORITY_SCHEMA_RELPATHS = MappingProxyType(
    {
        "release_manifest": (
            "C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json"
        ),
        "baseline_test_cases": (
            "C_Semantic_Treehouse/manifests/schemas/"
            "baseline-test-cases.schema.json"
        ),
        "requirements": (
            "C_Semantic_Treehouse/manifests/schemas/"
            "v0.4-requirements.schema.json"
        ),
        "v0_4_test_cases": (
            "C_Semantic_Treehouse/manifests/schemas/"
            "v0.4-test-cases.schema.json"
        ),
        "validation_suites": (
            "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json"
        ),
    }
)
HISTORICAL_QUERY_IDS = (
    "sparql-cq01-dataset-id",
    "sparql-cq02-provider",
    "sparql-cq03-endpoint",
    "sparql-cq04-format-frequency",
    "sparql-cq05-unit",
    "sparql-cq06-coverage",
    "sparql-cq07-conforms-to",
    "sparql-cq08-record-fields",
)
V04_QUERY_IDS = (
    "sparql-v04-cq09-dataset-count",
    "sparql-v04-cq10-dataset-node-iri",
    "sparql-v04-cq11-core-metadata",
    "sparql-v04-cq12-distribution-values",
    "sparql-v04-cq13-temporal-values",
    "sparql-v04-cq14-temporal-order",
    "sparql-v04-cq15-optional-fields",
    "sparql-v04-cq16-profile-version-binding",
    "sparql-v04-cq17-named-shapes",
    "sparql-v04-cq18-constraint-components",
    "sparql-v04-cq19-closed-shape-inventory",
    "sparql-v04-cq20-inherited-record-contract",
)
REQUIRED_QUERY_IDS = HISTORICAL_QUERY_IDS + V04_QUERY_IDS
REQUIRED_V04_COVERAGE = frozenset(
    {
        "dataset-cardinality",
        "dataset-node-iri",
        "core-metadata-values",
        "distribution-values",
        "temporal-values",
        "temporal-order",
        "optional-fields",
        "profile-version-binding",
        "named-shapes",
        "constraint-components",
        "closed-shape-inventory",
        "inherited-record-contract",
    }
)
DISCOVERY_DIRECTORIES = MappingProxyType(
    {
        "C_Semantic_Treehouse/tests/sparql/queries": frozenset({".rq"}),
        "C_Semantic_Treehouse/tests/sparql/expected": frozenset({".tsv"}),
        "C_Semantic_Treehouse/tests/sparql/v0.4/queries": frozenset({".rq"}),
        "C_Semantic_Treehouse/tests/sparql/v0.4/expected": frozenset(
            {".tsv", ".txt"}
        ),
    }
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class DuplicateJsonKey(ValueError):
    """Raised when a JSON object repeats a key."""


@dataclass(frozen=True, order=True)
class ManifestIssue:
    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


@dataclass(frozen=True)
class AuthorityBundle:
    ok: bool
    documents: Mapping[str, dict[str, Any]]
    records: tuple[dict[str, Any], ...]
    issues: tuple[ManifestIssue, ...]

    @property
    def release_manifest(self) -> dict[str, Any] | None:
        return self.documents.get("release_manifest")

    @property
    def baseline_manifest(self) -> dict[str, Any] | None:
        return self.documents.get("baseline_test_cases")

    @property
    def requirements_manifest(self) -> dict[str, Any] | None:
        return self.documents.get("requirements")

    @property
    def v04_manifest(self) -> dict[str, Any] | None:
        return self.documents.get("v0_4_test_cases")

    @property
    def registry(self) -> dict[str, Any] | None:
        return self.documents.get("validation_suites")


@dataclass(frozen=True)
class SparqlManifestValidation:
    root: Path
    manifest_path: Path
    schema_path: Path
    manifest: dict[str, Any] | None
    manifest_sha256: str | None
    schema_sha256: str | None
    authority_bundle: AuthorityBundle
    artifacts_by_id: Mapping[str, dict[str, Any]]
    release_artifacts_by_id: Mapping[str, dict[str, Any]]
    issues: tuple[ManifestIssue, ...]
    discovered_paths: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.manifest is not None and not self.issues

    def deterministic_record(self) -> dict[str, Any]:
        queries = self.manifest.get("queries", []) if self.manifest else []
        releases: dict[str, int] = {}
        forms: dict[str, int] = {}
        for query in queries:
            if not isinstance(query, dict):
                continue
            release = query.get("release")
            form = query.get("query_form")
            if isinstance(release, str):
                releases[release] = releases.get(release, 0) + 1
            if isinstance(form, str):
                forms[form] = forms.get(form, 0) + 1
        return {
            "manifest_path": MANIFEST_RELPATH,
            "manifest_sha256": self.manifest_sha256,
            "schema_path": SCHEMA_RELPATH,
            "schema_sha256": self.schema_sha256,
            "manifest_schema_version": (
                self.manifest.get("manifest_schema_version")
                if self.manifest
                else None
            ),
            "required_query_ids": list(REQUIRED_QUERY_IDS),
            "query_count": len(queries),
            "artifact_count": len(self.artifacts_by_id),
            "query_counts_by_release": dict(sorted(releases.items())),
            "query_counts_by_form": dict(sorted(forms.items())),
            "discovered_paths": list(self.discovered_paths),
            "issues": [issue.as_dict() for issue in self.issues],
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonKey(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json_strict(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8-sig"), object_pairs_hook=_strict_object
    )


def _sorted_issues(issues: Iterable[ManifestIssue]) -> tuple[ManifestIssue, ...]:
    return tuple(sorted(issues))


def _json_pointer(parts: Iterable[Any]) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(encoded) if encoded else "/"


def _schema_issues(schema: Any, document: Any) -> list[ManifestIssue]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return [
            ManifestIssue(
                "schema_engine_missing",
                "/",
                "jsonschema is required for SPARQL manifest validation",
            )
        ]
    try:
        validator = Draft202012Validator(schema)
    except Exception as exc:  # noqa: BLE001 - malformed schema fails closed
        return [
            ManifestIssue(
                "schema_invalid",
                "/$schema",
                f"{exc.__class__.__name__}: schema construction failed",
            )
        ]
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: ([str(part) for part in error.absolute_path], error.message),
    )
    return [
        ManifestIssue(
            "schema_validation",
            _json_pointer(error.absolute_path),
            error.message,
        )
        for error in errors
    ]


def _repository_relative_path(value: Any) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        return None
    return path


def _safe_file(root: Path, relative: str) -> tuple[Path | None, str | None]:
    pure = _repository_relative_path(relative)
    if pure is None:
        return None, "path is not a normalized repository-relative POSIX path"
    lexical = root.joinpath(*pure.parts)
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            return None, "path traverses a symbolic link"
    try:
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(root.resolve())
    except (FileNotFoundError, OSError, ValueError):
        return None, "path is missing or escapes the repository"
    if not resolved.is_file():
        return None, "path does not name a regular file"
    if resolved.stat().st_size == 0:
        return None, "file is empty"
    return resolved, None


def _authority_issue(
    authority: str, code: str, location: str, message: str
) -> ManifestIssue:
    return ManifestIssue(
        f"authority_{code}", f"/authorities/{authority}{location}", message
    )


def _ensure_root_imports(root: Path) -> None:
    scripts_dir = str(root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)


def validate_authorities(root: Path) -> AuthorityBundle:
    """Run schema and semantic validation for every consumed authority."""

    root = root.resolve()
    _ensure_root_imports(root)
    issues: list[ManifestIssue] = []
    documents: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []

    try:
        from dssc_validation.release_manifest import (
            load_and_audit_release_manifest,
        )

        audit = load_and_audit_release_manifest(root)
        if audit.manifest is not None:
            documents["release_manifest"] = audit.manifest
        for issue in audit.issues:
            issues.append(
                _authority_issue(
                    "release_manifest",
                    str(issue.get("code", "semantic")),
                    str(issue.get("location", "/")),
                    str(issue.get("message", "release manifest validation failed")),
                )
            )
        records.append(
            {
                "id": "release_manifest",
                **audit.deterministic_record(),
                "status": "PASS" if audit.ok else "FAIL",
            }
        )
    except Exception as exc:  # noqa: BLE001 - authority failure is data
        issues.append(
            _authority_issue(
                "release_manifest",
                "exception",
                "/",
                f"{exc.__class__.__name__}: authority validator failed",
            )
        )

    try:
        from dssc_validation.baseline_manifest import (
            BaselineManifestError,
            load_and_validate_baseline_manifest,
        )

        try:
            baseline = load_and_validate_baseline_manifest(root)
        except BaselineManifestError as exc:
            for issue in exc.issues:
                issues.append(
                    _authority_issue(
                        "baseline_test_cases",
                        str(issue.code),
                        str(issue.location),
                        str(issue.message),
                    )
                )
        else:
            documents["baseline_test_cases"] = baseline.manifest
            records.append(
                {
                    "id": "baseline_test_cases",
                    "manifest_path": AUTHORITY_RELPATHS["baseline_test_cases"],
                    "manifest_sha256": baseline.manifest_sha256,
                    "schema_path": AUTHORITY_SCHEMA_RELPATHS[
                        "baseline_test_cases"
                    ],
                    "schema_sha256": baseline.schema_sha256,
                    "manifest_schema_version": baseline.manifest_schema_version,
                    "artifact_count": len(baseline.artifacts),
                    "case_count": len(baseline.cases),
                    "status": "PASS",
                }
            )
    except Exception as exc:  # noqa: BLE001
        issues.append(
            _authority_issue(
                "baseline_test_cases",
                "exception",
                "/",
                f"{exc.__class__.__name__}: authority validator failed",
            )
        )

    try:
        from dssc_validation.requirements_registry import (
            load_and_validate_requirements,
        )

        requirements = load_and_validate_requirements(root)
        if requirements.manifest is not None:
            documents["requirements"] = requirements.manifest
        for issue in requirements.issues:
            issues.append(
                _authority_issue(
                    "requirements",
                    str(issue.get("code", "semantic")),
                    str(issue.get("location", "/")),
                    str(issue.get("message", "requirements validation failed")),
                )
            )
        records.append(
            {
                "id": "requirements",
                **requirements.deterministic_record(),
                "status": "PASS" if requirements.ok else "FAIL",
            }
        )
    except Exception as exc:  # noqa: BLE001
        issues.append(
            _authority_issue(
                "requirements",
                "exception",
                "/",
                f"{exc.__class__.__name__}: authority validator failed",
            )
        )

    try:
        from dssc_validation.v04_manifest import load_and_validate_v04_manifest

        v04 = load_and_validate_v04_manifest(root)
        if v04.manifest is not None:
            documents["v0_4_test_cases"] = v04.manifest
        for issue in v04.issues:
            item = issue.as_dict()
            issues.append(
                _authority_issue(
                    "v0_4_test_cases",
                    item["code"],
                    item["location"],
                    item["message"],
                )
            )
        records.append(
            {
                "id": "v0_4_test_cases",
                **v04.deterministic_record(),
                "status": "PASS" if v04.ok else "FAIL",
            }
        )
    except Exception as exc:  # noqa: BLE001
        issues.append(
            _authority_issue(
                "v0_4_test_cases",
                "exception",
                "/",
                f"{exc.__class__.__name__}: authority validator failed",
            )
        )

    try:
        from dssc_validation.suite_registry import load_and_validate_registry

        registry = load_and_validate_registry(root)
        if registry.registry is not None:
            documents["validation_suites"] = registry.registry
        for issue in registry.issues:
            issues.append(
                _authority_issue(
                    "validation_suites", issue.code, "/", issue.message
                )
            )
        registry_schema = root / AUTHORITY_SCHEMA_RELPATHS["validation_suites"]
        records.append(
            {
                "id": "validation_suites",
                "manifest_path": AUTHORITY_RELPATHS["validation_suites"],
                "manifest_sha256": registry.registry_sha256,
                "schema_path": AUTHORITY_SCHEMA_RELPATHS["validation_suites"],
                "schema_sha256": (
                    sha256_file(registry_schema) if registry_schema.is_file() else None
                ),
                "contract_version": registry.contract_version,
                "status": "PASS" if registry.ok else "FAIL",
            }
        )
    except Exception as exc:  # noqa: BLE001
        issues.append(
            _authority_issue(
                "validation_suites",
                "exception",
                "/",
                f"{exc.__class__.__name__}: authority validator failed",
            )
        )

    release = documents.get("release_manifest")
    registry = documents.get("validation_suites")
    if release is not None and registry is not None:
        binding = release.get("validationSuiteRegistry")
        registry_path = root / AUTHORITY_RELPATHS["validation_suites"]
        actual_hash = sha256_file(registry_path) if registry_path.is_file() else None
        actual_version = registry.get("contract_version")
        if not isinstance(binding, dict):
            issues.append(
                _authority_issue(
                    "release_manifest",
                    "registry_binding",
                    "/validationSuiteRegistry",
                    "release manifest lacks the validation registry binding",
                )
            )
        else:
            if binding.get("path") != AUTHORITY_RELPATHS["validation_suites"]:
                issues.append(
                    _authority_issue(
                        "release_manifest",
                        "registry_path",
                        "/validationSuiteRegistry/path",
                        "release registry path does not name the canonical registry",
                    )
                )
            if binding.get("sha256") != actual_hash:
                issues.append(
                    _authority_issue(
                        "release_manifest",
                        "registry_hash",
                        "/validationSuiteRegistry/sha256",
                        "release registry hash differs from current bytes",
                    )
                )
            if binding.get("contractVersion") != actual_version:
                issues.append(
                    _authority_issue(
                        "release_manifest",
                        "registry_version",
                        "/validationSuiteRegistry/contractVersion",
                        "release registry contract version differs from current registry",
                    )
                )

    sorted_records = tuple(sorted(records, key=lambda item: str(item.get("id"))))
    sorted_issue_values = _sorted_issues(issues)
    return AuthorityBundle(
        ok=(not sorted_issue_values and len(documents) == len(AUTHORITY_RELPATHS)),
        documents=MappingProxyType(documents),
        records=sorted_records,
        issues=sorted_issue_values,
    )


def _release_indexes(
    release_manifest: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    release_by_id: dict[str, dict[str, Any]] = {}
    artifact_by_id: dict[str, dict[str, Any]] = {}
    if release_manifest is None:
        return release_by_id, artifact_by_id
    for release in release_manifest.get("releases", []):
        if not isinstance(release, dict) or not isinstance(release.get("id"), str):
            continue
        release_by_id[release["id"]] = release
        for artifact in release.get("artifacts", []):
            if not isinstance(artifact, dict) or not isinstance(
                artifact.get("id"), str
            ):
                continue
            artifact_copy = dict(artifact)
            artifact_copy["release"] = release["id"]
            artifact_by_id[artifact["id"]] = artifact_copy
    return release_by_id, artifact_by_id


def _discover_paths(root: Path, issues: list[ManifestIssue]) -> tuple[str, ...]:
    paths: list[str] = []
    for relative_dir, extensions in DISCOVERY_DIRECTORIES.items():
        directory = root.joinpath(*PurePosixPath(relative_dir).parts)
        if not directory.is_dir() or directory.is_symlink():
            issues.append(
                ManifestIssue(
                    "discovery_directory",
                    f"/discovery/{relative_dir}",
                    "fixed SPARQL discovery directory is missing or unsafe",
                )
            )
            continue
        for child in sorted(directory.iterdir(), key=lambda item: item.name):
            child_relative = child.relative_to(root).as_posix()
            if child.is_symlink():
                issues.append(
                    ManifestIssue(
                        "discovery_symlink",
                        f"/discovery/{child_relative}",
                        "SPARQL discovery does not follow symbolic links",
                    )
                )
                continue
            if child.is_dir():
                issues.append(
                    ManifestIssue(
                        "unexpected_discovery_directory",
                        f"/discovery/{child_relative}",
                        "fixed query/expected directories must contain only files",
                    )
                )
                continue
            if child.suffix in extensions:
                paths.append(child_relative)
    return tuple(sorted(paths))


def _path_hash_conflicts(
    document: dict[str, Any], authority: AuthorityBundle
) -> list[ManifestIssue]:
    records: list[tuple[str, str, str]] = []
    for index, artifact in enumerate(document.get("artifacts", [])):
        if isinstance(artifact, dict):
            path = artifact.get("path")
            digest = artifact.get("sha256")
            if isinstance(path, str) and isinstance(digest, str):
                records.append((path, digest, f"/artifacts/{index}"))
    release = authority.release_manifest or {}
    for release_index, release_item in enumerate(release.get("releases", [])):
        if not isinstance(release_item, dict):
            continue
        for artifact_index, artifact in enumerate(release_item.get("artifacts", [])):
            if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
                records.append(
                    (
                        artifact["path"],
                        str(artifact.get("sha256", "")),
                        f"/authorities/release_manifest/releases/{release_index}/"
                        f"artifacts/{artifact_index}",
                    )
                )
    baseline = authority.baseline_manifest or {}
    for index, artifact in enumerate(baseline.get("artifacts", [])):
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
            records.append(
                (
                    artifact["path"],
                    str(artifact.get("sha256", "")),
                    f"/authorities/baseline_test_cases/artifacts/{index}",
                )
            )
    by_path: dict[str, dict[str, list[str]]] = {}
    for path, digest, location in records:
        by_path.setdefault(path, {}).setdefault(digest, []).append(location)
    issues: list[ManifestIssue] = []
    for path, digests in sorted(by_path.items()):
        if len(digests) > 1:
            issues.append(
                ManifestIssue(
                    "path_hash_conflict",
                    "/artifacts",
                    f"path {path!r} is bound to multiple SHA-256 values: "
                    f"{sorted(digests)}",
                )
            )
    return issues


def _historical_oracle_issues(
    document: dict[str, Any],
    authority: AuthorityBundle,
    query_by_id: Mapping[str, dict[str, Any]],
    artifact_by_id: Mapping[str, dict[str, Any]],
) -> list[ManifestIssue]:
    baseline = authority.baseline_manifest or {}
    baseline_cases = {
        case.get("id"): case
        for case in baseline.get("cases", [])
        if isinstance(case, dict) and case.get("category") == "sparql"
    }
    baseline_artifacts = {
        artifact.get("id"): artifact
        for artifact in baseline.get("artifacts", [])
        if isinstance(artifact, dict)
    }
    issues: list[ManifestIssue] = []
    for query_id in HISTORICAL_QUERY_IDS:
        query = query_by_id.get(query_id)
        baseline_case = baseline_cases.get(query_id)
        location = f"/queries/{query_id}"
        if query is None or baseline_case is None:
            issues.append(
                ManifestIssue(
                    "historical_case_missing",
                    location,
                    "historical SPARQL case is absent from one of the manifests",
                )
            )
            continue
        expected = {
            "release": baseline_case.get("release"),
            "required": baseline_case.get("required"),
            "enabled": baseline_case.get("enabled"),
            "artifact_refs": baseline_case.get("artifact_refs"),
            "comparison": {
                "kind": baseline_case.get("engine_config", {}).get("comparison"),
                "sort_rows": baseline_case.get("engine_config", {}).get("sort_rows"),
                "preserve_duplicates": baseline_case.get("engine_config", {}).get(
                    "preserve_duplicates"
                ),
            },
            "oracle": {
                "expected_variables": baseline_case.get("oracle", {}).get(
                    "expected_variables"
                ),
                "expected_row_count": baseline_case.get("oracle", {}).get(
                    "expected_row_count"
                ),
                "allow_empty": False,
            },
        }
        actual = {key: query.get(key) for key in expected}
        if actual != expected:
            issues.append(
                ManifestIssue(
                    "historical_oracle_changed",
                    location,
                    "historical release, graph, comparison, or oracle differs from baseline",
                )
            )
        refs = baseline_case.get("artifact_refs", {})
        for role in ("query", "expected"):
            artifact_id = refs.get(role) if isinstance(refs, dict) else None
            actual_artifact = artifact_by_id.get(artifact_id)
            baseline_artifact = baseline_artifacts.get(artifact_id)
            if actual_artifact != baseline_artifact:
                issues.append(
                    ManifestIssue(
                        "historical_artifact_changed",
                        f"{location}/artifact_refs/{role}",
                        "historical query/expected path or hash differs from baseline",
                    )
                )
    return issues


def _release_assertion_issues(
    query: dict[str, Any],
    query_location: str,
    release_artifacts: Mapping[str, dict[str, Any]],
) -> list[ManifestIssue]:
    issues: list[ManifestIssue] = []
    for index, assertion in enumerate(query.get("release_assertions", [])):
        if not isinstance(assertion, dict):
            continue
        location = f"{query_location}/release_assertions/{index}"
        artifact_id = assertion.get("artifact_ref")
        artifact = release_artifacts.get(artifact_id)
        if artifact is None:
            issues.append(
                ManifestIssue(
                    "dangling_release_assertion", location, f"unknown artifact {artifact_id!r}"
                )
            )
            continue
        if artifact.get("release") != query.get("release"):
            issues.append(
                ManifestIssue(
                    "release_assertion_version",
                    location,
                    "release assertion artifact belongs to a different release",
                )
            )
        origin = artifact.get("origin")
        if not isinstance(origin, dict):
            origin = {}
        comparisons = {
            "origin_type": origin.get("type"),
            "inherited_from": origin.get("inheritedFrom"),
            "source_artifact": origin.get("sourceArtifact"),
            "change": origin.get("change"),
        }
        for key, expected in assertion.items():
            if key == "artifact_ref":
                continue
            if comparisons.get(key) != expected:
                issues.append(
                    ManifestIssue(
                        "release_assertion_mismatch",
                        f"{location}/{key}",
                        f"expected {expected!r}; release manifest has {comparisons.get(key)!r}",
                    )
                )
    return issues


def semantic_validate_sparql_manifest(
    document: dict[str, Any],
    root: Path,
    authority: AuthorityBundle,
    *,
    verify_hashes: bool = True,
    check_orphans: bool = True,
) -> tuple[
    tuple[ManifestIssue, ...],
    Mapping[str, dict[str, Any]],
    Mapping[str, dict[str, Any]],
    tuple[str, ...],
]:
    """Validate IDs, references, paths, hashes, required sets, and orphans."""

    issues: list[ManifestIssue] = list(authority.issues)
    release_by_id, release_artifacts = _release_indexes(authority.release_manifest)
    requirement_ids = {
        item.get("id")
        for item in (authority.requirements_manifest or {}).get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    artifacts: dict[str, dict[str, Any]] = {}
    used_artifact_ids: set[str] = set()
    for index, artifact in enumerate(document.get("artifacts", [])):
        if not isinstance(artifact, dict):
            continue
        location = f"/artifacts/{index}"
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str):
            continue
        if artifact_id in artifacts:
            issues.append(
                ManifestIssue(
                    "duplicate_artifact_id",
                    f"{location}/id",
                    f"duplicate artifact ID {artifact_id!r}",
                )
            )
        else:
            artifacts[artifact_id] = artifact
        release_id = artifact.get("release")
        if release_id not in release_by_id:
            issues.append(
                ManifestIssue(
                    "dangling_artifact_release",
                    f"{location}/release",
                    f"unknown release {release_id!r}",
                )
            )
        relative = artifact.get("path")
        if not isinstance(relative, str):
            continue
        path, path_error = _safe_file(root, relative)
        if path_error is not None:
            issues.append(ManifestIssue("artifact_path", f"{location}/path", path_error))
            continue
        if verify_hashes:
            actual_hash = sha256_file(path)
            if artifact.get("sha256") != actual_hash:
                issues.append(
                    ManifestIssue(
                        "artifact_hash_mismatch",
                        f"{location}/sha256",
                        f"expected {artifact.get('sha256')!r}; actual {actual_hash}",
                    )
                )

    queries: dict[str, dict[str, Any]] = {}
    query_order: list[str] = []
    v04_coverage: set[str] = set()
    for index, query in enumerate(document.get("queries", [])):
        if not isinstance(query, dict):
            continue
        location = f"/queries/{index}"
        query_id = query.get("id")
        if not isinstance(query_id, str):
            continue
        query_order.append(query_id)
        if query_id in queries:
            issues.append(
                ManifestIssue(
                    "duplicate_query_id",
                    f"{location}/id",
                    f"duplicate query ID {query_id!r}",
                )
            )
        else:
            queries[query_id] = query
        release_id = query.get("release")
        if release_id not in release_by_id:
            issues.append(
                ManifestIssue(
                    "dangling_query_release",
                    f"{location}/release",
                    f"unknown release {release_id!r}",
                )
            )
        if query.get("required") is True and query.get("enabled") is not True:
            issues.append(
                ManifestIssue(
                    "required_query_skipped",
                    f"{location}/enabled",
                    "a required query cannot be disabled or skipped",
                )
            )
        if release_id == "v0.4":
            v04_coverage.update(
                item for item in query.get("coverage", []) if isinstance(item, str)
            )
        refs = query.get("artifact_refs")
        if not isinstance(refs, dict):
            continue
        query_artifact_id = refs.get("query")
        expected_artifact_id = refs.get("expected")
        for role, artifact_id in (
            ("query", query_artifact_id),
            ("expected", expected_artifact_id),
        ):
            artifact = artifacts.get(artifact_id)
            if artifact is None:
                issues.append(
                    ManifestIssue(
                        f"dangling_{role}_reference",
                        f"{location}/artifact_refs/{role}",
                        f"unknown SPARQL artifact {artifact_id!r}",
                    )
                )
                continue
            used_artifact_ids.add(str(artifact_id))
            if artifact.get("release") != release_id:
                issues.append(
                    ManifestIssue(
                        "artifact_release_mismatch",
                        f"{location}/artifact_refs/{role}",
                        "query and query/expected artifact releases differ",
                    )
                )
        expected_kinds = {
            "SELECT": ("sparql-query", "expected-tsv"),
            "ASK": ("sparql-query", "expected-boolean"),
            "COUNT": ("sparql-query", "expected-integer"),
        }
        query_form = query.get("query_form")
        if query_form in expected_kinds:
            query_artifact = artifacts.get(query_artifact_id)
            expected_artifact = artifacts.get(expected_artifact_id)
            query_kind, expected_kind = expected_kinds[str(query_form)]
            if query_artifact is not None and query_artifact.get("kind") != query_kind:
                issues.append(
                    ManifestIssue(
                        "query_artifact_kind",
                        f"{location}/artifact_refs/query",
                        f"{query_form} query requires kind {query_kind}",
                    )
                )
            if expected_artifact is not None and expected_artifact.get("kind") != expected_kind:
                issues.append(
                    ManifestIssue(
                        "expected_artifact_kind",
                        f"{location}/artifact_refs/expected",
                        f"{query_form} query requires kind {expected_kind}",
                    )
                )
        for role in ("graph_inputs", "local_contexts"):
            for ref_index, artifact_id in enumerate(refs.get(role, [])):
                artifact = release_artifacts.get(artifact_id)
                ref_location = f"{location}/artifact_refs/{role}/{ref_index}"
                if artifact is None:
                    issues.append(
                        ManifestIssue(
                            "dangling_graph_reference",
                            ref_location,
                            f"unknown release artifact {artifact_id!r}",
                        )
                    )
                    continue
                if artifact.get("release") != release_id:
                    issues.append(
                        ManifestIssue(
                            "graph_release_mismatch",
                            ref_location,
                            f"artifact belongs to {artifact.get('release')!r}, not {release_id!r}",
                        )
                    )
                if role == "graph_inputs" and artifact.get("mediaType") not in {
                    "text/turtle",
                    "application/ld+json",
                }:
                    issues.append(
                        ManifestIssue(
                            "graph_media_type",
                            ref_location,
                            f"unsupported graph media type {artifact.get('mediaType')!r}",
                        )
                    )
                if role == "local_contexts" and artifact.get("mediaType") != "application/ld+json":
                    issues.append(
                        ManifestIssue(
                            "context_media_type",
                            ref_location,
                            "local context must be an application/ld+json artifact",
                        )
                    )
        for req_index, requirement_id in enumerate(query.get("requirement_refs", [])):
            if requirement_id not in requirement_ids:
                issues.append(
                    ManifestIssue(
                        "dangling_requirement_reference",
                        f"{location}/requirement_refs/{req_index}",
                        f"unknown requirement {requirement_id!r}",
                    )
                )
        issues.extend(_release_assertion_issues(query, location, release_artifacts))

    declared_required = document.get("required_query_ids")
    if declared_required != list(REQUIRED_QUERY_IDS):
        issues.append(
            ManifestIssue(
                "required_query_set",
                "/required_query_ids",
                "required query IDs must equal the fixed historical and v0.4 CQ order",
            )
        )
    if query_order != list(REQUIRED_QUERY_IDS):
        issues.append(
            ManifestIssue(
                "query_order_or_set",
                "/queries",
                "query records must equal the fixed required CQ order exactly once",
            )
        )
    if v04_coverage != REQUIRED_V04_COVERAGE:
        missing = sorted(REQUIRED_V04_COVERAGE - v04_coverage)
        extra = sorted(v04_coverage - REQUIRED_V04_COVERAGE)
        issues.append(
            ManifestIssue(
                "required_v04_coverage",
                "/queries",
                f"v0.4 coverage mismatch; missing={missing}; extra={extra}",
            )
        )
    for artifact_id in sorted(set(artifacts) - used_artifact_ids):
        issues.append(
            ManifestIssue(
                "orphan_manifest_artifact",
                f"/artifacts/{artifact_id}",
                "query/expected artifact is not referenced by a query",
            )
        )

    issues.extend(_path_hash_conflicts(document, authority))
    issues.extend(_historical_oracle_issues(document, authority, queries, artifacts))

    discovered_paths = _discover_paths(root, issues) if check_orphans else ()
    if check_orphans:
        declared_paths = {
            artifact.get("path")
            for artifact in document.get("artifacts", [])
            if isinstance(artifact, dict) and isinstance(artifact.get("path"), str)
        }
        for path in sorted(set(discovered_paths) - declared_paths):
            issues.append(
                ManifestIssue(
                    "orphan_file",
                    f"/discovery/{path}",
                    "query or expected file is absent from the SPARQL manifest",
                )
            )
        for path in sorted(declared_paths - set(discovered_paths)):
            issues.append(
                ManifestIssue(
                    "undiscovered_artifact",
                    f"/artifacts/{path}",
                    "manifest query/expected path is outside fixed discovery or missing",
                )
            )

    return (
        _sorted_issues(issues),
        MappingProxyType(artifacts),
        MappingProxyType(release_artifacts),
        discovered_paths,
    )


def validate_sparql_manifest_document(
    document: Any,
    schema: Any,
    root: Path,
    authority: AuthorityBundle,
    *,
    verify_hashes: bool = True,
    check_orphans: bool = True,
) -> tuple[
    tuple[ManifestIssue, ...],
    Mapping[str, dict[str, Any]],
    Mapping[str, dict[str, Any]],
    tuple[str, ...],
]:
    schema_issues = _schema_issues(schema, document)
    if schema_issues:
        return _sorted_issues(schema_issues), MappingProxyType({}), MappingProxyType({}), ()
    if not isinstance(document, dict):
        return (
            (ManifestIssue("manifest_root", "/", "manifest root must be an object"),),
            MappingProxyType({}),
            MappingProxyType({}),
            (),
        )
    return semantic_validate_sparql_manifest(
        document,
        root,
        authority,
        verify_hashes=verify_hashes,
        check_orphans=check_orphans,
    )


def load_and_validate_sparql_manifest(
    root: Path,
    *,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
    authority_bundle: AuthorityBundle | None = None,
    verify_hashes: bool = True,
    check_orphans: bool = True,
) -> SparqlManifestValidation:
    root = root.resolve()
    manifest_path = manifest_path or root.joinpath(*PurePosixPath(MANIFEST_RELPATH).parts)
    schema_path = schema_path or root.joinpath(*PurePosixPath(SCHEMA_RELPATH).parts)
    authority = authority_bundle or validate_authorities(root)
    issues: list[ManifestIssue] = []
    document: dict[str, Any] | None = None
    schema: Any = None
    if not schema_path.is_file():
        issues.append(ManifestIssue("missing_schema", "/$schema", "SPARQL schema is missing"))
    else:
        try:
            schema = load_json_strict(schema_path)
        except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKey) as exc:
            issues.append(
                ManifestIssue(
                    "schema_parse",
                    "/$schema",
                    f"{exc.__class__.__name__}: SPARQL schema cannot be parsed",
                )
            )
    if not manifest_path.is_file():
        issues.append(ManifestIssue("missing_manifest", "/", "SPARQL manifest is missing"))
    else:
        try:
            value = load_json_strict(manifest_path)
        except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKey) as exc:
            issues.append(
                ManifestIssue(
                    "manifest_parse",
                    "/",
                    f"{exc.__class__.__name__}: SPARQL manifest cannot be parsed",
                )
            )
        else:
            if isinstance(value, dict):
                document = value
            else:
                issues.append(
                    ManifestIssue("manifest_root", "/", "manifest root must be an object")
                )
    artifacts: Mapping[str, dict[str, Any]] = MappingProxyType({})
    release_artifacts: Mapping[str, dict[str, Any]] = MappingProxyType({})
    discovered: tuple[str, ...] = ()
    if document is not None and schema is not None and not issues:
        semantic_issues, artifacts, release_artifacts, discovered = (
            validate_sparql_manifest_document(
                document,
                schema,
                root,
                authority,
                verify_hashes=verify_hashes,
                check_orphans=check_orphans,
            )
        )
        issues.extend(semantic_issues)
    else:
        issues.extend(authority.issues)
    return SparqlManifestValidation(
        root=root,
        manifest_path=manifest_path,
        schema_path=schema_path,
        manifest=document,
        manifest_sha256=(sha256_file(manifest_path) if manifest_path.is_file() else None),
        schema_sha256=(sha256_file(schema_path) if schema_path.is_file() else None),
        authority_bundle=authority,
        artifacts_by_id=artifacts,
        release_artifacts_by_id=release_artifacts,
        issues=_sorted_issues(issues),
        discovered_paths=discovered,
    )


__all__ = [
    "AUTHORITY_RELPATHS",
    "AUTHORITY_SCHEMA_RELPATHS",
    "AuthorityBundle",
    "HISTORICAL_QUERY_IDS",
    "MANIFEST_RELPATH",
    "ManifestIssue",
    "REQUIRED_QUERY_IDS",
    "REQUIRED_V04_COVERAGE",
    "SCHEMA_RELPATH",
    "SparqlManifestValidation",
    "V04_QUERY_IDS",
    "load_and_validate_sparql_manifest",
    "load_json_strict",
    "semantic_validate_sparql_manifest",
    "sha256_file",
    "validate_authorities",
    "validate_sparql_manifest_document",
]
