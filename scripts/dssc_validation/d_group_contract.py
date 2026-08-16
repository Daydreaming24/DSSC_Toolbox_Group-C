"""Deterministic extraction and read-only audit of the frozen D-group SHACL TTL."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pyshacl import validate
from pyshacl.entrypoints import meta_validate
from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
from rdflib.collection import Collection

from dssc_validation.hashing import sha256_file, sha256_text


D_TTL_RELPATH = "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl"
D_EXPLANATION_RELPATH = (
    "inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md"
)
D_SHA256SUMS_RELPATH = "inputs/d-group/v0.4/SHA256SUMS"
FROZEN_SHA256SUMS_RELPATH = "docs/provenance/manifests/frozen-files-SHA256SUMS"
VALID_SAMPLE_RELPATH = (
    "inputs/original-plan/DSSC_Minimal_Energy_Scenario/metadata/"
    "data-product-valid.jsonld"
)
INVALID_SAMPLE_RELPATH = (
    "inputs/original-plan/DSSC_Minimal_Energy_Scenario/metadata/"
    "data-product-invalid.jsonld"
)

SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("https://example.org/dssc-energy#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
RDF_NS = Namespace(str(RDF))
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
DCT = Namespace("http://purl.org/dc/terms/")

_PREFIXES = {
    "sh": str(SH),
    "ex": str(EX),
    "dcat": str(DCAT),
    "dct": str(DCT),
    "rdf": str(RDF_NS),
    "xsd": str(XSD),
}

_CONSTRAINT_COMPONENTS = {
    SH.closed: SH.ClosedConstraintComponent,
    SH.datatype: SH.DatatypeConstraintComponent,
    SH["in"]: SH.InConstraintComponent,
    SH.maxCount: SH.MaxCountConstraintComponent,
    SH.minCount: SH.MinCountConstraintComponent,
    SH.minLength: SH.MinLengthConstraintComponent,
    SH.nodeKind: SH.NodeKindConstraintComponent,
    SH.pattern: SH.PatternConstraintComponent,
    SH.property: SH.PropertyConstraintComponent,
    SH.sparql: SH.SPARQLConstraintComponent,
    SH.ignoredProperties: SH.ClosedConstraintComponent,
}

_CONSTRAINT_PREDICATES = tuple(_CONSTRAINT_COMPONENTS)
_TARGET_PREDICATES = (
    SH.targetClass,
    SH.targetNode,
    SH.targetSubjectsOf,
    SH.targetObjectsOf,
)
_DIRECT_TARGET_KINDS = {
    SH.targetClass: "DIRECT_TARGET_CLASS",
    SH.targetNode: "DIRECT_TARGET_NODE",
    SH.targetSubjectsOf: "DIRECT_TARGET_SUBJECTS_OF",
    SH.targetObjectsOf: "DIRECT_TARGET_OBJECTS_OF",
}
_OWNER_TARGET_KINDS = {
    SH.targetClass: "OWNER_TARGET_CLASS",
    SH.targetNode: "OWNER_TARGET_NODE",
    SH.targetSubjectsOf: "OWNER_TARGET_SUBJECTS_OF",
    SH.targetObjectsOf: "OWNER_TARGET_OBJECTS_OF",
}
_STATUS_HEADER = re.compile(
    r"^\s*#\s+(PASS|FAIL|INAPPLICABLE|UNTESTABLE)\s+—\s+(.+?)\s*$"
)
_STATUS_HEADER_ORDER = ("PASS", "FAIL", "INAPPLICABLE", "UNTESTABLE")
_CHECKSUM_RECORD = re.compile(r"^([0-9a-f]{64})  ([^\r\n]+)$")
_STATUS_PRECEDENCE = ("UNTESTABLE", "FAIL", "INAPPLICABLE", "PASS")
_HEADER_REQUIREMENT_BY_STATUS = {
    "INAPPLICABLE": "D04-R016",
    "UNTESTABLE": "D04-R017",
}


def _expand_curie(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if ":" in value:
        prefix, local = value.split(":", 1)
        namespace = _PREFIXES.get(prefix)
        if namespace is not None:
            return namespace + local
    return value


def _literal_value(term: Literal) -> Any:
    python_value = term.toPython()
    if isinstance(python_value, (str, int, float, bool)) or python_value is None:
        return python_value
    return str(term)


def _term_value(graph: Graph, term: Any) -> Any:
    if isinstance(term, URIRef):
        return str(term)
    if isinstance(term, Literal):
        return _literal_value(term)
    if isinstance(term, BNode):
        try:
            return [_term_value(graph, item) for item in Collection(graph, term)]
        except Exception:  # noqa: BLE001 - a non-list blank node is normalized below
            path = graph.value(term, SH.path)
            if path is not None:
                return {"anonymous_property_path": _term_value(graph, path)}
            return {"anonymous_node": True}
    return str(term)


def _messages(graph: Graph, shape: URIRef) -> list[str]:
    values = [str(value) for value in graph.objects(shape, SH.message)]
    for constraint in graph.objects(shape, SH.sparql):
        values.extend(str(value) for value in graph.objects(constraint, SH.message))
    return sorted(set(values))


def _direct_targets(graph: Graph, shape: URIRef) -> list[dict[str, Any]]:
    return sorted(
        [
            {
                "kind": _DIRECT_TARGET_KINDS[predicate],
                "predicate": str(predicate),
                "value": str(value),
                "owner_shape": None,
            }
            for predicate in _TARGET_PREDICATES
            for value in graph.objects(shape, predicate)
        ],
        key=lambda item: (
            item["kind"],
            item["predicate"],
            item["value"],
            item["owner_shape"] or "",
        ),
    )


def _effective_targets(
    graph: Graph, shape: URIRef, direct: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if direct:
        return direct
    inherited: list[dict[str, Any]] = []
    for owner in graph.subjects(SH.property, shape):
        if isinstance(owner, URIRef):
            for target in _direct_targets(graph, owner):
                predicate = URIRef(target["predicate"])
                inherited.append(
                    {
                        "kind": _OWNER_TARGET_KINDS[predicate],
                        "predicate": target["predicate"],
                        "value": target["value"],
                        "owner_shape": str(owner),
                    }
                )
    unique = {
        (
            item["kind"],
            item["predicate"],
            item["value"],
            item["owner_shape"],
        ): item
        for item in inherited
    }
    return [unique[key] for key in sorted(unique)]


def _constraints(graph: Graph, shape: URIRef) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for predicate in _CONSTRAINT_PREDICATES:
        component = _CONSTRAINT_COMPONENTS[predicate]
        for value in graph.objects(shape, predicate):
            if predicate == SH.sparql:
                select = graph.value(value, SH.select)
                normalized_value: Any = {
                    "rdf_types": sorted(
                        str(item) for item in graph.objects(value, RDF.type)
                    ),
                    "messages": sorted(
                        str(item) for item in graph.objects(value, SH.message)
                    ),
                    "select": {
                        "hash_algorithm": "SHA-256-UTF8-RDF-LEXICAL-FORM",
                        "sha256": (
                            sha256_text(str(select)) if select is not None else None
                        ),
                        "length_chars": len(str(select)) if select is not None else 0,
                    },
                }
            elif predicate == SH.property and isinstance(value, BNode):
                normalized_value = {
                    "anonymous_property_path": (
                        str(graph.value(value, SH.path))
                        if graph.value(value, SH.path) is not None
                        else None
                    )
                }
            else:
                normalized_value = _term_value(graph, value)
            values.append(
                {
                    "predicate": str(predicate),
                    "component": str(component),
                    "value": normalized_value,
                }
            )
    return sorted(values, key=lambda item: (item["predicate"], repr(item["value"])))


def _sparql_constraints(graph: Graph, shape: URIRef) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for constraint in graph.objects(shape, SH.sparql):
        select = graph.value(constraint, SH.select)
        records.append(
            {
                "message": (
                    str(graph.value(constraint, SH.message))
                    if graph.value(constraint, SH.message) is not None
                    else None
                ),
                "query_hash": sha256_text(str(select)) if select is not None else None,
                "query_length": len(str(select)) if select is not None else 0,
                "hash_algorithm": "SHA-256 of exact RDF lexical sh:select UTF-8",
            }
        )
    return sorted(records, key=lambda item: (item["query_hash"] or ""))


def _shape_record(graph: Graph, shape: URIRef, shape_type: str) -> dict[str, Any]:
    direct_targets = _direct_targets(graph, shape)
    constraints = _constraints(graph, shape)
    property_references = sorted(
        str(value) for value in graph.objects(shape, SH.property) if isinstance(value, URIRef)
    )
    anonymous_property_paths = sorted(
        str(path)
        for value in graph.objects(shape, SH.property)
        if isinstance(value, BNode)
        for path in [graph.value(value, SH.path)]
        if path is not None
    )
    ignored: list[Any] = []
    for head in graph.objects(shape, SH.ignoredProperties):
        if isinstance(head, BNode):
            ignored.extend(_term_value(graph, item) for item in Collection(graph, head))
    return {
        "shape": str(shape),
        "shape_type": shape_type,
        "name": str(graph.value(shape, SH.name)) if graph.value(shape, SH.name) else None,
        "direct_targets": direct_targets,
        "effective_targets": _effective_targets(graph, shape, direct_targets),
        "path": str(graph.value(shape, SH.path)) if graph.value(shape, SH.path) else None,
        "severity": (
            str(graph.value(shape, SH.severity)) if graph.value(shape, SH.severity) else None
        ),
        "messages": _messages(graph, shape),
        "constraint_components": sorted(
            {item["component"] for item in constraints}
        ),
        "constraints": constraints,
        "property_references": property_references,
        "anonymous_property_paths": anonymous_property_paths,
        "closed_allowlist": anonymous_property_paths,
        "ignored_properties": sorted(str(value) for value in ignored),
        "sparql_constraints": _sparql_constraints(graph, shape),
    }


def _extract_status_header(root: Path) -> dict[str, Any]:
    lines = (root / D_TTL_RELPATH).read_text(encoding="utf-8").splitlines()
    mappings = [
        {
            "status": match.group(1),
            "line_start": line_number,
            "line_end": line_number,
            "quoted_text": line,
            "description": match.group(2),
        }
        for line_number, line in enumerate(lines, start=1)
        for match in [_STATUS_HEADER.fullmatch(line)]
        if match is not None
    ]
    issues: list[str] = []
    status_order = tuple(item["status"] for item in mappings)
    if status_order != _STATUS_HEADER_ORDER:
        issues.append(
            "TTL status header must contain PASS, FAIL, INAPPLICABLE and "
            "UNTESTABLE exactly once in canonical order"
        )

    mapping_lines = [item["line_start"] for item in mappings]
    line_start = mapping_lines[0] - 1 if mapping_lines else None
    line_end = mapping_lines[-1] if mapping_lines else None
    if mapping_lines and mapping_lines != list(
        range(mapping_lines[0], mapping_lines[0] + len(mapping_lines))
    ):
        issues.append("TTL status header mapping lines must be contiguous")
    if (
        line_start is None
        or line_start < 1
        or "结果映射" not in lines[line_start - 1]
    ):
        issues.append("TTL status header heading is missing immediately before mappings")

    block_lines = (
        [
            {"line_number": number, "quoted_text": lines[number - 1]}
            for number in range(line_start, line_end + 1)
        ]
        if line_start is not None and line_end is not None and line_start >= 1
        else []
    )
    return {
        "document": D_TTL_RELPATH,
        "line_start": line_start,
        "line_end": line_end,
        "status_order": list(status_order),
        "mappings": mappings,
        "lines": block_lines,
        "issues": sorted(issues),
    }


def _checksum_records(path: Path) -> tuple[dict[str, str], list[str]]:
    records: dict[str, str] = {}
    issues: list[str] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = _CHECKSUM_RECORD.fullmatch(line)
        if match is None:
            issues.append(f"invalid checksum record at line {line_number}")
            continue
        digest, relpath = match.groups()
        if relpath in records:
            issues.append(f"duplicate checksum path at line {line_number}: {relpath}")
            continue
        records[relpath] = digest
    return records, issues


def audit_d_input_integrity(root: Path) -> dict[str, Any]:
    """Cross-check D checksums, frozen manifest records, and actual bytes."""
    d_manifest_path = root / D_SHA256SUMS_RELPATH
    frozen_manifest_path = root / FROZEN_SHA256SUMS_RELPATH
    issues: list[str] = []
    try:
        d_records, d_issues = _checksum_records(d_manifest_path)
    except (OSError, UnicodeError) as exc:
        d_records, d_issues = {}, [f"D SHA256SUMS is unreadable: {exc}"]
    try:
        frozen_records, frozen_issues = _checksum_records(frozen_manifest_path)
    except (OSError, UnicodeError) as exc:
        frozen_records, frozen_issues = {}, [f"frozen manifest is unreadable: {exc}"]
    issues.extend(d_issues)
    issues.extend(frozen_issues)

    expected_d_paths = {
        "received/building-energy-shapes_D.ttl": D_TTL_RELPATH,
        "received/初始TTL到最终TTL修改说明.md": D_EXPLANATION_RELPATH,
    }
    if set(d_records) != set(expected_d_paths):
        issues.append(
            "D SHA256SUMS must contain exactly the two frozen received artifacts"
        )

    sources: list[dict[str, Any]] = []
    for d_relpath, repo_relpath in expected_d_paths.items():
        source_path = root / repo_relpath
        actual = sha256_file(source_path) if source_path.is_file() else None
        d_expected = d_records.get(d_relpath)
        frozen_expected = frozen_records.get(repo_relpath)
        matches = (
            actual is not None
            and actual == d_expected
            and actual == frozen_expected
        )
        if not matches:
            issues.append(f"checksum binding differs for {repo_relpath}")
        sources.append(
            {
                "path": repo_relpath,
                "actual_sha256": actual,
                "d_sha256sums_sha256": d_expected,
                "frozen_manifest_sha256": frozen_expected,
                "matches": matches,
            }
        )
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "d_sha256sums_path": D_SHA256SUMS_RELPATH,
        "d_sha256sums_sha256": (
            sha256_file(d_manifest_path) if d_manifest_path.is_file() else None
        ),
        "frozen_manifest_path": FROZEN_SHA256SUMS_RELPATH,
        "frozen_manifest_sha256": (
            sha256_file(frozen_manifest_path)
            if frozen_manifest_path.is_file()
            else None
        ),
        "sources": sources,
        "issues": sorted(issues),
    }


def extract_d_group_contract(root: Path) -> tuple[Graph, dict[str, Any]]:
    """Parse the frozen TTL and return a stable, blank-node-independent record."""
    ttl_path = root / D_TTL_RELPATH
    graph = Graph().parse(ttl_path, format="turtle")
    node_shapes = sorted(
        (shape for shape in graph.subjects(RDF.type, SH.NodeShape) if isinstance(shape, URIRef)),
        key=str,
    )
    property_shapes = sorted(
        (
            shape
            for shape in graph.subjects(RDF.type, SH.PropertyShape)
            if isinstance(shape, URIRef)
        ),
        key=str,
    )
    records = [
        *[_shape_record(graph, shape, "NodeShape") for shape in node_shapes],
        *[_shape_record(graph, shape, "PropertyShape") for shape in property_shapes],
    ]
    records.sort(key=lambda item: item["shape"])
    return graph, {
        "source_path": D_TTL_RELPATH,
        "source_sha256": sha256_file(ttl_path),
        "triple_count": len(graph),
        "named_node_shape_count": len(node_shapes),
        "named_property_shape_count": len(property_shapes),
        "named_shape_count": len(records),
        "constraint_record_count": sum(
            len(record["constraints"]) for record in records
        ),
        "status_header": _extract_status_header(root),
        "shapes": records,
    }


def run_meta_shacl(graph: Graph) -> dict[str, Any]:
    """Execute the locked pySHACL Meta-SHACL preflight."""
    try:
        conforms, report_graph, _ = meta_validate(
            graph, inference="rdfs", advanced=True
        )
    except Exception as exc:  # noqa: BLE001 - normalized into program evidence
        return {
            "status": "ERROR",
            "conforms": False,
            "result_count": None,
            "report_triple_count": None,
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }
    result_count = len(list(report_graph.subjects(RDF.type, SH.ValidationResult)))
    return {
        "status": "SUCCESS" if conforms and result_count == 0 else "ERROR",
        "conforms": bool(conforms),
        "result_count": result_count,
        "report_triple_count": len(report_graph),
        "error_type": None,
        "message": "Meta-SHACL passed" if conforms else "Meta-SHACL failed",
    }


def _validation_results(report: Graph) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for result in report.subjects(RDF.type, SH.ValidationResult):
        path = report.value(result, SH.resultPath)
        value = report.value(result, SH.value)
        records.append(
            {
                "source_shape": str(report.value(result, SH.sourceShape)),
                "path": str(path) if path is not None else None,
                "constraint_component": str(
                    report.value(result, SH.sourceConstraintComponent)
                ),
                "severity": str(report.value(result, SH.resultSeverity)),
                "message": str(report.value(result, SH.resultMessage)),
                "value": str(value) if value is not None else None,
            }
        )
    return sorted(
        records,
        key=lambda item: (
            item["source_shape"],
            item["path"] or "",
            item["constraint_component"],
            item["message"],
            item["value"] or "",
        ),
    )


def run_source_smoke(root: Path, shapes_graph: Graph) -> dict[str, Any]:
    """Validate the two frozen original-plan examples without modifying them."""
    cases: list[dict[str, Any]] = []
    for case_id, relpath, expected in (
        ("source-valid", VALID_SAMPLE_RELPATH, "PASS"),
        ("source-invalid", INVALID_SAMPLE_RELPATH, "FAIL"),
    ):
        data_graph = Graph().parse(root / relpath, format="json-ld")
        dataset_count = len(set(data_graph.subjects(RDF.type, DCAT.Dataset)))
        conforms, report_graph, _ = validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference="none",
            advanced=True,
            abort_on_first=False,
            meta_shacl=True,
            allow_warnings=False,
            allow_infos=False,
        )
        results = _validation_results(report_graph)
        violation_count = sum(item["severity"] == str(SH.Violation) for item in results)
        warning_count = sum(item["severity"] == str(SH.Warning) for item in results)
        actual = (
            "FAIL"
            if violation_count
            else "INAPPLICABLE"
            if warning_count
            else "PASS"
        )
        cases.append(
            {
                "id": case_id,
                "source_path": relpath,
                "source_sha256": sha256_file(root / relpath),
                "data_triple_count": len(data_graph),
                "dataset_target_count": dataset_count,
                "conforms_boolean": bool(conforms),
                "expected_business_status": expected,
                "actual_business_status": actual,
                "result_count": len(results),
                "violation_count": violation_count,
                "warning_count": warning_count,
                "results": results,
            }
        )
    expected_invalid = {
        (str(EX.ProviderNameShape), str(SH.MinCountConstraintComponent), str(EX.providerName)),
        (str(EX.UnitShape), str(SH.InConstraintComponent), str(EX.unit)),
        (str(EX.TemporalEndShape), str(SH.MinCountConstraintComponent), str(EX.temporalEnd)),
    }
    invalid_actual = {
        (item["source_shape"], item["constraint_component"], item["path"])
        for item in cases[1]["results"]
    }
    issues: list[str] = []
    if cases[0]["actual_business_status"] != "PASS" or cases[0]["result_count"] != 0:
        issues.append("source valid example did not produce zero results and PASS")
    if cases[0]["dataset_target_count"] != 1:
        issues.append("source valid example did not activate exactly one Dataset target")
    if cases[1]["actual_business_status"] != "FAIL" or invalid_actual != expected_invalid:
        issues.append("source invalid example did not exactly match the three-rule oracle")
    if cases[1]["dataset_target_count"] != 1:
        issues.append("source invalid example did not activate exactly one Dataset target")
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "cases": cases,
        "issues": sorted(issues),
    }


def _normalized_targets(
    locator_target: Any,
) -> set[tuple[str, str, str, str | None]]:
    values: set[tuple[str, str, str, str | None]] = set()
    targets = locator_target if isinstance(locator_target, list) else [locator_target]
    for target in targets:
        if not isinstance(target, dict):
            continue
        kind = target.get("kind")
        predicate = target.get("predicate")
        value = target.get("value")
        owner_shape = target.get("owner_shape")
        if isinstance(value, dict):
            value = value.get("value")
        if not (
            isinstance(kind, str)
            and isinstance(predicate, str)
            and isinstance(value, str)
            and (owner_shape is None or isinstance(owner_shape, str))
        ):
            continue
        values.add(
            (
                kind,
                _expand_curie(predicate),
                _expand_curie(value),
                _expand_curie(owner_shape),
            )
        )
    return values


def _manifest_term_value(term: Any) -> Any:
    if not isinstance(term, dict):
        return _expand_curie(term)
    term_type = term.get("term_type")
    if term_type == "IRI":
        return _expand_curie(term.get("value"))
    if term_type in {"INTEGER", "BOOLEAN", "LITERAL", "TEXT"}:
        return term.get("value")
    if term_type == "RDF_LIST":
        return [_manifest_term_value(item) for item in term.get("items", [])]
    if term_type == "PROPERTY_PATH_SHAPE":
        path = term.get("path")
        return {"anonymous_property_path": _manifest_term_value(path)}
    if term_type == "SPARQL_CONSTRAINT":
        select = term.get("select", {})
        return {
            "rdf_types": sorted(_expand_curie(item) for item in term.get("rdf_types", [])),
            "messages": sorted(str(item) for item in term.get("messages", [])),
            "select": {
                "hash_algorithm": select.get("hash_algorithm"),
                "sha256": select.get("sha256"),
                "length_chars": select.get("length_chars"),
            },
        }
    return term


def _manifest_constraints(locator: dict[str, Any]) -> set[str]:
    records: set[str] = set()
    for constraint in locator.get("constraints", []):
        if not isinstance(constraint, dict):
            continue
        normalized = {
            "predicate": _expand_curie(constraint.get("predicate")),
            "component": _expand_curie(constraint.get("component")),
            "value": _manifest_term_value(constraint.get("value")),
        }
        records.add(json.dumps(normalized, ensure_ascii=False, sort_keys=True))
    return records


def _extracted_constraints(shape: dict[str, Any]) -> set[str]:
    return {
        json.dumps(item, ensure_ascii=False, sort_keys=True)
        for item in shape.get("constraints", [])
    }


def _header_contract_issues(
    manifest: dict[str, Any], extraction: dict[str, Any]
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    header = extraction.get("status_header", {})
    for message in header.get("issues", []):
        issues.append(
            {
                "code": "STATUS_HEADER_CONTRACT_INVALID",
                "location": D_TTL_RELPATH,
                "message": str(message),
            }
        )

    profile = manifest.get("profile", {})
    profile_header = (
        profile.get("status_header_source") if isinstance(profile, dict) else None
    )
    expected_profile_header = {
        "path": header.get("document"),
        "line_start": header.get("line_start"),
        "line_end": header.get("line_end"),
    }
    actual_profile_header = (
        {
            "path": profile_header.get("path"),
            "line_start": profile_header.get("line_start"),
            "line_end": profile_header.get("line_end"),
        }
        if isinstance(profile_header, dict)
        else None
    )
    if actual_profile_header != expected_profile_header:
        issues.append(
            {
                "code": "STATUS_HEADER_SOURCE_MISMATCH",
                "location": "$.profile.status_header_source",
                "message": "status-header document or canonical line range differs",
            }
        )

    precedence = profile.get("business_status_precedence") if isinstance(profile, dict) else None
    if precedence != list(_STATUS_PRECEDENCE):
        issues.append(
            {
                "code": "FOUR_STATUS_PRECEDENCE_MISMATCH",
                "location": "$.profile.business_status_precedence",
                "message": "business-status precedence differs from the frozen oracle",
            }
        )

    requirements = [
        item for item in manifest.get("requirements", []) if isinstance(item, dict)
    ]
    manifest_statuses = {
        status
        for requirement in requirements
        for status in requirement.get("expected_business_statuses", [])
        if isinstance(status, str)
    }
    if manifest_statuses != set(_STATUS_HEADER_ORDER):
        issues.append(
            {
                "code": "FOUR_STATUS_REQUIREMENT_COVERAGE",
                "location": "$.requirements",
                "message": "requirements do not cover exactly the four frozen business statuses",
            }
        )

    header_lines = {
        item.get("line_number"): item.get("quoted_text")
        for item in header.get("lines", [])
        if isinstance(item, dict)
    }
    status_by_line = {
        item.get("line_start"): item.get("status")
        for item in header.get("mappings", [])
        if isinstance(item, dict)
    }
    locators_by_requirement: dict[str, list[dict[str, Any]]] = {}
    for requirement in requirements:
        requirement_id = requirement.get("id")
        if not isinstance(requirement_id, str):
            continue
        for source in requirement.get("sources", []):
            locator = source.get("locator") if isinstance(source, dict) else None
            if not isinstance(locator, dict) or locator.get("kind") != "TTL_HEADER_COMMENT":
                continue
            locators_by_requirement.setdefault(requirement_id, []).append(locator)
            line_start = locator.get("line_start")
            line_end = locator.get("line_end")
            valid_range = (
                isinstance(line_start, int)
                and not isinstance(line_start, bool)
                and isinstance(line_end, int)
                and not isinstance(line_end, bool)
                and line_start <= line_end
            )
            quoted_lines = (
                [header_lines.get(number) for number in range(line_start, line_end + 1)]
                if valid_range
                else []
            )
            expected_quote = (
                "\n".join(str(line) for line in quoted_lines)
                if quoted_lines and all(line is not None for line in quoted_lines)
                else None
            )
            if (
                locator.get("document") != header.get("document")
                or expected_quote is None
                or locator.get("quoted_text") != expected_quote
            ):
                issues.append(
                    {
                        "code": "STATUS_HEADER_LOCATOR_MISMATCH",
                        "location": requirement_id,
                        "message": (
                            "TTL header locator document, line range or exact quoted "
                            "text differs"
                        ),
                    }
                )

    for status, requirement_id in _HEADER_REQUIREMENT_BY_STATUS.items():
        locators = locators_by_requirement.get(requirement_id, [])
        mapped_statuses = [
            status_by_line.get(locator.get("line_start"))
            for locator in locators
            if locator.get("line_start") == locator.get("line_end")
        ]
        if len(locators) != 1 or mapped_statuses != [status]:
            issues.append(
                {
                    "code": "STATUS_HEADER_REQUIREMENT_MAPPING",
                    "location": requirement_id,
                    "message": (
                        f"{requirement_id} must have exactly one exact {status} "
                        "TTL-header locator"
                    ),
                }
            )
    return issues


def compare_registry_to_contract(
    manifest: dict[str, Any], extraction: dict[str, Any]
) -> dict[str, Any]:
    """Perform bidirectional named-shape and source-detail coverage checks."""
    issues: list[dict[str, str]] = []
    extracted = {item["shape"]: item for item in extraction["shapes"]}
    registry: dict[str, tuple[str, dict[str, Any]]] = {}
    for requirement in manifest.get("requirements", []):
        if not isinstance(requirement, dict):
            continue
        for source in requirement.get("sources", []):
            locator = source.get("locator") if isinstance(source, dict) else None
            if not isinstance(locator, dict) or locator.get("kind") != "SHACL_SHAPE":
                continue
            shape = _expand_curie(locator.get("shape"))
            if not isinstance(shape, str):
                continue
            if shape in registry:
                issues.append(
                    {
                        "code": "DUPLICATE_SHAPE_COVERAGE",
                        "location": requirement.get("id", "<unknown>"),
                        "message": f"shape is covered more than once: {shape}",
                    }
                )
            else:
                registry[shape] = (requirement.get("id", "<unknown>"), locator)

    for shape in sorted(set(extracted) - set(registry)):
        issues.append(
            {
                "code": "UNCOVERED_NAMED_SHAPE",
                "location": shape,
                "message": "named D-group shape has no requirement",
            }
        )
    for shape in sorted(set(registry) - set(extracted)):
        issues.append(
            {
                "code": "DANGLING_SOURCE_SHAPE",
                "location": registry[shape][0],
                "message": f"registry source shape is absent from D TTL: {shape}",
            }
        )

    for shape in sorted(set(extracted) & set(registry)):
        requirement_id, locator = registry[shape]
        actual = extracted[shape]
        expected_path = _expand_curie(locator.get("path"))
        if expected_path != actual["path"]:
            issues.append(
                {
                    "code": "SOURCE_PATH_MISMATCH",
                    "location": requirement_id,
                    "message": f"path differs for {shape}",
                }
            )
        expected_severity = _expand_curie(locator.get("severity"))
        if expected_severity != actual["severity"]:
            issues.append(
                {
                    "code": "SOURCE_SEVERITY_MISMATCH",
                    "location": requirement_id,
                    "message": f"severity differs for {shape}",
                }
            )
        expected_messages = sorted(str(item) for item in locator.get("messages", []))
        if expected_messages != actual["messages"]:
            issues.append(
                {
                    "code": "SOURCE_MESSAGE_MISMATCH",
                    "location": requirement_id,
                    "message": f"messages differ for {shape}",
                }
            )
        expected_components = {
            _expand_curie(item) for item in locator.get("constraint_components", [])
        }
        actual_components = set(actual["constraint_components"])
        if expected_components != actual_components:
            issues.append(
                {
                    "code": "SOURCE_COMPONENT_MISMATCH",
                    "location": requirement_id,
                    "message": (
                        f"components differ for {shape}; expected "
                        f"{sorted(expected_components)}, actual {sorted(actual_components)}"
                    ),
                }
            )
        expected_constraints = _manifest_constraints(locator)
        actual_constraints = _extracted_constraints(actual)
        if expected_constraints != actual_constraints:
            issues.append(
                {
                    "code": "SOURCE_CONSTRAINT_VALUE_MISMATCH",
                    "location": requirement_id,
                    "message": (
                        f"constraint predicate/value set differs for {shape}; "
                        f"expected {len(expected_constraints)}, actual "
                        f"{len(actual_constraints)}"
                    ),
                }
            )
        expected_targets = _normalized_targets(locator.get("target"))
        actual_targets = {
            (
                item["kind"],
                item["predicate"],
                item["value"],
                item["owner_shape"],
            )
            for item in actual["effective_targets"]
        }
        if expected_targets != actual_targets:
            issues.append(
                {
                    "code": "SOURCE_TARGET_MISMATCH",
                    "location": requirement_id,
                    "message": f"target provenance differs for {shape}",
                }
            )
        sparql = locator.get("sparql")
        if isinstance(sparql, dict):
            actual_hashes = {
                item["query_hash"] for item in actual["sparql_constraints"]
            }
            if sparql.get("sha256") not in actual_hashes:
                issues.append(
                    {
                        "code": "SPARQL_QUERY_HASH_MISMATCH",
                        "location": requirement_id,
                        "message": f"SPARQL query hash differs for {shape}",
                    }
                )

    operational = [
        requirement
        for requirement in manifest.get("requirements", [])
        if isinstance(requirement, dict)
        and requirement.get("rule_kind") == "OPERATIONAL_CLASSIFICATION"
    ]
    if [item.get("id") for item in operational] != ["D04-R017"]:
        issues.append(
            {
                "code": "OPERATIONAL_MAPPING_COVERAGE",
                "location": "$.requirements",
                "message": "TTL-header operational mapping must be exactly D04-R017",
            }
        )
    issues.extend(_header_contract_issues(manifest, extraction))
    return {
        "status": "SUCCESS" if not issues else "ERROR",
        "named_shape_count": len(extracted),
        "covered_shape_count": len(set(extracted) & set(registry)),
        "registry_shape_count": len(registry),
        "issues": sorted(
            issues, key=lambda item: (item["code"], item["location"], item["message"])
        ),
    }


def audit_d_group_contract(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Run parse, Meta-SHACL, source smoke, and bidirectional coverage."""
    input_integrity = audit_d_input_integrity(root)
    graph, extraction = extract_d_group_contract(root)
    meta = run_meta_shacl(graph)
    smoke = run_source_smoke(root, graph)
    coverage = compare_registry_to_contract(manifest, extraction)
    successful = all(
        item.get("status") == "SUCCESS"
        for item in (input_integrity, meta, smoke, coverage)
    )
    return {
        "status": "SUCCESS" if successful else "ERROR",
        "input_integrity": input_integrity,
        "extraction": extraction,
        "meta_shacl": meta,
        "source_smoke": smoke,
        "coverage": coverage,
    }


__all__ = [
    "D_EXPLANATION_RELPATH",
    "D_SHA256SUMS_RELPATH",
    "D_TTL_RELPATH",
    "INVALID_SAMPLE_RELPATH",
    "VALID_SAMPLE_RELPATH",
    "audit_d_group_contract",
    "audit_d_input_integrity",
    "compare_registry_to_contract",
    "extract_d_group_contract",
    "run_meta_shacl",
    "run_source_smoke",
]
