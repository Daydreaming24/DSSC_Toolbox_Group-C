"""Deterministic Phase 04 release-model result and evidence writers."""

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
from dssc_validation.paths import is_exact_phase_build_dir, prepare_phase_build_dir
from dssc_validation.provenance import collect_loaded_source_hashes


RESULT_SCHEMA = "dssc.v0.4-model.result.v1"
ENVIRONMENT_SCHEMA = "dssc.v0.4-model.environment.v1"

_SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_SOURCES = (
    "scripts/validate.py",
    "scripts/dssc_validation/checks_model.py",
    "scripts/dssc_validation/d_group_contract.py",
    "scripts/dssc_validation/entrypoint_catalog.py",
    "scripts/dssc_validation/evidence.py",
    "scripts/dssc_validation/hashing.py",
    "scripts/dssc_validation/lock_contract.py",
    "scripts/dssc_validation/model_contract.py",
    "scripts/dssc_validation/model_report.py",
    "scripts/dssc_validation/model_validation.py",
    "scripts/dssc_validation/paths.py",
    "scripts/dssc_validation/provenance.py",
    "scripts/dssc_validation/release_manifest.py",
    "scripts/dssc_validation/requirements_registry.py",
    "scripts/dssc_validation/suite_registry.py",
)
_VALIDATOR_DISTRIBUTIONS = (
    "rdflib",
    "PyLD",
    "pyshacl",
    "jsonschema",
)


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


def collect_model_environment(root: Path, profile: str) -> dict[str, Any]:
    """Collect machine-local inventory for the environment sidecar."""
    source_state, issues = _source_state(root, profile)
    versions: dict[str, str | None] = {}
    for distribution in _VALIDATOR_DISTRIBUTIONS:
        try:
            versions[distribution] = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            versions[distribution] = None
            issues.append(f"required validator distribution is missing: {distribution}")
    try:
        pip_version: str | None = metadata.version("pip")
    except metadata.PackageNotFoundError:
        pip_version = None
        issues.append("required pip distribution is missing")
    return {
        "schema": ENVIRONMENT_SCHEMA,
        "suite": "v0.4-model",
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
        "issues": sorted(set(issues)),
    }


