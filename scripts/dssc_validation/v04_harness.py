"""Phase 05 four-state fixture harness.

The public entrypoint accepts an already schema/semantic-validated manifest and
the dispatcher context.  It still rechecks all authority, dependency, Shape,
registry and fixture byte bindings before parsing any SUT, then validates each
fixture in a fresh RDF graph.  Expected FAIL/INAPPLICABLE/UNTESTABLE outcomes
are successful test executions only when their complete manifest oracle
matches.
"""

from __future__ import annotations

import copy
import io
import json
import logging
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any, Mapping
from urllib.parse import unquote, urlparse

from dssc_validation.hashing import sha256_file
from dssc_validation.v04_classifier import (
    DATASET_CARDINALITY_SHAPE,
    DATASET_CLOSED_SHAPE,
    SH,
    VALIDATION_SUBMISSION,
    V04ReportError,
    assert_named_shapes,
    build_requirement_bindings,
    collect_target_activation,
    normalize_shacl_report,
)
from dssc_validation.v04_report import (
    V04OracleError,
    assert_case_oracle,
    error_case_result,
)
from dssc_validation.v04_reporter import (
    finalize_v04_result,
    write_v04_evidence,
)


EXPECTED_D_SHAPE_SHA256 = (
    "a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda"
)
EXPECTED_PYSHACL_VERSION = "0.40.1"
TEST_MANIFEST_RELPATH = "C_Semantic_Treehouse/manifests/v0.4-test-cases.json"
TEST_SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/manifests/schemas/v0.4-test-cases.schema.json"
)
RELEASE_MANIFEST_RELPATH = "C_Semantic_Treehouse/manifests/release-manifest.json"
RELEASE_SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json"
)
REQUIREMENTS_RELPATH = "C_Semantic_Treehouse/manifests/v0.4-requirements.json"
REQUIREMENTS_SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/manifests/schemas/v0.4-requirements.schema.json"
)
REGISTRY_RELPATH = "C_Semantic_Treehouse/manifests/validation-suites.json"
REGISTRY_SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json"
)
D_SOURCE_RELPATH = "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl"

MANIFEST_ENGINE_CONFIG: dict[str, Any] = {
    "name": "pySHACL",
    "version": EXPECTED_PYSHACL_VERSION,
    "inference": "none",
    "advanced": True,
    "abort_on_first": False,
    "meta_shacl": True,
    "allow_warnings": False,
    "allow_infos": False,
    "do_owl_imports": False,
}

PYSHACL_KWARGS: dict[str, Any] = {
    "inference": "none",
    "advanced": True,
    "abort_on_first": False,
    "meta_shacl": True,
    "allow_warnings": False,
    "allow_infos": False,
    "do_owl_imports": False,
    "inplace": False,
    "debug": False,
    "iterate_rules": False,
    "sparql_mode": False,
}

# These six combinations are the only expected inability-to-test outcomes.
# Authority, manifest, harness, dependency and unexpected validator failures
# intentionally have no entry here and therefore remain program ERROR.
UNTESTABLE_ALLOWLIST: dict[str, tuple[str, str]] = {
    "D04-PC061": ("INPUT_PARSE", "MALFORMED_JSON"),
    "D04-PC062": ("OFFLINE_LOAD", "JSONLD_EXPANSION_ERROR"),
    "D04-PC063": ("OFFLINE_LOAD", "OFFLINE_CONTEXT_UNAVAILABLE"),
    "D04-PC064": ("VALIDATOR_EXECUTION", "VALIDATOR_TIMEOUT"),
    "D04-PC065": ("VALIDATOR_EXECUTION", "VALIDATOR_CRASH"),
    "D04-PC066": (
        "VALIDATOR_EXECUTION",
        "VALIDATION_SERVICE_RUNTIME_EXCEPTION",
    ),
}
CONTROLLED_FAULT_CASES = frozenset({"D04-PC064", "D04-PC065", "D04-PC066"})
EXPECTED_CASE_IDS = tuple(f"D04-PC{number:03d}" for number in range(1, 67))


class V04HarnessError(RuntimeError):
    """Unexpected authority, dependency or orchestration failure."""

    def __init__(self, code: str, message: str, stage: str = "HARNESS"):
        super().__init__(message)
        self.code = code
        self.message = message
        self.stage = stage

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "stage": self.stage, "message": self.message}


class _ObservedSUTFailure(RuntimeError):
    def __init__(self, stage: str, reason_code: str):
        super().__init__(reason_code)
        self.stage = stage
        self.reason_code = reason_code


class _ControlledValidatorFault(_ObservedSUTFailure):
    pass


@dataclass
class _Preflight:
    root: Path
    manifest: dict[str, Any]
    requirements: dict[str, Any]
    release_manifest: dict[str, Any]
    registry: dict[str, Any]
    shapes_graph: Any
    bindings: dict[str, Any]
    authority_record: dict[str, Any]
    consumed_manifest_hashes: dict[str, str]
    fixture_hashes: dict[str, str]
    input_hashes: dict[str, str]


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise V04HarnessError(
            "AUTHORITY_JSON_PARSE", f"{label} cannot be parsed", "AUTHORITY_PREFLIGHT"
        ) from exc
    if not isinstance(value, dict):
        raise V04HarnessError(
            "AUTHORITY_JSON_TYPE", f"{label} root must be an object", "AUTHORITY_PREFLIGHT"
        )
    return value


