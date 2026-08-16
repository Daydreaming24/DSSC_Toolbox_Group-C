"""Environment doctor with normalized results and machine sidecars."""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import re
import subprocess
import struct
import sys
from pathlib import Path
from typing import Any

from dssc_validation import (
    EXPECTED_ENSUREPIP_VERSION,
    EXPECTED_PYTHON_VERSION,
    FIXED_PIP_VERSION,
)
from dssc_validation.evidence import normalized_text, write_result_and_machine
from dssc_validation.hashing import sha256_file
from dssc_validation.lock_contract import (
    PYPI_INDEX,
    canonical_name,
    compare_environment_to_locks,
    parse_hash_lock,
)
from dssc_validation.paths import (
    bootstrap_lock_path,
    is_repo_venv_interpreter,
    lock_metadata_path,
    phase01_build_dir,
    prepare_phase01_build_dir,
    python_version_file,
    repository_root as canonical_repository_root,
    requirements_in_path,
    requirements_lock_path,
    validation_suites_path,
    validation_suites_schema_path,
)
from dssc_validation.provenance import collect_loaded_source_hashes
from dssc_validation.profile_contract import container_contract_check
from dssc_validation.venv_contract import check_current_venv


DIRECT_DEPENDENCIES = (
    ("rdflib", "rdflib", "rdflib"),
    ("pyshacl", "pyshacl", "pyshacl"),
    ("PyLD", "PyLD", "pyld"),
    ("jsonschema", "jsonschema", "jsonschema"),
    ("PyYAML", "PyYAML", "yaml"),
    (
        "openapi-spec-validator",
        "openapi-spec-validator",
        "openapi_spec_validator",
    ),
)

EXPECTED_BOOTSTRAP_TOOLS = {
    "pip": "25.0.1",
    "pip-tools": "7.4.1",
    "setuptools": "75.8.2",
    "wheel": "0.45.1",
}


def _expected_generator_command(output: str, source: str) -> list[str]:
    return [
        "python",
        "-m",
        "piptools",
        "compile",
        "--no-config",
        "--resolver=backtracking",
        "--generate-hashes",
        "--allow-unsafe",
        "--strip-extras",
        "--newline=lf",
        "--index-url",
        PYPI_INDEX,
        "--output-file",
        output,
        source,
    ]

REQUIRED_FILES = (
    ".python-version",
    "requirements.in",
    "requirements.lock",
    "requirements-bootstrap.in",
    "requirements-bootstrap.lock",
    "requirements.lock.json",
    "Dockerfile.validation",
    "scripts/bootstrap.ps1",
    "scripts/bootstrap.sh",
    "scripts/doctor.py",
    "scripts/validate.py",
    "scripts/verify_frozen_files.py",
    "scripts/dssc_validation/venv_contract.py",
    "C_Semantic_Treehouse/manifests/validation-suites.json",
    "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json",
    "docs/provenance/manifests/frozen-files-SHA256SUMS",
)

REQUIRED_DIRECTORIES = (
    "scripts",
    "C_Semantic_Treehouse/manifests",
    "docs/provenance/manifests",
    "inputs/source-archives/received",
)


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _not_required(reason: str) -> dict[str, Any]:
    return {"status": "not_required", "reason": reason}


def _run(
    command: list[str],
    cwd: Path,
    timeout: int = 30,
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={
                **os.environ,
                "PYTHONUTF8": "1",
                "PIP_CONFIG_FILE": os.devnull,
            },
            check=False,
            timeout=timeout,
        )
        return completed.returncode, completed.stdout or "", completed.stderr or ""
    except FileNotFoundError:
        return 127, "", "not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def _version_triple(text: str) -> str | None:
    match = re.search(r"(\d+\.\d+\.\d+)", text)
    return match.group(1) if match else None


