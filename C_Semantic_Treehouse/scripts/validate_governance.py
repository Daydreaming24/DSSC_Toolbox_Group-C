#!/usr/bin/env python3
"""Fail-closed Phase 06 governance and provenance component."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROOT_SCRIPTS = REPOSITORY_ROOT / "scripts"
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

from governance_contract import run_governance_component  # noqa: E402


def run_component(context: dict[str, Any]) -> dict[str, Any]:
    """Run the controlled checker contract used by ``scripts/validate.py``."""

    return run_governance_component(context)


def main() -> int:
    result = run_component(
        {
            "repository_root": REPOSITORY_ROOT,
            "profile": "host",
            "suite": "all",
            "contract_version": None,
            "registry_sha256": None,
        }
    )
    print(result["message"])
    return 0 if result["program_status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