def _safe_path(root: Path, relpath: Any, *, must_exist: bool = True) -> Path:
    if not isinstance(relpath, str) or not relpath or "\\" in relpath:
        raise V04HarnessError("UNSAFE_PATH", "repository path must be non-empty POSIX text")
    pure = PurePosixPath(relpath)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise V04HarnessError("UNSAFE_PATH", f"unsafe repository path: {relpath}")
    candidate = root.joinpath(*pure.parts)
    try:
        candidate.resolve().relative_to(root.resolve())
    except (OSError, ValueError) as exc:
        raise V04HarnessError("UNSAFE_PATH", f"path escapes repository: {relpath}") from exc
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink() or bool(getattr(current, "is_junction", lambda: False)()):
            raise V04HarnessError("UNSAFE_PATH", f"path traverses a link: {relpath}")
    if must_exist and (not candidate.is_file() or candidate.stat().st_size == 0):
        raise V04HarnessError("MISSING_FILE", f"required file is missing/empty: {relpath}")
    return candidate


def _hash_bound(root: Path, relpath: str, expected: str, label: str) -> Path:
    path = _safe_path(root, relpath)
    actual = sha256_file(path)
    if actual != expected:
        raise V04HarnessError(
            "HASH_MISMATCH",
            f"{label} hash mismatch: expected {expected}; actual {actual}",
            "AUTHORITY_PREFLIGHT",
        )
    return path


def _distribution_preflight() -> dict[str, str]:
    versions: dict[str, str] = {}
    for distribution in ("rdflib", "pyshacl", "PyLD", "jsonschema"):
        try:
            versions[distribution] = metadata.version(distribution)
        except metadata.PackageNotFoundError as exc:
            raise V04HarnessError(
                "CORE_DEPENDENCY_MISSING",
                f"required distribution is missing: {distribution}",
                "CORE_DEPENDENCY_PREFLIGHT",
            ) from exc
    if versions["pyshacl"] != EXPECTED_PYSHACL_VERSION:
        raise V04HarnessError(
            "PYSHACL_VERSION_MISMATCH",
            f"pySHACL must equal {EXPECTED_PYSHACL_VERSION}",
            "CORE_DEPENDENCY_PREFLIGHT",
        )
    try:
        import pyld  # noqa: F401
        import pyshacl  # noqa: F401
        import rdflib  # noqa: F401
    except ImportError as exc:
        raise V04HarnessError(
            "CORE_DEPENDENCY_IMPORT", "required validator module is not importable",
            "CORE_DEPENDENCY_PREFLIGHT",
        ) from exc
    return versions


def _release_record(document: Mapping[str, Any], release_id: str) -> dict[str, Any]:
    matches = [
        release
        for release in document.get("releases", [])
        if isinstance(release, dict) and release.get("id") == release_id
    ]
    if len(matches) != 1:
        raise V04HarnessError("RELEASE_REFERENCE", "release reference is not unique")
    return matches[0]


def _artifact_record(release: Mapping[str, Any], artifact_id: str) -> dict[str, Any]:
    matches = [
        artifact
        for artifact in release.get("artifacts", [])
        if isinstance(artifact, dict) and artifact.get("id") == artifact_id
    ]
    if len(matches) != 1:
        raise V04HarnessError("SHAPE_ARTIFACT_REFERENCE", "Shape artifact is not unique")
    return matches[0]


def _parse_shapes(path: Path, relpath: str) -> Any:
    try:
        from rdflib import Graph
    except ImportError as exc:
        raise V04HarnessError(
            "CORE_DEPENDENCY_IMPORT", "RDFLib is not importable",
            "CORE_DEPENDENCY_PREFLIGHT",
        ) from exc
    graph = Graph()
    try:
        graph.parse(
            data=path.read_text(encoding="utf-8-sig"),
            format="turtle",
            publicID="https://dssc.local/repository/" + relpath,
        )
    except Exception as exc:
        raise V04HarnessError(
            "AUTHORITATIVE_SHAPE_PARSE",
            "authoritative Shape graph cannot be parsed",
            "AUTHORITY_SHAPE_PREFLIGHT",
        ) from exc
    if len(graph) == 0:
        raise V04HarnessError(
            "AUTHORITATIVE_SHAPE_EMPTY", "authoritative Shape graph is empty",
            "AUTHORITY_SHAPE_PREFLIGHT",
        )
    return graph


def _verify_shape_targets(shapes_graph: Any) -> dict[str, Any]:
    from rdflib import Namespace, URIRef

    sh = Namespace(SH)
    cardinality = URIRef(DATASET_CARDINALITY_SHAPE)
    submission = URIRef(VALIDATION_SUBMISSION)
    closed = URIRef(DATASET_CLOSED_SHAPE)
    if (cardinality, sh.targetNode, submission) not in shapes_graph:
        raise V04HarnessError(
            "CARDINALITY_TARGET_MISSING", "fixed cardinality targetNode is missing",
            "AUTHORITY_SHAPE_PREFLIGHT",
        )
    if (closed, sh.severity, sh.Warning) not in shapes_graph:
        raise V04HarnessError(
            "CLOSED_WARNING_MISSING", "approved Closed Shape Warning is missing",
            "AUTHORITY_SHAPE_PREFLIGHT",
        )
    return {
        "cardinality_target": True,
        "closed_shape_warning": True,
        "shape_triple_count": len(shapes_graph),
    }


