"""Fail-closed repository virtual-environment boundary and trust checks.

The filesystem preflight uses only the Python standard library and is designed
to run from the selected base interpreter with ``-I -S`` before an existing
venv interpreter, site ``.pth`` file, or package manager can execute.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import stat
import sys
import sysconfig
from pathlib import Path
from typing import Any


MARKER_NAME = ".dssc-phase01-venv.json"
MARKER_SCHEMA = "dssc.phase01.venv-trust.v1"
SYSCONFIG_KEYS = ("data", "platlib", "purelib", "scripts")
PIP_SCHEME_KEYS = ("data", "headers", "platlib", "purelib", "scripts")


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _normalized(path: Path) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


def _is_within(path: Path, parent: Path) -> bool:
    try:
        return os.path.commonpath((_normalized(path), _normalized(parent))) == _normalized(
            parent
        )
    except ValueError:
        return False


def _is_link_like(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if is_junction and is_junction():
            return True
        if not path.exists():
            return False
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except OSError:
        return True


def _path_boundary(path: Path, venv: Path) -> tuple[bool, bool]:
    """Return (contained, existing_ancestors_are_not_links)."""

    lexical = _lexical_absolute(path)
    root = _lexical_absolute(venv)
    if not _is_within(lexical, root):
        return False, False
    try:
        resolved = lexical.resolve(strict=False)
        root_resolved = root.resolve(strict=True)
    except OSError:
        return False, False
    if not _is_within(resolved, root_resolved):
        return False, False

    relative = Path(os.path.relpath(os.fspath(lexical), os.fspath(root)))
    current = root
    if _is_link_like(current):
        return True, False
    for part in relative.parts:
        if part in ("", "."):
            continue
        if part == "..":
            return False, False
        current = current / part
        if current.exists() or _is_link_like(current):
            if _is_link_like(current):
                return True, False
            if current != lexical and not current.is_dir():
                return True, False
    return True, True


def _read_venv_config(path: Path) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    issues: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        return {}, ["VENV_CONFIG_UNREADABLE"]
    for line in lines:
        if not line.strip() or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lower()
        if key in values:
            issues.append("VENV_CONFIG_DUPLICATE_KEY")
        values[key] = value.strip()
    return values, issues


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_file_sha256(path: Path) -> str | None:
    try:
        if not path.is_file() or _is_link_like(path):
            return None
        return _sha256_file(path)
    except OSError:
        return None


def _allowed_posix_link(path: Path, venv: Path, base_python: Path) -> str | None:
    if os.name == "nt":
        return None
    try:
        relative = path.relative_to(venv)
        resolved = path.resolve(strict=True)
    except (OSError, ValueError):
        return None
    if relative == Path("lib64"):
        try:
            if resolved == (venv / "lib").resolve(strict=True):
                return "lib64_to_venv_lib"
        except OSError:
            return None
    launcher_names = {
        "python",
        "python3",
        f"python{sys.version_info.major}.{sys.version_info.minor}",
    }
    if (
        len(relative.parts) == 2
        and relative.parts[0] == "bin"
        and relative.parts[1] in launcher_names
    ):
        try:
            if resolved == base_python.resolve(strict=True):
                return "venv_launcher_to_selected_base"
        except OSError:
            return None
    return None


def _is_prelaunch_site_hook(relative: Path) -> bool:
    """Identify files/packages that ``site`` can execute during venv startup."""

    lowered = tuple(part.casefold() for part in relative.parts)
    try:
        site_index = next(
            index
            for index, part in enumerate(lowered)
            if part in ("site-packages", "dist-packages")
        )
    except StopIteration:
        return False
    tail = lowered[site_index + 1 :]
    if not tail:
        return False
    first = tail[0]
    return bool(
        (len(tail) == 1 and first.endswith(".pth"))
        or first in (
            "sitecustomize.py",
            "sitecustomize",
            "usercustomize.py",
            "usercustomize",
        )
    )


def _tree_audit(
    venv: Path, base_python: Path, *, reject_prelaunch_site_hooks: bool = False
) -> dict[str, Any]:
    records: list[str] = []
    allowed_links: list[str] = []
    unsafe_links = 0
    special_entries = 0
    prelaunch_site_hooks = 0
    access_errors = 0
    file_count = 0
    directory_count = 0
    stack = [venv]

    while stack:
        directory = stack.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError:
            access_errors += 1
            continue
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(venv).as_posix()
            if relative == MARKER_NAME:
                continue
            try:
                info = entry.stat(follow_symlinks=False)
                reparse = bool(
                    getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                )
                link_like = entry.is_symlink() or reparse or _is_link_like(path)
            except OSError:
                access_errors += 1
                continue
            if link_like:
                allowed_kind = _allowed_posix_link(path, venv, base_python)
                if allowed_kind is None:
                    unsafe_links += 1
                    records.append(f"UNSAFE_LINK\t{relative}")
                else:
                    allowed_links.append(relative)
                    records.append(f"LINK\t{relative}\t{allowed_kind}")
                continue
            if stat.S_ISDIR(info.st_mode):
                directory_count += 1
                records.append(f"DIR\t{relative}")
                stack.append(path)
            elif stat.S_ISREG(info.st_mode):
                if reject_prelaunch_site_hooks and _is_prelaunch_site_hook(
                    Path(relative)
                ):
                    prelaunch_site_hooks += 1
                    records.append(f"PRELAUNCH_SITE_HOOK\t{relative}")
                    continue
                try:
                    file_hash = _sha256_file(path)
                except OSError:
                    access_errors += 1
                    continue
                file_count += 1
                records.append(f"FILE\t{relative}\t{info.st_size}\t{file_hash}")
            else:
                special_entries += 1
                records.append(f"SPECIAL\t{relative}")

    canonical = "\n".join(sorted(records)) + "\n"
    ok = (
        unsafe_links == 0
        and special_entries == 0
        and access_errors == 0
        and prelaunch_site_hooks == 0
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "tree_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "file_count": file_count,
        "directory_count": directory_count,
        "allowed_links": sorted(allowed_links),
        "unsafe_link_count": unsafe_links,
        "special_entry_count": special_entries,
        "prelaunch_site_hook_count": prelaunch_site_hooks,
        "access_error_count": access_errors,
    }


def _resolved_config_value(value: str | None) -> Path | None:
    if not value:
        return None
    try:
        return Path(value).resolve(strict=True)
    except OSError:
        return None


def _launcher_binding(venv: Path, base_python: Path) -> bool:
    try:
        base = base_python.resolve(strict=True)
        if os.name == "nt":
            launcher = venv / "Scripts" / "python.exe"
            template = base.parent / "Lib" / "venv" / "scripts" / "nt" / "python.exe"
            return bool(
                launcher.is_file()
                and template.is_file()
                and not _is_link_like(launcher)
                and not _is_link_like(template)
                and _sha256_file(launcher) == _sha256_file(template)
            )
        launcher = venv / "bin" / "python"
        return launcher.exists() and launcher.resolve(strict=True) == base
    except OSError:
        return False


def _marker_inputs(
    expected_version: str,
    expected_pip_version: str,
    base_python: Path,
    bootstrap_source: Path,
    runtime_lock: Path,
    bootstrap_lock: Path,
    tree: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": MARKER_SCHEMA,
        "python_version": expected_version,
        "pip_version": expected_pip_version,
        "base_python_sha256": _safe_file_sha256(base_python.resolve(strict=True)),
        "bootstrap_source_sha256": _safe_file_sha256(bootstrap_source),
        "venv_contract_source_sha256": _safe_file_sha256(Path(__file__)),
        "runtime_lock_sha256": _safe_file_sha256(runtime_lock),
        "bootstrap_lock_sha256": _safe_file_sha256(bootstrap_lock),
        "tree_sha256": tree["tree_sha256"],
        "tree_file_count": tree["file_count"],
        "tree_directory_count": tree["directory_count"],
        "allowed_links": tree["allowed_links"],
    }


def _read_marker(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file() or _is_link_like(path):
            return None
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _filesystem_contract(
    venv: Path,
    base_python: Path,
    expected_version: str,
    expected_pip_version: str,
    bootstrap_source: Path,
    runtime_lock: Path,
    bootstrap_lock: Path,
    marker_mode: str,
    require_running_base: bool,
) -> dict[str, Any]:
    venv = _lexical_absolute(venv)
    base_python = _lexical_absolute(base_python)
    config_path = venv / "pyvenv.cfg"
    config, config_issues = _read_venv_config(config_path)
    config_contained, config_real = _path_boundary(config_path, venv)
    tree = _tree_audit(
        venv,
        base_python,
        reject_prelaunch_site_hooks=marker_mode == "created",
    ) if venv.is_dir() else {
        "status": "FAIL",
        "tree_sha256": hashlib.sha256(b"").hexdigest(),
        "file_count": 0,
        "directory_count": 0,
        "allowed_links": [],
        "unsafe_link_count": 0,
        "special_entry_count": 0,
        "prelaunch_site_hook_count": 0,
        "access_error_count": 1,
    }
    base_resolved = None
    try:
        base_resolved = base_python.resolve(strict=True)
    except OSError:
        pass
    running_base_ok = True
    if require_running_base:
        try:
            running_base_ok = Path(sys.executable).resolve(strict=True) == base_resolved
        except OSError:
            running_base_ok = False

    checks: dict[str, bool] = {
        "selected_base_is_running_interpreter": running_base_ok,
        "cpython_version": (
            platform.python_implementation() == "CPython"
            and platform.python_version() == expected_version
        ),
        "venv_root_real_directory": venv.is_dir() and not _is_link_like(venv),
        "venv_config_real_file": (
            config_path.is_file()
            and config_contained
            and config_real
            and not _is_link_like(config_path)
        ),
        "system_site_packages_disabled": (
            config.get("include-system-site-packages", "").lower() == "false"
        ),
        "venv_config_version": config.get("version") == expected_version,
        "venv_config_home_matches_base": (
            base_resolved is not None
            and _resolved_config_value(config.get("home")) == base_resolved.parent
        ),
        "venv_config_executable_matches_base": (
            base_resolved is not None
            and _resolved_config_value(config.get("executable")) == base_resolved
        ),
        "venv_launcher_matches_base": _launcher_binding(venv, base_python),
        "venv_tree_has_no_unsafe_links": tree["status"] == "PASS",
        "contract_inputs_are_real_files": all(
            _safe_file_sha256(path) is not None
            for path in (bootstrap_source, runtime_lock, bootstrap_lock, Path(__file__))
        ),
    }

    expected_marker = None
    try:
        expected_marker = _marker_inputs(
            expected_version,
            expected_pip_version,
            base_python,
            bootstrap_source,
            runtime_lock,
            bootstrap_lock,
            tree,
        )
    except OSError:
        pass
    marker_path = venv / MARKER_NAME
    if marker_mode == "created":
        checks["trusted_marker_state"] = not marker_path.exists() and not _is_link_like(
            marker_path
        )
    elif marker_mode == "require":
        checks["trusted_marker_state"] = (
            expected_marker is not None and _read_marker(marker_path) == expected_marker
        )
    elif marker_mode == "ignore":
        checks["trusted_marker_state"] = True
    else:
        raise ValueError(f"unknown marker mode: {marker_mode}")

    issues = list(config_issues)
    issues.extend(name.upper() for name, passed in checks.items() if not passed)
    return {
        "schema": "dssc.venv_filesystem_preflight.result.v1",
        "status": "PASS" if not issues else "FAIL",
        "marker_mode": marker_mode,
        "checks": checks,
        "tree": tree,
        "issues": sorted(set(issues)),
    }


def _bootstrap_paths(venv: Path) -> tuple[Path, Path, Path]:
    root = venv.parent
    bootstrap = root / "scripts" / (
        "bootstrap.ps1" if os.name == "nt" else "bootstrap.sh"
    )
    return bootstrap, root / "requirements.lock", root / "requirements-bootstrap.lock"


def check_current_venv(
    expected_venv: Path,
    expected_version: str,
    expected_pip_version: str,
    require_marker: bool = True,
) -> dict[str, Any]:
    """Validate the running venv and its previously established trust marker."""

    venv = _lexical_absolute(expected_venv)
    base_python = Path(getattr(sys, "_base_executable", sys.executable))
    bootstrap_source, runtime_lock, bootstrap_lock = _bootstrap_paths(venv)
    filesystem = _filesystem_contract(
        venv,
        base_python,
        expected_version,
        expected_pip_version,
        bootstrap_source,
        runtime_lock,
        bootstrap_lock,
        "require" if require_marker else "created",
        False,
    )
    issues = list(filesystem["issues"])
    checks: dict[str, bool] = {
        "filesystem_preflight": filesystem["status"] == "PASS",
        "prefix_matches_venv": (
            _normalized(_lexical_absolute(Path(sys.prefix))) == _normalized(venv)
            and _normalized(_lexical_absolute(Path(sys.base_prefix)))
            != _normalized(venv)
        ),
        "cpython_version": (
            platform.python_implementation() == "CPython"
            and platform.python_version() == expected_version
        ),
    }

    config_paths: dict[str, Path] = {}
    contained = True
    real_ancestors = True
    for key in SYSCONFIG_KEYS:
        value = sysconfig.get_path(key)
        if not value:
            contained = False
            real_ancestors = False
            continue
        candidate = Path(value)
        config_paths[key] = candidate
        candidate_contained, candidate_real = _path_boundary(candidate, venv)
        contained = contained and candidate_contained
        real_ancestors = real_ancestors and candidate_real
    checks["sysconfig_paths_contained"] = contained
    checks["sysconfig_paths_have_no_links"] = real_ancestors

    site_paths_ok = False
    if checks["filesystem_preflight"]:
        try:
            import site

            site_paths = [Path(value) for value in site.getsitepackages()]
            site_paths_ok = bool(site_paths) and site.ENABLE_USER_SITE is False
            for candidate in site_paths:
                candidate_contained, candidate_real = _path_boundary(candidate, venv)
                site_paths_ok = site_paths_ok and candidate_contained and candidate_real
        except (AttributeError, OSError):
            site_paths_ok = False
    checks["site_package_paths_contained"] = site_paths_ok

    safe_to_import_pip = all(checks.values())
    if safe_to_import_pip:
        try:
            import pip
            from pip._internal.locations import get_scheme

            pip_file = Path(pip.__file__)
            purelib = config_paths.get("purelib")
            pip_contained, pip_real = _path_boundary(pip_file, venv)
            checks["pip_location_in_venv"] = bool(
                purelib
                and pip_contained
                and pip_real
                and _is_within(
                    pip_file.resolve(strict=True), purelib.resolve(strict=True)
                )
            )
            checks["pip_version_fixed"] = (
                importlib.metadata.version("pip") == expected_pip_version
            )
            scheme = get_scheme("dssc_venv_contract_probe")
            pip_scheme_ok = True
            for key in PIP_SCHEME_KEYS:
                candidate_contained, candidate_real = _path_boundary(
                    Path(getattr(scheme, key)), venv
                )
                pip_scheme_ok = (
                    pip_scheme_ok and candidate_contained and candidate_real
                )
            checks["pip_write_paths_contained"] = pip_scheme_ok
        except (
            AttributeError,
            ImportError,
            importlib.metadata.PackageNotFoundError,
            OSError,
            TypeError,
        ):
            checks["pip_location_in_venv"] = False
            checks["pip_version_fixed"] = False
            checks["pip_write_paths_contained"] = False
    else:
        checks["pip_location_in_venv"] = False
        checks["pip_version_fixed"] = False
        checks["pip_write_paths_contained"] = False

    issues.extend(name.upper() for name, passed in checks.items() if not passed)
    return {
        "schema": "dssc.venv_contract.result.v1",
        "status": "PASS" if not issues else "FAIL",
        "expected_version": expected_version,
        "expected_pip_version": expected_pip_version,
        "sysconfig_keys": list(SYSCONFIG_KEYS),
        "pip_scheme_keys": list(PIP_SCHEME_KEYS),
        "checks": checks,
        "filesystem_preflight": filesystem,
        "issues": sorted(set(issues)),
    }


def _write_trust_marker(
    venv: Path,
    base_python: Path,
    expected_version: str,
    expected_pip_version: str,
    bootstrap_source: Path,
    runtime_lock: Path,
    bootstrap_lock: Path,
) -> dict[str, Any]:
    preflight = _filesystem_contract(
        venv,
        base_python,
        expected_version,
        expected_pip_version,
        bootstrap_source,
        runtime_lock,
        bootstrap_lock,
        "ignore",
        True,
    )
    if preflight["status"] != "PASS":
        return preflight
    marker = _marker_inputs(
        expected_version,
        expected_pip_version,
        base_python,
        bootstrap_source,
        runtime_lock,
        bootstrap_lock,
        preflight["tree"],
    )
    marker_path = venv / MARKER_NAME
    temporary = venv / f".{MARKER_NAME}.{os.getpid()}.tmp"
    try:
        payload = json.dumps(marker, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, marker_path)
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return {
            **preflight,
            "status": "FAIL",
            "issues": sorted(set(preflight["issues"] + ["MARKER_WRITE_FAILED"])),
        }
    return {
        **preflight,
        "status": "PASS",
        "marker_written": True,
        "marker_sha256": _sha256_file(marker_path),
    }


def _required_path(parser: argparse.ArgumentParser, value: Path | None, name: str) -> Path:
    if value is None:
        parser.error(f"{name} is required for this mode")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository .venv isolation")
    parser.add_argument(
        "--mode",
        choices=("runtime", "created-preflight", "reuse-preflight", "write-marker"),
        default="runtime",
    )
    parser.add_argument("--venv", required=True, type=Path)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-pip-version", required=True)
    parser.add_argument("--base-python", type=Path)
    parser.add_argument("--bootstrap-source-file", type=Path)
    parser.add_argument("--runtime-lock-file", type=Path)
    parser.add_argument("--bootstrap-lock-file", type=Path)
    parser.add_argument("--allow-missing-marker", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "runtime":
        result = check_current_venv(
            args.venv,
            args.expected_version,
            args.expected_pip_version,
            require_marker=not args.allow_missing_marker,
        )
    else:
        base_python = _required_path(parser, args.base_python, "--base-python")
        bootstrap_source = _required_path(
            parser, args.bootstrap_source_file, "--bootstrap-source-file"
        )
        runtime_lock = _required_path(
            parser, args.runtime_lock_file, "--runtime-lock-file"
        )
        bootstrap_lock = _required_path(
            parser, args.bootstrap_lock_file, "--bootstrap-lock-file"
        )
        if args.mode == "write-marker":
            result = _write_trust_marker(
                args.venv,
                base_python,
                args.expected_version,
                args.expected_pip_version,
                bootstrap_source,
                runtime_lock,
                bootstrap_lock,
            )
        else:
            result = _filesystem_contract(
                args.venv,
                base_python,
                args.expected_version,
                args.expected_pip_version,
                bootstrap_source,
                runtime_lock,
                bootstrap_lock,
                "created" if args.mode == "created-preflight" else "require",
                True,
            )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
