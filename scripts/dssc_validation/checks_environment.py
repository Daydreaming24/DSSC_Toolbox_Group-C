"""Environment check component — reuses doctor core logic."""

from __future__ import annotations

from typing import Any

from dssc_validation.doctor_core import run_doctor


def run_environment_check(context: dict[str, Any]) -> dict[str, Any]:
    profile = context.get("profile")
    if profile not in ("host", "container"):
        return {
            "status": "FAIL",
            "program_status": "ERROR",
            "message": "environment check requires explicit profile host|container",
            "details": {},
        }

    report, machine = run_doctor(
        root=context["repository_root"],
        profile=profile,
    )
    overall = report.get("overall_status", "FAIL")
    ok = overall == "PASS"
    return {
        "status": "PASS" if ok else "FAIL",
        "program_status": "SUCCESS" if ok else "ERROR",
        "message": f"environment doctor overall_status={overall} profile={profile}",
        "details": {"doctor": report},
        "machine_details": {"doctor": machine},
    }
