"""Controlled logical entrypoint catalog for suite components."""

from __future__ import annotations

from importlib import import_module
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dssc_validation.checks_all import run_all_composition_check
from dssc_validation.checks_baseline import run_baseline_check
from dssc_validation.checks_environment import run_environment_check
from dssc_validation.checks_frozen import run_frozen_check
from dssc_validation.checks_model import run_model_check
from dssc_validation.checks_traceability import run_traceability_check


EntrypointFn = Callable[[dict[str, Any]], dict[str, Any]]


def _lazy_v04(function_name: str) -> EntrypointFn:
    """Load Phase 05 dependencies only when a v0.4 component executes."""

    def invoke(context: dict[str, Any]) -> dict[str, Any]:
        module = import_module("dssc_validation.checks_v04")
        function = getattr(module, function_name)
        return function(context)

    return invoke


def _lazy_phase06(function_name: str) -> EntrypointFn:
    """Load Phase 06 adapters only when an internal ``all`` check executes."""

    def invoke(context: dict[str, Any]) -> dict[str, Any]:
        module = import_module("dssc_validation.checks_phase06")
        function = getattr(module, function_name)
        return function(context)

    return invoke


@dataclass(frozen=True)
class LazyEntrypoint:
    """Callable adapter with an inspectable, immutable import target."""

    target_module: str
    target_function: str

    def __call__(self, context: dict[str, Any]) -> dict[str, Any]:
        module = import_module(self.target_module)
        function = getattr(module, self.target_function)
        return function(context)


def _lazy_phase07(function_name: str) -> LazyEntrypoint:
    """Load the Phase 07 documentation checker only when ``all`` reaches it."""

    return LazyEntrypoint(
        target_module="check_documentation",
        target_function=function_name,
    )


@dataclass(frozen=True)
class CatalogEntry:
    function: EntrypointFn
    allowed_suites: frozenset[str]


ENTRYPOINT_CATALOG: dict[str, CatalogEntry] = {
    "check_frozen_files": CatalogEntry(
        function=run_frozen_check,
        allowed_suites=frozenset({"frozen"}),
    ),
    "check_environment": CatalogEntry(
        function=run_environment_check,
        allowed_suites=frozenset({"environment"}),
    ),
    "check_baseline": CatalogEntry(
        function=run_baseline_check,
        allowed_suites=frozenset({"baseline"}),
    ),
    "check_traceability": CatalogEntry(
        function=run_traceability_check,
        allowed_suites=frozenset({"traceability"}),
    ),
    "check_v04_model": CatalogEntry(
        function=run_model_check,
        allowed_suites=frozenset({"v0.4-model"}),
    ),
    "check_v04_test_case_schema": CatalogEntry(
        function=_lazy_v04("run_v04_test_case_schema_check"),
        allowed_suites=frozenset({"v0.4"}),
    ),
    "check_v04_manifest_semantics": CatalogEntry(
        function=_lazy_v04("run_v04_manifest_semantics_check"),
        allowed_suites=frozenset({"v0.4"}),
    ),
    "check_v04_fixture_hashes": CatalogEntry(
        function=_lazy_v04("run_v04_fixture_hashes_check"),
        allowed_suites=frozenset({"v0.4"}),
    ),
    "check_v04_four_state": CatalogEntry(
        function=_lazy_v04("run_v04_four_state_check"),
        allowed_suites=frozenset({"v0.4"}),
    ),
    "check_v04_report_assertions": CatalogEntry(
        function=_lazy_v04("run_v04_report_assertions_check"),
        allowed_suites=frozenset({"v0.4"}),
    ),
    "check_v04_target_activation": CatalogEntry(
        function=_lazy_v04("run_v04_target_activation_check"),
        allowed_suites=frozenset({"v0.4"}),
    ),
    "check_v04_fault_injection": CatalogEntry(
        function=_lazy_v04("run_v04_fault_injection_check"),
        allowed_suites=frozenset({"v0.4"}),
    ),
    "check_all_composition": CatalogEntry(
        function=run_all_composition_check,
        allowed_suites=frozenset({"all"}),
    ),
    "check_semantic_sparql": CatalogEntry(
        function=_lazy_phase06("run_phase06_sparql_check"),
        allowed_suites=frozenset({"all"}),
    ),
    "check_quality_metrics": CatalogEntry(
        function=_lazy_phase06("run_phase06_quality_check"),
        allowed_suites=frozenset({"all"}),
    ),
    "check_governance": CatalogEntry(
        function=_lazy_phase06("run_phase06_governance_check"),
        allowed_suites=frozenset({"all"}),
    ),
    "check_documentation": CatalogEntry(
        function=_lazy_phase07("run_documentation_check"),
        allowed_suites=frozenset({"all"}),
    ),
}

ALLOWED_ENTRYPOINT_IDS: frozenset[str] = frozenset(ENTRYPOINT_CATALOG)


def entrypoint_allowed_for_suite(entrypoint_id: str, suite_id: str) -> bool:
    entry = ENTRYPOINT_CATALOG.get(entrypoint_id)
    return entry is not None and suite_id in entry.allowed_suites


def resolve_entrypoint(entrypoint_id: str, suite_id: str) -> EntrypointFn:
    entry = ENTRYPOINT_CATALOG.get(entrypoint_id)
    if entry is None:
        raise KeyError(f"unknown entrypoint: {entrypoint_id}")
    if suite_id not in entry.allowed_suites:
        raise KeyError(
            f"entrypoint {entrypoint_id!r} is not allowed for suite {suite_id!r}"
        )
    return entry.function
