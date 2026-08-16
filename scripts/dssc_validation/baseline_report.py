"""Deterministic result, environment, and Markdown evidence for Phase 02."""

from __future__ import annotations

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
from dssc_validation.hashing import sha256_file
from dssc_validation.paths import (
    is_exact_phase_build_dir,
    prepare_phase_build_dir,
    requirements_lock_path,
)
from dssc_validation.provenance import collect_loaded_source_hashes


RESULT_SCHEMA = "dssc.baseline.result.v1"
ENVIRONMENT_SCHEMA = "dssc.baseline.environment.v1"

_SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_SOURCES = (
    "scripts/validate.py",
    "scripts/dssc_validation/baseline_manifest.py",
    "scripts/dssc_validation/baseline_report.py",
    "scripts/dssc_validation/baseline_runner.py",
    "scripts/dssc_validation/checks_baseline.py",
    "scripts/dssc_validation/entrypoint_catalog.py",
    "scripts/dssc_validation/evidence.py",
    "scripts/dssc_validation/hashing.py",
    "scripts/dssc_validation/paths.py",
    "scripts/dssc_validation/provenance.py",
    "scripts/dssc_validation/suite_registry.py",
)
_VALIDATOR_DISTRIBUTIONS = (
    "rdflib",
    "PyLD",
    "pyshacl",
    "jsonschema",
    "PyYAML",
    "openapi-spec-validator",
)


def _normalize_json_pointers(value: Any, parent_key: str | None = None) -> Any:
    """Encode RFC 6901 pointers as URI fragments, distinct from file paths."""
    if isinstance(value, dict):
        return {
            key: _normalize_json_pointers(item, key)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_json_pointers(item, parent_key) for item in value]
    if (
        isinstance(value, str)
        and parent_key in {"instance_pointer", "schema_pointer"}
        and value.startswith("/")
    ):
        return f"json-pointer:{value}"
    return value


def _sanitize_result_text(value: Any, root: Path) -> Any:
    if isinstance(value, str):
        return normalized_text(value, root, Path(sys.executable))
    if isinstance(value, dict):
        return {key: _sanitize_result_text(item, root) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_result_text(item, root) for item in value]
    return value


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
        dirty_code, dirty_output = _run_git(root, "status", "--porcelain")
        if commit_code != 0 or _SOURCE_COMMIT.fullmatch(commit) is None:
            issues.append("host Git commit is unavailable or malformed")
        if dirty_code != 0:
            issues.append("host Git dirty state is unavailable")
        return {
            "source": "host-git",
            "commit": commit if _SOURCE_COMMIT.fullmatch(commit) else None,
            "dirty": bool(dirty_output) if dirty_code == 0 else None,
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


def collect_baseline_environment(
    root: Path,
    profile: str,
) -> tuple[dict[str, Any], list[str]]:
    """Collect machine-local inventory; return explicit provenance issues."""
    if profile not in {"host", "container"}:
        raise ValueError("baseline profile must be host or container")

    source_state, issues = _source_state(root, profile)
    versions: dict[str, str | None] = {}
    for distribution in _VALIDATOR_DISTRIBUTIONS:
        try:
            versions[distribution] = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            versions[distribution] = None
            issues.append(f"mandatory distribution is unavailable: {distribution}")

    try:
        pip_version: str | None = metadata.version("pip")
    except metadata.PackageNotFoundError:
        pip_version = None
        issues.append("pip distribution metadata is unavailable")

    lock_path = requirements_lock_path(root)
    lock_hash = sha256_file(lock_path) if lock_path.is_file() else None
    if lock_hash is None:
        issues.append("requirements.lock is unavailable")

    environment = {
        "schema": ENVIRONMENT_SCHEMA,
        "suite": "baseline",
        "profile": profile,
        "source_state": source_state,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
            "platform": platform.platform(),
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable": sys.executable,
            "repository_root": str(root.resolve()),
            "cwd": str(Path.cwd().resolve()),
        },
        "pip_version": pip_version,
        "validator_versions": versions,
        "requirements_lock_sha256": lock_hash,
        "issues": sorted(issues),
    }
    return environment, sorted(issues)


