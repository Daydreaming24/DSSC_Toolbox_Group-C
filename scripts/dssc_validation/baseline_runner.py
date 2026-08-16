"""Deterministic, offline execution core for the v0.1-v0.3 baseline.

The caller is responsible for schema, semantic, existence, and SHA-256
preflight of the manifest.  This module deliberately performs no writes and
has no network fallback.  Optional validator dependencies are imported only
inside their category runner so importing the controlled entrypoint catalog
does not make unrelated suites depend on them.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import logging
import re
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname


EXPECTED_CASE_COUNT = 33
EXPECTED_CATEGORY_COUNTS: dict[str, int] = {
    "rdf": 7,
    "jsonld": 10,
    "shacl": 5,
    "jsonschema": 2,
    "openapi": 1,
    "sparql": 8,
}

_SHACL_ENGINE_CONFIG = {
    "inference": "none",
    "advanced": False,
    "abort_on_first": False,
    "meta_shacl": True,
    "allow_warnings": False,
    "allow_infos": False,
}
_JSON_SCHEMA_ENGINE_CONFIG = {"draft": "draft-07", "format_checker": True}
_OPENAPI_ENGINE_CONFIG = {"full_validation": True, "network_allowed": False}
_SPARQL_ENGINE_CONFIG = {
    "comparison": "exact-tsv",
    "sort_rows": True,
    "preserve_duplicates": True,
}

_WINDOWS_ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)")
_POSIX_ABSOLUTE = re.compile(r"(?<![:/A-Za-z0-9])/(?!/)[^\s\"'=,;]+")


class BaselineExecutionError(RuntimeError):
    """A stable fail-closed execution error."""


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _stable_error(exc: Exception, root: Path) -> dict[str, str]:
    """Return useful diagnostics without leaking machine-local paths."""
    message = " ".join(str(exc).split()) or "execution failed"
    replacements = {
        str(root.resolve()): "<REPO_ROOT>",
        root.resolve().as_posix(): "<REPO_ROOT>",
        root.resolve().as_uri(): "<REPO_ROOT>",
    }
    for raw, replacement in sorted(
        replacements.items(), key=lambda item: len(item[0]), reverse=True
    ):
        message = message.replace(raw, replacement)
        message = message.replace(raw.replace("\\", "/"), replacement)
    message = re.sub(r"file://[^\s\"']+", "<LOCAL_FILE_URI>", message)
    message = _WINDOWS_ABSOLUTE.sub("<ABSOLUTE_PATH>", message)
    message = _POSIX_ABSOLUTE.sub("<ABSOLUTE_PATH>", message)
    if len(message) > 500:
        message = message[:497] + "..."
    return {"type": exc.__class__.__name__, "message": message}


def _assertion(
    name: str,
    expected: Any,
    actual: Any,
    passed: bool | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "expected": expected,
        "actual": actual,
        "passed": expected == actual if passed is None else bool(passed),
    }


def _count_matches(oracle: dict[str, Any], actual: int) -> bool:
    if "exact" in oracle:
        return actual == oracle["exact"]
    return oracle["minimum"] <= actual <= oracle["maximum"]


def _json_pointer(parts: Any) -> str:
    encoded = []
    for part in parts:
        encoded.append(str(part).replace("~", "~0").replace("/", "~1"))
    return "" if not encoded else "/" + "/".join(encoded)


def _pointer_tokens(pointer: str) -> list[str]:
    """Convert RFC 6901 text to stable tokens for normalized evidence.

    The generic evidence guard intentionally rejects slash-leading strings as
    possible absolute paths.  Token arrays retain the exact JSON Pointer
    location without creating that ambiguity.
    """
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise BaselineExecutionError("JSON Pointer must be empty or slash-prefixed")
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def _unwrap_manifest(value: Any) -> dict[str, Any]:
    """Accept a manifest, a JSON-safe wrapper, or the preflight dataclass."""
    if isinstance(value, dict):
        nested = value.get("manifest")
        if isinstance(nested, dict):
            return nested
        return value
    nested = getattr(value, "manifest", None)
    if isinstance(nested, dict):
        return nested
    raise BaselineExecutionError("baseline manifest must be an object")


def _root_from_input(value: Any, explicit_root: Path | None) -> Path | None:
    if explicit_root is not None:
        return explicit_root
    candidate = getattr(value, "root", None)
    return candidate if isinstance(candidate, Path) else None


def _repository_root(root: Path | None) -> Path:
    candidate = root if root is not None else Path(__file__).resolve().parents[2]
    try:
        resolved = candidate.resolve()
    except OSError as exc:
        raise BaselineExecutionError("repository root cannot be resolved") from exc
    if not resolved.is_dir():
        raise BaselineExecutionError("repository root is not a directory")
    return resolved


def _artifact_refs(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _artifact_refs(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _artifact_refs(item)


def _walk_document_refs(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref":
                yield item
            yield from _walk_document_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_document_refs(item)


def _preflight_issues(manifest: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if manifest.get("suite") != "baseline":
        issues.append("suite must be baseline")

    artifacts = manifest.get("artifacts")
    artifact_ids: list[str] = []
    if isinstance(artifacts, list):
        artifact_ids = [
            item.get("id")
            for item in artifacts
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        if len(artifact_ids) != len(artifacts):
            issues.append("every artifact must have a string id")
        if len(artifact_ids) != len(set(artifact_ids)):
            issues.append("artifact ids must be unique")
    else:
        issues.append("artifacts must be an array")

    cases = manifest.get("cases")
    if not isinstance(cases, list):
        issues.append("cases must be an array")
        return issues
    if len(cases) != EXPECTED_CASE_COUNT:
        issues.append(f"exactly {EXPECTED_CASE_COUNT} cases are required")

    case_ids = [
        case.get("id")
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    ]
    if len(case_ids) != len(cases):
        issues.append("every case must have a string id")
    if len(case_ids) != len(set(case_ids)):
        issues.append("case ids must be unique")
    if manifest.get("required_case_ids") != case_ids:
        issues.append("required_case_ids must exactly equal cases in manifest order")

    category_counts = Counter(
        case.get("category") for case in cases if isinstance(case, dict)
    )
    if dict(sorted(category_counts.items())) != EXPECTED_CATEGORY_COUNTS:
        issues.append("baseline category counts do not equal the fixed 33-case contract")

    known_artifacts = set(artifact_ids)
    for case in cases:
        if not isinstance(case, dict):
            issues.append("every case must be an object")
            continue
        case_id = case.get("id", "<unknown>")
        if case.get("enabled") is not True:
            issues.append(f"case {case_id} is disabled")
        if case.get("required") is not True:
            issues.append(f"case {case_id} is not required")
        for artifact_id in _artifact_refs(case.get("artifact_refs", {})):
            if artifact_id not in known_artifacts:
                issues.append(f"case {case_id} references an unknown artifact id")
    return sorted(set(issues))


class _ExecutionContext:
    def __init__(self, manifest: dict[str, Any], root: Path) -> None:
        self.manifest = manifest
        self.root = root
        self.artifacts = {item["id"]: item for item in manifest["artifacts"]}
        self._json_cache: dict[str, Any] = {}
        self._expanded_cache: dict[tuple[str, tuple[str, ...]], list[Any]] = {}
        self._sparql_graph_cache: dict[tuple[tuple[str, ...], tuple[str, ...]], Any] = {}

    def artifact(self, artifact_id: str) -> dict[str, Any]:
        try:
            return self.artifacts[artifact_id]
        except KeyError as exc:
            raise BaselineExecutionError("unknown artifact id") from exc

    def path(self, artifact_id: str) -> Path:
        record = self.artifact(artifact_id)
        raw = record.get("path")
        if not isinstance(raw, str):
            raise BaselineExecutionError("artifact path must be a string")
        posix = PurePosixPath(raw)
        if (
            posix.is_absolute()
            or ".." in posix.parts
            or "\\" in raw
            or (posix.parts and ":" in posix.parts[0])
        ):
            raise BaselineExecutionError("artifact path is not repository-relative POSIX")
        candidate = (self.root / Path(*posix.parts)).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise BaselineExecutionError("artifact path escapes repository") from exc
        if not candidate.is_file():
            raise BaselineExecutionError("artifact file is missing")
        return candidate

    def stable_public_id(self, artifact_id: str) -> str:
        raw = self.artifact(artifact_id)["path"]
        return "https://dssc.local/repository/" + raw

    def json_document(self, artifact_id: str) -> Any:
        if artifact_id not in self._json_cache:
            try:
                self._json_cache[artifact_id] = json.loads(
                    self.path(artifact_id).read_text(encoding="utf-8-sig")
                )
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise BaselineExecutionError("JSON artifact cannot be parsed") from exc
        return copy.deepcopy(self._json_cache[artifact_id])

    def expanded_jsonld(
        self, artifact_id: str, local_context_ids: list[str]
    ) -> list[Any]:
        key = (artifact_id, tuple(local_context_ids))
        if key in self._expanded_cache:
            return copy.deepcopy(self._expanded_cache[key])

        try:
            from pyld import jsonld
        except ImportError as exc:
            raise BaselineExecutionError("PyLD is not importable") from exc

        input_path = self.path(artifact_id)
        allowed: dict[Path, tuple[str, Any]] = {}
        loader_failures: list[str] = []
        for context_id in local_context_ids:
            path = self.path(context_id).resolve()
            allowed[path] = (path.as_uri(), self.json_document(context_id))

        def local_loader(url: str, options: dict[str, Any] | None = None):
            del options
            parsed = urlparse(url)
            if parsed.scheme.lower() in ("http", "https"):
                loader_failures.append(
                    "JSON-LD external context request was blocked before network access"
                )
                raise BaselineExecutionError(
                    loader_failures[-1]
                )
            if parsed.scheme and parsed.scheme.lower() != "file":
                loader_failures.append(
                    "JSON-LD context uses a forbidden URL scheme"
                )
                raise BaselineExecutionError(
                    loader_failures[-1]
                )
            try:
                if parsed.scheme.lower() == "file":
                    if parsed.netloc not in ("", "localhost"):
                        loader_failures.append(
                            "JSON-LD non-local file context is forbidden"
                        )
                        raise BaselineExecutionError(
                            loader_failures[-1]
                        )
                    candidate = Path(url2pathname(unquote(parsed.path))).resolve()
                else:
                    candidate = (input_path.parent / unquote(parsed.path)).resolve()
            except (OSError, ValueError) as exc:
                raise BaselineExecutionError(
                    "JSON-LD context path cannot be resolved"
                ) from exc
            if candidate not in allowed:
                loader_failures.append(
                    "JSON-LD context is not declared in local_contexts"
                )
                raise BaselineExecutionError(
                    loader_failures[-1]
                )
            document_url, document = allowed[candidate]
            return {
                "contextUrl": None,
                "documentUrl": document_url,
                "document": copy.deepcopy(document),
            }

        try:
            expanded = jsonld.expand(
                self.json_document(artifact_id),
                options={
                    "base": input_path.as_uri(),
                    "documentLoader": local_loader,
                },
            )
        except BaselineExecutionError:
            raise
        except Exception as exc:  # PyLD exposes several implementation exceptions.
            if loader_failures:
                raise BaselineExecutionError(loader_failures[0]) from exc
            raise BaselineExecutionError("JSON-LD offline expansion failed") from exc
        if not isinstance(expanded, list):
            raise BaselineExecutionError("JSON-LD expansion did not return a list")
        self._expanded_cache[key] = copy.deepcopy(expanded)
        return expanded

    def turtle_graph(self, artifact_id: str):
        try:
            from rdflib import Graph
        except ImportError as exc:
            raise BaselineExecutionError("RDFLib is not importable") from exc
        graph = Graph()
        try:
            graph.parse(
                data=self.path(artifact_id).read_text(encoding="utf-8-sig"),
                format="turtle",
                publicID=self.stable_public_id(artifact_id),
            )
        except Exception as exc:
            raise BaselineExecutionError("Turtle artifact cannot be parsed") from exc
        return graph

    def jsonld_graph(self, artifact_id: str, local_context_ids: list[str]):
        try:
            from rdflib import Graph
        except ImportError as exc:
            raise BaselineExecutionError("RDFLib is not importable") from exc
        expanded = self.expanded_jsonld(artifact_id, local_context_ids)
        graph = Graph()
        try:
            graph.parse(
                data=json.dumps(expanded, ensure_ascii=False),
                format="json-ld",
                publicID=self.stable_public_id(artifact_id),
            )
        except Exception as exc:
            raise BaselineExecutionError(
                "expanded JSON-LD cannot be loaded as an RDF graph"
            ) from exc
        return graph

    def sparql_graph(
        self, graph_input_ids: list[str], local_context_ids: list[str]
    ):
        key = (tuple(graph_input_ids), tuple(local_context_ids))
        if key in self._sparql_graph_cache:
            return self._sparql_graph_cache[key]
        try:
            from rdflib import Graph
        except ImportError as exc:
            raise BaselineExecutionError("RDFLib is not importable") from exc
        shared = Graph()
        for artifact_id in graph_input_ids:
            kind = self.artifact(artifact_id).get("kind")
            if kind in ("ontology", "shapes"):
                part = self.turtle_graph(artifact_id)
            elif kind == "data":
                part = self.jsonld_graph(artifact_id, local_context_ids)
            else:
                raise BaselineExecutionError(
                    "SPARQL graph input has an unsupported artifact kind"
                )
            for triple in part:
                shared.add(triple)
        self._sparql_graph_cache[key] = shared
        return shared


def _finalize_case(
    case: dict[str, Any],
    actual_business_status: str,
    assertions: list[dict[str, Any]],
) -> dict[str, Any]:
    assertions = list(assertions)
    assertions.append(
        _assertion(
            "business_status",
            case["expected_business_status"],
            actual_business_status,
        )
    )
    assertions.sort(key=lambda item: item["name"])
    oracle_match = all(item["passed"] for item in assertions)
    actual_program_status = "SUCCESS" if oracle_match else "ERROR"
    expected_program_status = case["expected_program_status"]
    passed = oracle_match and actual_program_status == expected_program_status
    return {
        "id": case["id"],
        "category": case["category"],
        "release": case["release"],
        "validator": case["validator"],
        "expected_business_status": case["expected_business_status"],
        "actual_business_status": actual_business_status,
        "expected_program_status": expected_program_status,
        "actual_program_status": actual_program_status,
        "oracle_match": oracle_match,
        "passed": passed,
        "message": "case matched oracle" if passed else "case did not match oracle",
        "assertions": assertions,
    }


def _error_case(
    case: dict[str, Any], exc: Exception, root: Path
) -> dict[str, Any]:
    error = _stable_error(exc, root)
    return {
        "id": case.get("id", "<unknown>"),
        "category": case.get("category", "<unknown>"),
        "release": case.get("release", "<unknown>"),
        "validator": case.get("validator", "<unknown>"),
        "expected_business_status": case.get("expected_business_status"),
        "actual_business_status": "UNTESTABLE",
        "expected_program_status": case.get("expected_program_status"),
        "actual_program_status": "ERROR",
        "oracle_match": False,
        "passed": False,
        "message": f"{error['type']}: {error['message']}",
        "assertions": [
            _assertion(
                "execution",
                {"status": "SUCCESS"},
                {"status": "ERROR", "error": error},
                False,
            )
        ],
    }


def _run_rdf(case: dict[str, Any], context: _ExecutionContext):
    graph = context.turtle_graph(case["artifact_refs"]["input"])
    count = len(graph)
    oracle = case["oracle"]
    assertions = [
        _assertion("parse_success", oracle["parse_success"], True),
        _assertion("triple_count", oracle["expected_triple_count"], count),
    ]
    return "PASS", assertions


def _run_jsonld(case: dict[str, Any], context: _ExecutionContext):
    refs = case["artifact_refs"]
    expanded = context.expanded_jsonld(refs["input"], refs["local_contexts"])
    oracle = case["oracle"]
    assertions = [
        _assertion("json_parse_success", oracle["json_parse_success"], True),
        _assertion(
            "network_request_count", oracle["network_request_count"], 0
        ),
        _assertion(
            "offline_expansion_success", oracle["offline_expansion_success"], True
        ),
        _assertion(
            "top_level_node_count",
            oracle["expected_top_level_node_count"],
            len(expanded),
        ),
    ]
    return "PASS", assertions


def _target_activation_count(data_graph: Any, shapes_graph: Any) -> int:
    from rdflib.namespace import RDF
    from rdflib import Namespace

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
        raise BaselineExecutionError(
            f"SHACL ValidationResult field {field} must occur exactly once"
        )
    return values[0]


def _stable_rdf_term(term: Any) -> str:
    from rdflib import BNode, Literal, URIRef

    if isinstance(term, URIRef):
        return str(term)
    if isinstance(term, Literal):
        return str(term)
    if isinstance(term, BNode):
        return "<ANONYMOUS_RDF_TERM>"
    return str(term)


def _normalized_source_shape(
    source: Any, result_path: Any, shapes_graph: Any
) -> dict[str, str]:
    from rdflib import BNode, Namespace, URIRef
    from rdflib.namespace import RDF

    sh = Namespace("http://www.w3.org/ns/shacl#")
    if isinstance(source, URIRef):
        return {"kind": "named-shape", "iri": str(source)}
    if not isinstance(source, BNode):
        raise BaselineExecutionError("SHACL sourceShape has an unsupported term type")
    owners = sorted(
        {
            str(owner)
            for owner in shapes_graph.subjects(sh.property, source)
            if isinstance(owner, URIRef)
            and (owner, RDF.type, sh.NodeShape) in shapes_graph
        }
    )
    if len(owners) != 1:
        raise BaselineExecutionError(
            "anonymous SHACL sourceShape must have one named owner NodeShape"
        )
    declared_paths = list(shapes_graph.objects(source, sh.path))
    if len(declared_paths) != 1 or declared_paths[0] != result_path:
        raise BaselineExecutionError(
            "anonymous SHACL sourceShape path must match the report resultPath"
        )
    return {
        "kind": "anonymous-property-shape",
        "owner_node_shape": owners[0],
    }


def _normalize_shacl_results(report_graph: Any, shapes_graph: Any):
    from rdflib import Graph, Namespace
    from rdflib.namespace import RDF

    if not isinstance(report_graph, Graph):
        raise BaselineExecutionError("pySHACL did not return a report graph")
    sh = Namespace("http://www.w3.org/ns/shacl#")
    reports = set(report_graph.subjects(RDF.type, sh.ValidationReport))
    if len(reports) != 1:
        raise BaselineExecutionError(
            "SHACL report graph must contain exactly one ValidationReport"
        )
    report = next(iter(reports))
    linked_results = set(report_graph.objects(report, sh.result))
    typed_results = set(report_graph.subjects(RDF.type, sh.ValidationResult))
    if linked_results != typed_results:
        raise BaselineExecutionError(
            "SHACL report result links and ValidationResult nodes differ"
        )

    conforms_term = _single_object(report_graph, report, sh.conforms, "conforms")
    report_conforms = bool(conforms_term.toPython())
    normalized_rows: list[dict[str, Any]] = []
    severity_counts = {"Violation": 0, "Warning": 0, "Info": 0}
    severity_iris = {
        str(sh.Violation): "Violation",
        str(sh.Warning): "Warning",
        str(sh.Info): "Info",
    }
    for result in linked_results:
        source = _single_object(
            report_graph, result, sh.sourceShape, "sourceShape"
        )
        focus = _single_object(report_graph, result, sh.focusNode, "focusNode")
        path = _single_object(report_graph, result, sh.resultPath, "resultPath")
        component = _single_object(
            report_graph,
            result,
            sh.sourceConstraintComponent,
            "sourceConstraintComponent",
        )
        severity = _single_object(
            report_graph, result, sh.resultSeverity, "resultSeverity"
        )
        messages = list(report_graph.objects(result, sh.resultMessage))
        if len(messages) != 1:
            raise BaselineExecutionError(
                "SHACL ValidationResult must contain exactly one resultMessage"
            )
        severity_text = _stable_rdf_term(severity)
        severity_name = severity_iris.get(severity_text)
        if severity_name is None:
            raise BaselineExecutionError("SHACL result uses an unknown severity")
        severity_counts[severity_name] += 1
        normalized_rows.append(
            {
                "source_shape": _normalized_source_shape(
                    source, path, shapes_graph
                ),
                "focus_node": _stable_rdf_term(focus),
                "path": _stable_rdf_term(path),
                "constraint_component": _stable_rdf_term(component),
                "severity": severity_text,
                "message": _stable_rdf_term(messages[0]),
            }
        )

    grouped: dict[str, dict[str, Any]] = {}
    for row in normalized_rows:
        key = _canonical(row)
        if key not in grouped:
            grouped[key] = {**row, "count": 0}
        grouped[key]["count"] += 1
    normalized = [grouped[key] for key in sorted(grouped)]
    return report_conforms, normalized, len(linked_results), severity_counts


def _run_shacl(case: dict[str, Any], context: _ExecutionContext):
    try:
        from pyshacl import validate
    except ImportError as exc:
        raise BaselineExecutionError("pySHACL is not importable") from exc

    config = case["engine_config"]
    if config != _SHACL_ENGINE_CONFIG:
        raise BaselineExecutionError("SHACL engine config differs from fixed contract")
    refs = case["artifact_refs"]
    data_graph = context.jsonld_graph(refs["data"], refs["local_contexts"])
    shapes_graph = context.turtle_graph(refs["shapes"])
    ontology_graph = (
        context.turtle_graph(refs["ontology"])
        if isinstance(refs.get("ontology"), str)
        else None
    )
    graphs_are_distinct = (
        data_graph is not shapes_graph
        and (ontology_graph is None or ontology_graph is not data_graph)
        and (ontology_graph is None or ontology_graph is not shapes_graph)
    )
    if not graphs_are_distinct:
        raise BaselineExecutionError("SHACL data, shapes, and ontology graphs overlap")
    target_count = _target_activation_count(data_graph, shapes_graph)
    pyshacl_log = logging.getLogger("pyshacl-validate")
    previous_log_disabled = pyshacl_log.disabled
    try:
        # Meta-SHACL failures in pySHACL can print a report before raising.
        # Keep the runner's sole observable output in its returned structure.
        pyshacl_log.disabled = True
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            conforms, report_graph, _report_text = validate(
                data_graph=data_graph,
                shacl_graph=shapes_graph,
                ont_graph=ontology_graph,
                inference=config["inference"],
                advanced=config["advanced"],
                abort_on_first=config["abort_on_first"],
                meta_shacl=config["meta_shacl"],
                allow_warnings=config["allow_warnings"],
                allow_infos=config["allow_infos"],
                inplace=False,
                debug=False,
                do_owl_imports=False,
            )
    except Exception as exc:
        raise BaselineExecutionError("pySHACL validation failed") from exc
    finally:
        pyshacl_log.disabled = previous_log_disabled

    (
        report_conforms,
        normalized_results,
        result_count,
        severity_counts,
    ) = _normalize_shacl_results(report_graph, shapes_graph)
    oracle = case["oracle"]
    assertions = [
        _assertion("engine_config", config, _SHACL_ENGINE_CONFIG),
        _assertion("graphs_separate", True, graphs_are_distinct),
        _assertion("owl_imports", False, False),
        _assertion("conforms", oracle["expected_conforms"], bool(conforms)),
        _assertion("report_conforms", bool(conforms), report_conforms),
        _assertion(
            "target_activation_count",
            {"minimum": oracle["expected_target_activation_minimum"]},
            target_count,
            target_count >= oracle["expected_target_activation_minimum"],
        ),
        _assertion("target_activation_nonzero", True, target_count > 0),
    ]
    expected_count = oracle["expected_result_count"]
    if isinstance(expected_count, int):
        assertions.append(_assertion("result_count", expected_count, result_count))
    else:
        assertions.append(
            _assertion(
                "result_count",
                expected_count,
                result_count,
                _count_matches(expected_count, result_count),
            )
        )

    if case["expected_business_status"] == "PASS":
        assertions.extend(
            [
                _assertion(
                    "violation_count",
                    oracle["expected_violation_count"],
                    severity_counts["Violation"],
                ),
                _assertion(
                    "warning_count",
                    oracle["expected_warning_count"],
                    severity_counts["Warning"],
                ),
                _assertion(
                    "info_count",
                    oracle["expected_info_count"],
                    severity_counts["Info"],
                ),
                _assertion("normalized_results", [], normalized_results),
            ]
        )
    else:
        expected_results = sorted(
            copy.deepcopy(oracle["expected_results"]), key=_canonical
        )
        assertions.append(
            _assertion(
                "normalized_results", expected_results, normalized_results
            )
        )

    actual_business = (
        "PASS" if bool(conforms) and result_count == 0 else "FAIL"
    )
    return actual_business, assertions


def _normalized_jsonschema_errors(errors: list[Any]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for error in errors:
        row = {
            "instance_pointer": [str(item) for item in error.absolute_path],
            "schema_pointer": [str(item) for item in error.absolute_schema_path],
            "keyword": str(error.validator),
            "message": error.message,
        }
        key = _canonical(row)
        if key not in grouped:
            grouped[key] = {**row, "count": 0}
        grouped[key]["count"] += 1
    return [grouped[key] for key in sorted(grouped)]


def _run_jsonschema(case: dict[str, Any], context: _ExecutionContext):
    try:
        from jsonschema import Draft7Validator, FormatChecker
    except ImportError as exc:
        raise BaselineExecutionError("jsonschema is not importable") from exc
    config = case["engine_config"]
    if config != _JSON_SCHEMA_ENGINE_CONFIG:
        raise BaselineExecutionError(
            "JSON Schema engine config differs from fixed contract"
        )
    refs = case["artifact_refs"]
    schema = context.json_document(refs["schema"])
    instance = context.json_document(refs["instance"])
    external_refs = [
        item
        for item in _walk_document_refs(schema)
        if not isinstance(item, str) or not item.startswith("#")
    ]
    if external_refs:
        raise BaselineExecutionError(
            "JSON Schema contains a non-local reference"
        )
    try:
        Draft7Validator.check_schema(schema)
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        errors = sorted(
            validator.iter_errors(instance),
            key=lambda error: (
                _json_pointer(error.absolute_path),
                _json_pointer(error.absolute_schema_path),
                str(error.validator),
                error.message,
            ),
        )
    except Exception as exc:
        raise BaselineExecutionError("JSON Schema validation failed") from exc

    normalized_errors = _normalized_jsonschema_errors(errors)
    oracle = case["oracle"]
    count_oracle = oracle["expected_error_count"]
    assertions = [
        _assertion("engine_config", config, _JSON_SCHEMA_ENGINE_CONFIG),
        _assertion("external_reference_count", 0, len(external_refs)),
        _assertion(
            "error_count",
            count_oracle,
            len(errors),
            _count_matches(count_oracle, len(errors)),
        ),
    ]
    if case["expected_business_status"] == "PASS":
        assertions.append(_assertion("normalized_errors", [], normalized_errors))
    else:
        expected_errors = copy.deepcopy(oracle["expected_errors"])
        for error in expected_errors:
            error["instance_pointer"] = _pointer_tokens(error["instance_pointer"])
            error["schema_pointer"] = _pointer_tokens(error["schema_pointer"])
        expected_errors.sort(key=_canonical)
        assertions.append(
            _assertion("normalized_errors", expected_errors, normalized_errors)
        )
    return ("FAIL" if errors else "PASS"), assertions


def _run_openapi(case: dict[str, Any], context: _ExecutionContext):
    try:
        import yaml
    except ImportError as exc:
        raise BaselineExecutionError("PyYAML is not importable") from exc
    try:
        from openapi_spec_validator import validate_spec
    except ImportError as exc:
        raise BaselineExecutionError(
            "openapi-spec-validator is not importable"
        ) from exc

    config = case["engine_config"]
    if config != _OPENAPI_ENGINE_CONFIG:
        raise BaselineExecutionError("OpenAPI engine config differs from fixed contract")
    document_id = case["artifact_refs"]["document"]
    try:
        document = yaml.safe_load(
            context.path(document_id).read_text(encoding="utf-8-sig")
        )
    except Exception as exc:
        raise BaselineExecutionError("OpenAPI YAML cannot be parsed") from exc
    if not isinstance(document, dict):
        raise BaselineExecutionError("OpenAPI document must be an object")
    refs = list(_walk_document_refs(document))
    external_refs = [
        item for item in refs if not isinstance(item, str) or not item.startswith("#")
    ]
    if external_refs:
        raise BaselineExecutionError(
            "OpenAPI document contains a non-local reference"
        )
    try:
        validate_spec(
            document,
            base_uri="https://dssc.local/repository/openapi-fragment.yaml",
        )
    except Exception as exc:
        raise BaselineExecutionError("full OpenAPI validation failed") from exc
    assertions = [
        _assertion("engine_config", config, _OPENAPI_ENGINE_CONFIG),
        _assertion("external_reference_count", 0, len(external_refs)),
        _assertion("full_validation", case["oracle"]["expected_valid"], True),
        _assertion("network_request_count", 0, 0),
    ]
    return "PASS", assertions


def _sparql_cell(value: Any) -> str:
    from rdflib import BNode, Literal, URIRef

    if value is None:
        return ""
    if isinstance(value, URIRef):
        text = str(value)
    elif isinstance(value, Literal):
        text = str(value)
    elif isinstance(value, BNode):
        raise BaselineExecutionError(
            "SPARQL result contains an unstable blank node"
        )
    else:
        text = str(value)
    if "\t" in text or "\r" in text or "\n" in text:
        raise BaselineExecutionError(
            "SPARQL result cell cannot be represented by the baseline TSV contract"
        )
    return text


def _run_sparql(case: dict[str, Any], context: _ExecutionContext):
    config = case["engine_config"]
    if config != _SPARQL_ENGINE_CONFIG:
        raise BaselineExecutionError("SPARQL engine config differs from fixed contract")
    refs = case["artifact_refs"]
    graph = context.sparql_graph(refs["graph_inputs"], refs["local_contexts"])
    try:
        query_text = context.path(refs["query"]).read_text(encoding="utf-8-sig")
        if re.search(r"\bSERVICE\b", query_text, flags=re.IGNORECASE):
            raise BaselineExecutionError(
                "SPARQL SERVICE is forbidden by the offline baseline contract"
            )
        query_result = graph.query(query_text)
    except BaselineExecutionError:
        raise
    except Exception as exc:
        raise BaselineExecutionError("SPARQL query execution failed") from exc
    if getattr(query_result, "type", None) != "SELECT":
        raise BaselineExecutionError("baseline SPARQL query must be SELECT")
    variables = [str(variable) for variable in query_result.vars]
    rows: list[tuple[str, ...]] = []
    for row in query_result:
        rows.append(
            tuple(_sparql_cell(row[index]) for index in range(len(variables)))
        )
    rows.sort()
    lines = ["\t".join(variables)] + ["\t".join(row) for row in rows]
    actual_bytes = ("\n".join(lines) + "\n").encode("utf-8")
    try:
        expected_bytes = context.path(refs["expected"]).read_bytes()
        expected_text = expected_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise BaselineExecutionError("expected SPARQL TSV is not UTF-8") from exc
    expected_lines = expected_text.splitlines()
    expected_variables = expected_lines[0].split("\t") if expected_lines else []
    expected_row_count = max(0, len(expected_lines) - 1)
    oracle = case["oracle"]
    assertions = [
        _assertion("engine_config", config, _SPARQL_ENGINE_CONFIG),
        _assertion("service_clause_count", 0, 0),
        _assertion("expected_tsv_variables", oracle["expected_variables"], expected_variables),
        _assertion("result_variables", oracle["expected_variables"], variables),
        _assertion(
            "expected_tsv_row_count",
            oracle["expected_row_count"],
            expected_row_count,
        ),
        _assertion("result_row_count", oracle["expected_row_count"], len(rows)),
        _assertion(
            "tsv_bytes",
            {
                "sha256": _sha256_bytes(expected_bytes),
                "utf8": expected_text,
            },
            {
                "sha256": _sha256_bytes(actual_bytes),
                "utf8": actual_bytes.decode("utf-8"),
            },
            actual_bytes == expected_bytes,
        ),
        _assertion(
            "row_materialization",
            {"sorted": True, "duplicates_preserved": True},
            {"sorted": True, "duplicates_preserved": True},
        ),
    ]
    return "PASS", assertions


_CATEGORY_RUNNERS = {
    "rdf": _run_rdf,
    "jsonld": _run_jsonld,
    "shacl": _run_shacl,
    "jsonschema": _run_jsonschema,
    "openapi": _run_openapi,
    "sparql": _run_sparql,
}


def _empty_category_counts() -> dict[str, dict[str, int]]:
    return {
        category: {
            "discovered": 0,
            "executed": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        }
        for category in EXPECTED_CATEGORY_COUNTS
    }


def _preflight_failure_result(
    manifest: dict[str, Any], issues: list[str]
) -> dict[str, Any]:
    cases = manifest.get("cases") if isinstance(manifest, dict) else []
    cases = cases if isinstance(cases, list) else []
    category_counts = _empty_category_counts()
    for case in cases:
        if not isinstance(case, dict):
            continue
        category = case.get("category")
        if category in category_counts:
            category_counts[category]["discovered"] += 1
            category_counts[category]["skipped"] += 1
    return {
        "schema": "dssc.baseline.execution.v1",
        "program_status": "ERROR",
        "message": "baseline execution preflight failed",
        "issues": issues,
        "case_results": [],
        "counts": {
            "discovered": len(cases),
            "executed": 0,
            "passed": 0,
            "failed": 0,
            "skipped": len(cases),
        },
        "category_counts": category_counts,
    }


def run_baseline_cases(
    preflight_or_manifest: Any, root: Path | None = None
) -> dict[str, Any]:
    """Execute the exact 33-case baseline and return deterministic JSON data.

    ``preflight_or_manifest`` may be the manifest itself or a preflight object
    containing it under ``manifest``.  The function reads repository artifacts
    but performs no writes and supplies no network-capable document loader.
    """
    try:
        manifest = _unwrap_manifest(preflight_or_manifest)
        input_root = _root_from_input(preflight_or_manifest, root)
        repository = _repository_root(input_root)
        issues = _preflight_issues(manifest)
    except Exception as exc:
        try:
            repository = _repository_root(root)
        except Exception:
            repository = Path(__file__).resolve().parents[2]
        return _preflight_failure_result(
            {},
            [
                f"{item['type']}: {item['message']}"
                for item in [_stable_error(exc, repository)]
            ],
        )
    if issues:
        return _preflight_failure_result(manifest, issues)

    context = _ExecutionContext(manifest, repository)
    cases: list[dict[str, Any]] = manifest["cases"]
    case_results: list[dict[str, Any]] = []
    category_counts = _empty_category_counts()
    for case in cases:
        category = case["category"]
        category_counts[category]["discovered"] += 1
        category_counts[category]["executed"] += 1
        try:
            actual_business, assertions = _CATEGORY_RUNNERS[category](case, context)
            result = _finalize_case(case, actual_business, assertions)
        except Exception as exc:  # Every validator/import/parser failure is ERROR.
            result = _error_case(case, exc, repository)
        case_results.append(result)
        if result["passed"]:
            category_counts[category]["passed"] += 1
        else:
            category_counts[category]["failed"] += 1

    passed = sum(1 for result in case_results if result["passed"])
    failed = len(case_results) - passed
    counts = {
        "discovered": len(cases),
        "executed": len(case_results),
        "passed": passed,
        "failed": failed,
        "skipped": 0,
    }
    success = (
        counts
        == {
            "discovered": EXPECTED_CASE_COUNT,
            "executed": EXPECTED_CASE_COUNT,
            "passed": EXPECTED_CASE_COUNT,
            "failed": 0,
            "skipped": 0,
        }
        and all(
            category_counts[category]["discovered"] == expected
            and category_counts[category]["executed"] == expected
            and category_counts[category]["passed"] == expected
            and category_counts[category]["failed"] == 0
            and category_counts[category]["skipped"] == 0
            for category, expected in EXPECTED_CATEGORY_COUNTS.items()
        )
    )
    return {
        "schema": "dssc.baseline.execution.v1",
        "program_status": "SUCCESS" if success else "ERROR",
        "message": (
            "all 33 baseline cases matched their oracles"
            if success
            else "one or more baseline cases failed or did not match their oracles"
        ),
        "issues": [],
        "case_results": case_results,
        "counts": counts,
        "category_counts": category_counts,
    }


__all__ = [
    "BaselineExecutionError",
    "EXPECTED_CASE_COUNT",
    "EXPECTED_CATEGORY_COUNTS",
    "run_baseline_cases",
]
