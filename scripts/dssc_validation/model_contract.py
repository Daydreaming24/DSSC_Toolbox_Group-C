"""Deterministic Phase 04 release-model audit and contract smoke."""

from __future__ import annotations

import copy
import json
import re
import shutil
import tempfile
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any

from dssc_validation.d_group_contract import (
    D_TTL_RELPATH,
    INVALID_SAMPLE_RELPATH,
    run_meta_shacl,
)
from dssc_validation.hashing import sha256_file, sha256_text
from dssc_validation.lock_contract import canonical_name, parse_hash_lock
from dssc_validation.model_validation import (
    ModelValidationError,
    graph_from_expanded_jsonld,
    offline_expand_jsonld,
    parse_turtle,
    run_shacl_validation,
)
from dssc_validation.release_manifest import (
    EXPECTED_RECORD_INHERITANCE,
    ReleaseManifestAudit,
)


MODEL_ROOT = "C_Semantic_Treehouse/model/v0.4"
ONTOLOGY_RELPATH = f"{MODEL_ROOT}/building-energy-ontology.ttl"
SHAPES_RELPATH = f"{MODEL_ROOT}/data-product-metadata-shapes.ttl"
CONTEXT_RELPATH = f"{MODEL_ROOT}/data-product-context.jsonld"
VALID_RELPATH = f"{MODEL_ROOT}/data-product-valid.jsonld"
README_RELPATH = f"{MODEL_ROOT}/README.md"
SHA256SUMS_RELPATH = f"{MODEL_ROOT}/SHA256SUMS"
MODEL_IMPLEMENTATION_RELPATH = "scripts/dssc_validation/model_contract.py"

EXPECTED_PHASE03_SEMANTIC_SHA256 = (
    "8a6d4bee6c06623915e4fa2664d465b666e087db9caf0b315ef2f5831bd0e3fe"
)
EXPECTED_PHASE03_SEMANTIC_SIZE = 79254
EXPECTED_REQUIREMENT_IDS = tuple(f"D04-R{index:03d}" for index in range(1, 18))

_SHA256 = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
_SUM_LINE = re.compile(r"^(?P<sha>[0-9a-f]{64})  (?P<path>[^\r\n]+)$")

_REQUIRED_IMPLEMENTATION_PATHS: dict[str, tuple[str, ...]] = {
    "D04-R001": (SHAPES_RELPATH,),
    "D04-R002": (SHAPES_RELPATH, CONTEXT_RELPATH),
    "D04-R003": (SHAPES_RELPATH, ONTOLOGY_RELPATH, CONTEXT_RELPATH),
    "D04-R004": (SHAPES_RELPATH, CONTEXT_RELPATH),
    "D04-R005": (SHAPES_RELPATH, ONTOLOGY_RELPATH, CONTEXT_RELPATH),
    "D04-R006": (SHAPES_RELPATH, CONTEXT_RELPATH),
    "D04-R007": (SHAPES_RELPATH, CONTEXT_RELPATH),
    "D04-R008": (SHAPES_RELPATH, ONTOLOGY_RELPATH, CONTEXT_RELPATH),
    "D04-R009": (SHAPES_RELPATH, CONTEXT_RELPATH),
    "D04-R010": (SHAPES_RELPATH, CONTEXT_RELPATH),
    "D04-R011": (SHAPES_RELPATH, ONTOLOGY_RELPATH, CONTEXT_RELPATH),
    "D04-R012": (SHAPES_RELPATH, ONTOLOGY_RELPATH, CONTEXT_RELPATH),
    "D04-R013": (SHAPES_RELPATH, ONTOLOGY_RELPATH, CONTEXT_RELPATH),
    "D04-R014": (SHAPES_RELPATH, CONTEXT_RELPATH),
    "D04-R015": (SHAPES_RELPATH, CONTEXT_RELPATH),
    "D04-R016": (SHAPES_RELPATH, ONTOLOGY_RELPATH, CONTEXT_RELPATH),
    "D04-R017": (SHAPES_RELPATH, MODEL_IMPLEMENTATION_RELPATH),
}


