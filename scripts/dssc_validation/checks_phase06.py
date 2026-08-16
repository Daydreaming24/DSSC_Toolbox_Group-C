"""Controlled adapters for the three Phase 06 internal checks."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys
from typing import Any


_SCRIPT_MODULES = {
    "sparql": "run_sparql_tests",
    "quality": "quality_metrics",
    "governance": "validate_governance",
}


def _run_fixed_checker(name: str, context: dict[str, Any]) -> dict[str, Any]:
    """Load one repository-owned checker from a fixed, non-manifest path."""

    root = context.get("repository_root")
    if not isinstance(root, Path):
        raise ValueError("Phase 06 checker requires repository_root")
    script_dir = root / "C_Semantic_Treehouse" / "scripts"
    if not script_dir.is_dir():
        raise FileNotFoundError(f"Phase 06 script directory missing: {script_dir}")
    script_dir_text = str(script_dir)
    if script_dir_text not in sys.path:
        sys.path.insert(0, script_dir_text)
    module = import_module(_SCRIPT_MODULES[name])
    function = getattr(module, "run_component", None)
    if not callable(function):
        raise AttributeError(
            f"{_SCRIPT_MODULES[name]}.run_component is missing or not callable"
        )
    value = function(context)
    if not isinstance(value, dict):
        raise TypeError(f"{name} checker must return an object")
    return value


def run_phase06_sparql_check(context: dict[str, Any]) -> dict[str, Any]:
    return _run_fixed_checker("sparql", context)


def run_phase06_quality_check(context: dict[str, Any]) -> dict[str, Any]:
    return _run_fixed_checker("quality", context)


def run_phase06_governance_check(context: dict[str, Any]) -> dict[str, Any]:
    return _run_fixed_checker("governance", context)


__all__ = [
    "run_phase06_governance_check",
    "run_phase06_quality_check",
    "run_phase06_sparql_check",
]
