"""Deterministic v0.4 case-oracle assertions.

This module contains no validator invocation and never changes expected data.
It compares one normalized execution record with the already validated test
case manifest and returns explicit, machine-readable assertions.
"""

from __future__ import annotations

from typing import Any, Mapping

from dssc_validation.v04_classifier import expand_iri, mapped_requirement_ids


class V04OracleError(RuntimeError):
    """The test oracle itself is structurally unusable."""


def _assertion(
    assertion_id: str,
    passed: bool,
    expected: Any,
    actual: Any,
) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
    }


def _count_matches(expected: Mapping[str, Any], actual: int) -> bool:
    if not isinstance(actual, int) or actual < 0:
        return False
    if "exact" in expected and actual != expected["exact"]:
        return False
    if "minimum" in expected and actual < expected["minimum"]:
        return False
    if "maximum" in expected and actual > expected["maximum"]:
        return False
    return any(key in expected for key in ("exact", "minimum", "maximum"))


def _term_matches(expected: Mapping[str, Any], actual: Any) -> bool:
    if not isinstance(actual, dict):
        return False
    term_type = expected.get("term_type")
    if term_type != actual.get("term_type"):
        return False
    if term_type == "IRI":
        value = expected.get("value")
        return isinstance(value, str) and expand_iri(value) == actual.get("value")
    if term_type == "BNODE":
        return expected.get("match") == "ANY" and actual.get("match") == "ANY"
    if term_type == "LITERAL":
        if expected.get("lexical_form") != actual.get("lexical_form"):
            return False
        if "datatype" in expected:
            datatype = expected.get("datatype")
            return (
                isinstance(datatype, str)
                and expand_iri(datatype) == actual.get("datatype")
                and "language" not in actual
            )
        if "language" in expected:
            return (
                expected.get("language") == actual.get("language")
                and "datatype" not in actual
            )
        return "datatype" not in actual and "language" not in actual
    return False


def _message_matches(expected: Mapping[str, Any], actual: Any) -> bool:
    if not isinstance(actual, str) or not actual:
        return False
    policy = expected.get("policy")
    if policy == "PRESENT":
        return True
    if policy == "EXACT":
        return actual == expected.get("value")
    raise V04OracleError(f"unknown message policy: {policy!r}")


def _result_matches(expected: Mapping[str, Any], actual: Mapping[str, Any]) -> bool:
    source_shape = expected.get("source_shape")
    component = expected.get("source_constraint_component")
    severity = expected.get("severity")
    requirement_id = expected.get("requirement_id")
    if not all(
        isinstance(value, str)
        for value in (source_shape, component, severity, requirement_id)
    ):
        raise V04OracleError("expected result identity fields are incomplete")
    if actual.get("requirement_id") != requirement_id:
        return False
    if actual.get("source_shape") != expand_iri(source_shape):
        return False
    if actual.get("source_constraint_component") != expand_iri(component):
        return False
    if actual.get("severity") != expand_iri(severity):
        return False
    if "result_path" in expected:
        expected_path = expected.get("result_path")
        if not isinstance(expected_path, str) or actual.get("result_path") != expand_iri(
            expected_path
        ):
            return False
    elif actual.get("result_path") is not None:
        # Omitting result_path is an assertion that this is a node/SPARQL
        # result without a path, not a wildcard over arbitrary paths.
        return False
    message = expected.get("message")
    if not isinstance(message, dict) or not _message_matches(message, actual.get("message")):
        return False
    if "focus_node" in expected:
        focus = expected.get("focus_node")
        if not isinstance(focus, dict) or not _term_matches(
            focus, actual.get("focus_node")
        ):
            return False
    if "value" in expected:
        value = expected.get("value")
        if not isinstance(value, dict) or not _term_matches(value, actual.get("value")):
            return False
    return True


