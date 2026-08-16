"""Explicit host/container profile boundary for validation evidence."""

from __future__ import annotations

import os
import platform
import struct
from typing import Any


CONTAINER_CONTRACT_ENV = "DSSC_VALIDATION_CONTAINER_CONTRACT"
EXPECTED_CONTAINER_CONTRACT = (
    "dssc.phase01.container.v1-linux-amd64-python-3.12.10-"
    "fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db"
)


def container_contract_check() -> tuple[bool, dict[str, Any], dict[str, Any]]:
    """Validate the fixed image marker and linux/amd64 execution boundary."""
    system = platform.system()
    machine = platform.machine()
    normalized_machine = machine.lower()
    pointer_bits = struct.calcsize("P") * 8
    effective_uid = os.geteuid() if hasattr(os, "geteuid") else None
    nonroot_ok = effective_uid is not None and effective_uid != 0
    platform_ok = (
        system == "Linux"
        and normalized_machine in ("amd64", "x86_64")
        and pointer_bits == 64
    )
    actual_marker = os.environ.get(CONTAINER_CONTRACT_ENV, "")
    marker_ok = actual_marker == EXPECTED_CONTAINER_CONTRACT
    result = {
        "status": "PASS" if platform_ok and marker_ok and nonroot_ok else "FAIL",
        "expected_platform": "linux/amd64",
        "platform_match": platform_ok,
        "nonroot_match": nonroot_ok,
        "contract_marker_match": marker_ok,
    }
    machine_details = {
        "system": system,
        "machine": machine,
        "pointer_bits": pointer_bits,
        "effective_uid": effective_uid,
        "contract_environment_variable": CONTAINER_CONTRACT_ENV,
        "contract_marker": actual_marker or None,
    }
    return platform_ok and marker_ok and nonroot_ok, result, machine_details
