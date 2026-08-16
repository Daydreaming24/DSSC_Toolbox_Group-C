"""Schema and cross-record validation for the v0.4 four-state manifest.

The public loader is intentionally side-effect free.  It validates the JSON
Schema first, resolves all authority references against the repository root,
and verifies fixture bytes before returning an ``ok`` result.  The document
level entry points make the same checks available to negative controls without
rewriting the canonical manifest.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from dssc_validation.hashing import sha256_file


MANIFEST_RELPATH = "C_Semantic_Treehouse/manifests/v0.4-test-cases.json"
SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/manifests/schemas/v0.4-test-cases.schema.json"
)
RELEASE_MANIFEST_RELPATH = "C_Semantic_Treehouse/manifests/release-manifest.json"
REQUIREMENTS_MANIFEST_RELPATH = (
    "C_Semantic_Treehouse/manifests/v0.4-requirements.json"
)

EXPECTED_RELEASE_ID = "v0.4"
EXPECTED_PROFILE_ID = "dssc-building-energy-metadata-v0.4"
EXPECTED_SHAPE_ARTIFACT_ID = "v04-metadata-shapes"
EXPECTED_SHAPE_PATH = (
    "C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl"
)
EXPECTED_SHAPE_SHA256 = (
    "a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda"
)

FAILURE_REASON_BY_STAGE: dict[str, frozenset[str]] = {
    "INPUT_PARSE": frozenset({"MALFORMED_JSON", "MALFORMED_RDF"}),
    "OFFLINE_LOAD": frozenset(
        {"JSONLD_EXPANSION_ERROR", "OFFLINE_CONTEXT_UNAVAILABLE"}
    ),
    "VALIDATOR_EXECUTION": frozenset(
        {
            "VALIDATOR_TIMEOUT",
            "VALIDATOR_CRASH",
            "VALIDATION_SERVICE_RUNTIME_EXCEPTION",
        }
    ),
}

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[/\\]")
_STATUS_DIRECTORIES = {
    "PASS": "pass",
    "FAIL": "fail",
    "INAPPLICABLE": "inapplicable",
    "UNTESTABLE": "untestable",
}


@dataclass(frozen=True, order=True)
class ManifestIssue:
    """One stable, machine-readable manifest failure."""

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
class V04ManifestValidationResult:
    """Complete result of loading and validating one manifest document."""

    manifest_path: Path
    schema_path: Path
    manifest: dict[str, Any] | None
    manifest_sha256: str | None
    schema_sha256: str | None
    release_manifest_sha256: str | None
    requirements_manifest_sha256: str | None
    issues: tuple[ManifestIssue, ...]

    @property
    def ok(self) -> bool:
        return self.manifest is not None and not self.issues

    def deterministic_record(self) -> dict[str, Any]:
        cases = self.manifest.get("cases", []) if self.manifest else []
        fixture_records = [
            {
                "assertion_id": case["fixture"]["assertion_id"],
                "path": case["fixture"]["path"],
                "sha256": case["fixture"]["sha256"],
            }
            for case in cases
            if isinstance(case, dict) and isinstance(case.get("fixture"), dict)
            and all(
                key in case["fixture"]
                for key in ("assertion_id", "path", "sha256")
            )
        ]
        status_counts = {
            status: sum(
                1
                for case in cases
                if isinstance(case, dict)
                and case.get("expected_business_status") == status
            )
            for status in ("PASS", "FAIL", "INAPPLICABLE", "UNTESTABLE")
        }
        return {
            "manifest_path": MANIFEST_RELPATH,
            "manifest_sha256": self.manifest_sha256,
            "schema_path": SCHEMA_RELPATH,
            "schema_sha256": self.schema_sha256,
            "release_manifest_path": RELEASE_MANIFEST_RELPATH,
            "release_manifest_sha256": self.release_manifest_sha256,
            "requirements_manifest_path": REQUIREMENTS_MANIFEST_RELPATH,
            "requirements_manifest_sha256": self.requirements_manifest_sha256,
            "manifest_schema_version": (
                self.manifest.get("manifest_schema_version")
                if self.manifest
                else None
            ),
            "case_ids": [
                case.get("case_id") for case in cases if isinstance(case, dict)
            ],
            "case_count": len(cases),
            "business_status_counts": status_counts,
            "fixtures": fixture_records,
            "issues": [issue.as_dict() for issue in self.issues],
        }


class _DuplicateKey(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKey(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_reject_duplicate_keys)


def _location(parts: tuple[Any, ...] | list[Any]) -> str:
    if not parts:
        return "$"
    return "$" + "".join(
        f"[{part}]" if isinstance(part, int) else f".{part}" for part in parts
    )


def _issue(code: str, location: str, message: str) -> ManifestIssue:
    return ManifestIssue(code=code, location=location, message=message)


def _sorted_issues(issues: list[ManifestIssue]) -> tuple[ManifestIssue, ...]:
    return tuple(sorted(set(issues)))


def _duplicates(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for value in values:
        try:
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        except TypeError:
            continue
    return sorted(duplicates, key=str)


def _schema_issues(schema: Any, document: Any) -> list[ManifestIssue]:
    if not isinstance(schema, dict):
        return [_issue("SCHEMA_ROOT", "$schema", "schema root must be an object")]
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [
            _issue(
                "SCHEMA_INVALID",
                _location(tuple(exc.absolute_schema_path)),
                exc.message,
            )
        ]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(document),
        key=lambda item: (
            tuple(str(part) for part in item.absolute_path),
            tuple(str(part) for part in item.absolute_schema_path),
            item.message,
        ),
    )
    return [
        _issue(
            "SCHEMA_VALIDATION",
            _location(tuple(error.absolute_path)),
            error.message,
        )
        for error in errors
    ]


def _safe_repo_path(root: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, "repository path must be a non-empty string"
    if "\x00" in value:
        return None, "repository path contains NUL"
    if (
        value.startswith("/")
        or value.startswith("\\")
        or _WINDOWS_ABSOLUTE.match(value)
        or "\\" in value
        or "//" in value
        or value.endswith("/")
    ):
        return None, "repository path must use a normalized relative POSIX path"
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None, "repository path contains an unsafe segment"
    candidate = (root / Path(*parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None, "repository path resolves outside the repository"
    return candidate, None


def _verify_file_binding(
    root: Path,
    path_value: Any,
    sha_value: Any,
    location: str,
    issues: list[ManifestIssue],
    *,
    role: str,
    verify_hash: bool = True,
) -> str | None:
    path, path_issue = _safe_repo_path(root, path_value)
    if path_issue:
        issues.append(_issue("UNSAFE_PATH", f"{location}.path", path_issue))
        return None
    if not isinstance(sha_value, str) or _SHA256.fullmatch(sha_value) is None:
        issues.append(
            _issue(
                "INVALID_SHA256",
                f"{location}.sha256",
                f"{role} must declare a lowercase SHA-256",
            )
        )
        return None
    if not verify_hash:
        return None
    if path is None or not path.is_file():
        issues.append(
            _issue(
                f"{role.upper()}_MISSING",
                f"{location}.path",
                f"bound {role} file is missing: {path_value}",
            )
        )
        return None
    try:
        actual = sha256_file(path)
    except OSError as exc:
        issues.append(
            _issue(
                f"{role.upper()}_UNREADABLE",
                f"{location}.path",
                f"cannot hash {role}: {exc.__class__.__name__}",
            )
        )
        return None
    if actual != sha_value:
        issues.append(
            _issue(
                f"{role.upper()}_HASH_MISMATCH",
                f"{location}.sha256",
                f"expected {sha_value}; actual {actual}",
            )
        )
    return actual


def _count_bounds(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, dict):
        return None
    exact = value.get("exact")
    if isinstance(exact, int) and not isinstance(exact, bool):
        return exact, exact
    minimum = value.get("minimum")
    maximum = value.get("maximum")
    if (
        isinstance(minimum, int)
        and not isinstance(minimum, bool)
        and isinstance(maximum, int)
        and not isinstance(maximum, bool)
    ):
        return minimum, maximum
    return None


def _requirement_maps(
    requirements_manifest: dict[str, Any],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, str],
    dict[str, str],
]:
    requirements = {
        item["id"]: item
        for item in requirements_manifest.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    decision_id_to_path = {
        item["id"]: item["path"]
        for item in requirements_manifest.get("decision_catalog", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("path"), str)
    }
    decision_path_to_id = {
        path: decision_id for decision_id, path in decision_id_to_path.items()
    }
    return requirements, decision_id_to_path, decision_path_to_id


def _release_map(release_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in release_manifest.get("releases", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _result_reference_issues(
    result: dict[str, Any],
    location: str,
    case_requirement_ids: set[str],
    requirements: dict[str, dict[str, Any]],
) -> list[ManifestIssue]:
    issues: list[ManifestIssue] = []
    requirement_id = result.get("requirement_id")
    if requirement_id not in case_requirement_ids:
        issues.append(
            _issue(
                "RESULT_REQUIREMENT_NOT_IN_CASE",
                f"{location}.requirement_id",
                f"result references requirement outside its case: {requirement_id}",
            )
        )
    requirement = requirements.get(str(requirement_id))
    if requirement is None:
        issues.append(
            _issue(
                "DANGLING_RESULT_REQUIREMENT",
                f"{location}.requirement_id",
                f"unknown requirement ID: {requirement_id}",
            )
        )
        return issues

    locators = [
        source.get("locator")
        for source in requirement.get("sources", [])
        if isinstance(source, dict)
        and isinstance(source.get("locator"), dict)
        and source["locator"].get("kind") == "SHACL_SHAPE"
    ]
    candidates = [
        locator
        for locator in locators
        if locator.get("shape") == result.get("source_shape")
        and result.get("source_constraint_component")
        in locator.get("constraint_components", [])
        and locator.get("severity") == result.get("severity")
    ]
    if not candidates:
        issues.append(
            _issue(
                "RESULT_SOURCE_REFERENCE_MISMATCH",
                location,
                "source shape/component/severity does not map to the requirement",
            )
        )
        return issues

    result_path = result.get("result_path")
    source_paths = {locator.get("path") for locator in candidates}
    non_null_paths = {path for path in source_paths if isinstance(path, str)}
    if non_null_paths:
        if result_path is None:
            issues.append(
                _issue(
                    "RESULT_PATH_REQUIRED",
                    f"{location}.result_path",
                    "a property-path requirement must assert result_path",
                )
            )
        elif result_path not in non_null_paths:
            issues.append(
                _issue(
                    "RESULT_PATH_MISMATCH",
                    f"{location}.result_path",
                    f"expected one of {sorted(non_null_paths)}; got {result_path}",
                )
            )
    elif result_path is not None and requirement_id != "D04-R016":
        issues.append(
            _issue(
                "UNEXPECTED_RESULT_PATH",
                f"{location}.result_path",
                "node/SPARQL result has no normative result path",
            )
        )

    messages = {
        message
        for locator in candidates
        for message in locator.get("messages", [])
        if isinstance(message, str)
    }
    message_assertion = result.get("message")
    if isinstance(message_assertion, dict):
        policy = message_assertion.get("policy")
        value = message_assertion.get("value")
        if messages:
            if policy != "EXACT" or value not in messages:
                issues.append(
                    _issue(
                        "RESULT_MESSAGE_MISMATCH",
                        f"{location}.message",
                        "a normative sh:message requires its exact registered text",
                    )
                )
        elif policy != "PRESENT":
            issues.append(
                _issue(
                    "RESULT_MESSAGE_POLICY",
                    f"{location}.message",
                    "a Shape without normative sh:message requires PRESENT policy",
                )
            )
    return issues


def semantic_validate_v04_manifest(
    document: dict[str, Any],
    root: Path,
    *,
    release_manifest: dict[str, Any] | None = None,
    requirements_manifest: dict[str, Any] | None = None,
    verify_fixture_hashes: bool = True,
) -> tuple[ManifestIssue, ...]:
    """Validate paths, bytes, IDs, and all cross-record references.

    Callers may inject already-loaded authority documents for deterministic
    negative controls.  Fixture hashing can be disabled only for schema and
    pure semantic controls; the canonical suite must use the default ``True``.
    Shape and evidence bindings are always verified.
    """

    root = root.resolve()
    issues: list[ManifestIssue] = []

    if release_manifest is None:
        try:
            value = _load_json(root / RELEASE_MANIFEST_RELPATH)
        except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateKey) as exc:
            issues.append(
                _issue(
                    "RELEASE_MANIFEST_UNAVAILABLE",
                    RELEASE_MANIFEST_RELPATH,
                    f"{exc.__class__.__name__}: cannot load release authority",
                )
            )
            release_manifest = {}
        else:
            release_manifest = value if isinstance(value, dict) else {}
    if requirements_manifest is None:
        try:
            value = _load_json(root / REQUIREMENTS_MANIFEST_RELPATH)
        except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateKey) as exc:
            issues.append(
                _issue(
                    "REQUIREMENTS_MANIFEST_UNAVAILABLE",
                    REQUIREMENTS_MANIFEST_RELPATH,
                    f"{exc.__class__.__name__}: cannot load requirements authority",
                )
            )
            requirements_manifest = {}
        else:
            requirements_manifest = value if isinstance(value, dict) else {}

    release_manifest = release_manifest or {}
    requirements_manifest = requirements_manifest or {}
    releases = _release_map(release_manifest)
    requirements, decision_id_to_path, decision_path_to_id = _requirement_maps(
        requirements_manifest
    )
    planned_cases = {
        item["id"]: item
        for item in requirements_manifest.get("planned_cases", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    business_planned_case_ids = {
        planned_case_id
        for planned_case_id, planned_case in planned_cases.items()
        if planned_case.get("expected_business_status") is not None
    }

    top_release = document.get("release", {})
    release_id = top_release.get("id") if isinstance(top_release, dict) else None
    release = releases.get(str(release_id))
    if release is None:
        issues.append(
            _issue(
                "DANGLING_RELEASE_REFERENCE",
                "$.release.id",
                f"unknown release ID: {release_id}",
            )
        )
    elif release_manifest.get("currentRelease") != release_id:
        issues.append(
            _issue(
                "RELEASE_NOT_CURRENT",
                "$.release.id",
                f"release {release_id} is not the release-manifest currentRelease",
            )
        )

    top_profile = document.get("profile", {})
    profile_id = top_profile.get("id") if isinstance(top_profile, dict) else None
    authority_profile = requirements_manifest.get("profile", {})
    if (
        not isinstance(authority_profile, dict)
        or authority_profile.get("id") != profile_id
    ):
        issues.append(
            _issue(
                "DANGLING_PROFILE_REFERENCE",
                "$.profile.id",
                f"profile is absent from requirements authority: {profile_id}",
            )
        )

    shape = document.get("shape_artifact", {})
    shape_assertion_id = (
        shape.get("assertion_id") if isinstance(shape, dict) else None
    )
    artifact_assertion_ids: list[Any] = [shape_assertion_id]
    artifact_bindings: list[tuple[str, Any, Any]] = []
    if isinstance(shape, dict):
        artifact_bindings.append(("$.shape_artifact", shape.get("path"), shape.get("sha256")))
        _verify_file_binding(
            root,
            shape.get("path"),
            shape.get("sha256"),
            "$.shape_artifact",
            issues,
            role="artifact",
        )
        release_artifacts = (
            release.get("artifacts", []) if isinstance(release, dict) else []
        )
        matching_artifacts = [
            artifact
            for artifact in release_artifacts
            if isinstance(artifact, dict)
            and artifact.get("id") == shape.get("artifact_id")
        ]
        if len(matching_artifacts) != 1:
            issues.append(
                _issue(
                    "DANGLING_SHAPE_ARTIFACT_REFERENCE",
                    "$.shape_artifact.artifact_id",
                    f"release does not contain exactly one artifact {shape.get('artifact_id')}",
                )
            )
        else:
            authority_shape = matching_artifacts[0]
            if (
                authority_shape.get("path") != shape.get("path")
                or authority_shape.get("sha256") != shape.get("sha256")
            ):
                issues.append(
                    _issue(
                        "SHAPE_ARTIFACT_BINDING_MISMATCH",
                        "$.shape_artifact",
                        "shape artifact path/hash differs from the release manifest",
                    )
                )

    evidence_refs = document.get("evidence_refs", {})
    if isinstance(evidence_refs, dict):
        for key in ("meta_shacl", "shape_structure"):
            evidence = evidence_refs.get(key)
            if not isinstance(evidence, dict):
                continue
            location = f"$.evidence_refs.{key}"
            artifact_assertion_ids.append(evidence.get("assertion_id"))
            artifact_bindings.append((location, evidence.get("path"), evidence.get("sha256")))
            _verify_file_binding(
                root,
                evidence.get("path"),
                evidence.get("sha256"),
                location,
                issues,
                role="evidence",
            )
    for duplicate in _duplicates(artifact_assertion_ids):
        issues.append(
            _issue(
                "DUPLICATE_ARTIFACT_ASSERTION_ID",
                "$.shape_artifact|$.evidence_refs",
                f"duplicate artifact assertion ID: {duplicate}",
            )
        )
    artifact_path_hashes: dict[str, set[str]] = {}
    for _, path_value, sha_value in artifact_bindings:
        if isinstance(path_value, str) and isinstance(sha_value, str):
            artifact_path_hashes.setdefault(path_value, set()).add(sha_value)
    for path_value, hashes in sorted(artifact_path_hashes.items()):
        if len(hashes) > 1:
            issues.append(
                _issue(
                    "SAME_ARTIFACT_PATH_HASH_CONFLICT",
                    "$.shape_artifact|$.evidence_refs",
                    f"one artifact path has multiple hashes: {path_value}",
                )
            )

    cases = document.get("cases", [])
    case_ids = [
        case.get("case_id") for case in cases if isinstance(case, dict)
    ]
    fixture_ids = [
        case["fixture"].get("assertion_id")
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("fixture"), dict)
    ]
    for duplicate in _duplicates(case_ids):
        issues.append(
            _issue(
                "DUPLICATE_CASE_ID",
                "$.cases",
                f"duplicate case ID: {duplicate}",
            )
        )
    for duplicate in _duplicates(fixture_ids):
        issues.append(
            _issue(
                "DUPLICATE_FIXTURE_ASSERTION_ID",
                "$.cases[*].fixture.assertion_id",
                f"duplicate fixture assertion ID: {duplicate}",
            )
        )

    covered_requirements: set[str] = set()
    realized_planned_case_ids: set[str] = set()
    fixture_path_hashes: dict[str, set[str]] = {}
    result_assertion_ids: list[Any] = []
    result_signatures: dict[str, list[tuple[Any, ...]]] = {}

    for case_index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        location = f"$.cases[{case_index}]"
        case_id = case.get("case_id")
        status = case.get("expected_business_status")
        case_requirements = {
            item for item in case.get("requirement_ids", []) if isinstance(item, str)
        }
        covered_requirements.update(case_requirements & set(requirements))

        planned_case = planned_cases.get(str(case_id))
        if planned_case is None:
            issues.append(
                _issue(
                    "DANGLING_PLANNED_CASE_REFERENCE",
                    f"{location}.case_id",
                    f"case ID is absent from requirements planned_cases: {case_id}",
                )
            )
        elif planned_case.get("expected_business_status") is None:
            issues.append(
                _issue(
                    "PROGRAM_ERROR_PLANNED_CASE_IN_FIXTURE_MANIFEST",
                    f"{location}.case_id",
                    f"program-ERROR planned case cannot be a fixture case: {case_id}",
                )
            )
        else:
            realized_planned_case_ids.add(str(case_id))
            if planned_case.get("expected_business_status") != status:
                issues.append(
                    _issue(
                        "PLANNED_CASE_STATUS_MISMATCH",
                        f"{location}.expected_business_status",
                        "fixture status differs from its planned-case authority; "
                        f"expected={planned_case.get('expected_business_status')}; "
                        f"actual={status}",
                    )
                )
            planned_requirements = {
                item
                for item in planned_case.get("covers_requirement_ids", [])
                if isinstance(item, str)
            }
            if case_requirements != planned_requirements:
                issues.append(
                    _issue(
                        "PLANNED_CASE_REQUIREMENT_SET_MISMATCH",
                        f"{location}.requirement_ids",
                        "fixture requirements differ from its planned-case authority; "
                        f"expected={sorted(planned_requirements)}; "
                        f"actual={sorted(case_requirements)}",
                    )
                )

        if case.get("release_id") != release_id or case.get("release_id") not in releases:
            issues.append(
                _issue(
                    "CASE_RELEASE_REFERENCE_MISMATCH",
                    f"{location}.release_id",
                    "case release must resolve to the top-level release",
                )
            )
        if case.get("profile_id") != profile_id:
            issues.append(
                _issue(
                    "CASE_PROFILE_REFERENCE_MISMATCH",
                    f"{location}.profile_id",
                    "case profile must equal the top-level profile",
                )
            )
        if case.get("shape_artifact_assertion_id") != shape_assertion_id:
            issues.append(
                _issue(
                    "CASE_SHAPE_REFERENCE_MISMATCH",
                    f"{location}.shape_artifact_assertion_id",
                    "case shape assertion must resolve to shape_artifact",
                )
            )

        for requirement_index, requirement_id in enumerate(
            case.get("requirement_ids", [])
        ):
            requirement_location = f"{location}.requirement_ids[{requirement_index}]"
            requirement = requirements.get(requirement_id)
            if requirement is None:
                issues.append(
                    _issue(
                        "DANGLING_REQUIREMENT_REFERENCE",
                        requirement_location,
                        f"unknown requirement ID: {requirement_id}",
                    )
                )
            elif status not in requirement.get("expected_business_statuses", []):
                issues.append(
                    _issue(
                        "REQUIREMENT_STATUS_MISMATCH",
                        requirement_location,
                        f"{requirement_id} does not permit business status {status}",
                    )
                )

        declared_decisions = {
            item for item in case.get("decision_ids", []) if isinstance(item, str)
        }
        unknown_decisions = sorted(declared_decisions - set(decision_id_to_path))
        for decision_id in unknown_decisions:
            issues.append(
                _issue(
                    "DANGLING_DECISION_REFERENCE",
                    f"{location}.decision_ids",
                    f"unknown decision ID: {decision_id}",
                )
            )
        expected_decisions: set[str] = set()
        unresolved_decision_paths: set[str] = set()
        for requirement_id in case_requirements:
            requirement = requirements.get(requirement_id)
            if not isinstance(requirement, dict):
                continue
            for path_value in requirement.get("decision_refs", []):
                decision_id = decision_path_to_id.get(path_value)
                if decision_id is None:
                    unresolved_decision_paths.add(str(path_value))
                else:
                    expected_decisions.add(decision_id)
        if unresolved_decision_paths:
            issues.append(
                _issue(
                    "REQUIREMENT_DECISION_CATALOG_GAP",
                    f"{location}.decision_ids",
                    "requirement decision paths are absent from decision_catalog: "
                    + ", ".join(sorted(unresolved_decision_paths)),
                )
            )
        if declared_decisions != expected_decisions:
            issues.append(
                _issue(
                    "CASE_DECISION_SET_MISMATCH",
                    f"{location}.decision_ids",
                    "case decisions must equal the union required by its requirements; "
                    f"expected={sorted(expected_decisions)}; actual={sorted(declared_decisions)}",
                )
            )

        fixture = case.get("fixture")
        if isinstance(fixture, dict):
            fixture_path = fixture.get("path")
            fixture_hash = fixture.get("sha256")
            if isinstance(fixture_path, str) and isinstance(fixture_hash, str):
                fixture_path_hashes.setdefault(fixture_path, set()).add(fixture_hash)
            _verify_file_binding(
                root,
                fixture_path,
                fixture_hash,
                f"{location}.fixture",
                issues,
                role="fixture",
                verify_hash=verify_fixture_hashes,
            )
            expected_directory = _STATUS_DIRECTORIES.get(str(status))
            if expected_directory is not None and isinstance(fixture_path, str):
                prefix = (
                    "C_Semantic_Treehouse/fixtures/v0.4/"
                    f"{expected_directory}/"
                )
                if not fixture_path.startswith(prefix):
                    issues.append(
                        _issue(
                            "FIXTURE_STATUS_PATH_MISMATCH",
                            f"{location}.fixture.path",
                            f"{status} fixture must be under {prefix}",
                        )
                    )
            fixture_format = fixture.get("format")
            if isinstance(fixture_path, str):
                suffix = Path(fixture_path).suffix.lower()
                if fixture_format == "json-ld" and suffix not in {".json", ".jsonld"}:
                    issues.append(
                        _issue(
                            "FIXTURE_FORMAT_PATH_MISMATCH",
                            f"{location}.fixture.format",
                            "json-ld fixture must use .json or .jsonld",
                        )
                    )
                if fixture_format == "turtle" and suffix != ".ttl":
                    issues.append(
                        _issue(
                            "FIXTURE_FORMAT_PATH_MISMATCH",
                            f"{location}.fixture.format",
                            "turtle fixture must use .ttl",
                        )
                    )

        oracle = case.get("oracle")
        if not isinstance(oracle, dict):
            continue
        if status == "UNTESTABLE":
            failure_stage = oracle.get("failure_stage")
            reason_code = oracle.get("reason_code")
            allowed = FAILURE_REASON_BY_STAGE.get(str(failure_stage), frozenset())
            if reason_code not in allowed:
                issues.append(
                    _issue(
                        "FAILURE_STAGE_REASON_MISMATCH",
                        f"{location}.oracle",
                        f"reason {reason_code} is not controlled for stage {failure_stage}",
                    )
                )
            fixture_format = (
                fixture.get("format") if isinstance(fixture, dict) else None
            )
            if reason_code in {
                "MALFORMED_JSON",
                "JSONLD_EXPANSION_ERROR",
                "OFFLINE_CONTEXT_UNAVAILABLE",
            } and fixture_format != "json-ld":
                issues.append(
                    _issue(
                        "FAILURE_REASON_FORMAT_MISMATCH",
                        f"{location}.fixture.format",
                        f"{reason_code} requires json-ld input",
                    )
                )
            if reason_code == "MALFORMED_RDF" and fixture_format != "turtle":
                issues.append(
                    _issue(
                        "FAILURE_REASON_FORMAT_MISMATCH",
                        f"{location}.fixture.format",
                        "MALFORMED_RDF requires turtle input",
                    )
                )
            continue

        expected_results = oracle.get("expected_results", [])
        if not isinstance(expected_results, list):
            continue
        case_signatures: list[tuple[Any, ...]] = []
        aggregate_minimum = 0
        aggregate_maximum = 0
        aggregate_complete = True
        for result_index, result in enumerate(expected_results):
            if not isinstance(result, dict):
                aggregate_complete = False
                continue
            result_location = f"{location}.oracle.expected_results[{result_index}]"
            result_assertion_ids.append(result.get("assertion_id"))
            issues.extend(
                _result_reference_issues(
                    result,
                    result_location,
                    case_requirements,
                    requirements,
                )
            )
            bounds = _count_bounds(result.get("count"))
            if bounds is None:
                aggregate_complete = False
            else:
                minimum, maximum = bounds
                if minimum > maximum:
                    issues.append(
                        _issue(
                            "INVALID_COUNT_BOUNDS",
                            f"{result_location}.count",
                            f"minimum {minimum} exceeds maximum {maximum}",
                        )
                    )
                aggregate_minimum += minimum
                aggregate_maximum += maximum
            signature = (
                result.get("requirement_id"),
                result.get("source_shape"),
                result.get("source_constraint_component"),
                result.get("result_path"),
                result.get("severity"),
                json.dumps(
                    result.get("message"),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                json.dumps(
                    result.get("focus_node"),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                json.dumps(
                    result.get("value"),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )
            case_signatures.append(signature)
        result_signatures[str(case_id)] = case_signatures
        for duplicate in _duplicates(case_signatures):
            issues.append(
                _issue(
                    "DUPLICATE_RESULT_ASSERTION",
                    f"{location}.oracle.expected_results",
                    "two expected result assertions have the same semantic matcher",
                )
            )
        overall_bounds = _count_bounds(oracle.get("result_count"))
        if overall_bounds is not None:
            overall_minimum, overall_maximum = overall_bounds
            if overall_minimum > overall_maximum:
                issues.append(
                    _issue(
                        "INVALID_COUNT_BOUNDS",
                        f"{location}.oracle.result_count",
                        f"minimum {overall_minimum} exceeds maximum {overall_maximum}",
                    )
                )
            if aggregate_complete and (
                aggregate_minimum > overall_maximum
                or aggregate_maximum < overall_minimum
            ):
                issues.append(
                    _issue(
                        "RESULT_COUNT_CONTRADICTION",
                        f"{location}.oracle.result_count",
                        "overall result count cannot contain the expected-result counts",
                    )
                )

    for path_value, hashes in sorted(fixture_path_hashes.items()):
        if len(hashes) > 1:
            issues.append(
                _issue(
                    "SAME_FIXTURE_PATH_HASH_CONFLICT",
                    "$.cases[*].fixture",
                    f"one fixture path has multiple hashes: {path_value}",
                )
            )
    for duplicate in _duplicates(result_assertion_ids):
        issues.append(
            _issue(
                "DUPLICATE_RESULT_ASSERTION_ID",
                "$.cases[*].oracle.expected_results",
                f"duplicate result assertion ID: {duplicate}",
            )
        )

    missing_coverage = sorted(set(requirements) - covered_requirements)
    if missing_coverage:
        issues.append(
            _issue(
                "REQUIREMENT_REVERSE_COVERAGE",
                "$.cases[*].requirement_ids",
                "requirements have no realized case: " + ", ".join(missing_coverage),
            )
        )
    missing_planned_cases = sorted(
        business_planned_case_ids - realized_planned_case_ids
    )
    if missing_planned_cases:
        issues.append(
            _issue(
                "PLANNED_CASE_REVERSE_COVERAGE",
                "$.cases[*].case_id",
                "business-status planned cases have no realized fixture: "
                + ", ".join(missing_planned_cases),
            )
        )
    return _sorted_issues(issues)


def validate_v04_manifest_document(
    document: Any,
    schema: Any,
    root: Path,
    *,
    release_manifest: dict[str, Any] | None = None,
    requirements_manifest: dict[str, Any] | None = None,
    verify_fixture_hashes: bool = True,
) -> tuple[ManifestIssue, ...]:
    """Run schema validation followed by semantic validation on one document."""

    schema_errors = _schema_issues(schema, document)
    if schema_errors:
        return _sorted_issues(schema_errors)
    if not isinstance(document, dict):
        return (_issue("MANIFEST_ROOT", "$", "manifest root must be an object"),)
    return semantic_validate_v04_manifest(
        document,
        root,
        release_manifest=release_manifest,
        requirements_manifest=requirements_manifest,
        verify_fixture_hashes=verify_fixture_hashes,
    )


def load_and_validate_v04_manifest(
    root: Path,
    *,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
    verify_fixture_hashes: bool = True,
) -> V04ManifestValidationResult:
    """Load and fail-closed validate the canonical or a temporary manifest."""

    root = root.resolve()
    manifest_path = manifest_path or (root / MANIFEST_RELPATH)
    schema_path = schema_path or (root / SCHEMA_RELPATH)
    issues: list[ManifestIssue] = []
    manifest: dict[str, Any] | None = None
    schema: Any = None

    if not schema_path.is_file():
        issues.append(_issue("MISSING_SCHEMA", "$schema", "v0.4 schema is missing"))
    else:
        try:
            schema = _load_json(schema_path)
        except _DuplicateKey as exc:
            issues.append(_issue("DUPLICATE_JSON_KEY", "$schema", str(exc)))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(_issue("SCHEMA_PARSE", "$schema", str(exc)))

    if not manifest_path.is_file():
        issues.append(_issue("MISSING_MANIFEST", "$", "v0.4 manifest is missing"))
    else:
        try:
            value = _load_json(manifest_path)
        except _DuplicateKey as exc:
            issues.append(_issue("DUPLICATE_JSON_KEY", "$", str(exc)))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(_issue("MANIFEST_PARSE", "$", str(exc)))
        else:
            if not isinstance(value, dict):
                issues.append(
                    _issue("MANIFEST_ROOT", "$", "manifest root must be an object")
                )
            else:
                manifest = value

    release_path = root / RELEASE_MANIFEST_RELPATH
    requirements_path = root / REQUIREMENTS_MANIFEST_RELPATH
    release_manifest: dict[str, Any] | None = None
    requirements_manifest: dict[str, Any] | None = None
    for role, path, code in (
        ("release", release_path, "RELEASE_MANIFEST_UNAVAILABLE"),
        ("requirements", requirements_path, "REQUIREMENTS_MANIFEST_UNAVAILABLE"),
    ):
        try:
            value = _load_json(path)
        except _DuplicateKey as exc:
            issues.append(_issue("DUPLICATE_JSON_KEY", str(path), str(exc)))
            continue
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(
                _issue(
                    code,
                    str(path),
                    f"{exc.__class__.__name__}: cannot load {role} authority",
                )
            )
            continue
        if not isinstance(value, dict):
            issues.append(_issue(code, str(path), f"{role} authority must be an object"))
        elif role == "release":
            release_manifest = value
        else:
            requirements_manifest = value

    if schema is not None and manifest is not None and not issues:
        issues.extend(
            validate_v04_manifest_document(
                manifest,
                schema,
                root,
                release_manifest=release_manifest,
                requirements_manifest=requirements_manifest,
                verify_fixture_hashes=verify_fixture_hashes,
            )
        )
    elif schema is not None and manifest is not None:
        # Schema errors remain useful even when an authority file is unavailable.
        issues.extend(_schema_issues(schema, manifest))

    return V04ManifestValidationResult(
        manifest_path=manifest_path,
        schema_path=schema_path,
        manifest=manifest,
        manifest_sha256=(sha256_file(manifest_path) if manifest_path.is_file() else None),
        schema_sha256=(sha256_file(schema_path) if schema_path.is_file() else None),
        release_manifest_sha256=(
            sha256_file(release_path) if release_path.is_file() else None
        ),
        requirements_manifest_sha256=(
            sha256_file(requirements_path) if requirements_path.is_file() else None
        ),
        issues=_sorted_issues(issues),
    )


# Descriptive alias used by callers that name the artifact rather than the phase.
load_and_validate_v04_test_cases = load_and_validate_v04_manifest


__all__ = [
    "FAILURE_REASON_BY_STAGE",
    "MANIFEST_RELPATH",
    "SCHEMA_RELPATH",
    "ManifestIssue",
    "V04ManifestValidationResult",
    "load_and_validate_v04_manifest",
    "load_and_validate_v04_test_cases",
    "semantic_validate_v04_manifest",
    "validate_v04_manifest_document",
]