def _report_assertions(
    case_id: str,
    case: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> list[dict[str, Any]]:
    oracle = case.get("oracle")
    report = execution.get("report")
    activation = execution.get("target_activation")
    if not isinstance(oracle, dict) or not isinstance(report, dict):
        raise V04OracleError("report oracle/execution is unavailable")
    if not isinstance(activation, dict):
        raise V04OracleError("target activation evidence is unavailable")
    assertions: list[dict[str, Any]] = []
    expected_minimum = oracle.get("expected_target_activation_minimum")
    actual_activation = activation.get("count")
    assertions.append(
        _assertion(
            f"{case_id}.target-activation-minimum",
            isinstance(expected_minimum, int)
            and isinstance(actual_activation, int)
            and actual_activation >= expected_minimum,
            {"minimum": expected_minimum},
            actual_activation,
        )
    )
    assertions.append(
        _assertion(
            f"{case_id}.cardinality-target-active",
            activation.get("cardinality_target_active") is True,
            True,
            activation.get("cardinality_target_active"),
        )
    )
    if case.get("expected_business_status") == "PASS":
        assertions.extend(
            [
                _assertion(
                    f"{case_id}.pass-one-dataset",
                    activation.get("dataset_node_count") == 1,
                    1,
                    activation.get("dataset_node_count"),
                ),
                _assertion(
                    f"{case_id}.pass-dataset-shape-target",
                    isinstance(activation.get("dataset_target_activation_count"), int)
                    and activation["dataset_target_activation_count"] > 0,
                    {"minimum": 1},
                    activation.get("dataset_target_activation_count"),
                ),
            ]
        )

    expected_count = oracle.get("result_count")
    actual_results = report.get("results")
    if not isinstance(expected_count, dict) or not isinstance(actual_results, list):
        raise V04OracleError("result-count oracle/execution is unavailable")
    assertions.append(
        _assertion(
            f"{case_id}.result-count",
            _count_matches(expected_count, len(actual_results)),
            dict(expected_count),
            len(actual_results),
        )
    )

    expected_results = oracle.get("expected_results", [])
    if not isinstance(expected_results, list):
        raise V04OracleError("expected_results must be an array")
    coverage = [False] * len(actual_results)
    for index, expected_result in enumerate(expected_results):
        if not isinstance(expected_result, dict):
            raise V04OracleError("expected result must be an object")
        matcher_id = expected_result.get("assertion_id")
        if not isinstance(matcher_id, str) or not matcher_id:
            matcher_id = f"{case_id}.expected-result-{index + 1:02d}"
        matches: list[int] = []
        for actual_index, actual_result in enumerate(actual_results):
            if isinstance(actual_result, dict) and _result_matches(
                expected_result, actual_result
            ):
                matches.append(actual_index)
                coverage[actual_index] = True
        expected_matches = expected_result.get("count")
        if not isinstance(expected_matches, dict):
            raise V04OracleError("expected result count must be an object")
        assertions.append(
            _assertion(
                matcher_id,
                _count_matches(expected_matches, len(matches)),
                dict(expected_matches),
                len(matches),
            )
        )
    assertions.append(
        _assertion(
            f"{case_id}.all-report-results-asserted",
            all(coverage),
            len(actual_results),
            sum(1 for item in coverage if item),
        )
    )
    case_requirements = case.get("requirement_ids")
    actual_requirements = mapped_requirement_ids(actual_results)
    assertions.append(
        _assertion(
            f"{case_id}.result-requirement-scope",
            isinstance(case_requirements, list)
            and set(actual_requirements).issubset(set(case_requirements)),
            sorted(case_requirements) if isinstance(case_requirements, list) else [],
            actual_requirements,
        )
    )
    return assertions


def assert_case_oracle(
    case: Mapping[str, Any], execution: Mapping[str, Any]
) -> dict[str, Any]:
    """Return the normalized case result and separate program status."""
    case_id = case.get("case_id")
    expected_status = case.get("expected_business_status")
    actual_status = execution.get("actual_business_status")
    if not isinstance(case_id, str) or expected_status not in {
        "PASS",
        "FAIL",
        "INAPPLICABLE",
        "UNTESTABLE",
    }:
        raise V04OracleError("case identity/status is invalid")
    assertions = [
        _assertion(
            f"{case_id}.business-status",
            actual_status == expected_status,
            expected_status,
            actual_status,
        )
    ]
    if expected_status == "UNTESTABLE":
        oracle = case.get("oracle")
        if not isinstance(oracle, dict):
            raise V04OracleError("UNTESTABLE oracle is unavailable")
        assertions.extend(
            [
                _assertion(
                    f"{case_id}.failure-stage",
                    execution.get("failure_stage") == oracle.get("failure_stage"),
                    oracle.get("failure_stage"),
                    execution.get("failure_stage"),
                ),
                _assertion(
                    f"{case_id}.reason-code",
                    execution.get("reason_code") == oracle.get("reason_code"),
                    oracle.get("reason_code"),
                    execution.get("reason_code"),
                ),
                _assertion(
                    f"{case_id}.no-fabricated-report",
                    execution.get("report") is None,
                    None,
                    execution.get("report"),
                ),
            ]
        )
        if oracle.get("failure_stage") == "VALIDATOR_EXECUTION":
            assertions.extend(
                [
                    _assertion(
                        f"{case_id}.preflight-complete-before-fault",
                        execution.get("preflight_complete") is True,
                        True,
                        execution.get("preflight_complete"),
                    ),
                    _assertion(
                        f"{case_id}.preflight-evidence-before-fault",
                        isinstance(execution.get("completed_preflights"), dict)
                        and all(
                            execution["completed_preflights"].get(name) is True
                            for name in (
                                "authority",
                                "dependency",
                                "shape",
                                "manifest",
                                "fixture_hash",
                                "sut_parse",
                            )
                        ),
                        {
                            name: True
                            for name in (
                                "authority",
                                "dependency",
                                "shape",
                                "manifest",
                                "fixture_hash",
                                "sut_parse",
                            )
                        },
                        execution.get("completed_preflights"),
                    ),
                ]
            )
    else:
        assertions.extend(_report_assertions(case_id, case, execution))
    passed = all(assertion["passed"] for assertion in assertions)
    return {
        "case_id": case_id,
        "fixture_path": case.get("fixture", {}).get("path")
        if isinstance(case.get("fixture"), dict)
        else None,
        "requirement_ids": list(case.get("requirement_ids", [])),
        "expected_business_status": expected_status,
        "actual_business_status": actual_status,
        "assertions": assertions,
        "program_status": "SUCCESS" if passed else "ERROR",
        "passed": passed,
        "execution": dict(execution),
    }


def error_case_result(
    case: Mapping[str, Any], code: str, message: str
) -> dict[str, Any]:
    """Represent an unexpected harness/authority failure without UNTESTABLE."""
    case_id = str(case.get("case_id", "<unknown>"))
    return {
        "case_id": case_id,
        "fixture_path": case.get("fixture", {}).get("path")
        if isinstance(case.get("fixture"), dict)
        else None,
        "requirement_ids": list(case.get("requirement_ids", [])),
        "expected_business_status": case.get("expected_business_status"),
        "actual_business_status": None,
        "assertions": [
            _assertion(f"{case_id}.program-error", False, "SUCCESS", code)
        ],
        "program_status": "ERROR",
        "passed": False,
        "execution": {"error": {"code": code, "message": message}},
    }


__all__ = [
    "V04OracleError",
    "assert_case_oracle",
    "error_case_result",
]
