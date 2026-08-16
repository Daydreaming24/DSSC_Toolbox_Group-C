"""Offline JSON-LD and report-graph-aware SHACL helpers for Phase 04."""

from __future__ import annotations

import copy
import io
import json
import logging
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path, PurePosixPath
from typing import Any


SHACL_ENGINE_CONFIG: dict[str, Any] = {
    "inference": "none",
    "advanced": True,
    "abort_on_first": False,
    "meta_shacl": True,
    "allow_warnings": False,
    "allow_infos": False,
    "inplace": False,
    "debug": False,
    "do_owl_imports": False,
    "iterate_rules": False,
    "sparql_mode": False,
}


class ModelValidationError(RuntimeError):
    """Stable fail-closed model-validation error."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ModelValidationError("JSON artifact cannot be parsed") from exc


def _public_url(logical_path: str) -> str:
    posix = PurePosixPath(logical_path)
    if posix.is_absolute() or ".." in posix.parts or not posix.parts:
        raise ModelValidationError("logical JSON-LD path must be repository-relative")
    return "https://dssc.local/repository/" + posix.as_posix()


def offline_expand_jsonld(
    input_path: Path,
    logical_input_path: str,
    local_contexts: list[tuple[Path, str]],
) -> tuple[list[Any], dict[str, Any]]:
    """Expand JSON-LD with an exact allowlist and no network fallback."""
    try:
        from pyld import jsonld
    except ImportError as exc:
        raise ModelValidationError("PyLD is not importable") from exc

    document = _read_json(input_path)
    document_url = _public_url(logical_input_path)
    allowed: dict[str, Any] = {}
    context_records: list[dict[str, str]] = []
    for path, logical_path in local_contexts:
        url = _public_url(logical_path)
        if url in allowed:
            raise ModelValidationError("duplicate JSON-LD context URL")
        allowed[url] = _read_json(path)
        context_records.append({"logical_path": logical_path, "document_url": url})

    loader_requests: list[str] = []

    def local_loader(url: str, options: dict[str, Any] | None = None):
        del options
        loader_requests.append(url)
        if url not in allowed:
            raise ModelValidationError(
                "JSON-LD context request is outside the local allowlist"
            )
        return {
            "contextUrl": None,
            "documentUrl": url,
            "document": copy.deepcopy(allowed[url]),
        }

    try:
        expanded = jsonld.expand(
            document,
            options={"base": document_url, "documentLoader": local_loader},
        )
    except ModelValidationError:
        raise
    except Exception as exc:
        raise ModelValidationError("JSON-LD offline expansion failed") from exc
    if not isinstance(expanded, list):
        raise ModelValidationError("JSON-LD expansion did not return an array")
    unknown_requests = sorted(set(loader_requests) - set(allowed))
    if unknown_requests:
        raise ModelValidationError("JSON-LD loader observed an unapproved request")
    return expanded, {
        "input": logical_input_path,
        "document_url": document_url,
        "contexts": sorted(context_records, key=lambda item: item["logical_path"]),
        "loader_request_count": len(loader_requests),
        "network_request_count": 0,
        "expanded_node_count": len(expanded),
    }


def graph_from_expanded_jsonld(expanded: list[Any], public_id: str):
    try:
        from rdflib import Graph
    except ImportError as exc:
        raise ModelValidationError("RDFLib is not importable") from exc
    graph = Graph()
    try:
        graph.parse(
            data=json.dumps(expanded, ensure_ascii=False),
            format="json-ld",
            publicID=public_id,
        )
    except Exception as exc:
        raise ModelValidationError("expanded JSON-LD cannot be parsed as RDF") from exc
    return graph


def parse_turtle(path: Path, logical_path: str):
    try:
        from rdflib import Graph
    except ImportError as exc:
        raise ModelValidationError("RDFLib is not importable") from exc
    graph = Graph()
    try:
        graph.parse(
            data=path.read_text(encoding="utf-8-sig"),
            format="turtle",
            publicID=_public_url(logical_path),
        )
    except Exception as exc:
        raise ModelValidationError("Turtle artifact cannot be parsed") from exc
    return graph


def target_activation_count(data_graph: Any, shapes_graph: Any) -> int:
    from rdflib import Namespace
    from rdflib.namespace import RDF

    sh = Namespace("http://www.w3.org/ns/shacl#")
    activations: set[tuple[Any, Any]] = set()
    for shape, target_class in shapes_graph.subject_objects(sh.targetClass):
        for focus in data_graph.subjects(RDF.type, target_class):
            activations.add((shape, focus))
    for shape, focus in shapes_graph.subject_objects(sh.targetNode):
        activations.add((shape, focus))
    for shape, predicate in shapes_graph.subject_objects(sh.targetSubjectsOf):
        for focus in data_graph.subjects(predicate, None):
            activations.add((shape, focus))
    for shape, predicate in shapes_graph.subject_objects(sh.targetObjectsOf):
        for focus in data_graph.objects(None, predicate):
            activations.add((shape, focus))
    return len(activations)


def _single_object(graph: Any, subject: Any, predicate: Any, field: str):
    values = list(graph.objects(subject, predicate))
    if len(values) != 1:
        raise ModelValidationError(
            f"SHACL ValidationResult field {field} must occur exactly once"
        )
    return values[0]


def _optional_object(graph: Any, subject: Any, predicate: Any, field: str):
    values = list(graph.objects(subject, predicate))
    if len(values) > 1:
        raise ModelValidationError(
            f"SHACL ValidationResult field {field} must occur at most once"
        )
    return values[0] if values else None


def _stable_term(term: Any) -> str | None:
    if term is None:
        return None
    from rdflib import BNode

    if isinstance(term, BNode):
        return "<ANONYMOUS_RDF_TERM>"
    return str(term)


def normalize_shacl_report(report_graph: Any) -> dict[str, Any]:
    """Parse the report graph structurally; the conforms boolean is diagnostic."""
    from rdflib import Graph, Namespace
    from rdflib.namespace import RDF

    if not isinstance(report_graph, Graph):
        raise ModelValidationError("pySHACL did not return an RDF report graph")
    sh = Namespace("http://www.w3.org/ns/shacl#")
    reports = set(report_graph.subjects(RDF.type, sh.ValidationReport))
    if len(reports) != 1:
        raise ModelValidationError("SHACL report graph must contain one ValidationReport")
    report = next(iter(reports))
    linked = set(report_graph.objects(report, sh.result))
    typed = set(report_graph.subjects(RDF.type, sh.ValidationResult))
    if linked != typed:
        raise ModelValidationError(
            "SHACL report links and typed ValidationResult nodes differ"
        )
    conforms = _single_object(report_graph, report, sh.conforms, "conforms")
    rows: list[dict[str, Any]] = []
    severity_names = {
        str(sh.Violation): "Violation",
        str(sh.Warning): "Warning",
        str(sh.Info): "Info",
    }
    severity_counts = {"Violation": 0, "Warning": 0, "Info": 0}
    for result in linked:
        source = _single_object(report_graph, result, sh.sourceShape, "sourceShape")
        focus = _single_object(report_graph, result, sh.focusNode, "focusNode")
        component = _single_object(
            report_graph,
            result,
            sh.sourceConstraintComponent,
            "sourceConstraintComponent",
        )
        severity = _single_object(
            report_graph, result, sh.resultSeverity, "resultSeverity"
        )
        path = _optional_object(report_graph, result, sh.resultPath, "resultPath")
        value = _optional_object(report_graph, result, sh.value, "value")
        messages = list(report_graph.objects(result, sh.resultMessage))
        if len(messages) != 1:
            raise ModelValidationError(
                "SHACL ValidationResult must contain exactly one resultMessage"
            )
        severity_iri = str(severity)
        severity_name = severity_names.get(severity_iri)
        if severity_name is None:
            raise ModelValidationError("SHACL result uses an unknown severity")
        severity_counts[severity_name] += 1
        rows.append(
            {
                "source_shape": _stable_term(source),
                "focus_node": _stable_term(focus),
                "path": _stable_term(path),
                "constraint_component": _stable_term(component),
                "severity": severity_iri,
                "severity_name": severity_name,
                "message": _stable_term(messages[0]),
                "value": _stable_term(value),
            }
        )
    rows.sort(
        key=lambda item: (
            item["source_shape"] or "",
            item["focus_node"] or "",
            item["path"] or "",
            item["constraint_component"] or "",
            item["severity"],
            item["message"] or "",
            item["value"] or "",
        )
    )
    business_status = (
        "FAIL"
        if severity_counts["Violation"]
        else "INAPPLICABLE"
        if severity_counts["Warning"]
        else "PASS"
    )
    return {
        "report_conforms": bool(conforms.toPython()),
        "report_triple_count": len(report_graph),
        "result_count": len(rows),
        "severity_counts": severity_counts,
        "business_status": business_status,
        "results": rows,
    }


def run_shacl_validation(data_graph: Any, shapes_graph: Any) -> dict[str, Any]:
    try:
        from pyshacl import validate
    except ImportError as exc:
        raise ModelValidationError("pySHACL is not importable") from exc
    if data_graph is shapes_graph:
        raise ModelValidationError("SHACL data and shapes graphs must be separate")
    before_count = len(data_graph)
    before_triples = frozenset(data_graph)
    shapes_before_count = len(shapes_graph)
    shapes_before_triples = frozenset(shapes_graph)
    activation_count = target_activation_count(data_graph, shapes_graph)
    try:
        from rdflib import Graph
    except ImportError as exc:
        raise ModelValidationError("RDFLib is not importable") from exc
    validation_shapes = Graph()
    for triple in shapes_graph:
        validation_shapes.add(triple)
    logger = logging.getLogger("pyshacl-validate")
    previous_disabled = logger.disabled
    kwargs = dict(SHACL_ENGINE_CONFIG)
    try:
        logger.disabled = True
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            conforms, report_graph, _ = validate(
                data_graph=data_graph,
                shacl_graph=validation_shapes,
                ont_graph=None,
                **kwargs,
            )
    except Exception as exc:
        raise ModelValidationError("pySHACL validation failed") from exc
    finally:
        logger.disabled = previous_disabled
    if len(data_graph) != before_count or frozenset(data_graph) != before_triples:
        raise ModelValidationError("pySHACL mutated the submitted data graph")
    if (
        len(shapes_graph) != shapes_before_count
        or frozenset(shapes_graph) != shapes_before_triples
    ):
        raise ModelValidationError("pySHACL mutated the submitted shapes graph")
    report = normalize_shacl_report(report_graph)
    if bool(conforms) != report["report_conforms"]:
        raise ModelValidationError("pySHACL and report graph conforms values differ")
    return {
        "engine_config": dict(SHACL_ENGINE_CONFIG),
        "graphs_separate": True,
        "ontology_graph_supplied": False,
        "data_triple_count": before_count,
        "shapes_triple_count": shapes_before_count,
        "shapes_graph_unchanged": True,
        "throwaway_shapes_graph_supplied": True,
        "target_activation_count": activation_count,
        "pyshacl_conforms": bool(conforms),
        **report,
    }


__all__ = [
    "ModelValidationError",
    "SHACL_ENGINE_CONFIG",
    "graph_from_expanded_jsonld",
    "normalize_shacl_report",
    "offline_expand_jsonld",
    "parse_turtle",
    "run_shacl_validation",
    "target_activation_count",
]
