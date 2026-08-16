#!/usr/bin/env python3
"""Fail-closed Phase 09 publication safety / privacy scanner.

Scans the publication candidate for personal absolute paths (outside approved
ZIP-internal allowlist exceptions), secrets/credentials, Git identity/history
sensitive content, source-ZIP integrity, license/redistribution decision
anchors, large/cache/macOS/Treehouse-upstream residue, and workflow /
.gitattributes / shell executable contracts.

Only standard library plus Phase 01 lock-declared dependencies (jsonschema is
not required). Runs from the repository ``.venv``.

ZIP-internal historical absolute paths are permitted **only** via the named
allowlist in ``docs/provenance/manifests/privacy-exclusions.tsv``. There is no
global ignore that silences personal-path findings inside source archives.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]

PRIVACY_EXCLUSIONS_REL = "docs/provenance/manifests/privacy-exclusions.tsv"
SOURCE_ARCHIVES_DIR_REL = "inputs/source-archives/received"
SOURCE_ZIP_SPECS: tuple[dict[str, Any], ...] = (
    {
        "filename": "DSSC_C_Semantic_Governance_Reproducible_Package_2026-06-25.zip",
        "role": "v0-core-zip",
        "sha256": "44f21783e57966c145c19e4c6edd74405bc1ace8ae2f31fae3f4bb92805d1135",
        "size_bytes": 130092,
    },
    {
        "filename": "DSSC_Tool_Learning.zip",
        "role": "task-plan-zip",
        "sha256": "ce13a59d3d3834bdc67d74616421ee9b19d262bfda8c4de69bfc7b5193012241",
        "size_bytes": 30411,
    },
)
DELIVERABLES_REL = "C_Semantic_Treehouse/manifests/deliverables.json"
WORKFLOW_REL = ".github/workflows/validate.yml"
GITATTRIBUTES_REL = ".gitattributes"
TREEHOUSE_UPSTREAM_REL = "tools/semantic-treehouse/upstream"
SHELL_EXECUTABLES = (
    "scripts/bootstrap.sh",
    "scripts/reproduce.sh",
    "scripts/validate.sh",
)
EXPECTED_CONTAINER_CONTRACT = (
    "dssc.phase01.container.v1-linux-amd64-python-3.12.10-"
    "fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db"
)


def is_gitless_validation_container(root: Path) -> bool:
    """Return true only for the declared clean-room container boundary."""

    return (
        os.environ.get("DSSC_VALIDATION_PROFILE", "").strip().casefold()
        == "container"
        and os.environ.get("DSSC_VALIDATION_CONTAINER_CONTRACT", "")
        == EXPECTED_CONTAINER_CONTRACT
        and not (root / ".git").exists()
        and root.as_posix() == "/workspace"
    )

# Soft limits for publication hygiene (tracked tree only).
MAX_SINGLE_TRACKED_FILE_BYTES = 5 * 1024 * 1024  # 5 MiB
MAX_TRACKED_TREE_BYTES = 50 * 1024 * 1024  # 50 MiB
TEXT_SCAN_MAX_BYTES = 2 * 1024 * 1024

# Binary / non-text suffixes skipped for content path/secret scan.
BINARY_SUFFIXES = frozenset(
    {
        ".zip",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".pdf",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".pyc",
        ".pyd",
        ".so",
        ".dll",
        ".exe",
        ".bin",
    }
)

FORBIDDEN_TRACKED_BASENAMES = frozenset(
    {
        ".env",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "credentials",
        "credentials.json",
        ".DS_Store",
    }
)
FORBIDDEN_TRACKED_SUFFIXES = frozenset(
    {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".pyc"}
)
FORBIDDEN_TRACKED_NAME_PARTS = (
    "__MACOSX/",
    "/__pycache__/",
    "/.venv/",
    "/node_modules/",
)

# High-confidence secret / path patterns (bytes for binary-safe scanning).
WINDOWS_USER_PATH_RE = re.compile(
    rb"(?<![A-Za-z0-9])[A-Za-z]:[\\/]Users[\\/][^\\/\r\n\t\"']+"
)
POSIX_HOME_PATH_RE = re.compile(
    rb"(?<![:A-Za-z0-9])/(?:home|Users)/[A-Za-z0-9._-]+(?:/[^\s\"']*)?"
)
# Host-personal temporary tokens only. Bare container/system ``/tmp`` paths
# (Docker tmpfs contracts, POSIX examples) are not treated as privacy leaks.
TEMP_PATH_RE = re.compile(
    rb"(?i)(?:%TEMP%|%TMP%|\$env:TEMP|\$env:TMP|\$TMPDIR|"
    rb"\$\{TEMP\}|\$\{TMP\}|"
    rb"AppData[\\/]Local[\\/]Temp|"
    rb"(?<![A-Za-z0-9])[A-Za-z]:[\\/]Users[\\/][^\\/\r\n\t\"']+[\\/]"
    rb"AppData[\\/]Local[\\/]Temp)"
)
PRIVATE_KEY_RE = re.compile(
    rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
)
TOKEN_RES = (
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
)
ENV_ASSIGNMENT_RE = re.compile(
    rb"(?m)^[ \t]*(?:export[ \t]+)?(?:"
    rb"API[_-]?KEY|ACCESS[_-]?TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|"
    rb"PRIVATE[_-]?KEY|AUTH[_-]?TOKEN|GITHUB_TOKEN|GH_TOKEN"
    rb")[ \t]*=[ \t]*['\"]?([^\s#'\"]{12,})"
)
PLACEHOLDER_VALUES = frozenset(
    {
        b"changeme",
        b"example",
        b"placeholder",
        b"redacted",
        b"replace-me",
        b"replace_me",
        b"your-token-here",
        b"xxxx",
        b"todo",
    }
)

REASON_CODES = frozenset(
    {
        "PERSONAL_ABSOLUTE_PATH",
        "WINDOWS_USER_PATH",
        "POSIX_HOME_PATH",
        "TEMPORARY_PATH",
        "SECRET_CANARY",
        "PRIVATE_KEY_MATERIAL",
        "ENV_CREDENTIAL",
        "TRACKED_SECRET_FILE",
        "TRACKED_CACHE_OR_METADATA",
        "TREEHOUSE_UPSTREAM_TRACKED",
        "SOURCE_ZIP_MISSING",
        "SOURCE_ZIP_HASH_MISMATCH",
        "SOURCE_ZIP_SIZE_MISMATCH",
        "SOURCE_ZIP_NAME_MISMATCH",
        "ZIP_PATH_NOT_ALLOWLISTED",
        "UNKNOWN_ALLOWLIST_ENTRY",
        "ALLOWLIST_MISSING",
        "GIT_AUTHOR_EMPTY",
        "GIT_HISTORY_SENSITIVE",
        "LARGE_FILE",
        "REPOSITORY_SIZE",
        "GITATTRIBUTES_MISSING",
        "SHELL_EXECUTABLE_MODE",
        "SHELL_LINE_ENDING",
        "WORKFLOW_PERMISSIONS",
        "LICENSE_DECISION_MISSING",
        "D_GROUP_DECISION_MISSING",
        "ZERO_SCAN_TARGETS",
        "CHECKER_ERROR",
    }
)


@dataclass(order=True)
class Issue:
    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


@dataclass
class CheckResult:
    ok: bool = True
    issues: list[Issue] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def add(self, code: str, location: str, message: str) -> None:
        if code not in REASON_CODES:
            code = "CHECKER_ERROR"
        self.issues.append(Issue(code=code, location=location, message=message))
        self.ok = False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_posix(path: str) -> str:
    return path.replace("\\", "/")


def git_ls_files(root: Path) -> list[str]:
    raw = subprocess.check_output(
        ["git", "ls-files", "-z"],
        cwd=root,
        stderr=subprocess.PIPE,
    )
    return sorted(p.decode("utf-8") for p in raw.split(b"\0") if p)


def git_ls_files_stage(root: Path) -> dict[str, str]:
    """Return path -> mode (e.g. 100644 / 100755) for tracked files."""
    raw = subprocess.check_output(
        ["git", "ls-files", "-s", "-z"],
        cwd=root,
        stderr=subprocess.PIPE,
    )
    modes: dict[str, str] = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        # format: <mode> <sha> <stage>\t<path>
        try:
            meta, path_b = entry.split(b"\t", 1)
            mode = meta.split(b" ", 1)[0].decode("ascii")
            modes[path_b.decode("utf-8")] = mode
        except ValueError:
            continue
    return modes


def container_candidate_files(root: Path) -> list[str]:
    """Inventory immutable image files while excluding the mounted build sink."""

    def raise_walk_error(error: OSError) -> None:
        raise error

    found: list[str] = []
    for current, directories, files in os.walk(
        root,
        topdown=True,
        onerror=raise_walk_error,
    ):
        current_path = Path(current)
        for name in directories:
            path = current_path / name
            if path.is_symlink():
                raise OSError(f"symlink-like candidate node is forbidden: {path}")
        if current_path == root:
            directories[:] = [name for name in directories if name != "build"]
        for name in files:
            path = current_path / name
            if path.is_symlink():
                raise OSError(f"symlink-like candidate node is forbidden: {path}")
            found.append(path.relative_to(root).as_posix())
    return sorted(found)


def load_privacy_allowlist(root: Path, result: CheckResult) -> dict[str, set[str]]:
    """Return role -> set of approved ZIP-internal SourcePath entries."""
    path = root / PRIVACY_EXCLUSIONS_REL
    if not path.is_file():
        result.add(
            "ALLOWLIST_MISSING",
            PRIVACY_EXCLUSIONS_REL,
            "privacy exclusions allowlist is missing",
        )
        return {}
    text = path.read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        result.add(
            "ALLOWLIST_MISSING",
            PRIVACY_EXCLUSIONS_REL,
            "privacy exclusions allowlist is empty",
        )
        return {}
    header = lines[0].split("\t")
    expected = ["RepositoryPath", "SourceRole", "SourcePath", "SHA256", "Reason"]
    if header != expected:
        result.add(
            "ALLOWLIST_MISSING",
            PRIVACY_EXCLUSIONS_REL,
            f"unexpected allowlist header {header!r}",
        )
        return {}
    by_role: dict[str, set[str]] = {}
    known_roles = {spec["role"] for spec in SOURCE_ZIP_SPECS} | {
        "v0-core-zip",
        "task-plan-zip",
        "read-only-reference",
    }
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != 5:
            result.add(
                "UNKNOWN_ALLOWLIST_ENTRY",
                PRIVACY_EXCLUSIONS_REL,
                f"malformed allowlist row: {line!r}",
            )
            continue
        _repo, role, source_path, _sha, _reason = parts
        if role not in known_roles and role not in {"read-only-reference"}:
            result.add(
                "UNKNOWN_ALLOWLIST_ENTRY",
                f"{PRIVACY_EXCLUSIONS_REL}:{role}",
                f"unknown allowlist SourceRole {role!r}",
            )
            continue
        if not source_path or ".." in source_path.split("/"):
            result.add(
                "UNKNOWN_ALLOWLIST_ENTRY",
                f"{PRIVACY_EXCLUSIONS_REL}:{source_path}",
                f"invalid allowlist SourcePath {source_path!r}",
            )
            continue
        by_role.setdefault(role, set()).add(to_posix(source_path))
    return by_role


def is_probably_text(data: bytes) -> bool:
    if not data:
        return True
    sample = data[:8192]
    if b"\0" in sample:
        return False
    # High ratio of non-printable bytes → binary.
    non_print = sum(1 for b in sample if b < 9 or (13 < b < 32 and b != 10))
    return (non_print / max(len(sample), 1)) < 0.30


def value_looks_placeholder(value: bytes) -> bool:
    lowered = value.strip().strip(b"'\"").lower()
    if lowered in PLACEHOLDER_VALUES:
        return True
    if lowered.startswith(b"<") and lowered.endswith(b">"):
        return True
    return False


_META_PATTERN_LINE = re.compile(
    rb"(?i)re\.compile\(|TEMP_TOKEN_RE|TEMP_PATH_RE|WINDOWS_USER_PATH|"
    rb"POSIX_HOME_PATH|HOME_EXPANSION|PRIVATE_KEY_RE|TOKEN_RES|"
    rb"_WINDOWS_ABSOLUTE|_POSIX_ABSOLUTE|_ASSIGNMENT_SECRET|"
    # Multi-line raw-string bodies of the detectors above (continuation lines
    # do not contain re.compile(...), but still only define patterns).
    rb"%TEMP%\|%TMP%|\\\$env:TEMP|\\\$env:TMP|AppData\[\\\\/\]Local\[\\\\/\]Temp"
)


def _line_is_meta_pattern_definition(line: bytes) -> bool:
    """True when the line defines a detector pattern rather than a real path."""
    return bool(_META_PATTERN_LINE.search(line))


def scan_bytes_for_issues(
    data: bytes,
    location: str,
    result: CheckResult,
    *,
    allow_personal_paths: bool = False,
) -> None:
    """Append content issues found in *data* for *location*."""
    if not allow_personal_paths:
        has_win = False
        has_posix = False
        has_temp = False
        for line in data.splitlines():
            if _line_is_meta_pattern_definition(line):
                continue
            if WINDOWS_USER_PATH_RE.search(line):
                has_win = True
            if POSIX_HOME_PATH_RE.search(line):
                has_posix = True
            if TEMP_PATH_RE.search(line):
                has_temp = True
        if has_win:
            result.add(
                "WINDOWS_USER_PATH",
                location,
                "Windows user-directory absolute path detected outside allowlist",
            )
        if has_posix:
            result.add(
                "POSIX_HOME_PATH",
                location,
                "POSIX home absolute path detected outside allowlist",
            )
        if has_temp:
            result.add(
                "TEMPORARY_PATH",
                location,
                "temporary directory path token detected",
            )
        if has_win or has_posix:
            result.add(
                "PERSONAL_ABSOLUTE_PATH",
                location,
                "personal absolute path detected outside approved ZIP allowlist",
            )

    if PRIVATE_KEY_RE.search(data):
        result.add(
            "PRIVATE_KEY_MATERIAL",
            location,
            "private key PEM/header material detected",
        )
    for rx in TOKEN_RES:
        if rx.search(data):
            result.add(
                "SECRET_CANARY",
                location,
                f"high-confidence token pattern matched: {rx.pattern!r}",
            )
            break
    for match in ENV_ASSIGNMENT_RE.finditer(data):
        value = match.group(1)
        if value_looks_placeholder(value):
            continue
        result.add(
            "ENV_CREDENTIAL",
            location,
            "credential-like environment assignment detected",
        )
        break


def check_tracked_filenames(tracked: Sequence[str], result: CheckResult) -> int:
    scanned = 0
    for rel in tracked:
        scanned += 1
        posix = to_posix(rel)
        name = Path(posix).name
        lower = posix.lower()
        if name in FORBIDDEN_TRACKED_BASENAMES or name.lower() in {
            n.lower() for n in FORBIDDEN_TRACKED_BASENAMES
        }:
            if name in {".DS_Store"} or name.startswith("._"):
                result.add(
                    "TRACKED_CACHE_OR_METADATA",
                    posix,
                    "macOS metadata must not be tracked",
                )
            else:
                result.add(
                    "TRACKED_SECRET_FILE",
                    posix,
                    f"forbidden secret/credential basename tracked: {name}",
                )
        suffix = Path(posix).suffix.lower()
        if suffix in FORBIDDEN_TRACKED_SUFFIXES:
            if suffix == ".pyc":
                result.add(
                    "TRACKED_CACHE_OR_METADATA",
                    posix,
                    "Python cache artifact must not be tracked",
                )
            else:
                result.add(
                    "TRACKED_SECRET_FILE",
                    posix,
                    f"forbidden secret suffix tracked: {suffix}",
                )
        for part in FORBIDDEN_TRACKED_NAME_PARTS:
            if part in f"/{lower}/" or lower.startswith(part.lstrip("/")):
                result.add(
                    "TRACKED_CACHE_OR_METADATA",
                    posix,
                    f"forbidden cache/metadata path component: {part}",
                )
                break
        if posix == TREEHOUSE_UPSTREAM_REL or posix.startswith(
            TREEHOUSE_UPSTREAM_REL + "/"
        ):
            result.add(
                "TREEHOUSE_UPSTREAM_TRACKED",
                posix,
                "Treehouse upstream checkout must remain untracked/gitignored",
            )
    return scanned


def check_tracked_content(
    root: Path,
    tracked: Sequence[str],
    result: CheckResult,
    *,
    extra_text_files: Sequence[tuple[str, Path]] = (),
) -> int:
    scanned = 0
    for rel in tracked:
        posix = to_posix(rel)
        if posix.startswith(SOURCE_ARCHIVES_DIR_REL + "/"):
            # ZIP identity is checked separately; do not full-scan zip bytes.
            continue
        path = root / posix
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in BINARY_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            result.add("CHECKER_ERROR", posix, f"stat failed: {exc}")
            continue
        if size > TEXT_SCAN_MAX_BYTES:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            result.add("CHECKER_ERROR", posix, f"read failed: {exc}")
            continue
        if not is_probably_text(data):
            continue
        scanned += 1
        scan_bytes_for_issues(data, posix, result, allow_personal_paths=False)

    for label, path in extra_text_files:
        if not path.is_file():
            result.add("CHECKER_ERROR", label, f"extra scan file missing: {path}")
            continue
        data = path.read_bytes()
        scanned += 1
        scan_bytes_for_issues(data, label, result, allow_personal_paths=False)
    return scanned


def check_source_zips(
    root: Path,
    allowlist_by_role: Mapping[str, set[str]],
    result: CheckResult,
) -> None:
    archives_dir = root / SOURCE_ARCHIVES_DIR_REL
    for spec in SOURCE_ZIP_SPECS:
        filename = spec["filename"]
        rel = f"{SOURCE_ARCHIVES_DIR_REL}/{filename}"
        path = archives_dir / filename
        if not path.is_file():
            result.add("SOURCE_ZIP_MISSING", rel, "required source ZIP is missing")
            continue
        if path.name != filename:
            result.add(
                "SOURCE_ZIP_NAME_MISMATCH",
                rel,
                f"filename {path.name!r} does not match approved {filename!r}",
            )
        size = path.stat().st_size
        if size != spec["size_bytes"]:
            result.add(
                "SOURCE_ZIP_SIZE_MISMATCH",
                rel,
                f"size {size} != approved {spec['size_bytes']}",
            )
        actual = sha256_file(path)
        if actual != spec["sha256"]:
            result.add(
                "SOURCE_ZIP_HASH_MISMATCH",
                rel,
                f"sha256 {actual} != approved {spec['sha256']}",
            )
            continue

        role = spec["role"]
        allowed_entries = allowlist_by_role.get(role, set())
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    # Normalize ZIP entry names (core ZIP uses backslashes).
                    entry = to_posix(info.filename.replace("\\", "/"))
                    # Skip macOS metadata entries by name (not personal-path content).
                    base = entry.rsplit("/", 1)[-1]
                    if entry.startswith("__MACOSX/") or base == ".DS_Store" or base.startswith("._"):
                        continue
                    try:
                        data = zf.read(info)
                    except Exception as exc:  # noqa: BLE001
                        result.add(
                            "CHECKER_ERROR",
                            f"{rel}!{entry}",
                            f"failed to read ZIP entry: {exc}",
                        )
                        continue
                    if not is_probably_text(data):
                        continue
                    # Only personal absolute paths inside ZIP require the named
                    # allowlist. Container/system temp tokens alone are not a
                    # privacy-exclusion gate for ZIP entries.
                    has_personal = bool(
                        WINDOWS_USER_PATH_RE.search(data)
                        or POSIX_HOME_PATH_RE.search(data)
                    )
                    if not has_personal:
                        continue
                    if entry in allowed_entries:
                        # Named allowlist exception — permitted.
                        continue
                    result.add(
                        "ZIP_PATH_NOT_ALLOWLISTED",
                        f"{rel}!{entry}",
                        (
                            "ZIP entry contains personal absolute paths but is "
                            "not on the named privacy-exclusions allowlist "
                            f"(role={role})"
                        ),
                    )
        except zipfile.BadZipFile as exc:
            result.add("CHECKER_ERROR", rel, f"invalid ZIP: {exc}")


def check_git_identity_and_history(root: Path, result: CheckResult) -> dict[str, Any]:
    stats: dict[str, Any] = {"authors": [], "commit_count": 0}
    try:
        authors_raw = subprocess.check_output(
            ["git", "log", "--format=%an <%ae>"],
            cwd=root,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        authors = sorted({line.strip() for line in authors_raw.splitlines() if line.strip()})
        stats["authors"] = authors
        stats["commit_count"] = len(
            [ln for ln in authors_raw.splitlines() if ln.strip()]
        )
        if not authors:
            result.add(
                "GIT_AUTHOR_EMPTY",
                "git log",
                "no commit authors found in repository history",
            )
        # Scan commit subjects/bodies for secret material only. Historical
        # prose may mention paths; author identity decisions are §6.8.
        messages = subprocess.check_output(
            ["git", "log", "--format=%B", "-n", "200"],
            cwd=root,
            stderr=subprocess.PIPE,
        )
        if PRIVATE_KEY_RE.search(messages):
            result.add(
                "GIT_HISTORY_SENSITIVE",
                "git-history:messages",
                "private key material found in recent commit messages",
            )
        for rx in TOKEN_RES:
            if rx.search(messages):
                result.add(
                    "GIT_HISTORY_SENSITIVE",
                    "git-history:messages",
                    f"token pattern found in recent commit messages: {rx.pattern!r}",
                )
                break
        for match in ENV_ASSIGNMENT_RE.finditer(messages):
            if value_looks_placeholder(match.group(1)):
                continue
            result.add(
                "GIT_HISTORY_SENSITIVE",
                "git-history:messages",
                "credential-like assignment found in recent commit messages",
            )
            break
    except subprocess.CalledProcessError as exc:
        result.add("CHECKER_ERROR", "git log", f"git log failed: {exc}")
    return stats


def check_size_and_hygiene(
    root: Path, tracked: Sequence[str], result: CheckResult
) -> dict[str, Any]:
    total = 0
    large: list[dict[str, Any]] = []
    for rel in tracked:
        path = root / rel
        if not path.is_file():
            continue
        size = path.stat().st_size
        total += size
        if size > MAX_SINGLE_TRACKED_FILE_BYTES:
            large.append({"path": to_posix(rel), "size_bytes": size})
            result.add(
                "LARGE_FILE",
                to_posix(rel),
                f"tracked file exceeds {MAX_SINGLE_TRACKED_FILE_BYTES} bytes ({size})",
            )
    if total > MAX_TRACKED_TREE_BYTES:
        result.add(
            "REPOSITORY_SIZE",
            "tracked-tree",
            f"tracked tree size {total} exceeds {MAX_TRACKED_TREE_BYTES} bytes",
        )
    # Untracked Treehouse upstream presence is allowed (gitignored); only warn
    # via stats, not as a failure.
    upstream = root / TREEHOUSE_UPSTREAM_REL
    return {
        "tracked_total_bytes": total,
        "large_files": large,
        "treehouse_upstream_present_on_disk": upstream.exists(),
        "treehouse_upstream_tracked": any(
            to_posix(p) == TREEHOUSE_UPSTREAM_REL
            or to_posix(p).startswith(TREEHOUSE_UPSTREAM_REL + "/")
            for p in tracked
        ),
    }


def check_gitattributes_and_scripts(
    root: Path,
    result: CheckResult,
    *,
    gitless_container: bool = False,
) -> None:
    ga = root / GITATTRIBUTES_REL
    if not ga.is_file():
        result.add(
            "GITATTRIBUTES_MISSING",
            GITATTRIBUTES_REL,
            ".gitattributes is required for line-ending / binary contracts",
        )
    else:
        text = ga.read_text(encoding="utf-8")
        if "eol=lf" not in text:
            result.add(
                "SHELL_LINE_ENDING",
                GITATTRIBUTES_REL,
                ".gitattributes must declare eol=lf policy",
            )
        if "inputs/source-archives/received/** -text" not in text.replace("\r\n", "\n"):
            # Accept either explicit or broader -text coverage of archives.
            if "source-archives" not in text or "-text" not in text:
                result.add(
                    "GITATTRIBUTES_MISSING",
                    GITATTRIBUTES_REL,
                    "source-archives byte-preservation (-text) rule missing",
                )

    if gitless_container:
        modes = {}
        for rel in SHELL_EXECUTABLES:
            path = root / rel
            if path.is_file():
                executable = bool(
                    path.stat().st_mode
                    & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                )
                modes[rel] = "100755" if executable else "100644"
    else:
        modes = git_ls_files_stage(root)
    for rel in SHELL_EXECUTABLES:
        mode = modes.get(rel)
        if mode is None:
            result.add(
                "SHELL_EXECUTABLE_MODE",
                rel,
                "required shell script is not tracked",
            )
            continue
        if mode != "100755":
            result.add(
                "SHELL_EXECUTABLE_MODE",
                rel,
                f"expected git mode 100755, found {mode}",
            )
        path = root / rel
        if path.is_file():
            data = path.read_bytes()
            if b"\r\n" in data:
                result.add(
                    "SHELL_LINE_ENDING",
                    rel,
                    "shell script contains CRLF line endings",
                )


def check_workflow_permissions(root: Path, result: CheckResult) -> None:
    path = root / WORKFLOW_REL
    if not path.is_file():
        result.add(
            "WORKFLOW_PERMISSIONS",
            WORKFLOW_REL,
            "validate.yml workflow is missing",
        )
        return
    text = path.read_text(encoding="utf-8")
    # Fail-closed: top-level permissions must pin contents: read.
    if not re.search(r"(?m)^permissions:\s*$", text):
        result.add(
            "WORKFLOW_PERMISSIONS",
            WORKFLOW_REL,
            "workflow must declare top-level permissions",
        )
        return
    if not re.search(r"(?m)^  contents:\s*read\s*$", text):
        result.add(
            "WORKFLOW_PERMISSIONS",
            WORKFLOW_REL,
            "workflow permissions.contents must be 'read'",
        )
    # Reject write permissions and secret dependencies at a shallow level.
    if re.search(r"(?m)^  contents:\s*write\s*$", text):
        result.add(
            "WORKFLOW_PERMISSIONS",
            WORKFLOW_REL,
            "workflow must not request contents: write",
        )
    if re.search(r"\$\{\{\s*secrets\.", text):
        result.add(
            "WORKFLOW_PERMISSIONS",
            WORKFLOW_REL,
            "workflow must not reference repository secrets expressions",
        )


def check_license_decisions(root: Path, result: CheckResult) -> None:
    path = root / DELIVERABLES_REL
    if not path.is_file():
        result.add(
            "LICENSE_DECISION_MISSING",
            DELIVERABLES_REL,
            "deliverables.json missing; cannot verify license/redistribution decisions",
        )
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add(
            "LICENSE_DECISION_MISSING",
            DELIVERABLES_REL,
            f"deliverables.json unparseable: {exc}",
        )
        return
    decisions = data.get("license_decisions") or []
    decision_ids = {
        d.get("id") for d in decisions if isinstance(d, dict) and isinstance(d.get("id"), str)
    }
    required_decision_prefixes = (
        "DEC-P09-INTERIM-NOASSERTION",
        "DEC-SCENARIO-CC-BY-4.0",
        "DEC-P09-D-GROUP-PENDING",
        "DEC-P09-SOURCE-ZIP-PENDING",
    )
    # Accept either interim pending IDs or later APPROVED replacements that
    # still cover the same decision namespaces after §6.8.
    for required in required_decision_prefixes:
        if required not in decision_ids:
            # Allow upgraded IDs that replace the interim ones after §6.8.
            upgraded = any(
                isinstance(i, str)
                and (
                    i.startswith("DEC-P09-LICENSE")
                    or i.startswith("DEC-P09-D-GROUP")
                    or i.startswith("DEC-P09-SOURCE-ZIP")
                    or i.startswith("DEC-SCENARIO-")
                )
                for i in decision_ids
            )
            if not upgraded and required not in decision_ids:
                result.add(
                    "LICENSE_DECISION_MISSING",
                    f"license_decisions.{required}",
                    f"required license/redistribution decision {required!r} is absent",
                )
    # D-group files must reference a D-group decision.
    d_paths = (
        "inputs/d-group/v0.4/received/building-energy-shapes_D.ttl",
        "inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md",
        "C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl",
    )
    by_path = {
        item.get("path"): item
        for item in data.get("deliverables") or []
        if isinstance(item, dict)
    }
    for d_path in d_paths:
        item = by_path.get(d_path)
        if not item:
            result.add(
                "D_GROUP_DECISION_MISSING",
                d_path,
                "D-group / Shape deliverable is not listed in deliverables.json",
            )
            continue
        did = item.get("decision_id")
        if not isinstance(did, str) or (
            "D-GROUP" not in did
            and did not in decision_ids
        ):
            result.add(
                "D_GROUP_DECISION_MISSING",
                d_path,
                f"D-group related file lacks D-group decision_id (found {did!r})",
            )
        # Accept DEC-P09-D-GROUP-* family.
        if isinstance(did, str) and not (
            did.startswith("DEC-P09-D-GROUP") or "D-GROUP" in did
        ):
            # Byte-copy Shape may share D-group decision; require it.
            if d_path.endswith("data-product-metadata-shapes.ttl") or "d-group" in d_path:
                if not (isinstance(did, str) and did.startswith("DEC-P09-D-GROUP")):
                    result.add(
                        "D_GROUP_DECISION_MISSING",
                        d_path,
                        f"expected DEC-P09-D-GROUP* decision, found {did!r}",
                    )


def evaluate_publication_safety(
    root: Path,
    *,
    tracked_files: Sequence[str] | None = None,
    extra_text_files: Sequence[tuple[str, Path]] = (),
    skip_git_history: bool = False,
) -> CheckResult:
    result = CheckResult(ok=True)
    gitless_container = is_gitless_validation_container(root)
    inventory_mode = "provided" if tracked_files is not None else "git"
    try:
        if tracked_files is None:
            if gitless_container:
                tracked_files = container_candidate_files(root)
                inventory_mode = "container-filesystem"
            else:
                tracked_files = git_ls_files(root)
        tracked = list(tracked_files)

        allowlist = load_privacy_allowlist(root, result)
        name_scanned = check_tracked_filenames(tracked, result)
        content_scanned = check_tracked_content(
            root, tracked, result, extra_text_files=extra_text_files
        )
        check_source_zips(root, allowlist, result)
        git_stats: dict[str, Any] = {}
        if not skip_git_history and not gitless_container:
            git_stats = check_git_identity_and_history(root, result)
        elif gitless_container:
            git_stats = {
                "status": "NOT_AVAILABLE_IN_GITLESS_CONTAINER",
                "boundary": "validated by host and true-clone safety runs",
            }
        size_stats = check_size_and_hygiene(root, tracked, result)
        check_gitattributes_and_scripts(
            root,
            result,
            gitless_container=gitless_container,
        )
        check_workflow_permissions(root, result)
        check_license_decisions(root, result)

        total_scanned = name_scanned + content_scanned
        if total_scanned == 0:
            result.add(
                "ZERO_SCAN_TARGETS",
                "publication-safety",
                "zero scan targets; scanner fail-closed",
            )

        # Deduplicate issues (same code+location+message).
        unique: list[Issue] = []
        seen: set[tuple[str, str, str]] = set()
        for issue in result.issues:
            key = (issue.code, issue.location, issue.message)
            if key in seen:
                continue
            seen.add(key)
            unique.append(issue)
        result.issues = unique
        result.ok = len(result.issues) == 0

        result.stats = {
            "tracked_count": len(tracked),
            "candidate_inventory_mode": inventory_mode,
            "name_scanned": name_scanned,
            "content_scanned": content_scanned,
            "total_scanned": total_scanned,
            "issue_count": len(result.issues),
            "privacy_allowlist_roles": sorted(allowlist.keys()),
            "privacy_allowlist_entry_count": sum(len(v) for v in allowlist.values()),
            "source_zips": [
                {
                    "filename": s["filename"],
                    "sha256": s["sha256"],
                    "size_bytes": s["size_bytes"],
                    "role": s["role"],
                }
                for s in SOURCE_ZIP_SPECS
            ],
            "git": git_stats,
            "size": size_stats,
            "extra_text_files": [label for label, _ in extra_text_files],
        }
        return result
    except Exception as exc:  # noqa: BLE001
        result.add("CHECKER_ERROR", "evaluate_publication_safety", repr(exc))
        result.ok = False
        return result


def build_report(result: CheckResult) -> dict[str, Any]:
    issues = [
        i.as_dict()
        for i in sorted(result.issues, key=lambda x: (x.code, x.location, x.message))
    ]
    return {
        "schema": "dssc.publication-safety-check.result.v1",
        "ok": result.ok and len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
        "reason_codes": sorted({i["code"] for i in issues}),
        "stats": result.stats,
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cwd_policy": "repository-root-via-script-location",
        },
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root (default: inferred from script location)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="optional path to write machine-readable JSON report",
    )
    parser.add_argument(
        "--extra-text-file",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help=(
            "additional text file to scan as if it were a tracked publication "
            "file (used by negative controls). Format: label=path"
        ),
    )
    parser.add_argument(
        "--skip-git-history",
        action="store_true",
        help="skip git log author/message scan (negative-control isolation)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    extras: list[tuple[str, Path]] = []
    for item in args.extra_text_file:
        if "=" not in item:
            print(
                f"invalid --extra-text-file {item!r}; expected LABEL=PATH",
                file=sys.stderr,
            )
            return 2
        label, raw_path = item.split("=", 1)
        extras.append((label, Path(raw_path)))

    try:
        result = evaluate_publication_safety(
            root,
            extra_text_files=extras,
            skip_git_history=bool(args.skip_git_history),
        )
        report = build_report(result)
    except Exception as exc:  # noqa: BLE001
        report = {
            "schema": "dssc.publication-safety-check.result.v1",
            "ok": False,
            "issue_count": 1,
            "issues": [
                {
                    "code": "CHECKER_ERROR",
                    "location": "main",
                    "message": repr(exc),
                }
            ],
            "reason_codes": ["CHECKER_ERROR"],
            "stats": {},
        }

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(text)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
