"""Parse hash locks and compare the installed distribution set exactly."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any


PYPI_INDEX = "https://pypi.org/simple"
_EXACT_PIN = re.compile(
    r"(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"==(?P<version>[A-Za-z0-9][A-Za-z0-9.!+_-]*)"
)


def canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


@dataclass
class LockedDistribution:
    name: str
    canonical_name: str
    version: str
    marker: str | None
    applicable: bool
    hashes: list[str] = field(default_factory=list)


@dataclass
class LockAudit:
    path: Path
    entries: list[LockedDistribution]
    issues: list[str]
    index_url: str | None

    @property
    def ok(self) -> bool:
        return not self.issues and bool(self.entries)


def parse_hash_lock(path: Path) -> LockAudit:
    issues: list[str] = []
    entries: list[LockedDistribution] = []
    index_url: str | None = None
    current: LockedDistribution | None = None

    def finish_current() -> None:
        nonlocal current
        if current is None:
            return
        if not current.hashes:
            issues.append(f"{current.name}: no SHA-256 hashes")
        entries.append(current)
        current = None

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        return LockAudit(path, [], [f"cannot read lock: {exc}"], None)

    for line_number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("--index-url "):
            finish_current()
            value = stripped.split(maxsplit=1)[1].strip()
            if index_url is not None and index_url != value:
                issues.append(f"line {line_number}: conflicting index URL")
            index_url = value
            continue
        if stripped.startswith("--hash="):
            if current is None:
                issues.append(f"line {line_number}: hash without requirement")
                continue
            token = stripped.rstrip("\\").strip()
            if not re.fullmatch(r"--hash=sha256:[0-9a-fA-F]{64}", token):
                issues.append(f"line {line_number}: invalid SHA-256 hash token")
            else:
                current.hashes.append(token.split(":", 1)[1].lower())
            continue
        if stripped.startswith("--"):
            finish_current()
            issues.append(f"line {line_number}: unsupported pip option {stripped!r}")
            continue

        finish_current()
        requirement_text = stripped.rstrip("\\").strip()
        if ";" in requirement_text:
            issues.append(
                f"line {line_number}: environment markers are forbidden in the shared lock"
            )
            continue
        if "@" in requirement_text or "://" in requirement_text:
            issues.append(f"line {line_number}: direct URL/VCS requirement is forbidden")
            continue
        match = _EXACT_PIN.fullmatch(requirement_text)
        if match is None:
            issues.append(
                f"line {line_number}: requirement must be a plain name with one exact == pin"
            )
            continue
        name = match.group("name")
        version = match.group("version")
        current = LockedDistribution(
            name=name,
            canonical_name=canonical_name(name),
            version=version,
            marker=None,
            applicable=True,
        )

    finish_current()

    # pip-tools omits the default PyPI URL from the lock body even when the
    # generator receives it explicitly. Bootstrap supplies the exact URL on
    # the pip command line and metadata binds that contract. If a lock does
    # carry an index directive, only the approved URL is accepted.
    if index_url not in (None, PYPI_INDEX):
        issues.append(
            f"lock index must be {PYPI_INDEX!r}, found {index_url!r}"
        )
    names = [entry.canonical_name for entry in entries]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        issues.append("duplicate lock distribution(s): " + ", ".join(duplicates))
    if not entries:
        issues.append("lock contains 0 distributions")
    return LockAudit(path, entries, issues, index_url)


def installed_distributions() -> tuple[dict[str, str], list[str]]:
    installed: dict[str, str] = {}
    issues: list[str] = []
    for distribution in metadata.distributions():
        raw_name = distribution.metadata.get("Name")
        if not raw_name:
            issues.append("installed distribution missing Name metadata")
            continue
        name = canonical_name(raw_name)
        version = distribution.version
        if name in installed:
            issues.append(
                f"duplicate installed distribution metadata: {name} "
                f"({installed[name]} and {version})"
            )
        installed[name] = version
    return dict(sorted(installed.items())), issues


def compare_environment_to_locks(
    runtime: LockAudit,
    bootstrap: LockAudit,
) -> tuple[dict[str, Any], dict[str, str]]:
    expected: dict[str, str] = {}
    issues: list[str] = []
    for audit in (runtime, bootstrap):
        for entry in audit.entries:
            if not entry.applicable:
                continue
            previous = expected.get(entry.canonical_name)
            if previous is not None and previous != entry.version:
                issues.append(
                    f"conflicting pins across locks: {entry.canonical_name} "
                    f"{previous} vs {entry.version}"
                )
            expected[entry.canonical_name] = entry.version

    installed, installed_issues = installed_distributions()
    issues.extend(installed_issues)
    missing = sorted(set(expected) - set(installed))
    unexpected = sorted(set(installed) - set(expected))
    mismatched = sorted(
        name
        for name in set(expected) & set(installed)
        if expected[name] != installed[name]
    )
    exact = not issues and not missing and not unexpected and not mismatched
    result: dict[str, Any] = {
        "status": "PASS" if exact else "FAIL",
        "expected_count": len(expected),
        "installed_count": len(installed),
        "missing": missing,
        "unexpected": unexpected,
        "version_mismatches": mismatched,
        "issues": issues,
        "expected_versions": dict(sorted(expected.items())),
    }
    return result, installed
