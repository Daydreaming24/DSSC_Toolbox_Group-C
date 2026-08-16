"""Controlled composition check for the public ``all`` suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dssc_validation import PUBLIC_SUITE_IDS


EXPECTED_CONSTITUENT_SUITES = (
    "frozen",
    "environment",
    "baseline",
    "traceability",
    "v0.4-model",
    "v0.4",
)
EXPECTED_ALL_COMPONENTS = (
    {"id": "all.composition", "entrypoint": "check_all_composition"},
    {"id": "all.semantic-sparql", "entrypoint": "check_semantic_sparql"},
    {"id": "all.quality", "entrypoint": "check_quality_metrics"},
    {"id": "all.governance", "entrypoint": "check_governance"},
    {"id": "all.documentation", "entrypoint": "check_documentation"},
)
EXPECTED_V04_COMPONENTS = (
    {"id": "v0.4.test-case-schema", "entrypoint": "check_v04_test_case_schema"},
    {"id": "v0.4.manifest-semantics", "entrypoint": "check_v04_manifest_semantics"},
    {"id": "v0.4.fixture-hashes", "entrypoint": "check_v04_fixture_hashes"},
    {"id": "v0.4.four-state", "entrypoint": "check_v04_four_state"},
    {"id": "v0.4.report-assertions", "entrypoint": "check_v04_report_assertions"},
    {"id": "v0.4.target-activation", "entrypoint": "check_v04_target_activation"},
    {"id": "v0.4.fault-injection", "entrypoint": "check_v04_fault_injection"},
)


def _failure(message: str, issues: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "program_status": "ERROR",
        "message": message,
        "details": {"issues": sorted(issues or [])},
        "machine_details": {},
    }


def run_all_composition_check(context: dict[str, Any]) -> dict[str, Any]:
    """Prove that ``all`` expands the six public non-composite suites once."""

    # Import lazily: suite_registry consumes the completed controlled catalog,
    # while this checker is itself imported while that catalog is constructed.
    from dssc_validation.suite_registry import (
        expand_suite_components,
        load_and_validate_registry,
    )

    root = context.get("repository_root")
    if not isinstance(root, Path):
        return _failure("all composition checker requires repository_root")

    load = load_and_validate_registry(root)
    if not load.ok or load.registry is None:
        return _failure(
            "all composition registry validation failed",
            [f"{issue.code}: {issue.message}" for issue in load.issues],
        )

    issues: list[str] = []
    registry = load.registry
    suites = {
        item.get("id"): item
        for item in registry.get("suites", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    all_suite = suites.get("all")
    if not isinstance(all_suite, dict):
        issues.append("all suite is absent")
    else:
        if all_suite.get("status") != "IMPLEMENTED":
            issues.append("all suite must be IMPLEMENTED")
        if all_suite.get("owner_phase") != "05":
            issues.append("all owner_phase must be 05")
        if tuple(all_suite.get("depends_on", [])) != EXPECTED_CONSTITUENT_SUITES:
            issues.append("all dependencies are not the exact six-suite order")
        if all_suite.get("components") != list(EXPECTED_ALL_COMPONENTS):
            issues.append(
                "all must contain the composition check, the three fixed Phase 06 "
                "checks, and the Phase 07 documentation check"
            )

    v04_suite = suites.get("v0.4")
    if not isinstance(v04_suite, dict):
        issues.append("v0.4 suite is absent")
    else:
        if v04_suite.get("status") != "IMPLEMENTED":
            issues.append("v0.4 suite must be IMPLEMENTED")
        if v04_suite.get("owner_phase") != "05":
            issues.append("v0.4 owner_phase must be 05")
        if v04_suite.get("depends_on") != ["environment", "v0.4-model"]:
            issues.append("v0.4 dependencies differ from the fixed Phase 05 contract")
        if v04_suite.get("components") != list(EXPECTED_V04_COMPONENTS):
            issues.append("v0.4 must expose the exact seven Phase 05 components")

    if tuple(PUBLIC_SUITE_IDS) != EXPECTED_CONSTITUENT_SUITES + ("all",):
        issues.append("public suite catalog differs from the fixed seven-suite contract")

    components, error_code, error_message = expand_suite_components(registry, "all")
    if error_code is not None or components is None:
        issues.append(f"all expansion failed: {error_code}: {error_message}")
        components = []

    owner_order: list[str] = []
    for component in components:
        owner = component.get("suite_id")
        if isinstance(owner, str) and owner not in owner_order:
            owner_order.append(owner)
    expected_owner_order = list(EXPECTED_CONSTITUENT_SUITES) + ["all"]
    if owner_order != expected_owner_order:
        issues.append(
            "all expanded owner order mismatch: "
            f"expected={expected_owner_order}; actual={owner_order}"
        )
    for suite_id in EXPECTED_CONSTITUENT_SUITES:
        count = sum(1 for item in owner_order if item == suite_id)
        if count != 1:
            issues.append(f"all must expand suite owner {suite_id} exactly once")

    if issues:
        return _failure("all composition contract failed", issues)
    return {
        "status": "PASS",
        "program_status": "SUCCESS",
        "message": (
            "all expands the six constituent public suites and runs the Phase 06 "
            "semantic/quality/governance checks plus Phase 07 documentation deterministically"
        ),
        "details": {
            "constituent_suites": list(EXPECTED_CONSTITUENT_SUITES),
            "expanded_owner_order": owner_order,
            "expanded_component_ids": [item["id"] for item in components],
            "expanded_component_count": len(components),
            "contract_version": load.contract_version,
            "registry_sha256": load.registry_sha256,
        },
        "machine_details": {},
    }


__all__ = [
    "EXPECTED_CONSTITUENT_SUITES",
    "EXPECTED_ALL_COMPONENTS",
    "EXPECTED_V04_COMPONENTS",
    "run_all_composition_check",
]