def _issue(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def _sorted_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    unique = {
        (item["code"], item["location"], item["message"]): item
        for item in issues
    }
    return [unique[key] for key in sorted(unique)]


def _repo_path(root: Path, relpath: str) -> Path:
    return root / Path(*PurePosixPath(relpath).parts)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def requirements_semantic_projection(document: dict[str, Any]) -> dict[str, Any]:
    """Return the Phase 03 semantic surface, excluding implementation only."""
    projection = copy.deepcopy(document)
    requirements = projection.get("requirements", [])
    for requirement in requirements:
        if isinstance(requirement, dict):
            requirement.pop("implementation", None)
    return projection


def requirements_semantic_projection_record(
    document: dict[str, Any],
) -> dict[str, Any]:
    payload = _canonical_json_bytes(requirements_semantic_projection(document))
    return {
        "algorithm": (
            "remove $.requirements[*].implementation; canonical JSON UTF-8 "
            "sort_keys=true,separators=(',',':'),ensure_ascii=false; LF"
        ),
        "expected_phase03_sha256": EXPECTED_PHASE03_SEMANTIC_SHA256,
        "expected_phase03_size_bytes": EXPECTED_PHASE03_SEMANTIC_SIZE,
        "actual_sha256": sha256_text(payload.decode("utf-8")),
        "actual_size_bytes": len(payload),
        "unchanged": (
            sha256_text(payload.decode("utf-8"))
            == EXPECTED_PHASE03_SEMANTIC_SHA256
            and len(payload) == EXPECTED_PHASE03_SEMANTIC_SIZE
        ),
    }


def _v04_release_artifacts(
    release_manifest: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(release_manifest, dict):
        return {}
    for release in release_manifest.get("releases", []):
        if isinstance(release, dict) and release.get("id") == "v0.4":
            return {
                item["path"]: item
                for item in release.get("artifacts", [])
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            }
    return {}


def audit_requirements_implementation(
    root: Path,
    document: dict[str, Any] | None,
    release_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    """Check Phase 04 paths/hash descriptions without changing Phase 03 semantics."""
    issues: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return {
            "status": "ERROR",
            "semantic_projection": {},
            "requirements": [],
            "issues": [
                _issue(
                    "REQUIREMENTS_UNAVAILABLE",
                    "$",
                    "requirements registry is unavailable",
                )
            ],
        }
    projection = requirements_semantic_projection_record(document)
    if not projection["unchanged"]:
        issues.append(
            _issue(
                "SEMANTIC_PROJECTION_MISMATCH",
                "$.requirements",
                "Phase 03 fields outside implementation changed",
            )
        )
    requirements = document.get("requirements", [])
    requirement_ids = [
        item.get("id") for item in requirements if isinstance(item, dict)
    ]
    if tuple(requirement_ids) != EXPECTED_REQUIREMENT_IDS:
        issues.append(
            _issue(
                "REQUIREMENT_SET_OR_ORDER",
                "$.requirements",
                "expected D04-R001 through D04-R017",
            )
        )
    release_artifacts = _v04_release_artifacts(release_manifest)
    records: list[dict[str, Any]] = []
    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, dict):
            continue
        requirement_id = requirement.get("id")
        location = f"$.requirements[{index}].implementation"
        implementation = requirement.get("implementation")
        if not isinstance(implementation, dict):
            issues.append(
                _issue(
                    "IMPLEMENTATION_COVERAGE_MISSING",
                    location,
                    str(requirement_id),
                )
            )
            continue
        if implementation.get("status") != "PLANNED":
            issues.append(
                _issue(
                    "IMPLEMENTATION_STATUS",
                    f"{location}.status",
                    "overall status must remain PLANNED until Phase 05",
                )
            )
        fixture_refs = implementation.get("fixture_refs", [])
        evidence_refs = implementation.get("evidence_refs", [])
        for collection_name, references in (
            ("fixture_refs", fixture_refs),
            ("evidence_refs", evidence_refs),
        ):
            if not references or any(
                not isinstance(item, dict)
                or item.get("status") != "PLANNED"
                or item.get("phase") != "05"
                or item.get("path") is not None
                for item in references
            ):
                issues.append(
                    _issue(
                        "PHASE05_REFERENCE_CHANGED",
                        f"{location}.{collection_name}",
                        "Phase 05 fixture/evidence refs must remain PLANNED/null",
                    )
                )
        implemented: dict[str, dict[str, Any]] = {}
        for reference_index, reference in enumerate(
            implementation.get("artifact_refs", [])
        ):
            if not isinstance(reference, dict) or reference.get("status") != "IMPLEMENTED":
                continue
            path_value = reference.get("path")
            reference_location = f"{location}.artifact_refs[{reference_index}]"
            if not isinstance(path_value, str):
                issues.append(
                    _issue(
                        "IMPLEMENTATION_ARTIFACT_DANGLING",
                        f"{reference_location}.path",
                        "implemented artifact path is missing",
                    )
                )
                continue
            path = _repo_path(root, path_value)
            if not path.is_file() or path.stat().st_size == 0:
                issues.append(
                    _issue(
                        "IMPLEMENTATION_ARTIFACT_DANGLING",
                        f"{reference_location}.path",
                        path_value,
                    )
                )
                continue
            actual_hash = sha256_file(path)
            description = reference.get("description", "")
            hashes = {
                value.lower() for value in _SHA256.findall(str(description))
            }
            if actual_hash not in hashes:
                issues.append(
                    _issue(
                        "IMPLEMENTATION_HASH_MISMATCH",
                        f"{reference_location}.description",
                        f"description must bind {actual_hash}",
                    )
                )
            if reference.get("phase") != "04":
                issues.append(
                    _issue(
                        "IMPLEMENTATION_PHASE",
                        f"{reference_location}.phase",
                        "implemented model artifact must belong to Phase 04",
                    )
                )
            if path_value != MODEL_IMPLEMENTATION_RELPATH:
                release_artifact = release_artifacts.get(path_value)
                if release_artifact is None:
                    issues.append(
                        _issue(
                            "IMPLEMENTATION_RELEASE_BINDING_MISSING",
                            f"{reference_location}.path",
                            path_value,
                        )
                    )
                elif release_artifact.get("sha256") != actual_hash:
                    issues.append(
                        _issue(
                            "IMPLEMENTATION_RELEASE_HASH_MISMATCH",
                            f"{reference_location}.path",
                            path_value,
                        )
                    )
            if path_value in implemented:
                issues.append(
                    _issue(
                        "DUPLICATE_IMPLEMENTATION_ARTIFACT",
                        f"{reference_location}.path",
                        path_value,
                    )
                )
            implemented[path_value] = {
                "path": path_value,
                "sha256": actual_hash,
            }
        required = set(_REQUIRED_IMPLEMENTATION_PATHS.get(str(requirement_id), ()))
        missing = sorted(required - set(implemented))
        if missing:
            issues.append(
                _issue(
                    "IMPLEMENTATION_COVERAGE_MISSING",
                    f"{location}.artifact_refs",
                    f"{requirement_id} missing {missing}",
                )
            )
        records.append(
            {
                "id": requirement_id,
                "overall_status": implementation.get("status"),
                "implemented_artifacts": [
                    implemented[path] for path in sorted(implemented)
                ],
                "required_artifacts": sorted(required),
                "coverage_complete": not missing,
            }
        )
    issues = _sorted_issues(issues)
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "semantic_projection": projection,
        "requirements": records,
        "issues": issues,
    }


def _parse_sha256sums(root: Path) -> dict[str, Any]:
    path = _repo_path(root, SHA256SUMS_RELPATH)
    issues: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []
    if not path.is_file() or path.stat().st_size == 0:
        return {
            "status": "ERROR",
            "path": SHA256SUMS_RELPATH,
            "records": [],
            "issues": [_issue("SHA256SUMS_MISSING", SHA256SUMS_RELPATH, "missing or empty")],
        }
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    paths: list[str] = []
    for index, line in enumerate(lines, start=1):
        match = _SUM_LINE.fullmatch(line)
        if match is None:
            issues.append(
                _issue("SHA256SUMS_FORMAT", f"{SHA256SUMS_RELPATH}:L{index}", "invalid checksum record")
            )
            continue
        relpath = match.group("path")
        expected = match.group("sha")
        paths.append(relpath)
        artifact = _repo_path(root, relpath)
        actual = sha256_file(artifact) if artifact.is_file() else None
        if actual != expected:
            issues.append(
                _issue("SHA256SUMS_HASH_MISMATCH", f"{SHA256SUMS_RELPATH}:L{index}", relpath)
            )
        records.append(
            {"path": relpath, "sha256": expected, "actual_sha256": actual}
        )
    expected_paths = sorted(
        {README_RELPATH, ONTOLOGY_RELPATH, SHAPES_RELPATH, CONTEXT_RELPATH, VALID_RELPATH}
    )
    if paths != sorted(paths) or paths != expected_paths:
        issues.append(
            _issue(
                "SHA256SUMS_SET_OR_ORDER",
                SHA256SUMS_RELPATH,
                "checksum paths must be the exact sorted five-artifact set",
            )
        )
    if SHA256SUMS_RELPATH in paths:
        issues.append(
            _issue("SHA256SUMS_SELF_REFERENCE", SHA256SUMS_RELPATH, "checksum file lists itself")
        )
    issues = _sorted_issues(issues)
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "path": SHA256SUMS_RELPATH,
        "sha256": sha256_file(path),
        "records": records,
        "issues": issues,
    }


