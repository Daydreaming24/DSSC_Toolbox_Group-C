"""Fail-closed SHACL report parsing and four-state classification for v0.4.

The module deliberately treats the RDF report graph as the result contract.  A
``conforms`` boolean alone is never sufficient: every ``sh:ValidationResult``
must be structurally complete, use a known severity and source shape, and map
unambiguously to one Phase 03 requirement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


EX = "https://example.org/dssc-energy#"
SH = "http://www.w3.org/ns/shacl#"
DCAT = "http://www.w3.org/ns/dcat#"
DCT = "http://purl.org/dc/terms/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
XSD = "http://www.w3.org/2001/XMLSchema#"

PREFIXES: dict[str, str] = {
    "ex": EX,
    "sh": SH,
    "dcat": DCAT,
    "dct": DCT,
    "rdf": RDF,
    "xsd": XSD,
}

DATASET_CLOSED_SHAPE = EX + "DatasetClosedShape"
DATASET_CARDINALITY_SHAPE = EX + "DatasetCardinalityShape"
VALIDATION_SUBMISSION = EX + "ValidationSubmission"


class V04ReportError(RuntimeError):
    """A stable program-level report/classification failure."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class RequirementBinding:
    """Allowed report surface for one named source shape."""

    requirement_id: str
    source_shape: str
    severity: str
    components: frozenset[str]
    path: str | None
    messages: frozenset[str]


def expand_iri(value: str | None) -> str | None:
    """Expand the fixed D-contract CURIE vocabulary without remote lookup."""
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise V04ReportError("INVALID_IRI", "IRI/CURIE must be a non-empty string")
    if value.startswith(("http://", "https://")):
        return value
    if ":" not in value:
        raise V04ReportError("UNKNOWN_PREFIX", f"IRI value is not absolute or a CURIE: {value}")
    prefix, local = value.split(":", 1)
    namespace = PREFIXES.get(prefix)
    if namespace is None or not local:
        raise V04ReportError("UNKNOWN_PREFIX", f"unknown or empty CURIE prefix: {value}")
    return namespace + local


def build_requirement_bindings(
    requirements_manifest: Mapping[str, Any],
) -> dict[str, RequirementBinding]:
    """Build an unambiguous source-shape to requirement mapping.

    Only normative ``SHACL_SHAPE`` locators participate.  Operational header
    requirements have no report result and therefore cannot be used to excuse
    an otherwise unknown result.
    """
    requirements = requirements_manifest.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise V04ReportError(
            "REQUIREMENTS_UNAVAILABLE", "requirements manifest has no requirements"
        )
    result: dict[str, RequirementBinding] = {}
    for requirement in requirements:
        if not isinstance(requirement, dict):
            raise V04ReportError("REQUIREMENT_STRUCTURE", "requirement must be an object")
        requirement_id = requirement.get("id")
        sources = requirement.get("sources")
        if not isinstance(requirement_id, str) or not isinstance(sources, list):
            raise V04ReportError("REQUIREMENT_STRUCTURE", "requirement id/sources are invalid")
        for source in sources:
            locator = source.get("locator") if isinstance(source, dict) else None
            if not isinstance(locator, dict) or locator.get("kind") != "SHACL_SHAPE":
                continue
            shape = expand_iri(locator.get("shape"))
            severity = expand_iri(locator.get("severity"))
            components_value = locator.get("constraint_components")
            messages_value = locator.get("messages", [])
            if (
                shape is None
                or severity is None
                or not isinstance(components_value, list)
                or not components_value
                or not isinstance(messages_value, list)
            ):
                raise V04ReportError(
                    "REQUIREMENT_LOCATOR",
                    f"requirement {requirement_id} has an incomplete SHACL locator",
                )
            binding = RequirementBinding(
                requirement_id=requirement_id,
                source_shape=shape,
                severity=severity,
                components=frozenset(
                    expanded
                    for item in components_value
                    for expanded in [expand_iri(item)]
                    if expanded is not None
                ),
                path=expand_iri(locator.get("path")),
                messages=frozenset(str(item) for item in messages_value),
            )
            prior = result.get(shape)
            if prior is not None and prior != binding:
                raise V04ReportError(
                    "AMBIGUOUS_SOURCE_SHAPE",
                    f"source shape maps to multiple requirements: {shape}",
                )
            result[shape] = binding
    if not result:
        raise V04ReportError("REQUIREMENT_MAPPING_EMPTY", "no SHACL result mappings found")
    return result


