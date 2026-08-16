"""Deterministic Phase 03 traceability result and Markdown generation."""

from __future__ import annotations

import copy
import os
import platform
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

from dssc_validation.evidence import (
    assert_normalized_result,
    atomic_write_json,
    atomic_write_text,
    normalized_text,
)
from dssc_validation.hashing import sha256_file, sha256_text
from dssc_validation.paths import is_exact_phase_build_dir, prepare_phase_build_dir
from dssc_validation.provenance import collect_loaded_source_hashes


RESULT_SCHEMA = "dssc.traceability.result.v1"
ENVIRONMENT_SCHEMA = "dssc.traceability.environment.v1"

_SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_SOURCES = (
    "scripts/validate.py",
    "scripts/dssc_validation/checks_traceability.py",
    "scripts/dssc_validation/d_group_contract.py",
    "scripts/dssc_validation/entrypoint_catalog.py",
    "scripts/dssc_validation/evidence.py",
    "scripts/dssc_validation/hashing.py",
    "scripts/dssc_validation/paths.py",
    "scripts/dssc_validation/provenance.py",
    "scripts/dssc_validation/requirements_registry.py",
    "scripts/dssc_validation/suite_registry.py",
    "scripts/dssc_validation/traceability_report.py",
)
_VALIDATOR_DISTRIBUTIONS = ("rdflib", "pyshacl", "jsonschema")


def _sanitize(value: Any, root: Path) -> Any:
    if isinstance(value, str):
        return normalized_text(value, root, Path(sys.executable))
    if isinstance(value, dict):
        return {key: _sanitize(item, root) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item, root) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item, root) for item in value]
    return value


def normalized_contract_evidence(contract: dict[str, Any]) -> dict[str, Any]:
    """Return a reversible evidence view of source header prose.

    The shared normalized-result guard intentionally rejects slash-prefixed
    filesystem-looking substrings.  One authoritative Chinese FAIL comment
    uses solidus as punctuation (``缺失/类型错/...``), so the evidence view
    records an exact UTF-8 hash and renders each solidus as the literal
    ``\\u002f`` sequence.  Contract comparison always occurs before this
    presentation-only encoding.
    """
    evidence = copy.deepcopy(contract)
    extraction = evidence.get("extraction")
    header = extraction.get("status_header") if isinstance(extraction, dict) else None
    if not isinstance(header, dict):
        return evidence
    for collection_name in ("mappings", "lines"):
        for item in header.get(collection_name, []):
            if not isinstance(item, dict):
                continue
            raw = item.get("quoted_text")
            if isinstance(raw, str):
                item["quoted_text_sha256"] = sha256_text(raw)
                item["quoted_text"] = raw.replace("/", "\\u002f")
            description = item.get("description")
            if isinstance(description, str):
                item["description"] = description.replace("/", "\\u002f")
    header["source_text_encoding"] = "solidus-as-literal-backslash-u002f"
    return evidence


def _run_git(root: Path, *args: str) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""
    return completed.returncode, (completed.stdout or "").strip()


def _source_state(root: Path, profile: str) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    if profile == "host":
        commit_code, commit = _run_git(root, "rev-parse", "HEAD")
        dirty_code, dirty = _run_git(root, "status", "--porcelain")
        if commit_code != 0 or _SOURCE_COMMIT.fullmatch(commit) is None:
            issues.append("host Git commit is unavailable or malformed")
        if dirty_code != 0:
            issues.append("host Git dirty state is unavailable")
        return {
            "source": "host-git",
            "commit": commit if _SOURCE_COMMIT.fullmatch(commit) else None,
            "dirty": bool(dirty) if dirty_code == 0 else None,
        }, issues
    commit = os.environ.get("DSSC_SOURCE_COMMIT", "").strip().lower()
    dirty_text = os.environ.get("DSSC_SOURCE_DIRTY", "").strip().lower()
    if _SOURCE_COMMIT.fullmatch(commit) is None:
        issues.append("container image source commit is unavailable or malformed")
    if dirty_text not in {"true", "false"}:
        issues.append("container image source dirty state must be true or false")
    return {
        "source": "container-image-build-args",
        "commit": commit if _SOURCE_COMMIT.fullmatch(commit) else None,
        "dirty": dirty_text == "true" if dirty_text in {"true", "false"} else None,
    }, issues


