"""Schema and cross-record validation for the Phase 03 requirements registry."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from dssc_validation.hashing import sha256_file


MANIFEST_RELPATH = "C_Semantic_Treehouse/manifests/v0.4-requirements.json"
SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/manifests/schemas/v0.4-requirements.schema.json"
)

_REQUIREMENT_ID = re.compile(r"^D04-R\d{3}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[/\\]")
_ADR_STATUS = re.compile(
    r"^\s*-\s*(?:status|状态)\s*[:：]\s*`?([A-Z_]+)`?\s*$", re.IGNORECASE
)
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_APPROVAL_HEADING = "## 组级人工批准记录"
_APPROVAL_COLUMNS = ("审批角色与可审计身份", "日期", "批准范围", "结论", "证据引用")
_REQUIRED_APPROVAL_ROLES = (
    "项目维护方/当前用户",
    "DSSC Toolbox C 组",
    "DSSC Toolbox D 组",
)
_EXPECTED_REQUIREMENT_IDS = tuple(f"D04-R{number:03d}" for number in range(1, 18))
_EXPECTED_SHAPE_REQUIREMENTS = {
    "ex:DatasetCardinalityShape": "D04-R001",
    "ex:BuildingEnergyDatasetShape": "D04-R002",
    "ex:DatasetIdShape": "D04-R003",
    "ex:TitleShape": "D04-R004",
    "ex:ProviderNameShape": "D04-R005",
    "ex:SpatialShape": "D04-R006",
    "ex:FrequencyShape": "D04-R007",
    "ex:UnitShape": "D04-R008",
    "ex:FormatShape": "D04-R009",
    "ex:EndpointUrlShape": "D04-R010",
    "ex:TemporalStartShape": "D04-R011",
    "ex:TemporalEndShape": "D04-R012",
    "ex:TemporalOrderShape": "D04-R013",
    "ex:DescriptionShape": "D04-R014",
    "ex:LicenseShape": "D04-R015",
    "ex:DatasetClosedShape": "D04-R016",
}


def requirements_manifest_path(root: Path) -> Path:
    return root / MANIFEST_RELPATH


def requirements_schema_path(root: Path) -> Path:
    return root / SCHEMA_RELPATH


def _location(parts: tuple[Any, ...] | list[Any]) -> str:
    if not parts:
        return "$"
    return "$" + "".join(
        f"[{part}]" if isinstance(part, int) else f".{part}" for part in parts
    )


def _issue(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def _sorted_issues(issues: list[dict[str, str]]) -> tuple[dict[str, str], ...]:
    unique = {
        (item["code"], item["location"], item["message"]): item for item in issues
    }
    return tuple(unique[key] for key in sorted(unique))


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _safe_repo_path(root: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, "repository path must be a non-empty string"
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


def _duplicate_values(values: list[Any]) -> list[Any]:
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


def _schema_issues(schema: Any, document: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(schema, dict):
        return [_issue("SCHEMA_ROOT", "$schema", "schema root must be an object")]
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        issues.append(
            _issue(
                "SCHEMA_INVALID",
                _location(tuple(exc.absolute_schema_path)),
                exc.message,
            )
        )
        return issues
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(
        validator.iter_errors(document),
        key=lambda item: (tuple(str(part) for part in item.absolute_path), item.message),
    ):
        issues.append(
            _issue(
                "SCHEMA_VALIDATION",
                _location(tuple(error.absolute_path)),
                error.message,
            )
        )
    return issues


def _verify_bound_file(
    root: Path,
    path_value: Any,
    sha_value: Any,
    location: str,
    issues: list[dict[str, str]],
    *,
    path_field: str = "path",
) -> Path | None:
    path, path_issue = _safe_repo_path(root, path_value)
    if path_issue:
        issues.append(_issue("UNSAFE_PATH", f"{location}.{path_field}", path_issue))
        return None
    if not isinstance(sha_value, str) or _SHA256.fullmatch(sha_value) is None:
        issues.append(
            _issue("INVALID_SHA256", f"{location}.sha256", "expected lowercase SHA-256")
        )
        return path
    if path is None or not path.is_file():
        issues.append(
            _issue(
                "MISSING_SOURCE",
                f"{location}.{path_field}",
                f"source file is missing: {path_value}",
            )
        )
        return path
    actual = sha256_file(path)
    if actual != sha_value:
        issues.append(
            _issue(
                "SOURCE_HASH_MISMATCH",
                f"{location}.sha256",
                f"expected {sha_value}; actual {actual}",
            )
        )
    return path


def _markdown_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [item.strip() for item in stripped[1:-1].split("|")]


def _valid_iso_date(value: str) -> bool:
    if _ISO_DATE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _decision_acceptance_issues(
    text: str,
    location: str,
    decision_id: str,
) -> list[dict[str, str]]:
    """Validate the top-level ADR status and the three human approval rows."""
    issues: list[dict[str, str]] = []
    lines = text.splitlines()
    metadata_end = next(
        (index for index, line in enumerate(lines) if line.startswith("## ")),
        len(lines),
    )
    status_values = [
        match.group(1).upper()
        for line in lines[:metadata_end]
        for match in [_ADR_STATUS.fullmatch(line)]
        if match is not None
    ]
    if status_values != ["ACCEPTED"]:
        issues.append(
            _issue(
                "DECISION_NOT_ACCEPTED",
                location,
                (
                    f"blocking decision must declare exactly one top-level "
                    f"ACCEPTED status: {decision_id}"
                ),
            )
        )

    try:
        approval_start = lines.index(_APPROVAL_HEADING) + 1
    except ValueError:
        approval_start = len(lines)
        issues.append(
            _issue(
                "DECISION_APPROVAL_SECTION_MISSING",
                location,
                f"blocking decision lacks the group approval section: {decision_id}",
            )
        )

    approval_lines: list[list[str]] = []
    for line in lines[approval_start:]:
        if line.startswith("## "):
            break
        cells = _markdown_cells(line)
        if cells is not None:
            approval_lines.append(cells)

    table_is_structured = (
        len(approval_lines) >= 2
        and tuple(approval_lines[0]) == _APPROVAL_COLUMNS
        and len(approval_lines[1]) == len(_APPROVAL_COLUMNS)
        and all(re.fullmatch(r":?-{3,}:?", cell) for cell in approval_lines[1])
    )
    if not table_is_structured:
        issues.append(
            _issue(
                "DECISION_APPROVAL_TABLE_INVALID",
                location,
                f"blocking decision has an invalid approval table: {decision_id}",
            )
        )
    data_rows = approval_lines[2:] if table_is_structured else approval_lines

    records: dict[str, list[list[str]]] = {
        role: [] for role in _REQUIRED_APPROVAL_ROLES
    }
    for cells in data_rows:
        if len(cells) == 5 and cells[0] in records:
            records[cells[0]].append(cells)
        elif cells:
            issues.append(
                _issue(
                    "DECISION_APPROVAL_ROLE_UNKNOWN",
                    location,
                    (
                        "blocking decision approval table contains an unapproved "
                        f"role or malformed row: {decision_id}"
                    ),
                )
            )

    for role in _REQUIRED_APPROVAL_ROLES:
        role_records = records[role]
        if len(role_records) != 1:
            issues.append(
                _issue(
                    "DECISION_APPROVAL_ROLE_COUNT",
                    location,
                    (
                        f"blocking decision must contain exactly one approval row "
                        f"for {role}: {decision_id}"
                    ),
                )
            )
            continue
        _, approval_date, scope, conclusion, evidence = role_records[0]
        invalid_fields: list[str] = []
        if not _valid_iso_date(approval_date):
            invalid_fields.append("date")
        if not scope:
            invalid_fields.append("scope")
        if conclusion not in {"批准", "APPROVED", "ACCEPTED"}:
            invalid_fields.append("conclusion")
        if not evidence:
            invalid_fields.append("evidence")
        if invalid_fields:
            issues.append(
                _issue(
                    "DECISION_APPROVAL_RECORD_INVALID",
                    location,
                    (
                        f"approval row for {role} has invalid fields "
                        f"{invalid_fields}: {decision_id}"
                    ),
                )
            )
    return issues


def _semantic_issues(
    document: dict[str, Any],
    root: Path,
    *,
    require_accepted_decisions: bool,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    profile = document.get("profile")
    if isinstance(profile, dict):
        normative = profile.get("normative_source")
        if isinstance(normative, dict):
            _verify_bound_file(
                root,
                normative.get("path"),
                normative.get("sha256"),
                "$.profile.normative_source",
                issues,
            )
        for index, source in enumerate(profile.get("explanatory_sources", [])):
            if isinstance(source, dict):
                _verify_bound_file(
                    root,
                    source.get("path"),
                    source.get("sha256"),
                    f"$.profile.explanatory_sources[{index}]",
                    issues,
                )
        header = profile.get("status_header_source")
        if isinstance(header, dict):
            _verify_bound_file(
                root,
                header.get("path"),
                header.get("sha256"),
                "$.profile.status_header_source",
                issues,
            )

    decision_catalog = document.get("decision_catalog", [])
    decision_ids = [
        item.get("id") for item in decision_catalog if isinstance(item, dict)
    ]
    decision_paths = [
        item.get("path") for item in decision_catalog if isinstance(item, dict)
    ]
    for duplicate in _duplicate_values(decision_ids):
        issues.append(
            _issue("DUPLICATE_DECISION_ID", "$.decision_catalog", f"duplicate decision ID: {duplicate}")
        )
    for duplicate in _duplicate_values(decision_paths):
        issues.append(
            _issue(
                "DUPLICATE_DECISION_PATH",
                "$.decision_catalog",
                f"duplicate decision path: {duplicate}",
            )
        )
    decisions: dict[str, dict[str, Any]] = {}
    decisions_by_path: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(decision_catalog):
        if not isinstance(item, dict):
            continue
        decision_id = item.get("id")
        if not isinstance(decision_id, str) or decision_id in decisions:
            continue
        decisions[decision_id] = item
        if isinstance(item.get("path"), str):
            decisions_by_path[item["path"]] = item
        path, path_issue = _safe_repo_path(root, item.get("path"))
        location = f"$.decision_catalog[{index}].path"
        if path_issue:
            issues.append(_issue("UNSAFE_PATH", location, path_issue))
        elif path is None or not path.is_file():
            issues.append(
                _issue("DANGLING_DECISION", location, f"decision file is missing: {item.get('path')}")
            )
        elif require_accepted_decisions:
            text = path.read_text(encoding="utf-8")
            issues.extend(
                _decision_acceptance_issues(
                    text,
                    location,
                    str(decision_id),
                )
            )

    issue_catalog = document.get("issue_catalog", [])
    issue_ids = [item.get("id") for item in issue_catalog if isinstance(item, dict)]
    for duplicate in _duplicate_values(issue_ids):
        issues.append(
            _issue("DUPLICATE_ISSUE_ID", "$.issue_catalog", f"duplicate issue ID: {duplicate}")
        )
    known_issue_ids = {item for item in issue_ids if isinstance(item, str)}

    requirements = document.get("requirements", [])
    requirement_ids = [
        item.get("id") for item in requirements if isinstance(item, dict)
    ]
    for duplicate in _duplicate_values(requirement_ids):
        issues.append(
            _issue("DUPLICATE_REQUIREMENT_ID", "$.requirements", f"duplicate requirement ID: {duplicate}")
        )
    requirement_by_id = {
        item["id"]: item
        for item in requirements
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and requirement_ids.count(item["id"]) == 1
    }
    if tuple(requirement_ids) != _EXPECTED_REQUIREMENT_IDS:
        issues.append(
            _issue(
                "REQUIREMENT_ID_SET_OR_ORDER",
                "$.requirements",
                "canonical requirement IDs/order must be D04-R001 through D04-R017",
            )
        )
    for index, requirement_id in enumerate(requirement_ids):
        if isinstance(requirement_id, str) and _REQUIREMENT_ID.fullmatch(requirement_id) is None:
            issues.append(
                _issue(
                    "INVALID_REQUIREMENT_ID",
                    f"$.requirements[{index}].id",
                    f"invalid requirement ID: {requirement_id}",
                )
            )

    planned_cases = document.get("planned_cases", [])
    case_ids = [item.get("id") for item in planned_cases if isinstance(item, dict)]
    for duplicate in _duplicate_values(case_ids):
        issues.append(
            _issue("DUPLICATE_PLANNED_CASE_ID", "$.planned_cases", f"duplicate planned case ID: {duplicate}")
        )
    case_by_id = {
        item["id"]: item
        for item in planned_cases
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and case_ids.count(item["id"]) == 1
    }

    obligation_owner: dict[str, str] = {}
    shape_owner: dict[str, str] = {}
    constraint_owner: dict[tuple[str, str, str], str] = {}
    obligation_case_links: dict[str, set[str]] = {
        requirement_id: set() for requirement_id in requirement_by_id
    }

    for requirement_index, requirement in enumerate(requirements):
        if not isinstance(requirement, dict):
            continue
        requirement_id = requirement.get("id")
        if not isinstance(requirement_id, str):
            continue
        requirement_location = f"$.requirements[{requirement_index}]"

        for decision_index, decision_path in enumerate(requirement.get("decision_refs", [])):
            if decision_path not in decisions_by_path:
                issues.append(
                    _issue(
                        "DANGLING_DECISION_REFERENCE",
                        f"{requirement_location}.decision_refs[{decision_index}]",
                        f"decision path is absent from decision_catalog: {decision_path}",
                    )
                )
        for issue_index, issue_id in enumerate(requirement.get("issue_refs", [])):
            if issue_id not in known_issue_ids:
                issues.append(
                    _issue(
                        "DANGLING_ISSUE_REFERENCE",
                        f"{requirement_location}.issue_refs[{issue_index}]",
                        f"unknown issue ID: {issue_id}",
                    )
                )

        sources = requirement.get("sources", [])
        source_components: set[str] = set()
        if not sources:
            issues.append(
                _issue("MISSING_SOURCE_LOCATOR", f"{requirement_location}.sources", "requirement has no source locator")
            )
        for source_index, source in enumerate(sources):
            if not isinstance(source, dict) or not isinstance(source.get("locator"), dict):
                continue
            locator = source["locator"]
            locator_location = f"{requirement_location}.sources[{source_index}].locator"
            _verify_bound_file(
                root,
                locator.get("document"),
                locator.get("sha256"),
                locator_location,
                issues,
                path_field="document",
            )
            if locator.get("kind") == "SHACL_SHAPE":
                source_components.update(
                    item
                    for item in locator.get("constraint_components", [])
                    if isinstance(item, str)
                )
                shape = locator.get("shape")
                if isinstance(shape, str):
                    expected_requirement = _EXPECTED_SHAPE_REQUIREMENTS.get(shape)
                    if expected_requirement is not None and expected_requirement != requirement_id:
                        issues.append(
                            _issue(
                                "UNSTABLE_SHAPE_REQUIREMENT_ID",
                                f"{locator_location}.shape",
                                f"{shape} must map to {expected_requirement}, not {requirement_id}",
                            )
                        )
                    previous = shape_owner.setdefault(shape, requirement_id)
                    if previous != requirement_id:
                        issues.append(
                            _issue(
                                "CONFLICTING_SOURCE_SHAPE_MAPPING",
                                f"{locator_location}.shape",
                                f"source shape maps to both {previous} and {requirement_id}: {shape}",
                            )
                        )
                    path_value = locator.get("path")
                    path_key = "<none>" if path_value is None else str(path_value)
                    for component in locator.get("constraint_components", []):
                        key = (shape, path_key, str(component))
                        previous_component = constraint_owner.setdefault(
                            key, requirement_id
                        )
                        if previous_component != requirement_id:
                            issues.append(
                                _issue(
                                    "CONFLICTING_SOURCE_CONSTRAINT_MAPPING",
                                    f"{locator_location}.constraint_components",
                                    f"source constraint maps to both {previous_component} and {requirement_id}: {key}",
                                )
                            )

        implementation = requirement.get("implementation")
        if isinstance(implementation, dict):
            for collection_name in ("artifact_refs", "fixture_refs", "evidence_refs"):
                for reference_index, reference in enumerate(
                    implementation.get(collection_name, [])
                ):
                    if not isinstance(reference, dict):
                        continue
                    reference_path = reference.get("path")
                    if reference_path is None:
                        continue
                    path, path_issue = _safe_repo_path(root, reference_path)
                    location = (
                        f"{requirement_location}.implementation.{collection_name}"
                        f"[{reference_index}].path"
                    )
                    if path_issue:
                        issues.append(_issue("UNSAFE_PATH", location, path_issue))
                    elif reference.get("status") == "IMPLEMENTED" and (
                        path is None or not path.is_file()
                    ):
                        issues.append(
                            _issue(
                                "DANGLING_IMPLEMENTED_REFERENCE",
                                location,
                                f"implemented artifact is missing: {reference_path}",
                            )
                        )

        obligations = requirement.get("test_obligations", [])
        obligation_components: set[str] = set()
        if not obligations:
            issues.append(
                _issue("EMPTY_TEST_OBLIGATIONS", f"{requirement_location}.test_obligations", "requirement has no test obligations")
            )
        for obligation_index, obligation in enumerate(obligations):
            if not isinstance(obligation, dict):
                continue
            obligation_id = obligation.get("id")
            obligation_location = f"{requirement_location}.test_obligations[{obligation_index}]"
            obligation_components.update(
                item
                for item in obligation.get("covers_components", [])
                if isinstance(item, str)
            )
            unknown_components = set(obligation.get("covers_components", [])) - source_components
            if unknown_components and requirement.get("rule_kind") == "NORMATIVE_SHACL":
                issues.append(
                    _issue(
                        "OBLIGATION_COMPONENT_NOT_IN_SOURCE",
                        f"{obligation_location}.covers_components",
                        f"obligation components are absent from source: {sorted(unknown_components)}",
                    )
                )
            if isinstance(obligation_id, str):
                previous = obligation_owner.setdefault(obligation_id, requirement_id)
                if previous != requirement_id or sum(
                    1
                    for item in obligations
                    if isinstance(item, dict) and item.get("id") == obligation_id
                ) > 1:
                    issues.append(
                        _issue(
                            "DUPLICATE_TEST_OBLIGATION_ID",
                            f"{obligation_location}.id",
                            f"duplicate test obligation ID: {obligation_id}",
                        )
                    )
            for case_index, case_id in enumerate(obligation.get("planned_case_ids", [])):
                if case_id not in case_by_id:
                    issues.append(
                        _issue(
                            "DANGLING_PLANNED_CASE_REFERENCE",
                            f"{obligation_location}.planned_case_ids[{case_index}]",
                            f"unknown planned case ID: {case_id}",
                        )
                    )
                    continue
                obligation_case_links.setdefault(requirement_id, set()).add(case_id)
                if requirement_id not in case_by_id[case_id].get("covers_requirement_ids", []):
                    issues.append(
                        _issue(
                            "PLANNED_CASE_REVERSE_REFERENCE",
                            f"{obligation_location}.planned_case_ids[{case_index}]",
                            f"case {case_id} does not cover {requirement_id}",
                        )
                    )
        missing_component_obligations = source_components - obligation_components
        if missing_component_obligations:
            issues.append(
                _issue(
                    "SOURCE_COMPONENT_WITHOUT_TEST_OBLIGATION",
                    f"{requirement_location}.test_obligations",
                    f"source components lack test obligations: {sorted(missing_component_obligations)}",
                )
            )

    for case_index, planned_case in enumerate(planned_cases):
        if not isinstance(planned_case, dict):
            continue
        case_id = planned_case.get("id")
        covered_component_union: set[str] = set()
        for covered_requirement_id in planned_case.get("covers_requirement_ids", []):
            covered_requirement = requirement_by_id.get(covered_requirement_id)
            if not isinstance(covered_requirement, dict):
                continue
            for source in covered_requirement.get("sources", []):
                locator = source.get("locator") if isinstance(source, dict) else None
                if isinstance(locator, dict):
                    covered_component_union.update(
                        item
                        for item in locator.get("constraint_components", [])
                        if isinstance(item, str)
                    )
        unknown_case_components = (
            set(planned_case.get("covers_components", [])) - covered_component_union
        )
        if unknown_case_components:
            issues.append(
                _issue(
                    "PLANNED_CASE_COMPONENT_NOT_IN_REQUIREMENT",
                    f"$.planned_cases[{case_index}].covers_components",
                    f"case components are absent from covered requirements: {sorted(unknown_case_components)}",
                )
            )
        for reference_index, requirement_id in enumerate(
            planned_case.get("covers_requirement_ids", [])
        ):
            location = f"$.planned_cases[{case_index}].covers_requirement_ids[{reference_index}]"
            if requirement_id not in requirement_by_id:
                issues.append(
                    _issue(
                        "DANGLING_REQUIREMENT_REFERENCE",
                        location,
                        f"unknown requirement ID: {requirement_id}",
                    )
                )
            elif case_id not in obligation_case_links.get(requirement_id, set()):
                issues.append(
                    _issue(
                        "TEST_OBLIGATION_REVERSE_REFERENCE",
                        location,
                        f"no obligation in {requirement_id} references case {case_id}",
                    )
                )

    return issues


@dataclass(frozen=True)
class RequirementsValidationResult:
    manifest_path: Path
    schema_path: Path
    manifest: dict[str, Any] | None
    manifest_sha256: str | None
    schema_sha256: str | None
    issues: tuple[dict[str, str], ...]

    @property
    def ok(self) -> bool:
        return self.manifest is not None and not self.issues

    def deterministic_record(self) -> dict[str, Any]:
        requirements = self.manifest.get("requirements", []) if self.manifest else []
        planned_cases = self.manifest.get("planned_cases", []) if self.manifest else []
        obligations = [
            obligation
            for requirement in requirements
            if isinstance(requirement, dict)
            for obligation in requirement.get("test_obligations", [])
            if isinstance(obligation, dict)
        ]
        return {
            "manifest_path": MANIFEST_RELPATH,
            "manifest_sha256": self.manifest_sha256,
            "schema_path": SCHEMA_RELPATH,
            "schema_sha256": self.schema_sha256,
            "manifest_schema_version": (
                self.manifest.get("manifest_schema_version") if self.manifest else None
            ),
            "requirement_ids": [
                item.get("id") for item in requirements if isinstance(item, dict)
            ],
            "requirement_count": len(requirements),
            "planned_case_ids": [
                item.get("id") for item in planned_cases if isinstance(item, dict)
            ],
            "planned_case_count": len(planned_cases),
            "test_obligation_ids": [item.get("id") for item in obligations],
            "test_obligation_count": len(obligations),
            "issues": list(self.issues),
        }


def load_and_validate_requirements(
    root: Path,
    *,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
    require_accepted_decisions: bool = True,
) -> RequirementsValidationResult:
    """Validate schema, hashes, paths, IDs, and all cross-record references."""
    root = root.resolve()
    manifest_path = manifest_path or requirements_manifest_path(root)
    schema_path = schema_path or requirements_schema_path(root)
    issues: list[dict[str, str]] = []
    manifest: dict[str, Any] | None = None
    schema: Any = None

    if not schema_path.is_file():
        issues.append(_issue("MISSING_SCHEMA", "$schema", "requirements schema is missing"))
    else:
        try:
            schema = _load_json(schema_path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(_issue("SCHEMA_PARSE", "$schema", str(exc)))

    if not manifest_path.is_file():
        issues.append(_issue("MISSING_MANIFEST", "$", "requirements manifest is missing"))
    else:
        try:
            value = _load_json(manifest_path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(_issue("MANIFEST_PARSE", "$", str(exc)))
        else:
            if not isinstance(value, dict):
                issues.append(_issue("MANIFEST_ROOT", "$", "manifest root must be an object"))
            else:
                manifest = value

    if schema is not None and manifest is not None:
        schema_errors = _schema_issues(schema, manifest)
        issues.extend(schema_errors)
        if not schema_errors:
            issues.extend(
                _semantic_issues(
                    manifest,
                    root,
                    require_accepted_decisions=require_accepted_decisions,
                )
            )

    return RequirementsValidationResult(
        manifest_path=manifest_path,
        schema_path=schema_path,
        manifest=manifest,
        manifest_sha256=sha256_file(manifest_path) if manifest_path.is_file() else None,
        schema_sha256=sha256_file(schema_path) if schema_path.is_file() else None,
        issues=_sorted_issues(issues),
    )


__all__ = [
    "MANIFEST_RELPATH",
    "SCHEMA_RELPATH",
    "RequirementsValidationResult",
    "load_and_validate_requirements",
    "requirements_manifest_path",
    "requirements_schema_path",
]
