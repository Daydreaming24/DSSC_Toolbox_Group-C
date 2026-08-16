"""Deterministic result, Markdown and environment evidence for v0.4 fixtures."""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable

from dssc_validation.evidence import (
    assert_normalized_result,
    atomic_write_json,
    atomic_write_text,
    normalized_text,
)
from dssc_validation.hashing import sha256_file
from dssc_validation.provenance import collect_loaded_source_hashes


RESULT_SCHEMA = "dssc.v0.4.result.v1"
ENVIRONMENT_SCHEMA = "dssc.v0.4.environment.v1"

_SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_SOURCES = (
    "scripts/validate.py",
    "scripts/dssc_validation/entrypoint_catalog.py",
    "scripts/dssc_validation/evidence.py",
    "scripts/dssc_validation/hashing.py",
    "scripts/dssc_validation/paths.py",
    "scripts/dssc_validation/provenance.py",
    "scripts/dssc_validation/suite_registry.py",
    "scripts/dssc_validation/v04_classifier.py",
    "scripts/dssc_validation/v04_harness.py",
    "scripts/dssc_validation/v04_manifest.py",
    "scripts/dssc_validation/v04_report.py",
    "scripts/dssc_validation/v04_reporter.py",
)
_DISTRIBUTIONS = ("rdflib", "pyshacl", "PyLD", "jsonschema", "pip")


def _sanitize(value: Any, root: Path) -> Any:
    if isinstance(value, str):
        return normalized_text(value, root, Path(sys.executable))
    if isinstance(value, dict):
        return {str(key): _sanitize(item, root) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item, root) for item in value]
    return value


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""
    return completed.returncode, (completed.stdout or "").strip()


def _source_state(root: Path, profile: str) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    if profile == "host":
        commit_code, commit = _git(root, "rev-parse", "HEAD")
        dirty_code, dirty = _git(root, "status", "--porcelain")
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


def collect_v04_environment(root: Path, profile: str) -> dict[str, Any]:
    """Collect machine-local values in a sidecar excluded from rerun equality."""
    if profile not in {"host", "container"}:
        raise ValueError("v0.4 profile must be host or container")
    source_state, issues = _source_state(root, profile)
    versions: dict[str, str | None] = {}
    for distribution in _DISTRIBUTIONS:
        try:
            versions[distribution] = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            versions[distribution] = None
            issues.append(f"required distribution is missing: {distribution}")
    return {
        "schema": ENVIRONMENT_SCHEMA,
        "suite": "v0.4",
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
        "versions": versions,
        "issues": sorted(set(issues)),
    }


def finalize_v04_result(
    root: Path,
    profile: str,
    payload: dict[str, Any],
    required_sources: Iterable[str] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind source provenance and fail closed on incomplete evidence."""
    required = tuple(dict.fromkeys((*_REQUIRED_SOURCES, *required_sources)))
    source_hashes, source_issues = collect_loaded_source_hashes(root, required)
    environment = collect_v04_environment(root, profile)
    successful = (
        payload.get("program_status") == "SUCCESS"
        and payload.get("exit_code") == 0
        and not source_issues
        and not environment["issues"]
    )
    result = {
        "schema": RESULT_SCHEMA,
        "suite": "v0.4",
        "profile": profile,
        **payload,
        "source_hashes": source_hashes,
        "source_hash_issues": sorted(source_issues),
        "program_status": "SUCCESS" if successful else "ERROR",
        "exit_code": 0 if successful else 1,
        "message": (
            "v0.4 fixture validation passed"
            if successful
            else payload.get("message", "v0.4 fixture validation failed")
        ),
    }
    result = _sanitize(result, root)
    assert_normalized_result(result)
    return result, environment


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_v04_markdown(result: dict[str, Any]) -> str:
    """Render Markdown solely from the normalized results JSON."""
    counts = result.get("counts", {})
    lines = [
        "# v0.4 four-state fixture validation",
        "",
        f"- program_status: `{_md(result.get('program_status'))}`",
        f"- exit_code: `{_md(result.get('exit_code'))}`",
        f"- contract_version: `{_md(result.get('registry_contract_version'))}`",
        f"- registry_sha256: `{_md(result.get('registry_sha256'))}`",
        f"- test manifest SHA-256: `{_md(result.get('test_manifest_sha256'))}`",
        f"- Shape SHA-256: `{_md(result.get('shape_sha256'))}`",
        "",
        "## Counts",
        "",
        "| discovered | executed | passed | failed | skipped |",
        "|---:|---:|---:|---:|---:|",
        (
            f"| {counts.get('discovered', 0)} | {counts.get('executed', 0)} | "
            f"{counts.get('passed', 0)} | {counts.get('failed', 0)} | "
            f"{counts.get('skipped', 0)} |"
        ),
        "",
        "## Business statuses",
        "",
        "| PASS | FAIL | INAPPLICABLE | UNTESTABLE |",
        "|---:|---:|---:|---:|",
    ]
    status_counts = result.get("business_status_counts", {})
    lines.append(
        f"| {status_counts.get('PASS', 0)} | {status_counts.get('FAIL', 0)} | "
        f"{status_counts.get('INAPPLICABLE', 0)} | "
        f"{status_counts.get('UNTESTABLE', 0)} |"
    )
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| case | expected | actual | program | assertions |",
            "|---|---|---|---|---:|",
        ]
    )
    for case in result.get("case_results", []):
        assertions = case.get("assertions", []) if isinstance(case, dict) else []
        passed_assertions = sum(
            1
            for assertion in assertions
            if isinstance(assertion, dict) and assertion.get("passed") is True
        )
        lines.append(
            f"| `{_md(case.get('case_id'))}` | "
            f"`{_md(case.get('expected_business_status'))}` | "
            f"`{_md(case.get('actual_business_status'))}` | "
            f"`{_md(case.get('program_status'))}` | "
            f"{passed_assertions}/{len(assertions)} |"
        )
    lines.append("")
    return "\n".join(lines)


def _prepare_output(root: Path) -> Path:
    root = root.resolve()
    current = root
    for name in ("build", "validation", "v0.4"):
        current = current / name
        if current.is_symlink() or bool(
            getattr(current, "is_junction", lambda: False)()
        ):
            raise ValueError(f"v0.4 output component is a link: {name}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"v0.4 output component is not a directory: {name}")
        current.mkdir(exist_ok=True)
    current.resolve().relative_to(root)
    return current


def write_v04_evidence(
    root: Path,
    result: dict[str, Any],
    environment: dict[str, Any],
) -> tuple[Path, Path, Path]:
    """Write the three exact Phase 05 outputs atomically."""
    output = _prepare_output(root)
    result_path = output / "results.json"
    markdown_path = output / "report.md"
    environment_path = output / "run-environment.json"
    atomic_write_json(result_path, result)
    atomic_write_text(markdown_path, render_v04_markdown(result))
    sidecar = dict(environment)
    sidecar["result_file"] = "results.json"
    sidecar["result_sha256"] = sha256_file(result_path)
    sidecar["report_file"] = "report.md"
    sidecar["report_sha256"] = sha256_file(markdown_path)
    atomic_write_json(environment_path, sidecar)
    return result_path, markdown_path, environment_path


__all__ = [
    "collect_v04_environment",
    "finalize_v04_result",
    "render_v04_markdown",
    "write_v04_evidence",
]
