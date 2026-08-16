"""Frozen-files check component (reuses scripts/verify_frozen_files.py)."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

from dssc_validation.hashing import sha256_file
from dssc_validation.paths import scripts_dir


def _load_verify_module():
    path = scripts_dir() / "verify_frozen_files.py"
    spec = importlib.util.spec_from_file_location("verify_frozen_files", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen verifier from {path.name}")
    module = importlib.util.module_from_spec(spec)
    # Keep import side-effects minimal; module only defines helpers + main.
    sys.modules["verify_frozen_files"] = module
    spec.loader.exec_module(module)
    return module, path


def run_frozen_check(context: dict[str, Any]) -> dict[str, Any]:
    """Execute frozen-file verification; fail if 0 entries checked."""
    root: Path = context["repository_root"]
    verbose = bool(context.get("verbose", False))

    try:
        module, verifier_path = _load_verify_module()
    except Exception as exc:  # noqa: BLE001 — surface as program ERROR
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": f"failed to load verify_frozen_files.py: {exc}",
            "details": {},
        }

    # Reimplement the check loop with entry counting so 0 entries fails closed.
    manifest = (
        root
        / "docs"
        / "provenance"
        / "manifests"
        / "frozen-files-SHA256SUMS"
    )
    if not manifest.is_file():
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "frozen-files-SHA256SUMS missing",
            "details": {"manifest": "docs/provenance/manifests/frozen-files-SHA256SUMS"},
        }

    failures: list[str] = []
    checked = 0
    records = 0
    seen_paths: set[str] = set()
    sha256 = module.sha256

    for line_number, raw_line in enumerate(
        manifest.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            expected, relative_name = line.split(maxsplit=1)
        except ValueError:
            failures.append(f"line {line_number}: invalid manifest record")
            continue

        records += 1
        if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            failures.append(f"line {line_number}: invalid SHA-256 value")
            continue
        normalized_name = relative_name.replace("\\", "/")
        if normalized_name in seen_paths:
            failures.append(f"line {line_number}: duplicate path: {relative_name}")
            continue
        seen_paths.add(normalized_name)

        candidate = (root / relative_name).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            failures.append(
                f"line {line_number}: path escapes repository: {relative_name}"
            )
            continue

        if not candidate.is_file():
            failures.append(f"missing: {relative_name}")
            continue

        actual = sha256(candidate)
        checked += 1
        if actual.lower() != expected.lower():
            failures.append(
                f"hash mismatch: {relative_name} "
                f"(expected {expected.lower()}, found {actual.lower()})"
            )
        elif verbose:
            print(f"OK  {relative_name}")

    if records == 0 or checked == 0:
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "frozen verification discovered 0 manifest entries",
            "details": {
                "checked": 0,
                "records": records,
                "failures": failures,
                "verifier_sha256": sha256_file(verifier_path),
            },
        }

    if failures:
        for failure in failures:
            print(f"FAIL  {failure}")
        print(f"Frozen-file verification failed: {len(failures)} error(s).")
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": f"frozen verification failed: {len(failures)} error(s)",
            "details": {
                "checked": checked,
                "records": records,
                "failure_count": len(failures),
                "failures": failures[:50],
                "verifier_sha256": sha256_file(verifier_path),
            },
        }

    print(f"Frozen-file verification passed: {checked} file(s).")
    return {
        "status": "PASS",
        "program_status": "SUCCESS",
        "message": f"frozen verification passed: {checked} file(s)",
        "details": {
            "checked": checked,
            "records": records,
            "failure_count": 0,
            "verifier_sha256": sha256_file(verifier_path),
        },
    }