def _shape_derivation(root: Path, release_manifest: dict[str, Any] | None) -> dict[str, Any]:
    source = _repo_path(root, D_TTL_RELPATH)
    target = _repo_path(root, SHAPES_RELPATH)
    issues: list[dict[str, str]] = []
    source_hash = sha256_file(source) if source.is_file() else None
    target_hash = sha256_file(target) if target.is_file() else None
    if source_hash != target_hash or (
        source.is_file() and target.is_file() and source.read_bytes() != target.read_bytes()
    ):
        issues.append(
            _issue("BYTE_COPY_MISMATCH", SHAPES_RELPATH, "release Shape differs from D source bytes")
        )
    artifact = _v04_release_artifacts(release_manifest).get(SHAPES_RELPATH)
    origin = artifact.get("origin") if isinstance(artifact, dict) else None
    if not isinstance(origin, dict) or origin.get("transformation") != "byte-copy":
        issues.append(
            _issue("BYTE_COPY_TRANSFORMATION", SHAPES_RELPATH, "manifest must declare byte-copy")
        )
    attribute_line = f"{SHAPES_RELPATH} -text"
    attributes = (root / ".gitattributes").read_text(encoding="utf-8-sig").splitlines()
    if attributes.count(attribute_line) != 1:
        issues.append(
            _issue("BYTE_COPY_GIT_ATTRIBUTE", ".gitattributes", "exact Shape -text rule is required once")
        )
    issues = _sorted_issues(issues)
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "source_path": D_TTL_RELPATH,
        "source_sha256": source_hash,
        "target_path": SHAPES_RELPATH,
        "target_sha256": target_hash,
        "byte_identical": source_hash is not None and source_hash == target_hash,
        "gitattributes_rule": attribute_line,
        "issues": issues,
    }