def _pip_version_from_cli(text: str) -> str | None:
    """Parse ``python -m pip --version`` output without matching upgrade notices.

    Recent pip may emit text like ``A new release of pip is available: 26.2.1``
    before or after the real ``pip 25.0.1 from ...`` line. The first bare
    ``X.Y.Z`` match is therefore not safe.
    """
    match = re.search(r"(?im)^\s*pip\s+(\d+\.\d+\.\d+)\b", text)
    if match:
        return match.group(1)
    match = re.search(r"(?i)\bpip\s+(\d+\.\d+\.\d+)\b", text)
    return match.group(1) if match else None


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "root must be an object"
    return value, None


def _metadata_contract(root: Path) -> dict[str, Any]:
    metadata_path = lock_metadata_path(root)
    metadata, error = _read_json(metadata_path)
    runtime_lock = requirements_lock_path(root)
    bootstrap_lock = bootstrap_lock_path(root)
    runtime_input = requirements_in_path(root)
    bootstrap_input = root / "requirements-bootstrap.in"

    actual_hashes = {
        "requirements.in": sha256_file(runtime_input) if runtime_input.is_file() else None,
        "requirements-bootstrap.in": (
            sha256_file(bootstrap_input) if bootstrap_input.is_file() else None
        ),
        "requirements.lock": sha256_file(runtime_lock) if runtime_lock.is_file() else None,
        "requirements-bootstrap.lock": (
            sha256_file(bootstrap_lock) if bootstrap_lock.is_file() else None
        ),
    }
    checks: dict[str, bool] = {
        "metadata_readable": metadata is not None,
        "schema": False,
        "python_version": False,
        "ensurepip_version": False,
        "index": False,
        "generator": False,
        "generator_commands": False,
        "self_hosted_regeneration": False,
        "bootstrap_tools": False,
        "hash_bindings": False,
    }
    expected_hashes: dict[str, Any] = {}
    if metadata is not None:
        checks["schema"] = (
            metadata.get("schema") == "dssc.requirements_lock_metadata.v1"
        )
        python_info = metadata.get("python")
        if isinstance(python_info, dict):
            checks["python_version"] = (
                python_info.get("implementation") == "CPython"
                and python_info.get("version") == EXPECTED_PYTHON_VERSION
            )
            checks["ensurepip_version"] = (
                python_info.get("ensurepip_version") == EXPECTED_ENSUREPIP_VERSION
            )
        checks["index"] = metadata.get("index") == PYPI_INDEX
        generator = metadata.get("generator")
        if isinstance(generator, dict):
            checks["generator"] = (
                generator.get("name") == "pip-tools"
                and generator.get("version") == "7.4.1"
                and generator.get("pip_version") == FIXED_PIP_VERSION
            )
            commands = generator.get("commands")
            checks["generator_commands"] = isinstance(commands, dict) and commands == {
                "bootstrap": _expected_generator_command(
                    "requirements-bootstrap.lock", "requirements-bootstrap.in"
                ),
                "runtime": _expected_generator_command(
                    "requirements.lock", "requirements.in"
                ),
            }
            checks["self_hosted_regeneration"] = (
                generator.get("verified_self_hosted_regeneration") is True
            )
        checks["bootstrap_tools"] = (
            metadata.get("bootstrap_tools") == EXPECTED_BOOTSTRAP_TOOLS
        )
        inputs = metadata.get("inputs")
        locks = metadata.get("locks")
        if isinstance(inputs, dict) and isinstance(locks, dict):
            for name, section in (
                ("requirements.in", inputs),
                ("requirements-bootstrap.in", inputs),
                ("requirements.lock", locks),
                ("requirements-bootstrap.lock", locks),
            ):
                record = section.get(name)
                expected_hashes[name] = (
                    record.get("sha256") if isinstance(record, dict) else None
                )
            checks["hash_bindings"] = all(
                expected_hashes.get(name) == actual_hashes.get(name)
                for name in actual_hashes
            )

    ok = all(checks.values())
    return {
        "status": _status(ok),
        "checks": checks,
        "actual_sha256": actual_hashes,
        "expected_sha256": expected_hashes,
        "parse_error": error,
    }


