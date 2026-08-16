"""Controlled catalog component for the Phase 04 release-model contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dssc_validation.hashing import sha256_file
from dssc_validation.model_contract import audit_model_contract
from dssc_validation.model_report import (
    finalize_model_result,
    write_model_evidence,
)
from dssc_validation.paths import (
    is_exact_phase_build_dir,
    requirements_lock_path,
    validation_suites_path,
    validation_suites_schema_path,
)
from dssc_validation.release_manifest import load_and_audit_release_manifest
from dssc_validation.requirements_registry import load_and_validate_requirements


def _failure_component(message: str) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "program_status": "ERROR",
        "message": message,
        "details": {},
        "machine_details": {},
    }


def run_model_check(context: dict[str, Any]) -> dict[str, Any]:
    """Audit the release/model contract and write normalized Phase 04 evidence."""
    root = context.get("repository_root")
    profile = context.get("profile")
    output_dir = context.get("output_dir")
    evidence_phase = context.get("evidence_phase")
    if not isinstance(root, Path) or profile not in {"host", "container"}:
        return _failure_component(
            "v0.4-model checker requires repository_root and host|container profile"
        )
    allowed_phases = {f"{phase:02d}" for phase in range(4, 10)}
    if (
        evidence_phase not in allowed_phases
        or not isinstance(output_dir, Path)
        or not is_exact_phase_build_dir(output_dir, evidence_phase, root)
    ):
        return _failure_component(
            "v0.4-model checker requires the exact registry-selected evidence "
            "boundary at Phase 04 or later"
        )

    try:
        release_audit = load_and_audit_release_manifest(root)
        requirements_validation = load_and_validate_requirements(root)
        payload = audit_model_contract(
            root,
            release_audit,
            requirements_validation,
            output_dir,
            profile,
        )
        registry_path = validation_suites_path(root)
        registry_schema_path = validation_suites_schema_path(root)
        lock_path = requirements_lock_path(root)
        actual_registry_hash = (
            sha256_file(registry_path) if registry_path.is_file() else None
        )
        actual_registry_schema_hash = (
            sha256_file(registry_schema_path)
            if registry_schema_path.is_file()
            else None
        )
        registry_issues: list[dict[str, str]] = []
        if actual_registry_hash is None:
            registry_issues.append(
                {
                    "code": "SUITE_REGISTRY_MISSING",
                    "location": "C_Semantic_Treehouse/manifests/validation-suites.json",
                    "message": "suite registry is missing",
                }
            )
        elif actual_registry_hash != context.get("registry_sha256"):
            registry_issues.append(
                {
                    "code": "SUITE_REGISTRY_CONTEXT_HASH_MISMATCH",
                    "location": "C_Semantic_Treehouse/manifests/validation-suites.json",
                    "message": "dispatcher registry hash differs from the current file",
                }
            )
        if actual_registry_schema_hash is None:
            registry_issues.append(
                {
                    "code": "SUITE_REGISTRY_SCHEMA_MISSING",
                    "location": "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json",
                    "message": "suite registry schema is missing",
                }
            )
        suite_registry_record = {
            "status": "SUCCESS" if not registry_issues else "ERROR",
            "path": "C_Semantic_Treehouse/manifests/validation-suites.json",
            "sha256": actual_registry_hash,
            "contract_version": context.get("contract_version"),
            "schema_path": (
                "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json"
            ),
            "schema_sha256": actual_registry_schema_hash,
            "issues": registry_issues,
        }
        payload["suite_registry"] = suite_registry_record
        payload["checks"].append(
            {"id": "suite_registry", "status": suite_registry_record["status"]}
        )
        payload["counts"]["discovered"] += 1
        payload["counts"]["executed"] += 1
        if registry_issues:
            payload["counts"]["failed"] += 1
            payload["program_status"] = "ERROR"
            payload["exit_code"] = 1
            payload["message"] = "v0.4 release model failed"
        else:
            payload["counts"]["passed"] += 1
        payload.update(
            {
                "requirements_validation": {
                    "status": (
                        "SUCCESS" if requirements_validation.ok else "ERROR"
                    ),
                    "issues": list(requirements_validation.issues),
                },
                "registry_contract_version": context.get("contract_version"),
                "registry_path": (
                    "C_Semantic_Treehouse/manifests/validation-suites.json"
                ),
                "registry_sha256": context.get("registry_sha256"),
                "registry_schema_path": (
                    "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json"
                ),
                "registry_schema_sha256": (
                    actual_registry_schema_hash
                ),
                "requirements_lock_sha256": (
                    sha256_file(lock_path) if lock_path.is_file() else None
                ),
            }
        )
        result, environment = finalize_model_result(root, profile, payload)
        result_path, environment_path, markdown_path = write_model_evidence(
            output_dir,
            profile,
            result,
            environment,
            root,
            evidence_phase,
        )
    except Exception as exc:  # noqa: BLE001 - dispatcher receives a stable failure
        return _failure_component(
            f"v0.4-model checker failed closed: {exc.__class__.__name__}"
        )

    passed = result.get("program_status") == "SUCCESS" and result.get("exit_code") == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "program_status": "SUCCESS" if passed else "ERROR",
        "message": (
            "v0.4 release model passed" if passed else "v0.4 release model failed"
        ),
        "details": {
            "model_result": result,
            "evidence_files": [
                result_path.name,
                environment_path.name,
                markdown_path.name,
            ],
        },
        "machine_details": {"model_environment": environment},
    }


__all__ = ["run_model_check"]