def _turtle_audit(root: Path) -> tuple[dict[str, Any], Any]:
    from rdflib import Literal, Namespace, URIRef
    from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

    issues: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []
    shapes_graph = None
    ontology_graph = None
    for relpath in (ONTOLOGY_RELPATH, SHAPES_RELPATH):
        try:
            graph = parse_turtle(_repo_path(root, relpath), relpath)
        except ModelValidationError as exc:
            issues.append(_issue("TURTLE_PARSE", relpath, str(exc)))
            continue
        records.append(
            {"path": relpath, "sha256": sha256_file(_repo_path(root, relpath)), "triple_count": len(graph)}
        )
        if relpath == SHAPES_RELPATH:
            shapes_graph = graph
        elif relpath == ONTOLOGY_RELPATH:
            ontology_graph = graph
    if shapes_graph is None:
        issues.append(_issue("SHAPES_UNAVAILABLE", SHAPES_RELPATH, "cannot run model smoke"))
    ontology_assertions: list[dict[str, Any]] = []
    if ontology_graph is None:
        issues.append(
            _issue("ONTOLOGY_UNAVAILABLE", ONTOLOGY_RELPATH, "cannot audit ontology semantics")
        )
    else:
        ontology = URIRef("https://w3id.org/dssc-demo/building-energy/v0.4")
        prior = URIRef("https://w3id.org/dssc-demo/building-energy/v0.3")
        ex = Namespace("https://example.org/dssc-energy#")
        expected_metadata = {
            "ontology_type": (ontology, RDF.type, OWL.Ontology),
            "version_iri": (ontology, OWL.versionIRI, ontology),
            "prior_version": (ontology, OWL.priorVersion, prior),
            "version_info": (ontology, OWL.versionInfo, Literal("0.4")),
            "created": (ontology, DCTERMS.created, Literal("2026-08-10", datatype=XSD.date)),
            "title": (
                ontology,
                DCTERMS.title,
                Literal("Building Energy Semantic Model v0.4"),
            ),
            "breaking_description": (
                ontology,
                DCTERMS.description,
                Literal(
                    "Breaking metadata wire-profile migration to the D-group "
                    "dcat:Dataset contract. The v0.3 Energy Reading Record "
                    "sub-contract is unchanged and inherited through the release manifest."
                ),
            ),
        }
        for name, triple in sorted(expected_metadata.items()):
            passed = triple in ontology_graph
            ontology_assertions.append(
                {"name": name, "expected": True, "actual": passed, "passed": passed}
            )
            if not passed:
                issues.append(
                    _issue("ONTOLOGY_IDENTITY_MISMATCH", ONTOLOGY_RELPATH, name)
                )

        expected_properties = {
            ex.datasetId: XSD.string,
            ex.providerName: XSD.string,
            ex.unit: XSD.string,
            ex.temporalStart: XSD.date,
            ex.temporalEnd: XSD.date,
        }
        local_iris = {
            term
            for triple in ontology_graph
            for term in triple
            if isinstance(term, URIRef) and str(term).startswith(str(ex))
        }
        local_set_ok = local_iris == set(expected_properties)
        ontology_assertions.append(
            {
                "name": "exact_local_property_set",
                "expected": sorted(map(str, expected_properties)),
                "actual": sorted(map(str, local_iris)),
                "passed": local_set_ok,
            }
        )
        if not local_set_ok:
            issues.append(
                _issue(
                    "ONTOLOGY_LOCAL_PROPERTY_SET",
                    ONTOLOGY_RELPATH,
                    "expected exactly five D wire local properties",
                )
            )
        for prop, range_iri in sorted(expected_properties.items(), key=lambda item: str(item[0])):
            passed = all(
                triple in ontology_graph
                for triple in (
                    (prop, RDF.type, OWL.DatatypeProperty),
                    (prop, RDFS.domain, URIRef("http://www.w3.org/ns/dcat#Dataset")),
                    (prop, RDFS.range, range_iri),
                )
            )
            ontology_assertions.append(
                {
                    "name": f"property_contract:{prop}",
                    "expected": {"type": str(OWL.DatatypeProperty), "domain": "http://www.w3.org/ns/dcat#Dataset", "range": str(range_iri)},
                    "actual": passed,
                    "passed": passed,
                }
            )
            if not passed:
                issues.append(
                    _issue("ONTOLOGY_PROPERTY_CONTRACT", ONTOLOGY_RELPATH, str(prop))
                )
        be_namespace = "https://w3id.org/dssc-demo/building-energy#"
        adapter_terms = sorted(
            {
                str(term)
                for triple in ontology_graph
                for term in triple
                if isinstance(term, URIRef) and str(term).startswith(be_namespace)
            }
        )
        adapter_predicates = sorted(
            str(predicate)
            for predicate in (RDFS.subPropertyOf, OWL.equivalentProperty)
            if any(ontology_graph.triples((None, predicate, None)))
        )
        no_adapter = not adapter_terms and not adapter_predicates
        ontology_assertions.append(
            {
                "name": "no_namespace_adapter",
                "expected": {"be_terms": [], "adapter_predicates": []},
                "actual": {"be_terms": adapter_terms, "adapter_predicates": adapter_predicates},
                "passed": no_adapter,
            }
        )
        if not no_adapter:
            issues.append(
                _issue(
                    "ONTOLOGY_NAMESPACE_ADAPTER",
                    ONTOLOGY_RELPATH,
                    "be:/subProperty/equivalentProperty adapter is forbidden",
                )
            )
    issues = _sorted_issues(issues)
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "artifacts": records,
        "ontology_assertions": ontology_assertions,
        "issues": issues,
    }, shapes_graph


