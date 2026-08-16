from __future__ import annotations

import re
from pathlib import Path

from validation_common import CheckResult, ROOT, VALIDATION_DIR, relative, write_report


REPO_ROOT = ROOT.parent
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
WINDOWS_ABSOLUTE_RE = re.compile(r"(^|[^A-Za-z0-9_])[A-Za-z]:[\\/]")
SCRIPT_SUFFIXES = {".py", ".ps1", ".sh", ".cmd"}


def markdown_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*.md") if "tools/semantic-treehouse/upstream" not in path.as_posix())


def script_files() -> list[Path]:
    candidates = list((ROOT / "scripts").glob("*")) + [REPO_ROOT / "Makefile", REPO_ROOT / "make.cmd"]
    return sorted(path for path in candidates if path.is_file() and (path.suffix in SCRIPT_SUFFIXES or path.name in {"Makefile", "make.cmd"}))


def is_external(target: str) -> bool:
    lowered = target.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("mailto:")
        or lowered.startswith("#")
        or lowered.startswith("app://")
    )


def normalize_target(target: str) -> str:
    cleaned = target.strip().split("#", 1)[0].strip()
    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned[1:-1].strip()
    return cleaned.replace("%20", " ")


def candidate_paths(markdown_path: Path, target: str) -> list[Path]:
    target_path = Path(target)
    candidates = []
    if target_path.is_absolute():
        candidates.append(target_path)
    else:
        candidates.extend([
            markdown_path.parent / target_path,
            ROOT / target_path,
            REPO_ROOT / target_path,
        ])
    return candidates


def check_markdown_links() -> CheckResult:
    broken: list[str] = []
    checked = 0
    for markdown_path in markdown_files():
        text = markdown_path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            raw_target = match.group(1)
            target = normalize_target(raw_target)
            if not target or is_external(target) or target.startswith("data:"):
                continue
            if WINDOWS_ABSOLUTE_RE.search(target):
                continue
            checked += 1
            if not any(path.exists() for path in candidate_paths(markdown_path, target)):
                broken.append(f"- `{relative(markdown_path)}` -> `{raw_target}`")
    detail = [f"Checked local Markdown links: {checked}"]
    if broken:
        detail.append("")
        detail.append("Broken links:")
        detail.extend(broken)
    else:
        detail.append("No broken local Markdown links detected.")
    return CheckResult("Markdown local links", not broken, "\n".join(detail))


def check_windows_paths_in_scripts() -> CheckResult:
    findings: list[str] = []
    for script_path in script_files():
        text = script_path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if WINDOWS_ABSOLUTE_RE.search(line):
                findings.append(f"- `{relative(script_path)}` line {line_number}: `{line.strip()}`")
    detail = []
    if findings:
        detail.append("Windows absolute paths found in scripts:")
        detail.extend(findings)
    else:
        detail.append("No absolute Windows-only paths found in scripts.")
    return CheckResult("Windows-only script paths", not findings, "\n".join(detail))


def main() -> int:
    results = [check_markdown_links(), check_windows_paths_in_scripts()]
    report_path = VALIDATION_DIR / "path-link-report.md"
    ok = write_report(
        report_path,
        "Path And Link Report",
        results,
        notes=[
            "Absolute Windows paths are allowed in documentation examples but not in scripts.",
            "Markdown link checking is conservative and ignores external URLs and anchors.",
        ],
    )
    print(f"Path/link report: {relative(report_path)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