def _one(graph: Any, subject: Any, predicate: Any, field: str) -> Any:
    values = list(graph.objects(subject, predicate))
    if len(values) != 1:
        raise V04ReportError(
            "REPORT_STRUCTURE",
            f"SHACL result field {field} must occur exactly once",
        )
    return values[0]


def _optional(graph: Any, subject: Any, predicate: Any, field: str) -> Any | None:
    values = list(graph.objects(subject, predicate))
    if len(values) > 1:
        raise V04ReportError(
            "REPORT_STRUCTURE",
            f"SHACL result field {field} must occur at most once",
        )
    return values[0] if values else None


def normalize_term(term: Any | None) -> dict[str, Any] | None:
    """Return a deterministic RDF-term record without preserving blank IDs."""
    if term is None:
        return None
    try:
        from rdflib import BNode, Literal, URIRef
    except ImportError as exc:  # pragma: no cover - dependency preflight catches it
        raise V04ReportError("RDFLIB_MISSING", "RDFLib is not importable") from exc
    if isinstance(term, URIRef):
        return {"term_type": "IRI", "value": str(term)}
    if isinstance(term, BNode):
        return {"term_type": "BNODE", "match": "ANY"}
    if isinstance(term, Literal):
        record: dict[str, Any] = {
            "term_type": "LITERAL",
            "lexical_form": str(term),
        }
        if term.language:
            record["language"] = str(term.language)
        elif term.datatype:
            record["datatype"] = str(term.datatype)
        return record
    raise V04ReportError("UNKNOWN_RDF_TERM", "report contains an unsupported RDF term")


def _term_sort_key(value: dict[str, Any] | None) -> tuple[str, ...]:
    if value is None:
        return ("",)
    return (
        str(value.get("term_type", "")),
        str(value.get("value", "")),
        str(value.get("lexical_form", "")),
        str(value.get("datatype", "")),
        str(value.get("language", "")),
        str(value.get("match", "")),
    )


def _validate_result_against_binding(
    *,
    binding: RequirementBinding,
    component: str,
    severity: str,
    path: str | None,
    message: str,
) -> None:
    if component not in binding.components:
        raise V04ReportError(
            "UNKNOWN_CONSTRAINT_COMPONENT",
            f"constraint component is not mapped for {binding.requirement_id}: {component}",
        )
    if severity != binding.severity:
        raise V04ReportError(
            "SOURCE_SEVERITY_MISMATCH",
            f"severity is not mapped for {binding.requirement_id}: {severity}",
        )
    # Closed-shape results carry the undeclared predicate as resultPath even
    # though the shape-level requirement locator has no fixed path.
    if binding.path is not None and path != binding.path:
        raise V04ReportError(
            "SOURCE_PATH_MISMATCH",
            f"result path is not mapped for {binding.requirement_id}",
        )
    if (
        binding.path is None
        and binding.requirement_id != "D04-R016"
        and path is not None
    ):
        raise V04ReportError(
            "SOURCE_PATH_MISMATCH",
            f"unexpected result path for {binding.requirement_id}",
        )
    if binding.messages and message not in binding.messages:
        raise V04ReportError(
            "SOURCE_MESSAGE_MISMATCH",
            f"result message is not normative for {binding.requirement_id}",
        )