def collect_traceability_environment(root: Path, profile: str) -> dict[str, Any]:
    source_state, source_issues = _source_state(root, profile)
    versions: dict[str, str | None] = {}
    for distribution in _VALIDATOR_DISTRIBUTIONS:
        try:
            versions[distribution] = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            versions[distribution] = None
            source_issues.append(f"required validator distribution is missing: {distribution}")
    try:
        pip_version: str | None = metadata.version("pip")
    except metadata.PackageNotFoundError:
        pip_version = None
        source_issues.append("required pip distribution is missing")
    return {
        "schema": ENVIRONMENT_SCHEMA,
        "suite": "traceability",
        "profile": profile,
        "source_state": source_state,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable": sys.executable,
            "repository_root": str(root),
            "cwd": str(Path.cwd()),
        },
        "pip": pip_version,
        "validators": versions,
        "issues": sorted(set(source_issues)),
    }


def finalize_traceability_result(
    root: Path, profile: str, payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_hashes, source_hash_issues = collect_loaded_source_hashes(
        root, _REQUIRED_SOURCES
    )
    environment = collect_traceability_environment(root, profile)
    successful = (
        payload.get("program_status") == "SUCCESS"
        and payload.get("exit_code") == 0
        and not source_hash_issues
        and not environment["issues"]
    )
    result = {
        "schema": RESULT_SCHEMA,
        "suite": "traceability",
        "profile": profile,
        **payload,
        "source_hashes": source_hashes,
        "source_hash_issues": sorted(source_hash_issues),
        "program_status": "SUCCESS" if successful else "ERROR",
        "exit_code": 0 if successful else 1,
        "message": (
            "D-group requirements traceability passed"
            if successful
            else payload.get("message", "D-group requirements traceability failed")
        ),
    }
    result = _sanitize(result, root)
    assert_normalized_result(result)
    return result, environment


def render_traceability_markdown(result: dict[str, Any]) -> str:
    registry = result.get("requirements_registry", {})
    contract = result.get("d_group_contract", {})
    coverage = contract.get("coverage", {}) if isinstance(contract, dict) else {}
    smoke = contract.get("source_smoke", {}) if isinstance(contract, dict) else {}
    lines = [
        "# Phase 03 D-group Traceability Result",
        "",
        f"- schema: `{result.get('schema')}`",
        f"- profile: `{result.get('profile')}`",
        f"- program_status: `{result.get('program_status')}`",
        f"- exit_code: `{result.get('exit_code')}`",
        f"- requirements manifest: `{registry.get('manifest_path')}`",
        f"- requirements manifest SHA-256: `{registry.get('manifest_sha256')}`",
        f"- requirements schema SHA-256: `{registry.get('schema_sha256')}`",
        f"- requirement count: `{registry.get('requirement_count')}`",
        f"- planned case count: `{registry.get('planned_case_count')}`",
        f"- test obligation count: `{registry.get('test_obligation_count')}`",
        f"- named shape coverage: `{coverage.get('covered_shape_count')}/{coverage.get('named_shape_count')}`",
        f"- source smoke status: `{smoke.get('status')}`",
        "",
        "## Checks",
        "",
        "| check | status | issues |",
        "|---|---|---:|",
    ]
    for name, value in (
        ("requirements registry", result.get("requirements_validation", {})),
        ("D input integrity", contract.get("input_integrity", {})),
        ("Meta-SHACL", contract.get("meta_shacl", {})),
        ("bidirectional coverage", coverage),
        ("source smoke", smoke),
        ("documentation", result.get("documentation_validation", {})),
    ):
        issues = value.get("issues", []) if isinstance(value, dict) else []
        status = value.get("status", "UNKNOWN") if isinstance(value, dict) else "UNKNOWN"
        lines.append(f"| {name} | `{status}` | {len(issues)} |")
    lines.extend(["", "## Requirement IDs", ""])
    lines.extend(f"- `{item}`" for item in registry.get("requirement_ids", []))
    lines.append("")
    return "\n".join(lines)


def render_source_contract_markdown(contract: dict[str, Any]) -> str:
    extraction = contract.get("extraction", {})
    coverage = contract.get("coverage", {})
    input_integrity = contract.get("input_integrity", {})
    meta = contract.get("meta_shacl", {})
    smoke = contract.get("source_smoke", {})
    lines = [
        "# D-group Source Contract Audit",
        "",
        f"- status: `{contract.get('status')}`",
        f"- source: `{extraction.get('source_path')}`",
        f"- source SHA-256: `{extraction.get('source_sha256')}`",
        f"- D/frozen checksum binding: `{input_integrity.get('status')}`",
        f"- triples: `{extraction.get('triple_count')}`",
        f"- named NodeShapes: `{extraction.get('named_node_shape_count')}`",
        f"- named PropertyShapes: `{extraction.get('named_property_shape_count')}`",
        f"- Meta-SHACL: `{meta.get('status')}`",
        f"- coverage: `{coverage.get('covered_shape_count')}/{coverage.get('named_shape_count')}`",
        f"- source smoke: `{smoke.get('status')}`",
        "",
        "## Shapes",
        "",
        "| shape | type | path | severity | components | messages |",
        "|---|---|---|---|---|---:|",
    ]
    for shape in extraction.get("shapes", []):
        lines.append(
            f"| `{shape.get('shape')}` | {shape.get('shape_type')} | "
            f"`{shape.get('path') or 'N/A'}` | `{shape.get('severity')}` | "
            f"{', '.join(shape.get('constraint_components', []))} | "
            f"{len(shape.get('messages', []))} |"
        )
    lines.append("")
    return "\n".join(lines)


def _source_locators(requirement: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for source in requirement.get("sources", []):
        locator = source.get("locator") if isinstance(source, dict) else None
        if not isinstance(locator, dict):
            continue
        if isinstance(locator.get("shape"), str):
            values.append(locator["shape"])
        elif locator.get("kind") == "TTL_HEADER_COMMENT":
            values.append(
                f"TTL_HEADER_COMMENT:L{locator.get('line_start')}-L{locator.get('line_end')}"
            )
    return sorted(values)


def _source_paths(requirement: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for source in requirement.get("sources", []):
        locator = source.get("locator") if isinstance(source, dict) else None
        if isinstance(locator, dict) and isinstance(locator.get("path"), str):
            values.append(locator["path"])
    return sorted(values)


def _components(requirement: dict[str, Any]) -> list[str]:
    values: set[str] = set()
    for source in requirement.get("sources", []):
        locator = source.get("locator") if isinstance(source, dict) else None
        if isinstance(locator, dict):
            values.update(
                item
                for item in locator.get("constraint_components", [])
                if isinstance(item, str)
            )
    return sorted(values)


def _targets(requirement: dict[str, Any]) -> list[str]:
    values: set[str] = set()
    for source in requirement.get("sources", []):
        locator = source.get("locator") if isinstance(source, dict) else None
        target = locator.get("target") if isinstance(locator, dict) else None
        if not isinstance(target, dict) or target.get("kind") == "OPERATIONAL_SCOPE":
            continue
        value = target.get("value")
        target_value = value.get("value") if isinstance(value, dict) else value
        owner = target.get("owner_shape")
        owner_suffix = f" via {owner}" if isinstance(owner, str) else ""
        values.add(
            f"{target.get('kind')} {target.get('predicate')} {target_value}{owner_suffix}"
        )
    return sorted(values)


def _severities(requirement: dict[str, Any]) -> list[str]:
    return sorted(
        {
            locator["severity"]
            for source in requirement.get("sources", [])
            if isinstance(source, dict)
            for locator in [source.get("locator")]
            if isinstance(locator, dict) and isinstance(locator.get("severity"), str)
        }
    )


def _messages(requirement: dict[str, Any]) -> list[str]:
    values: set[str] = set()
    has_shacl_locator = False
    for source in requirement.get("sources", []):
        locator = source.get("locator") if isinstance(source, dict) else None
        if not isinstance(locator, dict):
            continue
        if locator.get("kind") == "SHACL_SHAPE":
            has_shacl_locator = True
            values.update(str(item) for item in locator.get("messages", []))
        elif isinstance(locator.get("quoted_text"), str):
            values.add(locator["quoted_text"])
    if not values and has_shacl_locator:
        return ["∅ (no explicit sh:message)"]
    return sorted(values)


def _implemented_artifacts(requirement: dict[str, Any]) -> list[str]:
    implementation = requirement.get("implementation")
    if not isinstance(implementation, dict):
        return []
    values: list[str] = []
    for reference in implementation.get("artifact_refs", []):
        if not isinstance(reference, dict) or reference.get("status") != "IMPLEMENTED":
            continue
        path = reference.get("path")
        if not isinstance(path, str):
            continue
        description = str(reference.get("description", "")).replace("|", "\\|")
        values.append(
            f"`P{reference.get('phase')} {path}`<br>{description}"
        )
    return sorted(values)


def render_requirements_traceability(
    manifest: dict[str, Any], manifest_sha256: str
) -> str:
    """Render the human view solely from the machine registry."""
    lines = [
        "# v0.4 Requirements Traceability",
        "",
        "> 此表由 `C_Semantic_Treehouse/manifests/v0.4-requirements.json` "
        "确定性生成；机器 registry 是唯一 oracle。",
        "",
        f"- registry SHA-256: `{manifest_sha256}`",
        f"- manifest schema version: `{manifest.get('manifest_schema_version')}`",
        f"- profile: `{manifest.get('profile', {}).get('id')}`",
        "",
        "| ID | business rule | source locator | target | path | severity | message | components | statuses | planned cases | decisions | implemented artifacts |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for requirement in manifest.get("requirements", []):
        obligations = requirement.get("test_obligations", [])
        planned_cases = sorted(
            {
                case_id
                for obligation in obligations
                if isinstance(obligation, dict)
                for case_id in obligation.get("planned_case_ids", [])
            }
        )
        values = [
            requirement.get("id", ""),
            str(requirement.get("business_rule", "")).replace("|", "\\|"),
            "<br>".join(f"`{item}`" for item in _source_locators(requirement)) or "—",
            "<br>".join(f"`{item}`" for item in _targets(requirement)) or "—",
            "<br>".join(f"`{item}`" for item in _source_paths(requirement)) or "—",
            "<br>".join(f"`{item}`" for item in _severities(requirement)) or "—",
            "<br>".join(
                f"`{item.replace('|', '\\|')}`" for item in _messages(requirement)
            )
            or "—",
            "<br>".join(f"`{item}`" for item in _components(requirement)) or "—",
            ", ".join(requirement.get("expected_business_statuses", [])),
            "<br>".join(f"`{item}`" for item in planned_cases),
            "<br>".join(f"`{item}`" for item in requirement.get("decision_refs", [])) or "—",
            "<br>".join(_implemented_artifacts(requirement)) or "—",
        ]
        lines.append("| " + " | ".join(values) + " |")
    lines.extend(
        [
            "",
            "## 解释性差异",
            "",
            "`ex:BuildingEnergyDatasetShape` 在规范性 TTL 中没有显式 "
            "`sh:message`，其 NodeKind 结果也没有 path。D04-R002 因此保留空 "
            "message 与不适用 path；validator 默认文本不构成规范 oracle。",
            "",
            "## 实现边界",
            "",
            "Phase 04 已登记发布 Shape、必要 ontology/context 与 model contract "
            "实现引用，并在每个引用中绑定 SHA-256。fixture/evidence 引用和完整四状态 "
            "classifier/harness 继续保持 `PLANNED`；正式 fixtures 与 "
            "`v0.4-test-cases.json` 由 Phase 05 创建。",
            "",
        ]
    )
    return "\n".join(lines)


def write_traceability_evidence(
    output_dir: Path,
    profile: str,
    result: dict[str, Any],
    environment: dict[str, Any],
    root: Path,
    evidence_phase: str,
) -> tuple[Path, Path, Path, Path, Path]:
    allowed = {f"{phase:02d}" for phase in range(3, 10)}
    if evidence_phase not in allowed or not is_exact_phase_build_dir(
        output_dir, evidence_phase, root
    ):
        raise ValueError(
            "traceability evidence output must equal the registry-selected "
            "build/phase-NN/current directory at Phase 03 or later"
        )
    output_dir = prepare_phase_build_dir(evidence_phase, root)
    result_path = output_dir / f"traceability-{profile}.result.json"
    environment_path = output_dir / f"traceability-{profile}.environment.json"
    markdown_path = output_dir / f"traceability-{profile}.md"
    contract_json_path = output_dir / "source-contract-audit.json"
    contract_markdown_path = output_dir / "source-contract-audit.md"
    atomic_write_json(result_path, result)
    sidecar = dict(environment)
    sidecar["result_file"] = result_path.name
    sidecar["result_sha256"] = sha256_file(result_path)
    atomic_write_json(environment_path, sidecar)
    atomic_write_text(markdown_path, render_traceability_markdown(result))
    contract = result.get("d_group_contract", {})
    atomic_write_json(contract_json_path, contract)
    atomic_write_text(contract_markdown_path, render_source_contract_markdown(contract))
    return (
        result_path,
        environment_path,
        markdown_path,
        contract_json_path,
        contract_markdown_path,
    )


def normalized_semantic_view(result: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "schema",
        "suite",
        "requirements_registry",
        "requirements_validation",
        "d_group_contract",
        "documentation_validation",
        "registry_contract_version",
        "registry_sha256",
        "requirements_lock_sha256",
        "source_hashes",
        "source_hash_issues",
        "program_status",
        "exit_code",
        "message",
    )
    return {key: result.get(key) for key in keys}


__all__ = [
    "collect_traceability_environment",
    "finalize_traceability_result",
    "normalized_semantic_view",
    "normalized_contract_evidence",
    "render_requirements_traceability",
    "render_source_contract_markdown",
    "render_traceability_markdown",
    "write_traceability_evidence",
]
