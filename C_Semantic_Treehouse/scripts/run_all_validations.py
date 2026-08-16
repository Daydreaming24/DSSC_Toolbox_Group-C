from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from validation_common import CheckResult, ROOT, VALIDATION_DIR, relative, write_report


SCRIPT_DIR = ROOT / "scripts"


def run_script(script_name: str) -> CheckResult:
    script_path = SCRIPT_DIR / script_name
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    detail = [
        f"Command: `{sys.executable} {relative(script_path)}`",
        f"Exit code: {completed.returncode}",
        "",
        "```text",
        completed.stdout.strip(),
        "```",
    ]
    return CheckResult(script_name, completed.returncode == 0, "\n".join(detail))


def main() -> int:
    scripts = [
        "validate_rdf.py",
        "validate_shacl.py",
        "validate_jsonld.py",
        "validate_jsonschema.py",
        "validate_openapi.py",
    ]
    results = [run_script(script) for script in scripts]
    ok = write_report(VALIDATION_DIR / "all-validations-report.md", "All Validations Report", results)
    print(f"All validations report: {relative(VALIDATION_DIR / 'all-validations-report.md')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
