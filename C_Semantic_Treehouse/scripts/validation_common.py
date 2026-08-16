"""Shared helpers for the C Group validation harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"
VALIDATION_DIR = ROOT / "validation"


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def ensure_validation_dir() -> None:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_report(path: Path, title: str, results: Iterable[CheckResult], notes: Iterable[str] = ()) -> bool:
    ensure_validation_dir()
    result_list = list(results)
    all_passed = all(result.passed for result in result_list)
    lines = [
        f"# {title}",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Overall status: {'PASS' if all_passed else 'FAIL'}",
        "",
        "## Checks",
        "",
    ]
    for result in result_list:
        status = "PASS" if result.passed else "FAIL"
        lines.extend([f"### {result.name}", "", f"Status: {status}", "", result.detail.strip(), ""])
    note_list = [note.strip() for note in notes if note.strip()]
    if note_list:
        lines.extend(["## Notes", ""])
        for note in note_list:
            lines.append(f"- {note}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return all_passed


def dependency_error(module_name: str, install_hint: str = "python -m pip install -r C_Semantic_Treehouse/requirements.txt") -> SystemExit:
    return SystemExit(f"Missing Python dependency '{module_name}'. Install with: {install_hint}")
