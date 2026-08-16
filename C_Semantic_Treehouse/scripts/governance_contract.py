"""Deterministic governance/provenance validation for Phase 06.

The module deliberately consumes the established manifest validators before it
reads governance assertions.  This prevents malformed, stale, or disconnected
authority records from being hidden behind a documentation-only PASS.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


GOVERNANCE_RELPATH = "C_Semantic_Treehouse/governance"
RESULT_RELPATH = "build/validation/governance/results.json"
REPORT_RELPATH = "build/validation/governance/report.md"
ENVIRONMENT_RELPATH = "build/validation/governance/run-environment.json"
PREFLIGHT_RELPATH = "build/phase-06/governance/manifest-preflight.json"
NEGATIVE_RELPATH = "build/phase-06/governance/negative-controls.json"
DETERMINISM_RELPATH = "build/phase-06/governance/determinism.json"
SPARQL_MANIFEST_RELPATH = (
    "C_Semantic_Treehouse/tests/sparql/sparql-test-cases.json"
)
SPARQL_SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/tests/sparql/sparql-test-cases.schema.json"
)
LOCK_RELPATH = "requirements.lock"

EXPECTED_FILES = (
    "model-card.md",
    "changelog.md",
    "namespace-policy.md",
    "release-policy.md",
    "deprecation-policy.md",
    "review-workflow.md",
    "provenance.jsonld",
)

EXPECTED_CONTRACT_VERSION = "1.6.0"
MANIFEST_ORDER = (
    "release",
    "baseline",
    "requirements",
    "v0.4-test-cases",
    "validation-suites",
)
MANIFEST_PATHS = {
    "release": (
        "C_Semantic_Treehouse/manifests/release-manifest.json",
        "C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json",
    ),
    "baseline": (
        "C_Semantic_Treehouse/manifests/baseline-test-cases.json",
        "C_Semantic_Treehouse/manifests/schemas/baseline-test-cases.schema.json",
    ),
    "requirements": (
        "C_Semantic_Treehouse/manifests/v0.4-requirements.json",
        "C_Semantic_Treehouse/manifests/schemas/v0.4-requirements.schema.json",
    ),
    "v0.4-test-cases": (
        "C_Semantic_Treehouse/manifests/v0.4-test-cases.json",
        "C_Semantic_Treehouse/manifests/schemas/v0.4-test-cases.schema.json",
    ),
    "validation-suites": (
        "C_Semantic_Treehouse/manifests/validation-suites.json",
        "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json",
    ),
}

REQUIRED_SOURCE_PATHS = (
    "scripts/validate.py",
    "scripts/dssc_validation/__init__.py",
    "scripts/dssc_validation/baseline_manifest.py",
    "scripts/dssc_validation/checks_all.py",
    "scripts/dssc_validation/checks_phase06.py",
    "scripts/dssc_validation/entrypoint_catalog.py",
    "scripts/dssc_validation/hashing.py",
    "scripts/dssc_validation/paths.py",
    "scripts/dssc_validation/release_manifest.py",
    "scripts/dssc_validation/requirements_registry.py",
    "scripts/dssc_validation/suite_registry.py",
    "scripts/dssc_validation/v04_manifest.py",
    "C_Semantic_Treehouse/scripts/governance_contract.py",
    "C_Semantic_Treehouse/scripts/quality_metrics.py",
    "C_Semantic_Treehouse/scripts/run_sparql_tests.py",
    "C_Semantic_Treehouse/scripts/sparql_manifest.py",
    "C_Semantic_Treehouse/scripts/sparql_report.py",
    "C_Semantic_Treehouse/scripts/validate_governance.py",
)

REQUIRED_HEADINGS = {
    "model-card.md": (
        "## Version Scope and History",
        "## v0.4 Scope",
        "## Intended Users",
        "## Intended Use",
        "## Risks and Limitations",
        "## Validation Strategy",
        "## Review Status",
    ),
    "changelog.md": (
        "## v0.4",
        "## v0.3",
        "## v0.2",
        "## v0.1",
    ),
    "namespace-policy.md": (
        "## Historical Project Namespace",
        "## v0.4 Contract Namespace",
        "## Coexistence and Migration Boundary",
    ),
    "release-policy.md": (
        "## D-Group Input Gate",
        "## Four-State Gate",
        "## Manifest Gate",
        "## Cross-Platform Gate",
        "## Evidence Gate",
        "## Approval and Publication Gate",
    ),
    "deprecation-policy.md": (
        "## Historical Retention",
        "## v0.3 to v0.4 Metadata Migration",
        "## Energy Reading Record",
    ),
    "review-workflow.md": (
        "## C-Group Semantic Review",
        "## D-Group Contract Verification",
        "## Domain Review",
        "## Automated Gate",
        "## Human Release Approval",
        "## Current v0.4 Evidence Status",
    ),
}

REQUIRED_TOKENS = {
    "model-card.md": (
        "v0.1",
        "v0.2",
        "v0.3",
        "v0.4",
        "dcat:Dataset",
        "https://example.org/dssc-energy#",
        "wire-profile breaking",
        "Energy Reading Record",
        "PASS",
        "FAIL",
        "INAPPLICABLE",
        "UNTESTABLE",
    ),
    "changelog.md": (
        "be:DataProductMetadata",
        "dcat:Dataset",
        "dct:identifier",
        "ex:datasetId",
        "JSON",
        "application/json",
        "A Group",
        "B Group",
        "D Group",
        "wire-profile breaking",
    ),
    "namespace-policy.md": (
        "https://w3id.org/dssc-demo/building-energy#",
        "https://example.org/dssc-energy#",
        "dcat:Dataset",
        "v0.3",
        "v0.4",
        "Energy Reading Record",
    ),
    "release-policy.md": (
        "a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda",
        "release-manifest.json",
        "baseline-test-cases.json",
        "v0.4-requirements.json",
        "v0.4-test-cases.json",
        "validation-suites.json",
        "Windows",
        "Linux",
        "Docker",
        "pending",
    ),
    "deprecation-policy.md": (
        "be:DataProductMetadata",
        "dcat:Dataset",
        "dct:identifier",
        "ex:datasetId",
        "be:endpointUrl",
        "dcat:endpointURL",
        "be:format",
        "dct:format",
        "application/json",
        "change: none",
    ),
    "review-workflow.md": (
        "C Group",
        "D Group",
        "Domain Reviewer",
        "scripts/validate.py --suite all",
        "Release Approver",
        "CI",
        "GitHub",
        "Semantic Treehouse",
        "PENDING",
    ),
}

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")

AGENT_C = "https://w3id.org/dssc-demo/agents/c-group"
AGENT_D = "https://w3id.org/dssc-demo/agents/d-group"
V01 = "https://w3id.org/dssc-demo/building-energy/v0.1"
V02 = "https://w3id.org/dssc-demo/building-energy/v0.2"
V03 = "https://w3id.org/dssc-demo/building-energy/v0.3"
V04 = "https://w3id.org/dssc-demo/building-energy/v0.4"
HISTORICAL_ACTIVITY = (
    "https://w3id.org/dssc-demo/building-energy/activity/model-generation"
)
HISTORICAL_REPORT_IDS = (
    "https://w3id.org/dssc-demo/building-energy/report/rdf-validation",
    "https://w3id.org/dssc-demo/building-energy/report/pyshacl-validation",
    "https://w3id.org/dssc-demo/building-energy/report/jsonld-validation",
    "https://w3id.org/dssc-demo/building-energy/report/jsonschema-validation",
    "https://w3id.org/dssc-demo/building-energy/report/openapi-validation",
    "https://w3id.org/dssc-demo/building-energy/report/sparql-competency",
    "https://w3id.org/dssc-demo/building-energy/report/quality-metrics",
)
D_SHAPE = "https://w3id.org/dssc-demo/building-energy/source/d-shape-v0.4"
D_NOTE = "https://w3id.org/dssc-demo/building-energy/source/d-change-note-v0.4"
DERIVATION = "https://w3id.org/dssc-demo/building-energy/activity/c-group-v0.4-derivation"
RECORD_CONTRACT = "https://w3id.org/dssc-demo/building-energy/contract/v0.3-energy-reading-record"
VALIDATION_ACTIVITY = "https://w3id.org/dssc-demo/building-energy/activity/phase-06-governance-validation"
VALIDATION_ARTIFACT = "https://w3id.org/dssc-demo/building-energy/evidence/phase-06-manifest-preflight"
EXTERNAL_STATUS_EXPECTATIONS = {
    "https://w3id.org/dssc-demo/building-energy/activity/v0.4-release-approval": {
        "kind": "release-approval",
        "status": "responsibility-accepted",
        "evidence_ref": "docs/v0.4/human-decisions.md",
        "evidence_tokens": (
            "DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED",
            "Daydreaming24",
            "ACCEPTED_LIMITATION",
        ),
    },
    "https://w3id.org/dssc-demo/building-energy/activity/v0.4-ci-validation": {
        "kind": "ci",
        "status": "confirmed",
        "evidence_ref": "docs/v0.4/publication-record.md",
        "evidence_tokens": (
            "Run `head_sha`",
            "Ubuntu job",
            "Windows job",
            "Docker job",
            "`success`",
        ),
    },
    "https://w3id.org/dssc-demo/building-energy/activity/v0.4-github-publication": {
        "kind": "github-publication",
        "status": "confirmed",
        "evidence_ref": "docs/v0.4/publication-record.md",
        "evidence_tokens": (
            "普通 push",
            "canonical GitHub URL",
            "远程 clone resolved SHA",
        ),
    },
    "https://w3id.org/dssc-demo/building-energy/activity/v0.4-treehouse-run": {
        "kind": "treehouse-run",
        "status": "completed-local-optional",
        "evidence_ref": "C_Semantic_Treehouse/C_semantic_treehouse_usage.md",
        "evidence_tokens": (
            "deployment=PASS",
            "current runtime=PAUSED",
            "publication=NOT RUN",
            "SHACL validator execution=PASS",
        ),
    },
}


class DuplicateJsonKey(ValueError):
    """Raised when a JSON object contains two lexical instances of one key."""


@dataclass(frozen=True)
class Check:
    id: str
    passed: bool
    message: str
    details: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "passed": self.passed,
            "message": self.message,
            "details": dict(self.details),
        }


def _check(
    check_id: str,
    passed: bool,
    message: str,
    **details: Any,
) -> Check:
    return Check(check_id, bool(passed), message, details)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_json(root: Path, relpath: str, value: Any) -> None:
    _atomic_write(_resolve_output(root, relpath), _json_bytes(value))


def _write_text(root: Path, relpath: str, value: str) -> None:
    _atomic_write(_resolve_output(root, relpath), value.encode("utf-8"))


def _resolve_output(root: Path, relpath: str) -> Path:
    allowed = (
        "build/validation/governance/",
        "build/phase-06/governance/",
    )
    if not relpath.startswith(allowed) or ".." in PurePosixPath(relpath).parts:
        raise ValueError(f"governance output path is outside the allowlist: {relpath}")
    path = root.joinpath(*PurePosixPath(relpath).parts)
    path.resolve().relative_to(root.resolve())
    return path


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonKey(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _load_json_text(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_reject_duplicate_pairs)


def _safe_repo_path(root: Path, relpath: Any) -> tuple[Path | None, str | None]:
    if not isinstance(relpath, str) or not relpath:
        return None, "path must be a non-empty string"
    if "\\" in relpath or WINDOWS_DRIVE.match(relpath):
        return None, "path must use repository-relative POSIX syntax"
    pure = PurePosixPath(relpath)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        return None, "path must be normalized and repository-relative"
    lexical = root.joinpath(*pure.parts)
    try:
        lexical.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None, "path resolves outside the repository"
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink() or bool(getattr(current, "is_junction", lambda: False)()):
            return None, "path contains a link or junction"
    if not lexical.exists():
        return None, "path is missing"
    try:
        mode = lexical.stat(follow_symlinks=False).st_mode
    except OSError as exc:
        return None, f"path cannot be stat'ed: {exc.__class__.__name__}"
    if not stat.S_ISREG(mode):
        return None, "path is not a regular file"
    return lexical, None


def _manifest_validation_record(
    manifest_id: str,
    passed: bool,
    manifest_sha256: str | None,
    schema_sha256: str | None,
    issues: list[dict[str, Any]],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    manifest_path, schema_path = MANIFEST_PATHS[manifest_id]
    return {
        "id": manifest_id,
        "passed": bool(passed),
        "manifest_path": manifest_path,
        "manifest_sha256": manifest_sha256,
        "schema_path": schema_path,
        "schema_sha256": schema_sha256,
        "issues": issues,
        "summary": dict(summary),
    }


def _current_hash_or_none(root: Path, relpath: str) -> str | None:
    path, issue = _safe_repo_path(root, relpath)
    return _sha256_file(path) if issue is None and path is not None else None


def build_manifest_preflight(root: Path, context: Mapping[str, Any]) -> dict[str, Any]:
    """Run all five established schema/semantic validators in fixed order."""

    from dssc_validation.baseline_manifest import (
        BaselineManifestError,
        load_and_validate_baseline_manifest,
    )
    from dssc_validation.release_manifest import load_and_audit_release_manifest
    from dssc_validation.requirements_registry import load_and_validate_requirements
    from dssc_validation.suite_registry import load_and_validate_registry
    from dssc_validation.v04_manifest import load_and_validate_v04_manifest

    validations: list[dict[str, Any]] = []
    registry_version: str | None = None
    registry_sha256: str | None = None

    try:
        release = load_and_audit_release_manifest(root)
        record = release.deterministic_record()
        validations.append(
            _manifest_validation_record(
                "release",
                release.ok,
                release.manifest_sha256,
                release.schema_sha256,
                list(release.issues),
                {
                    "current_release": record.get("current_release"),
                    "release_ids": record.get("release_ids", []),
                    "artifact_count": record.get("artifact_count", 0),
                },
            )
        )
    except Exception as exc:  # noqa: BLE001 - authority checks fail closed
        validations.append(
            _manifest_validation_record(
                "release",
                False,
                _current_hash_or_none(root, MANIFEST_PATHS["release"][0]),
                _current_hash_or_none(root, MANIFEST_PATHS["release"][1]),
                [{"code": "VALIDATOR_EXCEPTION", "message": exc.__class__.__name__}],
                {},
            )
        )
    if not validations[-1]["passed"]:
        return _finalize_manifest_preflight(validations, registry_version, registry_sha256)

    try:
        baseline = load_and_validate_baseline_manifest(root)
        baseline_record = baseline.deterministic_record()
        validations.append(
            _manifest_validation_record(
                "baseline",
                True,
                baseline.manifest_sha256,
                baseline.schema_sha256,
                [],
                {
                    "case_count": baseline_record["case_count"],
                    "artifact_count": baseline_record["artifact_count"],
                    "release_counts": baseline_record["release_counts"],
                },
            )
        )
    except BaselineManifestError as exc:
        validations.append(
            _manifest_validation_record(
                "baseline",
                False,
                _current_hash_or_none(root, MANIFEST_PATHS["baseline"][0]),
                _current_hash_or_none(root, MANIFEST_PATHS["baseline"][1]),
                [issue.as_dict() for issue in exc.issues], {},
            )
        )
    except Exception as exc:  # noqa: BLE001
        validations.append(
            _manifest_validation_record(
                "baseline",
                False,
                _current_hash_or_none(root, MANIFEST_PATHS["baseline"][0]),
                _current_hash_or_none(root, MANIFEST_PATHS["baseline"][1]),
                [{"code": "VALIDATOR_EXCEPTION", "message": exc.__class__.__name__}], {},
            )
        )
    if not validations[-1]["passed"]:
        return _finalize_manifest_preflight(validations, registry_version, registry_sha256)

    try:
        requirements = load_and_validate_requirements(root)
        requirements_record = requirements.deterministic_record()
        validations.append(
            _manifest_validation_record(
                "requirements",
                requirements.ok,
                requirements.manifest_sha256,
                requirements.schema_sha256,
                list(requirements.issues),
                {
                    "requirement_count": requirements_record["requirement_count"],
                    "planned_case_count": requirements_record["planned_case_count"],
                    "test_obligation_count": requirements_record["test_obligation_count"],
                },
            )
        )
    except Exception as exc:  # noqa: BLE001
        validations.append(
            _manifest_validation_record(
                "requirements",
                False,
                _current_hash_or_none(root, MANIFEST_PATHS["requirements"][0]),
                _current_hash_or_none(root, MANIFEST_PATHS["requirements"][1]),
                [{"code": "VALIDATOR_EXCEPTION", "message": exc.__class__.__name__}], {},
            )
        )
    if not validations[-1]["passed"]:
        return _finalize_manifest_preflight(validations, registry_version, registry_sha256)

    try:
        cases = load_and_validate_v04_manifest(root, verify_fixture_hashes=True)
        case_record = cases.deterministic_record()
        validations.append(
            _manifest_validation_record(
                "v0.4-test-cases",
                cases.ok,
                cases.manifest_sha256,
                cases.schema_sha256,
                [issue.as_dict() for issue in cases.issues],
                {
                    "case_count": case_record["case_count"],
                    "status_counts": case_record["business_status_counts"],
                    "fixture_count": len(case_record["fixtures"]),
                },
            )
        )
    except Exception as exc:  # noqa: BLE001
        validations.append(
            _manifest_validation_record(
                "v0.4-test-cases",
                False,
                _current_hash_or_none(root, MANIFEST_PATHS["v0.4-test-cases"][0]),
                _current_hash_or_none(root, MANIFEST_PATHS["v0.4-test-cases"][1]),
                [{"code": "VALIDATOR_EXCEPTION", "message": exc.__class__.__name__}], {},
            )
        )
    if not validations[-1]["passed"]:
        return _finalize_manifest_preflight(validations, registry_version, registry_sha256)

    try:
        registry = load_and_validate_registry(root)
        registry_version = registry.contract_version
        registry_sha256 = registry.registry_sha256
        issues = [
            {"code": issue.code, "message": issue.message}
            for issue in registry.issues
        ]
        expected_context_version = context.get("contract_version")
        expected_context_hash = context.get("registry_sha256")
        if registry_version != EXPECTED_CONTRACT_VERSION:
            issues.append(
                {
                    "code": "CONTRACT_VERSION",
                    "message": (
                        f"expected {EXPECTED_CONTRACT_VERSION}; actual {registry_version}"
                    ),
                }
            )
        if expected_context_version is not None and expected_context_version != registry_version:
            issues.append(
                {
                    "code": "CONTEXT_CONTRACT_VERSION",
                    "message": "dispatcher contract version differs from registry",
                }
            )
        if expected_context_hash is not None and expected_context_hash != registry_sha256:
            issues.append(
                {
                    "code": "CONTEXT_REGISTRY_HASH",
                    "message": "dispatcher registry hash differs from current bytes",
                }
            )
        suite_count = (
            len(registry.registry.get("suites", []))
            if isinstance(registry.registry, dict)
            else 0
        )
        validations.append(
            _manifest_validation_record(
                "validation-suites",
                registry.ok and not issues,
                registry.registry_sha256,
                _sha256_file(root / MANIFEST_PATHS["validation-suites"][1]),
                issues,
                {
                    "contract_version": registry.contract_version,
                    "suite_count": suite_count,
                },
            )
        )
    except Exception as exc:  # noqa: BLE001
        validations.append(
            _manifest_validation_record(
                "validation-suites",
                False,
                _current_hash_or_none(root, MANIFEST_PATHS["validation-suites"][0]),
                _current_hash_or_none(root, MANIFEST_PATHS["validation-suites"][1]),
                [{"code": "VALIDATOR_EXCEPTION", "message": exc.__class__.__name__}], {},
            )
        )
    return _finalize_manifest_preflight(validations, registry_version, registry_sha256)


def _finalize_manifest_preflight(
    validations: list[dict[str, Any]],
    registry_version: str | None,
    registry_sha256: str | None,
) -> dict[str, Any]:
    passed = all(item["passed"] for item in validations) and len(validations) == len(MANIFEST_ORDER)
    executed = len(validations)
    return {
        "schema": "dssc.governance.manifest-preflight.v1",
        "program_status": "SUCCESS" if passed else "ERROR",
        "validation_order": list(MANIFEST_ORDER),
        "counts": {
            "discovered": len(MANIFEST_ORDER),
            "executed": executed,
            "passed": sum(1 for item in validations if item["passed"]),
            "failed": sum(1 for item in validations if not item["passed"]),
            "skipped": len(MANIFEST_ORDER) - executed,
        },
        "registry_contract_version": registry_version,
        "registry_sha256": registry_sha256,
        "validations": validations,
    }


def _preflight_ok(preflight: Mapping[str, Any]) -> bool:
    counts = preflight.get("counts")
    return (
        preflight.get("program_status") == "SUCCESS"
        and isinstance(counts, Mapping)
        and counts.get("discovered") == len(MANIFEST_ORDER)
        and counts.get("executed") == len(MANIFEST_ORDER)
        and counts.get("passed") == len(MANIFEST_ORDER)
        and counts.get("failed") == 0
        and counts.get("skipped") == 0
        and preflight.get("registry_contract_version") == EXPECTED_CONTRACT_VERSION
        and isinstance(preflight.get("registry_sha256"), str)
        and bool(SHA256_PATTERN.fullmatch(str(preflight.get("registry_sha256"))))
    )


def _read_governance_documents(root: Path) -> tuple[dict[str, str], list[str]]:
    documents: dict[str, str] = {}
    issues: list[str] = []
    for name in EXPECTED_FILES:
        relpath = f"{GOVERNANCE_RELPATH}/{name}"
        path, issue = _safe_repo_path(root, relpath)
        if issue is not None or path is None:
            issues.append(f"{name}: {issue}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(f"{name}: cannot read UTF-8 ({exc.__class__.__name__})")
            continue
        if not text.strip():
            issues.append(f"{name}: file is empty")
            continue
        documents[name] = text
    return documents, sorted(issues)


def _document_checks(documents: Mapping[str, str], file_issues: list[str]) -> list[Check]:
    checks: list[Check] = []
    missing = sorted(set(EXPECTED_FILES) - set(documents))
    checks.append(
        _check(
            "files.required",
            not missing and not file_issues,
            "all seven governance/provenance files are regular, non-empty UTF-8 files",
            missing=missing,
            issues=file_issues,
        )
    )
    for name in EXPECTED_FILES[:-1]:
        text = documents.get(name, "")
        lines = text.splitlines()
        headings = REQUIRED_HEADINGS[name]
        tokens = REQUIRED_TOKENS[name]
        missing_headings = [
            item
            for item in headings
            if sum(
                line.rstrip() == item or line.rstrip().startswith(item + " ")
                for line in lines
            )
            != 1
        ]
        missing_tokens = [item for item in tokens if item not in text]
        checks.append(
            _check(
                f"content.{name.removesuffix('.md')}",
                not missing_headings and not missing_tokens,
                f"{name} contains the cumulative v0.1-v0.4 governance contract",
                missing_or_duplicate_headings=missing_headings,
                missing_tokens=missing_tokens,
            )
        )

    changelog = documents.get("changelog.md", "")
    positions = [changelog.find(f"## {version}") for version in ("v0.4", "v0.3", "v0.2", "v0.1")]
    checks.append(
        _check(
            "history.version-order",
            all(position >= 0 for position in positions) and positions == sorted(positions),
            "changelog retains v0.1-v0.3 and places v0.4 first",
            positions=positions,
        )
    )
    return checks


def _node_ids(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    return set()


def _node_types(node: Mapping[str, Any]) -> set[str]:
    value = node.get("@type")
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    return set()


def _manifest_hash_map(preflight: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in preflight.get("validations", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _provenance_checks(
    root: Path,
    provenance: Any,
    release_manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    external_evidence_overrides: Mapping[str, str] | None = None,
) -> list[Check]:
    checks: list[Check] = []
    try:
        from pyld import jsonld

        expanded = jsonld.expand(provenance)
        expansion_issue = None
    except Exception as exc:  # noqa: BLE001 - parser errors are evidence
        expanded = []
        expansion_issue = exc.__class__.__name__
    checks.append(
        _check(
            "provenance.jsonld-parse",
            expansion_issue is None and bool(expanded),
            "provenance JSON-LD parses and expands offline",
            expanded_node_count=len(expanded),
            issue=expansion_issue,
        )
    )

    graph = provenance.get("@graph") if isinstance(provenance, dict) else None
    nodes = [item for item in graph if isinstance(item, dict)] if isinstance(graph, list) else []
    ids = [item.get("@id") for item in nodes if isinstance(item.get("@id"), str)]
    duplicate_ids = sorted({item for item in ids if ids.count(item) > 1})
    by_id = {item["@id"]: item for item in nodes if isinstance(item.get("@id"), str)}
    required_ids = {
        AGENT_C,
        AGENT_D,
        V01,
        V02,
        V03,
        V04,
        HISTORICAL_ACTIVITY,
        *HISTORICAL_REPORT_IDS,
        D_SHAPE,
        D_NOTE,
        DERIVATION,
        RECORD_CONTRACT,
        VALIDATION_ACTIVITY,
        VALIDATION_ARTIFACT,
        *EXTERNAL_STATUS_EXPECTATIONS,
    }
    missing_ids = sorted(required_ids - set(by_id))
    expected_types = {
        AGENT_C: "Agent",
        AGENT_D: "Agent",
        V01: "Entity",
        V02: "Entity",
        V03: "Entity",
        V04: "Entity",
        HISTORICAL_ACTIVITY: "Activity",
        **{node_id: "Entity" for node_id in HISTORICAL_REPORT_IDS},
        D_SHAPE: "Entity",
        D_NOTE: "Entity",
        DERIVATION: "Activity",
        RECORD_CONTRACT: "Entity",
        VALIDATION_ACTIVITY: "Activity",
        VALIDATION_ARTIFACT: "Entity",
        **{node_id: "Activity" for node_id in EXTERNAL_STATUS_EXPECTATIONS},
    }
    type_issues = sorted(
        f"{node_id}: expected {expected_type}"
        for node_id, expected_type in expected_types.items()
        if node_id in by_id and expected_type not in _node_types(by_id[node_id])
    )
    checks.append(
        _check(
            "provenance.required-entities",
            not duplicate_ids and not missing_ids and not type_issues,
            "required agents, versions, sources, activities, contracts, and evidence entities exist",
            duplicate_ids=duplicate_ids,
            missing_ids=missing_ids,
            type_issues=type_issues,
        )
    )

    relationship_issues: list[str] = []
    historical = by_id.get(HISTORICAL_ACTIVITY, {})
    v04 = by_id.get(V04, {})
    derivation = by_id.get(DERIVATION, {})
    validation_activity = by_id.get(VALIDATION_ACTIVITY, {})
    artifact = by_id.get(VALIDATION_ARTIFACT, {})
    if _node_ids(by_id.get(V01, {}).get("wasGeneratedBy")) != {HISTORICAL_ACTIVITY}:
        relationship_issues.append("v0.1 historical generator relation is missing")
    if _node_ids(by_id.get(V02, {}).get("wasDerivedFrom")) != {V01}:
        relationship_issues.append("v0.2 must remain derived from v0.1")
    if _node_ids(by_id.get(V03, {}).get("wasDerivedFrom")) != {V02}:
        relationship_issues.append("v0.3 must remain derived from v0.2")
    if _node_ids(historical.get("wasAssociatedWith")) != {AGENT_C}:
        relationship_issues.append("historical generation must remain associated with C Group")
    for report_id in HISTORICAL_REPORT_IDS:
        if _node_ids(by_id.get(report_id, {}).get("wasGeneratedBy")) != {HISTORICAL_ACTIVITY}:
            relationship_issues.append(f"historical report generator missing: {report_id}")
    if _node_ids(v04.get("wasGeneratedBy")) != {DERIVATION}:
        relationship_issues.append("v0.4 must have the C-group derivation activity as generator")
    if not {V03, D_SHAPE}.issubset(_node_ids(v04.get("wasDerivedFrom"))):
        relationship_issues.append("v0.4 derivation must include v0.3 and the D Shape")
    if _node_ids(v04.get("wasAttributedTo")) != {AGENT_C}:
        relationship_issues.append("v0.4 must be attributed to C Group")
    if not {V03, D_SHAPE, D_NOTE}.issubset(_node_ids(derivation.get("used"))):
        relationship_issues.append("C derivation must use v0.3 and both D source entities")
    if _node_ids(derivation.get("wasAssociatedWith")) != {AGENT_C}:
        relationship_issues.append("C derivation must be associated with C Group")
    if _node_ids(artifact.get("wasGeneratedBy")) != {VALIDATION_ACTIVITY}:
        relationship_issues.append("manifest preflight artifact must link to validation activity")
    expected_manifest_ids = {
        f"https://w3id.org/dssc-demo/building-energy/manifest/{manifest_id}"
        for manifest_id in MANIFEST_ORDER
    }
    if _node_ids(validation_activity.get("used")) != expected_manifest_ids:
        relationship_issues.append("validation activity must use exactly the five consumed manifests")
    if _node_ids(validation_activity.get("generated")) != {VALIDATION_ARTIFACT}:
        relationship_issues.append("validation activity must generate the preflight artifact")
    checks.append(
        _check(
            "provenance.relations",
            not relationship_issues,
            "PROV generation, derivation, use, attribution, and association relations are complete",
            issues=relationship_issues,
        )
    )

    source_catalog = {
        item.get("id"): item
        for item in release_manifest.get("sourceCatalog", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    artifact_catalog = {
        item.get("id"): item
        for release in release_manifest.get("releases", [])
        if isinstance(release, dict)
        for item in release.get("artifacts", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    binding_issues: list[str] = []
    actual_hash_issues: list[str] = []
    for node in nodes:
        path_value = node.get("path")
        sha_value = node.get("sha256")
        source_ref = node.get("sourceRef")
        artifact_ref = node.get("releaseArtifactRef")
        if source_ref is not None:
            source = source_catalog.get(source_ref)
            if source is None or path_value != source.get("path") or sha_value != source.get("sha256"):
                binding_issues.append(f"{node.get('@id')}: source binding differs from release manifest")
        if artifact_ref is not None:
            release_artifact = artifact_catalog.get(artifact_ref)
            if (
                release_artifact is None
                or path_value != release_artifact.get("path")
                or sha_value != release_artifact.get("sha256")
            ):
                binding_issues.append(f"{node.get('@id')}: artifact binding differs from release manifest")
        if path_value is not None or sha_value is not None:
            if not isinstance(sha_value, str) or not SHA256_PATTERN.fullmatch(sha_value):
                actual_hash_issues.append(f"{node.get('@id')}: invalid SHA-256")
                continue
            path, issue = _safe_repo_path(root, path_value)
            if issue is not None or path is None:
                actual_hash_issues.append(f"{node.get('@id')}: {issue}")
            elif _sha256_file(path) != sha_value:
                actual_hash_issues.append(f"{node.get('@id')}: file bytes do not match SHA-256")
    checks.append(
        _check(
            "provenance.bindings",
            not binding_issues and not actual_hash_issues,
            "source/artifact paths and hashes match the release manifest and repository bytes",
            manifest_binding_issues=sorted(binding_issues),
            byte_freshness_issues=sorted(actual_hash_issues),
        )
    )

    d_source_issues: list[str] = []
    for node_id, source_ref in ((D_SHAPE, "d-shape-v04"), (D_NOTE, "d-change-note")):
        node = by_id.get(node_id, {})
        if node.get("sourceRef") != source_ref:
            d_source_issues.append(f"{node_id}: sourceRef mismatch")
        if _node_ids(node.get("wasAttributedTo")) != {AGENT_D}:
            d_source_issues.append(f"{node_id}: D Group attribution missing")
    checks.append(
        _check(
            "provenance.d-group-sources",
            not d_source_issues,
            "normative and explanatory D-group source entities are explicit",
            issues=d_source_issues,
        )
    )

    release_v04 = next(
        (item for item in release_manifest.get("releases", []) if isinstance(item, dict) and item.get("id") == "v0.4"),
        {},
    )
    compatibility_issues: list[str] = []
    if v04.get("compatibility") != release_v04.get("compatibilityClassification"):
        compatibility_issues.append("v0.4 compatibility classification differs from release manifest")
    if v04.get("priorVersion") != V03:
        compatibility_issues.append("v0.4 priorVersion must be v0.3")
    if _node_ids(v04.get("inherits")) != {RECORD_CONTRACT}:
        compatibility_issues.append("v0.4 must inherit the v0.3 record contract")
    record = by_id.get(RECORD_CONTRACT, {})
    if record.get("change") != "none" or _node_ids(record.get("wasDerivedFrom")) != {V03}:
        compatibility_issues.append("record contract must be unchanged and derived from v0.3")
    inherited = {
        item.get("id"): item
        for item in release_v04.get("artifacts", [])
        if isinstance(item, dict)
        and isinstance(item.get("origin"), dict)
        and item["origin"].get("type") == "inherited"
    }
    member_ids = _node_ids(record.get("hadMember"))
    member_refs = {
        by_id.get(member_id, {}).get("releaseArtifactRef")
        for member_id in member_ids
    }
    if member_refs != set(inherited):
        compatibility_issues.append("record contract members differ from exact v0.4 inheritance set")
    if len(member_ids) != 5:
        compatibility_issues.append("record inheritance must contain exactly five entities")
    checks.append(
        _check(
            "provenance.compatibility",
            not compatibility_issues,
            "v0.3 derivation, wire-profile compatibility, and five unchanged record artifacts are exact",
            issues=compatibility_issues,
            inherited_artifact_ids=sorted(inherited),
        )
    )

    preflight_by_id = _manifest_hash_map(preflight)
    manifest_issues: list[str] = []
    for manifest_id in MANIFEST_ORDER:
        node_id = f"https://w3id.org/dssc-demo/building-energy/manifest/{manifest_id}"
        node = by_id.get(node_id, {})
        expected = preflight_by_id.get(manifest_id, {})
        if node.get("path") != expected.get("manifest_path"):
            manifest_issues.append(f"{manifest_id}: path mismatch")
        if node.get("sha256") != expected.get("manifest_sha256"):
            manifest_issues.append(f"{manifest_id}: hash mismatch")
    checks.append(
        _check(
            "provenance.manifest-usage",
            not manifest_issues,
            "validation activity manifest entities match the current preflight",
            issues=manifest_issues,
        )
    )

    validation_issues: list[str] = []
    if artifact.get("path") != PREFLIGHT_RELPATH:
        validation_issues.append("validation artifact path is not the fixed manifest-preflight path")
    preflight_path, preflight_path_issue = _safe_repo_path(root, PREFLIGHT_RELPATH)
    if preflight_path_issue is not None or preflight_path is None:
        validation_issues.append(f"manifest preflight unavailable: {preflight_path_issue}")
    else:
        actual_preflight_hash = _sha256_file(preflight_path)
        if artifact.get("sha256") != actual_preflight_hash:
            validation_issues.append("validation artifact SHA-256 is stale")
        try:
            actual_preflight = _load_json_text(preflight_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            validation_issues.append(f"manifest preflight cannot be parsed: {exc.__class__.__name__}")
        else:
            if actual_preflight != preflight or not _preflight_ok(actual_preflight):
                validation_issues.append("manifest preflight content is not the current successful preflight")
    checks.append(
        _check(
            "provenance.validation-artifact",
            not validation_issues,
            "the recorded validation artifact exists, is successful, and is byte-current",
            issues=validation_issues,
        )
    )

    external_status_issues: list[str] = []
    forbidden_dynamic_fields = {
        "generated",
        "generatedAtTime",
        "startedAtTime",
        "endedAtTime",
        "outcome",
        "evidenceUrl",
        "runUrl",
    }
    for node_id, expectation in sorted(EXTERNAL_STATUS_EXPECTATIONS.items()):
        activity_kind = expectation["kind"]
        node = by_id.get(node_id, {})
        if "Activity" not in _node_types(node):
            external_status_issues.append(f"{activity_kind}: must be an Activity")
        if node.get("activityKind") != activity_kind:
            external_status_issues.append(
                f"{activity_kind}: activityKind must equal {activity_kind!r}"
            )
        if node.get("status") != expectation["status"]:
            external_status_issues.append(
                f"{activity_kind}: status must equal {expectation['status']!r}"
            )
        if node.get("evidenceRef") != expectation["evidence_ref"]:
            external_status_issues.append(
                f"{activity_kind}: evidenceRef must equal {expectation['evidence_ref']!r}"
            )
        evidence_ref = expectation["evidence_ref"]
        evidence_text: str | None = None
        if external_evidence_overrides is not None and evidence_ref in external_evidence_overrides:
            evidence_text = external_evidence_overrides[evidence_ref]
        else:
            evidence_path, evidence_issue = _safe_repo_path(root, evidence_ref)
            if evidence_issue is not None or evidence_path is None:
                external_status_issues.append(
                    f"{activity_kind}: evidenceRef target is invalid: {evidence_issue}"
                )
            elif evidence_path.stat().st_size == 0:
                external_status_issues.append(
                    f"{activity_kind}: evidenceRef target must be non-empty"
                )
            else:
                try:
                    evidence_text = evidence_path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    external_status_issues.append(
                        f"{activity_kind}: evidenceRef target is not readable UTF-8: {exc.__class__.__name__}"
                    )
        if evidence_text is not None:
            if not evidence_text.strip():
                external_status_issues.append(
                    f"{activity_kind}: evidenceRef content must be non-empty"
                )
            missing_tokens = sorted(
                token
                for token in expectation["evidence_tokens"]
                if token not in evidence_text
            )
            if missing_tokens:
                external_status_issues.append(
                    f"{activity_kind}: evidenceRef is missing required support tokens {missing_tokens}"
                )
        description = node.get("description")
        if not isinstance(description, str) or not description.strip():
            external_status_issues.append(f"{activity_kind}: description must be non-empty")
        if node.get("wasAssociatedWith") != AGENT_C:
            external_status_issues.append(
                f"{activity_kind}: wasAssociatedWith must equal {AGENT_C!r}"
            )
        populated = sorted(field for field in forbidden_dynamic_fields if field in node)
        if populated:
            external_status_issues.append(
                f"{activity_kind}: dynamic/self-referential fields are forbidden {populated}"
            )
    checks.append(
        _check(
            "provenance.external-status-truth",
            not external_status_issues,
            "release responsibility, CI, GitHub publication, and optional Treehouse status match current stable evidence boundaries",
            issues=external_status_issues,
        )
    )
    return checks


def _evaluate_documents(
    root: Path,
    documents: Mapping[str, str],
    file_issues: list[str],
    release_manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    external_evidence_overrides: Mapping[str, str] | None = None,
) -> tuple[list[Check], Any | None, str | None]:
    checks = _document_checks(documents, file_issues)
    provenance_text = documents.get("provenance.jsonld", "")
    try:
        provenance = _load_json_text(provenance_text)
        parse_code = None
    except DuplicateJsonKey:
        provenance = None
        parse_code = "DUPLICATE_JSON_KEY"
    except (json.JSONDecodeError, UnicodeError, TypeError):
        provenance = None
        parse_code = "JSON_PARSE"
    checks.append(
        _check(
            "provenance.strict-json",
            parse_code is None and isinstance(provenance, dict),
            "provenance uses strict JSON object syntax with unique keys",
            issue_code=parse_code,
        )
    )
    if isinstance(provenance, dict):
        checks.extend(
            _provenance_checks(
                root,
                provenance,
                release_manifest,
                preflight,
                external_evidence_overrides,
            )
        )
    else:
        for check_id, message in (
            ("provenance.jsonld-parse", "provenance JSON-LD cannot be parsed"),
            ("provenance.required-entities", "required entities cannot be inspected"),
            ("provenance.relations", "required relations cannot be inspected"),
            ("provenance.bindings", "source/hash bindings cannot be inspected"),
            ("provenance.d-group-sources", "D source entities cannot be inspected"),
            ("provenance.compatibility", "compatibility cannot be inspected"),
            ("provenance.manifest-usage", "manifest usage cannot be inspected"),
            ("provenance.validation-artifact", "validation artifact cannot be inspected"),
            ("provenance.external-status-truth", "external status truth cannot be inspected"),
        ):
            checks.append(_check(check_id, False, message, issue_code=parse_code))
    return checks, provenance, parse_code


def _governance_hashes(root: Path) -> tuple[dict[str, str], list[str]]:
    hashes: dict[str, str] = {}
    issues: list[str] = []
    for name in EXPECTED_FILES:
        relpath = f"{GOVERNANCE_RELPATH}/{name}"
        path, issue = _safe_repo_path(root, relpath)
        if issue is not None or path is None:
            issues.append(f"{relpath}: {issue}")
        else:
            hashes[relpath] = _sha256_file(path)
    return dict(sorted(hashes.items())), sorted(issues)


def _source_hashes(
    root: Path,
    required_paths: tuple[str, ...] = REQUIRED_SOURCE_PATHS,
) -> tuple[dict[str, str], list[str]]:
    hashes: dict[str, str] = {}
    issues: list[str] = []
    for relpath in required_paths:
        path, issue = _safe_repo_path(root, relpath)
        if issue is not None or path is None:
            issues.append(f"{relpath}: {issue}")
        else:
            hashes[relpath] = _sha256_file(path)
    return dict(sorted(hashes.items())), sorted(issues)


def _phase06_contract_hashes(root: Path) -> tuple[dict[str, str], list[str]]:
    hashes: dict[str, str] = {}
    issues: list[str] = []
    for relpath in (SPARQL_MANIFEST_RELPATH, SPARQL_SCHEMA_RELPATH, LOCK_RELPATH):
        path, issue = _safe_repo_path(root, relpath)
        if issue is not None or path is None:
            issues.append(f"{relpath}: {issue}")
        else:
            hashes[relpath] = _sha256_file(path)
    return dict(sorted(hashes.items())), sorted(issues)


def _load_release_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_PATHS["release"][0]
    value = _load_json_text(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("release manifest root must be an object")
    return value


def _core_result(
    root: Path,
    preflight: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    documents, file_issues = _read_governance_documents(root)
    release_manifest = _load_release_manifest(root)
    checks, _provenance, _parse_code = _evaluate_documents(
        root, documents, file_issues, release_manifest, preflight
    )
    governance_hashes, governance_hash_issues = _governance_hashes(root)
    source_hashes, source_hash_issues = _source_hashes(root)
    phase06_contract_hashes, phase06_contract_issues = _phase06_contract_hashes(root)
    checks.append(
        _check(
            "freshness.governance-files",
            not governance_hash_issues and len(governance_hashes) == len(EXPECTED_FILES),
            "all governance input bytes are hashed from fixed paths",
            issues=governance_hash_issues,
            hash_count=len(governance_hashes),
        )
    )
    checks.append(
        _check(
            "freshness.loaded-sources",
            not source_hash_issues and len(source_hashes) == len(REQUIRED_SOURCE_PATHS),
            "dispatcher, adapter, checker, reporter, and manifest helper sources are hash-bound",
            issues=source_hash_issues,
            hash_count=len(source_hashes),
        )
    )
    checks.append(
        _check(
            "freshness.phase06-contracts",
            not phase06_contract_issues and len(phase06_contract_hashes) == 3,
            "SPARQL manifest/schema and dependency lock bytes are hash-bound",
            issues=phase06_contract_issues,
            hash_count=len(phase06_contract_hashes),
        )
    )
    checks.sort(key=lambda item: item.id)
    passed_count = sum(1 for item in checks if item.passed)
    successful = passed_count == len(checks) and _preflight_ok(preflight)
    manifest_hashes = {
        item["manifest_path"]: item["manifest_sha256"]
        for item in preflight.get("validations", [])
        if isinstance(item, dict) and isinstance(item.get("manifest_sha256"), str)
    }
    schema_hashes = {
        item["schema_path"]: item["schema_sha256"]
        for item in preflight.get("validations", [])
        if isinstance(item, dict) and isinstance(item.get("schema_sha256"), str)
    }
    result = {
        "schema": "dssc.governance.result.v1",
        "suite": "governance",
        "program_status": "SUCCESS" if successful else "ERROR",
        "message": (
            "governance and provenance validation passed"
            if successful
            else "governance and provenance validation failed"
        ),
        "counts": {
            "discovered": len(checks),
            "executed": len(checks),
            "passed": passed_count,
            "failed": len(checks) - passed_count,
            "skipped": 0,
        },
        "checks": [item.as_dict() for item in checks],
        "manifest_preflight": dict(preflight),
        "manifest_hashes": dict(sorted(manifest_hashes.items())),
        "schema_hashes": dict(sorted(schema_hashes.items())),
        "registry_contract_version": preflight.get("registry_contract_version"),
        "registry_sha256": preflight.get("registry_sha256"),
        "phase06_contract_hashes": phase06_contract_hashes,
        "requirements_lock_sha256": phase06_contract_hashes.get(LOCK_RELPATH),
        "governance_hashes": governance_hashes,
        "source_hashes": source_hashes,
        "source_hash_issues": source_hash_issues,
    }
    return result, documents


def _check_failed(checks: list[Check], check_id: str) -> bool:
    return any(item.id == check_id and not item.passed for item in checks)


def _negative_controls(
    root: Path,
    canonical_documents: Mapping[str, str],
    release_manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    provenance = _load_json_text(canonical_documents["provenance.jsonld"])
    controls: list[dict[str, Any]] = []

    def add(control_id: str, expected: str, actual: bool) -> None:
        controls.append(
            {
                "id": control_id,
                "passed": bool(actual),
                "expected_failure": expected,
            }
        )

    missing_docs = dict(canonical_documents)
    missing_docs.pop("model-card.md", None)
    checks, _, _ = _evaluate_documents(root, missing_docs, [], release_manifest, preflight)
    add("file.missing", "files.required", _check_failed(checks, "files.required"))

    stale_changelog = dict(canonical_documents)
    stale_changelog["changelog.md"] = stale_changelog["changelog.md"].replace("## v0.4", "## removed-v0.4", 1)
    checks, _, _ = _evaluate_documents(root, stale_changelog, [], release_manifest, preflight)
    add("content.v0.4-missing", "content.changelog", _check_failed(checks, "content.changelog"))

    missing_relation = copy.deepcopy(provenance)
    for node in missing_relation["@graph"]:
        if node.get("@id") == V04:
            node.pop("wasGeneratedBy", None)
    docs = dict(canonical_documents)
    docs["provenance.jsonld"] = _json_bytes(missing_relation).decode("utf-8")
    checks, _, _ = _evaluate_documents(root, docs, [], release_manifest, preflight)
    add("provenance.missing-relation", "provenance.relations", _check_failed(checks, "provenance.relations"))

    missing_entity = copy.deepcopy(provenance)
    missing_entity["@graph"] = [
        node for node in missing_entity["@graph"] if node.get("@id") != D_NOTE
    ]
    docs["provenance.jsonld"] = _json_bytes(missing_entity).decode("utf-8")
    checks, _, _ = _evaluate_documents(root, docs, [], release_manifest, preflight)
    add(
        "provenance.missing-entity",
        "provenance.required-entities",
        _check_failed(checks, "provenance.required-entities"),
    )

    tampered_source = copy.deepcopy(provenance)
    for node in tampered_source["@graph"]:
        if node.get("@id") == D_SHAPE:
            node["sha256"] = "0" * 64
    docs["provenance.jsonld"] = _json_bytes(tampered_source).decode("utf-8")
    checks, _, _ = _evaluate_documents(root, docs, [], release_manifest, preflight)
    add("provenance.source-hash", "provenance.bindings", _check_failed(checks, "provenance.bindings"))

    stale_artifact = copy.deepcopy(provenance)
    for node in stale_artifact["@graph"]:
        if node.get("@id") == VALIDATION_ARTIFACT:
            node["sha256"] = "f" * 64
    docs["provenance.jsonld"] = _json_bytes(stale_artifact).decode("utf-8")
    checks, _, _ = _evaluate_documents(root, docs, [], release_manifest, preflight)
    add(
        "provenance.validation-artifact-stale",
        "provenance.validation-artifact",
        _check_failed(checks, "provenance.validation-artifact"),
    )

    for node_id, expectation in sorted(EXTERNAL_STATUS_EXPECTATIONS.items()):
        false_status = copy.deepcopy(provenance)
        for node in false_status["@graph"]:
            if node.get("@id") == node_id:
                node["status"] = "completed-without-bound-evidence"
                break
        docs["provenance.jsonld"] = _json_bytes(false_status).decode("utf-8")
        checks, _, _ = _evaluate_documents(root, docs, [], release_manifest, preflight)
        add(
            f"provenance.external-status.{expectation['kind']}",
            "provenance.external-status-truth",
            _check_failed(checks, "provenance.external-status-truth"),
        )

    external_mutations = (
        ("missing-evidence-ref", "evidenceRef", None),
        ("wrong-activity-kind", "activityKind", "wrong-kind"),
        ("wrong-agent", "wasAssociatedWith", AGENT_D),
        ("empty-description", "description", ""),
        ("forbidden-run-url", "runUrl", "https://example.invalid/run/1"),
    )
    external_node_id = "https://w3id.org/dssc-demo/building-energy/activity/v0.4-ci-validation"
    for control_suffix, field, value in external_mutations:
        mutated = copy.deepcopy(provenance)
        for node in mutated["@graph"]:
            if node.get("@id") == external_node_id:
                if value is None:
                    node.pop(field, None)
                else:
                    node[field] = value
                break
        docs["provenance.jsonld"] = _json_bytes(mutated).decode("utf-8")
        checks, _, _ = _evaluate_documents(root, docs, [], release_manifest, preflight)
        add(
            f"provenance.external-status.{control_suffix}",
            "provenance.external-status-truth",
            _check_failed(checks, "provenance.external-status-truth"),
        )

    docs["provenance.jsonld"] = canonical_documents["provenance.jsonld"]
    release_evidence_ref = EXTERNAL_STATUS_EXPECTATIONS[
        "https://w3id.org/dssc-demo/building-energy/activity/v0.4-release-approval"
    ]["evidence_ref"]
    for control_suffix, evidence_text in (
        ("empty-evidence", ""),
        ("unsupported-evidence", "non-empty text without the required decision tokens"),
    ):
        checks, _, _ = _evaluate_documents(
            root,
            docs,
            [],
            release_manifest,
            preflight,
            {release_evidence_ref: evidence_text},
        )
        add(
            f"provenance.external-status.{control_suffix}",
            "provenance.external-status-truth",
            _check_failed(checks, "provenance.external-status-truth"),
        )

    docs["provenance.jsonld"] = "{invalid"
    checks, _, code = _evaluate_documents(root, docs, [], release_manifest, preflight)
    add("provenance.malformed-json", "JSON_PARSE", code == "JSON_PARSE" and _check_failed(checks, "provenance.strict-json"))

    docs["provenance.jsonld"] = '{"@context": {}, "@context": {}, "@graph": []}'
    checks, _, code = _evaluate_documents(root, docs, [], release_manifest, preflight)
    add("provenance.duplicate-json-key", "DUPLICATE_JSON_KEY", code == "DUPLICATE_JSON_KEY" and _check_failed(checks, "provenance.strict-json"))

    failed_preflight = copy.deepcopy(preflight)
    failed_preflight["program_status"] = "ERROR"
    failed_preflight["counts"]["failed"] = 1
    add("manifest-preflight.fail-closed", "preflight gate rejects ERROR", not _preflight_ok(failed_preflight))

    context_mismatch = build_manifest_preflight(
        root,
        {
            "repository_root": root,
            "contract_version": EXPECTED_CONTRACT_VERSION,
            "registry_sha256": "0" * 64,
        },
    )
    add(
        "manifest-preflight.context-hash",
        "existing registry checker rejects dispatcher/hash divergence",
        context_mismatch.get("program_status") == "ERROR"
        and context_mismatch.get("counts", {}).get("failed") == 1,
    )

    _hashes, source_issues = _source_hashes(
        root,
        REQUIRED_SOURCE_PATHS
        + ("C_Semantic_Treehouse/scripts/governance_missing_control.py",),
    )
    add(
        "freshness.source-missing",
        "source freshness rejects a missing required helper",
        any("governance_missing_control.py" in issue for issue in source_issues),
    )

    controls.sort(key=lambda item: item["id"])
    passed = sum(1 for item in controls if item["passed"])
    return {
        "schema": "dssc.governance.negative-controls.v1",
        "program_status": "SUCCESS" if passed == len(controls) and controls else "ERROR",
        "counts": {
            "discovered": len(controls),
            "executed": len(controls),
            "passed": passed,
            "failed": len(controls) - passed,
            "skipped": 0,
        },
        "controls": controls,
    }


def _render_report(result: Mapping[str, Any]) -> str:
    lines = [
        "# Governance and Provenance Validation Report",
        "",
        f"- Program status: `{result.get('program_status')}`",
        f"- Registry contract: `{result.get('registry_contract_version')}`",
        f"- Registry SHA-256: `{result.get('registry_sha256')}`",
        f"- Discovered/executed/passed/failed/skipped: "
        f"`{result.get('counts', {}).get('discovered', 0)}/"
        f"{result.get('counts', {}).get('executed', 0)}/"
        f"{result.get('counts', {}).get('passed', 0)}/"
        f"{result.get('counts', {}).get('failed', 0)}/"
        f"{result.get('counts', {}).get('skipped', 0)}`",
        "",
        "## Manifest preflight",
        "",
        "| Manifest | Result | Manifest SHA-256 | Schema SHA-256 |",
        "|---|---|---|---|",
    ]
    for item in result.get("manifest_preflight", {}).get("validations", []):
        lines.append(
            f"| `{item['id']}` | `{'PASS' if item['passed'] else 'FAIL'}` | "
            f"`{item.get('manifest_sha256')}` | `{item.get('schema_sha256')}` |"
        )
    lines.extend(["", "## Governance checks", ""])
    for item in result.get("checks", []):
        lines.append(
            f"- `{'PASS' if item['passed'] else 'FAIL'}` `{item['id']}` — {item['message']}"
        )
    lines.extend(["", "## Phase 06 contract hashes", ""])
    for path, digest in result.get("phase06_contract_hashes", {}).items():
        lines.append(f"- `{path}` — `{digest}`")
    lines.extend(["", "## Source hashes", ""])
    for path, digest in result.get("source_hashes", {}).items():
        lines.append(f"- `{path}` — `{digest}`")
    negative = result.get("negative_controls", {})
    determinism = result.get("determinism", {})
    lines.extend(
        [
            "",
            "## Fail-closed evidence",
            "",
            f"- Negative controls: `{negative.get('program_status')}` "
            f"({negative.get('counts', {}).get('passed', 0)}/"
            f"{negative.get('counts', {}).get('discovered', 0)})",
            f"- Deterministic rerun: `{'PASS' if determinism.get('byte_identical') else 'FAIL'}`",
            f"- Core result SHA-256: `{determinism.get('run_1_sha256')}`",
            "",
            "Environment-specific metadata is stored separately in "
            "`build/validation/governance/run-environment.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def _environment_record(context: Mapping[str, Any]) -> dict[str, Any]:
    versions: dict[str, str | None] = {}
    for distribution in ("PyLD", "jsonschema"):
        try:
            versions[distribution] = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            versions[distribution] = None
    return {
        "schema": "dssc.governance.environment.v1",
        "profile": context.get("profile", "host"),
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
        },
        "dependency_versions": versions,
    }


def _component_failure(message: str, details: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "program_status": "ERROR",
        "message": message,
        "details": dict(details),
        "machine_details": {},
    }


def _write_failure_evidence(
    root: Path,
    context: Mapping[str, Any],
    preflight: Mapping[str, Any],
    message: str,
) -> None:
    result = {
        "schema": "dssc.governance.result.v1",
        "suite": "governance",
        "program_status": "ERROR",
        "message": message,
        "counts": {
            "discovered": 1,
            "executed": 1,
            "passed": 0,
            "failed": 1,
            "skipped": 0,
        },
        "checks": [
            {
                "id": "manifest.preflight",
                "passed": False,
                "message": message,
                "details": {},
            }
        ],
        "manifest_preflight": dict(preflight),
        "registry_contract_version": preflight.get("registry_contract_version"),
        "registry_sha256": preflight.get("registry_sha256"),
    }
    _write_json(root, RESULT_RELPATH, result)
    _write_text(root, REPORT_RELPATH, _render_report(result))
    _write_json(root, ENVIRONMENT_RELPATH, _environment_record(context))


def run_governance_component(context: dict[str, Any]) -> dict[str, Any]:
    """Execute the five-manifest gate, governance audit, controls, and rerun."""

    root_value = context.get("repository_root")
    if not isinstance(root_value, Path):
        return _component_failure("governance checker requires repository_root", {})
    root = root_value.resolve()

    # This is deliberately the first semantic operation in the component.
    try:
        preflight = build_manifest_preflight(root, context)
        _write_json(root, PREFLIGHT_RELPATH, preflight)
    except Exception as exc:  # noqa: BLE001
        return _component_failure(
            "governance manifest preflight raised and failed closed",
            {"exception_type": exc.__class__.__name__},
        )

    if not _preflight_ok(preflight):
        message = "governance blocked by failed manifest schema/semantic preflight"
        try:
            _write_failure_evidence(root, context, preflight, message)
        except Exception:
            pass
        return _component_failure(
            message,
            {
                "manifest_preflight": PREFLIGHT_RELPATH,
                "counts": preflight.get("counts", {}),
                "validations": preflight.get("validations", []),
            },
        )

    try:
        first, documents = _core_result(root, preflight)
        second, _ = _core_result(root, preflight)
        first_bytes = _json_bytes(first)
        second_bytes = _json_bytes(second)
        determinism = {
            "schema": "dssc.governance.determinism.v1",
            "program_status": (
                "SUCCESS"
                if first.get("program_status") == "SUCCESS"
                and second.get("program_status") == "SUCCESS"
                and first_bytes == second_bytes
                else "ERROR"
            ),
            "comparison_scope": "normalized governance core result; environment excluded",
            "run_1_sha256": _sha256_bytes(first_bytes),
            "run_2_sha256": _sha256_bytes(second_bytes),
            "run_1_size": len(first_bytes),
            "run_2_size": len(second_bytes),
            "byte_identical": first_bytes == second_bytes,
        }
        release_manifest = _load_release_manifest(root)
        negative = _negative_controls(
            root, documents, release_manifest, preflight
        )
        _write_json(root, NEGATIVE_RELPATH, negative)
        _write_json(root, DETERMINISM_RELPATH, determinism)

        successful = (
            first.get("program_status") == "SUCCESS"
            and negative.get("program_status") == "SUCCESS"
            and determinism.get("program_status") == "SUCCESS"
        )
        result = dict(first)
        result["program_status"] = "SUCCESS" if successful else "ERROR"
        result["message"] = (
            "governance and provenance validation passed"
            if successful
            else "governance and provenance validation failed"
        )
        result["negative_controls"] = {
            "program_status": negative["program_status"],
            "counts": negative["counts"],
            "evidence_path": NEGATIVE_RELPATH,
        }
        result["determinism"] = {
            **determinism,
            "evidence_path": DETERMINISM_RELPATH,
        }
        _write_json(root, RESULT_RELPATH, result)
        _write_text(root, REPORT_RELPATH, _render_report(result))
        environment = _environment_record(context)
        environment["result_path"] = RESULT_RELPATH
        environment["result_sha256"] = _sha256_file(root / RESULT_RELPATH)
        _write_json(root, ENVIRONMENT_RELPATH, environment)
    except Exception as exc:  # noqa: BLE001
        message = "governance evaluation raised and failed closed"
        try:
            _write_failure_evidence(root, context, preflight, message)
        except Exception:
            pass
        return _component_failure(message, {"exception_type": exc.__class__.__name__})

    details = {
        "counts": result["counts"],
        "manifest_preflight_counts": preflight["counts"],
        "registry_contract_version": result["registry_contract_version"],
        "registry_sha256": result["registry_sha256"],
        "manifest_hashes": result["manifest_hashes"],
        "schema_hashes": result["schema_hashes"],
        "phase06_contract_hashes": result["phase06_contract_hashes"],
        "requirements_lock_sha256": result["requirements_lock_sha256"],
        "negative_controls": result["negative_controls"],
        "determinism": result["determinism"],
        "evidence_files": [
            RESULT_RELPATH,
            REPORT_RELPATH,
            ENVIRONMENT_RELPATH,
            PREFLIGHT_RELPATH,
            NEGATIVE_RELPATH,
            DETERMINISM_RELPATH,
        ],
    }
    if not successful:
        return _component_failure(result["message"], details)
    return {
        "status": "PASS",
        "program_status": "SUCCESS",
        "message": result["message"],
        "details": details,
        "machine_details": {
            "environment_file": ENVIRONMENT_RELPATH,
        },
    }


__all__ = [
    "build_manifest_preflight",
    "run_governance_component",
]