def _jsonld_audit(root: Path) -> tuple[dict[str, Any], Any]:
    from rdflib import Literal, Namespace, URIRef
    from rdflib.namespace import RDF, XSD

    issues: list[dict[str, str]] = []
    graph = None
    expansion_record: dict[str, Any] = {}
    context_assertions: list[dict[str, Any]] = []
    graph_assertions: list[dict[str, Any]] = []
    expected_context = {
        "ex": "https://example.org/dssc-energy#",
        "dcat": "http://www.w3.org/ns/dcat#",
        "dct": "http://purl.org/dc/terms/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "Dataset": "dcat:Dataset",
        "datasetId": "ex:datasetId",
        "title": "dct:title",
        "description": "dct:description",
        "providerName": "ex:providerName",
        "license": {"@id": "dct:license", "@type": "@id"},
        "spatial": "dct:spatial",
        "frequency": "dct:accrualPeriodicity",
        "unit": "ex:unit",
        "temporalStart": {"@id": "ex:temporalStart", "@type": "xsd:date"},
        "temporalEnd": {"@id": "ex:temporalEnd", "@type": "xsd:date"},
        "endpointUrl": {"@id": "dcat:endpointURL", "@type": "@id"},
        "format": "dct:format",
    }
    try:
        context_document = _read_json(_repo_path(root, CONTEXT_RELPATH))
    except Exception as exc:  # noqa: BLE001 - recorded below as a stable issue
        context_document = None
        issues.append(_issue("CONTEXT_PARSE", CONTEXT_RELPATH, exc.__class__.__name__))
    context_mapping = (
        context_document.get("@context") if isinstance(context_document, dict) else None
    )
    exact_context = (
        context_document == {"@context": expected_context}
        and "conformsTo" not in expected_context
        and "dct:conformsTo" not in expected_context
    )
    context_assertions.append(
        {
            "name": "exact_term_mapping_and_coercion",
            "expected": expected_context,
            "actual": context_mapping,
            "passed": exact_context,
        }
    )
    if not exact_context:
        issues.append(
            _issue(
                "CONTEXT_MAPPING_MISMATCH",
                CONTEXT_RELPATH,
                "context terms/coercions must equal the fixed D wire mapping",
            )
        )
    try:
        expanded, expansion_record = offline_expand_jsonld(
            _repo_path(root, VALID_RELPATH),
            VALID_RELPATH,
            [(_repo_path(root, CONTEXT_RELPATH), CONTEXT_RELPATH)],
        )
        graph = graph_from_expanded_jsonld(
            expanded, "https://dssc.local/repository/" + VALID_RELPATH
        )
    except ModelValidationError as exc:
        issues.append(_issue("JSONLD_OFFLINE_EXPANSION", VALID_RELPATH, str(exc)))
    datasets: list[Any] = []
    if graph is not None:
        dcat = Namespace("http://www.w3.org/ns/dcat#")
        dct = Namespace("http://purl.org/dc/terms/")
        ex = Namespace("https://example.org/dssc-energy#")
        datasets = sorted(set(graph.subjects(RDF.type, dcat.Dataset)), key=str)
        if len(datasets) != 1 or not isinstance(datasets[0], URIRef):
            issues.append(
                _issue("CANONICAL_DATASET_CARDINALITY", VALID_RELPATH, "expected exactly one IRI dcat:Dataset")
            )
        elif any(graph.objects(datasets[0], dct.conformsTo)):
            issues.append(
                _issue("CANONICAL_CONFORMS_TO", VALID_RELPATH, "canonical Dataset must omit dct:conformsTo")
            )
        dataset = URIRef(
            "https://example.org/dssc-energy/datasets/building-energy-hourly-v1"
        )
        expected_graph = {
            (dataset, RDF.type, dcat.Dataset),
            (dataset, ex.datasetId, Literal("building-energy-hourly-v1")),
            (dataset, dct.title, Literal("Building Energy Consumption Dataset API")),
            (
                dataset,
                dct.description,
                Literal(
                    "Hourly electricity consumption readings for demo buildings "
                    "in a city energy data space."
                ),
            ),
            (dataset, ex.providerName, Literal("Energy Data Provider Ltd.")),
            (dataset, dct.license, URIRef("https://creativecommons.org/licenses/by/4.0/")),
            (dataset, dct.spatial, Literal("Shenzhen demo district")),
            (dataset, dct.accrualPeriodicity, Literal("hourly")),
            (dataset, ex.unit, Literal("kWh")),
            (dataset, ex.temporalStart, Literal("2026-05-01", datatype=XSD.date)),
            (dataset, ex.temporalEnd, Literal("2026-05-02", datatype=XSD.date)),
            (dataset, dcat.endpointURL, URIRef("https://api.example.org/energy/buildings/hourly")),
            (dataset, dct["format"], Literal("application/json")),
        }
        actual_graph = set(graph)
        exact_graph = actual_graph == expected_graph
        graph_assertions.extend(
            [
                {
                    "name": "exact_triple_count",
                    "expected": 13,
                    "actual": len(graph),
                    "passed": len(graph) == 13,
                },
                {
                    "name": "exact_canonical_scenario_graph",
                    "expected_triple_count": len(expected_graph),
                    "actual_triple_count": len(actual_graph),
                    "missing": sorted(
                        (tuple(map(str, triple)) for triple in expected_graph - actual_graph)
                    ),
                    "unexpected": sorted(
                        (tuple(map(str, triple)) for triple in actual_graph - expected_graph)
                    ),
                    "passed": exact_graph,
                },
            ]
        )
        if not exact_graph:
            issues.append(
                _issue(
                    "CANONICAL_SCENARIO_MISMATCH",
                    VALID_RELPATH,
                    "expanded graph must equal the fixed 13-triple canonical scenario",
                )
            )
    issues = _sorted_issues(issues)
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "context_path": CONTEXT_RELPATH,
        "context_sha256": sha256_file(_repo_path(root, CONTEXT_RELPATH)),
        "example_path": VALID_RELPATH,
        "example_sha256": sha256_file(_repo_path(root, VALID_RELPATH)),
        "expansion": expansion_record,
        "data_triple_count": len(graph) if graph is not None else None,
        "dataset_count": len(datasets),
        "dataset_is_iri": len(datasets) == 1 and isinstance(datasets[0], URIRef),
        "context_assertions": context_assertions,
        "graph_assertions": graph_assertions,
        "issues": issues,
    }, graph


def _inheritance_audit(root: Path, release_manifest: dict[str, Any] | None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []
    release_artifacts = _v04_release_artifacts(release_manifest)
    context_relpath = "C_Semantic_Treehouse/model/v0.3/energy-reading-record-context.jsonld"
    for relpath, expected_hash in sorted(EXPECTED_RECORD_INHERITANCE.items()):
        path = _repo_path(root, relpath)
        actual_hash = sha256_file(path) if path.is_file() else None
        record: dict[str, Any] = {
            "path": relpath,
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "parse_status": "ERROR",
        }
        if actual_hash != expected_hash:
            issues.append(_issue("INHERITED_HASH_DRIFT", relpath, "v0.3 record hash changed"))
        manifest_artifact = release_artifacts.get(relpath)
        origin = manifest_artifact.get("origin") if isinstance(manifest_artifact, dict) else None
        if not isinstance(origin, dict) or (
            origin.get("type"), origin.get("inheritedFrom"), origin.get("change")
        ) != ("inherited", "v0.3", "none"):
            issues.append(_issue("INHERITED_MANIFEST_BINDING", relpath, "invalid inherited origin"))
        try:
            if relpath.endswith(".ttl"):
                graph = parse_turtle(path, relpath)
                meta = run_meta_shacl(graph)
                if meta.get("status") != "SUCCESS":
                    raise ModelValidationError("inherited record Shape failed Meta-SHACL")
                record.update({"parse_status": "SUCCESS", "triple_count": len(graph), "meta_shacl": meta})
            elif relpath.endswith(".schema.json"):
                from jsonschema import Draft7Validator

                schema = _read_json(path)
                Draft7Validator.check_schema(schema)
                record.update({"parse_status": "SUCCESS", "schema_dialect": schema.get("$schema")})
            elif relpath.endswith("context.jsonld"):
                expanded, expansion = offline_expand_jsonld(path, relpath, [])
                record.update({"parse_status": "SUCCESS", "expanded_node_count": len(expanded), "expansion": expansion})
            else:
                expanded, expansion = offline_expand_jsonld(
                    path,
                    relpath,
                    [(_repo_path(root, context_relpath), context_relpath)],
                )
                graph = graph_from_expanded_jsonld(
                    expanded, "https://dssc.local/repository/" + relpath
                )
                record.update({"parse_status": "SUCCESS", "triple_count": len(graph), "expansion": expansion})
        except Exception as exc:  # noqa: BLE001 - normalized fail-closed record
            issues.append(_issue("INHERITED_PARSE", relpath, exc.__class__.__name__))
        records.append(record)
    issues = _sorted_issues(issues)
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "artifacts": records,
        "issues": issues,
    }


