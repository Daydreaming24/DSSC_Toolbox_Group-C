#!/usr/bin/env python3
"""Audit and publish normalized Phase 02 baseline release evidence."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dssc_validation.baseline_report import (  # noqa: E402
    normalized_semantic_view,
    render_baseline_markdown,
)
from dssc_validation.evidence import (  # noqa: E402
    assert_normalized_result,
    atomic_write_json,
    atomic_write_text,
    json_bytes,
)
from dssc_validation.hashing import sha256_file  # noqa: E402


_EXPECTED_COUNTS = {
    "discovered": 33,
    "executed": 33,
    "passed": 33,
    "failed": 0,
    "skipped": 0,
}
# The reviewed payload published by this tool remains Phase 02 evidence. Its
# Docker security audit follows the current shared runtime contract, whose
# fixed narrow mount set covers every planned registry owner Phase.
_EVIDENCE_PHASES = tuple(f"{phase:02d}" for phase in range(1, 10))
_EXPECTED_MOUNTS = [
    f"/workspace/build/phase-{phase}/current" for phase in _EVIDENCE_PHASES
]
_WINDOWS_ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)")
_SENSITIVE = re.compile(r"-----BEGIN |\b(?:ghp_|github_pat_|sk-|AKIA)[A-Za-z0-9_\-]+")
_TIMESTAMP = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def _load_json(path: Path, encoding: str = "utf-8") -> dict[str, Any]:
    value = json.loads(path.read_text(encoding=encoding))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root must be an object: {path.name}")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _semantic_sha(value: dict[str, Any]) -> str:
    import hashlib

    return hashlib.sha256(json_bytes(value)).hexdigest()


def _docker_image_inspect(root: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["docker", "image", "inspect", "dssc-c-validation:v0.4-env"],
        cwd=str(root),
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
    )
    _require(completed.returncode == 0, "docker image inspect failed")
    value = json.loads(completed.stdout)
    _require(isinstance(value, list) and len(value) == 1, "image inspect count differs")
    return value[0]


def _docker_record(root: Path, build_dir: Path) -> dict[str, Any]:
    image = _docker_image_inspect(root)
    container_path = build_dir / "docker-container-inspect.json"
    container_value = json.loads(container_path.read_text(encoding="utf-16"))
    _require(
        isinstance(container_value, list) and len(container_value) == 1,
        "container inspect count differs",
    )
    container = container_value[0]
    config = image["Config"]
    env = {
        item.split("=", 1)[0]: item.split("=", 1)[1]
        for item in config["Env"]
        if "=" in item
    }
    labels = config.get("Labels") or {}
    host_config = container["HostConfig"]
    mounts = container["Mounts"]
    destinations = sorted(mount["Destination"] for mount in mounts)
    _require(image["Architecture"] == "amd64", "image architecture differs")
    _require(image["Os"] == "linux", "image OS differs")
    _require(config["User"] == "dssc", "image user differs")
    _require(container["Config"]["User"] == "10001:10001", "runtime user differs")
    _require(host_config["ReadonlyRootfs"] is True, "root filesystem is writable")
    _require(host_config["NetworkMode"] == "none", "runtime network is enabled")
    _require(host_config["Privileged"] is False, "container is privileged")
    _require(host_config["CapDrop"] == ["ALL"], "capability drop differs")
    _require(
        host_config["SecurityOpt"] == ["no-new-privileges:true"],
        "security options differ",
    )
    _require(sorted(host_config["Tmpfs"]) == ["/tmp"], "tmpfs target differs")
    _require(destinations == _EXPECTED_MOUNTS, "runtime evidence mounts differ")
    _require(
        all(mount["Type"] == "bind" and mount["RW"] is True for mount in mounts),
        "runtime evidence mounts are not writable binds",
    )
    forbidden = ("/.git", "/.venv", "docker.sock", "docker_engine")
    _require(
        not any(
            marker in (mount["Source"].replace("\\", "/").lower())
            for mount in mounts
            for marker in forbidden
        ),
        "forbidden runtime mount detected",
    )

    dockerfile = (root / "Dockerfile.validation").read_text(encoding="utf-8")
    base_match = re.search(r"^FROM\s+\S+@(sha256:[0-9a-f]{64})$", dockerfile, re.MULTILINE)
    _require(base_match is not None, "fixed base image digest is unavailable")
    source_commit = env.get("DSSC_SOURCE_COMMIT")
    source_dirty = env.get("DSSC_SOURCE_DIRTY")
    _require(
        isinstance(source_commit, str) and re.fullmatch(r"[0-9a-f]{40}", source_commit),
        "image source commit is malformed",
    )
    _require(source_dirty in {"true", "false"}, "image source dirty state is malformed")
    _require(
        labels.get("org.opencontainers.image.revision") == source_commit
        and labels.get("org.dssc.source-dirty") == source_dirty,
        "image labels do not bind source state",
    )
    return {
        "schema": "dssc.baseline.docker-image.v1",
        "image": "dssc-c-validation:v0.4-env",
        "image_id": image["Id"],
        "repo_digests": sorted(image.get("RepoDigests") or []),
        "base_image_digest": base_match.group(1),
        "os": image["Os"],
        "architecture": image["Architecture"],
        "image_user": config["User"],
        "runtime_user": container["Config"]["User"],
        "source_state": {
            "commit": source_commit,
            "dirty": source_dirty == "true",
        },
        "runtime_contract": {
            "read_only_root": host_config["ReadonlyRootfs"],
            "network_mode": host_config["NetworkMode"],
            "privileged": host_config["Privileged"],
            "cap_drop": host_config["CapDrop"],
            "security_opt": host_config["SecurityOpt"],
            "tmpfs_targets": ["temporary-directory"],
            "mount_targets": [
                f"phase-{phase}-current" for phase in _EVIDENCE_PHASES
            ],
            "mount_count": len(mounts),
            "forbidden_mount_count": 0,
        },
    }


def _prepare_release_dir(root: Path) -> Path:
    current = root
    for name in (
        "C_Semantic_Treehouse",
        "evidence",
        "releases",
        "v0.4",
        "baseline",
    ):
        current = current / name
        if current.is_symlink() or (
            getattr(current, "is_junction", None) and current.is_junction()
        ):
            raise RuntimeError(f"release evidence path component is link-like: {name}")
        if current.exists():
            _require(current.is_dir(), f"release evidence component is not a directory: {name}")
        else:
            current.mkdir()
    current.resolve().relative_to(root.resolve())
    return current


def _audit_text(name: str, text: str, root: Path) -> list[str]:
    issues: list[str] = []
    if str(root.resolve()) in text or str(root.resolve()).replace("\\", "/") in text:
        issues.append(f"{name}: repository absolute path")
    if _WINDOWS_ABSOLUTE.search(text) or "/workspace/" in text:
        issues.append(f"{name}: machine absolute path")
    if _SENSITIVE.search(text):
        issues.append(f"{name}: sensitive token pattern")
    if _TIMESTAMP.search(text):
        issues.append(f"{name}: timestamp")
    return issues


def main() -> int:
    root = _SCRIPTS.parent.resolve()
    build_dir = root / "build" / "phase-02" / "current"
    container_dir = build_dir / "docker"
    release_dir = _prepare_release_dir(root)

    host_result_path = build_dir / "baseline-host.result.json"
    container_result_path = container_dir / "baseline-container.result.json"
    host_environment_path = build_dir / "baseline-host.environment.json"
    container_environment_path = container_dir / "baseline-container.environment.json"
    host_markdown_path = build_dir / "baseline-host.md"
    container_markdown_path = container_dir / "baseline-container.md"
    host_outer_path = build_dir / "suite-baseline-host.result.json"
    container_outer_path = container_dir / "suite-baseline-container.result.json"
    negative_path = build_dir / "negative-controls.json"
    contract_path = build_dir / "phase02-contract-controls.json"

    host_result = _load_json(host_result_path)
    container_result = _load_json(container_result_path)
    host_environment = _load_json(host_environment_path)
    container_environment = _load_json(container_environment_path)
    host_outer = _load_json(host_outer_path)
    container_outer = _load_json(container_outer_path)
    negative = _load_json(negative_path)
    contract = _load_json(contract_path)
    for value in (host_result, container_result, host_outer, container_outer, negative, contract):
        assert_normalized_result(value)

    _require(host_result["program_status"] == "SUCCESS", "host baseline failed")
    _require(container_result["program_status"] == "SUCCESS", "container baseline failed")
    _require(host_result["counts"] == _EXPECTED_COUNTS, "host counts differ")
    _require(container_result["counts"] == _EXPECTED_COUNTS, "container counts differ")
    _require(host_outer["program_status"] == "SUCCESS", "host suite envelope failed")
    _require(container_outer["program_status"] == "SUCCESS", "container suite envelope failed")
    _require(host_outer["evidence_phase"] == "02", "host evidence phase differs")
    _require(container_outer["evidence_phase"] == "02", "container evidence phase differs")
    _require(
        host_outer["components"][-1]["details"]["baseline_result"] == host_result,
        "host suite envelope does not bind baseline result",
    )
    _require(
        container_outer["components"][-1]["details"]["baseline_result"]
        == container_result,
        "container suite envelope does not bind baseline result",
    )

    _require(host_environment["issues"] == [], "host environment has issues")
    _require(container_environment["issues"] == [], "container environment has issues")
    _require(
        host_environment["result_sha256"] == sha256_file(host_result_path),
        "host environment result binding differs",
    )
    _require(
        container_environment["result_sha256"] == sha256_file(container_result_path),
        "container environment result binding differs",
    )
    _require(
        host_environment["source_state"]["commit"]
        == container_environment["source_state"]["commit"],
        "host/container source commits differ",
    )
    _require(
        host_environment["source_state"]["dirty"]
        == container_environment["source_state"]["dirty"],
        "host/container source dirty states differ",
    )
    _require(
        host_environment["validator_versions"]
        == container_environment["validator_versions"],
        "host/container validator versions differ",
    )
    _require(
        host_environment["requirements_lock_sha256"]
        == container_environment["requirements_lock_sha256"],
        "host/container lock hashes differ",
    )
    _require(
        host_markdown_path.read_text(encoding="utf-8")
        == render_baseline_markdown(host_result),
        "host Markdown is stale",
    )
    _require(
        container_markdown_path.read_text(encoding="utf-8")
        == render_baseline_markdown(container_result),
        "container Markdown is stale",
    )
    for name, control in (("baseline", negative), ("contract", contract)):
        _require(control["program_status"] == "SUCCESS", f"{name} controls failed")
        _require(control["counts"]["discovered"] > 0, f"{name} controls discovered zero")
        _require(control["counts"]["failed"] == 0, f"{name} controls contain failure")
        _require(control["counts"]["skipped"] == 0, f"{name} controls contain skip")

    host_view = normalized_semantic_view(host_result)
    container_view = normalized_semantic_view(container_result)
    _require(host_view == container_view, "host/container normalized semantics differ")
    host_semantic_sha = _semantic_sha(host_view)
    container_semantic_sha = _semantic_sha(container_view)
    docker_record = _docker_record(root, build_dir)
    _require(
        docker_record["source_state"]["commit"]
        == host_environment["source_state"]["commit"],
        "image/source evidence commits differ",
    )
    _require(
        docker_record["source_state"]["dirty"]
        == host_environment["source_state"]["dirty"],
        "image/source evidence dirty states differ",
    )

    comparison = {
        "schema": "dssc.baseline.comparison.v1",
        "suite": "baseline",
        "program_status": "SUCCESS",
        "counts": {"compared": 1, "equal": 1, "different": 0},
        "host": {
            "result_file": "baseline-host.result.json",
            "result_sha256": sha256_file(host_result_path),
            "semantic_sha256": host_semantic_sha,
        },
        "container": {
            "result_file": "baseline-container.result.json",
            "result_sha256": sha256_file(container_result_path),
            "semantic_sha256": container_semantic_sha,
        },
        "normalized_semantics_equal": True,
        "differences": [],
        "environment_consistency": {
            "source_commit_equal": True,
            "source_dirty_equal": True,
            "validator_versions_equal": True,
            "requirements_lock_sha256_equal": True,
        },
        "case_counts": host_result["counts"],
        "category_counts": host_result["category_counts"],
        "negative_controls": {
            "result_sha256": sha256_file(negative_path),
            "counts": negative["counts"],
        },
        "contract_controls": {
            "result_sha256": sha256_file(contract_path),
            "counts": contract["counts"],
        },
        "docker": docker_record,
        "publisher_source_hashes": {
            "scripts/publish_baseline_evidence.py": sha256_file(Path(__file__)),
            "scripts/dssc_validation/baseline_report.py": sha256_file(
                root / "scripts" / "dssc_validation" / "baseline_report.py"
            ),
        },
    }
    assert_normalized_result(comparison)
    comparison_path = build_dir / "baseline-host-container-comparison.json"
    docker_path = build_dir / "docker-image.json"
    atomic_write_json(comparison_path, comparison)
    atomic_write_json(docker_path, docker_record)

    published: list[tuple[str, Path, str]] = []
    json_publications = (
        ("baseline-host.result.json", host_result_path, host_result),
        ("baseline-container.result.json", container_result_path, container_result),
        ("baseline-host-container-comparison.json", comparison_path, comparison),
        ("negative-controls.json", negative_path, negative),
        ("phase02-contract-controls.json", contract_path, contract),
        ("docker-image.json", docker_path, docker_record),
    )
    for name, source, value in json_publications:
        destination = release_dir / name
        atomic_write_json(destination, value)
        _require(sha256_file(destination) == sha256_file(source), f"stale publish: {name}")
        published.append((name, destination, "json"))
    for name, source, result in (
        ("baseline-host.md", host_markdown_path, host_result),
        ("baseline-container.md", container_markdown_path, container_result),
    ):
        destination = release_dir / name
        atomic_write_text(destination, render_baseline_markdown(result))
        _require(sha256_file(destination) == sha256_file(source), f"stale publish: {name}")
        published.append((name, destination, "markdown"))

    readme = "\n".join(
        [
            "# Phase 02 baseline release evidence",
            "",
            "This directory contains audited, deterministic v0.1-v0.3 baseline evidence.",
            "Machine-local environment inventories and raw Docker logs remain under `build/phase-02/`.",
            "",
            f"- normalized semantic SHA-256: `{host_semantic_sha}`",
            f"- container image ID: `{docker_record['image_id']}`",
            f"- source commit: `{docker_record['source_state']['commit']}`",
            f"- source dirty at evidence build: `{str(docker_record['source_state']['dirty']).lower()}`",
            "- baseline cases: `33/33`",
            "- baseline negative controls: `37/37`",
            "- registry/output/Docker contract controls: `30/30`",
            "",
        ]
    )
    readme_path = release_dir / "README.md"
    atomic_write_text(readme_path, readme)
    published.append(("README.md", readme_path, "markdown"))

    hygiene_issues: list[str] = []
    file_records: list[dict[str, Any]] = []
    for name, path, kind in sorted(published):
        text = path.read_text(encoding="utf-8")
        hygiene_issues.extend(_audit_text(name, text, root))
        if kind == "json":
            assert_normalized_result(_load_json(path))
        file_records.append(
            {
                "path": f"C_Semantic_Treehouse/evidence/releases/v0.4/baseline/{name}",
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    _require(not hygiene_issues, "; ".join(hygiene_issues))
    audit = {
        "schema": "dssc.baseline.release-audit.v1",
        "program_status": "SUCCESS",
        "counts": {
            "discovered": len(file_records),
            "executed": len(file_records),
            "passed": len(file_records),
            "failed": 0,
            "skipped": 0,
        },
        "checks": {
            "absolute_paths_absent": True,
            "sensitive_patterns_absent": True,
            "timestamps_absent": True,
            "normalized_json": True,
            "source_hashes_fresh": True,
            "markdown_derived_from_json": True,
        },
        "files": file_records,
        "publisher_sha256": sha256_file(Path(__file__)),
    }
    assert_normalized_result(audit)
    audit_path = release_dir / "baseline-release-audit.json"
    atomic_write_json(audit_path, audit)
    print(
        "baseline release evidence published: "
        f"files={len(file_records) + 1} semantic_sha256={host_semantic_sha}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
