"""Controlled Phase 05 component entrypoints for the v0.4 fixture suite."""

from __future__ import annotations

import copy
import hashlib
import json
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping
from unittest.mock import patch

from dssc_validation.evidence import atomic_write_json, json_bytes
from dssc_validation.v04_classifier import (
    SH,
    V04ReportError,
    build_requirement_bindings,
    normalize_shacl_report,
)
from dssc_validation.v04_controls import run_v04_contract_controls
from dssc_validation.v04_harness import (
    V04HarnessError,
    classify_execution_failure,
    evaluate_v04_suite_aggregate,
    execute_v04_suite,
    run_failure_boundary_self_tests,
    run_v04_harness,
)
from dssc_validation.v04_manifest import (
    V04ManifestValidationResult,
    load_and_validate_v04_manifest,
)
from dssc_validation.v04_reporter import finalize_v04_result


_CACHE_KEY = "_dssc_v04_phase05_cache"
_MANIFEST_VALIDATION_RELPATH = "build/phase-05/manifest-validation.json"
_NEGATIVE_CONTROLS_RELPATH = "build/phase-05/negative-controls.json"
_DETERMINISM_RELPATH = "build/phase-05/determinism.json"
_REQUIRED_SOURCES = (
    "scripts/dssc_validation/checks_v04.py",
    "scripts/dssc_validation/v04_controls.py",
    "scripts/dssc_validation/checks_all.py",
)
_SCHEMA_ISSUE_CODES = frozenset(
    {
        "DUPLICATE_JSON_KEY",
        "MANIFEST_PARSE",
        "MANIFEST_ROOT",
        "MISSING_MANIFEST",
        "MISSING_SCHEMA",
        "SCHEMA_INVALID",
        "SCHEMA_PARSE",
        "SCHEMA_ROOT",
        "SCHEMA_VALIDATION",
    }
)
_REPORT_FIELDS = frozenset(
    {
        "focus_node",
        "result_path",
        "source_shape",
        "source_constraint_component",
        "severity",
        "message",
        "value",
        "requirement_id",
    }
)


def _failure(message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "program_status": "ERROR",
        "message": message,
        "details": details or {},
        "machine_details": {},
    }


def _success(message: str, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "program_status": "SUCCESS",
        "message": message,
        "details": details,
        "machine_details": {},
    }


def _root(context: Mapping[str, Any]) -> Path:
    value = context.get("repository_root")
    if not isinstance(value, Path):
        raise ValueError("v0.4 checker requires repository_root")
    return value.resolve()


def _cache(context: dict[str, Any]) -> dict[str, Any]:
    value = context.setdefault(_CACHE_KEY, {})
    if not isinstance(value, dict):
        raise ValueError("v0.4 checker cache is invalid")
    return value


def _manifest_validation(
    context: dict[str, Any], *, verify_fixture_hashes: bool
) -> V04ManifestValidationResult:
    cache = _cache(context)
    key = "manifest_full" if verify_fixture_hashes else "manifest_semantic"
    value = cache.get(key)
    if isinstance(value, V04ManifestValidationResult):
        return value
    value = load_and_validate_v04_manifest(
        _root(context), verify_fixture_hashes=verify_fixture_hashes
    )
    cache[key] = value
    return value