def _traceability_evidence(
    root: Path,
    output_dir: Path,
    profile: str,
    current_requirements_sha256: str | None,
) -> dict[str, Any]:
    path = output_dir / f"traceability-{profile}.result.json"
    issues: list[dict[str, str]] = []
    if not path.is_file() or path.stat().st_size == 0:
        return {
            "status": "ERROR",
            "path": path.name,
            "issues": [_issue("TRACEABILITY_EVIDENCE_MISSING", path.name, "missing or empty")],
        }
    try:
        result = _read_json(path)
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "ERROR",
            "path": path.name,
            "issues": [_issue("TRACEABILITY_EVIDENCE_PARSE", path.name, exc.__class__.__name__)],
        }
    contract = result.get("d_group_contract", {}) if isinstance(result, dict) else {}
    meta = contract.get("meta_shacl", {}) if isinstance(contract, dict) else {}
    extraction = contract.get("extraction", {}) if isinstance(contract, dict) else {}
    requirements = result.get("requirements_registry", {}) if isinstance(result, dict) else {}
    if result.get("program_status") != "SUCCESS" or result.get("exit_code") != 0:
        issues.append(_issue("TRACEABILITY_EVIDENCE_FAILED", path.name, "traceability did not pass"))
    if not (
        meta.get("status") == "SUCCESS"
        and meta.get("conforms") is True
        and meta.get("result_count") == 0
    ):
        issues.append(_issue("TRACEABILITY_META_SHACL", path.name, "Meta-SHACL pass evidence is absent"))
    current_shape_hash = sha256_file(_repo_path(root, D_TTL_RELPATH))
    if extraction.get("source_sha256") != current_shape_hash:
        issues.append(_issue("TRACEABILITY_D_HASH_STALE", path.name, "D source hash differs"))
    if requirements.get("manifest_sha256") != current_requirements_sha256:
        issues.append(_issue("TRACEABILITY_REQUIREMENTS_STALE", path.name, "requirements hash differs"))
    issues = _sorted_issues(issues)
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "path": path.name,
        "sha256": sha256_file(path),
        "d_source_sha256": extraction.get("source_sha256"),
        "requirements_sha256": requirements.get("manifest_sha256"),
        "meta_shacl": {
            "status": meta.get("status"),
            "conforms": meta.get("conforms"),
            "result_count": meta.get("result_count"),
        },
        "issues": issues,
    }


def _clone_graph(graph: Any):
    from rdflib import Graph

    clone = Graph()
    for triple in graph:
        clone.add(triple)
    return clone


def _smoke_case(
    case_id: str,
    expected_status: str,
    result: dict[str, Any],
    assertions: list[tuple[str, bool, Any, Any]],
) -> dict[str, Any]:
    rows = [
        {"name": name, "passed": passed, "expected": expected, "actual": actual}
        for name, passed, expected, actual in assertions
    ]
    rows.append(
        {
            "name": "business_status",
            "passed": result.get("business_status") == expected_status,
            "expected": expected_status,
            "actual": result.get("business_status"),
        }
    )
    rows.sort(key=lambda item: item["name"])
    passed = all(item["passed"] for item in rows)
    return {
        "id": case_id,
        "expected_business_status": expected_status,
        "actual_business_status": result.get("business_status"),
        "passed": passed,
        "assertions": rows,
        "validation": result,
    }


