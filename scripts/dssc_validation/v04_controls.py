"""Deterministic in-memory negative controls for Phase 05 contracts.

This module mutates deep copies of the supplied canonical manifest and the
suite registry.  It never writes a manifest, fixture, registry, or evidence
file.  A control passes only when its mutation produces program ``ERROR`` and
the stable issue code declared by that control.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from dssc_validation.v04_manifest import (
    RELEASE_MANIFEST_RELPATH,
    REQUIREMENTS_MANIFEST_RELPATH,
    SCHEMA_RELPATH,
    semantic_validate_v04_manifest,
    validate_v04_manifest_document,
)


REGISTRY_RELPATH = "C_Semantic_Treehouse/manifests/validation-suites.json"
REGISTRY_SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json"
)
PROGRAM_ERROR_PLANNED_CASE_IDS = (
    "D04-PC067",
    "D04-PC068",
    "D04-PC069",
    "D04-PC070",
)

Document = dict[str, Any]
Mutator = Callable[[Document], None]


@dataclass(frozen=True)
class _ControlSpec:
    control_id: str
    domain: str
    validator: str
    expected_codes: tuple[str, ...]
    mutate: Mutator
    planned_case_ids: tuple[str, ...] = ()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _first_case(document: Document, status: str | None = None) -> Document:
    for case in document.get("cases", []):
        if isinstance(case, dict) and (
            status is None or case.get("expected_business_status") == status
        ):
            return case
    raise ValueError(f"canonical manifest has no {status or 'any'} case")


def _two_cases(document: Document, status: str | None = None) -> tuple[Document, Document]:
    cases = [
        case
        for case in document.get("cases", [])
        if isinstance(case, dict)
        and (status is None or case.get("expected_business_status") == status)
    ]
    if len(cases) < 2:
        raise ValueError(f"canonical manifest has fewer than two {status or 'any'} cases")
    return cases[0], cases[1]


def _suite(document: Document, suite_id: str) -> Document:
    for suite in document.get("suites", []):
        if isinstance(suite, dict) and suite.get("id") == suite_id:
            return suite
    raise ValueError(f"canonical registry has no suite {suite_id}")


def _implemented_suite_with_component(document: Document) -> Document:
    for suite in document.get("suites", []):
        if (
            isinstance(suite, dict)
            and suite.get("status") == "IMPLEMENTED"
            and isinstance(suite.get("components"), list)
            and suite["components"]
        ):
            return suite
    raise ValueError("canonical registry has no implemented component")


def _different_hash(value: str) -> str:
    candidate = "0" * 64
    return "1" * 64 if value == candidate else candidate


# Manifest schema mutations.
def _unknown_status(document: Document) -> None:
    _first_case(document)["expected_business_status"] = "UNKNOWN"


def _outside_path(document: Document) -> None:
    _first_case(document)["fixture"]["path"] = "../outside.jsonld"


def _missing_fixture_sha(document: Document) -> None:
    del _first_case(document)["fixture"]["sha256"]


def _missing_oracle(document: Document) -> None:
    del _first_case(document)["oracle"]


def _pass_report_field(document: Document) -> None:
    _first_case(document, "PASS")["oracle"]["expected_results"] = []


def _fail_missing_results(document: Document) -> None:
    del _first_case(document, "FAIL")["oracle"]["expected_results"]


def _inapplicable_missing_results(document: Document) -> None:
    del _first_case(document, "INAPPLICABLE")["oracle"]["expected_results"]


def _untestable_report_field(document: Document) -> None:
    _first_case(document, "UNTESTABLE")["oracle"]["result_count"] = {"exact": 0}


# Manifest semantic mutations.
def _contradictory_count(document: Document) -> None:
    _first_case(document, "FAIL")["oracle"]["result_count"] = {
        "minimum": 2,
        "maximum": 1,
    }


def _duplicate_case_id(document: Document) -> None:
    first, second = _two_cases(document)
    second["case_id"] = first["case_id"]


def _duplicate_fixture_id(document: Document) -> None:
    first, second = _two_cases(document)
    second["fixture"]["assertion_id"] = first["fixture"]["assertion_id"]


def _duplicate_artifact_assertion_id(document: Document) -> None:
    document["evidence_refs"]["meta_shacl"]["assertion_id"] = document[
        "shape_artifact"
    ]["assertion_id"]


def _dangling_requirement(document: Document) -> None:
    case = _first_case(document)
    case["requirement_ids"][0] = "D04-R999"


def _dangling_artifact(document: Document) -> None:
    document["shape_artifact"]["artifact_id"] = "missing-shape-artifact"


def _dangling_release(document: Document) -> None:
    document["release"]["id"] = "v9.9"
    for case in document.get("cases", []):
        if isinstance(case, dict):
            case["release_id"] = "v9.9"


def _dangling_profile(document: Document) -> None:
    document["profile"]["id"] = "missing-profile"
    for case in document.get("cases", []):
        if isinstance(case, dict):
            case["profile_id"] = "missing-profile"


def _dangling_decision(document: Document) -> None:
    _first_case(document)["decision_ids"] = ["ADR-999"]


def _same_path_different_hash(document: Document) -> None:
    first, second = _two_cases(document, "FAIL")
    second["fixture"]["path"] = first["fixture"]["path"]
    second["fixture"]["sha256"] = _different_hash(first["fixture"]["sha256"])


def _fixture_drift(document: Document) -> None:
    fixture = _first_case(document)["fixture"]
    fixture["sha256"] = _different_hash(fixture["sha256"])


def _failure_stage_reason_mismatch(document: Document) -> None:
    oracle = _first_case(document, "UNTESTABLE")["oracle"]
    oracle["failure_stage"] = "INPUT_PARSE"
    oracle["reason_code"] = "VALIDATOR_TIMEOUT"


def _remove_requirement_coverage(document: Document) -> None:
    target = "D04-R017"
    for case in document.get("cases", []):
        if isinstance(case, dict):
            case["requirement_ids"] = [
                item for item in case.get("requirement_ids", []) if item != target
            ]


def _dangling_planned_case(document: Document) -> None:
    _first_case(document)["case_id"] = "D04-PC999"


def _program_error_planned_case_in_manifest(document: Document) -> None:
    _first_case(document)["case_id"] = "D04-PC067"


def _planned_case_status_mismatch(document: Document) -> None:
    case = _first_case(document, "PASS")
    case["expected_business_status"] = "FAIL"


def _planned_case_requirements_mismatch(document: Document) -> None:
    case = next(
        case
        for case in document.get("cases", [])
        if isinstance(case, dict) and len(case.get("requirement_ids", [])) > 1
    )
    case["requirement_ids"] = case["requirement_ids"][1:]


def _planned_case_reverse_coverage(document: Document) -> None:
    target = _first_case(document)["case_id"]
    document["cases"] = [
        case
        for case in document.get("cases", [])
        if not isinstance(case, dict) or case.get("case_id") != target
    ]


# Suite-registry semantic mutations.
def _registry_duplicate_suite(document: Document) -> None:
    document["suites"][-1]["id"] = document["suites"][0]["id"]


def _registry_dangling_dependency(document: Document) -> None:
    document["suites"][0]["depends_on"] = ["missing-suite"]


def _registry_cycle(document: Document) -> None:
    _suite(document, "frozen")["depends_on"] = ["all"]


def _registry_zero_component(document: Document) -> None:
    _implemented_suite_with_component(document)["components"] = []


def _registry_unknown_entrypoint(document: Document) -> None:
    suite = _implemented_suite_with_component(document)
    suite["components"][0]["entrypoint"] = "unknown_entrypoint"


def _registry_duplicate_component(document: Document) -> None:
    suite = _implemented_suite_with_component(document)
    suite["components"].append(copy.deepcopy(suite["components"][0]))


def _registry_shell_payload(document: Document) -> None:
    suite = _implemented_suite_with_component(document)
    suite["components"][0]["command"] = "echo forbidden"


def _registry_all_incomplete(document: Document) -> None:
    _suite(document, "all")["depends_on"] = [
        "frozen",
        "environment",
        "baseline",
        "traceability",
        "v0.4-model",
    ]


def _manifest_control_specs() -> tuple[_ControlSpec, ...]:
    specs = (
        _ControlSpec(
            "manifest.schema.unknown_status",
            "manifest_schema",
            "manifest_schema",
            ("SCHEMA_VALIDATION",),
            _unknown_status,
            ("D04-PC068",),
        ),
        _ControlSpec(
            "manifest.schema.path_escape",
            "manifest_schema",
            "manifest_schema",
            ("SCHEMA_VALIDATION",),
            _outside_path,
        ),
        _ControlSpec(
            "manifest.schema.missing_fixture_sha",
            "manifest_schema",
            "manifest_schema",
            ("SCHEMA_VALIDATION",),
            _missing_fixture_sha,
        ),
        _ControlSpec(
            "manifest.schema.missing_oracle",
            "manifest_schema",
            "manifest_schema",
            ("SCHEMA_VALIDATION",),
            _missing_oracle,
        ),
        _ControlSpec(
            "manifest.schema.pass_report_field",
            "manifest_schema",
            "manifest_schema",
            ("SCHEMA_VALIDATION",),
            _pass_report_field,
        ),
        _ControlSpec(
            "manifest.schema.fail_missing_expected_results",
            "manifest_schema",
            "manifest_schema",
            ("SCHEMA_VALIDATION",),
            _fail_missing_results,
        ),
        _ControlSpec(
            "manifest.schema.inapplicable_missing_expected_results",
            "manifest_schema",
            "manifest_schema",
            ("SCHEMA_VALIDATION",),
            _inapplicable_missing_results,
        ),
        _ControlSpec(
            "manifest.schema.untestable_report_field",
            "manifest_schema",
            "manifest_schema",
            ("SCHEMA_VALIDATION",),
            _untestable_report_field,
        ),
        _ControlSpec(
            "manifest.semantic.contradictory_count",
            "manifest_semantic",
            "manifest_semantic",
            ("INVALID_COUNT_BOUNDS",),
            _contradictory_count,
        ),
        _ControlSpec(
            "manifest.semantic.duplicate_case_id",
            "manifest_semantic",
            "manifest_semantic",
            ("DUPLICATE_CASE_ID",),
            _duplicate_case_id,
        ),
        _ControlSpec(
            "manifest.semantic.duplicate_fixture_assertion_id",
            "manifest_semantic",
            "manifest_semantic",
            ("DUPLICATE_FIXTURE_ASSERTION_ID",),
            _duplicate_fixture_id,
        ),
        _ControlSpec(
            "manifest.semantic.duplicate_artifact_assertion_id",
            "manifest_semantic",
            "manifest_semantic",
            ("DUPLICATE_ARTIFACT_ASSERTION_ID",),
            _duplicate_artifact_assertion_id,
        ),
        _ControlSpec(
            "manifest.semantic.dangling_requirement",
            "manifest_semantic",
            "manifest_semantic",
            ("DANGLING_REQUIREMENT_REFERENCE",),
            _dangling_requirement,
        ),
        _ControlSpec(
            "manifest.semantic.dangling_artifact",
            "manifest_semantic",
            "manifest_semantic",
            ("DANGLING_SHAPE_ARTIFACT_REFERENCE",),
            _dangling_artifact,
        ),
        _ControlSpec(
            "manifest.semantic.dangling_release",
            "manifest_semantic",
            "manifest_semantic",
            ("DANGLING_RELEASE_REFERENCE",),
            _dangling_release,
        ),
        _ControlSpec(
            "manifest.semantic.dangling_profile",
            "manifest_semantic",
            "manifest_semantic",
            ("DANGLING_PROFILE_REFERENCE",),
            _dangling_profile,
        ),
        _ControlSpec(
            "manifest.semantic.dangling_decision",
            "manifest_semantic",
            "manifest_semantic",
            ("DANGLING_DECISION_REFERENCE",),
            _dangling_decision,
        ),
        _ControlSpec(
            "manifest.semantic.same_path_different_hash",
            "manifest_semantic",
            "manifest_semantic",
            ("SAME_FIXTURE_PATH_HASH_CONFLICT",),
            _same_path_different_hash,
        ),
        _ControlSpec(
            "manifest.semantic.fixture_hash_drift",
            "manifest_semantic",
            "manifest_semantic_hash",
            ("FIXTURE_HASH_MISMATCH",),
            _fixture_drift,
        ),
        _ControlSpec(
            "manifest.semantic.failure_stage_reason_mismatch",
            "manifest_semantic",
            "manifest_semantic",
            ("FAILURE_STAGE_REASON_MISMATCH",),
            _failure_stage_reason_mismatch,
        ),
        _ControlSpec(
            "manifest.semantic.reverse_requirement_coverage",
            "manifest_semantic",
            "manifest_semantic",
            ("REQUIREMENT_REVERSE_COVERAGE",),
            _remove_requirement_coverage,
        ),
        _ControlSpec(
            "manifest.semantic.dangling_planned_case",
            "manifest_semantic",
            "manifest_semantic",
            ("DANGLING_PLANNED_CASE_REFERENCE",),
            _dangling_planned_case,
        ),
        _ControlSpec(
            "manifest.semantic.program_error_case_in_fixture_manifest",
            "manifest_semantic",
            "manifest_semantic",
            ("PROGRAM_ERROR_PLANNED_CASE_IN_FIXTURE_MANIFEST",),
            _program_error_planned_case_in_manifest,
        ),
        _ControlSpec(
            "manifest.semantic.planned_case_status_mismatch",
            "manifest_semantic",
            "manifest_semantic",
            ("PLANNED_CASE_STATUS_MISMATCH",),
            _planned_case_status_mismatch,
        ),
        _ControlSpec(
            "manifest.semantic.planned_case_requirements_mismatch",
            "manifest_semantic",
            "manifest_semantic",
            ("PLANNED_CASE_REQUIREMENT_SET_MISMATCH",),
            _planned_case_requirements_mismatch,
        ),
        _ControlSpec(
            "manifest.semantic.planned_case_reverse_coverage",
            "manifest_semantic",
            "manifest_semantic",
            ("PLANNED_CASE_REVERSE_COVERAGE",),
            _planned_case_reverse_coverage,
        ),
    )
    return tuple(sorted(specs, key=lambda item: item.control_id))


def _registry_control_specs() -> tuple[_ControlSpec, ...]:
    specs = (
        _ControlSpec(
            "registry.duplicate_suite",
            "suite_registry",
            "registry_semantic",
            ("duplicate_suite_id",),
            _registry_duplicate_suite,
        ),
        _ControlSpec(
            "registry.dangling_dependency",
            "suite_registry",
            "registry_semantic",
            ("dangling_dependency",),
            _registry_dangling_dependency,
            ("D04-PC070",),
        ),
        _ControlSpec(
            "registry.dependency_cycle",
            "suite_registry",
            "registry_semantic",
            ("dependency_cycle",),
            _registry_cycle,
        ),
        _ControlSpec(
            "registry.zero_component",
            "suite_registry",
            "registry_semantic",
            ("zero_components",),
            _registry_zero_component,
        ),
        _ControlSpec(
            "registry.unknown_entrypoint",
            "suite_registry",
            "registry_semantic",
            ("unknown_entrypoint",),
            _registry_unknown_entrypoint,
        ),
        _ControlSpec(
            "registry.duplicate_component",
            "suite_registry",
            "registry_semantic",
            ("duplicate_component",),
            _registry_duplicate_component,
        ),
        _ControlSpec(
            "registry.shell_payload",
            "suite_registry",
            "registry_semantic",
            ("shell_payload",),
            _registry_shell_payload,
        ),
        _ControlSpec(
            "registry.all_expansion_incomplete",
            "suite_registry",
            "registry_semantic",
            ("all_composition",),
            _registry_all_incomplete,
        ),
    )
    return tuple(sorted(specs, key=lambda item: item.control_id))


def _preflight_error(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def _failure_result(
    issues: list[dict[str, str]], discovered: int,
) -> dict[str, Any]:
    return {
        "schema": "dssc-v0.4-contract-controls/v1",
        "program_status": "ERROR",
        "counts": {
            "discovered": discovered,
            "executed": 0,
            "passed": 0,
            "failed": discovered,
            "skipped": 0,
        },
        "controls": [],
        "planned_case_coverage": {
            "authority_program_error_case_ids": list(PROGRAM_ERROR_PLANNED_CASE_IDS),
            "covered_here": [],
            "delegated_external": ["D04-PC067", "D04-PC069"],
            "pending": list(PROGRAM_ERROR_PLANNED_CASE_IDS),
            "control_ids_by_planned_case": {
                planned_case_id: []
                for planned_case_id in PROGRAM_ERROR_PLANNED_CASE_IDS
            },
        },
        "issues": sorted(
            issues,
            key=lambda item: (
                item.get("code", ""),
                item.get("location", ""),
                item.get("message", ""),
            ),
        ),
    }


def run_v04_contract_controls(root: Path, manifest: Document) -> dict[str, Any]:
    """Run all Phase 05 contract controls and return deterministic JSON data."""

    root = root.resolve()
    specs = tuple(
        sorted(
            _manifest_control_specs() + _registry_control_specs(),
            key=lambda item: item.control_id,
        )
    )
    preflight_issues: list[dict[str, str]] = []
    if not isinstance(manifest, dict):
        preflight_issues.append(
            _preflight_error(
                "CANONICAL_MANIFEST_TYPE",
                "manifest",
                "canonical manifest must be an object",
            )
        )
        return _failure_result(preflight_issues, len(specs))

    paths = {
        "manifest_schema": root / SCHEMA_RELPATH,
        "release_manifest": root / RELEASE_MANIFEST_RELPATH,
        "requirements_manifest": root / REQUIREMENTS_MANIFEST_RELPATH,
        "registry": root / REGISTRY_RELPATH,
        "registry_schema": root / REGISTRY_SCHEMA_RELPATH,
    }
    loaded: dict[str, Any] = {}
    for role, path in paths.items():
        try:
            loaded[role] = _read_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            preflight_issues.append(
                _preflight_error(
                    "CONTROL_AUTHORITY_UNAVAILABLE",
                    role,
                    f"{exc.__class__.__name__}: cannot load control authority",
                )
            )
    if preflight_issues:
        return _failure_result(preflight_issues, len(specs))

    canonical_manifest_issues = validate_v04_manifest_document(
        manifest,
        loaded["manifest_schema"],
        root,
        release_manifest=loaded["release_manifest"],
        requirements_manifest=loaded["requirements_manifest"],
        verify_fixture_hashes=True,
    )
    for issue in canonical_manifest_issues:
        preflight_issues.append(
            _preflight_error(
                "CANONICAL_MANIFEST_INVALID",
                issue.location,
                f"{issue.code}: {issue.message}",
            )
        )

    registry_schema_errors = sorted(
        Draft202012Validator(loaded["registry_schema"]).iter_errors(
            loaded["registry"]
        ),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.message,
        ),
    )
    for error in registry_schema_errors:
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        preflight_issues.append(
            _preflight_error(
                "CANONICAL_REGISTRY_SCHEMA_INVALID",
                location,
                error.message,
            )
        )

    # Lazy import avoids a catalog/checker import cycle when this module is
    # consumed by the v0.4 suite entrypoint.
    from dssc_validation.suite_registry import semantic_validate_registry

    for issue in semantic_validate_registry(loaded["registry"]):
        preflight_issues.append(
            _preflight_error(
                "CANONICAL_REGISTRY_SEMANTIC_INVALID",
                REGISTRY_RELPATH,
                f"{issue.code}: {issue.message}",
            )
        )

    planned_cases = {
        item.get("id"): item
        for item in loaded["requirements_manifest"].get("planned_cases", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for planned_case_id in PROGRAM_ERROR_PLANNED_CASE_IDS:
        planned_case = planned_cases.get(planned_case_id)
        if not isinstance(planned_case, dict) or not (
            planned_case.get("expected_business_status") is None
            and planned_case.get("expected_program_status") == "ERROR"
        ):
            preflight_issues.append(
                _preflight_error(
                    "PROGRAM_ERROR_PLANNED_CASE_AUTHORITY",
                    planned_case_id,
                    "planned case must declare null business status and program ERROR",
                )
            )
    if preflight_issues:
        return _failure_result(preflight_issues, len(specs))

    controls: list[dict[str, Any]] = []
    aggregate_issues: list[dict[str, str]] = []
    for spec in specs:
        source = (
            loaded["registry"]
            if spec.validator == "registry_semantic"
            else manifest
        )
        candidate = copy.deepcopy(source)
        try:
            spec.mutate(candidate)
            if spec.validator == "manifest_schema":
                observed = validate_v04_manifest_document(
                    candidate,
                    loaded["manifest_schema"],
                    root,
                    release_manifest=loaded["release_manifest"],
                    requirements_manifest=loaded["requirements_manifest"],
                    verify_fixture_hashes=False,
                )
                actual_codes = sorted({issue.code for issue in observed})
            elif spec.validator in {
                "manifest_semantic",
                "manifest_semantic_hash",
            }:
                observed = semantic_validate_v04_manifest(
                    candidate,
                    root,
                    release_manifest=loaded["release_manifest"],
                    requirements_manifest=loaded["requirements_manifest"],
                    verify_fixture_hashes=(
                        spec.validator == "manifest_semantic_hash"
                    ),
                )
                actual_codes = sorted({issue.code for issue in observed})
            else:
                actual_codes = sorted(
                    {
                        issue.code
                        for issue in semantic_validate_registry(candidate)
                    }
                )
        except Exception as exc:  # noqa: BLE001 - control failures are evidence
            actual_codes = ["CONTROL_EXECUTION_ERROR"]
            aggregate_issues.append(
                {
                    "code": "CONTROL_EXECUTION_ERROR",
                    "control_id": spec.control_id,
                    "message": exc.__class__.__name__,
                }
            )
        actual_program_status = "ERROR" if actual_codes else "SUCCESS"
        passed = actual_program_status == "ERROR" and set(
            spec.expected_codes
        ).issubset(actual_codes)
        record = {
            "id": spec.control_id,
            "domain": spec.domain,
            "expected_program_status": "ERROR",
            "actual_program_status": actual_program_status,
            "expected_codes": list(spec.expected_codes),
            "actual_codes": actual_codes,
            "planned_case_ids": list(spec.planned_case_ids),
            "passed": passed,
        }
        controls.append(record)
        if not passed:
            aggregate_issues.append(
                {
                    "code": "CONTROL_EXPECTATION_MISSED",
                    "control_id": spec.control_id,
                    "message": (
                        f"expected={list(spec.expected_codes)}; "
                        f"actual={actual_codes}"
                    ),
                }
            )

    controls.sort(key=lambda item: item["id"])
    passed_count = sum(1 for item in controls if item["passed"])
    controls_by_planned_case = {
        planned_case_id: sorted(
            item["id"]
            for item in controls
            if planned_case_id in item["planned_case_ids"]
        )
        for planned_case_id in PROGRAM_ERROR_PLANNED_CASE_IDS
    }
    covered_here = sorted(
        planned_case_id
        for planned_case_id, control_ids in controls_by_planned_case.items()
        if control_ids
        and all(
            item["passed"]
            for item in controls
            if item["id"] in control_ids
        )
    )
    pending = sorted(set(PROGRAM_ERROR_PLANNED_CASE_IDS) - set(covered_here))
    successful = passed_count == len(controls) and not aggregate_issues
    return {
        "schema": "dssc-v0.4-contract-controls/v1",
        "program_status": "SUCCESS" if successful else "ERROR",
        "counts": {
            "discovered": len(controls),
            "executed": len(controls),
            "passed": passed_count,
            "failed": len(controls) - passed_count,
            "skipped": 0,
        },
        "controls": controls,
        "planned_case_coverage": {
            "authority_program_error_case_ids": list(PROGRAM_ERROR_PLANNED_CASE_IDS),
            "covered_here": covered_here,
            "delegated_external": ["D04-PC067", "D04-PC069"],
            "pending": pending,
            "control_ids_by_planned_case": controls_by_planned_case,
        },
        "issues": sorted(
            aggregate_issues,
            key=lambda item: (
                item.get("code", ""),
                item.get("control_id", ""),
                item.get("message", ""),
            ),
        ),
    }


__all__ = ["PROGRAM_ERROR_PLANNED_CASE_IDS", "run_v04_contract_controls"]
