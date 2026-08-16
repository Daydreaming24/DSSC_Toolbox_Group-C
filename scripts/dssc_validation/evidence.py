"""Deterministic result and machine-inventory evidence writers."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from dssc_validation.hashing import sha256_file
from dssc_validation.paths import (
    is_exact_phase_build_dir,
    prepare_phase_build_dir,
    repository_root,
)


_WINDOWS_ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)")
_POSIX_ABSOLUTE = re.compile(r"(?<![:/A-Za-z0-9.])/(?!/)[^\s\"'=]+")


def _walk_strings(value: Any, location: str = "$"):
    if isinstance(value, str):
        yield location, value
    elif isinstance(value, dict):
        for index, (key, item) in enumerate(value.items()):
            if isinstance(key, str):
                yield f"{location}.keys[{index}]", key
            yield from _walk_strings(item, f"{location}.values[{index}]")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{location}[{index}]")


def assert_normalized_result(value: Any) -> None:
    """Reject absolute filesystem paths from cross-machine result JSON."""
    findings: list[str] = []
    for location, text in _walk_strings(value):
        if _WINDOWS_ABSOLUTE.search(text) or _POSIX_ABSOLUTE.search(text):
            findings.append(location)
    if findings:
        raise ValueError(
            "normalized result contains absolute path(s) at: "
            + ", ".join(findings[:20])
        )


def normalized_text(text: str, root: Path, executable: Path | None = None) -> str:
    """Replace known machine-local absolute paths before result serialization."""
    replacements = {str(root.resolve()): "<REPO_ROOT>"}
    if executable is not None:
        replacements[str(executable.resolve())] = "<PYTHON_EXECUTABLE>"
    result = text
    for raw, replacement in sorted(
        replacements.items(), key=lambda item: len(item[0]), reverse=True
    ):
        result = result.replace(raw, replacement)
        result = result.replace(raw.replace("\\", "/"), replacement)
    return result


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json_bytes(value)
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = value.encode("utf-8")
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def write_result_and_machine(
    output_dir: Path,
    stem: str,
    result: dict[str, Any],
    machine: dict[str, Any],
    evidence_phase: str = "01",
) -> tuple[Path, Path]:
    """Write normalized result first; machine sidecar points to its exact hash."""
    root = repository_root()
    if not is_exact_phase_build_dir(output_dir, evidence_phase, root):
        raise ValueError(
            f"result output must equal build/phase-{evidence_phase}/current"
        )
    output_dir = prepare_phase_build_dir(evidence_phase, root)
    assert_normalized_result(result)
    result_path = output_dir / f"{stem}.result.json"
    machine_path = output_dir / f"{stem}.machine.json"
    atomic_write_json(result_path, result)

    sidecar = dict(machine)
    sidecar["result_file"] = result_path.name
    sidecar["result_sha256"] = sha256_file(result_path)
    atomic_write_json(machine_path, sidecar)
    return result_path, machine_path
