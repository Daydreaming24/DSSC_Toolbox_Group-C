from __future__ import annotations

import copy
import json
from pathlib import Path

try:
    from pyld import jsonld
except ModuleNotFoundError as exc:
    from validation_common import dependency_error

    raise dependency_error("pyld") from exc

from validation_common import CheckResult, MODEL_DIR, VALIDATION_DIR, load_json, relative, write_report


def inline_local_context(document: object, source_path: Path) -> object:
    """Inline sibling JSON-LD context files so expansion does not rely on HTTP/file fetching."""
    if isinstance(document, list):
        return [inline_local_context(item, source_path) for item in document]
    if not isinstance(document, dict):
        return document

    cloned = copy.deepcopy(document)
    context = cloned.get("@context")
    if isinstance(context, str):
        context_path = source_path.parent / context
        if context_path.exists():
            cloned["@context"] = load_json(context_path).get("@context", load_json(context_path))
    elif isinstance(context, list):
        inlined = []
        for item in context:
            if isinstance(item, str) and (source_path.parent / item).exists():
                context_doc = load_json(source_path.parent / item)
                inlined.append(context_doc.get("@context", context_doc))
            else:
                inlined.append(item)
        cloned["@context"] = inlined

    for key, value in list(cloned.items()):
        if key != "@context":
            cloned[key] = inline_local_context(value, source_path)
    return cloned


def main() -> int:
    results: list[CheckResult] = []
    jsonld_files = sorted(MODEL_DIR.glob("v*/**/*.jsonld"))
    if not jsonld_files:
        results.append(CheckResult("JSON-LD artifact discovery", False, "No `.jsonld` files found."))
    for path in jsonld_files:
        try:
            raw = load_json(path)
            inlined = inline_local_context(raw, path)
            expanded = jsonld.expand(inlined)
            results.append(
                CheckResult(
                    relative(path),
                    True,
                    f"JSON parsed and JSON-LD expanded successfully into {len(expanded)} top-level node(s).",
                )
            )
        except json.JSONDecodeError as exc:
            results.append(CheckResult(relative(path), False, f"JSONDecodeError: {exc}"))
        except Exception as exc:
            results.append(CheckResult(relative(path), False, f"{exc.__class__.__name__}: {exc}"))

    ok = write_report(VALIDATION_DIR / "jsonld-validation-report.md", "JSON-LD Validation Report", results)
    print(f"JSON-LD validation report: {relative(VALIDATION_DIR / 'jsonld-validation-report.md')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