def _pip_bootstrap_source_contract(root: Path) -> dict[str, Any]:
    """Audit that every bootstrap installer call uses an explicit interpreter."""
    source_paths = {
        "windows": root / "scripts" / "bootstrap.ps1",
        "linux": root / "scripts" / "bootstrap.sh",
        "container": root / "Dockerfile.validation",
        "venv_contract": root / "scripts" / "dssc_validation" / "venv_contract.py",
    }
    sources: dict[str, str] = {}
    readable = True
    for name, path in source_paths.items():
        try:
            sources[name] = path.read_text(encoding="utf-8-sig")
        except OSError:
            sources[name] = ""
            readable = False

    windows_lines = "\n".join(
        line for line in sources["windows"].splitlines() if not line.lstrip().startswith("#")
    )
    linux_lines = "\n".join(
        line for line in sources["linux"].splitlines() if not line.lstrip().startswith("#")
    )
    container_lines = "\n".join(
        line
        for line in sources["container"].splitlines()
        if not line.lstrip().startswith("#")
    )
    checks = {
        "sources_readable": readable,
        "windows_venv_python_m_pip": len(
            re.findall(
                r"&\s+\$VenvPython\s+-I\s+-m\s+pip\s+--isolated\b",
                windows_lines,
            )
        )
        >= 4,
        "linux_venv_python_m_pip": linux_lines.count(
            '"${VENV_PYTHON}" -I -m pip --isolated'
        )
        >= 4,
        "container_python_m_pip": container_lines.count(
            "python -I -m pip --isolated"
        )
        >= 3,
        "pip_config_file_is_os_devnull": (
            "$env:PIP_CONFIG_FILE = 'nul'" in windows_lines
            and "export PIP_CONFIG_FILE=/dev/null" in linux_lines
            and "PIP_CONFIG_FILE=/dev/null" in container_lines
        ),
        "pip_redirect_environment_cleared": (
            all(name in windows_lines for name in ("PIP_TARGET", "PIP_PREFIX", "PIP_ROOT", "PIP_USER"))
            and "unset PIP_TARGET PIP_PREFIX PIP_ROOT PIP_USER" in linux_lines
        ),
        "base_python_no_site_preflight": (
            "-I -S $VenvContract --mode $PreflightMode" in windows_lines
            and '-I -S "${VENV_CONTRACT}" --mode "${PREFLIGHT_MODE}"' in linux_lines
        ),
        "trust_marker_written_before_doctor": (
            "--mode write-marker" in windows_lines
            and "--mode write-marker" in linux_lines
        ),
        "windows_global_pip_absent": re.search(
            r"(?im)^\s*&\s+pip(?:\.exe)?\b", windows_lines
        )
        is None,
        "linux_global_pip_absent": re.search(
            r"(?im)^\s*pip(?:3(?:\.12)?)?\b", linux_lines
        )
        is None,
        "container_global_pip_absent": re.search(
            r"(?im)(?:^|&&\s*)pip(?:3(?:\.12)?)?\b", container_lines
        )
        is None,
        "explicit_pypi_index": all(
            text.count("--index-url https://pypi.org/simple") >= 2
            for text in (windows_lines, linux_lines, container_lines)
        ),
        "hash_required": all(
            text.count("--require-hashes") >= 2
            for text in (windows_lines, linux_lines, container_lines)
        ),
    }
    return {
        "status": _status(all(checks.values())),
        "checks": checks,
        "audited_sources": [
            "scripts/bootstrap.ps1",
            "scripts/bootstrap.sh",
            "Dockerfile.validation",
            "scripts/dssc_validation/venv_contract.py",
        ],
        "source_sha256": {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in source_paths.values()
            if path.is_file()
        },
    }


