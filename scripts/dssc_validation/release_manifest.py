"""Schema, integrity, and cross-record audit for the release manifest.

The JSON Schema owns record shape.  This module adds the relationships that
JSON Schema cannot express: stable identifiers, safe repository paths, exact
hash bindings, release/source/validator/requirement references, prior and
inheritance acyclicity, and the frozen v0.1-v0.3 baseline inventory.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from dssc_validation.baseline_manifest import (
    BaselineManifestError,
    load_and_validate_baseline_manifest,
)
from dssc_validation.hashing import sha256_file


MANIFEST_RELPATH = "C_Semantic_Treehouse/manifests/release-manifest.json"
SCHEMA_RELPATH = (
    "C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json"
)
REQUIREMENTS_RELPATH = (
    "C_Semantic_Treehouse/manifests/v0.4-requirements.json"
)
VALIDATION_SUITES_RELPATH = (
    "C_Semantic_Treehouse/manifests/validation-suites.json"
)

EXPECTED_RELEASE_IDS = ("v0.1", "v0.2", "v0.3", "v0.4")
EXPECTED_VALIDATOR_IDS = frozenset(
    {
        "rdflib-turtle",
        "pyld-jsonld",
        "pyshacl",
        "jsonschema-draft7",
        "openapi-spec-validator",
    }
)
EXPECTED_PHASE03_REQUIREMENTS_SHA256 = (
    "67391a561c61aa540535463df371e2aa5a0c4f8fff93b45c52a18b0067258ae1"
)
EXPECTED_RECORD_INHERITANCE = {
    "C_Semantic_Treehouse/model/v0.3/energy-reading-record.schema.json": (
        "dd07414e3752bf582bf5e721009064e16d7be3e1e06d60daaad08000869ccfa9"
    ),
    "C_Semantic_Treehouse/model/v0.3/energy-reading-record-context.jsonld": (
        "9727da9b8650dc444d719113a6978a3a26a59bfd1fde011a98e4c1f4b476f748"
    ),
    "C_Semantic_Treehouse/model/v0.3/energy-reading-record-shapes.ttl": (
        "84d1eee9cfeecd1791117552611e83d36af7df4f3b4c783ddbd75d45bae66c9a"
    ),
    "C_Semantic_Treehouse/model/v0.3/energy-reading-record-valid.jsonld": (
        "8f7509ad08fb9a62cdff1d6c904801c9421c3ce768bdd9ecb651cd480aa158e1"
    ),
    "C_Semantic_Treehouse/model/v0.3/energy-reading-record-invalid.jsonld": (
        "e516f6a8e4ea811170c72e922b86ac7ea46594046704d01a55a2c8e13cd8f358"
    ),
}
EXPECTED_REQUIREMENT_IDS = tuple(f"D04-R{index:03d}" for index in range(1, 18))
EXPECTED_HISTORICAL_ROLES = {
    "v01-ontology": "ontology",
    "v01-metadata-context": "metadata-context",
    "v01-metadata-shapes": "metadata-shapes",
    "v01-metadata-valid": "metadata-valid-example",
    "v02-ontology": "ontology",
    "v02-metadata-context": "metadata-context",
    "v02-metadata-invalid": "metadata-invalid-example",
    "v02-metadata-shapes": "metadata-shapes",
    "v02-metadata-valid": "metadata-valid-example",
    "v03-ontology": "ontology",
    "v03-metadata-context": "metadata-context",
    "v03-metadata-shapes": "metadata-shapes",
    "v03-metadata-valid": "metadata-valid-example",
    "v03-record-schema": "record-json-schema",
    "v03-record-context": "record-context",
    "v03-record-invalid": "record-invalid-example",
    "v03-record-shapes": "record-shapes",
    "v03-record-valid": "record-valid-example",
    "v03-openapi": "openapi",
}
EXPECTED_SOURCE_BINDINGS = {
    "C_Semantic_Treehouse/manifests/baseline-test-cases.json": (
        "e8fb57fe2f609c48c0340cf8e3b78d2e8f81d0fe0fd3ab505468cfe315767e43"
    ),
    "docs/provenance/manifests/frozen-files-SHA256SUMS": (
        # Git blob / LF working-tree bytes (eol=lf). Must not use Windows CRLF smudge hash.
        "d699b5a5f29083e882d714995800b03b3bd0ff289531ee88766dd2b6728c7cb2"
    ),
    "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl": (
        "a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda"
    ),
    "inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md": (
        "d95a98be50641dbf4c131818547756183bf795edc426668c7c43c00f934bc7b4"
    ),
    (
        "inputs/original-plan/DSSC_Minimal_Energy_Scenario/metadata/"
        "data-product-valid.jsonld"
    ): "fd64b653877fbf7df3bd9f66d482dafb576df7ce096cdb54c2f36079aa521013",
    (
        "inputs/original-plan/DSSC_Minimal_Energy_Scenario/metadata/"
        "data-product-invalid.jsonld"
    ): "e298d7aaf9b26dff54b539ba973900345783e35a549f6c03119487bbb8a66355",
    "docs/v0.4/decisions/ADR-001-dct-conforms-to.md": (
        "1f32a23a955cedc4c4b06a10a3ea82efd4ad2be3890562193838ac706b18988a"
    ),
    "docs/v0.4/decisions/ADR-002-wire-profile-and-version-identity.md": (
        "fcefb0a0aa615cc194d7077b2a20f0dcd62a19d446c163abe8adb8b8d39aa759"
    ),
    "docs/v0.4/decisions/ADR-003-energy-record-inheritance.md": (
        "d1bdfe0a533261bcff6bad0306c0436de7c6a415db19decf159dc34993729286"
    ),
}
EXPECTED_V04_NATIVE_ARTIFACTS = {
    "C_Semantic_Treehouse/model/v0.4/README.md": "release-documentation",
    "C_Semantic_Treehouse/model/v0.4/SHA256SUMS": "checksum-manifest",
    "C_Semantic_Treehouse/model/v0.4/building-energy-ontology.ttl": "ontology",
    "C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld": "metadata-context",
    "C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl": "metadata-shapes",
    "C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld": "metadata-valid-example",
}
EXPECTED_V04_NATIVE_TRANSFORMATIONS = {
    "C_Semantic_Treehouse/model/v0.4/README.md": "manual-derivation",
    "C_Semantic_Treehouse/model/v0.4/SHA256SUMS": "sha256-manifest",
    "C_Semantic_Treehouse/model/v0.4/building-energy-ontology.ttl": "manual-derivation",
    "C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld": "manual-derivation",
    "C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl": "byte-copy",
    "C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld": "manual-derivation",
}

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_GLOB_CHARACTERS = frozenset("*?[]{}")


def release_manifest_path(root: Path) -> Path:
    return root / Path(*PurePosixPath(MANIFEST_RELPATH).parts)


def release_manifest_schema_path(root: Path) -> Path:
    return root / Path(*PurePosixPath(SCHEMA_RELPATH).parts)


def _issue(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def _sorted_issues(issues: list[dict[str, str]]) -> tuple[dict[str, str], ...]:
    unique = {
        (item["code"], item["location"], item["message"]): item
        for item in issues
    }
    return tuple(unique[key] for key in sorted(unique))


class _DuplicateKey(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKey(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as stream:
        return json.load(stream, object_pairs_hook=_reject_duplicate_keys)


def _schema_issues(schema: Any, document: Any) -> list[dict[str, str]]:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from jsonschema.exceptions import SchemaError
    except ImportError:
        return [
            _issue(
                "SCHEMA_ENGINE_MISSING",
                "$schema",
                "jsonschema is not importable",
            )
        ]
    if not isinstance(schema, dict):
        return [_issue("SCHEMA_ROOT", "$schema", "schema root must be an object")]
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [_issue("SCHEMA_INVALID", "$schema", exc.message)]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        _issue(
            "SCHEMA_VALIDATION",
            "$"
            + "".join(
                f"[{part}]" if isinstance(part, int) else f".{part}"
                for part in error.absolute_path
            ),
            error.message,
        )
        for error in sorted(
            validator.iter_errors(document),
            key=lambda item: (
                tuple(str(part) for part in item.absolute_path),
                item.message,
            ),
        )
    ]


def _safe_repo_path(root: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, "path must be a non-empty string"
    if (
        value.startswith(("/", "\\"))
        or _WINDOWS_DRIVE.match(value)
        or "\\" in value
        or "\x00" in value
        or "//" in value
        or value.endswith("/")
        or any(character in value for character in _GLOB_CHARACTERS)
    ):
        return None, "path must be a canonical repository-relative POSIX path"
    parts = PurePosixPath(value).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return None, "path contains an unsafe segment"
    candidate = (root / Path(*parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None, "path resolves outside the repository"
    return candidate, None


def _duplicates(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for value in values:
        try:
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        except TypeError:
            continue
    return sorted(duplicates, key=str)


def _verify_file_binding(
    root: Path,
    path_value: Any,
    sha_value: Any,
    location: str,
    issues: list[dict[str, str]],
) -> Path | None:
    path, path_issue = _safe_repo_path(root, path_value)
    if path_issue:
        issues.append(_issue("UNSAFE_PATH", f"{location}.path", path_issue))
        return None
    if not isinstance(sha_value, str) or _SHA256.fullmatch(sha_value) is None:
        issues.append(
            _issue("INVALID_SHA256", f"{location}.sha256", "invalid SHA-256")
        )
    if path is None or not path.is_file():
        issues.append(
            _issue("ARTIFACT_MISSING", f"{location}.path", f"file is missing: {path_value}")
        )
        return None
    if path.stat().st_size == 0:
        issues.append(
            _issue("ARTIFACT_EMPTY", f"{location}.path", f"file is empty: {path_value}")
        )
    if isinstance(sha_value, str) and _SHA256.fullmatch(sha_value):
        actual = sha256_file(path)
        if actual != sha_value:
            issues.append(
                _issue(
                    "HASH_MISMATCH",
                    f"{location}.sha256",
                    f"expected {sha_value}; actual {actual}",
                )
            )
    return path


def _cycle_issues(
    edges: dict[str, set[str]], code: str, location: str
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    white, gray, black = 0, 1, 2
    colors = {node: white for node in edges}
    reported: set[tuple[str, ...]] = set()

    def visit(node: str, stack: list[str]) -> None:
        colors[node] = gray
        stack.append(node)
        for target in sorted(edges.get(node, set())):
            if target not in colors:
                continue
            if colors[target] == gray:
                cycle = tuple(stack[stack.index(target) :] + [target])
                if cycle not in reported:
                    reported.add(cycle)
                    issues.append(
                        _issue(code, location, " -> ".join(cycle))
                    )
            elif colors[target] == white:
                visit(target, stack)
        stack.pop()
        colors[node] = black

    for node in sorted(edges):
        if colors[node] == white:
            visit(node, [])
    return issues


def _historical_baseline_issues(
    root: Path,
    releases: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    issues: list[dict[str, str]] = []
    record: dict[str, Any] = {"status": "ERROR", "expected": [], "actual": []}
    try:
        baseline = load_and_validate_baseline_manifest(root)
    except BaselineManifestError as exc:
        issues.append(
            _issue("BASELINE_MANIFEST_INVALID", "$.releases", str(exc))
        )
        return issues, record
    expected = [
        {
            "id": artifact["id"],
            "release": artifact["release"],
            "role": EXPECTED_HISTORICAL_ROLES.get(artifact["id"]),
            "path": artifact["path"],
            "sha256": artifact["sha256"],
        }
        for artifact in baseline.deterministic_record()["artifacts"]
        if artifact["release"] in {"v0.1", "v0.2", "v0.3"}
        and artifact["path"].startswith(
            f"C_Semantic_Treehouse/model/{artifact['release']}/"
        )
    ]
    actual = [
        {
            "id": artifact.get("id"),
            "release": release.get("id"),
            "role": artifact.get("role"),
            "path": artifact.get("path"),
            "sha256": artifact.get("sha256"),
        }
        for release in releases
        if release.get("id") in {"v0.1", "v0.2", "v0.3"}
        for artifact in release.get("artifacts", [])
        if isinstance(artifact, dict)
    ]
    expected.sort(key=lambda item: (item["release"], item["id"]))
    actual.sort(key=lambda item: (str(item["release"]), str(item["id"])))
    if actual != expected:
        issues.append(
            _issue(
                "FROZEN_RELEASE_DRIFT",
                "$.releases",
                "v0.1-v0.3 artifact inventory differs from baseline-test-cases.json",
            )
        )
    record = {
        "status": "SUCCESS" if actual == expected else "ERROR",
        "baseline_manifest_sha256": baseline.manifest_sha256,
        "expected": expected,
        "actual": actual,
    }
    return issues, record


def _semantic_issues(
    document: dict[str, Any], root: Path
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    issues: list[dict[str, str]] = []
    releases = document.get("releases", [])
    if not isinstance(releases, list):
        return [_issue("RELEASES_TYPE", "$.releases", "releases must be an array")], {}

    release_ids = [
        item.get("id") for item in releases if isinstance(item, dict)
    ]
    for duplicate in _duplicates(release_ids):
        issues.append(
            _issue("DUPLICATE_RELEASE_ID", "$.releases", f"duplicate release ID: {duplicate}")
        )
    if tuple(release_ids) != EXPECTED_RELEASE_IDS:
        issues.append(
            _issue(
                "RELEASE_SET_OR_ORDER",
                "$.releases",
                "release IDs/order must be v0.1, v0.2, v0.3, v0.4",
            )
        )
    release_by_id = {
        item["id"]: item
        for item in releases
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and release_ids.count(item["id"]) == 1
    }
    current = document.get("currentRelease")
    current_status_ids = [
        item.get("id")
        for item in releases
        if isinstance(item, dict) and item.get("status") == "current"
    ]
    if current != "v0.4":
        issues.append(
            _issue("CURRENT_RELEASE_NOT_V04", "$.currentRelease", "currentRelease must equal v0.4")
        )
    if current_status_ids != ["v0.4"]:
        issues.append(
            _issue(
                "CURRENT_RELEASE_CARDINALITY",
                "$.releases",
                "exactly v0.4 must have status current",
            )
        )
    for release_id in ("v0.1", "v0.2", "v0.3"):
        if release_by_id.get(release_id, {}).get("status") != "frozen":
            issues.append(
                _issue("FROZEN_RELEASE_STATUS", f"$.releases[{release_id}]", "historical release must be frozen")
            )

    prior_edges = {release_id: set() for release_id in release_by_id}
    expected_priors = {
        "v0.1": None,
        "v0.2": "v0.1",
        "v0.3": "v0.2",
        "v0.4": "v0.3",
    }
    for release_id, release in release_by_id.items():
        prior = release.get("priorRelease")
        if prior != expected_priors[release_id]:
            issues.append(
                _issue("PRIOR_RELEASE_CHAIN", f"$.releases[{release_id}].priorRelease", "unexpected priorRelease")
            )
        if isinstance(prior, str):
            if prior not in release_by_id:
                issues.append(
                    _issue("DANGLING_PRIOR_RELEASE", f"$.releases[{release_id}].priorRelease", prior)
                )
            else:
                prior_edges[release_id].add(prior)
        root_value = release.get("root")
        root_path, root_issue = _safe_repo_path(root, root_value)
        if root_issue:
            issues.append(_issue("UNSAFE_PATH", f"$.releases[{release_id}].root", root_issue))
        elif root_path is None or not root_path.is_dir():
            issues.append(_issue("RELEASE_ROOT_MISSING", f"$.releases[{release_id}].root", str(root_value)))
    issues.extend(_cycle_issues(prior_edges, "PRIOR_RELEASE_CYCLE", "$.releases"))

    source_catalog = document.get("sourceCatalog", [])
    source_ids = [
        item.get("id") for item in source_catalog if isinstance(item, dict)
    ]
    for duplicate in _duplicates(source_ids):
        issues.append(_issue("DUPLICATE_SOURCE_ID", "$.sourceCatalog", str(duplicate)))
    sources = {
        item["id"]: item
        for item in source_catalog
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and source_ids.count(item["id"]) == 1
    }
    for index, source in enumerate(source_catalog):
        if isinstance(source, dict):
            _verify_file_binding(root, source.get("path"), source.get("sha256"), f"$.sourceCatalog[{index}]", issues)
            if source.get("path") == MANIFEST_RELPATH:
                issues.append(
                    _issue(
                        "MANIFEST_SELF_REFERENCE",
                        f"$.sourceCatalog[{index}].path",
                        MANIFEST_RELPATH,
                    )
                )
    source_path_hashes = {
        item.get("path"): item.get("sha256")
        for item in source_catalog
        if isinstance(item, dict)
    }
    for expected_path, expected_hash in EXPECTED_SOURCE_BINDINGS.items():
        if source_path_hashes.get(expected_path) != expected_hash:
            issues.append(
                _issue(
                    "SOURCE_CATALOG_BINDING",
                    "$.sourceCatalog",
                    f"missing or changed required source: {expected_path}",
                )
            )
    for source_id, expected_path in (
        ("baseline-contract", "C_Semantic_Treehouse/manifests/baseline-test-cases.json"),
        ("frozen-files", "docs/provenance/manifests/frozen-files-SHA256SUMS"),
    ):
        source = sources.get(source_id)
        if not isinstance(source, dict) or source.get("path") != expected_path:
            issues.append(
                _issue(
                    "SOURCE_CATALOG_ID_BINDING",
                    "$.sourceCatalog",
                    f"{source_id} must bind {expected_path}",
                )
            )
    d_source = sources.get("d-shape-v04")
    if not isinstance(d_source, dict) or (
        d_source.get("path"), d_source.get("sha256")
    ) != (
        "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl",
        EXPECTED_SOURCE_BINDINGS[
            "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl"
        ],
    ):
        issues.append(
            _issue(
                "D_SOURCE_BINDING",
                "$.sourceCatalog",
                "d-shape-v04 must bind the frozen D-group TTL",
            )
        )

    suite_registry = document.get("validationSuiteRegistry", {})
    if isinstance(suite_registry, dict):
        _verify_file_binding(
            root,
            suite_registry.get("path"),
            suite_registry.get("sha256"),
            "$.validationSuiteRegistry",
            issues,
        )
        if suite_registry.get("path") != VALIDATION_SUITES_RELPATH:
            issues.append(_issue("SUITE_REGISTRY_PATH", "$.validationSuiteRegistry.path", "unexpected suite registry path"))
        suite_path, _ = _safe_repo_path(root, suite_registry.get("path"))
        if suite_path is not None and suite_path.is_file():
            try:
                suite_value = _load_json(suite_path)
            except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateKey):
                suite_value = None
            if isinstance(suite_value, dict) and suite_registry.get("contractVersion") != suite_value.get("contract_version"):
                issues.append(_issue("SUITE_CONTRACT_VERSION_MISMATCH", "$.validationSuiteRegistry.contractVersion", "contract version differs from registry"))

    requirement_catalog = document.get("requirementRegistries", [])
    requirement_ids = [
        item.get("id") for item in requirement_catalog if isinstance(item, dict)
    ]
    for duplicate in _duplicates(requirement_ids):
        issues.append(_issue("DUPLICATE_REQUIREMENT_REGISTRY_ID", "$.requirementRegistries", str(duplicate)))
    requirements = {
        item["id"]: item
        for item in requirement_catalog
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and requirement_ids.count(item["id"]) == 1
    }
    for index, requirement in enumerate(requirement_catalog):
        if not isinstance(requirement, dict):
            continue
        _verify_file_binding(root, requirement.get("path"), requirement.get("sha256"), f"$.requirementRegistries[{index}]", issues)
        if requirement.get("phase03Sha256") != EXPECTED_PHASE03_REQUIREMENTS_SHA256:
            issues.append(_issue("PHASE03_REQUIREMENTS_HASH", f"$.requirementRegistries[{index}].phase03Sha256", "unexpected Phase 03 registry SHA-256"))
    if len(requirements) != 1 or not any(
        item.get("path") == REQUIREMENTS_RELPATH
        for item in requirements.values()
    ):
        issues.append(_issue("REQUIREMENT_REGISTRY_SET", "$.requirementRegistries", "exactly the v0.4 requirements registry is required"))

    artifact_by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    artifact_ids: list[str] = []
    path_hashes: dict[str, set[str]] = {}
    inheritance_edges = {release_id: set() for release_id in release_by_id}
    requirement_documents: dict[str, set[str]] = {}
    for requirement_id, requirement in requirements.items():
        path, _ = _safe_repo_path(root, requirement.get("path"))
        if path is None or not path.is_file():
            continue
        try:
            value = _load_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateKey):
            continue
        if isinstance(value, dict):
            requirement_documents[requirement_id] = {
                item.get("id")
                for item in value.get("requirements", [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }

    release_roots = {
        release_id: str(release.get("root", ""))
        for release_id, release in release_by_id.items()
    }
    for release_index, release in enumerate(releases):
        if not isinstance(release, dict):
            continue
        release_id = release.get("id")
        for reference in release.get("normativeInputRefs", []):
            if reference not in sources:
                issues.append(_issue("DANGLING_SOURCE_REFERENCE", f"$.releases[{release_index}].normativeInputRefs", str(reference)))
        validators = release.get("applicableValidatorRefs", [])
        for reference in validators:
            if reference not in EXPECTED_VALIDATOR_IDS:
                issues.append(_issue("DANGLING_VALIDATOR_REFERENCE", f"$.releases[{release_index}].applicableValidatorRefs", str(reference)))
        for reference_index, reference in enumerate(
            release.get("requirementRegistryRefs", [])
        ):
            location = (
                f"$.releases[{release_index}].requirementRegistryRefs"
                f"[{reference_index}]"
            )
            if not isinstance(reference, dict):
                continue
            registry_ref = reference.get("registryRef")
            if registry_ref not in requirements:
                issues.append(
                    _issue(
                        "DANGLING_REQUIREMENT_REFERENCE",
                        f"{location}.registryRef",
                        str(registry_ref),
                    )
                )
                continue
            requirement_ids_value = reference.get("requirementIds", [])
            known_ids = requirement_documents.get(registry_ref, set())
            for requirement_id in requirement_ids_value:
                if requirement_id not in known_ids:
                    issues.append(
                        _issue(
                            "DANGLING_REQUIREMENT_ID",
                            f"{location}.requirementIds",
                            str(requirement_id),
                        )
                    )
        for artifact_index, artifact in enumerate(release.get("artifacts", [])):
            if not isinstance(artifact, dict):
                continue
            artifact_id = artifact.get("id")
            artifact_ids.append(artifact_id)
            if isinstance(artifact_id, str) and artifact_id not in artifact_by_id:
                artifact_by_id[artifact_id] = (str(release_id), artifact)
            location = f"$.releases[{release_index}].artifacts[{artifact_index}]"
            _verify_file_binding(root, artifact.get("path"), artifact.get("sha256"), location, issues)
            if artifact.get("path") == MANIFEST_RELPATH:
                issues.append(
                    _issue(
                        "MANIFEST_SELF_REFERENCE",
                        f"{location}.path",
                        MANIFEST_RELPATH,
                    )
                )
            if isinstance(artifact.get("path"), str) and isinstance(artifact.get("sha256"), str):
                path_hashes.setdefault(artifact["path"], set()).add(artifact["sha256"])
    for duplicate in _duplicates(artifact_ids):
        issues.append(_issue("DUPLICATE_ARTIFACT_ID", "$.releases[*].artifacts", str(duplicate)))
    for path, hashes in sorted(path_hashes.items()):
        if len(hashes) > 1:
            issues.append(_issue("SAME_PATH_HASH_CONFLICT", "$.releases[*].artifacts", path))

    for release in releases:
        if not isinstance(release, dict) or release.get("id") not in {
            "v0.1",
            "v0.2",
            "v0.3",
        }:
            continue
        for artifact in release.get("artifacts", []):
            if not isinstance(artifact, dict):
                continue
            origin = artifact.get("origin")
            verified_by = (
                origin.get("verifiedBy", []) if isinstance(origin, dict) else []
            )
            if not (
                isinstance(origin, dict)
                and origin.get("type") == "frozen"
                and isinstance(verified_by, list)
                and {"baseline-contract", "frozen-files"}.issubset(verified_by)
            ):
                issues.append(
                    _issue(
                        "HISTORICAL_ARTIFACT_ORIGIN",
                        f"$.artifact[{artifact.get('id')}].origin",
                        "historical artifact must be frozen and verified by baseline-contract and frozen-files",
                    )
                )

    derivation_edges = {artifact_id: set() for artifact_id in artifact_by_id}
    for artifact_id, (release_id, artifact) in sorted(artifact_by_id.items()):
        origin = artifact.get("origin")
        if not isinstance(origin, dict):
            continue
        origin_type = origin.get("type")
        if origin_type == "derived":
            artifact_path = artifact.get("path")
            release_root = release_roots.get(release_id, "")
            if not isinstance(artifact_path, str) or not artifact_path.startswith(
                release_root + "/"
            ):
                issues.append(
                    _issue(
                        "ARTIFACT_OUTSIDE_RELEASE_ROOT",
                        f"$.artifact[{artifact_id}].path",
                        str(artifact_path),
                    )
                )
            for index, source in enumerate(origin.get("sources", [])):
                if not isinstance(source, dict):
                    continue
                kind = source.get("kind")
                reference = source.get("ref")
                target: dict[str, Any] | None = None
                if kind == "input":
                    target = sources.get(reference)
                    code = "DANGLING_SOURCE_REFERENCE"
                elif kind == "artifact":
                    target_pair = artifact_by_id.get(reference)
                    target = target_pair[1] if target_pair else None
                    code = "DANGLING_ARTIFACT_SOURCE_REFERENCE"
                else:
                    code = "UNKNOWN_SOURCE_KIND"
                location = f"$.artifact[{artifact_id}].origin.sources[{index}]"
                if target is None:
                    issues.append(_issue(code, location, str(reference)))
                elif source.get("path") != target.get("path") or source.get("sha256") != target.get("sha256"):
                    issues.append(_issue("SOURCE_BINDING_MISMATCH", location, str(reference)))
                if kind == "artifact" and reference == artifact_id:
                    issues.append(_issue("DERIVATION_SELF_REFERENCE", location, str(reference)))
                if kind == "artifact" and isinstance(reference, str):
                    derivation_edges.setdefault(artifact_id, set()).add(reference)
                if source.get("path") == MANIFEST_RELPATH:
                    issues.append(
                        _issue(
                            "MANIFEST_SELF_REFERENCE",
                            f"{location}.path",
                            MANIFEST_RELPATH,
                        )
                    )
        elif origin_type == "frozen":
            artifact_path = artifact.get("path")
            release_root = release_roots.get(release_id, "")
            if not isinstance(artifact_path, str) or not artifact_path.startswith(
                release_root + "/"
            ):
                issues.append(
                    _issue(
                        "ARTIFACT_OUTSIDE_RELEASE_ROOT",
                        f"$.artifact[{artifact_id}].path",
                        str(artifact_path),
                    )
                )
            for reference in origin.get("verifiedBy", []):
                if reference not in sources:
                    issues.append(
                        _issue(
                            "DANGLING_VERIFICATION_REFERENCE",
                            f"$.artifact[{artifact_id}].origin.verifiedBy",
                            str(reference),
                        )
                    )
        elif origin_type == "inherited":
            inherited_from = origin.get("inheritedFrom")
            source_artifact = origin.get("sourceArtifact")
            source_pair = artifact_by_id.get(source_artifact)
            if inherited_from not in release_by_id:
                issues.append(_issue("DANGLING_INHERITED_RELEASE", f"$.artifact[{artifact_id}].origin.inheritedFrom", str(inherited_from)))
            else:
                inheritance_edges.setdefault(release_id, set()).add(inherited_from)
            if source_pair is None or source_pair[0] != inherited_from:
                issues.append(_issue("DANGLING_INHERITED_ARTIFACT", f"$.artifact[{artifact_id}].origin.sourceArtifact", str(source_artifact)))
            elif artifact.get("path") != source_pair[1].get("path") or artifact.get("sha256") != source_pair[1].get("sha256"):
                issues.append(_issue("INHERITED_HASH_DRIFT", f"$.artifact[{artifact_id}]", str(source_artifact)))
            elif not str(artifact.get("path", "")).startswith(
                release_roots.get(str(inherited_from), "") + "/"
            ):
                issues.append(
                    _issue(
                        "INHERITED_PATH_OUTSIDE_SOURCE_ROOT",
                        f"$.artifact[{artifact_id}].path",
                        str(artifact.get("path")),
                    )
                )
    issues.extend(
        _cycle_issues(
            derivation_edges,
            "DERIVATION_CYCLE",
            "$.releases[*].artifacts[*].origin.sources",
        )
    )
    issues.extend(_cycle_issues(inheritance_edges, "INHERITANCE_CYCLE", "$.releases"))

    v04 = release_by_id.get("v0.4", {})
    if v04.get("normativeInputRefs") != ["d-shape-v04"]:
        issues.append(
            _issue(
                "V04_NORMATIVE_INPUT_SET",
                "$.releases[v0.4].normativeInputRefs",
                "v0.4 must bind only d-shape-v04 as normative input",
            )
        )
    v04_requirement_refs = v04.get("requirementRegistryRefs", [])
    if not (
        isinstance(v04_requirement_refs, list)
        and len(v04_requirement_refs) == 1
        and isinstance(v04_requirement_refs[0], dict)
        and v04_requirement_refs[0].get("registryRef") == "v04-requirements"
        and v04_requirement_refs[0].get("requirementIds")
        == list(EXPECTED_REQUIREMENT_IDS)
    ):
        issues.append(
            _issue(
                "V04_REQUIREMENT_COVERAGE",
                "$.releases[v0.4].requirementRegistryRefs",
                "v0.4 must cover D04-R001 through D04-R017 in order",
            )
        )
    native_v04 = {
        artifact.get("path"): artifact.get("role")
        for artifact in v04.get("artifacts", [])
        if isinstance(artifact, dict)
        and isinstance(artifact.get("origin"), dict)
        and artifact["origin"].get("type") != "inherited"
    }
    if native_v04 != EXPECTED_V04_NATIVE_ARTIFACTS:
        issues.append(
            _issue(
                "V04_NATIVE_ARTIFACT_SET",
                "$.releases[v0.4].artifacts",
                "v0.4 native release artifact paths/roles differ from the fixed six-item set",
            )
        )
    v04_by_path = {
        artifact.get("path"): artifact
        for artifact in v04.get("artifacts", [])
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str)
    }
    for path, transformation in sorted(EXPECTED_V04_NATIVE_TRANSFORMATIONS.items()):
        artifact = v04_by_path.get(path)
        origin = artifact.get("origin") if isinstance(artifact, dict) else None
        if not (
            isinstance(origin, dict)
            and origin.get("type") == "derived"
            and origin.get("transformation") == transformation
        ):
            issues.append(
                _issue(
                    "V04_NATIVE_ORIGIN",
                    f"$.releases[v0.4].artifacts[{path}].origin",
                    f"expected derived/{transformation}",
                )
            )
    shape_path = "C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl"
    shape_artifact = v04_by_path.get(shape_path)
    shape_origin = (
        shape_artifact.get("origin") if isinstance(shape_artifact, dict) else None
    )
    expected_shape_sources = [
        {
            "kind": "input",
            "ref": "d-shape-v04",
            "path": "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl",
            "sha256": EXPECTED_SOURCE_BINDINGS[
                "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl"
            ],
        }
    ]
    if not isinstance(shape_origin, dict) or shape_origin.get("sources") != expected_shape_sources:
        issues.append(
            _issue(
                "V04_SHAPE_DERIVATION_SOURCE",
                "$.releases[v0.4].artifacts[metadata-shapes].origin.sources",
                "byte-copy Shape must bind only d-shape-v04 with the fixed D path/hash",
            )
        )
    checksum_path = "C_Semantic_Treehouse/model/v0.4/SHA256SUMS"
    checksum_artifact = v04_by_path.get(checksum_path)
    checksum_origin = (
        checksum_artifact.get("origin")
        if isinstance(checksum_artifact, dict)
        else None
    )
    checksum_sources = (
        checksum_origin.get("sources", []) if isinstance(checksum_origin, dict) else []
    )
    expected_checksum_bindings = {
        (artifact.get("id"), artifact.get("path"), artifact.get("sha256"))
        for path, artifact in v04_by_path.items()
        if path in EXPECTED_V04_NATIVE_ARTIFACTS and path != checksum_path
    }
    actual_checksum_bindings = {
        (source.get("ref"), source.get("path"), source.get("sha256"))
        for source in checksum_sources
        if isinstance(source, dict) and source.get("kind") == "artifact"
    }
    if (
        len(checksum_sources) != 5
        or actual_checksum_bindings != expected_checksum_bindings
        or len(expected_checksum_bindings) != 5
    ):
        issues.append(
            _issue(
                "V04_CHECKSUM_DERIVATION_SOURCES",
                "$.releases[v0.4].artifacts[checksum-manifest].origin.sources",
                "SHA256SUMS must bind exactly README and the four core model artifacts",
            )
        )
    inherited = {
        artifact.get("path"): artifact.get("sha256")
        for artifact in v04.get("artifacts", [])
        if isinstance(artifact, dict)
        and isinstance(artifact.get("origin"), dict)
        and artifact["origin"].get("type") == "inherited"
    }
    if inherited != EXPECTED_RECORD_INHERITANCE:
        issues.append(_issue("RECORD_INHERITANCE_SET", "$.releases[v0.4].artifacts", "v0.4 must inherit exactly the five ADR-003 record artifacts"))
    if "C_Semantic_Treehouse/model/v0.3/openapi-fragment.yaml" in inherited:
        issues.append(_issue("OPENAPI_MUST_REMAIN_FROZEN", "$.releases[v0.4].artifacts", "v0.3 OpenAPI is frozen historical inventory, not inherited"))

    historical_issues, historical = _historical_baseline_issues(root, releases)
    issues.extend(historical_issues)
    record = {
        "release_ids": release_ids,
        "current_release": current,
        "source_ids": source_ids,
        "requirement_registry_ids": requirement_ids,
        "artifact_ids": sorted(item for item in artifact_ids if isinstance(item, str)),
        "artifact_count": len(artifact_ids),
        "record_inheritance": [
            {"path": path, "sha256": inherited[path]}
            for path in sorted(inherited)
        ],
        "historical_baseline": historical,
    }
    return issues, record


@dataclass(frozen=True)
class ReleaseManifestAudit:
    manifest_path: Path
    schema_path: Path
    manifest: dict[str, Any] | None
    manifest_sha256: str | None
    schema_sha256: str | None
    issues: tuple[dict[str, str], ...]
    semantic_record: dict[str, Any]

    @property
    def ok(self) -> bool:
        return self.manifest is not None and not self.issues

    def deterministic_record(self) -> dict[str, Any]:
        return {
            "manifest_path": MANIFEST_RELPATH,
            "manifest_sha256": self.manifest_sha256,
            "schema_path": SCHEMA_RELPATH,
            "schema_sha256": self.schema_sha256,
            "manifest_schema_version": (
                self.manifest.get("manifest_schema_version")
                if self.manifest is not None
                else None
            ),
            **self.semantic_record,
            "issues": list(self.issues),
        }


def load_and_audit_release_manifest(
    root: Path,
    *,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
) -> ReleaseManifestAudit:
    """Load and fully audit a release manifest without rewriting it."""
    root = root.resolve()
    manifest_path = manifest_path or release_manifest_path(root)
    schema_path = schema_path or release_manifest_schema_path(root)
    issues: list[dict[str, str]] = []
    manifest: dict[str, Any] | None = None
    schema: Any = None

    if not schema_path.is_file():
        issues.append(_issue("MISSING_SCHEMA", "$schema", "release manifest schema is missing"))
    else:
        try:
            schema = _load_json(schema_path)
        except _DuplicateKey as exc:
            issues.append(_issue("DUPLICATE_JSON_KEY", "$schema", str(exc)))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(_issue("SCHEMA_PARSE", "$schema", str(exc)))

    if not manifest_path.is_file():
        issues.append(_issue("MISSING_MANIFEST", "$", "release manifest is missing"))
    else:
        try:
            value = _load_json(manifest_path)
        except _DuplicateKey as exc:
            issues.append(_issue("DUPLICATE_JSON_KEY", "$", str(exc)))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(_issue("MANIFEST_PARSE", "$", str(exc)))
        else:
            if not isinstance(value, dict):
                issues.append(_issue("MANIFEST_ROOT", "$", "manifest root must be an object"))
            else:
                manifest = value

    semantic_record: dict[str, Any] = {}
    if manifest is not None:
        if schema is not None:
            issues.extend(_schema_issues(schema, manifest))
        try:
            semantic_errors, semantic_record = _semantic_issues(manifest, root)
            issues.extend(semantic_errors)
        except Exception as exc:  # noqa: BLE001 - malformed controls fail closed
            issues.append(
                _issue(
                    "SEMANTIC_AUDIT_ERROR",
                    "$",
                    f"{exc.__class__.__name__}: release semantic audit failed",
                )
            )

    return ReleaseManifestAudit(
        manifest_path=manifest_path,
        schema_path=schema_path,
        manifest=manifest,
        manifest_sha256=(sha256_file(manifest_path) if manifest_path.is_file() else None),
        schema_sha256=(sha256_file(schema_path) if schema_path.is_file() else None),
        issues=_sorted_issues(issues),
        semantic_record=semantic_record,
    )


__all__ = [
    "EXPECTED_PHASE03_REQUIREMENTS_SHA256",
    "EXPECTED_RECORD_INHERITANCE",
    "EXPECTED_RELEASE_IDS",
    "EXPECTED_VALIDATOR_IDS",
    "MANIFEST_RELPATH",
    "REQUIREMENTS_RELPATH",
    "ReleaseManifestAudit",
    "SCHEMA_RELPATH",
    "VALIDATION_SUITES_RELPATH",
    "load_and_audit_release_manifest",
    "release_manifest_path",
    "release_manifest_schema_path",
]
