#!/usr/bin/env python3
"""Unified, registry-driven validation dispatcher."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dssc_validation import PUBLIC_SUITE_IDS  # noqa: E402
from dssc_validation.entrypoint_catalog import resolve_entrypoint  # noqa: E402
from dssc_validation.evidence import (  # noqa: E402
    atomic_write_text,
    normalized_text,
    write_result_and_machine,
)
from dssc_validation.hashing import sha256_file, sha256_text  # noqa: E402
from dssc_validation.paths import (  # noqa: E402
    phase_build_dir,
    repository_root,
    requirements_lock_path,
)
from dssc_validation.provenance import collect_loaded_source_hashes  # noqa: E402
from dssc_validation.profile_contract import container_contract_check  # noqa: E402
from dssc_validation.suite_registry import (  # noqa: E402
    expand_suite_components,
    load_and_validate_registry,
)


_FIXED_SUITE_OWNER_PHASE = {
    "frozen": "01",
    "environment": "01",
    "baseline": "02",
    "traceability": "03",
    "v0.4-model": "04",
    "v0.4": "05",
    "all": "05",
}


def _run(command: list[str], root: Path, timeout: int = 30) -> dict[str, Any]:
    child_env = {
        **os.environ,
        "PYTHONUTF8": "1",
        "PIP_CONFIG_FILE": os.devnull,
    }
    for name in ("PIP_TARGET", "PIP_PREFIX", "PIP_ROOT", "PIP_USER"):
        child_env.pop(name, None)
    try:
        completed = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=child_env,
            check=False,
            timeout=timeout,
        )
        return {
            "exit_code": completed.returncode,
            "stdout": (completed.stdout or "").strip(),
            "stderr": (completed.stderr or "").strip(),
        }
    except FileNotFoundError:
        return {"exit_code": 127, "stdout": "", "stderr": "not found"}
    except subprocess.TimeoutExpired:
        return {"exit_code": 124, "stdout": "", "stderr": "timeout"}


def _git_machine(root: Path, profile: str) -> dict[str, Any]:
    if profile == "container":
        return {
            "status": "not_required",
            "reason": "container profile does not require Git CLI",
        }
    version = _run(["git", "--version"], root)
    commit = _run(["git", "rev-parse", "HEAD"], root)
    dirty = _run(["git", "status", "--porcelain"], root)
    return {
        "status": "PASS"
        if version["exit_code"] == commit["exit_code"] == dirty["exit_code"] == 0
        else "FAIL",
        "version": version["stdout"] or version["stderr"],
        "commit": commit["stdout"] or None,
        "dirty": bool(dirty["stdout"]) if dirty["exit_code"] == 0 else None,
        "exit_codes": {
            "version": version["exit_code"],
            "commit": commit["exit_code"],
            "dirty": dirty["exit_code"],
        },
    }


def _base_machine_inventory(root: Path, suite: str, profile: str) -> dict[str, Any]:
    pip = _run(
        [
            sys.executable,
            "-I",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "--version",
        ],
        root,
    )
    direct_versions: dict[str, str | None] = {}
    for distribution in (
        "rdflib",
        "pyshacl",
        "PyLD",
        "jsonschema",
        "PyYAML",
        "openapi-spec-validator",
    ):
        try:
            direct_versions[distribution] = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            direct_versions[distribution] = None
    return {
        "schema": "dssc.suite.machine.v1",
        "suite": suite,
        "profile": profile,
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
            "repository_root": str(root),
            "cwd": str(Path.cwd()),
        },
        "pip": {
            "raw": pip["stdout"] or pip["stderr"],
            "exit_code": pip["exit_code"],
        },
        "direct_dependency_versions": direct_versions,
        "git": _git_machine(root, profile),
        "components": [],
    }


def _result_skeleton(
    suite: str,
    profile: str,
    contract_version: str | None,
    registry_sha256: str | None,
    verbose: bool,
) -> dict[str, Any]:
    return {
        "schema": "dssc.suite.result.v1",
        "suite": suite,
        "profile": profile,
        "contract_version": contract_version,
        "registry_path": "C_Semantic_Treehouse/manifests/validation-suites.json",
        "registry_sha256": registry_sha256,
        "evidence_phase": None,
        "normalized_command": [
            "python",
            "scripts/validate.py",
            "--suite",
            suite,
            "--profile",
            profile,
        ]
        + (["--verbose"] if verbose else []),
        "requirements_lock_sha256": None,
        "program_status": "ERROR",
        "exit_code": 1,
        "message": "",
        "components": [],
        "counts": {
            "discovered": 0,
            "executed": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        },
        "source_hashes": {},
        "source_hash_issues": [],
    }


def _sanitize(value: Any, root: Path) -> Any:
    if isinstance(value, str):
        return normalized_text(value, root, Path(sys.executable))
    if isinstance(value, dict):
        return {key: _sanitize(item, root) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item, root) for item in value]
    return value


def _validated_component_result(value: Any) -> dict[str, Any]:
    allowed_keys = {"status", "program_status", "message", "details", "machine_details"}
    issues: list[str] = []
    if not isinstance(value, dict):
        issues.append("checker return value must be an object")
        value = {}
    unknown = sorted(set(value) - allowed_keys)
    if unknown:
        issues.append("unknown checker result keys: " + ", ".join(unknown))
    status = value.get("status")
    program_status = value.get("program_status")
    if (status, program_status) not in (("PASS", "SUCCESS"), ("FAIL", "ERROR")):
        issues.append("status/program_status must be PASS/SUCCESS or FAIL/ERROR")
    message = value.get("message")
    if not isinstance(message, str) or not message:
        issues.append("message must be a non-empty string")
    details = value.get("details")
    machine_details = value.get("machine_details", {})
    if not isinstance(details, dict):
        issues.append("details must be an object")
    if not isinstance(machine_details, dict):
        issues.append("machine_details must be an object")
    if not issues:
        try:
            json.dumps(details, sort_keys=True)
            json.dumps(machine_details, sort_keys=True)
        except (TypeError, ValueError):
            issues.append("details and machine_details must be JSON serializable")
    if issues:
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "invalid checker result contract: " + "; ".join(issues),
            "details": {"contract_issues": issues},
            "machine_details": {},
        }
    return {
        "status": status,
        "program_status": program_status,
        "message": message,
        "details": details,
        "machine_details": machine_details,
    }


def _safe_stem(suite: str, profile: str) -> str:
    if suite in PUBLIC_SUITE_IDS:
        return f"suite-{suite}-{profile}"
    return f"suite-unknown-{sha256_text(suite)[:12]}-{profile}"


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        f"# Suite result: {result['suite']}",
        "",
        f"- profile: `{result['profile']}`",
        f"- program_status: `{result['program_status']}`",
        f"- exit_code: `{result['exit_code']}`",
        f"- contract_version: `{result['contract_version']}`",
        f"- registry_sha256: `{result['registry_sha256']}`",
        f"- evidence_phase: `{result['evidence_phase']}`",
        f"- message: {result['message']}",
        "",
        "## Counts",
        "",
    ]
    for name in ("discovered", "executed", "passed", "failed", "skipped"):
        lines.append(f"- {name}: {result['counts'][name]}")
    lines.extend(["", "## Components", ""])
    for component in result["components"]:
        lines.append(
            f"- `{component['id']}` suite=`{component['suite_id']}` "
            f"entrypoint=`{component['entrypoint']}` status=`{component['status']}`"
        )
    lines.append("")
    atomic_write_text(path, "\n".join(lines))


def _finish_and_write(
    root: Path,
    requested_suite: str,
    profile: str,
    result: dict[str, Any],
    machine: dict[str, Any],
    evidence_phase: str,
) -> int:
    source_hashes, source_issues = collect_loaded_source_hashes(
        root,
        required_relpaths=("scripts/validate.py", "scripts/doctor.py"),
    )
    result["source_hashes"] = source_hashes
    result["source_hash_issues"] = source_issues
    if source_issues:
        result["program_status"] = "ERROR"
        result["exit_code"] = 1
        result["message"] = "source provenance failed: " + "; ".join(source_issues)

    result = _sanitize(result, root)
    result["evidence_phase"] = evidence_phase
    output = phase_build_dir(evidence_phase, root)
    stem = _safe_stem(requested_suite, profile)
    result_path, machine_path = write_result_and_machine(
        output, stem, result, machine, evidence_phase=evidence_phase
    )
    _write_markdown(output / f"{stem}.md", result)
    print(
        f"suite={requested_suite} program_status={result['program_status']} "
        f"exit_code={result['exit_code']} "
        f"result={result_path.name} machine={machine_path.name}"
    )
    return int(result["exit_code"])


def _active_evidence_phase(registry: dict[str, Any] | None) -> str:
    """Select the latest implemented Phase through the controlled suite map."""
    if not isinstance(registry, dict):
        return "01"
    owner_issues = [
        f"suite {suite.get('id')!r} owner_phase must equal "
        f"{_FIXED_SUITE_OWNER_PHASE[suite['id']]!r}"
        for suite in registry.get("suites", [])
        if isinstance(suite, dict)
        and suite.get("id") in _FIXED_SUITE_OWNER_PHASE
        and suite.get("owner_phase") != _FIXED_SUITE_OWNER_PHASE[suite["id"]]
    ]
    if owner_issues:
        raise ValueError("; ".join(owner_issues))
    phases = [
        _FIXED_SUITE_OWNER_PHASE[suite["id"]]
        for suite in registry.get("suites", [])
        if isinstance(suite, dict)
        and suite.get("status") == "IMPLEMENTED"
        and suite.get("id") in _FIXED_SUITE_OWNER_PHASE
    ]
    return max(phases, default="01")


def _safe_evidence_phase(registry: dict[str, Any] | None) -> str:
    """Choose a bounded failure-output phase without trusting owner_phase."""
    if not isinstance(registry, dict):
        return "01"
    phases = [
        _FIXED_SUITE_OWNER_PHASE[suite["id"]]
        for suite in registry.get("suites", [])
        if isinstance(suite, dict)
        and suite.get("status") == "IMPLEMENTED"
        and suite.get("id") in _FIXED_SUITE_OWNER_PHASE
    ]
    return max(phases, default="01")


def run_suite(suite: str, profile: str, verbose: bool = False) -> int:
    if profile not in ("host", "container"):
        print("ERROR: profile must be host or container", file=sys.stderr)
        return 2
    if profile == "container":
        container_ok, _, _ = container_contract_check()
        if not container_ok:
            print(
                "ERROR: container profile requires the fixed linux/amd64 "
                "validation-image contract",
                file=sys.stderr,
            )
            return 2
    root = repository_root()
    load = load_and_validate_registry(root)
    owner_phase_issue: str | None = None
    try:
        evidence_phase = _active_evidence_phase(load.registry if load.ok else None)
    except ValueError as exc:
        owner_phase_issue = str(exc)
        evidence_phase = _safe_evidence_phase(load.registry)
    safe_suite = suite if suite in PUBLIC_SUITE_IDS else "UNKNOWN"
    result = _result_skeleton(
        safe_suite,
        profile,
        load.contract_version,
        load.registry_sha256,
        verbose,
    )
    machine = _base_machine_inventory(root, safe_suite, profile)
    lock = requirements_lock_path(root)
    result["requirements_lock_sha256"] = sha256_file(lock) if lock.is_file() else None

    if owner_phase_issue is not None:
        result["message"] = "validation-suites registry owner_phase is invalid"
        result["registry_issues"] = [
            {"code": "owner_phase", "message": owner_phase_issue}
        ]
        print(result["message"])
        return _finish_and_write(
            root, suite, profile, result, machine, evidence_phase
        )

    if suite not in PUBLIC_SUITE_IDS:
        result["normalized_command"][3] = "<UNKNOWN_SUITE>"
        result["requested_suite_sha256"] = sha256_text(suite)
        result["message"] = "unknown suite; legal values: " + ", ".join(PUBLIC_SUITE_IDS)
        result["exit_code"] = 2
        print(result["message"])
        return _finish_and_write(
            root, suite, profile, result, machine, evidence_phase
        )

    if not load.ok or load.registry is None:
        result["message"] = "validation-suites registry is invalid"
        result["registry_issues"] = [
            {"code": issue.code, "message": issue.message} for issue in load.issues
        ]
        print(result["message"])
        return _finish_and_write(
            root, suite, profile, result, machine, evidence_phase
        )

    components, error_code, error_message = expand_suite_components(
        load.registry, suite
    )
    if error_code == "NOT_IMPLEMENTED":
        result["message"] = f"NOT_IMPLEMENTED: {error_message}"
        result["not_implemented"] = True
        print(f"NOT_IMPLEMENTED suite={suite}")
        return _finish_and_write(
            root, suite, profile, result, machine, evidence_phase
        )
    if error_code is not None or components is None:
        result["message"] = f"{error_code}: {error_message}"
        print(result["message"])
        return _finish_and_write(
            root, suite, profile, result, machine, evidence_phase
        )

    result["counts"]["discovered"] = len(components)
    context: dict[str, Any] = {
        "repository_root": root,
        "profile": profile,
        "verbose": verbose,
        "suite": suite,
        "contract_version": load.contract_version,
        "registry_sha256": load.registry_sha256,
        "evidence_phase": evidence_phase,
        "output_dir": phase_build_dir(evidence_phase, root),
    }
    passed = True
    for component in components:
        component_id = component["id"]
        entrypoint = component["entrypoint"]
        owner_suite = component["suite_id"]
        try:
            function = resolve_entrypoint(entrypoint, owner_suite)
            component_result = _validated_component_result(function(context))
        except Exception as exc:  # noqa: BLE001
            component_result = {
                "status": "FAIL",
                "program_status": "ERROR",
                "message": f"entrypoint {entrypoint!r} raised: {exc}",
                "details": {},
                "machine_details": {},
            }
        status = component_result.get("status", "FAIL")
        result["counts"]["executed"] += 1
        if status == "PASS":
            result["counts"]["passed"] += 1
        else:
            result["counts"]["failed"] += 1
            passed = False
        result["components"].append(
            {
                "id": component_id,
                "suite_id": owner_suite,
                "entrypoint": entrypoint,
                "status": status,
                "program_status": component_result.get("program_status"),
                "message": component_result.get("message"),
                "details": component_result.get("details") or {},
            }
        )
        machine["components"].append(
            {
                "id": component_id,
                "suite_id": owner_suite,
                "entrypoint": entrypoint,
                "details": component_result.get("machine_details") or {},
            }
        )

    result["program_status"] = "SUCCESS" if passed else "ERROR"
    result["exit_code"] = 0 if passed else 1
    result["message"] = f"suite {suite} passed" if passed else f"suite {suite} failed"
    return _finish_and_write(root, suite, profile, result, machine, evidence_phase)


def _resolve_profile(cli_profile: str | None) -> str:
    env_profile = os.environ.get("DSSC_VALIDATION_PROFILE", "").strip()
    if env_profile and env_profile not in ("host", "container"):
        raise ValueError("DSSC_VALIDATION_PROFILE must be host or container")
    if cli_profile and env_profile and cli_profile != env_profile:
        raise ValueError(
            f"profile mismatch: --profile={cli_profile} and "
            f"DSSC_VALIDATION_PROFILE={env_profile}"
        )
    return cli_profile or env_profile or "host"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DSSC unified validation entrypoint")
    parser.add_argument("--suite", "-s", required=True)
    parser.add_argument("--profile", choices=("host", "container"), default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    try:
        profile = _resolve_profile(args.profile)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return run_suite(args.suite, profile, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
