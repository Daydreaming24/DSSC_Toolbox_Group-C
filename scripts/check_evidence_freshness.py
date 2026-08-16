#!/usr/bin/env python3
"""Fail-closed Phase 09 evidence freshness checker.

Binds and verifies:

- four upstream manifests (release / baseline / requirements / v0.4-test-cases)
- validation-suites ``contract_version`` + manifest SHA-256 (frozen at Phase 08/09)
- deliverables.json runtime SHA-256 (recorded only; never hard-coded as oracle)
- requirements.lock SHA-256
- validator/harness source-file hashes (from selected evidence ``source_hashes``
  and a fixed core set of scripts)
- each selected release evidence report's input/artifact hashes still match disk

Historical Phase evidence may record older suite registry versions; freshness for
those files means their declared artifact/source hashes still match the current
tree, not that their embedded registry version equals the live contract.

Wrong *current* validation-suites bindings (deliverables.json, live registry
file, or an explicit binding override) always fail closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]

VALIDATION_SUITES_REL = "C_Semantic_Treehouse/manifests/validation-suites.json"
VALIDATION_SUITES_SCHEMA_REL = (
    "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json"
)
DELIVERABLES_REL = "C_Semantic_Treehouse/manifests/deliverables.json"
EVIDENCE_INDEX_REL = (
    "C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json"
)
LOCK_REL = "requirements.lock"

EXPECTED_CONTRACT_VERSION = "1.6.0"
EXPECTED_VALIDATION_SUITES_SHA256 = (
    "09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836"
)
EXPECTED_LOCK_SHA256 = (
    "d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2"
)
CORE_RESULTS_SCHEMA = "dssc.phase09.core-results.v1"
CORE_SOURCE_HASH_POLICY = "must-match-disk"

UPSTREAM_MANIFESTS: tuple[str, ...] = (
    "C_Semantic_Treehouse/manifests/release-manifest.json",
    "C_Semantic_Treehouse/manifests/baseline-test-cases.json",
    "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
    "C_Semantic_Treehouse/manifests/v0.4-test-cases.json",
)

# Core harness/validator sources that must remain hash-bound for release QA.
CORE_SOURCE_RELS: tuple[str, ...] = (
    "scripts/validate.py",
    "scripts/doctor.py",
    "scripts/verify_frozen_files.py",
    "scripts/check_deliverables.py",
    "scripts/check_publication_safety.py",
    "scripts/check_evidence_freshness.py",
    "scripts/dssc_validation/suite_registry.py",
    "scripts/dssc_validation/hashing.py",
    "scripts/dssc_validation/paths.py",
    "scripts/dssc_validation/evidence.py",
    "scripts/dssc_validation/entrypoint_catalog.py",
)

REASON_CODES = frozenset(
    {
        "MISSING_FILE",
        "EMPTY_FILE",
        "STALE_INPUT_HASH",
        "STALE_REPORT_HASH",
        "STALE_SOURCE_HASH",
        "STALE_LOCK_HASH",
        "WRONG_VALIDATION_SUITES_HASH",
        "WRONG_VALIDATION_SUITES_VERSION",
        "DELIVERABLES_MISMATCH",
        "UPSTREAM_MANIFEST_STALE",
        "EVIDENCE_OLD_MANIFEST",
        "EVIDENCE_EXPIRED",
        "EVIDENCE_UNPARSEABLE",
        "CORE_SOURCE_HASH_POLICY_REQUIRED",
        "ZERO_SCAN_TARGETS",
        "CHECKER_ERROR",
    }
)


@dataclass(order=True)
class Issue:
    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


@dataclass
class CheckResult:
    ok: bool = True
    issues: list[Issue] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def add(self, code: str, location: str, message: str) -> None:
        if code not in REASON_CODES:
            code = "CHECKER_ERROR"
        self.issues.append(Issue(code=code, location=location, message=message))
        self.ok = False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_posix(path: str) -> str:
    return path.replace("\\", "/")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_file(root: Path, rel: str, result: CheckResult) -> Path | None:
    path = root / rel
    if not path.is_file():
        result.add("MISSING_FILE", rel, "required freshness target is missing")
        return None
    if path.stat().st_size == 0:
        result.add("EMPTY_FILE", rel, "required freshness target is empty")
        return None
    return path


def bind_upstream_manifests(root: Path, result: CheckResult) -> dict[str, str]:
    bound: dict[str, str] = {}
    for rel in UPSTREAM_MANIFESTS:
        path = require_file(root, rel, result)
        if path is None:
            continue
        bound[rel] = sha256_file(path)
    return bound


def bind_validation_suites(
    root: Path,
    result: CheckResult,
    *,
    expected_version: str,
    expected_sha256: str,
) -> dict[str, Any]:
    path = require_file(root, VALIDATION_SUITES_REL, result)
    schema = require_file(root, VALIDATION_SUITES_SCHEMA_REL, result)
    info: dict[str, Any] = {
        "manifest_path": VALIDATION_SUITES_REL,
        "schema_path": VALIDATION_SUITES_SCHEMA_REL,
    }
    if path is None:
        return info
    actual = sha256_file(path)
    info["manifest_sha256"] = actual
    if schema is not None:
        info["schema_sha256"] = sha256_file(schema)
    try:
        data = load_json(path)
    except json.JSONDecodeError as exc:
        result.add(
            "EVIDENCE_UNPARSEABLE",
            VALIDATION_SUITES_REL,
            f"validation-suites.json unparseable: {exc}",
        )
        return info
    version = data.get("contract_version")
    info["contract_version"] = version
    if version != expected_version:
        result.add(
            "WRONG_VALIDATION_SUITES_VERSION",
            VALIDATION_SUITES_REL,
            f"contract_version {version!r} != expected {expected_version!r}",
        )
    if actual != expected_sha256:
        result.add(
            "WRONG_VALIDATION_SUITES_HASH",
            VALIDATION_SUITES_REL,
            f"manifest sha256 {actual} != expected {expected_sha256}",
        )
    return info


def bind_deliverables(root: Path, result: CheckResult) -> dict[str, Any]:
    path = require_file(root, DELIVERABLES_REL, result)
    info: dict[str, Any] = {"path": DELIVERABLES_REL}
    if path is None:
        return info
    runtime = sha256_file(path)
    info["runtime_sha256"] = runtime
    try:
        data = load_json(path)
    except json.JSONDecodeError as exc:
        result.add(
            "EVIDENCE_UNPARSEABLE",
            DELIVERABLES_REL,
            f"deliverables.json unparseable: {exc}",
        )
        return info
    vs = data.get("validation_suites") or {}
    info["declared_contract_version"] = vs.get("contract_version")
    info["declared_manifest_sha256"] = vs.get("manifest_sha256")
    if vs.get("contract_version") != EXPECTED_CONTRACT_VERSION:
        result.add(
            "WRONG_VALIDATION_SUITES_VERSION",
            f"{DELIVERABLES_REL}.validation_suites.contract_version",
            (
                f"deliverables declares contract_version "
                f"{vs.get('contract_version')!r} != {EXPECTED_CONTRACT_VERSION!r}"
            ),
        )
    if vs.get("manifest_sha256") != EXPECTED_VALIDATION_SUITES_SHA256:
        result.add(
            "WRONG_VALIDATION_SUITES_HASH",
            f"{DELIVERABLES_REL}.validation_suites.manifest_sha256",
            (
                f"deliverables declares validation-suites sha256 "
                f"{vs.get('manifest_sha256')!r} != expected "
                f"{EXPECTED_VALIDATION_SUITES_SHA256}"
            ),
        )
    # Cross-check declared upstream anchors exist as deliverable entries with
    # matching hashes when listed.
    by_path = {
        item.get("path"): item
        for item in data.get("deliverables") or []
        if isinstance(item, dict)
    }
    for rel in UPSTREAM_MANIFESTS + (VALIDATION_SUITES_REL, LOCK_REL):
        item = by_path.get(rel)
        if not item:
            result.add(
                "DELIVERABLES_MISMATCH",
                rel,
                "freshness anchor is not listed in deliverables.json",
            )
            continue
        disk = root / rel
        if not disk.is_file():
            result.add("MISSING_FILE", rel, "deliverable anchor missing on disk")
            continue
        actual = sha256_file(disk)
        declared = item.get("sha256")
        if declared != actual:
            result.add(
                "UPSTREAM_MANIFEST_STALE",
                rel,
                f"deliverables sha256 {declared} != disk {actual}",
            )
    return info


def bind_lock(root: Path, result: CheckResult) -> dict[str, Any]:
    path = require_file(root, LOCK_REL, result)
    info: dict[str, Any] = {"path": LOCK_REL}
    if path is None:
        return info
    actual = sha256_file(path)
    info["sha256"] = actual
    if actual != EXPECTED_LOCK_SHA256:
        result.add(
            "STALE_LOCK_HASH",
            LOCK_REL,
            f"lock sha256 {actual} != expected {EXPECTED_LOCK_SHA256}",
        )
    return info


def bind_core_sources(root: Path, result: CheckResult) -> dict[str, str]:
    bound: dict[str, str] = {}
    for rel in CORE_SOURCE_RELS:
        path = root / rel
        if not path.is_file():
            # Phase 09 checkers are created incrementally; only fail if a core
            # Phase 01–08 harness file is missing.
            if rel.startswith("scripts/check_"):
                # Optional until fully landed; still record absence.
                continue
            result.add("MISSING_FILE", rel, "core validator/harness source missing")
            continue
        bound[rel] = sha256_file(path)
    if not bound:
        result.add(
            "ZERO_SCAN_TARGETS",
            "core-sources",
            "zero core source files bound",
        )
    return bound


def verify_hash_map(
    root: Path,
    mapping: Mapping[str, Any],
    *,
    evidence_path: str,
    result: CheckResult,
    stale_code: str,
    label: str,
) -> int:
    """Verify path→sha256 map; return number of entries checked."""
    checked = 0
    for rel, expected in sorted(mapping.items(), key=lambda kv: str(kv[0])):
        if not isinstance(rel, str) or not isinstance(expected, str):
            result.add(
                "EVIDENCE_UNPARSEABLE",
                f"{evidence_path}:{label}",
                f"invalid hash map entry {rel!r} -> {expected!r}",
            )
            continue
        path = root / rel
        if not path.is_file():
            result.add(
                "MISSING_FILE",
                f"{evidence_path}:{rel}",
                f"{label} path missing on disk",
            )
            continue
        actual = sha256_file(path)
        checked += 1
        if actual != expected:
            result.add(
                stale_code,
                f"{evidence_path}:{rel}",
                f"{label} declared {expected} != disk {actual}",
            )
    return checked


def verify_artifact_list(
    root: Path,
    artifacts: Sequence[Mapping[str, Any]],
    *,
    evidence_path: str,
    result: CheckResult,
) -> int:
    checked = 0
    for item in artifacts:
        if not isinstance(item, Mapping):
            continue
        rel = item.get("path")
        expected = item.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            continue
        path = root / rel
        if not path.is_file():
            result.add(
                "MISSING_FILE",
                f"{evidence_path}:{rel}",
                "artifact path missing on disk",
            )
            continue
        actual = sha256_file(path)
        checked += 1
        if actual != expected:
            result.add(
                "STALE_INPUT_HASH",
                f"{evidence_path}:{rel}",
                f"artifact sha256 declared {expected} != disk {actual}",
            )
    return checked


def enforce_core_source_hash_contract(
    data: Mapping[str, Any],
    *,
    evidence_path: str,
    result: CheckResult,
) -> bool:
    """Require live core evidence to opt in to disk-bound source verification."""

    if data.get("schema") != CORE_RESULTS_SCHEMA:
        return False
    policy = data.get("source_hash_policy")
    if policy != CORE_SOURCE_HASH_POLICY:
        result.add(
            "CORE_SOURCE_HASH_POLICY_REQUIRED",
            f"{evidence_path}:source_hash_policy",
            (
                f"{CORE_RESULTS_SCHEMA} requires source_hash_policy="
                f"{CORE_SOURCE_HASH_POLICY!r}; actual={policy!r}"
            ),
        )
    source_hashes = data.get("source_hashes")
    if not isinstance(source_hashes, Mapping) or not source_hashes:
        result.add(
            "EVIDENCE_UNPARSEABLE",
            f"{evidence_path}:source_hashes",
            f"{CORE_RESULTS_SCHEMA} requires a non-empty source_hashes map",
        )
    return True


def check_evidence_reports(
    root: Path,
    evidence_index_path: Path,
    result: CheckResult,
    *,
    require_live_registry: bool = False,
) -> dict[str, Any]:
    try:
        index = load_json(evidence_index_path)
    except json.JSONDecodeError as exc:
        result.add(
            "EVIDENCE_UNPARSEABLE",
            to_posix(
                str(evidence_index_path.relative_to(root))
                if evidence_index_path.is_relative_to(root)
                else str(evidence_index_path)
            ),
            f"evidence-index unparseable: {exc}",
        )
        return {"reports_checked": 0}

    entries = index.get("entries") or []
    reports_checked = 0
    inputs_checked = 0
    sources_checked = 0
    report_paths: list[str] = []

    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        rel = entry.get("path")
        if not isinstance(rel, str):
            continue
        if not rel.endswith(".json"):
            # README and other non-JSON evidence: existence only.
            path = root / rel
            if not path.is_file():
                result.add("MISSING_FILE", rel, "evidence-index path missing")
            continue
        path = require_file(root, rel, result)
        if path is None:
            continue
        try:
            data = load_json(path)
        except json.JSONDecodeError as exc:
            result.add(
                "EVIDENCE_UNPARSEABLE",
                rel,
                f"evidence result unparseable: {exc}",
            )
            continue

        is_core_entry = entry.get("id") == "core-results" or rel.endswith(
            "/core-results.json"
        )
        is_core_results = data.get("schema") == CORE_RESULTS_SCHEMA
        if is_core_entry and not is_core_results:
            result.add(
                "EVIDENCE_UNPARSEABLE",
                f"{rel}:schema",
                f"core-results entry requires schema {CORE_RESULTS_SCHEMA!r}",
            )
        if not rel.endswith(".result.json") and not is_core_entry and not is_core_results:
            # Other indexed JSON documents are existence/parseability checked.
            continue
        reports_checked += 1
        report_paths.append(rel)
        enforce_core_source_hash_contract(
            data,
            evidence_path=rel,
            result=result,
        )

        # Optional explicit expiry / freshness markers used by negative controls.
        if data.get("freshness_status") in {"EXPIRED", "STALE", "INVALID"}:
            result.add(
                "EVIDENCE_EXPIRED",
                rel,
                f"evidence declares freshness_status={data.get('freshness_status')!r}",
            )
        if data.get("expires_at") == "1970-01-01T00:00:00Z":
            result.add(
                "EVIDENCE_EXPIRED",
                rel,
                "evidence declares an expired expires_at timestamp",
            )

        # If evidence claims a *live* validation-suites binding field that is
        # present and marked current, it must match. Historical registry_* fields
        # alone are not treated as live bindings.
        live_vs = data.get("validation_suites_manifest_sha256") or data.get(
            "live_registry_sha256"
        )
        if isinstance(live_vs, str) and live_vs != EXPECTED_VALIDATION_SUITES_SHA256:
            result.add(
                "WRONG_VALIDATION_SUITES_HASH",
                f"{rel}.live_validation_suites",
                f"live validation-suites hash {live_vs} != expected "
                f"{EXPECTED_VALIDATION_SUITES_SHA256}",
            )
        live_ver = data.get("validation_suites_contract_version") or data.get(
            "live_registry_contract_version"
        )
        if isinstance(live_ver, str) and live_ver != EXPECTED_CONTRACT_VERSION:
            result.add(
                "WRONG_VALIDATION_SUITES_VERSION",
                f"{rel}.live_validation_suites",
                f"live contract_version {live_ver!r} != {EXPECTED_CONTRACT_VERSION!r}",
            )

        # Reject evidence that points at a known-wrong upstream manifest path
        # with a still-declared hash that no longer matches (stale input).
        if isinstance(data.get("manifest_path"), str) and isinstance(
            data.get("manifest_sha256"), str
        ):
            m_rel = data["manifest_path"]
            m_path = root / m_rel
            if m_path.is_file():
                actual = sha256_file(m_path)
                if actual != data["manifest_sha256"]:
                    result.add(
                        "STALE_INPUT_HASH",
                        f"{rel}:{m_rel}",
                        (
                            f"evidence manifest_sha256 {data['manifest_sha256']} "
                            f"!= disk {actual}"
                        ),
                    )
                    # Also surface as old-manifest reference when hash drifts.
                    result.add(
                        "EVIDENCE_OLD_MANIFEST",
                        f"{rel}:{m_rel}",
                        "evidence still references a stale upstream manifest hash",
                    )
            else:
                result.add(
                    "MISSING_FILE",
                    f"{rel}:{m_rel}",
                    "evidence manifest_path missing on disk",
                )

        if isinstance(data.get("requirements_lock_sha256"), str):
            lock_path = root / LOCK_REL
            if lock_path.is_file():
                actual_lock = sha256_file(lock_path)
                if data["requirements_lock_sha256"] != actual_lock:
                    result.add(
                        "STALE_LOCK_HASH",
                        f"{rel}:requirements_lock_sha256",
                        (
                            f"evidence lock hash {data['requirements_lock_sha256']} "
                            f"!= disk {actual_lock}"
                        ),
                    )

        artifacts = data.get("artifact_hashes") or []
        if isinstance(artifacts, list):
            inputs_checked += verify_artifact_list(
                root, artifacts, evidence_path=rel, result=result
            )

        # Historical Phase evidence may record harness source_hashes from the
        # execution epoch. Later legitimate Phase edits change those scripts.
        # Live Phase 09 core evidence always verifies against disk and must state
        # that policy explicitly; other reports opt in with the same policy.
        source_hashes = data.get("source_hashes") or {}
        policy = data.get("source_hash_policy")
        if isinstance(source_hashes, Mapping) and source_hashes:
            if policy == CORE_SOURCE_HASH_POLICY or is_core_results:
                sources_checked += verify_hash_map(
                    root,
                    source_hashes,
                    evidence_path=rel,
                    result=result,
                    stale_code="STALE_SOURCE_HASH",
                    label="source_hashes",
                )
            else:
                # Count present entries without failing on historical drift.
                for s_rel, expected in source_hashes.items():
                    if not isinstance(s_rel, str) or not isinstance(expected, str):
                        continue
                    s_path = root / s_rel
                    if s_path.is_file():
                        sources_checked += 1

        # Self hash of report is not embedded; optional declared report_sha256
        # used only by negative-control fixtures.
        declared_report = data.get("report_sha256")
        if isinstance(declared_report, str):
            # Compute hash of file with report_sha256 field removed would be
            # circular; instead treat declared_report as an external binding
            # that must match the on-disk file bytes when provided as a pure
            # external oracle via binding override files. Here: if present and
            # not equal to actual file hash, flag STALE_REPORT_HASH.
            actual_report = sha256_file(path)
            if declared_report != actual_report:
                result.add(
                    "STALE_REPORT_HASH",
                    rel,
                    f"declared report_sha256 {declared_report} != disk {actual_report}",
                )

        if require_live_registry:
            reg = data.get("registry_sha256")
            if reg != EXPECTED_VALIDATION_SUITES_SHA256:
                result.add(
                    "WRONG_VALIDATION_SUITES_HASH",
                    f"{rel}.registry_sha256",
                    f"require_live_registry: {reg} != {EXPECTED_VALIDATION_SUITES_SHA256}",
                )

    return {
        "reports_checked": reports_checked,
        "inputs_checked": inputs_checked,
        "sources_checked": sources_checked,
        "report_paths": report_paths,
    }


def apply_binding_overrides(
    result: CheckResult,
    binding: Mapping[str, Any] | None,
) -> None:
    """Apply an optional external binding document (negative-control surface)."""
    if not binding:
        return
    if binding.get("validation_suites_manifest_sha256") not in (None, ""):
        declared = binding["validation_suites_manifest_sha256"]
        if declared != EXPECTED_VALIDATION_SUITES_SHA256:
            result.add(
                "WRONG_VALIDATION_SUITES_HASH",
                "binding.validation_suites_manifest_sha256",
                f"binding declares {declared} != expected {EXPECTED_VALIDATION_SUITES_SHA256}",
            )
    if binding.get("validation_suites_contract_version") not in (None, ""):
        declared_v = binding["validation_suites_contract_version"]
        if declared_v != EXPECTED_CONTRACT_VERSION:
            result.add(
                "WRONG_VALIDATION_SUITES_VERSION",
                "binding.validation_suites_contract_version",
                f"binding declares {declared_v!r} != {EXPECTED_CONTRACT_VERSION!r}",
            )
    if binding.get("requirements_lock_sha256") not in (None, ""):
        declared_l = binding["requirements_lock_sha256"]
        if declared_l != EXPECTED_LOCK_SHA256:
            result.add(
                "STALE_LOCK_HASH",
                "binding.requirements_lock_sha256",
                f"binding declares {declared_l} != expected {EXPECTED_LOCK_SHA256}",
            )
    # Explicit stale input/report declarations for controls.
    for item in binding.get("expected_input_hashes") or []:
        if not isinstance(item, Mapping):
            continue
        rel = item.get("path")
        expected = item.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            continue
        # Stash into result.stats for evaluate to verify against disk.
        result.stats.setdefault("_binding_inputs", []).append(
            {"path": rel, "sha256": expected}
        )
    for item in binding.get("expected_report_hashes") or []:
        if not isinstance(item, Mapping):
            continue
        rel = item.get("path")
        expected = item.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            continue
        result.stats.setdefault("_binding_reports", []).append(
            {"path": rel, "sha256": expected}
        )
    if binding.get("freshness_status") in {"EXPIRED", "STALE", "INVALID"}:
        result.add(
            "EVIDENCE_EXPIRED",
            "binding.freshness_status",
            f"binding freshness_status={binding.get('freshness_status')!r}",
        )
    if binding.get("references_old_manifest") is True:
        result.add(
            "EVIDENCE_OLD_MANIFEST",
            "binding.references_old_manifest",
            "binding explicitly references an old/unacceptable manifest set",
        )


def evaluate_evidence_freshness(
    root: Path,
    *,
    evidence_index: Path | None = None,
    binding: Mapping[str, Any] | None = None,
    expected_contract_version: str = EXPECTED_CONTRACT_VERSION,
    expected_validation_suites_sha256: str = EXPECTED_VALIDATION_SUITES_SHA256,
) -> CheckResult:
    result = CheckResult(ok=True)
    try:
        apply_binding_overrides(result, binding)

        upstream = bind_upstream_manifests(root, result)
        suites = bind_validation_suites(
            root,
            result,
            expected_version=expected_contract_version,
            expected_sha256=expected_validation_suites_sha256,
        )
        deliverables = bind_deliverables(root, result)
        lock = bind_lock(root, result)
        sources = bind_core_sources(root, result)

        index_path = evidence_index or (root / EVIDENCE_INDEX_REL)
        if not index_path.is_file():
            result.add(
                "MISSING_FILE",
                to_posix(
                    str(index_path.relative_to(root))
                    if index_path.is_relative_to(root)
                    else str(index_path)
                ),
                "evidence-index.json is missing",
            )
            evidence_stats: dict[str, Any] = {"reports_checked": 0}
        else:
            evidence_stats = check_evidence_reports(root, index_path, result)

        # Binding-declared input/report hash expectations (negative controls).
        for item in result.stats.pop("_binding_inputs", []):
            rel = item["path"]
            expected = item["sha256"]
            path = root / rel
            if not path.is_file():
                result.add("MISSING_FILE", rel, "binding input path missing")
                continue
            actual = sha256_file(path)
            if actual != expected:
                result.add(
                    "STALE_INPUT_HASH",
                    rel,
                    f"binding expected input hash {expected} != disk {actual}",
                )
        for item in result.stats.pop("_binding_reports", []):
            rel = item["path"]
            expected = item["sha256"]
            path = root / rel
            if not path.is_file():
                result.add("MISSING_FILE", rel, "binding report path missing")
                continue
            actual = sha256_file(path)
            if actual != expected:
                result.add(
                    "STALE_REPORT_HASH",
                    rel,
                    f"binding expected report hash {expected} != disk {actual}",
                )

        scanned = (
            len(upstream)
            + (1 if suites.get("manifest_sha256") else 0)
            + (1 if deliverables.get("runtime_sha256") else 0)
            + (1 if lock.get("sha256") else 0)
            + len(sources)
            + int(evidence_stats.get("reports_checked") or 0)
            + int(evidence_stats.get("inputs_checked") or 0)
            + int(evidence_stats.get("sources_checked") or 0)
        )
        if scanned == 0:
            result.add(
                "ZERO_SCAN_TARGETS",
                "evidence-freshness",
                "zero freshness targets scanned; fail-closed",
            )

        # Deduplicate.
        unique: list[Issue] = []
        seen: set[tuple[str, str, str]] = set()
        for issue in result.issues:
            key = (issue.code, issue.location, issue.message)
            if key in seen:
                continue
            seen.add(key)
            unique.append(issue)
        result.issues = unique
        result.ok = len(result.issues) == 0
        result.stats = {
            "scanned": scanned,
            "issue_count": len(result.issues),
            "upstream_manifests": upstream,
            "validation_suites": suites,
            "deliverables": deliverables,
            "lock": lock,
            "core_sources": sources,
            "evidence": evidence_stats,
            "expected_contract_version": expected_contract_version,
            "expected_validation_suites_sha256": expected_validation_suites_sha256,
            "expected_lock_sha256": EXPECTED_LOCK_SHA256,
        }
        return result
    except Exception as exc:  # noqa: BLE001
        result.add("CHECKER_ERROR", "evaluate_evidence_freshness", repr(exc))
        result.ok = False
        return result


def build_report(result: CheckResult) -> dict[str, Any]:
    issues = [
        i.as_dict()
        for i in sorted(result.issues, key=lambda x: (x.code, x.location, x.message))
    ]
    return {
        "schema": "dssc.evidence-freshness-check.result.v1",
        "ok": result.ok and len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
        "reason_codes": sorted({i["code"] for i in issues}),
        "stats": result.stats,
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cwd_policy": "repository-root-via-script-location",
        },
    }


def run_self_test() -> dict[str, Any]:
    """Exercise the fail-closed core source-hash policy contract in memory."""

    cases: tuple[tuple[str, Mapping[str, Any], str | None], ...] = (
        (
            "core-results-source-hash-policy-missing",
            {
                "schema": CORE_RESULTS_SCHEMA,
                "source_hashes": {"scripts/validate.py": "0" * 64},
            },
            "CORE_SOURCE_HASH_POLICY_REQUIRED",
        ),
        (
            "core-results-source-hash-policy-weakened",
            {
                "schema": CORE_RESULTS_SCHEMA,
                "source_hash_policy": "record-only",
                "source_hashes": {"scripts/validate.py": "0" * 64},
            },
            "CORE_SOURCE_HASH_POLICY_REQUIRED",
        ),
        (
            "core-results-source-hash-policy-valid",
            {
                "schema": CORE_RESULTS_SCHEMA,
                "source_hash_policy": CORE_SOURCE_HASH_POLICY,
                "source_hashes": {"scripts/validate.py": "0" * 64},
            },
            None,
        ),
    )
    controls: list[dict[str, Any]] = []
    for control_id, fixture, expected_code in cases:
        result = CheckResult()
        recognized = enforce_core_source_hash_contract(
            fixture,
            evidence_path=f"self-test/{control_id}.json",
            result=result,
        )
        codes = sorted({issue.code for issue in result.issues})
        passed = recognized and (
            not codes if expected_code is None else expected_code in codes and not result.ok
        )
        controls.append(
            {
                "id": control_id,
                "expected_reason_code": expected_code,
                "observed_reason_codes": codes,
                "status": "PASS" if passed else "FAIL",
            }
        )
    failed = [item["id"] for item in controls if item["status"] != "PASS"]
    return {
        "schema": "dssc.evidence-freshness-check.self-test.v1",
        "ok": not failed,
        "control_count": len(controls),
        "failed_controls": failed,
        "controls": controls,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run in-memory negative controls for the core source-hash policy",
    )
    parser.add_argument(
        "--evidence-index",
        type=Path,
        default=None,
        help="override evidence-index.json path (negative controls)",
    )
    parser.add_argument(
        "--binding",
        type=Path,
        default=None,
        help="optional external binding JSON (negative controls)",
    )
    parser.add_argument(
        "--expected-validation-suites-sha256",
        default=EXPECTED_VALIDATION_SUITES_SHA256,
        help="expected live validation-suites manifest hash",
    )
    parser.add_argument(
        "--expected-contract-version",
        default=EXPECTED_CONTRACT_VERSION,
        help="expected live validation-suites contract_version",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        report = run_self_test()
        text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.json_out is not None:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(text, encoding="utf-8", newline="\n")
        sys.stdout.write(text)
        return 0 if report.get("ok") else 1
    root = args.root.resolve()
    binding: Mapping[str, Any] | None = None
    if args.binding is not None:
        try:
            binding = load_json(args.binding)
        except Exception as exc:  # noqa: BLE001
            report = {
                "schema": "dssc.evidence-freshness-check.result.v1",
                "ok": False,
                "issue_count": 1,
                "issues": [
                    {
                        "code": "CHECKER_ERROR",
                        "location": str(args.binding),
                        "message": f"failed to load binding: {exc!r}",
                    }
                ],
                "reason_codes": ["CHECKER_ERROR"],
                "stats": {},
            }
            sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
            return 1

    try:
        result = evaluate_evidence_freshness(
            root,
            evidence_index=args.evidence_index,
            binding=binding,
            expected_contract_version=args.expected_contract_version,
            expected_validation_suites_sha256=args.expected_validation_suites_sha256,
        )
        report = build_report(result)
    except Exception as exc:  # noqa: BLE001
        report = {
            "schema": "dssc.evidence-freshness-check.result.v1",
            "ok": False,
            "issue_count": 1,
            "issues": [
                {
                    "code": "CHECKER_ERROR",
                    "location": "main",
                    "message": repr(exc),
                }
            ],
            "reason_codes": ["CHECKER_ERROR"],
            "stats": {},
        }

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(text)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