def _path_access(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized: dict[str, Any] = {}
    machine: dict[str, Any] = {}
    for relative in REQUIRED_FILES:
        path = root / relative
        normalized[relative] = {
            "exists": path.is_file(),
            "readable": path.is_file() and os.access(path, os.R_OK),
            "kind": "file",
        }
    for relative in REQUIRED_DIRECTORIES:
        path = root / relative
        normalized[relative] = {
            "exists": path.is_dir(),
            "readable": path.is_dir() and os.access(path, os.R_OK),
            "kind": "directory",
        }

    build = phase01_build_dir(root)
    write_error = None
    try:
        build = prepare_phase01_build_dir(root)
        probe = build / ".doctor-write-probe"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
        writable = True
    except (OSError, ValueError) as exc:
        writable = False
        write_error = str(exc)
    normalized["build/phase-01/current"] = {
        "exists": build.is_dir(),
        "readable": build.is_dir() and os.access(build, os.R_OK),
        "writable": writable,
        "kind": "directory",
    }
    machine["build_directory"] = str(build)
    machine["write_error"] = write_error
    return normalized, machine


def _git_capability(root: Path, profile: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if profile == "container":
        result = _not_required("container profile does not require Git CLI")
        return result, dict(result)

    version_code, version_out, version_err = _run(["git", "--version"], root)
    top_code, top_out, top_err = _run(["git", "rev-parse", "--show-toplevel"], root)
    version_text = (version_out or version_err).strip()
    top_text = (top_out or top_err).strip()
    try:
        top_matches = top_code == 0 and Path(top_text).resolve() == root.resolve()
    except OSError:
        top_matches = False
    ok = version_code == 0 and bool(version_text) and top_matches
    result = {
        "status": _status(ok),
        "top_level_matches_repository": top_matches,
    }
    machine = {
        "status": result["status"],
        "version": version_text.replace("git version", "").strip()
        if version_code == 0
        else None,
        "top_level": top_text if top_code == 0 else None,
        "version_exit_code": version_code,
        "top_level_exit_code": top_code,
    }
    return result, machine


def _docker_capabilities(
    root: Path, profile: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    if profile == "container":
        result = {
            "client": _not_required("container profile does not require Docker CLI"),
            "server": _not_required("container profile does not require Docker daemon"),
            "compose": _not_required("container profile does not require Compose"),
            "daemon_reachable": _not_required(
                "container profile does not access the host daemon"
            ),
        }
        return result, json.loads(json.dumps(result))

    if profile == "host-no-docker":
        # Native host validation that never executes the container track. The
        # Docker capability gates are intentionally out of scope; the container
        # track is certified by its own dedicated profile and job.
        reason = "host-no-docker profile does not exercise the container track"
        result = {
            "client": _not_required(reason),
            "server": _not_required(reason),
            "compose": _not_required(reason),
            "daemon_reachable": _not_required(reason),
        }
        return result, json.loads(json.dumps(result))

    commands = {
        "client": ["docker", "version", "--format", "{{.Client.Version}}"],
        "server": ["docker", "version", "--format", "{{.Server.Version}}"],
        "compose": ["docker", "compose", "version", "--short"],
    }
    result: dict[str, Any] = {}
    machine: dict[str, Any] = {}
    for name, command in commands.items():
        code, out, err = _run(command, root, timeout=45)
        version = (out or err).strip() if code == 0 else None
        passed = code == 0 and bool(version)
        result[name] = {"status": _status(passed)}
        machine[name] = {
            "status": result[name]["status"],
            "version": version,
            "exit_code": code,
        }
    daemon_ok = result["server"]["status"] == "PASS"
    result["daemon_reachable"] = {"status": _status(daemon_ok)}
    machine["daemon_reachable"] = {"status": _status(daemon_ok)}
    return result, machine


def _pip_check(root: Path, executable: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    code, out, err = _run(
        [
            str(executable),
            "-I",
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "check",
        ],
        root,
        timeout=120,
    )
    raw = (out + err).strip()
    result = {
        "status": _status(code == 0),
        "exit_code": code,
    }
    return result, {"exit_code": code, "output": raw[:2000]}


def run_doctor(root: Path, profile: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if profile not in ("host", "host-no-docker", "container"):
        raise ValueError("profile must be host, host-no-docker or container")

    root = root.resolve()
    invoked_executable = Path(sys.executable)
    executable = invoked_executable.resolve()
    implementation = platform.python_implementation()
    python_version = platform.python_version()
    pointer_bits = struct.calcsize("P") * 8
    expected_file = python_version_file(root)
    try:
        version_file_value = expected_file.read_text(encoding="utf-8").strip()
    except OSError:
        version_file_value = None
    in_repo_venv = is_repo_venv_interpreter(invoked_executable, root)
    interpreter_context = "container_system" if profile == "container" else "repo_venv"
    if profile == "container":
        container_ok, container_result, container_machine = container_contract_check()
    else:
        container_ok = True
        container_result = _not_required("host profile does not claim container identity")
        container_machine = dict(container_result)
    interpreter_ok = (
        implementation == "CPython"
        and python_version == EXPECTED_PYTHON_VERSION
        and version_file_value == EXPECTED_PYTHON_VERSION
        and pointer_bits == 64
        and (profile == "container" or in_repo_venv)
        and container_ok
    )
    if profile != "container":
        venv_isolation = check_current_venv(
            root / ".venv",
            EXPECTED_PYTHON_VERSION,
            FIXED_PIP_VERSION,
        )
    else:
        venv_isolation = _not_required(
            "container profile uses the image system interpreter"
        )

    try:
        import ensurepip

        ensurepip_version = ensurepip.version()
    except Exception:  # noqa: BLE001
        ensurepip_version = None
    ensurepip_ok = ensurepip_version == EXPECTED_ENSUREPIP_VERSION

    # Authoritative version is the installed distribution in this interpreter
    # (same source as venv_contract). CLI output is retained for diagnostics
    # only and must not override metadata when it contains upgrade notices.
    try:
        import importlib.metadata as _importlib_metadata

        pip_version = _importlib_metadata.version("pip")
        pip_code = 0
        pip_raw = f"importlib.metadata.version('pip')={pip_version}"
    except Exception as exc:  # noqa: BLE001
        pip_version = None
        pip_code = 1
        pip_raw = f"importlib.metadata.version('pip') failed: {exc}"
    cli_code, pip_out, pip_err = _run(
        [str(executable), "-I", "-m", "pip", "--isolated", "--version"], root
    )
    cli_text = "\n".join(part for part in (pip_out.strip(), pip_err.strip()) if part)
    if cli_text:
        pip_raw = f"{pip_raw}\ncli: {cli_text}"
    if pip_version is None and cli_code == 0:
        pip_version = _pip_version_from_cli(cli_text) or _version_triple(cli_text)
        pip_code = cli_code
    pip_ok = pip_version == FIXED_PIP_VERSION

    runtime_lock = parse_hash_lock(requirements_lock_path(root))
    bootstrap_lock = parse_hash_lock(bootstrap_lock_path(root))
    environment_match, installed = compare_environment_to_locks(
        runtime_lock, bootstrap_lock
    )
    expected_versions = environment_match["expected_versions"]

    direct_result: dict[str, Any] = {}
    direct_machine: dict[str, Any] = {}
    direct_ok = True
    for display_name, distribution_name, import_name in DIRECT_DEPENDENCIES:
        canonical = canonical_name(distribution_name)
        expected_version = expected_versions.get(canonical)
        actual_version = installed.get(canonical)
        try:
            importable = importlib.util.find_spec(import_name) is not None
        except (ImportError, AttributeError, ValueError):
            importable = False
        match = (
            expected_version is not None
            and actual_version == expected_version
            and importable
        )
        direct_result[display_name] = {
            "status": _status(match),
            "expected_version": expected_version,
            "installed": actual_version is not None,
            "version_match": actual_version == expected_version,
            "importable": importable,
        }
        direct_machine[display_name] = {
            "distribution": distribution_name,
            "import_name": import_name,
            "actual_version": actual_version,
        }
        direct_ok = direct_ok and match

    metadata = _metadata_contract(root)
    pip_bootstrap_contract = _pip_bootstrap_source_contract(root)
    pip_check_result, pip_check_machine = _pip_check(root, executable)
    git_result, git_machine = _git_capability(root, profile)
    docker_result, docker_machine = _docker_capabilities(root, profile)
    paths_result, paths_machine = _path_access(root)

    markers_ok = all(
        (root / relative).is_file() for relative in REQUIRED_FILES
    ) and all((root / relative).is_dir() for relative in REQUIRED_DIRECTORIES)
    canonical_root_matches = canonical_repository_root().resolve() == root
    path_access_ok = all(
        item.get("exists") is True and item.get("readable") is True
        for item in paths_result.values()
    ) and paths_result["build/phase-01/current"].get("writable") is True

    source_hashes, source_issues = collect_loaded_source_hashes(
        root,
        required_relpaths=(
            "scripts/doctor.py",
            "scripts/bootstrap.ps1",
            "scripts/bootstrap.sh",
            "Dockerfile.validation",
        ),
    )

    gates: list[tuple[str, bool]] = [
        ("repository_root", canonical_root_matches),
        ("repository_markers", markers_ok),
        ("python_interpreter", interpreter_ok),
        (
            "venv_isolation",
            profile == "container" or venv_isolation["status"] == "PASS",
        ),
        ("profile_identity", container_ok),
        ("ensurepip_source", ensurepip_ok),
        ("pip_version_fixed", pip_ok),
        ("pip_bootstrap_invocation", pip_bootstrap_contract["status"] == "PASS"),
        ("runtime_hash_lock", runtime_lock.ok),
        ("bootstrap_hash_lock", bootstrap_lock.ok),
        ("lock_metadata", metadata["status"] == "PASS"),
        ("installed_set_exact", environment_match["status"] == "PASS"),
        ("direct_dependencies", direct_ok),
        ("pip_check", pip_check_result["status"] == "PASS"),
        ("path_access", path_access_ok),
        ("source_hashes", not source_issues and bool(source_hashes)),
    ]
    if profile != "container":
        gates.append(("git", git_result["status"] == "PASS"))
    if profile == "host":
        gates.extend(
            [
                ("docker_client", docker_result["client"]["status"] == "PASS"),
                ("docker_server", docker_result["server"]["status"] == "PASS"),
                ("docker_compose", docker_result["compose"]["status"] == "PASS"),
                (
                    "docker_daemon_reachable",
                    docker_result["daemon_reachable"]["status"] == "PASS",
                ),
            ]
        )
    failed_gates = [name for name, passed in gates if not passed]

    result: dict[str, Any] = {
        "schema": "dssc.doctor.result.v1",
        "profile": profile,
        "overall_status": "PASS" if not failed_gates else "FAIL",
        "failed_gates": failed_gates,
        "repository": {
            "canonical_root_matches": canonical_root_matches,
            "required_markers_present": markers_ok,
        },
        "python": {
            "status": _status(interpreter_ok),
            "expected_implementation": "CPython",
            "expected_version": EXPECTED_PYTHON_VERSION,
            "expected_pointer_bits": 64,
            "pointer_bits_match": pointer_bits == 64,
            "version_file_match": version_file_value == EXPECTED_PYTHON_VERSION,
            "expected_context": interpreter_context,
            "repo_venv_required": profile != "container",
            "repo_venv_match": in_repo_venv if profile != "container" else None,
        },
        "container_identity": container_result,
        "venv_isolation": venv_isolation,
        "ensurepip": {
            "status": _status(ensurepip_ok),
            "expected_version": EXPECTED_ENSUREPIP_VERSION,
            "source": "CPython 3.12.10 standard-library ensurepip bundle",
        },
        "pip": {
            "status": _status(pip_ok),
            "expected_version": FIXED_PIP_VERSION,
            "invocation": "<PYTHON_EXECUTABLE> -I -m pip --isolated",
            "bootstrap_source_contract": pip_bootstrap_contract,
        },
        "locks": {
            "runtime": {
                "status": _status(runtime_lock.ok),
                "distribution_count": len(runtime_lock.entries),
                "issues": runtime_lock.issues,
                "sha256": (
                    sha256_file(runtime_lock.path) if runtime_lock.path.is_file() else None
                ),
            },
            "bootstrap": {
                "status": _status(bootstrap_lock.ok),
                "distribution_count": len(bootstrap_lock.entries),
                "issues": bootstrap_lock.issues,
                "sha256": (
                    sha256_file(bootstrap_lock.path)
                    if bootstrap_lock.path.is_file()
                    else None
                ),
            },
            "metadata": metadata,
            "validation_suites_sha256": (
                sha256_file(validation_suites_path(root))
                if validation_suites_path(root).is_file()
                else None
            ),
            "validation_suites_schema_sha256": (
                sha256_file(validation_suites_schema_path(root))
                if validation_suites_schema_path(root).is_file()
                else None
            ),
        },
        "installed_environment": environment_match,
        "direct_dependencies": direct_result,
        "pip_check": pip_check_result,
        "capabilities": {
            "git": git_result,
            "docker": docker_result,
        },
        "paths": paths_result,
        "source_hashes": source_hashes,
        "source_hash_issues": source_issues,
    }

    machine: dict[str, Any] = {
        "schema": "dssc.doctor.machine.v1",
        "profile": profile,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
            "platform": platform.platform(),
        },
        "python": {
            "implementation": implementation,
            "version": python_version,
            "pointer_bits": pointer_bits,
            "executable": str(executable),
            "repository_root": str(root),
            "cwd": str(Path.cwd()),
            "is_repo_venv": in_repo_venv,
            "ensurepip_version": ensurepip_version,
        },
        "container_identity": container_machine,
        "pip": {
            "version": pip_version,
            "raw": pip_raw,
            "exit_code": pip_code,
        },
        "installed_distributions": installed,
        "direct_dependencies": direct_machine,
        "pip_check": pip_check_machine,
        "git": git_machine,
        "docker": docker_machine,
        "paths": paths_machine,
    }
    return result, machine


def _print_human(result: dict[str, Any], machine: dict[str, Any]) -> None:
    print(
        f"DSSC doctor profile={result['profile']} "
        f"overall={result['overall_status']}"
    )
    python_machine = machine["python"]
    print(
        f"  python: {python_machine['implementation']} "
        f"{python_machine['version']} context={result['python']['expected_context']}"
    )
    print(
        f"  pip: {machine['pip']['version']} "
        f"expected={result['pip']['expected_version']}"
    )
    print(f"  lock: {result['locks']['runtime']['sha256']}")
    print(f"  pip_check: {result['pip_check']['status']}")
    print(f"  git: {result['capabilities']['git']['status']}")
    for name in ("client", "server", "compose", "daemon_reachable"):
        capability = result["capabilities"]["docker"][name]
        version = machine["docker"][name].get("version")
        print(f"  docker.{name}: {capability['status']} {version or ''}".rstrip())
    if result["failed_gates"]:
        print("  failed_gates: " + ", ".join(result["failed_gates"]))


def _resolve_profile(cli_profile: str | None) -> str:
    env_profile = os.environ.get("DSSC_VALIDATION_PROFILE", "").strip()
    if env_profile and env_profile not in ("host", "host-no-docker", "container"):
        raise ValueError(
            "DSSC_VALIDATION_PROFILE must be host, host-no-docker or container"
        )
    if cli_profile and env_profile and cli_profile != env_profile:
        raise ValueError(
            f"profile mismatch: --profile={cli_profile} and "
            f"DSSC_VALIDATION_PROFILE={env_profile}"
        )
    if cli_profile:
        return cli_profile
    if env_profile:
        return env_profile
    raise ValueError("--profile host|host-no-docker|container is required")


def doctor_main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="DSSC environment doctor")
    parser.add_argument(
        "--profile", choices=("host", "host-no-docker", "container"), default=None
    )
    parser.add_argument("--json", action="store_true", help="print normalized JSON")
    args = parser.parse_args(argv)
    try:
        profile = _resolve_profile(args.profile)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
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

    root = canonical_repository_root()
    result, machine = run_doctor(root, profile)
    output_dir = phase01_build_dir(root)
    result_path, machine_path = write_result_and_machine(
        output_dir,
        f"doctor-{profile}",
        result,
        machine,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_human(result, machine)
        print(
            f"Wrote {result_path.relative_to(root).as_posix()} and "
            f"{machine_path.relative_to(root).as_posix()}"
        )
    return 0 if result["overall_status"] == "PASS" else 1