def normalize_shacl_report(
    report_graph: Any,
    requirement_bindings: Mapping[str, RequirementBinding],
) -> dict[str, Any]:
    """Parse, validate, map and deterministically sort a SHACL report graph."""
    try:
        from rdflib import Graph, Literal, Namespace, URIRef
        from rdflib.namespace import RDF as RDF_NS, XSD as XSD_NS
    except ImportError as exc:
        raise V04ReportError("RDFLIB_MISSING", "RDFLib is not importable") from exc
    if not isinstance(report_graph, Graph):
        raise V04ReportError("REPORT_NOT_GRAPH", "validator did not return an RDF graph")
    sh = Namespace(SH)
    reports = set(report_graph.subjects(RDF_NS.type, sh.ValidationReport))
    if len(reports) != 1:
        raise V04ReportError(
            "REPORT_STRUCTURE", "report graph must contain exactly one ValidationReport"
        )
    report_node = next(iter(reports))
    linked = set(report_graph.objects(report_node, sh.result))
    typed = set(report_graph.subjects(RDF_NS.type, sh.ValidationResult))
    if linked != typed:
        raise V04ReportError(
            "REPORT_STRUCTURE", "linked and typed ValidationResult sets differ"
        )
    conforms_term = _one(report_graph, report_node, sh.conforms, "conforms")
    if not isinstance(conforms_term, Literal) or conforms_term.datatype not in (
        XSD_NS.boolean,
        None,
    ):
        raise V04ReportError("REPORT_STRUCTURE", "sh:conforms must be a boolean literal")
    conforms_value = conforms_term.toPython()
    if not isinstance(conforms_value, bool):
        raise V04ReportError("REPORT_STRUCTURE", "sh:conforms is not boolean-valued")

    known_severities = {
        SH + "Violation": "Violation",
        SH + "Warning": "Warning",
        SH + "Info": "Info",
    }
    counts = {"Violation": 0, "Warning": 0, "Info": 0}
    rows: list[dict[str, Any]] = []
    for node in linked:
        source_term = _one(report_graph, node, sh.sourceShape, "sourceShape")
        component_term = _one(
            report_graph, node, sh.sourceConstraintComponent, "sourceConstraintComponent"
        )
        severity_term = _one(report_graph, node, sh.resultSeverity, "resultSeverity")
        focus_term = _one(report_graph, node, sh.focusNode, "focusNode")
        path_term = _optional(report_graph, node, sh.resultPath, "resultPath")
        value_term = _optional(report_graph, node, sh.value, "value")
        messages = list(report_graph.objects(node, sh.resultMessage))
        if len(messages) != 1 or not isinstance(messages[0], Literal):
            raise V04ReportError(
                "REPORT_STRUCTURE", "each ValidationResult must have one literal message"
            )
        if not all(isinstance(term, URIRef) for term in (source_term, component_term, severity_term)):
            raise V04ReportError(
                "REPORT_STRUCTURE", "source shape, component and severity must be IRIs"
            )
        if path_term is not None and not isinstance(path_term, URIRef):
            raise V04ReportError("REPORT_STRUCTURE", "resultPath must be a named IRI")
        source = str(source_term)
        component = str(component_term)
        severity = str(severity_term)
        path = str(path_term) if path_term is not None else None
        message = str(messages[0])
        severity_name = known_severities.get(severity)
        if severity_name is None:
            raise V04ReportError("UNKNOWN_SEVERITY", f"unknown severity: {severity}")
        binding = requirement_bindings.get(source)
        if binding is None:
            raise V04ReportError("UNKNOWN_SOURCE_SHAPE", f"unmapped source shape: {source}")
        _validate_result_against_binding(
            binding=binding,
            component=component,
            severity=severity,
            path=path,
            message=message,
        )
        if severity_name == "Warning" and source != DATASET_CLOSED_SHAPE:
            raise V04ReportError(
                "UNAPPROVED_WARNING", "only DatasetClosedShape Warning is approved"
            )
        counts[severity_name] += 1
        rows.append(
            {
                "requirement_id": binding.requirement_id,
                "focus_node": normalize_term(focus_term),
                "result_path": path,
                "source_shape": source,
                "source_constraint_component": component,
                "severity": severity,
                "severity_name": severity_name,
                "message": message,
                "value": normalize_term(value_term),
            }
        )
    rows.sort(
        key=lambda item: (
            item["requirement_id"],
            item["source_shape"],
            item["result_path"] or "",
            item["source_constraint_component"],
            item["severity"],
            item["message"],
            _term_sort_key(item["focus_node"]),
            _term_sort_key(item["value"]),
        )
    )
    business_status = (
        "FAIL"
        if counts["Violation"] > 0
        else "INAPPLICABLE"
        if counts["Warning"] > 0
        else "PASS"
    )
    expected_conforms = len(rows) == 0
    if conforms_value != expected_conforms:
        raise V04ReportError(
            "REPORT_CONFORMS_MISMATCH",
            "sh:conforms conflicts with allow_warnings=false/allow_infos=false",
        )
    return {
        "report_conforms": conforms_value,
        "report_triple_count": len(report_graph),
        "result_count": len(rows),
        "severity_counts": counts,
        "business_status": business_status,
        "results": rows,
    }