def run_contract_smoke(
    root: Path,
    *,
    shapes_path: Path | None = None,
    shapes_logical_path: str = SHAPES_RELPATH,
) -> dict[str, Any]:
    """Run six independent graphs, including three SPARQL/target controls."""
    from rdflib import Literal, Namespace, URIRef
    from rdflib.namespace import RDF, XSD

    issues: list[dict[str, str]] = []
    cases: list[dict[str, Any]] = []
    try:
        shapes = parse_turtle(
            shapes_path or _repo_path(root, SHAPES_RELPATH), shapes_logical_path
        )
        expanded, _ = offline_expand_jsonld(
            _repo_path(root, VALID_RELPATH),
            VALID_RELPATH,
            [(_repo_path(root, CONTEXT_RELPATH), CONTEXT_RELPATH)],
        )
        canonical = graph_from_expanded_jsonld(
            expanded, "https://dssc.local/repository/" + VALID_RELPATH
        )
    except ModelValidationError as exc:
        return {
            "status": "ERROR",
            "engine_config": {},
            "cases": [],
            "counts": {"discovered": 6, "executed": 0, "passed": 0, "failed": 6, "skipped": 0},
            "issues": [_issue("SMOKE_PREFLIGHT", "contract-smoke", str(exc))],
        }
    dcat = Namespace("http://www.w3.org/ns/dcat#")
    dct = Namespace("http://purl.org/dc/terms/")
    ex = Namespace("https://example.org/dssc-energy#")
    sh = Namespace("http://www.w3.org/ns/shacl#")

    try:
        valid_result = run_shacl_validation(
            _clone_graph(canonical), _clone_graph(shapes)
        )
        cases.append(
            _smoke_case(
                "canonical-valid",
                "PASS",
                valid_result,
                [
                    ("target_nonzero", valid_result["target_activation_count"] > 0, ">0", valid_result["target_activation_count"]),
                    ("violation_count", valid_result["severity_counts"]["Violation"] == 0, 0, valid_result["severity_counts"]["Violation"]),
                    ("warning_count", valid_result["severity_counts"]["Warning"] == 0, 0, valid_result["severity_counts"]["Warning"]),
                ],
            )
        )

        invalid_expanded, _ = offline_expand_jsonld(
            _repo_path(root, INVALID_SAMPLE_RELPATH), INVALID_SAMPLE_RELPATH, []
        )
        invalid_graph = graph_from_expanded_jsonld(
            invalid_expanded, "https://dssc.local/repository/" + INVALID_SAMPLE_RELPATH
        )
        invalid_result = run_shacl_validation(invalid_graph, _clone_graph(shapes))
        expected_invalid = {
            (str(ex.ProviderNameShape), str(sh.MinCountConstraintComponent), str(ex.providerName)),
            (str(ex.UnitShape), str(sh.InConstraintComponent), str(ex.unit)),
            (str(ex.TemporalEndShape), str(sh.MinCountConstraintComponent), str(ex.temporalEnd)),
        }
        actual_invalid = {
            (item["source_shape"], item["constraint_component"], item["path"])
            for item in invalid_result["results"]
        }
        cases.append(
            _smoke_case(
                "source-invalid",
                "FAIL",
                invalid_result,
                [
                    ("target_nonzero", invalid_result["target_activation_count"] > 0, ">0", invalid_result["target_activation_count"]),
                    ("exact_required_results", actual_invalid == expected_invalid, sorted(expected_invalid), sorted(actual_invalid)),
                ],
            )
        )

        with tempfile.TemporaryDirectory(prefix="dssc-model-control-") as temporary:
            temp = Path(temporary)
            context_path = temp / "data-product-context.jsonld"
            valid_path = temp / "data-product-valid.jsonld"
            shutil.copyfile(_repo_path(root, CONTEXT_RELPATH), context_path)
            document = _read_json(_repo_path(root, VALID_RELPATH))
            document["dct:conformsTo"] = {
                "@id": "https://w3id.org/dssc-demo/building-energy/v0.4"
            }
            valid_path.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            control_expanded, _ = offline_expand_jsonld(
                valid_path,
                "temporary/data-product-valid.jsonld",
                [(context_path, "temporary/data-product-context.jsonld")],
            )
            control_graph = graph_from_expanded_jsonld(
                control_expanded,
                "https://dssc.local/repository/temporary/data-product-valid.jsonld",
            )
        control_result = run_shacl_validation(control_graph, _clone_graph(shapes))
        control_rows = control_result["results"]
        conforms_warning = (
            len(control_rows) == 1
            and control_rows[0]["source_shape"] == str(ex.DatasetClosedShape)
            and control_rows[0]["severity"] == str(sh.Warning)
            and control_rows[0]["path"] == str(dct.conformsTo)
        )
        cases.append(
            _smoke_case(
                "conforms-to-warning",
                "INAPPLICABLE",
                control_result,
                [
                    ("target_nonzero", control_result["target_activation_count"] > 0, ">0", control_result["target_activation_count"]),
                    ("closed_warning_only", conforms_warning, True, conforms_warning),
                    ("violation_count", control_result["severity_counts"]["Violation"] == 0, 0, control_result["severity_counts"]["Violation"]),
                ],
            )
        )

        from rdflib import Graph

        zero_result = run_shacl_validation(Graph(), _clone_graph(shapes))
        zero_hit = any(
            item["source_shape"] == str(ex.DatasetCardinalityShape)
            and item["constraint_component"] == str(sh.SPARQLConstraintComponent)
            for item in zero_result["results"]
        )
        cases.append(
            _smoke_case(
                "zero-dataset-control",
                "FAIL",
                zero_result,
                [
                    ("target_nonzero", zero_result["target_activation_count"] > 0, ">0", zero_result["target_activation_count"]),
                    ("cardinality_sparql_hit", zero_hit, True, zero_hit),
                ],
            )
        )

        two_graph = _clone_graph(canonical)
        datasets = list(two_graph.subjects(RDF.type, dcat.Dataset))
        if len(datasets) != 1:
            raise ModelValidationError("canonical graph must have one Dataset")
        original = datasets[0]
        second = URIRef(str(original) + "-second")
        for predicate, obj in list(two_graph.predicate_objects(original)):
            two_graph.add((second, predicate, obj))
        two_result = run_shacl_validation(two_graph, _clone_graph(shapes))
        two_hit = any(
            item["source_shape"] == str(ex.DatasetCardinalityShape)
            and item["constraint_component"] == str(sh.SPARQLConstraintComponent)
            for item in two_result["results"]
        )
        cases.append(
            _smoke_case(
                "two-dataset-control",
                "FAIL",
                two_result,
                [
                    ("target_nonzero", two_result["target_activation_count"] > 0, ">0", two_result["target_activation_count"]),
                    ("cardinality_sparql_hit", two_hit, True, two_hit),
                ],
            )
        )

        reversed_graph = _clone_graph(canonical)
        dataset = next(reversed_graph.subjects(RDF.type, dcat.Dataset))
        reversed_graph.set((dataset, ex.temporalStart, Literal("2026-05-03", datatype=XSD.date)))
        reversed_graph.set((dataset, ex.temporalEnd, Literal("2026-05-02", datatype=XSD.date)))
        reversed_result = run_shacl_validation(reversed_graph, _clone_graph(shapes))
        temporal_hit = any(
            item["source_shape"] == str(ex.TemporalOrderShape)
            and item["constraint_component"] == str(sh.SPARQLConstraintComponent)
            for item in reversed_result["results"]
        )
        cases.append(
            _smoke_case(
                "temporal-reversed-control",
                "FAIL",
                reversed_result,
                [
                    ("target_nonzero", reversed_result["target_activation_count"] > 0, ">0", reversed_result["target_activation_count"]),
                    ("temporal_sparql_hit", temporal_hit, True, temporal_hit),
                ],
            )
        )
    except Exception as exc:  # noqa: BLE001 - one smoke failure is program ERROR
        issues.append(_issue("SMOKE_EXECUTION", "contract-smoke", exc.__class__.__name__))

    for case in cases:
        if case["validation"].get("target_activation_count") == 0:
            issues.append(_issue("SHACL_TARGET_ZERO", case["id"], "no Shape target activated"))
        if not case["passed"]:
            issues.append(_issue("SMOKE_ASSERTION_FAILED", case["id"], "contract smoke oracle mismatch"))
    try:
        pyshacl_version = metadata.version("pyshacl")
    except metadata.PackageNotFoundError:
        pyshacl_version = None
        issues.append(_issue("PYSHACL_MISSING", "requirements.lock", "pySHACL is not installed"))
    lock = parse_hash_lock(root / "requirements.lock")
    locked_versions = {
        entry.canonical_name: entry.version for entry in lock.entries if entry.applicable
    }
    locked_pyshacl = locked_versions.get(canonical_name("pyshacl"))
    if lock.issues or pyshacl_version != locked_pyshacl:
        issues.append(_issue("PYSHACL_LOCK_MISMATCH", "requirements.lock", "runtime pySHACL differs from lock"))
    issues = _sorted_issues(issues)
    passed_count = sum(1 for case in cases if case["passed"])
    return {
        "status": "SUCCESS" if not issues and len(cases) == 6 else "ERROR",
        "engine_config": (cases[0]["validation"].get("engine_config", {}) if cases else {}),
        "pyshacl": {"locked_version": locked_pyshacl, "runtime_version": pyshacl_version},
        "counts": {
            "discovered": 6,
            "executed": len(cases),
            "passed": passed_count,
            "failed": 6 - passed_count,
            "skipped": 0,
        },
        "cases": cases,
        "issues": issues,
    }