def _preflight(manifest: dict[str, Any], context: Mapping[str, Any]) -> _Preflight:
    root = context.get("repository_root")
    if not isinstance(root, Path):
        raise V04HarnessError("CONTEXT", "repository_root must be a Path")
    root = root.resolve()
    if manifest.get("engine") != MANIFEST_ENGINE_CONFIG:
        raise V04HarnessError(
            "ENGINE_CONFIG", "manifest engine config differs from the fixed contract",
            "TEST_MANIFEST_PREFLIGHT",
        )
    if manifest.get("suite") != "v0.4":
        raise V04HarnessError("MANIFEST_SUITE", "test manifest suite must be v0.4")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise V04HarnessError("ZERO_TESTS", "test manifest discovered 0 cases")
    case_ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if case_ids != list(EXPECTED_CASE_IDS):
        raise V04HarnessError(
            "CASE_SET", "test manifest must contain D04-PC001..D04-PC066 in order",
            "TEST_MANIFEST_PREFLIGHT",
        )
    for case in cases:
        case_id = case["case_id"]
        if case_id in UNTESTABLE_ALLOWLIST:
            oracle = case.get("oracle")
            expected_pair = UNTESTABLE_ALLOWLIST[case_id]
            if (
                case.get("expected_business_status") != "UNTESTABLE"
                or not isinstance(oracle, dict)
                or (oracle.get("failure_stage"), oracle.get("reason_code"))
                != expected_pair
            ):
                raise V04HarnessError(
                    "UNTESTABLE_ALLOWLIST",
                    f"{case_id} does not declare its exact controlled failure",
                    "TEST_MANIFEST_PREFLIGHT",
                )
        elif case.get("expected_business_status") == "UNTESTABLE":
            raise V04HarnessError(
                "UNTESTABLE_ALLOWLIST", f"unapproved UNTESTABLE case: {case_id}",
                "TEST_MANIFEST_PREFLIGHT",
            )

    dependencies = _distribution_preflight()
    manifest_path_value = context.get("manifest_path", TEST_MANIFEST_RELPATH)
    if isinstance(manifest_path_value, Path):
        try:
            manifest_relpath = manifest_path_value.resolve().relative_to(root).as_posix()
        except ValueError as exc:
            raise V04HarnessError("UNSAFE_PATH", "manifest_path is outside repository") from exc
    else:
        manifest_relpath = str(manifest_path_value)
    manifest_path = _safe_path(root, manifest_relpath)
    persisted_manifest = _load_json(manifest_path, "v0.4 test manifest")
    if persisted_manifest != manifest:
        raise V04HarnessError(
            "MANIFEST_CONTEXT_DRIFT", "passed manifest differs from persisted bytes",
            "TEST_MANIFEST_PREFLIGHT",
        )

    fixed_json_paths = (
        TEST_SCHEMA_RELPATH,
        RELEASE_MANIFEST_RELPATH,
        RELEASE_SCHEMA_RELPATH,
        REQUIREMENTS_RELPATH,
        REQUIREMENTS_SCHEMA_RELPATH,
        REGISTRY_RELPATH,
        REGISTRY_SCHEMA_RELPATH,
    )
    fixed_paths = {relpath: _safe_path(root, relpath) for relpath in fixed_json_paths}
    release_manifest = _load_json(
        fixed_paths[RELEASE_MANIFEST_RELPATH], "release manifest"
    )
    requirements = _load_json(fixed_paths[REQUIREMENTS_RELPATH], "requirements manifest")
    registry = _load_json(fixed_paths[REGISTRY_RELPATH], "suite registry")
    actual_registry_hash = sha256_file(fixed_paths[REGISTRY_RELPATH])
    if context.get("registry_sha256") != actual_registry_hash:
        raise V04HarnessError(
            "REGISTRY_CONTEXT_DRIFT", "dispatcher registry hash differs from current file"
        )
    if context.get("contract_version") != registry.get("contract_version"):
        raise V04HarnessError(
            "REGISTRY_CONTEXT_DRIFT", "dispatcher contract version differs from registry"
        )
    release_registry = release_manifest.get("validationSuiteRegistry")
    if (
        not isinstance(release_registry, dict)
        or release_registry.get("path") != REGISTRY_RELPATH
        or release_registry.get("sha256") != actual_registry_hash
        or release_registry.get("contractVersion") != registry.get("contract_version")
    ):
        raise V04HarnessError(
            "RELEASE_REGISTRY_BINDING",
            "release manifest does not bind the active suite registry",
            "AUTHORITY_PREFLIGHT",
        )

    release_id = manifest.get("release", {}).get("id")
    profile_id = manifest.get("profile", {}).get("id")
    if not isinstance(release_id, str) or not isinstance(profile_id, str):
        raise V04HarnessError("MANIFEST_REFERENCE", "release/profile ID is invalid")
    release = _release_record(release_manifest, release_id)
    shape_assertion = manifest.get("shape_artifact")
    if not isinstance(shape_assertion, dict):
        raise V04HarnessError("SHAPE_ARTIFACT_REFERENCE", "shape assertion is unavailable")
    artifact_id = shape_assertion.get("artifact_id")
    if not isinstance(artifact_id, str):
        raise V04HarnessError("SHAPE_ARTIFACT_REFERENCE", "shape artifact ID is invalid")
    artifact = _artifact_record(release, artifact_id)
    for field in ("path", "sha256"):
        if shape_assertion.get(field) != artifact.get(field):
            raise V04HarnessError(
                "SHAPE_ARTIFACT_BINDING", f"shape assertion {field} differs from release"
            )
    if shape_assertion.get("sha256") != EXPECTED_D_SHAPE_SHA256:
        raise V04HarnessError(
            "D_SHAPE_HASH", "authoritative Shape hash differs from the approved D hash"
        )
    shape_relpath = shape_assertion["path"]
    shape_path = _hash_bound(
        root, shape_relpath, shape_assertion["sha256"], "release Shape"
    )
    d_path = _hash_bound(root, D_SOURCE_RELPATH, EXPECTED_D_SHAPE_SHA256, "D source")
    if shape_path.read_bytes() != d_path.read_bytes():
        raise V04HarnessError("D_SHAPE_BYTE_COPY", "release Shape is not the D byte-copy")
    profile = requirements.get("profile")
    if (
        not isinstance(profile, dict)
        or profile.get("id") != profile_id
        or profile.get("version") != release_id
        or profile.get("normative_source", {}).get("path") != D_SOURCE_RELPATH
        or profile.get("normative_source", {}).get("sha256")
        != EXPECTED_D_SHAPE_SHA256
    ):
        raise V04HarnessError(
            "REQUIREMENTS_PROFILE_BINDING", "requirements profile/source binding differs"
        )

    evidence_records: list[dict[str, str]] = []
    evidence_refs = manifest.get("evidence_refs")
    if not isinstance(evidence_refs, dict):
        raise V04HarnessError("EVIDENCE_REFERENCE", "evidence_refs is unavailable")
    for evidence_id in ("meta_shacl", "shape_structure"):
        reference = evidence_refs.get(evidence_id)
        if not isinstance(reference, dict):
            raise V04HarnessError("EVIDENCE_REFERENCE", f"{evidence_id} is unavailable")
        path = reference.get("path")
        expected_hash = reference.get("sha256")
        if not isinstance(path, str) or not isinstance(expected_hash, str):
            raise V04HarnessError("EVIDENCE_REFERENCE", f"{evidence_id} binding is invalid")
        _hash_bound(root, path, expected_hash, evidence_id)
        evidence_records.append(
            {"id": evidence_id, "path": path, "sha256": expected_hash}
        )

    fixture_hashes: dict[str, str] = {}
    canonical_hash: str | None = None
    for case in cases:
        fixture = case.get("fixture")
        if not isinstance(fixture, dict):
            raise V04HarnessError("FIXTURE_BINDING", "fixture assertion is unavailable")
        relpath = fixture.get("path")
        expected_hash = fixture.get("sha256")
        if fixture.get("format") not in {"json-ld", "turtle"}:
            raise V04HarnessError("FIXTURE_FORMAT", "fixture format is unsupported")
        if not isinstance(relpath, str) or not isinstance(expected_hash, str):
            raise V04HarnessError("FIXTURE_BINDING", "fixture path/hash is invalid")
        _hash_bound(root, relpath, expected_hash, f"fixture {case['case_id']}")
        fixture_hashes[relpath] = expected_hash
        if case["case_id"] == "D04-PC001":
            canonical_hash = expected_hash
    if canonical_hash is None:
        raise V04HarnessError("CANONICAL_FIXTURE", "canonical PASS fixture is missing")
    for case in cases:
        if case["case_id"] in CONTROLLED_FAULT_CASES:
            if case["fixture"]["sha256"] != canonical_hash:
                raise V04HarnessError(
                    "CONTROLLED_FAULT_SUT",
                    f"{case['case_id']} must use canonical valid SUT bytes",
                    "TEST_MANIFEST_PREFLIGHT",
                )

    shapes_graph = _parse_shapes(shape_path, shape_relpath)
    try:
        bindings = build_requirement_bindings(requirements)
        named_shapes = assert_named_shapes(shapes_graph, bindings)
    except V04ReportError as exc:
        raise V04HarnessError(exc.code, exc.message, "AUTHORITY_SHAPE_PREFLIGHT") from exc
    shape_targets = _verify_shape_targets(shapes_graph)

    consumed = {
        manifest_relpath: sha256_file(manifest_path),
        **{relpath: sha256_file(path) for relpath, path in fixed_paths.items()},
    }
    input_hashes = {
        D_SOURCE_RELPATH: EXPECTED_D_SHAPE_SHA256,
        shape_relpath: shape_assertion["sha256"],
    }
    return _Preflight(
        root=root,
        manifest=manifest,
        requirements=requirements,
        release_manifest=release_manifest,
        registry=registry,
        shapes_graph=shapes_graph,
        bindings=bindings,
        authority_record={
            "status": "SUCCESS",
            "dependency_versions": dependencies,
            "engine_config": dict(MANIFEST_ENGINE_CONFIG),
            "shape_integrity": {
                "path": shape_relpath,
                "sha256": shape_assertion["sha256"],
                "d_byte_copy": True,
                **shape_targets,
                **named_shapes,
            },
            "evidence_refs": evidence_records,
            "fixture_count": len(cases),
            "fixture_hashes_verified_before_execution": True,
        },
        consumed_manifest_hashes=dict(sorted(consumed.items())),
        fixture_hashes=dict(sorted(fixture_hashes.items())),
        input_hashes=dict(sorted(input_hashes.items())),
    )


