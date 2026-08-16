"""Controlled catalog component for Phase 03 D-group traceability."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dssc_validation.d_group_contract import audit_d_group_contract
from dssc_validation.hashing import sha256_file
from dssc_validation.paths import (
    is_exact_phase_build_dir,
    requirements_lock_path,
)
from dssc_validation.requirements_registry import load_and_validate_requirements
from dssc_validation.traceability_report import (
    finalize_traceability_result,
    normalized_contract_evidence,
    render_requirements_traceability,
    write_traceability_evidence,
)


_DOCUMENTS = (
    "docs/v0.4/requirements-traceability.md",
    "docs/v0.4/compatibility-matrix.md",
    "docs/v0.4/result-classification.md",
    "docs/v0.4/test-plan.md",
    "docs/v0.4/decisions/ADR-001-dct-conforms-to.md",
    "docs/v0.4/decisions/ADR-002-wire-profile-and-version-identity.md",
    "docs/v0.4/decisions/ADR-003-energy-record-inheritance.md",
)


def _documentation_validation(
    root: Path, manifest: dict[str, Any], manifest_sha256: str
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    hashes: dict[str, str] = {}
    texts: dict[str, str] = {}
    for relpath in _DOCUMENTS:
        path = root / relpath
        if not path.is_file() or path.stat().st_size == 0:
            issues.append(
                {
                    "code": "MISSING_DOCUMENT",
                    "location": relpath,
                    "message": "required Phase 03 document is missing or empty",
                }
            )
            continue
        hashes[relpath] = sha256_file(path)
        texts[relpath] = path.read_text(encoding="utf-8")

    traceability_path = "docs/v0.4/requirements-traceability.md"
    if traceability_path in texts:
        expected = render_requirements_traceability(manifest, manifest_sha256)
        if texts[traceability_path] != expected:
            issues.append(
                {
                    "code": "TRACEABILITY_MARKDOWN_DRIFT",
                    "location": traceability_path,
                    "message": "human traceability table differs from the machine registry",
                }
            )

    test_plan = texts.get("docs/v0.4/test-plan.md", "")
    for case in manifest.get("planned_cases", []):
        if isinstance(case, dict) and isinstance(case.get("id"), str):
            if case["id"] not in test_plan:
                issues.append(
                    {
                        "code": "TEST_PLAN_CASE_OMISSION",
                        "location": "docs/v0.4/test-plan.md",
                        "message": f"planned case is absent from test plan: {case['id']}",
                    }
                )
    for requirement in manifest.get("requirements", []):
        if isinstance(requirement, dict) and isinstance(requirement.get("id"), str):
            if requirement["id"] not in test_plan:
                issues.append(
                    {
                        "code": "TEST_PLAN_REQUIREMENT_OMISSION",
                        "location": "docs/v0.4/test-plan.md",
                        "message": (
                            f"requirement is absent from test plan: {requirement['id']}"
                        ),
                    }
                )

    compatibility = texts.get("docs/v0.4/compatibility-matrix.md", "")
    if "wire-profile breaking migration" not in compatibility:
        issues.append(
            {
                "code": "COMPATIBILITY_CONCLUSION_MISSING",
                "location": "docs/v0.4/compatibility-matrix.md",
                "message": "breaking-migration conclusion is missing",
            }
        )
    classification = texts.get("docs/v0.4/result-classification.md", "")
    for token in ("UNTESTABLE", "FAIL", "INAPPLICABLE", "PASS", "ERROR"):
        if token not in classification:
            issues.append(
                {
                    "code": "CLASSIFICATION_STATUS_MISSING",
                    "location": "docs/v0.4/result-classification.md",
                    "message": f"classification document omits {token}",
                }
            )
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "documents": [
            {"path": path, "sha256": hashes[path]} for path in sorted(hashes)
        ],
        "issues": sorted(
            issues, key=lambda item: (item["code"], item["location"], item["message"])
        ),
    }


def _failure_component(message: str) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "program_status": "ERROR",
        "message": message,
        "details": {},
        "machine_details": {},
    }


def run_traceability_check(context: dict[str, Any]) -> dict[str, Any]:
    """Validate the registry, audit the D contract, and write normalized evidence."""
    root = context.get("repository_root")
    profile = context.get("profile")
    output_dir = context.get("output_dir")
    evidence_phase = context.get("evidence_phase")
    if not isinstance(root, Path) or profile not in {"host", "container"}:
        return _failure_component(
            "traceability checker requires repository_root and host|container profile"
        )
    allowed_phases = {f"{phase:02d}" for phase in range(3, 10)}
    if (
        evidence_phase not in allowed_phases
        or not isinstance(output_dir, Path)
        or not is_exact_phase_build_dir(output_dir, evidence_phase, root)
    ):
        return _failure_component(
            "traceability checker requires the exact registry-selected evidence "
            "boundary at Phase 03 or later"
        )

    validation = load_and_validate_requirements(root)
    requirements_record = validation.deterministic_record()
    validation_record = {
        "status": "SUCCESS" if validation.ok else "ERROR",
        "issues": list(validation.issues),
    }
    if validation.manifest is None:
        contract = {
            "status": "ERROR",
            "issues": ["requirements manifest is unavailable"],
        }
        documentation = {
            "status": "ERROR",
            "documents": [],
            "issues": [
                {
                    "code": "MANIFEST_UNAVAILABLE",
                    "location": "docs/v0.4/requirements-traceability.md",
                    "message": "cannot compare documentation without a manifest",
                }
            ],
        }
    else:
        try:
            contract = audit_d_group_contract(root, validation.manifest)
            contract = normalized_contract_evidence(contract)
        except Exception as exc:  # noqa: BLE001 - normalized fail-closed evidence
            contract = {
                "status": "ERROR",
                "issues": [
                    {
                        "code": exc.__class__.__name__,
                        "message": str(exc),
                    }
                ],
            }
        documentation = _documentation_validation(
            root, validation.manifest, validation.manifest_sha256 or ""
        )

    successful = (
        validation.ok
        and contract.get("status") == "SUCCESS"
        and documentation.get("status") == "SUCCESS"
    )
    lock_path = requirements_lock_path(root)
    payload = {
        "requirements_registry": requirements_record,
        "requirements_validation": validation_record,
        "d_group_contract": contract,
        "documentation_validation": documentation,
        "registry_contract_version": context.get("contract_version"),
        "registry_sha256": context.get("registry_sha256"),
        "requirements_lock_sha256": (
            sha256_file(lock_path) if lock_path.is_file() else None
        ),
        "program_status": "SUCCESS" if successful else "ERROR",
        "exit_code": 0 if successful else 1,
        "message": (
            "D-group requirements traceability passed"
            if successful
            else "D-group requirements traceability failed"
        ),
    }
    result, environment = finalize_traceability_result(root, profile, payload)
    (
        result_path,
        environment_path,
        markdown_path,
        contract_json_path,
        contract_markdown_path,
    ) = write_traceability_evidence(
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
            "D-group requirements traceability passed"
            if passed
            else "D-group requirements traceability failed"
        ),
        "details": {
            "traceability_result": result,
            "evidence_files": [
                result_path.name,
                environment_path.name,
                markdown_path.name,
                contract_json_path.name,
                contract_markdown_path.name,
            ],
        },
        "machine_details": {"traceability_environment": environment},
    }


__all__ = ["run_traceability_check"]
