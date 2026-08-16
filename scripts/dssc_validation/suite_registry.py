"""Schema and cross-record validation for the public suite registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dssc_validation import PUBLIC_SUITE_IDS
from dssc_validation.entrypoint_catalog import (
    ALLOWED_ENTRYPOINT_IDS,
    entrypoint_allowed_for_suite,
)
from dssc_validation.hashing import sha256_file
from dssc_validation.paths import (
    validation_suites_path,
    validation_suites_schema_path,
)


FIXED_SCHEMA_REFERENCE = "schemas/validation-suites.schema.json"
FORBIDDEN_EXECUTABLE_KEYS = frozenset(
    {
        "args",
        "argv",
        "command",
        "executable",
        "kwargs",
        "module",
        "module_path",
        "parameters",
        "script",
        "shell",
    }
)


@dataclass(frozen=True)
class SemanticIssue:
    code: str
    message: str


@dataclass
class RegistryLoadResult:
    ok: bool
    registry: dict[str, Any] | None
    contract_version: str | None
    registry_sha256: str | None
    issues: list[SemanticIssue] = field(default_factory=list)
    path: Path | None = None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _schema_validate(instance: Any, schema: dict[str, Any]) -> list[SemanticIssue]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return [
            SemanticIssue(
                "schema_engine_missing",
                "jsonschema is not installed; schema validation cannot run",
            )
        ]

    issues: list[SemanticIssue] = []
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: [str(item) for item in error.absolute_path],
    )
    for error in errors:
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        issues.append(SemanticIssue("schema_violation", f"{location}: {error.message}"))
    return issues


def _suite_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    suites = registry.get("suites")
    if not isinstance(suites, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for suite in suites:
        if isinstance(suite, dict) and isinstance(suite.get("id"), str):
            result[suite["id"]] = suite
    return result


def semantic_validate_registry(registry: dict[str, Any]) -> list[SemanticIssue]:
    """Validate relationships and executable-safety rules without rewriting."""
    if not isinstance(registry, dict):
        return [SemanticIssue("type", "registry root must be an object")]

    issues: list[SemanticIssue] = []
    if registry.get("$schema") != FIXED_SCHEMA_REFERENCE:
        issues.append(
            SemanticIssue(
                "schema_reference",
                f"$schema must equal {FIXED_SCHEMA_REFERENCE!r}",
            )
        )
    contract_version = registry.get("contract_version")
    if not isinstance(contract_version, str) or not contract_version.strip():
        issues.append(
            SemanticIssue(
                "contract_version",
                "top-level contract_version must be a non-empty string",
            )
        )
    for banned in (
        "contractVersion",
        "schema_version",
        "suite_contract_version",
        "version",
    ):
        if banned in registry:
            issues.append(
                SemanticIssue(
                    "contract_version_field",
                    f"forbidden alternate version field present: {banned}",
                )
            )

    suites = registry.get("suites")
    if not isinstance(suites, list):
        issues.append(SemanticIssue("suites", "suites must be an array"))
        return issues

    ids: list[str] = []
    global_component_ids: set[str] = set()
    for index, suite in enumerate(suites):
        if not isinstance(suite, dict):
            issues.append(SemanticIssue("suite_type", f"suites[{index}] must be an object"))
            continue
        sid = suite.get("id")
        if not isinstance(sid, str):
            issues.append(SemanticIssue("suite_id", f"suites[{index}].id must be a string"))
            continue
        ids.append(sid)

        for key in FORBIDDEN_EXECUTABLE_KEYS:
            if key in suite:
                issues.append(
                    SemanticIssue(
                        "shell_payload",
                        f"suite {sid!r} contains forbidden executable key {key!r}",
                    )
                )

        components = suite.get("components")
        if not isinstance(components, list):
            issues.append(
                SemanticIssue("components_type", f"suite {sid!r} components must be an array")
            )
            components = []
        status = suite.get("status")
        if status == "IMPLEMENTED" and not components:
            issues.append(
                SemanticIssue(
                    "zero_components",
                    f"IMPLEMENTED suite {sid!r} must have non-empty components",
                )
            )
        elif status == "NOT_IMPLEMENTED" and components:
            issues.append(
                SemanticIssue(
                    "not_implemented_components",
                    f"NOT_IMPLEMENTED suite {sid!r} must not carry components",
                )
            )
        elif status not in ("IMPLEMENTED", "NOT_IMPLEMENTED"):
            issues.append(
                SemanticIssue(
                    "status",
                    f"suite {sid!r} has invalid implementation status {status!r}",
                )
            )

        local_component_ids: set[str] = set()
        local_entrypoints: set[str] = set()
        for component_index, component in enumerate(components):
            if not isinstance(component, dict):
                issues.append(
                    SemanticIssue(
                        "component_type",
                        f"suite {sid!r} components[{component_index}] must be an object",
                    )
                )
                continue
            for key in FORBIDDEN_EXECUTABLE_KEYS:
                if key in component:
                    issues.append(
                        SemanticIssue(
                            "shell_payload",
                            f"suite {sid!r} component contains forbidden key {key!r}",
                        )
                    )
            cid = component.get("id")
            entrypoint = component.get("entrypoint")
            if not isinstance(cid, str) or not cid:
                issues.append(
                    SemanticIssue(
                        "component_id",
                        f"suite {sid!r} components[{component_index}].id is invalid",
                    )
                )
            else:
                if cid in local_component_ids or cid in global_component_ids:
                    issues.append(
                        SemanticIssue(
                            "duplicate_component",
                            f"duplicate component id {cid!r}",
                        )
                    )
                local_component_ids.add(cid)
                global_component_ids.add(cid)
            if not isinstance(entrypoint, str) or not entrypoint:
                issues.append(
                    SemanticIssue(
                        "entrypoint",
                        f"suite {sid!r} component {cid!r} has invalid entrypoint",
                    )
                )
            else:
                if entrypoint in local_entrypoints:
                    issues.append(
                        SemanticIssue(
                            "duplicate_entrypoint",
                            f"suite {sid!r} repeats logical entrypoint {entrypoint!r}",
                        )
                    )
                local_entrypoints.add(entrypoint)
                if entrypoint not in ALLOWED_ENTRYPOINT_IDS:
                    issues.append(
                        SemanticIssue(
                            "unknown_entrypoint",
                            f"suite {sid!r} references unknown entrypoint {entrypoint!r}",
                        )
                    )
                elif not entrypoint_allowed_for_suite(entrypoint, sid):
                    issues.append(
                        SemanticIssue(
                            "entrypoint_suite_mismatch",
                            f"entrypoint {entrypoint!r} is not allowed for suite {sid!r}",
                        )
                    )

        dependencies = suite.get("depends_on")
        if not isinstance(dependencies, list):
            issues.append(
                SemanticIssue("depends_on_type", f"suite {sid!r} depends_on must be an array")
            )
        else:
            string_dependencies = [item for item in dependencies if isinstance(item, str)]
            duplicates = sorted(
                {item for item in string_dependencies if string_dependencies.count(item) > 1}
            )
            if duplicates:
                issues.append(
                    SemanticIssue(
                        "duplicate_dependency",
                        f"suite {sid!r} repeats dependencies: {', '.join(duplicates)}",
                    )
                )

    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        issues.append(
            SemanticIssue(
                "duplicate_suite_id",
                "duplicate suite id(s): " + ", ".join(duplicates),
            )
        )
    expected_set = set(PUBLIC_SUITE_IDS)
    actual_set = set(ids)
    if actual_set != expected_set:
        issues.append(
            SemanticIssue(
                "suite_set",
                f"suite set mismatch; missing={sorted(expected_set - actual_set)}; "
                f"extra={sorted(actual_set - expected_set)}",
            )
        )
    if ids != list(PUBLIC_SUITE_IDS):
        issues.append(
            SemanticIssue(
                "suite_order",
                "suite order must equal the fixed public suite order",
            )
        )

    suite_map = _suite_map(registry)
    for sid, suite in suite_map.items():
        dependencies = suite.get("depends_on")
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if not isinstance(dependency, str) or dependency not in suite_map:
                issues.append(
                    SemanticIssue(
                        "dangling_dependency",
                        f"suite {sid!r} depends on unregistered suite {dependency!r}",
                    )
                )
            elif (
                suite.get("status") == "IMPLEMENTED"
                and suite_map[dependency].get("status") != "IMPLEMENTED"
            ):
                issues.append(
                    SemanticIssue(
                        "implemented_dependency_not_implemented",
                        f"IMPLEMENTED suite {sid!r} depends on NOT_IMPLEMENTED {dependency!r}",
                    )
                )

    white, gray, black = 0, 1, 2
    colors = {sid: white for sid in suite_map}
    reported_cycles: set[tuple[str, ...]] = set()

    def visit(sid: str, stack: list[str]) -> None:
        colors[sid] = gray
        stack.append(sid)
        dependencies = suite_map[sid].get("depends_on")
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if not isinstance(dependency, str) or dependency not in suite_map:
                    continue
                if colors[dependency] == gray:
                    cycle = tuple(stack[stack.index(dependency) :] + [dependency])
                    if cycle not in reported_cycles:
                        reported_cycles.add(cycle)
                        issues.append(
                            SemanticIssue(
                                "dependency_cycle",
                                "dependency cycle: " + " -> ".join(cycle),
                            )
                        )
                elif colors[dependency] == white:
                    visit(dependency, stack)
        stack.pop()
        colors[sid] = black

    for suite_id in ids:
        if suite_id in colors and colors[suite_id] == white:
            visit(suite_id, [])

    all_suite = suite_map.get("all")
    if all_suite is not None:
        expected_dependencies = list(PUBLIC_SUITE_IDS[:-1])
        if all_suite.get("depends_on") != expected_dependencies:
            issues.append(
                SemanticIssue(
                    "all_composition",
                    "suite 'all' must depend on the other six suites in fixed order",
                )
            )
    return issues


def load_and_validate_registry(
    root: Path | None = None,
    registry_path: Path | None = None,
    schema_path: Path | None = None,
) -> RegistryLoadResult:
    path = registry_path if registry_path is not None else validation_suites_path(root)
    schema = (
        schema_path if schema_path is not None else validation_suites_schema_path(root)
    )
    if not path.is_file():
        return RegistryLoadResult(
            ok=False,
            registry=None,
            contract_version=None,
            registry_sha256=None,
            issues=[SemanticIssue("missing_registry", "validation suite registry is missing")],
            path=path,
        )

    registry_sha256 = sha256_file(path)
    try:
        registry = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return RegistryLoadResult(
            ok=False,
            registry=None,
            contract_version=None,
            registry_sha256=registry_sha256,
            issues=[SemanticIssue("parse_error", f"registry parse failed: {exc}")],
            path=path,
        )

    issues: list[SemanticIssue] = []
    if not schema.is_file():
        issues.append(SemanticIssue("missing_schema", "validation suite schema is missing"))
    else:
        try:
            schema_value = load_json(schema)
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(SemanticIssue("schema_parse", f"schema parse failed: {exc}"))
        else:
            issues.extend(_schema_validate(registry, schema_value))
    issues.extend(
        semantic_validate_registry(registry if isinstance(registry, dict) else {})
    )
    contract_version = (
        registry.get("contract_version")
        if isinstance(registry, dict)
        and isinstance(registry.get("contract_version"), str)
        else None
    )
    return RegistryLoadResult(
        ok=not issues,
        registry=registry if isinstance(registry, dict) else None,
        contract_version=contract_version,
        registry_sha256=registry_sha256,
        issues=issues,
        path=path,
    )


def expand_suite_components(
    registry: dict[str, Any], suite_id: str
) -> tuple[list[dict[str, str]] | None, str | None, str | None]:
    """Expand an implemented suite's dependency closure in stable DFS order."""
    suite_map = _suite_map(registry)
    target = suite_map.get(suite_id)
    if target is None:
        return None, "UNKNOWN_SUITE", f"unknown suite: {suite_id}"
    if target.get("status") == "NOT_IMPLEMENTED":
        return None, "NOT_IMPLEMENTED", f"suite {suite_id!r} is NOT_IMPLEMENTED"
    if target.get("status") != "IMPLEMENTED":
        return None, "INVALID_STATUS", f"suite {suite_id!r} has invalid status"

    ordered: list[dict[str, str]] = []
    visited_suites: set[str] = set()
    visiting: set[str] = set()
    component_ids: set[str] = set()
    entrypoints: set[str] = set()

    def expand(current_id: str) -> tuple[str | None, str | None]:
        if current_id in visited_suites:
            return None, None
        if current_id in visiting:
            return "DEPENDENCY_CYCLE", f"cycle encountered at suite {current_id!r}"
        current = suite_map.get(current_id)
        if current is None:
            return "DANGLING_DEPENDENCY", f"unknown dependency {current_id!r}"
        if current.get("status") != "IMPLEMENTED":
            return (
                "DEPENDENCY_NOT_IMPLEMENTED",
                f"dependency suite {current_id!r} is NOT_IMPLEMENTED",
            )
        visiting.add(current_id)
        dependencies = current.get("depends_on")
        if not isinstance(dependencies, list):
            return "INVALID_DEPENDENCY", f"suite {current_id!r} dependencies invalid"
        for dependency in dependencies:
            if not isinstance(dependency, str):
                return "INVALID_DEPENDENCY", f"suite {current_id!r} dependency invalid"
            code, message = expand(dependency)
            if code:
                return code, message

        components = current.get("components")
        if not isinstance(components, list) or not components:
            return "ZERO_COMPONENTS", f"suite {current_id!r} has 0 components"
        for component in components:
            if not isinstance(component, dict):
                return "INVALID_COMPONENT", f"suite {current_id!r} component invalid"
            component_id = component.get("id")
            entrypoint = component.get("entrypoint")
            if not isinstance(component_id, str) or not isinstance(entrypoint, str):
                return "INVALID_COMPONENT", f"suite {current_id!r} component invalid"
            if component_id in component_ids:
                return "DUPLICATE_COMPONENT", f"duplicate component {component_id!r}"
            if entrypoint in entrypoints:
                return "DUPLICATE_ENTRYPOINT", f"duplicate entrypoint {entrypoint!r}"
            if entrypoint not in ALLOWED_ENTRYPOINT_IDS:
                return "UNKNOWN_ENTRYPOINT", f"unknown entrypoint {entrypoint!r}"
            if not entrypoint_allowed_for_suite(entrypoint, current_id):
                return (
                    "ENTRYPOINT_SUITE_MISMATCH",
                    f"entrypoint {entrypoint!r} is not allowed for {current_id!r}",
                )
            component_ids.add(component_id)
            entrypoints.add(entrypoint)
            ordered.append(
                {
                    "id": component_id,
                    "entrypoint": entrypoint,
                    "suite_id": current_id,
                }
            )
        visiting.remove(current_id)
        visited_suites.add(current_id)
        return None, None

    error_code, error_message = expand(suite_id)
    if error_code:
        return None, error_code, error_message
    if not ordered:
        return None, "ZERO_COMPONENTS", f"suite {suite_id!r} expands to 0 components"
    return ordered, None, None