def _public_url(relpath: str) -> str:
    return "https://dssc.local/repository/" + relpath


def _parse_jsonld_fixture(root: Path, path: Path, relpath: str) -> tuple[Any, dict[str, Any]]:
    try:
        from pyld import jsonld
        from rdflib import Graph
    except ImportError as exc:
        raise V04HarnessError(
            "CORE_DEPENDENCY_IMPORT", "JSON-LD dependencies are not importable",
            "CORE_DEPENDENCY_PREFLIGHT",
        ) from exc
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _ObservedSUTFailure("INPUT_PARSE", "MALFORMED_JSON") from exc
    base_url = _public_url(relpath)
    repository_url = "https://dssc.local/repository/"
    requests: list[str] = []
    context_failure = False

    def local_loader(url: str, options: dict[str, Any] | None = None):
        nonlocal context_failure
        del options
        requests.append(url)
        if not url.startswith(repository_url):
            context_failure = True
            raise V04HarnessError("NETWORK_CONTEXT_FORBIDDEN", "HTTP context fetch is forbidden")
        parsed = urlparse(url)
        rel = unquote(parsed.path.removeprefix("/repository/"))
        try:
            context_path = _safe_path(root, rel)
            context_document = json.loads(
                context_path.read_text(encoding="utf-8-sig")
            )
        except (V04HarnessError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            context_failure = True
            raise V04HarnessError(
                "OFFLINE_CONTEXT_UNAVAILABLE", "required local context is unavailable"
            ) from exc
        return {
            "contextUrl": None,
            "documentUrl": url,
            "document": context_document,
        }

    try:
        expanded = jsonld.expand(
            document,
            options={"base": base_url, "documentLoader": local_loader},
        )
    except Exception as exc:
        if context_failure:
            raise _ObservedSUTFailure(
                "OFFLINE_LOAD", "OFFLINE_CONTEXT_UNAVAILABLE"
            ) from exc
        raise _ObservedSUTFailure("OFFLINE_LOAD", "JSONLD_EXPANSION_ERROR") from exc
    if not isinstance(expanded, list):
        raise _ObservedSUTFailure("OFFLINE_LOAD", "JSONLD_EXPANSION_ERROR")
    graph = Graph()
    try:
        graph.parse(
            data=json.dumps(expanded, ensure_ascii=False),
            format="json-ld",
            publicID=base_url,
        )
    except Exception as exc:
        raise _ObservedSUTFailure("INPUT_PARSE", "MALFORMED_RDF") from exc
    return graph, {
        "format": "json-ld",
        "document_url": base_url,
        "loader_requests": sorted(requests),
        "loader_request_count": len(requests),
        "network_request_count": 0,
        "expanded_node_count": len(expanded),
        "data_triple_count": len(graph),
    }


def _parse_fixture(preflight: _Preflight, case: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
    fixture = case["fixture"]
    relpath = fixture["path"]
    path = _safe_path(preflight.root, relpath)
    if fixture["format"] == "json-ld":
        return _parse_jsonld_fixture(preflight.root, path, relpath)
    try:
        from rdflib import Graph
        graph = Graph()
        graph.parse(
            data=path.read_text(encoding="utf-8-sig"),
            format="turtle",
            publicID=_public_url(relpath),
        )
    except Exception as exc:
        raise _ObservedSUTFailure("INPUT_PARSE", "MALFORMED_RDF") from exc
    return graph, {
        "format": "turtle",
        "document_url": _public_url(relpath),
        "loader_requests": [],
        "loader_request_count": 0,
        "network_request_count": 0,
        "data_triple_count": len(graph),
    }


def _inject_controlled_fault(case_id: str) -> None:
    pair = UNTESTABLE_ALLOWLIST[case_id]
    raise _ControlledValidatorFault(*pair)


def classify_execution_failure(
    case_id: str,
    stage: str,
    reason_code: str,
    *,
    authority_preflight_complete: bool,
    controlled: bool,
) -> dict[str, Any]:
    """Apply the boundary between expected UNTESTABLE and program ERROR."""
    allowed = UNTESTABLE_ALLOWLIST.get(case_id)
    is_controlled_validator = case_id in CONTROLLED_FAULT_CASES
    accepted = (
        authority_preflight_complete
        and allowed == (stage, reason_code)
        and (controlled if is_controlled_validator else True)
    )
    if accepted:
        return {
            "actual_business_status": "UNTESTABLE",
            "program_status": "SUCCESS",
            "failure_stage": stage,
            "reason_code": reason_code,
            "report": None,
            "controlled_fault": is_controlled_validator,
        }
    return {
        "actual_business_status": None,
        "program_status": "ERROR",
        "failure_stage": stage,
        "reason_code": reason_code,
        "report": None,
        "controlled_fault": False,
    }


def run_failure_boundary_self_tests() -> dict[str, Any]:
    """Deterministically prove PC067-070 and unexpected runtime stay ERROR."""
    cases = (
        (
            "D04-PC067",
            "AUTHORITY_SHAPE_PREFLIGHT",
            "SHAPE_PARSE_ERROR",
            True,
            False,
        ),
        ("D04-PC068", "TEST_MANIFEST_PREFLIGHT", "MANIFEST_INVALID", True, False),
        ("D04-PC069", "HARNESS_PREFLIGHT", "HARNESS_INTERNAL_ERROR", True, False),
        (
            "D04-PC070",
            "CORE_DEPENDENCY_PREFLIGHT",
            "DEPENDENCY_MISSING",
            True,
            False,
        ),
        (
            "D04-PC001",
            "VALIDATOR_EXECUTION",
            "UNEXPECTED_RUNTIME_EXCEPTION",
            True,
            False,
        ),
        # Even an allowlisted named fault remains a program error until every
        # authority/dependency/SUT preflight has completed successfully.
        (
            "D04-PC064",
            "VALIDATOR_EXECUTION",
            "VALIDATOR_TIMEOUT",
            False,
            True,
        ),
    )
    results: list[dict[str, Any]] = []
    for case_id, stage, reason, preflight_complete, controlled in cases:
        disposition = classify_execution_failure(
            case_id,
            stage,
            reason,
            authority_preflight_complete=preflight_complete,
            controlled=controlled,
        )
        passed = (
            disposition["program_status"] == "ERROR"
            and disposition["actual_business_status"] is None
        )
        results.append(
            {
                "case_id": case_id,
                "injected_stage": stage,
                "injected_reason_code": reason,
                "authority_preflight_complete": preflight_complete,
                "controlled": controlled,
                "actual_business_status": disposition["actual_business_status"],
                "program_status": disposition["program_status"],
                "passed": passed,
            }
        )
    return {
        "schema": "dssc.v0.4.failure-boundary-self-tests.v1",
        "discovered": len(results),
        "executed": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "failed": sum(1 for result in results if not result["passed"]),
        "skipped": 0,
        "all_passed": all(result["passed"] for result in results),
        "cases": results,
    }


def _run_validator(
    data_graph: Any,
    shapes_graph: Any,
    bindings: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        from pyshacl import validate
        from rdflib import Graph
    except ImportError as exc:
        raise V04HarnessError(
            "CORE_DEPENDENCY_IMPORT", "validator dependencies are not importable",
            "CORE_DEPENDENCY_PREFLIGHT",
        ) from exc
    if data_graph is shapes_graph:
        raise V04HarnessError("GRAPH_ISOLATION", "data and Shape graph are identical")
    before_data = frozenset(data_graph)
    before_shapes = frozenset(shapes_graph)
    validation_shapes = Graph()
    for triple in shapes_graph:
        validation_shapes.add(triple)
    activation = collect_target_activation(data_graph, shapes_graph)
    logger = logging.getLogger("pyshacl-validate")
    prior_disabled = logger.disabled
    try:
        logger.disabled = True
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            conforms, report_graph, _report_text = validate(
                data_graph=data_graph,
                shacl_graph=validation_shapes,
                ont_graph=None,
                **dict(PYSHACL_KWARGS),
            )
    except Exception as exc:
        raise V04HarnessError(
            "UNEXPECTED_VALIDATOR_EXCEPTION",
            f"pySHACL raised {exc.__class__.__name__}",
            "VALIDATOR_EXECUTION",
        ) from exc
    finally:
        logger.disabled = prior_disabled
    if frozenset(data_graph) != before_data or frozenset(shapes_graph) != before_shapes:
        raise V04HarnessError("GRAPH_MUTATION", "validator mutated an authority/data graph")
    try:
        report = normalize_shacl_report(report_graph, bindings)
    except V04ReportError as exc:
        raise V04HarnessError(exc.code, exc.message, "REPORT_PARSE") from exc
    if bool(conforms) != report["report_conforms"]:
        raise V04HarnessError("CONFORMS_MISMATCH", "validator/report conforms values differ")
    should_conform = report["result_count"] == 0
    if report["report_conforms"] != should_conform:
        raise V04HarnessError(
            "CONFORMS_POLICY_MISMATCH",
            "report conforms conflicts with fixed Warning/Info policy",
        )
    report.update(
        {
            "engine_config": dict(MANIFEST_ENGINE_CONFIG),
            "graphs_separate": True,
            "ontology_graph_supplied": False,
            "throwaway_shapes_graph_supplied": True,
            "data_graph_unchanged": True,
            "shapes_graph_unchanged": True,
        }
    )
    return report, activation


def _execute_case(preflight: _Preflight, case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = case["case_id"]
    try:
        data_graph, load_evidence = _parse_fixture(preflight, case)
        if case_id in CONTROLLED_FAULT_CASES:
            _inject_controlled_fault(case_id)
        report, activation = _run_validator(
            data_graph, preflight.shapes_graph, preflight.bindings
        )
        execution = {
            "actual_business_status": report["business_status"],
            "failure_stage": None,
            "reason_code": None,
            "controlled_fault": False,
            "load_evidence": load_evidence,
            "target_activation": activation,
            "report": report,
        }
    except _ObservedSUTFailure as exc:
        disposition = classify_execution_failure(
            case_id,
            exc.stage,
            exc.reason_code,
            authority_preflight_complete=True,
            controlled=isinstance(exc, _ControlledValidatorFault),
        )
        if disposition["program_status"] != "SUCCESS":
            raise V04HarnessError(
                "UNCONTROLLED_UNTESTABLE",
                f"unapproved inability-to-test observation for {case_id}",
                exc.stage,
            ) from exc
        if isinstance(exc, _ControlledValidatorFault):
            disposition["preflight_complete"] = True
            disposition["completed_preflights"] = {
                "authority": True,
                "dependency": True,
                "shape": True,
                "manifest": True,
                "fixture_hash": True,
                "sut_parse": True,
            }
        execution = disposition
    return assert_case_oracle(case, execution)


def _coverage_record(
    requirements: Mapping[str, Any], case_results: list[dict[str, Any]]
) -> dict[str, Any]:
    required = sorted(
        requirement.get("id")
        for requirement in requirements.get("requirements", [])
        if isinstance(requirement, dict) and isinstance(requirement.get("id"), str)
    )
    executed = sorted(
        {
            requirement_id
            for case in case_results
            if case.get("program_status") == "SUCCESS"
            for requirement_id in case.get("requirement_ids", [])
        }
    )
    missing = sorted(set(required) - set(executed))
    return {
        "required_requirement_ids": required,
        "executed_requirement_ids": executed,
        "covered_count": len(set(required) & set(executed)),
        "required_count": len(required),
        "missing_requirement_ids": missing,
        "complete": not missing and bool(required),
    }


def _sparql_execution_record(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    required_cases = ("D04-PC002", "D04-PC003", "D04-PC049")
    results: list[dict[str, Any]] = []
    by_id = {case.get("case_id"): case for case in case_results}
    component = SH + "SPARQLConstraintComponent"
    for case_id in required_cases:
        case = by_id.get(case_id, {})
        rows = case.get("execution", {}).get("report", {}).get("results", [])
        matched = sum(
            1
            for row in rows
            if isinstance(row, dict)
            and row.get("source_constraint_component") == component
        )
        results.append({"case_id": case_id, "sparql_result_count": matched, "passed": matched > 0})
    return {"all_executed": all(item["passed"] for item in results), "cases": results}


def evaluate_v04_suite_aggregate(
    counts: Mapping[str, Any],
    *,
    four_states_present: Any,
    coverage_complete: Any,
    sparql_all_executed: Any,
    failure_boundary_passed: Any,
) -> dict[str, Any]:
    """Apply the single fail-closed aggregate verdict used by the core."""

    guard_codes: list[str] = []
    required = ("discovered", "executed", "passed", "failed", "skipped")
    valid_counts = isinstance(counts, Mapping) and all(
        type(counts.get(name)) is int and counts[name] >= 0 for name in required
    )
    if not valid_counts:
        guard_codes.append("INVALID_EXECUTION_COUNTS")
    else:
        discovered = counts["discovered"]
        executed = counts["executed"]
        passed = counts["passed"]
        failed = counts["failed"]
        skipped = counts["skipped"]
        if discovered == 0:
            guard_codes.append("ZERO_TESTS")
        if discovered > 0 and executed == 0:
            guard_codes.append("ZERO_EXECUTED")
        if skipped > 0:
            guard_codes.append("REQUIRED_TEST_SKIPPED")
        if executed != discovered:
            guard_codes.append("INCOMPLETE_EXECUTION")
        if passed != discovered or failed != 0:
            guard_codes.append("CASE_ORACLE_FAILURE")
        if passed + failed != executed or executed + skipped != discovered:
            guard_codes.append("EXECUTION_COUNT_MISMATCH")
    for passed, code in (
        (four_states_present, "FOUR_STATES_MISSING"),
        (coverage_complete, "REQUIREMENT_COVERAGE_INCOMPLETE"),
        (sparql_all_executed, "REQUIRED_SPARQL_NOT_EXECUTED"),
        (failure_boundary_passed, "FAILURE_BOUNDARY_CONTROL_FAILED"),
    ):
        if passed is not True:
            guard_codes.append(code)
    successful = not guard_codes
    return {
        "program_status": "SUCCESS" if successful else "ERROR",
        "exit_code": 0 if successful else 1,
        "guard_codes": guard_codes,
    }


def execute_v04_suite(
    manifest: dict[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    """Execute the deterministic core and return an un-finalized suite payload."""
    preflight = _preflight(manifest, context)
    cases = manifest["cases"]
    results: list[dict[str, Any]] = []
    for case in cases:
        try:
            result = _execute_case(preflight, case)
        except (V04HarnessError, V04ReportError, V04OracleError) as exc:
            code = getattr(exc, "code", exc.__class__.__name__)
            message = getattr(exc, "message", str(exc))
            result = error_case_result(case, str(code), str(message))
        except Exception as exc:  # noqa: BLE001 - never convert to UNTESTABLE
            result = error_case_result(
                case,
                "UNEXPECTED_HARNESS_EXCEPTION",
                f"unexpected {exc.__class__.__name__}",
            )
        results.append(result)

    counts = {
        "discovered": len(cases),
        "executed": len(results),
        "passed": sum(1 for result in results if result.get("passed") is True),
        "failed": sum(1 for result in results if result.get("passed") is not True),
        "skipped": len(cases) - len(results),
    }
    status_counts = {status: 0 for status in ("PASS", "FAIL", "INAPPLICABLE", "UNTESTABLE")}
    for result in results:
        actual = result.get("actual_business_status")
        if actual in status_counts:
            status_counts[actual] += 1
    coverage = _coverage_record(preflight.requirements, results)
    sparql = _sparql_execution_record(results)
    boundary = run_failure_boundary_self_tests()
    four_states_present = all(status_counts[status] > 0 for status in status_counts)
    aggregate = evaluate_v04_suite_aggregate(
        counts,
        four_states_present=four_states_present,
        coverage_complete=coverage["complete"],
        sparql_all_executed=sparql["all_executed"],
        failure_boundary_passed=boundary["all_passed"],
    )
    successful = aggregate["program_status"] == "SUCCESS"
    lock_path = preflight.root / "requirements.lock"
    return {
        "manifest_schema_version": manifest.get("manifest_schema_version"),
        "test_manifest_path": TEST_MANIFEST_RELPATH,
        "test_manifest_sha256": preflight.consumed_manifest_hashes[TEST_MANIFEST_RELPATH],
        "registry_contract_version": context.get("contract_version"),
        "registry_path": REGISTRY_RELPATH,
        "registry_sha256": context.get("registry_sha256"),
        "requirements_lock_sha256": sha256_file(lock_path) if lock_path.is_file() else None,
        "shape_path": manifest["shape_artifact"]["path"],
        "shape_sha256": manifest["shape_artifact"]["sha256"],
        "engine_config": dict(MANIFEST_ENGINE_CONFIG),
        "authority_preflight": preflight.authority_record,
        "consumed_manifest_hashes": preflight.consumed_manifest_hashes,
        "input_hashes": preflight.input_hashes,
        "fixture_hashes": preflight.fixture_hashes,
        "counts": counts,
        "business_status_counts": status_counts,
        "four_states_present": four_states_present,
        "coverage": coverage,
        "sparql_execution": sparql,
        "failure_boundary_self_tests": boundary,
        "case_results": results,
        "program_status": aggregate["program_status"],
        "exit_code": aggregate["exit_code"],
        "message": (
            "v0.4 fixture validation passed"
            if successful
            else "v0.4 fixture validation failed"
        ),
    }


def run_v04_harness(
    manifest: dict[str, Any],
    context: Mapping[str, Any],
    *,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Controlled-catalog component API.

    Returns exactly the generic dispatcher component contract.  Global
    preflight failures are program ERROR and never appear as business
    UNTESTABLE.  When the core can be finalized, the three Phase 05 outputs are
    written under ``build/validation/v0.4``.
    """
    root = context.get("repository_root")
    profile = context.get("profile")
    if not isinstance(root, Path) or profile not in {"host", "container"}:
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "v0.4 harness requires repository_root and host|container profile",
            "details": {},
            "machine_details": {},
    }
    try:
        payload = execute_v04_suite(manifest, context)
        required_sources = context.get("v04_required_sources", ())
        if not isinstance(required_sources, (list, tuple)) or any(
            not isinstance(item, str) for item in required_sources
        ):
            raise V04HarnessError(
                "CONTEXT", "v04_required_sources must be an array of strings"
            )
        result, environment = finalize_v04_result(
            root, profile, payload, required_sources=required_sources
        )
        paths: tuple[Path, Path, Path] | tuple[()] = ()
        if write_outputs:
            paths = write_v04_evidence(root, result, environment)
    except Exception as exc:  # noqa: BLE001 - authority/harness failure is ERROR
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": f"v0.4 harness failed closed: {exc.__class__.__name__}",
            "details": {
                "error": {
                    "code": getattr(exc, "code", exc.__class__.__name__),
                    "stage": getattr(exc, "stage", "HARNESS"),
                    "message": getattr(exc, "message", str(exc)),
                },
                "failure_boundary_self_tests": run_failure_boundary_self_tests(),
            },
            "machine_details": {},
        }
    passed = result.get("program_status") == "SUCCESS" and result.get("exit_code") == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "program_status": "SUCCESS" if passed else "ERROR",
        "message": (
            "v0.4 fixture validation passed"
            if passed
            else "v0.4 fixture validation failed"
        ),
        "details": {
            "v04_result": result,
            "evidence_files": [path.relative_to(root).as_posix() for path in paths],
        },
        "machine_details": {"v04_environment": environment},
    }


__all__ = [
    "EXPECTED_PYSHACL_VERSION",
    "MANIFEST_ENGINE_CONFIG",
    "PYSHACL_KWARGS",
    "UNTESTABLE_ALLOWLIST",
    "V04HarnessError",
    "classify_execution_failure",
    "evaluate_v04_suite_aggregate",
    "execute_v04_suite",
    "run_failure_boundary_self_tests",
    "run_v04_harness",
]