def collect_target_activation(data_graph: Any, shapes_graph: Any) -> dict[str, Any]:
    """Enumerate the standard SHACL targets used by the D contract."""
    try:
        from rdflib import Namespace
        from rdflib.namespace import RDF as RDF_NS
    except ImportError as exc:
        raise V04ReportError("RDFLIB_MISSING", "RDFLib is not importable") from exc
    sh = Namespace(SH)
    dcat = Namespace(DCAT)
    activations: set[tuple[str, str, tuple[str, ...]]] = set()

    def add(shape: Any, kind: str, focus: Any) -> None:
        normalized = normalize_term(focus)
        activations.add((str(shape), kind, _term_sort_key(normalized)))

    for shape, target_class in shapes_graph.subject_objects(sh.targetClass):
        for focus in data_graph.subjects(RDF_NS.type, target_class):
            add(shape, "targetClass", focus)
    for shape, focus in shapes_graph.subject_objects(sh.targetNode):
        add(shape, "targetNode", focus)
    for shape, predicate in shapes_graph.subject_objects(sh.targetSubjectsOf):
        for focus in data_graph.subjects(predicate, None):
            add(shape, "targetSubjectsOf", focus)
    for shape, predicate in shapes_graph.subject_objects(sh.targetObjectsOf):
        for focus in data_graph.objects(None, predicate):
            add(shape, "targetObjectsOf", focus)

    rows = [
        {"shape": shape, "target_kind": kind, "focus_key": list(focus_key)}
        for shape, kind, focus_key in sorted(activations)
    ]
    datasets = set(data_graph.subjects(RDF_NS.type, dcat.Dataset))
    dataset_target_count = sum(
        1
        for shape, target_class in shapes_graph.subject_objects(sh.targetClass)
        if target_class == dcat.Dataset
        for _focus in data_graph.subjects(RDF_NS.type, target_class)
    )
    cardinality_target_active = any(
        shape == DATASET_CARDINALITY_SHAPE
        and kind == "targetNode"
        and focus_key[1] == VALIDATION_SUBMISSION
        for shape, kind, focus_key in activations
        if len(focus_key) > 1
    )
    return {
        "count": len(activations),
        "activations": rows,
        "dataset_node_count": len(datasets),
        "dataset_target_activation_count": dataset_target_count,
        "cardinality_target_active": cardinality_target_active,
    }


def assert_named_shapes(
    shapes_graph: Any,
    bindings: Mapping[str, RequirementBinding],
) -> dict[str, Any]:
    """Prove that every requirement-mapped named Shape is in the release graph."""
    try:
        from rdflib import Namespace, URIRef
        from rdflib.namespace import RDF as RDF_NS
    except ImportError as exc:
        raise V04ReportError("RDFLIB_MISSING", "RDFLib is not importable") from exc
    sh = Namespace(SH)
    present = {
        str(subject)
        for shape_type in (sh.NodeShape, sh.PropertyShape)
        for subject in shapes_graph.subjects(RDF_NS.type, shape_type)
        if isinstance(subject, URIRef)
    }
    required = set(bindings)
    missing = sorted(required - present)
    if missing:
        raise V04ReportError(
            "REQUIRED_SHAPE_MISSING", "release Shape graph omits: " + ", ".join(missing)
        )
    if DATASET_CARDINALITY_SHAPE not in present or DATASET_CLOSED_SHAPE not in present:
        raise V04ReportError(
            "REQUIRED_SHAPE_MISSING", "cardinality and closed named Shapes are required"
        )
    return {
        "named_shape_count": len(present),
        "required_shape_count": len(required),
        "required_shapes": sorted(required),
        "missing_shapes": [],
    }


def mapped_requirement_ids(results: Iterable[Mapping[str, Any]]) -> list[str]:
    return sorted(
        {
            str(result["requirement_id"])
            for result in results
            if isinstance(result.get("requirement_id"), str)
        }
    )


__all__ = [
    "DATASET_CARDINALITY_SHAPE",
    "DATASET_CLOSED_SHAPE",
    "PREFIXES",
    "RequirementBinding",
    "V04ReportError",
    "assert_named_shapes",
    "build_requirement_bindings",
    "collect_target_activation",
    "expand_iri",
    "mapped_requirement_ids",
    "normalize_shacl_report",
    "normalize_term",
]
