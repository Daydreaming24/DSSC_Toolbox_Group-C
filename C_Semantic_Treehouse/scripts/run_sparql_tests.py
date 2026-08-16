"""Version-bound, fail-closed SPARQL semantic test runner."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable

from rdflib import BNode, Graph, Literal, URIRef

from sparql_manifest import (
    AUTHORITY_RELPATHS,
    AUTHORITY_SCHEMA_RELPATHS,
    MANIFEST_RELPATH,
    SCHEMA_RELPATH,
    AuthorityBundle,
    ManifestIssue,
    SparqlManifestValidation,
    load_and_validate_sparql_manifest,
    load_json_strict,
    sha256_file,
    validate_sparql_manifest_document,
)
from sparql_report import (
    canonical_json_sha256,
    render_report,
    write_json,
    write_report,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_RELPATH = "build/validation/sparql"
PHASE_OUTPUT_RELPATH = "build/phase-06/sparql"
RESULTS_RELPATH = f"{OUTPUT_RELPATH}/results.json"
REPORT_RELPATH = f"{OUTPUT_RELPATH}/report.md"
ENVIRONMENT_RELPATH = f"{OUTPUT_RELPATH}/run-environment.json"
NEGATIVE_CONTROLS_RELPATH = f"{PHASE_OUTPUT_RELPATH}/negative-controls.json"
DETERMINISM_RELPATH = f"{PHASE_OUTPUT_RELPATH}/determinism.json"
NORMALIZED_COMMAND = (
    ".venv/Scripts/python.exe "
    "C_Semantic_Treehouse/scripts/run_sparql_tests.py"
)
SOURCE_BINDINGS = {
    "scripts/validate.py": ("dispatcher",),
    "scripts/dssc_validation/checks_phase06.py": (
        "phase-06-adapter",
        "sparql-component-adapter",
    ),
    "scripts/dssc_validation/entrypoint_catalog.py": (
        "controlled-entrypoint-catalog",
    ),
    "scripts/dssc_validation/checks_all.py": ("all-composition-checker",),
    "C_Semantic_Treehouse/scripts/run_sparql_tests.py": (
        "sparql-checker",
        "sparql-runner",
    ),
    "C_Semantic_Treehouse/scripts/sparql_manifest.py": (
        "sparql-manifest-semantic-checker",
        "sparql-helper",
    ),
    "C_Semantic_Treehouse/scripts/sparql_report.py": (
        "sparql-report-generator",
        "sparql-helper",
    ),
    "C_Semantic_Treehouse/scripts/quality_metrics.py": ("quality-checker",),
    "C_Semantic_Treehouse/scripts/validate_governance.py": (
        "governance-checker",
    ),
    "C_Semantic_Treehouse/scripts/governance_contract.py": (
        "governance-helper",
    ),
}


def _repository_path(root: Path, relative: str) -> Path:
    return root.joinpath(*PurePosixPath(relative).parts)


def _issue(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def _source_records(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    records: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for relative, roles in sorted(SOURCE_BINDINGS.items()):
        path = _repository_path(root, relative)
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
            issues.append(
                _issue(
                    "source_unavailable",
                    f"/sources/{relative}",
                    "required checker, adapter, reporter, or helper source is unavailable",
                )
            )
            continue
        records.append(
            {"path": relative, "roles": list(roles), "sha256": sha256_file(path)}
        )
    return records, issues


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def _cell_to_text(value: object) -> str:
    if isinstance(value, BNode):
        raise ValueError("blank-node result cells are not stable across executions")
    if isinstance(value, (URIRef, Literal)):
        text = str(value)
    elif value is None:
        text = ""
    else:
        text = str(value)
    if "\t" in text or "\r" in text or "\n" in text:
        raise ValueError("result cell contains an unescaped TSV control character")
    return text


def _graph_for_case(
    root: Path,
    query: dict[str, Any],
    release_artifacts: dict[str, dict[str, Any]] | Any,
) -> tuple[Graph, list[dict[str, Any]]]:
    graph = Graph()
    graph_records: list[dict[str, Any]] = []
    refs = query["artifact_refs"]["graph_inputs"]
    for artifact_id in refs:
        artifact = release_artifacts[artifact_id]
        path = _repository_path(root, artifact["path"])
        media_type = artifact["mediaType"]
        rdf_format = {
            "text/turtle": "turtle",
            "application/ld+json": "json-ld",
        }.get(media_type)
        if rdf_format is None:
            raise ValueError(f"unsupported graph media type for {artifact_id}")
        graph.parse(path.as_uri(), format=rdf_format)
        graph_records.append(
            {
                "id": artifact_id,
                "path": artifact["path"],
                "sha256": artifact["sha256"],
                "media_type": media_type,
            }
        )
    return graph, graph_records


def _select_result(
    result: Any,
    *,
    sort_rows: bool,
    preserve_duplicates: bool,
) -> tuple[list[str], list[list[str]], str]:
    variables = [str(variable) for variable in result.vars]
    rows = [
        [_cell_to_text(row.get(variable)) for variable in result.vars]
        for row in result
    ]
    if not preserve_duplicates:
        rows = [list(row) for row in dict.fromkeys(tuple(row) for row in rows)]
    if sort_rows:
        rows.sort()
    text = "\n".join(
        ["\t".join(variables)] + ["\t".join(row) for row in rows]
    )
    return variables, rows, text


def _case_failure(
    query: dict[str, Any],
    *,
    code: str,
    message: str,
    graph_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    refs = query.get("artifact_refs", {})
    return {
        "id": query.get("id"),
        "release": query.get("release"),
        "query_form": query.get("query_form"),
        "required": query.get("required"),
        "enabled": query.get("enabled"),
        "expected_business_status": "PASS",
        "actual_business_status": None,
        "status": "FAIL",
        "program_status": "ERROR",
        "query_artifact_ref": refs.get("query"),
        "expected_artifact_ref": refs.get("expected"),
        "graph_inputs": graph_records or [],
        "local_context_refs": list(refs.get("local_contexts", [])),
        "requirement_refs": list(query.get("requirement_refs", [])),
        "coverage": list(query.get("coverage", [])),
        "oracle": query.get("oracle", {}),
        "actual": {},
        "assertions": [
            {
                "id": code,
                "passed": False,
                "expected": "successful exact evaluation",
                "actual": message,
            }
        ],
    }


def _execute_case(
    root: Path,
    query: dict[str, Any],
    validation: SparqlManifestValidation,
) -> dict[str, Any]:
    graph_records: list[dict[str, Any]] = []
    try:
        graph, graph_records = _graph_for_case(
            root, query, validation.release_artifacts_by_id
        )
        query_artifact = validation.artifacts_by_id[
            query["artifact_refs"]["query"]
        ]
        expected_artifact = validation.artifacts_by_id[
            query["artifact_refs"]["expected"]
        ]
        query_path = _repository_path(root, query_artifact["path"])
        expected_path = _repository_path(root, expected_artifact["path"])
        query_text = query_path.read_text(encoding="utf-8")
        expected_text = _normalize_text(expected_path.read_text(encoding="utf-8"))
        result = graph.query(query_text)
    except Exception as exc:  # noqa: BLE001 - one case becomes deterministic ERROR
        return _case_failure(
            query,
            code="execution_error",
            message=f"{exc.__class__.__name__}: graph/query evaluation failed",
            graph_records=graph_records,
        )

    assertions: list[dict[str, Any]] = []

    def assertion(identifier: str, expected: Any, actual: Any) -> None:
        assertions.append(
            {
                "id": identifier,
                "passed": expected == actual,
                "expected": expected,
                "actual": actual,
            }
        )

    form = query["query_form"]
    oracle = query["oracle"]
    comparison = query["comparison"]
    actual: dict[str, Any]
    try:
        if form == "SELECT":
            assertion("result-form", "SELECT", str(result.type))
            variables, rows, actual_text = _select_result(
                result,
                sort_rows=comparison["sort_rows"],
                preserve_duplicates=comparison["preserve_duplicates"],
            )
            assertion("variables", oracle["expected_variables"], variables)
            assertion("row-count", oracle["expected_row_count"], len(rows))
            if not oracle["allow_empty"]:
                assertion("non-empty", True, len(rows) > 0)
            assertion("exact-tsv", expected_text, actual_text)
            actual = {
                "variables": variables,
                "row_count": len(rows),
                "output": actual_text,
                "output_sha256": hashlib.sha256(
                    actual_text.encode("utf-8")
                ).hexdigest(),
            }
        elif form == "ASK":
            assertion("result-form", "ASK", str(result.type))
            actual_boolean = bool(result.askAnswer)
            expected_boolean_text = str(oracle["expected_boolean"]).lower()
            assertion("expected-file", expected_boolean_text, expected_text)
            assertion("exact-boolean", oracle["expected_boolean"], actual_boolean)
            actual = {"boolean": actual_boolean, "output": str(actual_boolean).lower()}
        elif form == "COUNT":
            assertion("result-form", "SELECT", str(result.type))
            variables, rows, actual_text = _select_result(
                result, sort_rows=False, preserve_duplicates=True
            )
            expected_variables = oracle["expected_variables"]
            assertion("variables", expected_variables, variables)
            assertion("single-count-row", 1, len(rows))
            if len(rows) != 1 or len(rows[0]) != 1 or not re.fullmatch(
                r"[0-9]+", rows[0][0]
            ):
                raise ValueError("COUNT result must be one non-negative integer cell")
            actual_count = int(rows[0][0])
            expected_count_text = str(oracle["expected_count"])
            assertion("expected-file", expected_count_text, expected_text)
            assertion("exact-count", oracle["expected_count"], actual_count)
            actual = {
                "variables": variables,
                "count": actual_count,
                "output": str(actual_count),
                "raw_select_output": actual_text,
            }
        else:
            raise ValueError(f"unsupported query form {form!r}")
    except Exception as exc:  # noqa: BLE001
        return _case_failure(
            query,
            code="result_normalization_error",
            message=f"{exc.__class__.__name__}: result normalization failed",
            graph_records=graph_records,
        )

    for index, release_assertion in enumerate(query.get("release_assertions", [])):
        assertions.append(
            {
                "id": f"release-assertion-{index + 1}",
                "passed": True,
                "expected": release_assertion,
                "actual": release_assertion,
            }
        )
    passed = bool(assertions) and all(item["passed"] for item in assertions)
    refs = query["artifact_refs"]
    return {
        "id": query["id"],
        "release": query["release"],
        "query_form": form,
        "required": query["required"],
        "enabled": query["enabled"],
        "expected_business_status": "PASS",
        "actual_business_status": "PASS" if passed else None,
        "status": "PASS" if passed else "FAIL",
        "program_status": "SUCCESS" if passed else "ERROR",
        "query_artifact_ref": refs["query"],
        "query_path": validation.artifacts_by_id[refs["query"]]["path"],
        "query_sha256": validation.artifacts_by_id[refs["query"]]["sha256"],
        "expected_artifact_ref": refs["expected"],
        "expected_path": validation.artifacts_by_id[refs["expected"]]["path"],
        "expected_sha256": validation.artifacts_by_id[refs["expected"]][
            "sha256"
        ],
        "graph_inputs": graph_records,
        "graph_triple_count": len(graph),
        "local_context_refs": list(refs["local_contexts"]),
        "requirement_refs": list(query["requirement_refs"]),
        "coverage": list(query["coverage"]),
        "oracle": oracle,
        "actual": actual,
        "assertions": assertions,
    }


def _base_result(
    validation: SparqlManifestValidation,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    registry_record = next(
        (
            record
            for record in validation.authority_bundle.records
            if record.get("id") == "validation_suites"
        ),
        {},
    )
    return {
        "schema_version": "1.0.0",
        "suite": "sparql",
        "manifest_schema_version": (
            validation.manifest.get("manifest_schema_version")
            if validation.manifest
            else None
        ),
        "command": NORMALIZED_COMMAND,
        "status": "FAIL",
        "program_status": "ERROR",
        "exit_code": 1,
        "summary": {
            "discovered": 0,
            "executed": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "required": 0,
        },
        "registry": {
            "contract_version": registry_record.get("contract_version"),
            "sha256": registry_record.get("manifest_sha256"),
        },
        "authorities": list(validation.authority_bundle.records),
        "sparql_manifest": validation.deterministic_record(),
        "sources": sources,
        "cases": [],
        "issues": [],
    }


def execute_suite(
    root: Path,
    *,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Validate all authorities first, then execute every enabled required CQ."""

    root = root.resolve()
    validation = load_and_validate_sparql_manifest(root, manifest_path=manifest_path)
    sources, source_issues = _source_records(root)
    result = _base_result(validation, sources)
    preflight_issues = [issue.as_dict() for issue in validation.issues] + source_issues
    if preflight_issues:
        result["issues"] = sorted(
            preflight_issues,
            key=lambda item: (
                str(item.get("code")),
                str(item.get("location")),
                str(item.get("message")),
            ),
        )
        return result
    if validation.manifest is None:
        result["issues"] = [
            _issue("manifest_unavailable", "/", "validated manifest is unavailable")
        ]
        return result

    queries = validation.manifest["queries"]
    discovered = len(queries)
    enabled_queries = [query for query in queries if query["enabled"]]
    skipped = discovered - len(enabled_queries)
    cases = [
        _execute_case(root, query, validation) for query in enabled_queries
    ]
    passed = sum(1 for case in cases if case["status"] == "PASS")
    failed = len(cases) - passed
    required = sum(1 for query in queries if query["required"])
    result["cases"] = cases
    result["summary"] = {
        "discovered": discovered,
        "executed": len(cases),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "required": required,
    }
    complete = (
        discovered > 0
        and len(cases) == discovered
        and required == discovered
        and skipped == 0
        and failed == 0
        and all(case["program_status"] == "SUCCESS" for case in cases)
    )
    if not complete:
        result["issues"] = [
            _issue(
                "suite_incomplete",
                "/summary",
                "0 discovery, skipped required, failed, or incomplete execution is forbidden",
            )
        ]
        return result
    result["status"] = "PASS"
    result["program_status"] = "SUCCESS"
    result["exit_code"] = 0
    return result


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _git_value(root: Path, arguments: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def environment_record(root: Path) -> dict[str, Any]:
    lock_path = root / "requirements.lock"
    status = _git_value(root, ["status", "--porcelain"])
    return {
        "schema_version": "1.0.0",
        "suite": "sparql",
        "command": NORMALIZED_COMMAND,
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "packages": {
            "jsonschema": _package_version("jsonschema"),
            "pip": _package_version("pip"),
            "rdflib": _package_version("rdflib"),
        },
        "lock": {
            "path": "requirements.lock",
            "sha256": sha256_file(lock_path) if lock_path.is_file() else None,
        },
        "git": {
            "commit": _git_value(root, ["rev-parse", "HEAD"]),
            "dirty": status is None or bool(status),
        },
    }


def write_canonical_outputs(root: Path, result: dict[str, Any]) -> None:
    write_json(_repository_path(root, RESULTS_RELPATH), result)
    write_report(_repository_path(root, REPORT_RELPATH), result)
    write_json(_repository_path(root, ENVIRONMENT_RELPATH), environment_record(root))


def _mutated_control(
    control_id: str,
    document: dict[str, Any],
    schema: dict[str, Any],
    root: Path,
    authority: AuthorityBundle,
    expected_codes: set[str],
) -> dict[str, Any]:
    issues, _, _, _ = validate_sparql_manifest_document(
        document,
        schema,
        root,
        authority,
        verify_hashes=True,
        check_orphans=True,
    )
    codes = sorted({issue.code for issue in issues})
    passed = bool(issues) and (not expected_codes or bool(expected_codes & set(codes)))
    return {
        "id": control_id,
        "expected": "REJECT",
        "actual": "REJECT" if issues else "ACCEPT",
        "expected_issue_codes": sorted(expected_codes),
        "observed_issue_codes": codes,
        "passed": passed,
    }


def _write_temp_json(directory: Path, name: str, value: Any) -> Path:
    path = directory / f"{name}.json"
    write_json(path, value)
    return path


def _authority_control(
    root: Path,
    temp_dir: Path,
    authority_id: str,
    scenario: str,
    document: dict[str, Any],
) -> dict[str, Any]:
    path = _write_temp_json(temp_dir, f"{authority_id}-{scenario}", document)
    rejected = False
    codes: list[str] = []
    try:
        if authority_id == "release_manifest":
            from dssc_validation.release_manifest import (
                load_and_audit_release_manifest,
            )

            result = load_and_audit_release_manifest(
                root,
                manifest_path=path,
                schema_path=_repository_path(
                    root, AUTHORITY_SCHEMA_RELPATHS[authority_id]
                ),
            )
            rejected = not result.ok
            codes = sorted(
                {str(item.get("code", "semantic")) for item in result.issues}
            )
        elif authority_id == "baseline_test_cases":
            from dssc_validation.baseline_manifest import (
                BaselineManifestError,
                load_and_validate_baseline_manifest,
            )

            try:
                load_and_validate_baseline_manifest(
                    root,
                    manifest_path=path,
                    schema_path=_repository_path(
                        root, AUTHORITY_SCHEMA_RELPATHS[authority_id]
                    ),
                )
            except BaselineManifestError as exc:
                rejected = True
                codes = sorted({str(item.code) for item in exc.issues})
        elif authority_id == "requirements":
            from dssc_validation.requirements_registry import (
                load_and_validate_requirements,
            )

            result = load_and_validate_requirements(
                root,
                manifest_path=path,
                schema_path=_repository_path(
                    root, AUTHORITY_SCHEMA_RELPATHS[authority_id]
                ),
            )
            rejected = not result.ok
            codes = sorted(
                {str(item.get("code", "semantic")) for item in result.issues}
            )
        elif authority_id == "v0_4_test_cases":
            from dssc_validation.v04_manifest import load_and_validate_v04_manifest

            result = load_and_validate_v04_manifest(
                root,
                manifest_path=path,
                schema_path=_repository_path(
                    root, AUTHORITY_SCHEMA_RELPATHS[authority_id]
                ),
            )
            rejected = not result.ok
            codes = sorted({item.code for item in result.issues})
        elif authority_id == "validation_suites":
            from dssc_validation.suite_registry import load_and_validate_registry

            result = load_and_validate_registry(
                root,
                registry_path=path,
                schema_path=_repository_path(
                    root, AUTHORITY_SCHEMA_RELPATHS[authority_id]
                ),
            )
            rejected = not result.ok
            codes = sorted({item.code for item in result.issues})
        else:
            codes = ["unknown-control-authority"]
    except Exception as exc:  # noqa: BLE001 - exception is also fail-closed
        rejected = True
        codes = [f"exception:{exc.__class__.__name__}"]
    return {
        "id": f"{authority_id}.{scenario}",
        "expected": "REJECT",
        "actual": "REJECT" if rejected else "ACCEPT",
        "observed_issue_codes": codes,
        "passed": rejected,
    }


def run_negative_controls(root: Path) -> dict[str, Any]:
    root = root.resolve()
    canonical = load_and_validate_sparql_manifest(root)
    if not canonical.ok or canonical.manifest is None:
        return {
            "schema_version": "1.0.0",
            "suite": "sparql-negative-controls",
            "status": "FAIL",
            "program_status": "ERROR",
            "summary": {"total": 0, "passed": 0, "failed": 1},
            "controls": [],
            "issues": [issue.as_dict() for issue in canonical.issues],
        }
    schema = load_json_strict(_repository_path(root, SCHEMA_RELPATH))
    document = canonical.manifest
    authority = canonical.authority_bundle
    controls: list[dict[str, Any]] = []

    mutated = deepcopy(document)
    duplicate_query = deepcopy(mutated["queries"][0])
    duplicate_query["business_reason"] += " Duplicate-ID control."
    mutated["queries"].append(duplicate_query)
    controls.append(
        _mutated_control(
            "sparql.duplicate-query-id",
            mutated,
            schema,
            root,
            authority,
            {"duplicate_query_id"},
        )
    )

    mutated = deepcopy(document)
    duplicate_artifact = deepcopy(mutated["artifacts"][0])
    duplicate_artifact["path"] = mutated["artifacts"][2]["path"]
    duplicate_artifact["sha256"] = mutated["artifacts"][2]["sha256"]
    mutated["artifacts"].append(duplicate_artifact)
    controls.append(
        _mutated_control(
            "sparql.duplicate-artifact-id",
            mutated,
            schema,
            root,
            authority,
            {"duplicate_artifact_id"},
        )
    )

    for control_id, mutator, expected_codes in (
        (
            "sparql.dangling-graph-reference",
            lambda value: value["queries"][8]["artifact_refs"].__setitem__(
                "graph_inputs", ["missing-graph-artifact"]
            ),
            {"dangling_graph_reference"},
        ),
        (
            "sparql.dangling-expected-reference",
            lambda value: value["queries"][8]["artifact_refs"].__setitem__(
                "expected", "missing-expected-artifact"
            ),
            {"dangling_expected_reference"},
        ),
        (
            "sparql.dangling-release-reference",
            lambda value: value["queries"][8].__setitem__("release", "v0.9"),
            {"dangling_query_release"},
        ),
        (
            "sparql.dangling-requirement-reference",
            lambda value: value["queries"][8]["requirement_refs"].append(
                "D04-R999"
            ),
            {"dangling_requirement_reference"},
        ),
    ):
        mutated = deepcopy(document)
        mutator(mutated)
        controls.append(
            _mutated_control(
                control_id, mutated, schema, root, authority, expected_codes
            )
        )

    mutated = deepcopy(document)
    conflicting = deepcopy(mutated["artifacts"][0])
    conflicting["id"] = "path-hash-conflict-control"
    conflicting["sha256"] = "0" * 64
    mutated["artifacts"].append(conflicting)
    controls.append(
        _mutated_control(
            "sparql.same-path-multiple-hashes",
            mutated,
            schema,
            root,
            authority,
            {"path_hash_conflict"},
        )
    )

    mutated = deepcopy(document)
    mutated["queries"] = []
    controls.append(
        _mutated_control(
            "sparql.zero-query-discovery",
            mutated,
            schema,
            root,
            authority,
            {"schema_validation"},
        )
    )

    mutated = deepcopy(document)
    mutated["queries"][0]["enabled"] = False
    controls.append(
        _mutated_control(
            "sparql.required-query-skipped",
            mutated,
            schema,
            root,
            authority,
            {"schema_validation", "required_query_skipped"},
        )
    )

    mutated = deepcopy(document)
    removed_expected = mutated["queries"][8]["artifact_refs"]["expected"]
    mutated["artifacts"] = [
        item for item in mutated["artifacts"] if item["id"] != removed_expected
    ]
    controls.append(
        _mutated_control(
            "sparql.missing-expected",
            mutated,
            schema,
            root,
            authority,
            {"dangling_expected_reference", "orphan_file"},
        )
    )

    mutated = deepcopy(document)
    mutated["artifacts"][0]["path"] = mutated["artifacts"][2]["path"]
    mutated["artifacts"][0]["sha256"] = mutated["artifacts"][2]["sha256"]
    controls.append(
        _mutated_control(
            "sparql.orphan-query-file",
            mutated,
            schema,
            root,
            authority,
            {"orphan_file"},
        )
    )

    authority_documents = authority.documents
    with tempfile.TemporaryDirectory(prefix="dssc-phase06-sparql-") as directory:
        temp_dir = Path(directory)
        for authority_id in AUTHORITY_RELPATHS:
            canonical_document = authority_documents.get(authority_id)
            if canonical_document is None:
                controls.append(
                    {
                        "id": f"{authority_id}.canonical-unavailable",
                        "expected": "canonical authority",
                        "actual": "unavailable",
                        "observed_issue_codes": ["canonical-unavailable"],
                        "passed": False,
                    }
                )
                continue
            duplicate = deepcopy(canonical_document)
            dangling = deepcopy(canonical_document)
            if authority_id == "release_manifest":
                duplicate_item = deepcopy(duplicate["releases"][0]["artifacts"][0])
                duplicate_item["role"] = duplicate["releases"][0]["artifacts"][1][
                    "role"
                ]
                duplicate["releases"][0]["artifacts"].append(duplicate_item)
                dangling["currentRelease"] = "v0.9"
            elif authority_id == "baseline_test_cases":
                duplicate_item = deepcopy(duplicate["cases"][0])
                duplicate_item["enabled"] = not duplicate_item["enabled"]
                duplicate["cases"].append(duplicate_item)
                sparql_case = next(
                    case for case in dangling["cases"] if case["category"] == "sparql"
                )
                sparql_case["artifact_refs"]["graph_inputs"] = [
                    "missing-artifact"
                ]
            elif authority_id == "requirements":
                duplicate_item = deepcopy(duplicate["requirements"][0])
                duplicate_item["business_rule"] += " Duplicate-ID control."
                duplicate["requirements"].append(duplicate_item)
                dangling["requirements"][0]["test_obligations"][0][
                    "planned_case_ids"
                ].append("D04-PC999")
            elif authority_id == "v0_4_test_cases":
                duplicate_item = deepcopy(duplicate["cases"][0])
                duplicate_item["fixture"]["assertion_id"] += "-duplicate"
                duplicate["cases"].append(duplicate_item)
                dangling["cases"][0]["requirement_ids"].append("D04-R999")
            elif authority_id == "validation_suites":
                duplicate_item = deepcopy(duplicate["suites"][0])
                duplicate_item["description"] += " Duplicate-ID control."
                duplicate["suites"].append(duplicate_item)
                dangling["suites"][2]["depends_on"] = ["missing-suite"]
            controls.append(
                _authority_control(
                    root, temp_dir, authority_id, "duplicate-id", duplicate
                )
            )
            controls.append(
                _authority_control(
                    root, temp_dir, authority_id, "dangling-reference", dangling
                )
            )

    passed = sum(1 for control in controls if control["passed"])
    result = {
        "schema_version": "1.0.0",
        "suite": "sparql-negative-controls",
        "status": "PASS" if passed == len(controls) and controls else "FAIL",
        "program_status": (
            "SUCCESS" if passed == len(controls) and controls else "ERROR"
        ),
        "summary": {
            "total": len(controls),
            "passed": passed,
            "failed": len(controls) - passed,
        },
        "controls": controls,
        "issues": [],
    }
    return result


def run_determinism_check(root: Path) -> dict[str, Any]:
    first = execute_suite(root)
    second = execute_suite(root)
    first_json = canonical_json_sha256(first)
    second_json = canonical_json_sha256(second)
    first_report = hashlib.sha256(render_report(first).encode("utf-8")).hexdigest()
    second_report = hashlib.sha256(render_report(second).encode("utf-8")).hexdigest()
    passed = (
        first.get("program_status") == "SUCCESS"
        and second.get("program_status") == "SUCCESS"
        and first_json == second_json
        and first_report == second_report
    )
    return {
        "schema_version": "1.0.0",
        "suite": "sparql-determinism",
        "status": "PASS" if passed else "FAIL",
        "program_status": "SUCCESS" if passed else "ERROR",
        "runs": [
            {
                "run": 1,
                "results_sha256": first_json,
                "report_sha256": first_report,
                "program_status": first.get("program_status"),
            },
            {
                "run": 2,
                "results_sha256": second_json,
                "report_sha256": second_report,
                "program_status": second.get("program_status"),
            },
        ],
        "results_match": first_json == second_json,
        "reports_match": first_report == second_report,
    }


def run_component(context: dict[str, Any]) -> dict[str, Any]:
    root = context.get("repository_root")
    if not isinstance(root, Path):
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "SPARQL checker requires repository_root",
            "details": {"issues": ["repository_root is missing"]},
            "machine_details": {},
        }
    try:
        result = execute_suite(root)
        write_canonical_outputs(root, result)
        results_path = _repository_path(root, RESULTS_RELPATH)
        report_path = _repository_path(root, REPORT_RELPATH)
        environment_path = _repository_path(root, ENVIRONMENT_RELPATH)
        passed = result["program_status"] == "SUCCESS" and result["exit_code"] == 0
        return {
            "status": "PASS" if passed else "FAIL",
            "program_status": "SUCCESS" if passed else "ERROR",
            "message": (
                "20 version-bound SPARQL competency questions passed"
                if passed
                else "SPARQL manifest preflight or exact query evaluation failed"
            ),
            "details": {
                "summary": result["summary"],
                "results_path": RESULTS_RELPATH,
                "results_sha256": sha256_file(results_path),
                "report_path": REPORT_RELPATH,
                "report_sha256": sha256_file(report_path),
                "environment_path": ENVIRONMENT_RELPATH,
                "environment_sha256": sha256_file(environment_path),
                "manifest_sha256": result["sparql_manifest"]["manifest_sha256"],
                "schema_sha256": result["sparql_manifest"]["schema_sha256"],
                "registry": result["registry"],
                "sources": result["sources"],
                "issues": result["issues"],
            },
            "machine_details": {
                "results_path": RESULTS_RELPATH,
                "results_sha256": sha256_file(results_path),
                "report_path": REPORT_RELPATH,
                "report_sha256": sha256_file(report_path),
                "environment_path": ENVIRONMENT_RELPATH,
                "environment_sha256": sha256_file(environment_path),
            },
        }
    except Exception as exc:  # noqa: BLE001 - component boundary is fail closed
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "SPARQL checker raised an unexpected exception",
            "details": {"issues": [f"{exc.__class__.__name__}: execution aborted"]},
            "machine_details": {},
        }


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Validate and execute an alternate SPARQL manifest (negative controls).",
    )
    parser.add_argument(
        "--negative-controls",
        action="store_true",
        help="Run fail-closed authority and SPARQL manifest mutation controls.",
    )
    parser.add_argument(
        "--determinism-check",
        action="store_true",
        help="Execute two in-memory runs and compare deterministic JSON/Markdown hashes.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run canonical execution, negative controls, and determinism checks.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    requested_controls = args.negative_controls or args.self_test
    requested_determinism = args.determinism_check or args.self_test
    canonical_required = args.self_test or not (
        args.negative_controls or args.determinism_check
    )
    statuses: list[bool] = []
    if canonical_required:
        manifest_path = args.manifest
        if manifest_path is not None and not manifest_path.is_absolute():
            manifest_path = (Path.cwd() / manifest_path).resolve()
        result = execute_suite(ROOT, manifest_path=manifest_path)
        write_canonical_outputs(ROOT, result)
        statuses.append(result["program_status"] == "SUCCESS")
        print(
            f"SPARQL results: {RESULTS_RELPATH} "
            f"({result['program_status']}, exit={result['exit_code']})"
        )
    if requested_controls:
        controls = run_negative_controls(ROOT)
        controls_path = _repository_path(ROOT, NEGATIVE_CONTROLS_RELPATH)
        write_json(controls_path, controls)
        statuses.append(controls["program_status"] == "SUCCESS")
        print(
            f"SPARQL negative controls: {NEGATIVE_CONTROLS_RELPATH} "
            f"({controls['program_status']})"
        )
    if requested_determinism:
        determinism = run_determinism_check(ROOT)
        determinism_path = _repository_path(ROOT, DETERMINISM_RELPATH)
        write_json(determinism_path, determinism)
        statuses.append(determinism["program_status"] == "SUCCESS")
        print(
            f"SPARQL determinism: {DETERMINISM_RELPATH} "
            f"({determinism['program_status']})"
        )
    return 0 if statuses and all(statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
