"""Deterministic JSON and Markdown reporting for the SPARQL suite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json_text(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        separators=(",", ": "),
    ) + "\n"


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_text(value).encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json_text(value), encoding="utf-8", newline="\n")


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_report(result: dict[str, Any]) -> str:
    summary = result.get("summary", {})
    lines = [
        "# SPARQL Semantic Test Report",
        "",
        f"- Status: `{result.get('status', 'FAIL')}`",
        f"- Program status: `{result.get('program_status', 'ERROR')}`",
        f"- Exit code: `{result.get('exit_code', 1)}`",
        f"- Manifest schema version: `{result.get('manifest_schema_version', 'unknown')}`",
        f"- Discovered: `{summary.get('discovered', 0)}`",
        f"- Executed: `{summary.get('executed', 0)}`",
        f"- Passed: `{summary.get('passed', 0)}`",
        f"- Failed: `{summary.get('failed', 0)}`",
        f"- Skipped: `{summary.get('skipped', 0)}`",
        "",
        "## Authority preflight",
        "",
        "| Authority | Status | Manifest SHA-256 | Schema SHA-256 |",
        "|---|---|---|---|",
    ]
    for authority in result.get("authorities", []):
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    authority.get("id"),
                    authority.get("status"),
                    authority.get("manifest_sha256"),
                    authority.get("schema_sha256"),
                )
            )
            + " |"
        )
    registry = result.get("registry", {})
    lines.extend(
        [
            "",
            "## Registry binding",
            "",
            f"- Contract version: `{registry.get('contract_version', 'unknown')}`",
            f"- Registry SHA-256: `{registry.get('sha256', 'unknown')}`",
            "",
            "## Cases",
            "",
            "| ID | Release | Form | Required | Status | Rows/value |",
            "|---|---|---|---:|---|---|",
        ]
    )
    for case in result.get("cases", []):
        actual = case.get("actual", {})
        if case.get("query_form") == "ASK":
            value = actual.get("boolean")
        elif case.get("query_form") == "COUNT":
            value = actual.get("count")
        else:
            value = actual.get("row_count")
        lines.append(
            "| "
            + " | ".join(
                _cell(item)
                for item in (
                    case.get("id"),
                    case.get("release"),
                    case.get("query_form"),
                    str(bool(case.get("required"))).lower(),
                    case.get("status"),
                    value,
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Source bindings",
            "",
            "| Path | Roles | SHA-256 |",
            "|---|---|---|",
        ]
    )
    for source in result.get("sources", []):
        lines.append(
            "| "
            + " | ".join(
                _cell(item)
                for item in (
                    source.get("path"),
                    ", ".join(source.get("roles", [])),
                    source.get("sha256"),
                )
            )
            + " |"
        )
    lines.extend(["", "## Issues", ""])
    issues = result.get("issues", [])
    if issues:
        for issue in issues:
            lines.append(
                f"- `{_cell(issue.get('code'))}` at "
                f"`{_cell(issue.get('location'))}`: {_cell(issue.get('message'))}"
            )
    else:
        lines.append("No issues.")
    lines.extend(
        [
            "",
            "The machine-readable `results.json` is the deterministic source of truth. "
            "Runtime and platform metadata are isolated in `run-environment.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(result), encoding="utf-8", newline="\n")


__all__ = [
    "canonical_json_sha256",
    "canonical_json_text",
    "render_report",
    "write_json",
    "write_report",
]