def audit_model_contract(
    root: Path,
    release_audit: ReleaseManifestAudit,
    requirements_validation: Any,
    output_dir: Path,
    profile: str,
) -> dict[str, Any]:
    """Run all Phase 04 model checks and return one deterministic payload."""
    requirements_document = getattr(requirements_validation, "manifest", None)
    requirements_hash = getattr(requirements_validation, "manifest_sha256", None)
    release_manifest = release_audit.manifest
    shape_derivation = _shape_derivation(root, release_manifest)
    checksums = _parse_sha256sums(root)
    turtle, shapes_graph = _turtle_audit(root)
    jsonld, _canonical_graph = _jsonld_audit(root)
    implementation = audit_requirements_implementation(
        root, requirements_document, release_manifest
    )
    inheritance = _inheritance_audit(root, release_manifest)
    traceability = _traceability_evidence(
        root, output_dir, profile, requirements_hash
    )
    smoke = (
        run_contract_smoke(root)
        if shapes_graph is not None
        else {
            "status": "ERROR",
            "counts": {"discovered": 6, "executed": 0, "passed": 0, "failed": 6, "skipped": 0},
            "cases": [],
            "issues": [_issue("SHAPES_UNAVAILABLE", SHAPES_RELPATH, "cannot run smoke")],
        }
    )
    sections = {
        "release_manifest": {
            "status": "SUCCESS" if release_audit.ok else "ERROR",
            **release_audit.deterministic_record(),
        },
        "requirements_registry": {
            "status": "SUCCESS" if getattr(requirements_validation, "ok", False) else "ERROR",
            **requirements_validation.deterministic_record(),
        },
        "shape_derivation": shape_derivation,
        "sha256sums": checksums,
        "turtle": turtle,
        "jsonld": jsonld,
        "requirements_implementation": implementation,
        "record_inheritance": inheritance,
        "traceability_evidence": traceability,
        "contract_smoke": smoke,
    }
    check_records = [
        {"id": name, "status": value.get("status", "ERROR")}
        for name, value in sections.items()
    ]
    failed = [item for item in check_records if item["status"] != "SUCCESS"]
    return {
        "checks": check_records,
        "counts": {
            "discovered": len(check_records),
            "executed": len(check_records),
            "passed": len(check_records) - len(failed),
            "failed": len(failed),
            "skipped": 0,
        },
        **sections,
        "program_status": "SUCCESS" if not failed else "ERROR",
        "exit_code": 0 if not failed else 1,
        "message": (
            "v0.4 release model passed"
            if not failed
            else "v0.4 release model failed"
        ),
    }


__all__ = [
    "CONTEXT_RELPATH",
    "EXPECTED_PHASE03_SEMANTIC_SHA256",
    "EXPECTED_PHASE03_SEMANTIC_SIZE",
    "MODEL_IMPLEMENTATION_RELPATH",
    "ONTOLOGY_RELPATH",
    "SHAPES_RELPATH",
    "VALID_RELPATH",
    "audit_model_contract",
    "audit_requirements_implementation",
    "requirements_semantic_projection",
    "requirements_semantic_projection_record",
    "run_contract_smoke",
]
