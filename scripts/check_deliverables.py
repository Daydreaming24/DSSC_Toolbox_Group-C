#!/usr/bin/env python3
"""Fail-closed Phase 09 deliverables manifest checker.

Consumes ``C_Semantic_Treehouse/manifests/deliverables.json`` as the sole
required-files inventory. Does not hard-code a second required-files path list
for existence checks. Cross-record coverage gates confirm that contract anchors
(release-manifest artifacts, upstream manifests/schemas, validation-suites,
navigation docs, Phase 09 anchors) appear as deliverable entries.

``deliverables.json`` intentionally excludes itself; its SHA-256 is recorded only
in ignored runtime evidence and is never embedded as an expected constant.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MANIFEST = (
    ROOT / "C_Semantic_Treehouse" / "manifests" / "deliverables.json"
)
DEFAULT_SCHEMA = (
    ROOT
    / "C_Semantic_Treehouse"
    / "manifests"
    / "schemas"
    / "deliverables.schema.json"
)
SELF_MANIFEST_REL = "C_Semantic_Treehouse/manifests/deliverables.json"
SELF_SCHEMA_REL = "C_Semantic_Treehouse/manifests/schemas/deliverables.schema.json"
CHECKER_REL = "scripts/check_deliverables.py"
EVIDENCE_INDEX_REL = (
    "C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json"
)
VALIDATION_SUITES_REL = "C_Semantic_Treehouse/manifests/validation-suites.json"
VALIDATION_SUITES_SCHEMA_REL = (
    "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json"
)
RELEASE_MANIFEST_REL = "C_Semantic_Treehouse/manifests/release-manifest.json"
EXPECTED_CONTRACT_VERSION = "1.6.0"
EXPECTED_VALIDATION_SUITES_SHA256 = (
    "09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836"
)
EXPECTED_CONTAINER_CONTRACT = (
    "dssc.phase01.container.v1-linux-amd64-python-3.12.10-"
    "fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db"
)

# Coverage anchors that must appear in deliverables.json (listing check only).
# Existence/hash for required files is driven solely by deliverable records.
COVERAGE_ANCHORS: tuple[str, ...] = (
    SELF_SCHEMA_REL,
    CHECKER_REL,
    EVIDENCE_INDEX_REL,
    VALIDATION_SUITES_REL,
    VALIDATION_SUITES_SCHEMA_REL,
    RELEASE_MANIFEST_REL,
    "C_Semantic_Treehouse/manifests/baseline-test-cases.json",
    "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
    "C_Semantic_Treehouse/manifests/v0.4-test-cases.json",
    "C_Semantic_Treehouse/manifests/schemas/baseline-test-cases.schema.json",
    "C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json",
    "C_Semantic_Treehouse/manifests/schemas/v0.4-requirements.schema.json",
    "C_Semantic_Treehouse/manifests/schemas/v0.4-test-cases.schema.json",
    "迁移清单.md",
    "docs/v0.4/README.md",
    "scripts/README.md",
    ".github/workflows/validate.yml",
    "scripts/reproduce.ps1",
    "scripts/reproduce.sh",
)

# Runtime residue that must never appear as a publication deliverable.
# Tracked structural placeholders such as build/.gitkeep are allowed; phase
# evidence, venv, caches, and nested git metadata are not.
FORBIDDEN_DELIVERABLE_PREFIXES: tuple[str, ...] = (
    "build/",
    "build/phase-",
    "build/final-qa/",
    "build/clean-clone/",
    "build/remote-clean-clone/",
    "build/ci-verification/",
    ".venv/",
    "__pycache__/",
    ".git/",
)

# The validation image intentionally excludes ``build`` and mounts a fresh
# runtime evidence directory at ``/workspace/build``.  The tracked one-byte
# placeholder is therefore unavailable in that gitless image even though it is
# validated by every host/clone run.  This is the sole container omission; it
# does not relax any other manifest existence or hash check.
CONTAINER_OMITTED_STRUCTURAL_PATHS = frozenset({"build/.gitkeep"})

REASON_CODES = frozenset(
    {
        "SCHEMA_INVALID",
        "EMPTY_ENTRIES",
        "DUPLICATE_ID",
        "DUPLICATE_PATH",
        "CASE_PATH_COLLISION",
        "PATH_ESCAPE",
        "ABSOLUTE_PATH",
        "GLOB_PATH",
        "MISSING_FILE",
        "EMPTY_FILE",
        "STALE_HASH",
        "UNPARSEABLE_FILE",
        "UNKNOWN_ROLE",
        "MISSING_LICENSE_DECISION",
        "NOASSERTION_WITHOUT_DECISION",
        "ORPHAN_DECISION",
        "SELF_LISTED",
        "IGNORED_AS_DELIVERABLE",
        "TRACKED_NOT_LISTED",
        "PUBLISH_FALSE_STILL_TRACKED",
        "COVERAGE_MISSING",
        "VALIDATION_SUITES_MISMATCH",
        "SOURCE_REQUIRED",
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
    ok: bool
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def to_posix(path: str) -> str:
    return path.replace("\\", "/")


def is_absolute_path(path: str) -> bool:
    if path.startswith("/") or path.startswith("\\"):
        return True
    if re.match(r"^[A-Za-z]:[/\\]", path):
        return True
    return False


def has_path_escape(path: str) -> bool:
    parts = to_posix(path).split("/")
    return any(part == ".." for part in parts)


def has_glob(path: str) -> bool:
    return any(ch in path for ch in "*?[]{}")


def git_ls_files(root: Path) -> list[str]:
    raw = subprocess.check_output(
        ["git", "ls-files", "-z"],
        cwd=root,
        stderr=subprocess.PIPE,
    )
    return sorted(
        p.decode("utf-8") for p in raw.split(b"\0") if p
    )


def container_candidate_files(root: Path) -> list[str]:
    """Inventory the immutable image tree when ``.git`` is intentionally absent.

    Runtime evidence under ``build`` is a mounted output sink, not candidate
    content.  Every other regular file in the image must be declared by the
    deliverables manifest (apart from the manifest's named self-exception).
    """

    def raise_walk_error(error: OSError) -> None:
        raise error

    found: list[str] = []
    for current, directories, files in os.walk(
        root,
        topdown=True,
        onerror=raise_walk_error,
    ):
        current_path = Path(current)
        for name in directories:
            path = current_path / name
            if path.is_symlink():
                raise OSError(f"symlink-like candidate node is forbidden: {path}")
        if current_path == root:
            directories[:] = [name for name in directories if name != "build"]
        for name in files:
            path = current_path / name
            if path.is_symlink():
                raise OSError(f"symlink-like candidate node is forbidden: {path}")
            found.append(path.relative_to(root).as_posix())
    return sorted(found)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_schema(
    instance: Mapping[str, Any], schema: Mapping[str, Any]
) -> list[Issue]:
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    issues: list[Issue] = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        loc = "/" + "/".join(str(p) for p in error.absolute_path)
        issues.append(
            Issue(
                code="SCHEMA_INVALID",
                location=loc or "/",
                message=error.message,
            )
        )
    return issues


def collect_release_manifest_paths(root: Path) -> list[str]:
    path = root / RELEASE_MANIFEST_REL
    if not path.is_file():
        return []
    data = load_json(path)
    found: list[str] = []
    for entry in data.get("sourceCatalog", []):
        p = entry.get("path")
        if isinstance(p, str):
            found.append(to_posix(p))
    for release in data.get("releases", []):
        for art in release.get("artifacts", []):
            p = art.get("path")
            if isinstance(p, str):
                found.append(to_posix(p))
    reg = data.get("validationSuiteRegistry") or {}
    p = reg.get("path")
    if isinstance(p, str):
        found.append(to_posix(p))
    for reg_entry in data.get("requirementRegistries", []):
        p = reg_entry.get("path")
        if isinstance(p, str):
            found.append(to_posix(p))
    return sorted(set(found))


def looks_parseable(
    path: Path, media_type: str, *, rel_path: str, role: str | None
) -> tuple[bool, str]:
    """Return whether a required deliverable is format-parseable.

    Intentional UNTESTABLE / fault-injection fixtures under fixtures/** may be
    deliberately malformed; those only need non-empty readable bytes.
    """
    try:
        if path.stat().st_size == 0:
            return False, "empty file"
        # Fault-injection fixtures are oracles for harness ERROR/UNTESTABLE,
        # not well-formed JSON-LD documents.
        if role == "fixture" or "/fixtures/" in rel_path.replace("\\", "/"):
            with path.open("rb") as handle:
                handle.read(1)
            return True, "ok-fixture-bytes"
        if media_type in {
            "application/json",
            "application/ld+json",
            "application/schema+json",
        }:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
            return True, "ok"
        if media_type in {"application/yaml", "text/yaml"}:
            import yaml

            with path.open("r", encoding="utf-8") as handle:
                yaml.safe_load(handle)
            return True, "ok"
        # Binary / free-form: existence + non-empty is enough.
        with path.open("rb") as handle:
            handle.read(1)
        return True, "ok"
    except Exception as exc:  # noqa: BLE001 — surface parse failures as issues
        return False, str(exc)


def evaluate_deliverables(
    root: Path,
    manifest_path: Path,
    schema_path: Path,
    *,
    tracked_files: Sequence[str] | None = None,
) -> CheckResult:
    result = CheckResult(ok=True)
    container_gitless = (
        os.environ.get("DSSC_VALIDATION_PROFILE", "").strip().casefold()
        == "container"
        and os.environ.get("DSSC_VALIDATION_CONTAINER_CONTRACT", "")
        == EXPECTED_CONTAINER_CONTRACT
        and not (root / ".git").exists()
        and root.as_posix() == "/workspace"
    )
    container_omitted_count = 0
    inventory_mode = "provided" if tracked_files is not None else "git"
    try:
        if not schema_path.is_file():
            result.add(
                "MISSING_FILE",
                str(schema_path),
                "deliverables schema is missing",
            )
            return result
        if not manifest_path.is_file():
            result.add(
                "MISSING_FILE",
                str(manifest_path),
                "deliverables manifest is missing",
            )
            return result

        schema = load_json(schema_path)
        try:
            manifest = load_json(manifest_path)
        except Exception as exc:  # noqa: BLE001
            result.add(
                "UNPARSEABLE_FILE",
                SELF_MANIFEST_REL,
                f"deliverables.json is not valid JSON: {exc}",
            )
            return result

        schema_issues = validate_schema(manifest, schema)
        for issue in schema_issues:
            result.issues.append(issue)
            result.ok = False
        if schema_issues:
            # Still attempt semantic checks where possible.
            pass

        if not isinstance(manifest, dict):
            result.add(
                "SCHEMA_INVALID",
                SELF_MANIFEST_REL,
                "manifest root must be an object",
            )
            return result

        deliverables = manifest.get("deliverables")
        if not isinstance(deliverables, list) or len(deliverables) == 0:
            result.add(
                "EMPTY_ENTRIES",
                "deliverables",
                "deliverables array is missing or empty",
            )
            return result

        # validation-suites freeze binding from §6.1
        vs = manifest.get("validation_suites") or {}
        if isinstance(vs, dict):
            if vs.get("contract_version") != EXPECTED_CONTRACT_VERSION:
                result.add(
                    "VALIDATION_SUITES_MISMATCH",
                    "validation_suites.contract_version",
                    (
                        f"expected {EXPECTED_CONTRACT_VERSION}, "
                        f"got {vs.get('contract_version')!r}"
                    ),
                )
            if vs.get("manifest_sha256") != EXPECTED_VALIDATION_SUITES_SHA256:
                result.add(
                    "VALIDATION_SUITES_MISMATCH",
                    "validation_suites.manifest_sha256",
                    "manifest SHA-256 does not match Phase 08/§6.1 freeze",
                )
            vs_path = root / to_posix(str(vs.get("manifest_path") or ""))
            if vs_path.is_file():
                actual = sha256_file(vs_path)
                declared = vs.get("manifest_sha256")
                if isinstance(declared, str) and actual != declared:
                    result.add(
                        "STALE_HASH",
                        str(vs.get("manifest_path")),
                        "validation-suites.json hash does not match bytes on disk",
                    )

        decisions = manifest.get("license_decisions") or []
        decision_ids: set[str] = set()
        if isinstance(decisions, list):
            for d in decisions:
                if isinstance(d, dict) and isinstance(d.get("id"), str):
                    decision_ids.add(d["id"])

        ids: dict[str, str] = {}
        paths: dict[str, str] = {}
        case_paths: dict[str, str] = {}
        path_set: set[str] = set()
        publish_false_paths: set[str] = set()
        required_count = 0
        scanned = 0

        for idx, item in enumerate(deliverables):
            loc = f"deliverables[{idx}]"
            if not isinstance(item, dict):
                result.add("SCHEMA_INVALID", loc, "entry must be an object")
                continue

            entry_id = item.get("id")
            path = item.get("path")
            if not isinstance(entry_id, str) or not entry_id:
                result.add("SCHEMA_INVALID", f"{loc}.id", "id must be non-empty string")
                continue
            if entry_id in ids:
                result.add(
                    "DUPLICATE_ID",
                    f"{loc}.id",
                    f"duplicate deliverable id {entry_id!r} (also {ids[entry_id]})",
                )
            else:
                ids[entry_id] = loc

            if not isinstance(path, str) or not path:
                result.add(
                    "SCHEMA_INVALID", f"{loc}.path", "path must be non-empty string"
                )
                continue
            path = to_posix(path)

            if path == SELF_MANIFEST_REL:
                result.add(
                    "SELF_LISTED",
                    f"{loc}.path",
                    "deliverables.json must exclude itself",
                )

            if is_absolute_path(path):
                result.add(
                    "ABSOLUTE_PATH",
                    f"{loc}.path",
                    f"absolute path is forbidden: {path!r}",
                )
            if has_path_escape(path):
                result.add(
                    "PATH_ESCAPE",
                    f"{loc}.path",
                    f"path escape ('..') is forbidden: {path!r}",
                )
            if has_glob(path) or "\\" in item.get("path", ""):
                result.add(
                    "GLOB_PATH",
                    f"{loc}.path",
                    f"glob characters or backslashes are forbidden: {path!r}",
                )

            if any(
                path == pref.rstrip("/") or path.startswith(pref)
                for pref in FORBIDDEN_DELIVERABLE_PREFIXES
            ):
                if path != "build/.gitkeep":
                    result.add(
                        "IGNORED_AS_DELIVERABLE",
                        f"{loc}.path",
                        f"ignored runtime path must not be a deliverable: {path!r}",
                    )

            if path in paths:
                result.add(
                    "DUPLICATE_PATH",
                    f"{loc}.path",
                    f"duplicate path {path!r} (also {paths[path]})",
                )
            else:
                paths[path] = loc
                path_set.add(path)

            folded = path.casefold()
            if folded in case_paths and case_paths[folded] != path:
                result.add(
                    "CASE_PATH_COLLISION",
                    f"{loc}.path",
                    (
                        f"case-folded collision between {path!r} and "
                        f"{case_paths[folded]!r}"
                    ),
                )
            else:
                case_paths[folded] = path

            role = item.get("role")
            # Unknown role is primarily a schema concern; keep semantic code too.
            allowed_roles = {
                "model",
                "fixture",
                "test",
                "manifest",
                "schema",
                "script",
                "checker",
                "documentation",
                "evidence",
                "workflow",
                "environment",
                "governance",
                "mapping",
                "quality",
                "handoff",
                "input",
                "provenance",
                "prompt",
                "administrative",
                "lock",
                "other",
            }
            if role not in allowed_roles:
                result.add(
                    "UNKNOWN_ROLE",
                    f"{loc}.role",
                    f"unknown role {role!r}",
                )

            decision_id = item.get("decision_id")
            license_id = item.get("license_id")
            if not isinstance(decision_id, str) or not decision_id:
                result.add(
                    "MISSING_LICENSE_DECISION",
                    f"{loc}.decision_id",
                    "decision_id is required",
                )
            elif decision_id not in decision_ids:
                result.add(
                    "MISSING_LICENSE_DECISION",
                    f"{loc}.decision_id",
                    f"decision_id {decision_id!r} is not listed in license_decisions",
                )
            if license_id == "NOASSERTION":
                if not isinstance(decision_id, str) or decision_id not in decision_ids:
                    result.add(
                        "NOASSERTION_WITHOUT_DECISION",
                        f"{loc}.license_id",
                        "NOASSERTION requires an explicit maintainer decision_id",
                    )

            origin = item.get("origin")
            source = item.get("source")
            if origin in {"derived", "inherited", "third-party"} and not isinstance(
                source, dict
            ):
                result.add(
                    "SOURCE_REQUIRED",
                    f"{loc}.source",
                    f"origin {origin!r} requires a source object",
                )

            publish = item.get("publish")
            required = item.get("required")
            if publish is False:
                publish_false_paths.add(path)
            if required is True:
                required_count += 1

            # File existence / hash / parse for every listed deliverable.
            scanned += 1
            abs_path = root / path
            if not abs_path.is_file():
                if container_gitless and path in CONTAINER_OMITTED_STRUCTURAL_PATHS:
                    container_omitted_count += 1
                    continue
                result.add(
                    "MISSING_FILE",
                    path,
                    "listed deliverable file does not exist or is not a regular file",
                )
                continue
            if abs_path.stat().st_size == 0 and required is True:
                result.add(
                    "EMPTY_FILE",
                    path,
                    "required deliverable file is empty",
                )
                continue

            actual_hash = sha256_file(abs_path)
            declared_hash = item.get("sha256")
            if not isinstance(declared_hash, str) or actual_hash != declared_hash:
                result.add(
                    "STALE_HASH",
                    path,
                    (
                        f"declared sha256 {declared_hash!r} does not match "
                        f"actual {actual_hash}"
                    ),
                )

            media_type = item.get("media_type")
            if isinstance(media_type, str) and required is True:
                ok_parse, detail = looks_parseable(
                    abs_path,
                    media_type,
                    rel_path=path,
                    role=role if isinstance(role, str) else None,
                )
                if not ok_parse:
                    result.add(
                        "UNPARSEABLE_FILE",
                        path,
                        f"required file failed parseability check: {detail}",
                    )

        # Orphan decisions (informational severity kept as issue only if unused
        # by all entries when decisions array is empty — already schema-gated).
        used_decisions = {
            item.get("decision_id")
            for item in deliverables
            if isinstance(item, dict)
        }
        for did in sorted(decision_ids):
            if did not in used_decisions:
                # Allowed: unused interim decisions may remain for future files.
                pass

        # Coverage anchors must be listed (not a second existence inventory).
        for anchor in COVERAGE_ANCHORS:
            if anchor not in path_set:
                result.add(
                    "COVERAGE_MISSING",
                    anchor,
                    "required coverage anchor is not listed in deliverables.json",
                )

        for rel in collect_release_manifest_paths(root):
            if rel not in path_set:
                result.add(
                    "COVERAGE_MISSING",
                    rel,
                    "release-manifest referenced path is not listed in deliverables",
                )

        if container_gitless:
            structural_count = sum(
                1
                for item in deliverables
                if isinstance(item, Mapping)
                and item.get("path") == "build/.gitkeep"
            )
            if structural_count != 1 or container_omitted_count != 1:
                result.add(
                    "COVERAGE_MISSING",
                    "build/.gitkeep",
                    (
                        "gitless validation container requires exactly one manifest "
                        "entry for its intentionally omitted tracked structural "
                        f"placeholder; entries={structural_count}, omissions={container_omitted_count}"
                    ),
                )

        # Bidirectional git coverage (named self-exception for deliverables.json).
        if tracked_files is None:
            if container_gitless:
                tracked_files = container_candidate_files(root)
                inventory_mode = "container-filesystem"
            else:
                try:
                    tracked_files = git_ls_files(root)
                except (subprocess.SubprocessError, OSError) as exc:
                    result.add(
                        "CHECKER_ERROR",
                        "git ls-files",
                        f"failed to list tracked files: {exc}",
                    )
                    tracked_files = []
                    inventory_mode = "git-error"

        tracked_set = {to_posix(p) for p in tracked_files}
        if not tracked_set:
            result.add(
                "ZERO_SCAN_TARGETS",
                "candidate-inventory",
                f"candidate inventory is empty (mode={inventory_mode})",
            )
        for rel in sorted(tracked_set):
            if rel == SELF_MANIFEST_REL:
                continue
            if rel not in path_set:
                result.add(
                    "TRACKED_NOT_LISTED",
                    rel,
                    "tracked candidate file has no deliverables.json record",
                )

        for rel in sorted(publish_false_paths):
            if rel in tracked_set:
                result.add(
                    "PUBLISH_FALSE_STILL_TRACKED",
                    rel,
                    "publish:false file must not remain in the push tracked tree",
                )

        if scanned == 0:
            result.add(
                "ZERO_SCAN_TARGETS",
                "deliverables",
                "zero deliverable entries were scanned",
            )

        result.stats = {
            "deliverable_count": len(deliverables),
            "required_count": required_count,
            "scanned": scanned,
            "tracked_count": len(tracked_set),
            "candidate_inventory_mode": inventory_mode,
            "container_omitted_structural_count": container_omitted_count,
            "issue_count": len(result.issues),
            "manifest_path": to_posix(
                str(manifest_path.relative_to(root))
                if manifest_path.is_relative_to(root)
                else str(manifest_path)
            ),
            "schema_path": to_posix(
                str(schema_path.relative_to(root))
                if schema_path.is_relative_to(root)
                else str(schema_path)
            ),
            "schema_sha256": sha256_file(schema_path) if schema_path.is_file() else None,
            # Runtime-only: never treat as oracle for deliverables.json itself.
            "deliverables_runtime_sha256": (
                sha256_file(manifest_path) if manifest_path.is_file() else None
            ),
            "validation_suites_contract_version": (
                vs.get("contract_version") if isinstance(vs, dict) else None
            ),
            "validation_suites_manifest_sha256": (
                vs.get("manifest_sha256") if isinstance(vs, dict) else None
            ),
        }
        return result
    except Exception as exc:  # noqa: BLE001
        result.add("CHECKER_ERROR", "evaluate_deliverables", repr(exc))
        return result


def build_report(result: CheckResult) -> dict[str, Any]:
    issues = [i.as_dict() for i in sorted(result.issues, key=lambda x: (x.code, x.location, x.message))]
    reason_codes = sorted({i["code"] for i in issues})
    return {
        "schema": "dssc.deliverables-check.result.v1",
        "ok": result.ok and len(issues) == 0,
        "issue_count": len(issues),
        "reason_codes": reason_codes,
        "issues": issues,
        "stats": result.stats,
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cwd_policy": "repository-root-via-script-location",
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Phase 09 deliverables manifest (fail-closed)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to deliverables.json (default: package manifests path)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to deliverables.schema.json",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write machine JSON report",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = args.root.resolve()
    manifest_path = (
        args.manifest.resolve()
        if args.manifest is not None
        else (root / SELF_MANIFEST_REL)
    )
    schema_path = (
        args.schema.resolve()
        if args.schema is not None
        else (root / SELF_SCHEMA_REL)
    )

    result = evaluate_deliverables(root, manifest_path, schema_path)
    report = build_report(result)

    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(text)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