def finalize_model_result(
    root: Path, profile: str, payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind source provenance and fail closed on an incomplete environment."""
    source_hashes, source_hash_issues = collect_loaded_source_hashes(
        root, _REQUIRED_SOURCES
    )
    environment = collect_model_environment(root, profile)
    successful = (
        payload.get("program_status") == "SUCCESS"
        and payload.get("exit_code") == 0
        and not source_hash_issues
        and not environment["issues"]
    )
    result = {
        "schema": RESULT_SCHEMA,
        "suite": "v0.4-model",
        "profile": profile,
        **payload,
        "source_hashes": source_hashes,
        "source_hash_issues": sorted(source_hash_issues),
        "program_status": "SUCCESS" if successful else "ERROR",
        "exit_code": 0 if successful else 1,
        "message": (
            "v0.4 release model passed"
            if successful
            else payload.get("message", "v0.4 release model failed")
        ),
    }
    result = _sanitize(result, root)
    assert_normalized_result(result)
    return result, environment


def render_model_markdown(result: dict[str, Any]) -> str:
    """Render a compact deterministic report solely from the result JSON."""
    release = result.get("release_manifest", {})
    requirements = result.get("requirements_registry", {})
    projection = result.get("requirements_implementation", {}).get(
        "semantic_projection", {}
    )
    smoke = result.get("contract_smoke", {})
    counts = result.get("counts", {})
    lines = [
        "# v0.4 release model validation",
        "",
        f"- profile: `{result.get('profile')}`",
        f"- program_status: `{result.get('program_status')}`",
        f"- exit_code: `{result.get('exit_code')}`",
        f"- release manifest SHA-256: `{release.get('manifest_sha256')}`",
        f"- release schema SHA-256: `{release.get('schema_sha256')}`",
        f"- requirements SHA-256: `{requirements.get('manifest_sha256')}`",
        f"- Phase 03 semantic projection SHA-256: `{projection.get('actual_sha256')}`",
        f"- semantic projection unchanged: `{projection.get('unchanged')}`",
        f"- suite contract version: `{result.get('registry_contract_version')}`",
        f"- suite registry SHA-256: `{result.get('registry_sha256')}`",
        "",
        "## Checks",
        "",
        "| check | status |",
        "|---|---|",
    ]
    for check in result.get("checks", []):
        lines.append(f"| `{check.get('id')}` | `{check.get('status')}` |")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            "| discovered | executed | passed | failed | skipped |",
            "|---:|---:|---:|---:|---:|",
            (
                f"| {counts.get('discovered')} | {counts.get('executed')} | "
                f"{counts.get('passed')} | {counts.get('failed')} | "
                f"{counts.get('skipped')} |"
            ),
            "",
            "## Contract smoke",
            "",
            "| case | expected | actual | target count | passed |",
            "|---|---|---|---:|---|",
        ]
    )
    for case in smoke.get("cases", []):
        validation = case.get("validation", {})
        lines.append(
            f"| `{case.get('id')}` | `{case.get('expected_business_status')}` | "
            f"`{case.get('actual_business_status')}` | "
            f"{validation.get('target_activation_count')} | `{case.get('passed')}` |"
        )
    lines.append("")
    return "\n".join(lines)


def write_model_evidence(
    output_dir: Path,
    profile: str,
    result: dict[str, Any],
    environment: dict[str, Any],
    root: Path,
    evidence_phase: str,
) -> tuple[Path, Path, Path]:
    allowed = {f"{phase:02d}" for phase in range(4, 10)}
    if evidence_phase not in allowed or not is_exact_phase_build_dir(
        output_dir, evidence_phase, root
    ):
        raise ValueError(
            "model evidence output must equal the registry-selected "
            "build/phase-NN/current directory at Phase 04 or later"
        )
    output_dir = prepare_phase_build_dir(evidence_phase, root)
    result_path = output_dir / f"v0.4-model-{profile}.result.json"
    environment_path = output_dir / f"v0.4-model-{profile}.environment.json"
    markdown_path = output_dir / f"v0.4-model-{profile}.md"
    atomic_write_json(result_path, result)
    sidecar = dict(environment)
    sidecar["result_file"] = result_path.name
    sidecar["result_sha256"] = sha256_file(result_path)
    atomic_write_json(environment_path, sidecar)
    atomic_write_text(markdown_path, render_model_markdown(result))
    return result_path, environment_path, markdown_path


def normalized_semantic_view(result: dict[str, Any]) -> dict[str, Any]:
    """Return the host/container comparison surface."""
    keys = (
        "schema",
        "suite",
        "requirements_registry",
        "requirements_validation",
        "registry_contract_version",
        "registry_path",
        "registry_sha256",
        "registry_schema_path",
        "registry_schema_sha256",
        "suite_registry",
        "requirements_lock_sha256",
        "checks",
        "counts",
        "release_manifest",
        "shape_derivation",
        "sha256sums",
        "turtle",
        "jsonld",
        "requirements_implementation",
        "record_inheritance",
        "traceability_evidence",
        "contract_smoke",
        "source_hashes",
        "source_hash_issues",
        "program_status",
        "exit_code",
        "message",
    )
    view = {key: result.get(key) for key in keys}
    traceability = result.get("traceability_evidence")
    if isinstance(traceability, dict):
        view["traceability_evidence"] = {
            key: traceability.get(key)
            for key in (
                "status",
                "d_source_sha256",
                "requirements_sha256",
                "meta_shacl",
                "issues",
            )
        }
    return view


__all__ = [
    "collect_model_environment",
    "finalize_model_result",
    "normalized_semantic_view",
    "render_model_markdown",
    "write_model_evidence",
]
