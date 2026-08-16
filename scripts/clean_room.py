#!/usr/bin/env python3
"""Create a Phase 08 release-candidate clean-room rehearsal.

This script exports the current *working-tree release candidate*: every tracked
file (using its current working-tree bytes) plus every Git-unignored untracked
file.  Generated/local material is excluded by a named policy and recorded in
a machine-readable exclusion manifest.  A full rehearsal starts with no
repository ``.venv`` and runs the canonical reproduce wrapper first, so that
the wrapper itself must bootstrap from the locks before doctor and the explicit
``all`` wrapper are run as independent follow-up checks.

The activity is deliberately called a ``release-candidate clean-room
rehearsal``.  It is not the Phase 09 clean clone of a committed revision, and
every stable result records that distinction.

Examples (run with the repository .venv interpreter on a native host)::

    .venv\\Scripts\\python.exe scripts\\clean_room.py --mode manifest-only
    .venv\\Scripts\\python.exe scripts\\clean_room.py --mode export
    .venv\\Scripts\\python.exe scripts\\clean_room.py --mode rehearsal --profile host
    ./.venv/bin/python scripts/clean_room.py --mode rehearsal --profile host

The fixed validation image is a separate Docker certification track.  Its
container-profile doctor/all commands run directly in that image.  This script
requires native Git candidate metadata, does not mount the host source or
``.git`` into that image, and never mounts a Docker daemon socket.

Exit codes:

* 0: requested mode completed successfully
* 2: command-line usage error (argparse)
* 3: release-candidate inventory/policy error
* 4: unsafe output boundary or existing run directory
* 5: export/copy integrity error
* 6: a rehearsal command failed, was unavailable, or timed out
* 7: post-run source/output integrity error
* 8: unexpected internal error

The script creates no output for ``--dry-run``.  Every non-dry-run write and
every cleanup target is checked to be below ``build/clean-room/<run-id>``.
Existing run directories are never overwritten or deleted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INVENTORY = 3
EXIT_BOUNDARY = 4
EXIT_EXPORT = 5
EXIT_EXECUTION = 6
EXIT_INTEGRITY = 7
EXIT_INTERNAL = 8

ACTIVITY = "phase-08-release-candidate-clean-room-rehearsal"
PHASE09_STATEMENT = (
    "NOT PERFORMED: Phase 09 must run a real git clone of an authorized, "
    "committed revision."
)
CONTAINER_STATEMENT = (
    "NOT RUN by clean_room.py: fixed-image container doctor/all is an "
    "independent Docker certification track and uses no host-source, .git, or "
    "daemon-socket mount."
)
SCHEMA_PREFIX = "dssc.clean-room"
HEX_OBJECT_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
MAX_RUN_ID_CHARACTERS = 64
MAX_RUN_ID_UTF8_BYTES = 128
EXPECTED_REHEARSAL_COMMAND_IDS = (
    "reproduce-host",
    "doctor-host",
    "all-host-wrapper",
)
_WINDOWS_INVALID_FILENAME_CHARACTERS = frozenset('<>:"/\\|?*')

_CACHE_COMPONENTS = {
    "__pycache__",
    ".cache",
    "cache",
    "caches",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "htmlcov",
}
_LOCAL_DIRECTORY_COMPONENTS = {
    ".idea",
    ".vscode",
    ".vs",
    ".codex",
    ".claude",
}
_GENERATED_ROOTS = {"dist", "tmp", "temp"}
_SECRET_EXTENSIONS = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".jks",
    ".keystore",
}
_SECRET_BASENAMES = {
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ed25519",
    "id_ecdsa",
    "id_rsa",
    "local.settings.json",
    "pip.conf",
    "pip.ini",
}
_WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "clock$",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
    "com¹",
    "com²",
    "com³",
    "lpt¹",
    "lpt²",
    "lpt³",
}

_PRIVATE_KEY_RE = re.compile(
    rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
)
_TOKEN_RES = (
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
)
_ASSIGNMENT_SECRET_RE = re.compile(
    rb"(?i)(?:api[_-]?key|access[_-]?token|secret|password|passwd|credential)"
    rb"\s*[:=]\s*['\"]?([A-Za-z0-9_./+=:@-]{12,})"
)
_PLACEHOLDER_VALUES = {
    b"changeme",
    b"example",
    b"placeholder",
    b"redacted",
    b"replace-me",
    b"replace_me",
    b"your-token-here",
}

_WINDOWS_ABSOLUTE_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)[^\r\n\t\"']*"
)
# A slash preceded by ``.`` belongs to a dot-relative token (``./`` or
# ``../``).  Preserve those stable repository-relative spellings while still
# detecting a true POSIX absolute path at a token boundary.
_POSIX_ABSOLUTE_RE = re.compile(r"(?<![.:/A-Za-z0-9])/(?!/)[^\s\"'=]+")


class CleanRoomError(RuntimeError):
    """A fail-closed, user-facing clean-room error."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class CandidateFile:
    path: str
    origin: str
    kind: str
    mode: str
    size: int
    sha256: str
    source_path: Path

    def public_record(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "origin": self.origin,
            "kind": self.kind,
            "mode": self.mode,
            "size": self.size,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class Exclusion:
    path: str
    kind: str
    reason: str
    origin: str

    def public_record(self) -> dict[str, str]:
        return {
            "path": self.path,
            "kind": self.kind,
            "reason": self.reason,
            "origin": self.origin,
        }


@dataclass(frozen=True)
class Inventory:
    files: tuple[CandidateFile, ...]
    exclusions: tuple[Exclusion, ...]
    tracked_count: int
    untracked_count: int
    excluded_tracked_count: int
    excluded_untracked_count: int
    git_head: str
    git_dirty: bool
    git_status_sha256: str
    tree_sha256: str
    registry_contract_version: str
    registry_sha256: str
    lock_sha256: str


@dataclass(frozen=True)
class CommandSpec:
    command_id: str
    actual_argv: tuple[str, ...]
    display_argv: tuple[str, ...]
    environment_overrides: tuple[tuple[str, str], ...] = ()


def _sort_key(value: str) -> tuple[str, bytes]:
    return value.casefold(), value.encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _tree_sha256(records: Iterable[dict[str, Any]]) -> str:
    stable = [
        {
            "kind": record["kind"],
            "mode": record["mode"],
            "path": record["path"],
            "sha256": record["sha256"],
            "size": record["size"],
        }
        for record in records
    ]
    stable.sort(key=lambda item: _sort_key(item["path"]))
    return _sha256_bytes(
        json.dumps(
            stable,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


def _is_linklike(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if callable(is_junction) and is_junction():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        return bool(attributes & reparse)
    except OSError:
        return False


def _normalize_repo_path(raw: str) -> str:
    if not raw or "\x00" in raw:
        raise CleanRoomError("Git returned an empty or NUL-containing path", EXIT_INVENTORY)
    value = raw.replace("\\", "/")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise CleanRoomError(f"unsafe repository path: {raw!r}", EXIT_INVENTORY)
    normalized = unicodedata.normalize("NFC", pure.as_posix())
    if normalized.startswith("/") or normalized == ".":
        raise CleanRoomError(f"unsafe normalized repository path: {raw!r}", EXIT_INVENTORY)
    if any(ord(character) < 32 for character in normalized):
        raise CleanRoomError(
            f"control character in repository path: {raw!r}", EXIT_INVENTORY
        )
    return normalized


def _relative_path(root: Path, path: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise CleanRoomError("path escaped the repository root", EXIT_BOUNDARY) from exc
    return _normalize_repo_path(relative.as_posix())


def _assert_contained(path: Path, boundary: Path, *, allow_boundary: bool = False) -> None:
    boundary_resolved = boundary.resolve()
    path_resolved = path.resolve(strict=False)
    try:
        relative = path_resolved.relative_to(boundary_resolved)
    except ValueError as exc:
        raise CleanRoomError(
            f"refusing path outside clean-room boundary: {path}", EXIT_BOUNDARY
        ) from exc
    if not allow_boundary and relative == Path("."):
        raise CleanRoomError("operation requires a child of the clean-room boundary", EXIT_BOUNDARY)


def _atomic_write(path: Path, payload: bytes, run_root: Path) -> None:
    _assert_contained(path, run_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_contained(path.parent, run_root, allow_boundary=True)
    if _is_linklike(path.parent):
        raise CleanRoomError("refusing to write through a link-like directory", EXIT_BOUNDARY)
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_json(path: Path, value: Any, run_root: Path) -> None:
    _atomic_write(path, _json_bytes(value), run_root)


def _decode_git_path(raw: bytes) -> str:
    try:
        return raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise CleanRoomError(
            "Git emitted a path that is not valid UTF-8", EXIT_INVENTORY
        ) from exc


def _git_environment(*, read_only: bool) -> dict[str, str]:
    environment = os.environ.copy()
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_TERMINAL_PROMPT"] = "0"
    if read_only:
        environment["GIT_OPTIONAL_LOCKS"] = "0"
    return environment


def _run_git_bytes(
    root: Path,
    arguments: Sequence[str],
    *,
    read_only: bool = True,
    timeout: int = 60,
    extra_environment: dict[str, str] | None = None,
) -> bytes:
    environment = _git_environment(read_only=read_only)
    if extra_environment:
        environment.update(extra_environment)
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=str(root),
            env=environment,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise CleanRoomError("Git CLI is required for candidate export", EXIT_INVENTORY) from exc
    except subprocess.TimeoutExpired as exc:
        raise CleanRoomError("Git inventory command timed out", EXIT_INVENTORY) from exc
    if completed.returncode != 0:
        stderr = (completed.stderr or b"").decode("utf-8", "replace").strip()
        raise CleanRoomError(
            f"Git inventory command failed (exit {completed.returncode}): {stderr[:400]}",
            EXIT_INVENTORY,
        )
    return completed.stdout or b""


def _repository_root() -> Path:
    script_root = Path(__file__).resolve().parent.parent
    raw = _run_git_bytes(script_root, ["rev-parse", "--show-toplevel"])
    try:
        git_root = Path(raw.decode("utf-8", "strict").strip()).resolve()
    except UnicodeDecodeError as exc:
        raise CleanRoomError("Git repository root is not UTF-8", EXIT_INVENTORY) from exc
    if git_root != script_root:
        raise CleanRoomError(
            "scripts/clean_room.py is not running from its canonical Git worktree",
            EXIT_INVENTORY,
        )
    return script_root


def _exclusion_reason(path: str) -> str | None:
    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    if not parts:
        return "invalid-path"
    first = parts[0]
    basename = parts[-1]
    suffix = PurePosixPath(basename).suffix.casefold()

    if first == ".git":
        return "vcs-metadata-and-local-git-configuration"
    if first in {".venv", "venv"}:
        return "repository-virtual-environment"
    if first == "build":
        return "generated-build-output"
    if first in _GENERATED_ROOTS or first.startswith("_migration_staging"):
        return "generated-or-temporary-output"
    if parts[:3] == ("tools", "semantic-treehouse", "upstream"):
        return "optional-external-upstream-checkout"
    if parts[:3] in {
        ("c_semantic_treehouse", "validation", "generated"),
        ("c_semantic_treehouse", "evidence", "local"),
    }:
        return "generated-local-evidence"
    if any(part in _CACHE_COMPONENTS for part in parts):
        return "cache"
    if any(part in _LOCAL_DIRECTORY_COMPONENTS for part in parts):
        return "editor-or-agent-local-configuration"
    if basename == ".env" or (basename.startswith(".env.") and basename != ".env.example"):
        return "secret-or-machine-local-environment"
    if basename in _SECRET_BASENAMES or suffix in _SECRET_EXTENSIONS:
        return "credential-or-secret-file"
    if basename.startswith("secrets.") or basename.startswith("credentials."):
        return "credential-or-secret-file"
    if basename.endswith(".local") or ".local." in basename:
        return "machine-local-configuration"
    if suffix in {".pyc", ".pyo", ".log", ".tmp", ".bak"}:
        return "cache-or-temporary-file"
    if basename in {".coverage", "thumbs.db", ".ds_store"} or basename.startswith("._"):
        return "machine-generated-metadata"
    if basename.endswith(".swp"):
        return "editor-local-configuration"
    return None


def _secret_content_reason(path: Path) -> str | None:
    try:
        if path.stat().st_size > 2 * 1024 * 1024:
            return None
        data = path.read_bytes()
    except OSError as exc:
        raise CleanRoomError(f"cannot inspect untracked file {path.name!r}: {exc}", EXIT_INVENTORY) from exc
    if b"\x00" in data:
        return None
    if _PRIVATE_KEY_RE.search(data):
        return "private-key-content"
    for pattern in _TOKEN_RES:
        if pattern.search(data):
            return "credential-token-content"
    for match in _ASSIGNMENT_SECRET_RE.finditer(data):
        value = match.group(1).strip().lower()
        if value not in _PLACEHOLDER_VALUES and not value.startswith((b"${", b"<", b"your_")):
            return "credential-assignment-content"
    return None


def _safe_source_path(root: Path, relative: str) -> Path:
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    lexical = candidate.absolute()
    try:
        lexical.relative_to(root)
    except ValueError as exc:
        raise CleanRoomError(f"candidate path escaped repository: {relative}", EXIT_INVENTORY) from exc
    return candidate


def _safe_symlink_target(root: Path, source: Path) -> str:
    try:
        target = os.readlink(source)
    except OSError as exc:
        raise CleanRoomError(f"cannot read symlink {source.name!r}: {exc}", EXIT_INVENTORY) from exc
    if os.path.isabs(target):
        raise CleanRoomError("absolute symlinks are forbidden in a clean-room candidate", EXIT_INVENTORY)
    resolved = (source.parent / target).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CleanRoomError("candidate symlink resolves outside the repository", EXIT_INVENTORY) from exc
    return target


def _candidate_file(
    root: Path,
    relative: str,
    origin: str,
    index_mode: str | None,
) -> CandidateFile:
    source = _safe_source_path(root, relative)
    try:
        source_stat = source.lstat()
    except FileNotFoundError as exc:
        raise CleanRoomError(
            f"candidate path is missing from the working tree: {relative}", EXIT_INVENTORY
        ) from exc
    except OSError as exc:
        raise CleanRoomError(f"cannot stat candidate path {relative}: {exc}", EXIT_INVENTORY) from exc

    if stat.S_ISLNK(source_stat.st_mode):
        target = _safe_symlink_target(root, source)
        if index_mode is not None and index_mode != "120000":
            raise CleanRoomError(
                f"working-tree symlink/index mode mismatch: {relative}", EXIT_INVENTORY
            )
        payload = os.fsencode(target)
        mode = "120000"
        kind = "symlink"
        size = len(payload)
        digest = _sha256_bytes(payload)
    elif stat.S_ISREG(source_stat.st_mode):
        try:
            source.resolve(strict=True).relative_to(root)
        except (OSError, ValueError) as exc:
            raise CleanRoomError(
                f"candidate regular file resolves outside the repository: {relative}",
                EXIT_INVENTORY,
            ) from exc
        if index_mode == "120000":
            raise CleanRoomError(
                f"tracked symlink is not materialized as a symlink: {relative}", EXIT_INVENTORY
            )
        if index_mode is not None and index_mode not in {"100644", "100755"}:
            raise CleanRoomError(
                f"unsupported tracked Git mode {index_mode} at {relative}", EXIT_INVENTORY
            )
        mode = index_mode or ("100755" if source_stat.st_mode & 0o111 else "100644")
        kind = "file"
        size = source_stat.st_size
        digest = _sha256_file(source)
        try:
            after_stat = source.lstat()
        except OSError as exc:
            raise CleanRoomError(f"candidate changed while hashing: {relative}", EXIT_INVENTORY) from exc
        if (
            after_stat.st_size != source_stat.st_size
            or after_stat.st_mtime_ns != source_stat.st_mtime_ns
            or not stat.S_ISREG(after_stat.st_mode)
        ):
            raise CleanRoomError(f"candidate changed while hashing: {relative}", EXIT_INVENTORY)
    else:
        raise CleanRoomError(
            f"candidate entry is neither a regular file nor a safe symlink: {relative}",
            EXIT_INVENTORY,
        )
    return CandidateFile(relative, origin, kind, mode, size, digest, source)


def _tracked_entries(root: Path) -> dict[str, str]:
    raw = _run_git_bytes(root, ["ls-files", "--cached", "--stage", "-z"])
    entries: dict[str, str] = {}
    for item in raw.split(b"\x00"):
        if not item:
            continue
        try:
            metadata, raw_path = item.split(b"\t", 1)
            raw_mode, _object_id, raw_stage = metadata.split(b" ", 2)
        except ValueError as exc:
            raise CleanRoomError("malformed git ls-files --stage output", EXIT_INVENTORY) from exc
        if raw_stage != b"0":
            raise CleanRoomError("unmerged index entries cannot be rehearsed", EXIT_INVENTORY)
        path = _normalize_repo_path(_decode_git_path(raw_path))
        mode = raw_mode.decode("ascii", "strict")
        if path in entries:
            raise CleanRoomError(f"duplicate tracked path after normalization: {path}", EXIT_INVENTORY)
        entries[path] = mode
    return entries


def _untracked_entries(root: Path) -> set[str]:
    raw = _run_git_bytes(
        root, ["ls-files", "--others", "--exclude-standard", "-z"]
    )
    result: set[str] = set()
    for item in raw.split(b"\x00"):
        if item:
            path = _normalize_repo_path(_decode_git_path(item))
            if path in result:
                raise CleanRoomError(
                    f"duplicate untracked path after normalization: {path}", EXIT_INVENTORY
                )
            result.add(path)
    return result


def _scan_filesystem_exclusions(
    root: Path,
    candidate_paths: set[str],
    existing: Iterable[Exclusion],
) -> tuple[Exclusion, ...]:
    exclusions: dict[tuple[str, str], Exclusion] = {
        (item.path, item.kind): item for item in existing
    }

    def visit(directory: Path) -> None:
        try:
            entries = sorted(
                os.scandir(directory),
                key=lambda item: _sort_key(unicodedata.normalize("NFC", item.name)),
            )
        except OSError as exc:
            raise CleanRoomError(
                f"cannot audit repository directory {directory.name!r}: {exc}", EXIT_INVENTORY
            ) from exc
        for entry in entries:
            path = Path(entry.path)
            relative = _relative_path(root, path)
            try:
                is_symlink = entry.is_symlink()
                is_directory = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
            except OSError as exc:
                raise CleanRoomError(f"cannot inspect repository path {relative}: {exc}", EXIT_INVENTORY) from exc
            kind = "symlink" if is_symlink else "directory" if is_directory else "file"
            reason = _exclusion_reason(relative)
            if reason is not None:
                exclusions.setdefault(
                    (relative, kind),
                    Exclusion(relative, kind, reason, "filesystem"),
                )
                continue
            if is_directory:
                visit(path)
                continue
            if relative in candidate_paths:
                continue
            if is_file or is_symlink:
                exclusions.setdefault(
                    (relative, kind),
                    Exclusion(relative, kind, "git-ignored-or-noncandidate", "filesystem"),
                )

    visit(root)
    return tuple(
        sorted(
            exclusions.values(),
            key=lambda item: (*_sort_key(item.path), item.kind, item.reason),
        )
    )


def _load_registry_contract(root: Path, candidate: dict[str, CandidateFile]) -> tuple[str, str]:
    relative = "C_Semantic_Treehouse/manifests/validation-suites.json"
    record = candidate.get(relative)
    if record is None:
        raise CleanRoomError("suite registry is absent from the release candidate", EXIT_INVENTORY)
    try:
        value = json.loads(record.source_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CleanRoomError(f"suite registry is unreadable: {exc}", EXIT_INVENTORY) from exc
    contract_version = value.get("contract_version") if isinstance(value, dict) else None
    if not isinstance(contract_version, str) or not contract_version:
        raise CleanRoomError("suite registry contract_version is invalid", EXIT_INVENTORY)
    return contract_version, record.sha256


def _inventory(root: Path) -> Inventory:
    tracked = _tracked_entries(root)
    untracked = _untracked_entries(root)
    overlap = set(tracked).intersection(untracked)
    if overlap:
        raise CleanRoomError("Git reported paths as both tracked and untracked", EXIT_INVENTORY)

    normalized_case: dict[str, str] = {}
    for relative in sorted((*tracked.keys(), *untracked), key=_sort_key):
        folded = relative.casefold()
        previous = normalized_case.get(folded)
        if previous is not None and previous != relative:
            raise CleanRoomError(
                f"case-insensitive path collision: {previous!r} and {relative!r}",
                EXIT_INVENTORY,
            )
        normalized_case[folded] = relative

    files: list[CandidateFile] = []
    exclusions: list[Exclusion] = []
    tracked_policy_violations: list[str] = []
    excluded_untracked = 0

    for relative in sorted(tracked, key=_sort_key):
        reason = _exclusion_reason(relative)
        source = _safe_source_path(root, relative)
        if reason is None and source.is_file() and not source.is_symlink():
            reason = _secret_content_reason(source)
        if reason is not None:
            exclusions.append(Exclusion(relative, "file", reason, "tracked"))
            if relative != "build/.gitkeep":
                tracked_policy_violations.append(f"{relative} ({reason})")
            continue
        files.append(_candidate_file(root, relative, "tracked", tracked[relative]))

    for relative in sorted(untracked, key=_sort_key):
        reason = _exclusion_reason(relative)
        source = _safe_source_path(root, relative)
        if reason is None and source.is_file() and not source.is_symlink():
            reason = _secret_content_reason(source)
        if reason is not None:
            kind = "symlink" if source.is_symlink() else "file"
            exclusions.append(Exclusion(relative, kind, reason, "untracked"))
            excluded_untracked += 1
            continue
        files.append(_candidate_file(root, relative, "untracked", None))

    if tracked_policy_violations:
        raise CleanRoomError(
            "tracked paths match the secret/local/generated exclusion policy; "
            "review instead of silently omitting them: "
            + ", ".join(tracked_policy_violations[:20]),
            EXIT_INVENTORY,
        )

    files.sort(key=lambda item: _sort_key(item.path))
    candidate = {item.path: item for item in files}
    if len(candidate) != len(files):
        raise CleanRoomError("candidate path collision after normalization", EXIT_INVENTORY)

    included_tracked = sum(item.origin == "tracked" for item in files)
    included_untracked = sum(item.origin == "untracked" for item in files)
    excluded_tracked = len(tracked) - included_tracked
    if included_tracked + excluded_tracked != len(tracked):
        raise CleanRoomError("tracked candidate completeness accounting failed", EXIT_INVENTORY)
    if included_untracked + excluded_untracked != len(untracked):
        raise CleanRoomError("untracked candidate completeness accounting failed", EXIT_INVENTORY)

    exclusions_tuple = _scan_filesystem_exclusions(
        root, set(candidate), exclusions
    )
    head = _run_git_bytes(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode(
        "ascii", "strict"
    ).strip().lower()
    if HEX_OBJECT_RE.fullmatch(head) is None:
        raise CleanRoomError("Git HEAD is not a full commit object ID", EXIT_INVENTORY)
    status = _run_git_bytes(
        root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"]
    )
    registry_version, registry_sha256 = _load_registry_contract(root, candidate)
    lock = candidate.get("requirements.lock")
    if lock is None:
        raise CleanRoomError("requirements.lock is absent from the release candidate", EXIT_INVENTORY)
    tree_hash = _tree_sha256(item.public_record() for item in files)
    return Inventory(
        files=tuple(files),
        exclusions=exclusions_tuple,
        tracked_count=len(tracked),
        untracked_count=len(untracked),
        excluded_tracked_count=excluded_tracked,
        excluded_untracked_count=excluded_untracked,
        git_head=head,
        git_dirty=bool(status),
        git_status_sha256=_sha256_bytes(status),
        tree_sha256=tree_hash,
        registry_contract_version=registry_version,
        registry_sha256=registry_sha256,
        lock_sha256=lock.sha256,
    )


def _source_manifest(inventory: Inventory) -> dict[str, Any]:
    tracked_included = sum(item.origin == "tracked" for item in inventory.files)
    untracked_included = sum(item.origin == "untracked" for item in inventory.files)
    return {
        "schema": f"{SCHEMA_PREFIX}.source-manifest.v1",
        "phase": "08",
        "activity": ACTIVITY,
        "source_kind": "current-working-tree-release-candidate",
        "phase_09_git_clone_performed": False,
        "phase_09_boundary": PHASE09_STATEMENT,
        "fixed_validation_image_track": CONTAINER_STATEMENT,
        "path_format": "repository-relative NFC Unicode with POSIX separators",
        "candidate_policy": {
            "tracked": "all Git-index paths, using current working-tree bytes",
            "untracked": "all Git-unignored untracked file paths",
            "ignored_and_local": "excluded and recorded by named policy",
        },
        "git": {
            "head": inventory.git_head,
            "dirty": inventory.git_dirty,
            "status_sha256": inventory.git_status_sha256,
        },
        "suite_registry": {
            "path": "C_Semantic_Treehouse/manifests/validation-suites.json",
            "contract_version": inventory.registry_contract_version,
            "sha256": inventory.registry_sha256,
        },
        "requirements_lock": {
            "path": "requirements.lock",
            "sha256": inventory.lock_sha256,
        },
        "completeness": {
            "tracked_discovered": inventory.tracked_count,
            "tracked_included": tracked_included,
            "tracked_policy_excluded": inventory.excluded_tracked_count,
            "untracked_discovered": inventory.untracked_count,
            "untracked_included": untracked_included,
            "untracked_policy_excluded": inventory.excluded_untracked_count,
            "unaccounted_candidate_paths": 0,
        },
        "file_count": len(inventory.files),
        "tree_sha256": inventory.tree_sha256,
        "files": [item.public_record() for item in inventory.files],
    }


def _exclusion_manifest(inventory: Inventory) -> dict[str, Any]:
    categories = sorted({item.reason for item in inventory.exclusions})
    return {
        "schema": f"{SCHEMA_PREFIX}.exclusion-manifest.v1",
        "phase": "08",
        "activity": ACTIVITY,
        "phase_09_git_clone_performed": False,
        "path_format": "repository-relative NFC Unicode with POSIX separators",
        "fixed_validation_image_track": CONTAINER_STATEMENT,
        "rules": [
            {"id": "vcs", "scope": ".git metadata and local Git configuration"},
            {"id": "venv", "scope": "repository .venv/venv environments"},
            {"id": "build", "scope": "top-level build and generated output"},
            {"id": "cache", "scope": "Python/tool caches and temporary files"},
            {
                "id": "external-upstream",
                "scope": "tools/semantic-treehouse/upstream checkout",
            },
            {"id": "secret", "scope": "secret/credential names and token content"},
            {"id": "local-config", "scope": "editor, agent and machine-local config"},
            {"id": "git-ignored", "scope": "remaining Git-ignored noncandidate files"},
        ],
        "category_count": len(categories),
        "categories": categories,
        "exclusion_count": len(inventory.exclusions),
        "exclusions": [item.public_record() for item in inventory.exclusions],
    }


def _validate_run_id(value: str) -> str:
    if not value:
        raise CleanRoomError(
            "run ID must contain at least one character",
            EXIT_BOUNDARY,
        )
    if value != unicodedata.normalize("NFC", value):
        raise CleanRoomError("run ID must already be NFC-normalized", EXIT_BOUNDARY)
    if len(value) > MAX_RUN_ID_CHARACTERS or len(value.encode("utf-8")) > MAX_RUN_ID_UTF8_BYTES:
        raise CleanRoomError(
            "run ID exceeds the 64-character or 128-byte UTF-8 limit",
            EXIT_BOUNDARY,
        )
    if value in {".", ".."}:
        raise CleanRoomError("run ID cannot be '.' or '..'", EXIT_BOUNDARY)
    if (
        value[0] == "."
        or value[-1] == "."
        or value[0].isspace()
        or value[-1].isspace()
    ):
        raise CleanRoomError(
            "run ID cannot start or end with a space or dot", EXIT_BOUNDARY
        )
    invalid = sorted(
        {
            character
            for character in value
            if character in _WINDOWS_INVALID_FILENAME_CHARACTERS
            or unicodedata.category(character).startswith("C")
        }
    )
    if invalid:
        raise CleanRoomError(
            "run ID contains a path separator, control character, or "
            "cross-platform-invalid filename character",
            EXIT_BOUNDARY,
        )
    stem = value.split(".", 1)[0].casefold().rstrip(" .")
    if stem in _WINDOWS_RESERVED_NAMES:
        raise CleanRoomError("run ID is a reserved path name", EXIT_BOUNDARY)
    return value


def _clean_room_base(root: Path, *, create: bool) -> Path:
    build = root / "build"
    if not build.exists() or not build.is_dir() or _is_linklike(build):
        raise CleanRoomError(
            "repository build/ must be an existing real directory", EXIT_BOUNDARY
        )
    base = build / "clean-room"
    if base.exists():
        if not base.is_dir() or _is_linklike(base):
            raise CleanRoomError("build/clean-room is not a real directory", EXIT_BOUNDARY)
    elif create:
        base.mkdir()
    resolved_build = build.resolve()
    resolved_base = base.resolve(strict=False)
    try:
        relative = resolved_base.relative_to(resolved_build)
    except ValueError as exc:
        raise CleanRoomError("clean-room base escaped build/", EXIT_BOUNDARY) from exc
    if relative != Path("clean-room"):
        raise CleanRoomError("clean-room base is not the exact allowed path", EXIT_BOUNDARY)
    return base


def _prepare_run_root(root: Path, run_id: str) -> Path:
    base = _clean_room_base(root, create=True)
    run_root = base / run_id
    _assert_contained(run_root, base)
    if run_root.exists() or run_root.is_symlink():
        raise CleanRoomError(
            f"run directory already exists; choose a new --run-id: {run_id}",
            EXIT_BOUNDARY,
        )
    run_root.mkdir()
    if _is_linklike(run_root):
        raise CleanRoomError("new run directory is link-like", EXIT_BOUNDARY)
    return run_root


def _copy_candidate(inventory: Inventory, source_root: Path, run_root: Path) -> str:
    _assert_contained(source_root, run_root)
    source_root.mkdir()
    for item in inventory.files:
        destination = source_root.joinpath(*PurePosixPath(item.path).parts)
        _assert_contained(destination, source_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        current = destination.parent
        while current != source_root:
            if _is_linklike(current):
                raise CleanRoomError(
                    f"export parent became link-like: {item.path}", EXIT_EXPORT
                )
            current = current.parent
        if destination.exists() or destination.is_symlink():
            raise CleanRoomError(f"duplicate export destination: {item.path}", EXIT_EXPORT)
        try:
            if item.kind == "symlink":
                target = os.readlink(item.source_path)
                os.symlink(target, destination)
            else:
                with item.source_path.open("rb") as source_handle, destination.open("xb") as destination_handle:
                    shutil.copyfileobj(source_handle, destination_handle, 1024 * 1024)
                os.chmod(destination, 0o755 if item.mode == "100755" else 0o644)
        except OSError as exc:
            raise CleanRoomError(f"failed to export {item.path}: {exc}", EXIT_EXPORT) from exc
        exported = _filesystem_record(source_root, destination, mode_override=item.mode)
        if (
            exported["kind"] != item.kind
            or exported["sha256"] != item.sha256
            or exported["size"] != item.size
        ):
            raise CleanRoomError(f"export hash mismatch: {item.path}", EXIT_EXPORT)

    exported_records = _snapshot_tree(
        source_root, mode_overrides={item.path: item.mode for item in inventory.files}
    )
    expected = {item.path: item.public_record() for item in inventory.files}
    actual = {item["path"]: item for item in exported_records}
    if set(actual) != set(expected):
        raise CleanRoomError("exported path set differs from source manifest", EXIT_EXPORT)
    for path, expected_record in expected.items():
        actual_record = actual[path]
        for key in ("kind", "mode", "size", "sha256"):
            if actual_record[key] != expected_record[key]:
                raise CleanRoomError(
                    f"exported record differs at {path} ({key})", EXIT_EXPORT
                )
    tree_hash = _tree_sha256(exported_records)
    if tree_hash != inventory.tree_sha256:
        raise CleanRoomError("exported tree hash differs from candidate tree hash", EXIT_EXPORT)
    return tree_hash


def _filesystem_record(
    root: Path, path: Path, *, mode_override: str | None = None
) -> dict[str, Any]:
    relative = _relative_path(root, path)
    path_stat = path.lstat()
    if stat.S_ISLNK(path_stat.st_mode):
        target = _safe_symlink_target(root, path)
        payload = os.fsencode(target)
        return {
            "path": relative,
            "kind": "symlink",
            "mode": "120000",
            "size": len(payload),
            "sha256": _sha256_bytes(payload),
        }
    if not stat.S_ISREG(path_stat.st_mode):
        raise CleanRoomError(
            f"unexpected non-file in clean-room output: {relative}", EXIT_INTEGRITY
        )
    return {
        "path": relative,
        "kind": "file",
        "mode": mode_override
        or ("100755" if path_stat.st_mode & 0o111 else "100644"),
        "size": path_stat.st_size,
        "sha256": _sha256_file(path),
    }


def _snapshot_tree(
    root: Path, *, mode_overrides: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    overrides = mode_overrides or {}
    records: list[dict[str, Any]] = []
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        directory_names.sort(key=_sort_key)
        file_names.sort(key=_sort_key)
        retained_directories: list[str] = []
        for name in directory_names:
            path = directory_path / name
            if path.is_symlink():
                relative = _relative_path(root, path)
                records.append(
                    _filesystem_record(
                        root, path, mode_override=overrides.get(relative)
                    )
                )
            else:
                retained_directories.append(name)
        directory_names[:] = retained_directories
        for name in file_names:
            path = directory_path / name
            relative = _relative_path(root, path)
            records.append(
                _filesystem_record(root, path, mode_override=overrides.get(relative))
            )
    records.sort(key=lambda item: _sort_key(item["path"]))
    return records


def _runtime_environment(runtime_root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUTF8": "1",
            "PYTHONNOUSERSITE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_NO_CACHE_DIR": "1",
            "DSSC_CLEAN_ROOM_ACTIVITY": ACTIVITY,
            "TMP": str(runtime_root / "tmp"),
            "TEMP": str(runtime_root / "tmp"),
            "TMPDIR": str(runtime_root / "tmp"),
            "XDG_CACHE_HOME": str(runtime_root / "cache"),
        }
    )
    for name in (
        "PIP_TARGET",
        "PIP_PREFIX",
        "PIP_ROOT",
        "PIP_USER",
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
    ):
        environment.pop(name, None)
    (runtime_root / "tmp").mkdir(parents=True, exist_ok=True)
    (runtime_root / "cache").mkdir(parents=True, exist_ok=True)
    return environment


def _initialize_rehearsal_git(
    source_root: Path,
    environment: dict[str, str],
    inventory: Inventory,
) -> str:
    if (source_root / ".git").exists():
        raise CleanRoomError("export unexpectedly contains .git metadata", EXIT_INTEGRITY)
    git_environment = environment.copy()
    git_environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            "TZ": "UTC",
        }
    )
    setup_commands = (
        ["git", "init", "-q"],
        ["git", "symbolic-ref", "HEAD", "refs/heads/phase-08-rehearsal"],
        ["git", "config", "core.autocrlf", "false"],
        ["git", "config", "commit.gpgsign", "false"],
        ["git", "add", "-f", "--all", "--", "."],
    )
    executable_paths = [item.path for item in inventory.files if item.mode == "100755"]
    mode_commands: list[list[str]] = []
    if executable_paths:
        mode_commands.append(
            ["git", "update-index", "--chmod=+x", "--", *executable_paths]
        )
    commands = (
        *setup_commands,
        *mode_commands,
        [
            "git",
            "-c",
            "user.name=DSSC Phase 08 Rehearsal",
            "-c",
            "user.email=phase08-rehearsal.invalid@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "-m",
            "Phase 08 release-candidate rehearsal snapshot; not a Phase 09 clone",
        ],
    )
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=str(source_root),
                env=git_environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            raise CleanRoomError("cannot create local rehearsal Git snapshot", EXIT_EXECUTION) from exc
        if completed.returncode != 0:
            raise CleanRoomError(
                f"local rehearsal Git snapshot failed at {command[1]} "
                f"(exit {completed.returncode})",
                EXIT_EXECUTION,
            )
    head = _run_git_in_rehearsal(source_root, ["rev-parse", "--verify", "HEAD^{commit}"], git_environment)
    status_output = _run_git_in_rehearsal(
        source_root, ["status", "--porcelain=v1", "--untracked-files=all"], git_environment
    )
    if status_output.strip():
        raise CleanRoomError("local rehearsal Git snapshot is unexpectedly dirty", EXIT_INTEGRITY)
    head = head.strip().lower()
    if HEX_OBJECT_RE.fullmatch(head) is None:
        raise CleanRoomError("local rehearsal Git snapshot ID is invalid", EXIT_INTEGRITY)
    return head


def _run_git_in_rehearsal(
    root: Path, arguments: Sequence[str], environment: dict[str, str]
) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=str(root),
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise CleanRoomError("local rehearsal Git verification failed", EXIT_INTEGRITY)
    return completed.stdout or ""


def _command_plan(source_root: Path, profile: str) -> tuple[CommandSpec, ...]:
    if profile != "host":
        raise CleanRoomError(
            "clean_room.py supports only the native host rehearsal profile; "
            "the fixed validation image is a separate Docker track",
            EXIT_USAGE,
        )

    system = platform.system()
    if system == "Windows":
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            raise CleanRoomError("Windows PowerShell 5.1+ is unavailable", EXIT_EXECUTION)
        prefix = (
            powershell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
        )
        display_prefix = (
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
        )
        venv_python = str(source_root / ".venv" / "Scripts" / "python.exe")
        return (
            CommandSpec(
                "reproduce-host",
                (*prefix, str(source_root / "scripts" / "reproduce.ps1")),
                (*display_prefix, "scripts/reproduce.ps1"),
            ),
            CommandSpec(
                "doctor-host",
                (venv_python, "-I", "scripts/doctor.py", "--profile", "host"),
                (".venv/Scripts/python.exe", "-I", "scripts/doctor.py", "--profile", "host"),
            ),
            CommandSpec(
                "all-host-wrapper",
                (*prefix, str(source_root / "scripts" / "validate.ps1"), "-Suite", "all"),
                (*display_prefix, "scripts/validate.ps1", "-Suite", "all"),
            ),
        )
    if system == "Linux":
        bash = shutil.which("bash")
        if bash is None:
            raise CleanRoomError("bash is unavailable for the Linux host profile", EXIT_EXECUTION)
        venv_python = str(source_root / ".venv" / "bin" / "python")
        return (
            CommandSpec(
                "reproduce-host",
                (str(source_root / "scripts" / "reproduce.sh"),),
                ("./scripts/reproduce.sh",),
            ),
            CommandSpec(
                "doctor-host",
                (venv_python, "-I", "scripts/doctor.py", "--profile", "host"),
                (".venv/bin/python", "-I", "scripts/doctor.py", "--profile", "host"),
            ),
            CommandSpec(
                "all-host-wrapper",
                (bash, "scripts/validate.sh", "--suite", "all"),
                ("bash", "scripts/validate.sh", "--suite", "all"),
            ),
        )
    raise CleanRoomError(
        f"native host rehearsal is unsupported on {system or 'unknown OS'}",
        EXIT_EXECUTION,
    )


def _required_command_files(profile: str, system: str) -> tuple[str, ...]:
    common = ("scripts/doctor.py", "scripts/validate.py")
    if profile != "host":
        return common
    if system == "Windows":
        # reproduce.ps1 owns the initial bootstrap; bootstrap.ps1 and
        # validate.ps1 remain explicit transitive requirements.
        return (*common, "scripts/bootstrap.ps1", "scripts/validate.ps1", "scripts/reproduce.ps1")
    if system == "Linux":
        # reproduce.sh executes bootstrap.sh and then validate.sh directly, so
        # all three shell files must be present in the exported candidate.
        return (*common, "scripts/bootstrap.sh", "scripts/validate.sh", "scripts/reproduce.sh")
    return common


def _validate_rehearsal_command_plan(
    plan: Sequence[CommandSpec], source_root: Path, system: str
) -> str:
    command_ids = tuple(item.command_id for item in plan)
    if command_ids != EXPECTED_REHEARSAL_COMMAND_IDS:
        raise CleanRoomError(
            "rehearsal command plan must start with reproduce-host and contain "
            "only reproduce-host, doctor-host, all-host-wrapper",
            EXIT_INTEGRITY,
        )
    if any(item.command_id == "bootstrap-host" for item in plan):
        raise CleanRoomError(
            "standalone bootstrap-host is forbidden because reproduce-host owns "
            "the from-zero bootstrap",
            EXIT_INTEGRITY,
        )

    if system == "Windows":
        wrapper = "scripts/reproduce.ps1"
        if plan[0].display_argv[-1:] != (wrapper,):
            raise CleanRoomError(
                "Windows reproduce-host does not target the canonical wrapper",
                EXIT_INTEGRITY,
            )
    elif system == "Linux":
        wrapper = "scripts/reproduce.sh"
        expected_actual = (str(source_root / "scripts" / "reproduce.sh"),)
        if plan[0].actual_argv != expected_actual or plan[0].display_argv != (
            "./scripts/reproduce.sh",
        ):
            raise CleanRoomError(
                "Linux reproduce-host must execute ./scripts/reproduce.sh directly",
                EXIT_INTEGRITY,
            )
    else:
        raise CleanRoomError(
            f"native host rehearsal is unsupported on {system or 'unknown OS'}",
            EXIT_EXECUTION,
        )
    return wrapper


def _cold_start_contract(
    *,
    plan: Sequence[CommandSpec],
    source_root: Path,
    system: str,
    observe_filesystem: bool,
) -> dict[str, Any]:
    wrapper = _validate_rehearsal_command_plan(plan, source_root, system)
    observed_state: str | None = None
    status_value = "DECLARED"
    if observe_filesystem:
        venv = source_root / ".venv"
        if venv.exists() or venv.is_symlink():
            raise CleanRoomError(
                "rehearsal source already contains .venv before reproduce-host",
                EXIT_INTEGRITY,
            )
        if system == "Linux":
            non_executable = [
                relative
                for relative in (
                    "scripts/reproduce.sh",
                    "scripts/bootstrap.sh",
                    "scripts/validate.sh",
                )
                if not os.access(source_root / relative, os.X_OK)
            ]
            if non_executable:
                raise CleanRoomError(
                    "canonical Linux reproduce chain is not executable: "
                    + ", ".join(non_executable),
                    EXIT_EXECUTION,
                )
        observed_state = "ABSENT"
        status_value = "PASS"
    return {
        "status": status_value,
        "required_initial_repository_venv_state": "ABSENT",
        "observed_initial_repository_venv_state": observed_state,
        "first_command_id": plan[0].command_id,
        "command_ids": [item.command_id for item in plan],
        "canonical_reproduce_wrapper": wrapper,
        "from_zero_bootstrap_owner": "reproduce-host",
        "contract": (
            "reproduce-host starts without a repository .venv and delegates to "
            "the canonical lock bootstrap before the frozen all suite"
        ),
    }


def _normalize_log(text: str, paths: Iterable[Path]) -> str:
    result = text
    replacements: set[str] = set()
    for path in paths:
        try:
            raw = str(path.resolve())
        except OSError:
            raw = str(path.absolute())
        replacements.update({raw, raw.replace("\\", "/")})
    for raw in sorted((item for item in replacements if item), key=len, reverse=True):
        result = result.replace(raw, "<LOCAL_PATH>")
        if platform.system() == "Windows":
            result = re.sub(re.escape(raw), "<LOCAL_PATH>", result, flags=re.IGNORECASE)
    result = _WINDOWS_ABSOLUTE_RE.sub("<ABSOLUTE_PATH>", result)
    result = _POSIX_ABSOLUTE_RE.sub("<ABSOLUTE_PATH>", result)
    return result


def _run_commands(
    plan: Sequence[CommandSpec],
    source_root: Path,
    evidence_dir: Path,
    run_root: Path,
    environment: dict[str, str],
    timeout_seconds: int,
) -> tuple[list[dict[str, Any]], bool]:
    logs = evidence_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    failed = False
    known_paths = (
        run_root,
        source_root,
        Path.home(),
        Path(tempfile.gettempdir()),
        Path(sys.executable),
    )
    for index, spec in enumerate(plan):
        if failed:
            results.append(
                {
                    "id": spec.command_id,
                    "argv": list(spec.display_argv),
                    "status": "NOT_RUN",
                    "reason": "an earlier fail-closed command did not succeed",
                }
            )
            continue
        try:
            command_environment = environment.copy()
            command_environment.update(dict(spec.environment_overrides))
            completed = subprocess.run(
                list(spec.actual_argv),
                cwd=str(source_root),
                env=command_environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
            return_code = completed.returncode
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            status_value = "PASS" if return_code == 0 else "FAIL"
        except FileNotFoundError as exc:
            return_code = 127
            stdout = ""
            stderr = f"command unavailable: {exc}"
            status_value = "FAIL"
        except subprocess.TimeoutExpired as exc:
            return_code = 124
            stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            stderr += "\ncommand timed out"
            status_value = "TIMEOUT"

        stdout = _normalize_log(stdout, known_paths)
        stderr = _normalize_log(stderr, known_paths)
        stdout_path = logs / f"{index + 1:02d}-{spec.command_id}.stdout.log"
        stderr_path = logs / f"{index + 1:02d}-{spec.command_id}.stderr.log"
        _atomic_write(stdout_path, stdout.encode("utf-8"), run_root)
        _atomic_write(stderr_path, stderr.encode("utf-8"), run_root)
        results.append(
            {
                "id": spec.command_id,
                "argv": list(spec.display_argv),
                "status": status_value,
                "exit_code": return_code,
                "stdout_log": _relative_path(run_root, stdout_path),
                "stdout_sha256": _sha256_file(stdout_path),
                "stderr_log": _relative_path(run_root, stderr_path),
                "stderr_sha256": _sha256_file(stderr_path),
            }
        )
        failed = return_code != 0
    return results, failed


def _source_path_baseline(source_root: Path, run_root: Path) -> frozenset[str]:
    """Record all pre-command source paths except the known ephemeral .git."""
    _assert_contained(source_root, run_root)
    paths: set[str] = set()

    def visit(directory: Path) -> None:
        try:
            entries = sorted(
                os.scandir(directory),
                key=lambda item: _sort_key(unicodedata.normalize("NFC", item.name)),
            )
        except OSError as exc:
            raise CleanRoomError(
                f"cannot record pre-command source baseline: {type(exc).__name__}",
                EXIT_INTEGRITY,
            ) from exc
        for entry in entries:
            path = Path(entry.path)
            _assert_contained(path, source_root)
            relative = _relative_path(source_root, path)
            if relative == ".git":
                continue
            paths.add(relative)
            try:
                link_like = entry.is_symlink() or _is_linklike(path)
                is_directory = entry.is_dir(follow_symlinks=False)
            except OSError as exc:
                raise CleanRoomError(
                    "cannot inspect pre-command source baseline entry",
                    EXIT_INTEGRITY,
                ) from exc
            if is_directory and not link_like:
                visit(path)

    visit(source_root)
    return frozenset(paths)


# Cleanup is security-sensitive: every target is scanned twice,
# bound to stable filesystem identities, atomically moved into a same-run
# quarantine, scanned again, and only then removed entry by entry.  All
# mutation checks are anchored at the immutable run/source root instead of at
# the target being deleted.  Keeping this implementation adjacent to the
# post-run audit makes the cleanup/audit boundary explicit.


@dataclass(frozen=True)
class CleanupIdentity:
    kind: str
    device: int
    inode: int
    nlink: int
    size: int
    mtime_ns: int
    mode: int
    windows_attributes: int

    def stable_key(self) -> tuple[str, int, int]:
        return self.kind, self.device, self.inode

    def exact_key(self) -> tuple[Any, ...]:
        if self.kind == "directory":
            return self.stable_key()
        return (*self.stable_key(), self.nlink, self.size, self.mtime_ns)


@dataclass(frozen=True)
class CleanupTreePlan:
    stable_boundary: Path
    target: Path
    identities: dict[str, CleanupIdentity]
    directories: tuple[Path, ...]
    files: tuple[Path, ...]
    links: tuple[Path, ...]


@dataclass(frozen=True)
class CleanupFilePlan:
    stable_boundary: Path
    target: Path
    identities: dict[str, CleanupIdentity]


def _cleanup_path_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _cleanup_lexical_relative(path: Path, boundary: Path) -> Path:
    path_absolute = Path(os.path.abspath(os.fspath(path)))
    boundary_absolute = Path(os.path.abspath(os.fspath(boundary)))
    try:
        relative = path_absolute.relative_to(boundary_absolute)
    except ValueError as exc:
        raise CleanRoomError(
            "cleanup path escaped its stable boundary", EXIT_BOUNDARY
        ) from exc
    if relative == Path("."):
        return relative
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise CleanRoomError("cleanup path is not lexically safe", EXIT_BOUNDARY)
    return relative


def _cleanup_identity(path: Path, *, label: str) -> CleanupIdentity:
    try:
        entry_stat = path.lstat()
    except OSError as exc:
        raise CleanRoomError(
            f"cannot lstat {label}: {type(exc).__name__}", EXIT_INTEGRITY
        ) from exc
    attributes = int(getattr(entry_stat, "st_file_attributes", 0))
    reparse = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    if stat.S_ISLNK(entry_stat.st_mode) or bool(attributes & reparse):
        kind = "link"
    elif stat.S_ISDIR(entry_stat.st_mode):
        kind = "directory"
    elif stat.S_ISREG(entry_stat.st_mode):
        kind = "file"
    else:
        kind = "special"
    inode = int(entry_stat.st_ino)
    if inode <= 0:
        raise CleanRoomError(
            f"filesystem identity is unavailable for {label}", EXIT_INTEGRITY
        )
    return CleanupIdentity(
        kind=kind,
        device=int(entry_stat.st_dev),
        inode=inode,
        nlink=int(entry_stat.st_nlink),
        size=int(entry_stat.st_size),
        mtime_ns=int(entry_stat.st_mtime_ns),
        mode=int(entry_stat.st_mode),
        windows_attributes=attributes,
    )


def _cleanup_merge_identity(
    identities: dict[str, CleanupIdentity],
    path: Path,
    identity: CleanupIdentity,
) -> None:
    key = _cleanup_path_key(path)
    previous = identities.get(key)
    if previous is not None and previous.exact_key() != identity.exact_key():
        raise CleanRoomError(
            "cleanup identity changed during preflight", EXIT_INTEGRITY
        )
    identities[key] = identity


def _cleanup_chain(boundary: Path, path: Path) -> tuple[Path, ...]:
    relative = _cleanup_lexical_relative(path, boundary)
    current = Path(os.path.abspath(os.fspath(boundary)))
    chain = [current]
    for part in relative.parts:
        current = current / part
        chain.append(current)
    return tuple(chain)


def _cleanup_capture_real_directory_chain(
    boundary: Path,
    directory: Path,
    identities: dict[str, CleanupIdentity],
    *,
    label: str,
) -> None:
    for path in _cleanup_chain(boundary, directory):
        identity = _cleanup_identity(path, label=label)
        if identity.kind != "directory":
            raise CleanRoomError(
                f"{label} ancestor is not a real directory", EXIT_INTEGRITY
            )
        _cleanup_merge_identity(identities, path, identity)


def _cleanup_verify_path(
    *,
    boundary: Path,
    path: Path,
    identities: dict[str, CleanupIdentity],
    expected_kind: str,
    exact_final: bool,
    label: str,
) -> CleanupIdentity:
    chain = _cleanup_chain(boundary, path)
    for index, current_path in enumerate(chain):
        key = _cleanup_path_key(current_path)
        expected = identities.get(key)
        if expected is None:
            raise CleanRoomError(
                f"{label} path was not in the cleanup preflight", EXIT_INTEGRITY
            )
        current = _cleanup_identity(current_path, label=label)
        final = index == len(chain) - 1
        required_kind = expected_kind if final else "directory"
        if current.kind != required_kind or expected.kind != required_kind:
            raise CleanRoomError(
                f"{label} type changed after preflight", EXIT_INTEGRITY
            )
        if current.stable_key() != expected.stable_key():
            raise CleanRoomError(
                f"{label} identity changed after preflight", EXIT_INTEGRITY
            )
        if final and exact_final and current.exact_key() != expected.exact_key():
            raise CleanRoomError(
                f"{label} metadata changed after preflight", EXIT_INTEGRITY
            )
    return current


def _cleanup_preflight_tree_once(
    target: Path,
    stable_boundary: Path,
    *,
    label: str,
    allow_posix_symlink_leaves: bool,
) -> CleanupTreePlan:
    if _cleanup_lexical_relative(target, stable_boundary) == Path("."):
        raise CleanRoomError(
            f"refusing to clean the stable {label} boundary", EXIT_BOUNDARY
        )
    identities: dict[str, CleanupIdentity] = {}
    _cleanup_capture_real_directory_chain(
        stable_boundary, target, identities, label=label
    )
    directories: list[Path] = []
    files: list[Path] = []
    links: list[Path] = []
    pending = [Path(os.path.abspath(os.fspath(target)))]
    while pending:
        directory = pending.pop()
        directory_identity = _cleanup_identity(directory, label=label)
        if directory_identity.kind != "directory":
            raise CleanRoomError(
                f"{label} contains a replaced directory", EXIT_INTEGRITY
            )
        _cleanup_merge_identity(identities, directory, directory_identity)
        directories.append(directory)
        try:
            entries = sorted(
                os.scandir(directory),
                key=lambda item: _sort_key(unicodedata.normalize("NFC", item.name)),
            )
        except OSError as exc:
            raise CleanRoomError(
                f"cannot scan {label}: {type(exc).__name__}", EXIT_INTEGRITY
            ) from exc
        for entry in entries:
            path = Path(entry.path)
            _cleanup_lexical_relative(path, stable_boundary)
            identity = _cleanup_identity(path, label=label)
            _cleanup_merge_identity(identities, path, identity)
            if identity.kind == "directory":
                pending.append(path)
            elif identity.kind == "file":
                files.append(path)
            elif identity.kind == "link":
                if os.name == "nt" or not allow_posix_symlink_leaves:
                    raise CleanRoomError(
                        f"{label} contains a link/reparse entry", EXIT_INTEGRITY
                    )
                links.append(path)
            else:
                raise CleanRoomError(
                    f"{label} contains a special filesystem entry", EXIT_INTEGRITY
                )
    directories.sort(key=lambda item: _sort_key(os.fspath(item)))
    files.sort(key=lambda item: _sort_key(os.fspath(item)))
    links.sort(key=lambda item: _sort_key(os.fspath(item)))
    return CleanupTreePlan(
        stable_boundary=Path(os.path.abspath(os.fspath(stable_boundary))),
        target=Path(os.path.abspath(os.fspath(target))),
        identities=identities,
        directories=tuple(directories),
        files=tuple(files),
        links=tuple(links),
    )


def _cleanup_tree_signature(plan: CleanupTreePlan) -> tuple[tuple[Any, ...], ...]:
    records: list[tuple[Any, ...]] = []
    for kind, paths in (
        ("directory", plan.directories),
        ("file", plan.files),
        ("link", plan.links),
    ):
        for path in paths:
            relative = _cleanup_lexical_relative(path, plan.target).as_posix()
            identity = plan.identities[_cleanup_path_key(path)]
            records.append((relative, kind, *identity.exact_key()))
    records.sort(key=lambda item: _sort_key(str(item[0])))
    return tuple(records)


def _cleanup_preflight_tree(
    target: Path,
    stable_boundary: Path,
    *,
    label: str,
    allow_posix_symlink_leaves: bool,
) -> CleanupTreePlan:
    first = _cleanup_preflight_tree_once(
        target,
        stable_boundary,
        label=label,
        allow_posix_symlink_leaves=allow_posix_symlink_leaves,
    )
    second = _cleanup_preflight_tree_once(
        target,
        stable_boundary,
        label=label,
        allow_posix_symlink_leaves=allow_posix_symlink_leaves,
    )
    if _cleanup_tree_signature(first) != _cleanup_tree_signature(second):
        raise CleanRoomError(
            f"{label} changed between cleanup preflight scans", EXIT_INTEGRITY
        )
    return second


def _cleanup_preflight_file_once(
    target: Path,
    stable_boundary: Path,
    *,
    label: str,
) -> CleanupFilePlan:
    if _cleanup_lexical_relative(target, stable_boundary) == Path("."):
        raise CleanRoomError(f"refusing to clean {label} boundary", EXIT_BOUNDARY)
    identities: dict[str, CleanupIdentity] = {}
    _cleanup_capture_real_directory_chain(
        stable_boundary, target.parent, identities, label=label
    )
    identity = _cleanup_identity(target, label=label)
    if identity.kind != "file":
        raise CleanRoomError(f"{label} is not a regular file", EXIT_INTEGRITY)
    _cleanup_merge_identity(identities, target, identity)
    return CleanupFilePlan(
        stable_boundary=Path(os.path.abspath(os.fspath(stable_boundary))),
        target=Path(os.path.abspath(os.fspath(target))),
        identities=identities,
    )


def _cleanup_preflight_file(
    target: Path,
    stable_boundary: Path,
    *,
    label: str,
) -> CleanupFilePlan:
    first = _cleanup_preflight_file_once(target, stable_boundary, label=label)
    second = _cleanup_preflight_file_once(target, stable_boundary, label=label)
    first_identity = first.identities[_cleanup_path_key(first.target)]
    second_identity = second.identities[_cleanup_path_key(second.target)]
    if first_identity.exact_key() != second_identity.exact_key():
        raise CleanRoomError(
            f"{label} changed between cleanup preflight scans", EXIT_INTEGRITY
        )
    return second


def _cleanup_prepare_quarantine(run_root: Path) -> tuple[Path, CleanupIdentity]:
    quarantine = run_root / ".cleanup-quarantine"
    _cleanup_lexical_relative(quarantine, run_root)
    try:
        quarantine.lstat()
    except FileNotFoundError:
        quarantine.mkdir()
    except OSError as exc:
        raise CleanRoomError(
            f"cannot inspect cleanup quarantine: {type(exc).__name__}",
            EXIT_INTEGRITY,
        ) from exc
    identity = _cleanup_identity(quarantine, label="cleanup quarantine")
    if identity.kind != "directory":
        raise CleanRoomError(
            "cleanup quarantine is not a real directory", EXIT_INTEGRITY
        )
    try:
        if any(os.scandir(quarantine)):
            raise CleanRoomError(
                "cleanup quarantine is not empty", EXIT_INTEGRITY
            )
    except OSError as exc:
        raise CleanRoomError(
            f"cannot scan cleanup quarantine: {type(exc).__name__}",
            EXIT_INTEGRITY,
        ) from exc
    return quarantine, identity


def _cleanup_verify_quarantine(
    quarantine: Path, expected: CleanupIdentity, run_root: Path
) -> None:
    relative = _cleanup_lexical_relative(quarantine, run_root)
    if relative.as_posix() != ".cleanup-quarantine":
        raise CleanRoomError("cleanup quarantine path changed", EXIT_BOUNDARY)
    current = _cleanup_identity(quarantine, label="cleanup quarantine")
    if current.kind != "directory" or current.stable_key() != expected.stable_key():
        raise CleanRoomError(
            "cleanup quarantine identity changed", EXIT_INTEGRITY
        )


def _cleanup_require_absent(path: Path, *, label: str) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise CleanRoomError(
            f"cannot verify removal of {label}: {type(exc).__name__}",
            EXIT_INTEGRITY,
        ) from exc
    raise CleanRoomError(f"{label} still exists after cleanup", EXIT_INTEGRITY)


def _cleanup_rename_once(source: Path, destination: Path) -> None:
    os.rename(source, destination)


def _cleanup_quarantine_tree(
    plan: CleanupTreePlan,
    *,
    quarantine: Path,
    quarantine_identity: CleanupIdentity,
    run_root: Path,
    quarantine_name: str,
    label: str,
    allow_posix_symlink_leaves: bool,
) -> CleanupTreePlan:
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", quarantine_name) is None:
        raise CleanRoomError("invalid internal quarantine name", EXIT_BOUNDARY)
    destination = quarantine / quarantine_name
    _cleanup_verify_quarantine(quarantine, quarantine_identity, run_root)
    try:
        destination.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise CleanRoomError(
            f"cannot inspect {label} quarantine target: {type(exc).__name__}",
            EXIT_INTEGRITY,
        ) from exc
    else:
        raise CleanRoomError(f"{label} quarantine target exists", EXIT_INTEGRITY)
    _cleanup_verify_path(
        boundary=plan.stable_boundary,
        path=plan.target,
        identities=plan.identities,
        expected_kind="directory",
        exact_final=True,
        label=label,
    )
    try:
        _cleanup_rename_once(plan.target, destination)
    except OSError as exc:
        raise CleanRoomError(
            f"cannot quarantine {label}: {type(exc).__name__}", EXIT_INTEGRITY
        ) from exc
    _cleanup_require_absent(plan.target, label=f"original {label}")
    moved = _cleanup_preflight_tree(
        destination,
        quarantine,
        label=f"quarantined {label}",
        allow_posix_symlink_leaves=allow_posix_symlink_leaves,
    )
    if _cleanup_tree_signature(plan) != _cleanup_tree_signature(moved):
        raise CleanRoomError(
            f"{label} identity changed while entering quarantine", EXIT_INTEGRITY
        )
    return moved


def _cleanup_quarantine_file(
    plan: CleanupFilePlan,
    *,
    quarantine: Path,
    quarantine_identity: CleanupIdentity,
    run_root: Path,
    quarantine_name: str,
    label: str,
) -> CleanupFilePlan:
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", quarantine_name) is None:
        raise CleanRoomError("invalid internal quarantine name", EXIT_BOUNDARY)
    destination = quarantine / quarantine_name
    _cleanup_verify_quarantine(quarantine, quarantine_identity, run_root)
    try:
        destination.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise CleanRoomError(
            f"cannot inspect {label} quarantine target: {type(exc).__name__}",
            EXIT_INTEGRITY,
        ) from exc
    else:
        raise CleanRoomError(f"{label} quarantine target exists", EXIT_INTEGRITY)
    before = _cleanup_verify_path(
        boundary=plan.stable_boundary,
        path=plan.target,
        identities=plan.identities,
        expected_kind="file",
        exact_final=True,
        label=label,
    )
    try:
        _cleanup_rename_once(plan.target, destination)
    except OSError as exc:
        raise CleanRoomError(
            f"cannot quarantine {label}: {type(exc).__name__}", EXIT_INTEGRITY
        ) from exc
    _cleanup_require_absent(plan.target, label=f"original {label}")
    moved = _cleanup_preflight_file(
        destination, quarantine, label=f"quarantined {label}"
    )
    after = moved.identities[_cleanup_path_key(moved.target)]
    if before.exact_key() != after.exact_key():
        raise CleanRoomError(
            f"{label} identity changed while entering quarantine", EXIT_INTEGRITY
        )
    return moved


def _cleanup_unlink_once(path: Path) -> None:
    path.unlink()


def _cleanup_rmdir_once(path: Path) -> None:
    path.rmdir()


def _cleanup_is_windows_read_only(identity: CleanupIdentity) -> bool:
    read_only = int(getattr(stat, "FILE_ATTRIBUTE_READONLY", 0))
    return bool(read_only and identity.windows_attributes & read_only)


def _cleanup_unlink_preflighted(
    plan: CleanupTreePlan | CleanupFilePlan,
    path: Path,
    *,
    expected_kind: str,
    label: str,
) -> bool:
    current = _cleanup_verify_path(
        boundary=plan.stable_boundary,
        path=path,
        identities=plan.identities,
        expected_kind=expected_kind,
        exact_final=True,
        label=label,
    )
    try:
        _cleanup_unlink_once(path)
        _cleanup_require_absent(path, label=label)
        return False
    except PermissionError as exc:
        if os.name != "nt" or expected_kind != "file":
            raise CleanRoomError(
                f"cannot unlink {label}: PermissionError", EXIT_INTEGRITY
            ) from exc
        current = _cleanup_verify_path(
            boundary=plan.stable_boundary,
            path=path,
            identities=plan.identities,
            expected_kind="file",
            exact_final=True,
            label=label,
        )
        if not _cleanup_is_windows_read_only(current):
            raise CleanRoomError(
                f"{label} permission failure is not a read-only attribute",
                EXIT_INTEGRITY,
            ) from exc
        if current.nlink != 1:
            raise CleanRoomError(
                f"refusing read-only retry for multiply linked {label}",
                EXIT_INTEGRITY,
            ) from exc
        try:
            os.chmod(path, stat.S_IMODE(current.mode) | stat.S_IWUSR)
        except OSError as chmod_exc:
            raise CleanRoomError(
                f"cannot clear read-only attribute for {label}: "
                f"{type(chmod_exc).__name__}",
                EXIT_INTEGRITY,
            ) from chmod_exc
        _cleanup_verify_path(
            boundary=plan.stable_boundary,
            path=path,
            identities=plan.identities,
            expected_kind="file",
            exact_final=True,
            label=label,
        )
        try:
            _cleanup_unlink_once(path)
        except OSError as retry_exc:
            raise CleanRoomError(
                f"read-only retry failed for {label}: {type(retry_exc).__name__}",
                EXIT_INTEGRITY,
            ) from retry_exc
        _cleanup_require_absent(path, label=label)
        return True
    except OSError as exc:
        raise CleanRoomError(
            f"cannot unlink {label}: {type(exc).__name__}", EXIT_INTEGRITY
        ) from exc


def _cleanup_rmdir_preflighted(
    plan: CleanupTreePlan,
    path: Path,
    *,
    label: str,
) -> bool:
    current = _cleanup_verify_path(
        boundary=plan.stable_boundary,
        path=path,
        identities=plan.identities,
        expected_kind="directory",
        exact_final=False,
        label=label,
    )
    try:
        _cleanup_rmdir_once(path)
        _cleanup_require_absent(path, label=label)
        return False
    except PermissionError as exc:
        if os.name != "nt" or not _cleanup_is_windows_read_only(current):
            raise CleanRoomError(
                f"cannot remove {label}: PermissionError", EXIT_INTEGRITY
            ) from exc
        try:
            os.chmod(
                path,
                stat.S_IMODE(current.mode) | stat.S_IWUSR | stat.S_IXUSR,
            )
        except OSError as chmod_exc:
            raise CleanRoomError(
                f"cannot clear read-only directory attribute for {label}: "
                f"{type(chmod_exc).__name__}",
                EXIT_INTEGRITY,
            ) from chmod_exc
        _cleanup_verify_path(
            boundary=plan.stable_boundary,
            path=path,
            identities=plan.identities,
            expected_kind="directory",
            exact_final=False,
            label=label,
        )
        try:
            _cleanup_rmdir_once(path)
        except OSError as retry_exc:
            raise CleanRoomError(
                f"read-only directory retry failed for {label}: "
                f"{type(retry_exc).__name__}",
                EXIT_INTEGRITY,
            ) from retry_exc
        _cleanup_require_absent(path, label=label)
        return True
    except OSError as exc:
        raise CleanRoomError(
            f"cannot remove {label}: {type(exc).__name__}", EXIT_INTEGRITY
        ) from exc


def _cleanup_delete_tree(
    plan: CleanupTreePlan, *, label: str
) -> dict[str, int]:
    read_only_retries = 0
    for path in (*plan.links, *plan.files):
        expected_kind = "link" if path in plan.links else "file"
        retried = _cleanup_unlink_preflighted(
            plan, path, expected_kind=expected_kind, label=label
        )
        read_only_retries += int(retried)
    directories = sorted(
        plan.directories,
        key=lambda item: (len(item.parts), _sort_key(os.fspath(item))),
        reverse=True,
    )
    for path in directories:
        retried = _cleanup_rmdir_preflighted(plan, path, label=label)
        read_only_retries += int(retried)
    return {
        "removed_directory_count": len(plan.directories),
        "removed_file_count": len(plan.files),
        "removed_symlink_count": len(plan.links),
        "windows_read_only_retries": read_only_retries,
    }


def _cleanup_delete_file(plan: CleanupFilePlan, *, label: str) -> dict[str, int]:
    retried = _cleanup_unlink_preflighted(
        plan, plan.target, expected_kind="file", label=label
    )
    return {
        "removed_file_count": 1,
        "windows_read_only_retries": int(retried),
    }


def _safe_remove_runtime(
    path: Path,
    run_root: Path,
    quarantine: Path,
    quarantine_identity: CleanupIdentity,
) -> dict[str, Any]:
    relative = _cleanup_lexical_relative(path, run_root).as_posix()
    policies = {
        "source/.venv": ("ephemeral venv", "ephemeral-venv", os.name != "nt"),
        "runtime": ("ephemeral runtime", "ephemeral-runtime", False),
    }
    policy = policies.get(relative)
    if policy is None:
        raise CleanRoomError(
            "runtime cleanup target is not allowlisted", EXIT_BOUNDARY
        )
    label, quarantine_name, allow_posix_symlink_leaves = policy
    try:
        path.lstat()
    except FileNotFoundError:
        return {"status": "ABSENT", "target": relative}
    except OSError as exc:
        raise CleanRoomError(
            f"cannot inspect {label}: {type(exc).__name__}", EXIT_INTEGRITY
        ) from exc
    plan = _cleanup_preflight_tree(
        path,
        run_root,
        label=label,
        allow_posix_symlink_leaves=allow_posix_symlink_leaves,
    )
    moved = _cleanup_quarantine_tree(
        plan,
        quarantine=quarantine,
        quarantine_identity=quarantine_identity,
        run_root=run_root,
        quarantine_name=quarantine_name,
        label=label,
        allow_posix_symlink_leaves=allow_posix_symlink_leaves,
    )
    result = _cleanup_delete_tree(moved, label=label)
    return {"status": "REMOVED", "target": relative, **result}


def _safe_remove_ephemeral_git(
    git_dir: Path,
    source_root: Path,
    run_root: Path,
    quarantine: Path,
    quarantine_identity: CleanupIdentity,
) -> dict[str, Any]:
    if _cleanup_lexical_relative(git_dir, source_root).as_posix() != ".git":
        raise CleanRoomError(
            "ephemeral Git cleanup target is not exact source/.git",
            EXIT_BOUNDARY,
        )
    try:
        git_dir.lstat()
    except FileNotFoundError:
        return {
            "status": "ABSENT",
            "target": ".git",
            "removed_directory_count": 0,
            "removed_file_count": 0,
            "removed_symlink_count": 0,
            "windows_read_only_retries": 0,
        }
    except OSError as exc:
        raise CleanRoomError(
            f"cannot inspect ephemeral Git: {type(exc).__name__}",
            EXIT_INTEGRITY,
        ) from exc
    plan = _cleanup_preflight_tree(
        git_dir,
        run_root,
        label="ephemeral Git",
        allow_posix_symlink_leaves=False,
    )
    moved = _cleanup_quarantine_tree(
        plan,
        quarantine=quarantine,
        quarantine_identity=quarantine_identity,
        run_root=run_root,
        quarantine_name="ephemeral-git",
        label="ephemeral Git",
        allow_posix_symlink_leaves=False,
    )
    result = _cleanup_delete_tree(moved, label="ephemeral Git")
    return {"status": "REMOVED", "target": ".git", **result}


def _find_generated_python_cache_targets(
    source_root: Path, run_root: Path
) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    _cleanup_lexical_relative(source_root, run_root)
    directories: list[Path] = []
    standalone_files: list[Path] = []
    skipped_roots = {".git", ".venv", "build"}

    def visit(directory: Path) -> None:
        try:
            entries = sorted(
                os.scandir(directory),
                key=lambda item: _sort_key(unicodedata.normalize("NFC", item.name)),
            )
        except OSError as exc:
            raise CleanRoomError(
                f"cannot locate generated Python cache: {type(exc).__name__}",
                EXIT_INTEGRITY,
            ) from exc
        for entry in entries:
            path = Path(entry.path)
            _cleanup_lexical_relative(path, source_root)
            if directory == source_root and entry.name in skipped_roots:
                continue
            identity = _cleanup_identity(path, label="generated Python cache scan")
            if entry.name == "__pycache__":
                if identity.kind != "directory":
                    raise CleanRoomError(
                        "generated __pycache__ target is link-like or invalid",
                        EXIT_INTEGRITY,
                    )
                directories.append(path)
                continue
            if identity.kind == "directory":
                visit(path)
            elif identity.kind == "file":
                if path.suffix in {".pyc", ".pyo"}:
                    standalone_files.append(path)
            elif identity.kind == "link":
                continue
            else:
                raise CleanRoomError(
                    "source contains a special entry during cache scan",
                    EXIT_INTEGRITY,
                )

    visit(source_root)
    directories.sort(key=lambda item: _sort_key(_relative_path(source_root, item)))
    standalone_files.sort(
        key=lambda item: _sort_key(_relative_path(source_root, item))
    )
    return tuple(directories), tuple(standalone_files)


def _cleanup_generated_python_caches(
    source_root: Path,
    run_root: Path,
    baseline_paths: frozenset[str],
    candidate_paths: frozenset[str],
    quarantine: Path,
    quarantine_identity: CleanupIdentity,
) -> dict[str, Any]:
    cache_directories, standalone_files = _find_generated_python_cache_targets(
        source_root, run_root
    )
    baseline_folded = {path.casefold() for path in baseline_paths}
    candidate_folded = {path.casefold() for path in candidate_paths}
    directory_plans: list[tuple[str, CleanupTreePlan]] = []
    file_plans: list[tuple[str, CleanupFilePlan]] = []

    for target in cache_directories:
        relative = _relative_path(source_root, target)
        folded = relative.casefold()
        prefix = folded + "/"
        if folded in baseline_folded or any(
            path.startswith(prefix) for path in baseline_folded
        ):
            raise CleanRoomError(
                f"Python cache existed before rehearsal commands: {relative}",
                EXIT_INTEGRITY,
            )
        if folded in candidate_folded or any(
            path.startswith(prefix) for path in candidate_folded
        ):
            raise CleanRoomError(
                f"Python cache overlaps a release-candidate path: {relative}",
                EXIT_INTEGRITY,
            )
        plan = _cleanup_preflight_tree(
            target,
            source_root,
            label=f"generated Python cache {relative}",
            allow_posix_symlink_leaves=False,
        )
        if len(plan.directories) != 1 or plan.links:
            raise CleanRoomError(
                f"generated Python cache has nested/link entries: {relative}",
                EXIT_INTEGRITY,
            )
        for path in plan.files:
            file_relative = _relative_path(source_root, path)
            if path.suffix not in {".pyc", ".pyo"}:
                raise CleanRoomError(
                    f"generated Python cache contains an unknown file: {file_relative}",
                    EXIT_INTEGRITY,
                )
        directory_plans.append((relative, plan))

    for target in standalone_files:
        relative = _relative_path(source_root, target)
        folded = relative.casefold()
        if folded in baseline_folded or folded in candidate_folded:
            raise CleanRoomError(
                f"standalone bytecode overlaps protected input: {relative}",
                EXIT_INTEGRITY,
            )
        file_plans.append(
            (
                relative,
                _cleanup_preflight_file(
                    target,
                    source_root,
                    label=f"standalone Python bytecode {relative}",
                ),
            )
        )

    moved_directories: list[tuple[str, CleanupTreePlan]] = []
    moved_files: list[tuple[str, CleanupFilePlan]] = []
    for index, (relative, plan) in enumerate(directory_plans, 1):
        moved_directories.append(
            (
                relative,
                _cleanup_quarantine_tree(
                    plan,
                    quarantine=quarantine,
                    quarantine_identity=quarantine_identity,
                    run_root=run_root,
                    quarantine_name=f"python-cache-{index:04d}",
                    label=f"generated Python cache {relative}",
                    allow_posix_symlink_leaves=False,
                ),
            )
        )
    for index, (relative, plan) in enumerate(file_plans, 1):
        moved_files.append(
            (
                relative,
                _cleanup_quarantine_file(
                    plan,
                    quarantine=quarantine,
                    quarantine_identity=quarantine_identity,
                    run_root=run_root,
                    quarantine_name=f"python-bytecode-{index:04d}",
                    label=f"standalone Python bytecode {relative}",
                ),
            )
        )

    removed_file_count = 0
    read_only_retries = 0
    for relative, plan in moved_directories:
        result = _cleanup_delete_tree(
            plan, label=f"generated Python cache {relative}"
        )
        removed_file_count += result["removed_file_count"]
        read_only_retries += result["windows_read_only_retries"]
    for relative, plan in moved_files:
        result = _cleanup_delete_file(
            plan, label=f"standalone Python bytecode {relative}"
        )
        removed_file_count += result["removed_file_count"]
        read_only_retries += result["windows_read_only_retries"]
    return {
        "status": "PASS",
        "baseline_path_count": len(baseline_paths),
        "candidate_file_count": len(candidate_paths),
        "removed_cache_directory_count": len(moved_directories),
        "removed_standalone_bytecode_count": len(moved_files),
        "removed_cache_file_count": removed_file_count,
        "windows_read_only_retries": read_only_retries,
        "removed_cache_directories": [item[0] for item in moved_directories],
        "removed_standalone_bytecode": [item[0] for item in moved_files],
    }


def _cleanup_finish_quarantine(
    quarantine: Path,
    quarantine_identity: CleanupIdentity,
    run_root: Path,
) -> dict[str, Any]:
    _cleanup_verify_quarantine(quarantine, quarantine_identity, run_root)
    try:
        remaining = sorted(entry.name for entry in os.scandir(quarantine))
    except OSError as exc:
        raise CleanRoomError(
            f"cannot finalize cleanup quarantine: {type(exc).__name__}",
            EXIT_INTEGRITY,
        ) from exc
    if remaining:
        raise CleanRoomError(
            "cleanup quarantine retained failed targets", EXIT_INTEGRITY
        )
    try:
        _cleanup_rmdir_once(quarantine)
    except OSError as exc:
        raise CleanRoomError(
            f"cannot remove empty cleanup quarantine: {type(exc).__name__}",
            EXIT_INTEGRITY,
        ) from exc
    _cleanup_require_absent(quarantine, label="cleanup quarantine")
    return {"status": "REMOVED", "remaining_entry_count": 0}


def _audit_isolated_output(
    source_root: Path, inventory: Inventory
) -> tuple[dict[str, Any], bool]:
    records = _snapshot_tree(
        source_root, mode_overrides={item.path: item.mode for item in inventory.files}
    )
    initial = {item.path: item.public_record() for item in inventory.files}
    current = {item["path"]: item for item in records}
    issues: list[dict[str, str]] = []
    output: list[dict[str, Any]] = []

    for path, initial_record in initial.items():
        current_record = current.get(path)
        if current_record is None:
            issues.append({"path": path, "issue": "exported source file was deleted"})
            continue
        for key in ("kind", "mode", "size", "sha256"):
            if current_record[key] != initial_record[key]:
                issues.append({"path": path, "issue": f"exported source changed: {key}"})
                break

    for path, record in current.items():
        if path in initial:
            continue
        if path == "build" or path.startswith("build/"):
            output.append(record)
        else:
            issues.append({"path": path, "issue": "generated outside allowed build/ path"})

    output.sort(key=lambda item: _sort_key(item["path"]))
    result = {
        "schema": f"{SCHEMA_PREFIX}.output-manifest.v1",
        "phase": "08",
        "activity": ACTIVITY,
        "phase_09_git_clone_performed": False,
        "allowed_generated_prefix": "build/",
        "source_files_unchanged": not any(
            issue["issue"].startswith("exported source") for issue in issues
        ),
        "outside_build_generation_absent": not any(
            issue["issue"].startswith("generated outside") for issue in issues
        ),
        "issue_count": len(issues),
        "issues": issues,
        "output_file_count": len(output),
        "output_tree_sha256": _tree_sha256(output),
        "files": output,
    }
    return result, bool(issues)


def _same_candidate(before: Inventory, after: Inventory) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if before.tree_sha256 != after.tree_sha256:
        issues.append("candidate tree SHA-256 changed")
    if before.git_head != after.git_head:
        issues.append("source Git HEAD changed")
    if before.git_status_sha256 != after.git_status_sha256:
        issues.append("source Git status changed")
    if before.registry_sha256 != after.registry_sha256:
        issues.append("suite registry SHA-256 changed")
    if before.registry_contract_version != after.registry_contract_version:
        issues.append("suite registry contract_version changed")
    before_paths = [(item.path, item.origin, item.sha256) for item in before.files]
    after_paths = [(item.path, item.origin, item.sha256) for item in after.files]
    if before_paths != after_paths and "candidate tree SHA-256 changed" not in issues:
        issues.append("candidate path/origin inventory changed")
    return not issues, issues


def _write_evidence_index(
    run_root: Path,
    evidence_dir: Path,
    *,
    run_id: str,
    mode: str,
    profile: str | None,
    candidate_tree_sha256: str,
    output_tree_sha256: str | None,
    program_status: str,
) -> tuple[Path, str]:
    index_path = evidence_dir / "evidence-index.json"
    entries: list[dict[str, Any]] = []
    for path in sorted(evidence_dir.rglob("*"), key=lambda item: _sort_key(item.as_posix())):
        if not path.is_file() or path == index_path:
            continue
        entries.append(
            {
                "path": _relative_path(run_root, path),
                "size": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    value = {
        "schema": f"{SCHEMA_PREFIX}.evidence-index.v1",
        "phase": "08",
        "activity": ACTIVITY,
        "run_id": run_id,
        "mode": mode,
        "profile": profile,
        "program_status": program_status,
        "phase_09_git_clone_performed": False,
        "phase_09_boundary": PHASE09_STATEMENT,
        "fixed_validation_image_track": CONTAINER_STATEMENT,
        "candidate_tree_sha256": candidate_tree_sha256,
        "output_tree_sha256": output_tree_sha256,
        "evidence_file_count": len(entries),
        "files": entries,
    }
    _write_json(index_path, value, run_root)
    return index_path, _sha256_file(index_path)


def _record_failure(
    *,
    run_root: Path,
    inventory: Inventory,
    mode: str,
    profile: str | None,
    exit_code: int,
    message: str,
) -> None:
    """Best-effort machine record for a newly-created, partial run."""
    if not run_root.exists() or not run_root.is_dir() or _is_linklike(run_root):
        return
    evidence_dir = run_root / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    value = {
        "schema": f"{SCHEMA_PREFIX}.failure.v1",
        "phase": "08",
        "activity": ACTIVITY,
        "mode": mode,
        "profile": profile,
        "program_status": "ERROR",
        "exit_code": exit_code,
        "message": message,
        "phase_09_git_clone_performed": False,
        "phase_09_boundary": PHASE09_STATEMENT,
        "fixed_validation_image_track": CONTAINER_STATEMENT,
        "candidate_tree_sha256": inventory.tree_sha256,
        "suite_registry": {
            "contract_version": inventory.registry_contract_version,
            "sha256": inventory.registry_sha256,
        },
    }
    _write_json(evidence_dir / "failure.json", value, run_root)
    _write_evidence_index(
        run_root,
        evidence_dir,
        run_id=run_root.name,
        mode=mode,
        profile=profile,
        candidate_tree_sha256=inventory.tree_sha256,
        output_tree_sha256=None,
        program_status="ERROR",
    )


def _manifest_only_or_export(
    *,
    root: Path,
    inventory: Inventory,
    mode: str,
    run_id: str,
) -> int:
    run_root = _prepare_run_root(root, run_id)
    evidence_dir = run_root / "evidence"
    evidence_dir.mkdir()
    source_manifest_path = evidence_dir / "source-manifest.json"
    exclusion_manifest_path = evidence_dir / "exclusion-manifest.json"
    _write_json(source_manifest_path, _source_manifest(inventory), run_root)
    _write_json(exclusion_manifest_path, _exclusion_manifest(inventory), run_root)
    exported_hash: str | None = None
    if mode == "export":
        exported_hash = _copy_candidate(inventory, run_root / "source", run_root)
    after = _inventory(root)
    source_unchanged, source_issues = _same_candidate(inventory, after)
    exit_code = EXIT_OK if source_unchanged else EXIT_INTEGRITY
    program_status = "SUCCESS" if exit_code == EXIT_OK else "ERROR"
    result = {
        "schema": f"{SCHEMA_PREFIX}.export-result.v1",
        "phase": "08",
        "activity": ACTIVITY,
        "run_id": run_id,
        "mode": mode,
        "program_status": program_status,
        "exit_code": exit_code,
        "phase_09_git_clone_performed": False,
        "phase_09_boundary": PHASE09_STATEMENT,
        "fixed_validation_image_track": CONTAINER_STATEMENT,
        "source_manifest": "evidence/source-manifest.json",
        "source_manifest_sha256": _sha256_file(source_manifest_path),
        "exclusion_manifest": "evidence/exclusion-manifest.json",
        "exclusion_manifest_sha256": _sha256_file(exclusion_manifest_path),
        "candidate_tree_sha256": inventory.tree_sha256,
        "export_performed": mode == "export",
        "exported_tree_sha256": exported_hash,
        "export_matches_candidate": exported_hash == inventory.tree_sha256 if exported_hash else None,
        "source_candidate_unchanged": source_unchanged,
        "source_candidate_issues": source_issues,
    }
    _write_json(evidence_dir / "export-result.json", result, run_root)
    index_path, index_hash = _write_evidence_index(
        run_root,
        evidence_dir,
        run_id=run_id,
        mode=mode,
        profile=None,
        candidate_tree_sha256=inventory.tree_sha256,
        output_tree_sha256=exported_hash,
        program_status=program_status,
    )
    print(
        f"clean-room {mode} {program_status} exit_code={exit_code} run_id={run_id} "
        f"candidate_tree_sha256={inventory.tree_sha256} "
        f"index={_relative_path(root, index_path)} index_sha256={index_hash}"
    )
    return exit_code


def _rehearsal(
    *,
    root: Path,
    inventory: Inventory,
    run_id: str,
    profile: str,
    timeout_seconds: int,
) -> int:
    run_root = _prepare_run_root(root, run_id)
    evidence_dir = run_root / "evidence"
    evidence_dir.mkdir()
    source_manifest_path = evidence_dir / "source-manifest.json"
    exclusion_manifest_path = evidence_dir / "exclusion-manifest.json"
    _write_json(source_manifest_path, _source_manifest(inventory), run_root)
    _write_json(exclusion_manifest_path, _exclusion_manifest(inventory), run_root)
    source_root = run_root / "source"
    exported_hash = _copy_candidate(inventory, source_root, run_root)

    missing = [
        path
        for path in _required_command_files(profile, platform.system())
        if not (source_root / path).is_file()
    ]
    if missing:
        raise CleanRoomError(
            "rehearsal command files are absent from candidate: " + ", ".join(missing),
            EXIT_EXECUTION,
        )

    runtime_root = run_root / "runtime"
    environment = _runtime_environment(runtime_root)
    environment.pop("SKIP_DOCTOR", None)
    for name in (
        "DSSC_VALIDATION_PROFILE",
        "DSSC_SOURCE_COMMIT",
        "DSSC_SOURCE_DIRTY",
    ):
        environment.pop(name, None)
    rehearsal_commit: str | None = None
    command_results: list[dict[str, Any]] = []
    command_failed = False
    cleanup_issues: list[str] = []
    cold_start: dict[str, Any] | None = None
    source_baseline: frozenset[str] | None = None
    candidate_paths = frozenset(item.path for item in inventory.files)
    quarantine_root, quarantine_identity = _cleanup_prepare_quarantine(run_root)
    cleanup_evidence: dict[str, Any] = {
        "ephemeral_venv": {"status": "NOT_RUN"},
        "ephemeral_git": {"status": "NOT_RUN"},
        "ephemeral_runtime": {"status": "NOT_RUN"},
        "generated_python_cache": {"status": "NOT_RUN"},
        "quarantine": {"status": "ACTIVE"},
    }
    try:
        rehearsal_commit = _initialize_rehearsal_git(
            source_root, environment, inventory
        )
        plan = _command_plan(source_root, profile)
        cold_start = _cold_start_contract(
            plan=plan,
            source_root=source_root,
            system=platform.system(),
            observe_filesystem=True,
        )
        source_baseline = _source_path_baseline(source_root, run_root)
        command_results, command_failed = _run_commands(
            plan,
            source_root,
            evidence_dir,
            run_root,
            environment,
            timeout_seconds,
        )
    finally:
        cleanup_halted = False

        def record_cleanup_failure(key: str, label: str, exc: BaseException) -> None:
            nonlocal cleanup_halted
            cleanup_evidence[key] = {
                "status": "ERROR",
                "error_type": type(exc).__name__,
            }
            cleanup_issues.append(f"failed to remove {label}: {type(exc).__name__}")
            cleanup_halted = True

        try:
            cleanup_evidence["ephemeral_venv"] = _safe_remove_runtime(
                source_root / ".venv",
                run_root,
                quarantine_root,
                quarantine_identity,
            )
        except (OSError, CleanRoomError) as exc:
            record_cleanup_failure("ephemeral_venv", "ephemeral .venv", exc)

        if not cleanup_halted:
            try:
                cleanup_evidence["ephemeral_git"] = _safe_remove_ephemeral_git(
                    source_root / ".git",
                    source_root,
                    run_root,
                    quarantine_root,
                    quarantine_identity,
                )
            except (OSError, CleanRoomError) as exc:
                record_cleanup_failure("ephemeral_git", "ephemeral .git", exc)
        else:
            cleanup_evidence["ephemeral_git"] = {
                "status": "NOT_RUN",
                "reason": "an earlier cleanup step failed closed",
            }

        if not cleanup_halted:
            try:
                cleanup_evidence["ephemeral_runtime"] = _safe_remove_runtime(
                    runtime_root,
                    run_root,
                    quarantine_root,
                    quarantine_identity,
                )
            except (OSError, CleanRoomError) as exc:
                record_cleanup_failure(
                    "ephemeral_runtime", "ephemeral runtime", exc
                )
        else:
            cleanup_evidence["ephemeral_runtime"] = {
                "status": "NOT_RUN",
                "reason": "an earlier cleanup step failed closed",
            }

        if not cleanup_halted and source_baseline is not None:
            try:
                cleanup_evidence[
                    "generated_python_cache"
                ] = _cleanup_generated_python_caches(
                    source_root,
                    run_root,
                    source_baseline,
                    candidate_paths,
                    quarantine_root,
                    quarantine_identity,
                )
            except (OSError, CleanRoomError) as exc:
                record_cleanup_failure(
                    "generated_python_cache", "generated Python cache", exc
                )
        elif source_baseline is None:
            cleanup_evidence["generated_python_cache"] = {
                "status": "NOT_RUN",
                "reason": "command-stage source baseline was not established",
            }
        else:
            cleanup_evidence["generated_python_cache"] = {
                "status": "NOT_RUN",
                "reason": "an earlier cleanup step failed closed",
            }

        if not cleanup_halted:
            try:
                cleanup_evidence["quarantine"] = _cleanup_finish_quarantine(
                    quarantine_root, quarantine_identity, run_root
                )
            except (OSError, CleanRoomError) as exc:
                record_cleanup_failure(
                    "quarantine", "cleanup quarantine", exc
                )
        else:
            cleanup_evidence["quarantine"] = {
                "status": "RETAINED",
                "reason": "a cleanup step failed closed",
            }

    output_manifest, isolated_integrity_failed = _audit_isolated_output(
        source_root, inventory
    )
    output_manifest_path = evidence_dir / "output-manifest.json"
    _write_json(output_manifest_path, output_manifest, run_root)
    after = _inventory(root)
    source_unchanged, source_issues = _same_candidate(inventory, after)
    if cleanup_issues:
        isolated_integrity_failed = True
    if output_manifest["output_file_count"] == 0:
        isolated_integrity_failed = True
        output_manifest["issues"].append(
            {"path": "build/", "issue": "rehearsal produced zero output files"}
        )
        output_manifest["issue_count"] = len(output_manifest["issues"])
        _write_json(output_manifest_path, output_manifest, run_root)

    reproduce_result = next(
        (item for item in command_results if item["id"] == "reproduce-host"),
        None,
    )
    if reproduce_result is None or reproduce_result.get("status") == "NOT_RUN":
        reproduce_contract: dict[str, Any] = {
            "status": "NOT_RUN",
            "reason": "the fail-closed command chain did not reach reproduce-host",
        }
    else:
        reproduce_contract = {
            "status": "EXECUTED",
            "command_id": "reproduce-host",
            "result_status": reproduce_result["status"],
            "exit_code": reproduce_result["exit_code"],
        }
    commands_value = {
        "schema": f"{SCHEMA_PREFIX}.commands.v1",
        "phase": "08",
        "activity": ACTIVITY,
        "profile": profile,
        "phase_09_git_clone_performed": False,
        "rehearsal_snapshot_git_commit": rehearsal_commit,
        "rehearsal_snapshot_note": (
            "Ephemeral local snapshot metadata supported the host Git evidence contract; "
            "it was removed after execution and is not a Phase 09 clone."
        ),
        "cold_start_contract": cold_start,
        "cleanup": cleanup_evidence,
        "reproduce_contract": reproduce_contract,
        "fixed_validation_image_track": CONTAINER_STATEMENT,
        "commands": command_results,
    }
    commands_path = evidence_dir / "commands.json"
    _write_json(commands_path, commands_value, run_root)

    integrity_failed = isolated_integrity_failed or not source_unchanged
    exit_code = (
        EXIT_INTEGRITY
        if integrity_failed
        else EXIT_EXECUTION
        if command_failed
        else EXIT_OK
    )
    program_status = "SUCCESS" if exit_code == EXIT_OK else "ERROR"
    result = {
        "schema": f"{SCHEMA_PREFIX}.rehearsal-result.v1",
        "phase": "08",
        "activity": ACTIVITY,
        "run_id": run_id,
        "mode": "rehearsal",
        "profile": profile,
        "program_status": program_status,
        "exit_code": exit_code,
        "phase_09_git_clone_performed": False,
        "phase_09_boundary": PHASE09_STATEMENT,
        "fixed_validation_image_track": CONTAINER_STATEMENT,
        "candidate_tree_sha256": inventory.tree_sha256,
        "exported_tree_sha256": exported_hash,
        "export_matches_candidate": exported_hash == inventory.tree_sha256,
        "suite_registry": {
            "contract_version": inventory.registry_contract_version,
            "sha256": inventory.registry_sha256,
        },
        "requirements_lock_sha256": inventory.lock_sha256,
        "cold_start_contract": cold_start,
        "cleanup": cleanup_evidence,
        "source_candidate_unchanged": source_unchanged,
        "source_candidate_issues": source_issues,
        "isolated_source_unchanged_outside_build": not isolated_integrity_failed,
        "cleanup_issues": cleanup_issues,
        "commands_manifest": "evidence/commands.json",
        "commands_manifest_sha256": _sha256_file(commands_path),
        "output_manifest": "evidence/output-manifest.json",
        "output_manifest_sha256": _sha256_file(output_manifest_path),
        "output_tree_sha256": output_manifest["output_tree_sha256"],
        "output_file_count": output_manifest["output_file_count"],
        "source_manifest": "evidence/source-manifest.json",
        "source_manifest_sha256": _sha256_file(source_manifest_path),
        "exclusion_manifest": "evidence/exclusion-manifest.json",
        "exclusion_manifest_sha256": _sha256_file(exclusion_manifest_path),
    }
    result_path = evidence_dir / "rehearsal-result.json"
    _write_json(result_path, result, run_root)
    index_path, index_hash = _write_evidence_index(
        run_root,
        evidence_dir,
        run_id=run_id,
        mode="rehearsal",
        profile=profile,
        candidate_tree_sha256=inventory.tree_sha256,
        output_tree_sha256=output_manifest["output_tree_sha256"],
        program_status=program_status,
    )
    print(
        f"clean-room rehearsal {program_status} profile={profile} exit_code={exit_code} "
        f"run_id={run_id} index={_relative_path(root, index_path)} "
        f"index_sha256={index_hash}"
    )
    return exit_code


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export and optionally execute a Phase 08 release-candidate clean-room "
            "rehearsal under build/clean-room/; full rehearsal runs the canonical "
            "reproduce wrapper first from an absent .venv."
        ),
        epilog=(
            "Exit codes: 0 success; 2 usage; 3 inventory/policy; 4 output boundary; "
            "5 export integrity; 6 command failure/timeout; 7 post-run integrity; "
            "8 internal error. Phase 09 clean clone is intentionally out of scope."
        ),
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=("manifest-only", "export", "rehearsal"),
        help=(
            "manifest inventory only, verified export, or cold-start reproduce plus "
            "doctor/all command rehearsal"
        ),
    )
    parser.add_argument(
        "--profile",
        choices=("host",),
        help=(
            "required for rehearsal; native host only; forbidden for "
            "manifest-only/export"
        ),
    )
    parser.add_argument(
        "--run-id",
        help=(
            "new NFC Unicode direct-child name under build/clean-room (internal spaces "
            "and non-ASCII are allowed; max 64 characters/128 UTF-8 bytes); defaults "
            "to a deterministic candidate-hash/mode/profile name and never overwrites "
            "an existing run"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="audit inventory and print a normalized plan without creating files",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
        help="per-command rehearsal timeout (60-7200; default: 1800)",
    )
    return parser


def _normalized_error(message: str, paths: Iterable[Path]) -> str:
    return _normalize_log(message, paths).strip()[:1000]


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.mode == "rehearsal" and arguments.profile is None:
        parser.error("--profile host is required with --mode rehearsal")
    if arguments.mode != "rehearsal" and arguments.profile is not None:
        parser.error("--profile is only valid with --mode rehearsal")
    if not 60 <= arguments.timeout_seconds <= 7200:
        parser.error("--timeout-seconds must be between 60 and 7200")

    root: Path | None = None
    run_root: Path | None = None
    inventory: Inventory | None = None
    try:
        root = _repository_root()
        inventory = _inventory(root)
        profile_suffix = arguments.profile or "none"
        default_id = (
            f"rc-{inventory.tree_sha256[:12]}-{arguments.mode}-{profile_suffix}"
        )
        run_id = _validate_run_id(arguments.run_id or default_id)
        base = _clean_room_base(root, create=False)
        prospective = base / run_id
        _assert_contained(prospective, base)
        if prospective.exists() or prospective.is_symlink():
            raise CleanRoomError(
                f"run directory already exists; choose a new --run-id: {run_id}",
                EXIT_BOUNDARY,
            )

        if arguments.mode == "rehearsal":
            missing = [
                path
                for path in _required_command_files(arguments.profile, platform.system())
                if path not in {item.path for item in inventory.files}
            ]
            if missing:
                raise CleanRoomError(
                    "rehearsal command files are absent from candidate: "
                    + ", ".join(missing),
                    EXIT_EXECUTION,
                )

        if arguments.dry_run:
            plan: list[list[str]] = []
            cold_start: dict[str, Any] | None = None
            if arguments.mode == "rehearsal":
                synthetic_source = prospective / "source"
                plan_specs = _command_plan(synthetic_source, arguments.profile)
                cold_start = _cold_start_contract(
                    plan=plan_specs,
                    source_root=synthetic_source,
                    system=platform.system(),
                    observe_filesystem=False,
                )
                plan = [list(item.display_argv) for item in plan_specs]
            value = {
                "schema": f"{SCHEMA_PREFIX}.dry-run.v1",
                "phase": "08",
                "activity": ACTIVITY,
                "mode": arguments.mode,
                "profile": arguments.profile,
                "run_id": run_id,
                "write_performed": False,
                "phase_09_git_clone_performed": False,
                "phase_09_boundary": PHASE09_STATEMENT,
                "fixed_validation_image_track": CONTAINER_STATEMENT,
                "candidate_file_count": len(inventory.files),
                "candidate_tree_sha256": inventory.tree_sha256,
                "tracked_discovered": inventory.tracked_count,
                "untracked_discovered": inventory.untracked_count,
                "exclusion_count": len(inventory.exclusions),
                "suite_registry_contract_version": inventory.registry_contract_version,
                "suite_registry_sha256": inventory.registry_sha256,
                "cold_start_contract": cold_start,
                "command_plan": plan,
            }
            print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
            return EXIT_OK

        run_root = prospective
        if arguments.mode in {"manifest-only", "export"}:
            return _manifest_only_or_export(
                root=root,
                inventory=inventory,
                mode=arguments.mode,
                run_id=run_id,
            )
        return _rehearsal(
            root=root,
            inventory=inventory,
            run_id=run_id,
            profile=arguments.profile,
            timeout_seconds=arguments.timeout_seconds,
        )
    except CleanRoomError as exc:
        paths = [item for item in (root, run_root) if item is not None]
        message = _normalized_error(str(exc), paths)
        if run_root is not None and inventory is not None:
            try:
                _record_failure(
                    run_root=run_root,
                    inventory=inventory,
                    mode=arguments.mode,
                    profile=arguments.profile,
                    exit_code=exc.exit_code,
                    message=message,
                )
            except Exception:
                pass
        print(f"ERROR: {message}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 - convert unexpected failures to stable status
        paths = [item for item in (root, run_root) if item is not None]
        message = _normalized_error(f"{type(exc).__name__}: {exc}", paths)
        if run_root is not None and inventory is not None:
            try:
                _record_failure(
                    run_root=run_root,
                    inventory=inventory,
                    mode=arguments.mode,
                    profile=arguments.profile,
                    exit_code=EXIT_INTERNAL,
                    message=message,
                )
            except Exception:
                pass
        print(f"ERROR: unexpected clean-room failure: {message}", file=sys.stderr)
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
