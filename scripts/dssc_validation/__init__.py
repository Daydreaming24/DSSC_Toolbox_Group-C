"""Internal validation support package for Phase 01+ entrypoints.

Not a public installable package. Loaded only by repository scripts under
``scripts/`` via explicit path insertion. Do not put shell commands or
arbitrary module paths in the suite registry.
"""

from __future__ import annotations

__all__ = [
    "EXPECTED_PYTHON_VERSION",
    "EXPECTED_ENSUREPIP_VERSION",
    "FIXED_PIP_VERSION",
    "PUBLIC_SUITE_IDS",
]

EXPECTED_PYTHON_VERSION = "3.12.10"
EXPECTED_ENSUREPIP_VERSION = "25.0.1"
FIXED_PIP_VERSION = "25.0.1"
PUBLIC_SUITE_IDS = (
    "frozen",
    "environment",
    "baseline",
    "traceability",
    "v0.4-model",
    "v0.4",
    "all",
)