def _phase05_output(root: Path, relpath: str) -> Path:
    expected_prefix = "build/phase-05/"
    if not relpath.startswith(expected_prefix) or ".." in Path(relpath).parts:
        raise ValueError("Phase 05 output path is outside the controlled boundary")
    current = root
    for name in ("build", "phase-05"):
        current = current / name
        if current.is_symlink() or bool(
            getattr(current, "is_junction", lambda: False)()
        ):
            raise ValueError(f"Phase 05 output component is a link: {name}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"Phase 05 output component is not a directory: {name}")
        current.mkdir(exist_ok=True)
    target = root.joinpath(*Path(relpath).parts)
    target.resolve().relative_to(root)
    return target


def _write_phase05_json(root: Path, relpath: str, value: dict[str, Any]) -> None:
    atomic_write_json(_phase05_output(root, relpath), value)


def _issue_records(result: V04ManifestValidationResult) -> list[dict[str, str]]:
    return [issue.as_dict() for issue in result.issues]


def run_v04_test_case_schema_check(context: dict[str, Any]) -> dict[str, Any]:
    """Validate the canonical test manifest's Draft 2020-12 branch contract."""
    try:
        result = _manifest_validation(context, verify_fixture_hashes=False)
    except Exception as exc:  # noqa: BLE001
        return _failure(f"v0.4 test-case schema check failed closed: {exc.__class__.__name__}")
    schema_issues = [
        issue.as_dict() for issue in result.issues if issue.code in _SCHEMA_ISSUE_CODES
    ]
    passed = (
        result.manifest is not None
        and result.schema_sha256 is not None
        and not schema_issues
    )
    details = {
        "manifest_path": "C_Semantic_Treehouse/manifests/v0.4-test-cases.json",
        "manifest_sha256": result.manifest_sha256,
        "schema_path": (
            "C_Semantic_Treehouse/manifests/schemas/v0.4-test-cases.schema.json"
        ),
        "schema_sha256": result.schema_sha256,
        "case_count": len(result.manifest.get("cases", [])) if result.manifest else 0,
        "issues": schema_issues,
    }
    if not passed:
        return _failure("v0.4 test-case schema validation failed", details)
    return _success("v0.4 test-case schema validation passed", details)


def run_v04_manifest_semantics_check(context: dict[str, Any]) -> dict[str, Any]:
    """Validate authority references and semantics independently of fixture bytes."""
    try:
        result = _manifest_validation(context, verify_fixture_hashes=False)
    except Exception as exc:  # noqa: BLE001
        return _failure(f"v0.4 manifest semantic check failed closed: {exc.__class__.__name__}")
    details = result.deterministic_record()
    if result.issues:
        return _failure("v0.4 manifest semantic validation failed", details)
    return _success("v0.4 manifest semantic validation passed", details)


def run_v04_fixture_hashes_check(context: dict[str, Any]) -> dict[str, Any]:
    """Verify every fixture byte binding and write manifest-validation evidence."""
    try:
        root = _root(context)
        result = _manifest_validation(context, verify_fixture_hashes=True)
        record = result.deterministic_record()
        issue_count = len(result.issues)
        checks = [
            {"id": "schema", "passed": not any(
                issue.code in _SCHEMA_ISSUE_CODES for issue in result.issues
            )},
            {"id": "cross-record-semantics", "passed": result.ok},
            {"id": "fixture-byte-bindings", "passed": result.ok},
        ]
        passed_count = sum(1 for item in checks if item["passed"])
        evidence = {
            "schema": "dssc.v0.4.manifest-validation.v1",
            "program_status": "SUCCESS" if result.ok else "ERROR",
            "counts": {
                "discovered": len(checks),
                "executed": len(checks),
                "passed": passed_count,
                "failed": len(checks) - passed_count,
                "skipped": 0,
            },
            "checks": checks,
            "validation": record,
        }
        _write_phase05_json(root, _MANIFEST_VALIDATION_RELPATH, evidence)
    except Exception as exc:  # noqa: BLE001
        return _failure(f"v0.4 fixture hash check failed closed: {exc.__class__.__name__}")
    details = {
        "fixture_count": record["case_count"],
        "fixture_hash_count": len(record["fixtures"]),
        "issue_count": issue_count,
        "evidence_file": _MANIFEST_VALIDATION_RELPATH,
        "manifest_sha256": record["manifest_sha256"],
    }
    if not result.ok:
        details["issues"] = _issue_records(result)
        return _failure("v0.4 fixture byte validation failed", details)
    return _success("v0.4 fixture byte validation passed", details)


def _ensure_harness(context: dict[str, Any]) -> dict[str, Any]:
    cache = _cache(context)
    value = cache.get("harness_component")
    if isinstance(value, dict):
        return value
    validation = _manifest_validation(context, verify_fixture_hashes=True)
    if not validation.ok or validation.manifest is None:
        value = _failure(
            "v0.4 harness blocked by invalid manifest",
            {"issues": _issue_records(validation)},
        )
    else:
        # Load and validate the complete controlled catalog before the first
        # canonical run. This fixes the loaded-source set for both reruns and
        # prevents a later negative-control import from changing provenance.
        from dssc_validation.suite_registry import load_and_validate_registry

        registry = load_and_validate_registry(_root(context))
        if not registry.ok:
            value = _failure(
                "v0.4 harness blocked by invalid suite registry",
                {
                    "issues": [
                        {"code": issue.code, "message": issue.message}
                        for issue in registry.issues
                    ]
                },
            )
            cache["harness_component"] = value
            return value
        context["manifest_path"] = validation.manifest_path
        context["v04_required_sources"] = _REQUIRED_SOURCES
        value = run_v04_harness(validation.manifest, context, write_outputs=True)
    cache["harness_component"] = value
    return value


def _core_result(context: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    component = _ensure_harness(context)
    details = component.get("details")
    result = details.get("v04_result") if isinstance(details, dict) else None
    if component.get("status") != "PASS" or not isinstance(result, dict):
        return None, component.get("message", "v0.4 harness result is unavailable")
    return result, None


def run_v04_four_state_check(context: dict[str, Any]) -> dict[str, Any]:
    """Execute all 66 cases once and emit the canonical three-file evidence set."""
    try:
        return _ensure_harness(context)
    except Exception as exc:  # noqa: BLE001
        return _failure(f"v0.4 four-state check failed closed: {exc.__class__.__name__}")


def run_v04_report_assertions_check(context: dict[str, Any]) -> dict[str, Any]:
    """Audit normalized report rows and every case assertion from the cached run."""
    try:
        result, error = _core_result(context)
        if result is None:
            return _failure("v0.4 report assertions unavailable", {"cause": error})
        cases = result.get("case_results", [])
        issues: list[str] = []
        assertion_count = 0
        report_case_count = 0
        report_result_count = 0
        for case in cases:
            case_id = str(case.get("case_id"))
            assertions = case.get("assertions")
            if not isinstance(assertions, list) or not assertions:
                issues.append(f"{case_id}: assertions unavailable")
                continue
            assertion_count += len(assertions)
            if case.get("program_status") != "SUCCESS" or not all(
                isinstance(item, dict) and item.get("passed") is True
                for item in assertions
            ):
                issues.append(f"{case_id}: one or more oracle assertions failed")
            if case.get("actual_business_status") == "UNTESTABLE":
                if case.get("execution", {}).get("report") is not None:
                    issues.append(f"{case_id}: UNTESTABLE fabricated a report")
                continue
            report_case_count += 1
            report = case.get("execution", {}).get("report")
            rows = report.get("results") if isinstance(report, dict) else None
            if not isinstance(rows, list) or report.get("result_count") != len(rows):
                issues.append(f"{case_id}: normalized report/result count is invalid")
                continue
            report_result_count += len(rows)
            for index, row in enumerate(rows):
                if not isinstance(row, dict) or not _REPORT_FIELDS.issubset(row):
                    issues.append(f"{case_id}: result {index} lacks normalized fields")
        by_id = {case.get("case_id"): case for case in cases if isinstance(case, dict)}
        pc059 = by_id.get("D04-PC059", {})
        pc060 = by_id.get("D04-PC060", {})
        if pc059.get("actual_business_status") != "INAPPLICABLE":
            issues.append("D04-PC059 did not classify as INAPPLICABLE")
        if pc060.get("actual_business_status") != "FAIL":
            issues.append("D04-PC060 did not apply Violation-over-Warning priority")
        if result.get("business_status_counts") != {
            "PASS": 6,
            "FAIL": 53,
            "INAPPLICABLE": 1,
            "UNTESTABLE": 6,
        }:
            issues.append("four-state distribution differs from the reviewed oracle")
    except Exception as exc:  # noqa: BLE001
        return _failure(f"v0.4 report assertion check failed closed: {exc.__class__.__name__}")
    details = {
        "case_count": len(cases),
        "report_case_count": report_case_count,
        "report_result_count": report_result_count,
        "assertion_count": assertion_count,
        "issues": sorted(issues),
    }
    if issues or len(cases) != 66:
        return _failure("v0.4 report assertions failed", details)
    return _success("v0.4 report assertions passed", details)


def run_v04_target_activation_check(context: dict[str, Any]) -> dict[str, Any]:
    """Reject empty-target success and prove the three SPARQL controls executed."""
    try:
        result, error = _core_result(context)
        if result is None:
            return _failure("v0.4 target evidence unavailable", {"cause": error})
        issues: list[str] = []
        checked = 0
        by_id: dict[str, dict[str, Any]] = {}
        for case in result.get("case_results", []):
            if not isinstance(case, dict):
                continue
            case_id = str(case.get("case_id"))
            by_id[case_id] = case
            if case.get("actual_business_status") == "UNTESTABLE":
                continue
            checked += 1
            activation = case.get("execution", {}).get("target_activation")
            if not isinstance(activation, dict):
                issues.append(f"{case_id}: target activation is unavailable")
                continue
            if activation.get("cardinality_target_active") is not True:
                issues.append(f"{case_id}: cardinality target was not active")
            if not isinstance(activation.get("count"), int) or activation["count"] < 1:
                issues.append(f"{case_id}: zero targets were activated")
            if case.get("actual_business_status") == "PASS" and (
                activation.get("dataset_node_count") != 1
                or not isinstance(activation.get("dataset_target_activation_count"), int)
                or activation["dataset_target_activation_count"] < 1
            ):
                issues.append(f"{case_id}: PASS lacks one activated Dataset")
        if by_id.get("D04-PC002", {}).get("actual_business_status") != "FAIL":
            issues.append("D04-PC002 zero-Dataset control did not fail")
        if by_id.get("D04-PC003", {}).get("actual_business_status") != "FAIL":
            issues.append("D04-PC003 two-Dataset control did not fail")
        sparql = result.get("sparql_execution")
        if not isinstance(sparql, dict) or sparql.get("all_executed") is not True:
            issues.append("required cardinality/temporal SPARQL constraints did not execute")
    except Exception as exc:  # noqa: BLE001
        return _failure(f"v0.4 target activation check failed closed: {exc.__class__.__name__}")
    details = {
        "checked_report_cases": checked,
        "untestable_cases": 66 - checked,
        "sparql_execution": result.get("sparql_execution"),
        "issues": sorted(issues),
    }
    if issues or checked != 60:
        return _failure("v0.4 target activation failed", details)
    return _success("v0.4 target activation passed", details)


def _minimal_report(
    *,
    source_shape: str,
    component: str,
    severity: str,
    path: str | None,
    message: str,
    conforms: bool,
) -> Any:
    from rdflib import BNode, Graph, Literal, Namespace, URIRef
    from rdflib.namespace import RDF

    graph = Graph()
    sh = Namespace(SH)
    report = BNode()
    row = BNode()
    graph.add((report, RDF.type, sh.ValidationReport))
    graph.add((report, sh.conforms, Literal(conforms)))
    graph.add((report, sh.result, row))
    graph.add((row, RDF.type, sh.ValidationResult))
    graph.add((row, sh.sourceShape, URIRef(source_shape)))
    graph.add((row, sh.sourceConstraintComponent, URIRef(component)))
    graph.add((row, sh.resultSeverity, URIRef(severity)))
    graph.add((row, sh.focusNode, URIRef("https://example.org/datasets/control")))
    if path is not None:
        graph.add((row, sh.resultPath, URIRef(path)))
    graph.add((row, sh.resultMessage, Literal(message)))
    return graph


def _runtime_control(
    control_id: str,
    passed: bool,
    expected: str,
    actual: str | None,
    planned_case_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "id": control_id,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
        "planned_case_ids": list(planned_case_ids),
    }


def _runtime_negative_controls(
    root: Path,
    manifest: dict[str, Any],
    context: dict[str, Any],
    core_result: dict[str, Any],
) -> dict[str, Any]:
    requirements = json.loads(
        (root / "C_Semantic_Treehouse/manifests/v0.4-requirements.json").read_text(
            encoding="utf-8"
        )
    )
    bindings = build_requirement_bindings(requirements)
    provider = bindings["https://example.org/dssc-energy#ProviderNameShape"]
    message = sorted(provider.messages)[0]
    controls: list[dict[str, Any]] = []

    report_specs = (
        (
            "report.unknown_severity",
            _minimal_report(
                source_shape=provider.source_shape,
                component=sorted(provider.components)[0],
                severity="https://example.org/dssc-energy#Critical",
                path=provider.path,
                message=message,
                conforms=False,
            ),
            "UNKNOWN_SEVERITY",
        ),
        (
            "report.unknown_source_shape",
            _minimal_report(
                source_shape="https://example.org/dssc-energy#UnknownShape",
                component=sorted(provider.components)[0],
                severity=SH + "Violation",
                path=provider.path,
                message=message,
                conforms=False,
            ),
            "UNKNOWN_SOURCE_SHAPE",
        ),
    )
    for control_id, graph, expected_code in report_specs:
        actual_code: str | None = None
        try:
            normalize_shacl_report(graph, bindings)
        except V04ReportError as exc:
            actual_code = exc.code
        controls.append(
            _runtime_control(
                control_id, actual_code == expected_code, expected_code, actual_code
            )
        )

    from rdflib import Graph

    actual_code = None
    try:
        normalize_shacl_report(Graph(), bindings)
    except V04ReportError as exc:
        actual_code = exc.code
    controls.append(
        _runtime_control(
            "report.malformed_graph",
            actual_code == "REPORT_STRUCTURE",
            "REPORT_STRUCTURE",
            actual_code,
        )
    )

    inconsistent = _minimal_report(
        source_shape=provider.source_shape,
        component=sorted(provider.components)[0],
        severity=SH + "Violation",
        path=provider.path,
        message=message,
        conforms=True,
    )
    actual_code = None
    try:
        normalize_shacl_report(inconsistent, bindings)
    except V04ReportError as exc:
        actual_code = exc.code
    controls.append(
        _runtime_control(
            "report.conforms_result_mismatch",
            actual_code == "REPORT_CONFORMS_MISMATCH",
            "REPORT_CONFORMS_MISMATCH",
            actual_code,
        )
    )

    by_id = {
        case.get("case_id"): case
        for case in core_result.get("case_results", [])
        if isinstance(case, dict)
    }
    priority_passed = (
        by_id.get("D04-PC059", {}).get("actual_business_status") == "INAPPLICABLE"
        and by_id.get("D04-PC060", {}).get("actual_business_status") == "FAIL"
    )
    controls.append(
        _runtime_control(
            "classifier.warning_violation_priority",
            priority_passed,
            "PC059=INAPPLICABLE; PC060=FAIL",
            (
                f"PC059={by_id.get('D04-PC059', {}).get('actual_business_status')}; "
                f"PC060={by_id.get('D04-PC060', {}).get('actual_business_status')}"
            ),
        )
    )

    for control_id, mutated, expected_code in (
        (
            "harness.zero_discovery",
            {**copy.deepcopy(manifest), "cases": []},
            "ZERO_TESTS",
        ),
        (
            "harness.required_case_missing",
            {**copy.deepcopy(manifest), "cases": copy.deepcopy(manifest["cases"][:-1])},
            "CASE_SET",
        ),
    ):
        actual_code = None
        try:
            execute_v04_suite(mutated, context)
        except V04HarnessError as exc:
            actual_code = exc.code
        controls.append(
            _runtime_control(
                control_id, actual_code == expected_code, expected_code, actual_code,
                ("D04-PC068",) if control_id == "harness.zero_discovery" else (),
            )
        )

    discovered = len(manifest["cases"])
    for control_id, counts, expected_code in (
        (
            "harness.zero_execution",
            {
                "discovered": discovered,
                "executed": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            },
            "ZERO_EXECUTED",
        ),
        (
            "harness.required_case_skipped",
            {
                "discovered": discovered,
                "executed": discovered - 1,
                "passed": discovered - 1,
                "failed": 0,
                "skipped": 1,
            },
            "REQUIRED_TEST_SKIPPED",
        ),
    ):
        aggregate = evaluate_v04_suite_aggregate(
            counts,
            four_states_present=True,
            coverage_complete=True,
            sparql_all_executed=True,
            failure_boundary_passed=True,
        )
        guard_codes = aggregate.get("guard_codes", [])
        controls.append(
            _runtime_control(
                control_id,
                aggregate.get("program_status") == "ERROR"
                and aggregate.get("exit_code") == 1
                and expected_code in guard_codes,
                f"ERROR/1 with {expected_code}",
                (
                    f"{aggregate.get('program_status')}/{aggregate.get('exit_code')}:"
                    + ",".join(str(item) for item in guard_codes)
                ),
            )
        )

    actual_code = None
    with patch(
        "dssc_validation.v04_harness._parse_shapes",
        side_effect=V04HarnessError(
            "AUTHORITATIVE_SHAPE_PARSE",
            "injected invalid authoritative Shape",
            "AUTHORITY_SHAPE_PREFLIGHT",
        ),
    ):
        try:
            execute_v04_suite(manifest, context)
        except V04HarnessError as exc:
            actual_code = exc.code
    controls.append(
        _runtime_control(
            "preflight.authoritative_shape_failure",
            actual_code == "AUTHORITATIVE_SHAPE_PARSE",
            "AUTHORITATIVE_SHAPE_PARSE",
            actual_code,
            ("D04-PC067",),
        )
    )

    real_version = metadata.version

    def missing_pyshacl(distribution: str) -> str:
        if distribution == "pyshacl":
            raise metadata.PackageNotFoundError(distribution)
        return real_version(distribution)

    actual_code = None
    with patch(
        "dssc_validation.v04_harness.metadata.version",
        side_effect=missing_pyshacl,
    ):
        try:
            execute_v04_suite(manifest, context)
        except V04HarnessError as exc:
            actual_code = exc.code
    controls.append(
        _runtime_control(
            "preflight.core_dependency_failure",
            actual_code == "CORE_DEPENDENCY_MISSING",
            "CORE_DEPENDENCY_MISSING",
            actual_code,
            ("D04-PC070",),
        )
    )

    with patch(
        "dssc_validation.v04_harness.execute_v04_suite",
        side_effect=V04HarnessError(
            "HARNESS_INTERNAL_ERROR",
            "injected harness preflight failure",
            "HARNESS_PREFLIGHT",
        ),
    ):
        disposition = run_v04_harness(manifest, context, write_outputs=False)
    harness_fault_passed = (
        disposition.get("status") == "FAIL"
        and disposition.get("program_status") == "ERROR"
        and disposition.get("details", {}).get("error", {}).get("code")
        == "HARNESS_INTERNAL_ERROR"
        and "v04_result" not in disposition.get("details", {})
    )
    controls.append(
        _runtime_control(
            "preflight.harness_failure",
            harness_fault_passed,
            "ERROR/HARNESS_INTERNAL_ERROR/no business result",
            (
                f"{disposition.get('program_status')}/"
                f"{disposition.get('details', {}).get('error', {}).get('code')}"
            ),
            ("D04-PC069",),
        )
    )

    unready = classify_execution_failure(
        "D04-PC064",
        "VALIDATOR_EXECUTION",
        "VALIDATOR_TIMEOUT",
        authority_preflight_complete=False,
        controlled=True,
    )
    controls.append(
        _runtime_control(
            "fault.allowlisted_before_preflight",
            unready.get("program_status") == "ERROR"
            and unready.get("actual_business_status") is None,
            "ERROR/no business status",
            f"{unready.get('program_status')}/{unready.get('actual_business_status')}",
        )
    )

    controls.sort(key=lambda item: item["id"])
    return {
        "schema": "dssc.v0.4.runtime-controls.v1",
        "program_status": (
            "SUCCESS" if controls and all(item["passed"] for item in controls) else "ERROR"
        ),
        "counts": {
            "discovered": len(controls),
            "executed": len(controls),
            "passed": sum(1 for item in controls if item["passed"]),
            "failed": sum(1 for item in controls if not item["passed"]),
            "skipped": 0,
        },
        "controls": controls,
    }


def _determinism_check(
    root: Path,
    manifest: dict[str, Any],
    context: dict[str, Any],
    first_result: dict[str, Any],
) -> dict[str, Any]:
    payload = execute_v04_suite(manifest, context)
    second_result, _environment = finalize_v04_result(
        root,
        str(context.get("profile")),
        payload,
        required_sources=_REQUIRED_SOURCES,
    )
    first_bytes = json_bytes(first_result)
    second_bytes = json_bytes(second_result)
    record = {
        "schema": "dssc.v0.4.determinism.v1",
        "program_status": (
            "SUCCESS"
            if first_result.get("program_status") == "SUCCESS"
            and second_result.get("program_status") == "SUCCESS"
            and first_bytes == second_bytes
            else "ERROR"
        ),
        "comparison_scope": "normalized results JSON; run-environment excluded",
        "run_1": {
            "sha256": hashlib.sha256(first_bytes).hexdigest(),
            "size": len(first_bytes),
        },
        "run_2": {
            "sha256": hashlib.sha256(second_bytes).hexdigest(),
            "size": len(second_bytes),
        },
        "byte_identical": first_bytes == second_bytes,
    }
    _write_phase05_json(root, _DETERMINISM_RELPATH, record)
    return record


def run_v04_fault_injection_check(context: dict[str, Any]) -> dict[str, Any]:
    """Run all contract/report/preflight controls and deterministic core rerun."""
    try:
        root = _root(context)
        result, error = _core_result(context)
        if result is None:
            return _failure("v0.4 fault controls unavailable", {"cause": error})
        validation = _manifest_validation(context, verify_fixture_hashes=True)
        if not validation.ok or validation.manifest is None:
            return _failure("v0.4 fault controls require a valid canonical manifest")
        manifest = validation.manifest
        contract = run_v04_contract_controls(root, manifest)
        boundary = run_failure_boundary_self_tests()
        runtime = _runtime_negative_controls(root, manifest, context, result)
        determinism = _determinism_check(root, manifest, context, result)

        planned_ids = ("D04-PC067", "D04-PC068", "D04-PC069", "D04-PC070")
        control_ids_by_case = {
            case_id: sorted(
                {
                    *contract.get("planned_case_coverage", {})
                    .get("control_ids_by_planned_case", {})
                    .get(case_id, []),
                    *[
                        item["id"]
                        for item in runtime.get("controls", [])
                        if case_id in item.get("planned_case_ids", [])
                    ],
                }
            )
            for case_id in planned_ids
        }
        covered = sorted(
            case_id for case_id, control_ids in control_ids_by_case.items() if control_ids
        )
        pending = sorted(set(planned_ids) - set(covered))
        planned_coverage = {
            "authority_program_error_case_ids": list(planned_ids),
            "covered": covered,
            "pending": pending,
            "control_ids_by_planned_case": control_ids_by_case,
        }
        successful = (
            contract.get("program_status") == "SUCCESS"
            and contract.get("counts", {}).get("skipped") == 0
            and boundary.get("all_passed") is True
            and boundary.get("skipped") == 0
            and runtime.get("program_status") == "SUCCESS"
            and runtime.get("counts", {}).get("skipped") == 0
            and determinism.get("program_status") == "SUCCESS"
            and not pending
        )
        evidence = {
            "schema": "dssc.v0.4.negative-controls.v1",
            "program_status": "SUCCESS" if successful else "ERROR",
            "groups": {
                "manifest_and_registry": contract,
                "failure_boundary": boundary,
                "runtime_and_report": runtime,
            },
            "planned_case_coverage": planned_coverage,
            "determinism_evidence": _DETERMINISM_RELPATH,
        }
        _write_phase05_json(root, _NEGATIVE_CONTROLS_RELPATH, evidence)
    except Exception as exc:  # noqa: BLE001
        return _failure(f"v0.4 fault-injection check failed closed: {exc.__class__.__name__}")
    details = {
        "contract_control_counts": contract.get("counts"),
        "runtime_control_counts": runtime.get("counts"),
        "failure_boundary_counts": {
            key: boundary.get(key)
            for key in ("discovered", "executed", "passed", "failed", "skipped")
        },
        "planned_case_coverage": planned_coverage,
        "determinism": determinism,
        "evidence_files": [
            _NEGATIVE_CONTROLS_RELPATH,
            _DETERMINISM_RELPATH,
        ],
    }
    if not successful:
        return _failure("v0.4 fault-injection controls failed", details)
    return _success("v0.4 fault-injection controls passed", details)


__all__ = [
    "run_v04_fault_injection_check",
    "run_v04_fixture_hashes_check",
    "run_v04_four_state_check",
    "run_v04_manifest_semantics_check",
    "run_v04_report_assertions_check",
    "run_v04_target_activation_check",
    "run_v04_test_case_schema_check",
]