def finalize_baseline_result(
    root: Path,
    profile: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Add reproducibility provenance and fail closed on missing evidence."""
    result = _normalize_json_pointers(_sanitize_result_text(dict(payload), root))
    result["schema"] = RESULT_SCHEMA
    result["suite"] = "baseline"
    result["profile"] = profile

    source_hashes, source_issues = collect_loaded_source_hashes(
        root,
        required_relpaths=_REQUIRED_SOURCES,
    )
    result["source_hashes"] = source_hashes
    result["source_hash_issues"] = sorted(source_issues)

    environment, environment_issues = collect_baseline_environment(root, profile)
    if source_issues or environment_issues:
        result["program_status"] = "ERROR"
        result["exit_code"] = 1
        result["message"] = "baseline evidence provenance failed"
    assert_normalized_result(result)
    return result, environment


def render_baseline_markdown(result: dict[str, Any]) -> str:
    """Render a compact deterministic report from result JSON only."""
    counts = result["counts"]
    lines = [
        "# v0.1-v0.3 baseline reproduction",
        "",
        f"- profile: `{result['profile']}`",
        f"- program_status: `{result['program_status']}`",
        f"- exit_code: `{result['exit_code']}`",
        f"- manifest_sha256: `{result['manifest_sha256']}`",
        f"- manifest_schema_sha256: `{result['manifest_schema_sha256']}`",
        f"- registry_contract_version: `{result['registry_contract_version']}`",
        f"- registry_sha256: `{result['registry_sha256']}`",
        f"- requirements_lock_sha256: `{result['requirements_lock_sha256']}`",
        "",
        "## Counts",
        "",
        "| discovered | executed | passed | failed | skipped |",
        "|---:|---:|---:|---:|---:|",
        (
            f"| {counts['discovered']} | {counts['executed']} | "
            f"{counts['passed']} | {counts['failed']} | {counts['skipped']} |"
        ),
        "",
        "## Categories",
        "",
        "| category | discovered | executed | passed | failed | skipped |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for category in ("rdf", "jsonld", "shacl", "jsonschema", "openapi", "sparql"):
        values = result["category_counts"][category]
        lines.append(
            f"| {category} | {values['discovered']} | {values['executed']} | "
            f"{values['passed']} | {values['failed']} | {values['skipped']} |"
        )

    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| case | category | expected business | actual business | program | assertions |",
            "|---|---|---|---|---|---:|",
        ]
    )
    for case in result["case_results"]:
        assertions = case.get("assertions", [])
        passed_assertions = sum(
            1 for assertion in assertions if assertion.get("passed") is True
        )
        lines.append(
            f"| `{case['id']}` | {case['category']} | "
            f"{case['expected_business_status']} | {case['actual_business_status']} | "
            f"{case['actual_program_status']} | {passed_assertions}/{len(assertions)} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_baseline_evidence(
    output_dir: Path,
    profile: str,
    result: dict[str, Any],
    environment: dict[str, Any],
    root: Path,
    evidence_phase: str,
) -> tuple[Path, Path, Path]:
    """Write to the exact active-Phase directory selected by the registry."""
    allowed_evidence_phases = {f"{phase:02d}" for phase in range(2, 10)}
    if evidence_phase not in allowed_evidence_phases or not is_exact_phase_build_dir(
        output_dir, evidence_phase, root
    ):
        raise ValueError(
            "baseline evidence output must equal the registry-selected "
            "build/phase-NN/current directory at Phase 02 or later"
        )
    output_dir = prepare_phase_build_dir(evidence_phase, root)
    result_path = output_dir / f"baseline-{profile}.result.json"
    environment_path = output_dir / f"baseline-{profile}.environment.json"
    markdown_path = output_dir / f"baseline-{profile}.md"
    atomic_write_json(result_path, result)
    environment_sidecar = dict(environment)
    environment_sidecar["result_file"] = result_path.name
    environment_sidecar["result_sha256"] = sha256_file(result_path)
    atomic_write_json(environment_path, environment_sidecar)
    atomic_write_text(markdown_path, render_baseline_markdown(result))
    return result_path, environment_path, markdown_path


def normalized_semantic_view(result: dict[str, Any]) -> dict[str, Any]:
    """Return the host/container comparison surface."""
    keys = (
        "schema",
        "suite",
        "manifest_path",
        "manifest_sha256",
        "manifest_schema_path",
        "manifest_schema_sha256",
        "manifest_schema_version",
        "registry_contract_version",
        "registry_sha256",
        "requirements_lock_sha256",
        "preflight",
        "artifact_hashes",
        "required_case_ids",
        "execution_schema",
        "execution_issues",
        "counts",
        "category_counts",
        "case_results",
        "source_hashes",
        "source_hash_issues",
        "program_status",
        "exit_code",
        "message",
    )
    return {key: result.get(key) for key in keys}
