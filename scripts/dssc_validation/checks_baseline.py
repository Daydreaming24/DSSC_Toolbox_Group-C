"""Controlled catalog component for the Phase 02 baseline reproduction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dssc_validation.baseline_manifest import (
    BaselineManifestError,
    baseline_manifest_path,
    baseline_manifest_schema_path,
    load_and_validate_baseline_manifest,
)
from dssc_validation.baseline_report import (
    finalize_baseline_result,
    write_baseline_evidence,
)
from dssc_validation.baseline_runner import (
    EXPECTED_CASE_COUNT,
    EXPECTED_CATEGORY_COUNTS,
    run_baseline_cases,
)
from dssc_validation.hashing import sha256_file
from dssc_validation.paths import is_exact_phase_build_dir, requirements_lock_path


def _empty_counts() -> dict[str, int]:
    return {
        "discovered": 0,
        "executed": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
    }


def _empty_category_counts() -> dict[str, dict[str, int]]:
    return {category: _empty_counts() for category in EXPECTED_CATEGORY_COUNTS}


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _hash_if_file(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def _failure_payload(
    context: dict[str, Any],
    root: Path,
    issue: dict[str, Any],
) -> dict[str, Any]:
    manifest_path = baseline_manifest_path(root)
    schema_path = baseline_manifest_schema_path(root)
    lock_path = requirements_lock_path(root)
    return {
        "manifest_path": _relative(root, manifest_path),
        "manifest_sha256": _hash_if_file(manifest_path),
        "manifest_schema_path": _relative(root, schema_path),
        "manifest_schema_sha256": _hash_if_file(schema_path),
        "manifest_schema_version": None,
        "registry_contract_version": context.get("contract_version"),
        "registry_sha256": context.get("registry_sha256"),
        "requirements_lock_sha256": _hash_if_file(lock_path),
        "preflight": {"status": "ERROR", "issues": issue.get("issues", [issue])},
        "artifact_hashes": [],
        "required_case_ids": [],
        "execution_schema": "dssc.baseline.execution.v1",
        "program_status": "ERROR",
        "exit_code": 1,
        "message": "baseline manifest preflight failed",
        "counts": _empty_counts(),
        "category_counts": _empty_category_counts(),
        "case_results": [],
    }


def _success_payload(
    context: dict[str, Any],
    root: Path,
    preflight: Any,
    execution: dict[str, Any],
) -> dict[str, Any]:
    preflight_record = preflight.deterministic_record()
    lock_path = requirements_lock_path(root)
    contract_issues = _execution_contract_issues(execution, preflight.required_case_ids)
    successful = execution.get("program_status") == "SUCCESS" and not contract_issues
    return {
        "manifest_path": _relative(root, preflight.manifest_path),
        "manifest_sha256": preflight.manifest_sha256,
        "manifest_schema_path": _relative(root, preflight.schema_path),
        "manifest_schema_sha256": preflight.schema_sha256,
        "manifest_schema_version": preflight.manifest_schema_version,
        "registry_contract_version": context.get("contract_version"),
        "registry_sha256": context.get("registry_sha256"),
        "requirements_lock_sha256": _hash_if_file(lock_path),
        "preflight": {
            "status": "SUCCESS",
            "case_count": preflight_record["case_count"],
            "category_counts": preflight_record["category_counts"],
            "release_counts": preflight_record["release_counts"],
            "validator_counts": preflight_record["validator_counts"],
            "artifact_count": preflight_record["artifact_count"],
            "artifact_kind_counts": preflight_record["artifact_kind_counts"],
            "artifact_release_counts": preflight_record["artifact_release_counts"],
        },
        "artifact_hashes": preflight_record["artifacts"],
        "required_case_ids": list(preflight.required_case_ids),
        "execution_schema": execution.get("schema"),
        "execution_issues": list(execution.get("issues", [])) + contract_issues,
        "program_status": "SUCCESS" if successful else "ERROR",
        "exit_code": 0 if successful else 1,
        "message": (
            execution.get("message", "baseline execution failed")
            if not contract_issues
            else "baseline execution result contract failed"
        ),
        "counts": execution.get("counts", _empty_counts()),
        "category_counts": execution.get(
            "category_counts", _empty_category_counts()
        ),
        "case_results": execution.get("case_results", []),
    }


def _execution_contract_issues(
    execution: dict[str, Any],
    required_case_ids: tuple[str, ...],
) -> list[str]:
    issues: list[str] = []
    expected_counts = {
        "discovered": EXPECTED_CASE_COUNT,
        "executed": EXPECTED_CASE_COUNT,
        "passed": EXPECTED_CASE_COUNT,
        "failed": 0,
        "skipped": 0,
    }
    if execution.get("counts") != expected_counts:
        issues.append("aggregate counts differ from the fixed 33-case contract")

    category_counts = execution.get("category_counts")
    for category, expected in EXPECTED_CATEGORY_COUNTS.items():
        expected_category = {
            "discovered": expected,
            "executed": expected,
            "passed": expected,
            "failed": 0,
            "skipped": 0,
        }
        if (
            not isinstance(category_counts, dict)
            or category_counts.get(category) != expected_category
        ):
            issues.append(f"category counts differ for {category}")

    cases = execution.get("case_results")
    if not isinstance(cases, list):
        return sorted(issues + ["case_results must be an array"])
    case_ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if case_ids != list(required_case_ids):
        issues.append("case result IDs/order differ from required_case_ids")
    for case in cases:
        if not isinstance(case, dict):
            issues.append("case result must be an object")
            continue
        case_id = case.get("id", "<unknown>")
        assertions = case.get("assertions")
        if case.get("passed") is not True:
            issues.append(f"case {case_id} did not pass its oracle")
        if case.get("actual_business_status") != case.get("expected_business_status"):
            issues.append(f"case {case_id} business status differs")
        if (
            case.get("expected_program_status") != "SUCCESS"
            or case.get("actual_program_status") != "SUCCESS"
        ):
            issues.append(f"case {case_id} program status differs")
        if not isinstance(assertions, list) or not assertions:
            issues.append(f"case {case_id} has no assertions")
        elif any(
            not isinstance(assertion, dict) or assertion.get("passed") is not True
            for assertion in assertions
        ):
            issues.append(f"case {case_id} contains a failed assertion")
    return sorted(set(issues))


def run_baseline_check(context: dict[str, Any]) -> dict[str, Any]:
    """Preflight, execute, and write the deterministic baseline evidence."""
    root = context.get("repository_root")
    profile = context.get("profile")
    output_dir = context.get("output_dir")
    evidence_phase = context.get("evidence_phase")
    if not isinstance(root, Path) or profile not in {"host", "container"}:
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "baseline checker requires repository_root and host|container profile",
            "details": {},
            "machine_details": {},
        }
    allowed_evidence_phases = {f"{phase:02d}" for phase in range(2, 10)}
    if (
        evidence_phase not in allowed_evidence_phases
        or not isinstance(output_dir, Path)
        or not is_exact_phase_build_dir(output_dir, evidence_phase, root)
    ):
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": (
                "baseline checker requires the exact registry-selected evidence "
                "boundary at Phase 02 or later"
            ),
            "details": {},
            "machine_details": {},
        }

    try:
        preflight = load_and_validate_baseline_manifest(root)
    except BaselineManifestError as exc:
        payload = _failure_payload(context, root, exc.as_dict())
    except Exception as exc:  # noqa: BLE001 - unexpected preflight errors are fatal
        payload = _failure_payload(
            context,
            root,
            {
                "code": "BASELINE_PREFLIGHT_INTERNAL_ERROR",
                "issues": [
                    {
                        "code": exc.__class__.__name__,
                        "location": "<preflight>",
                        "message": "unexpected baseline preflight failure",
                    }
                ],
            },
        )
    else:
        execution = run_baseline_cases(preflight.runner_input(), root)
        payload = _success_payload(context, root, preflight, execution)

    result, environment = finalize_baseline_result(root, profile, payload)
    result_path, environment_path, markdown_path = write_baseline_evidence(
        output_dir,
        profile,
        result,
        environment,
        root,
        evidence_phase,
    )
    passed = result.get("program_status") == "SUCCESS" and result.get("exit_code") == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "program_status": "SUCCESS" if passed else "ERROR",
        "message": (
            "baseline reproduction passed: 33/33 cases"
            if passed
            else "baseline reproduction failed"
        ),
        "details": {
            "baseline_result": result,
            "evidence_files": [
                result_path.name,
                environment_path.name,
                markdown_path.name,
            ],
        },
        "machine_details": {"baseline_environment": environment},
    }


__all__ = ["run_baseline_check"]
