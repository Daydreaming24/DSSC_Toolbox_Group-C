"""Repository path resolution based on script location (not CWD)."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def scripts_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def repository_root() -> Path:
    return scripts_dir().parent


def validation_suites_path(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / "C_Semantic_Treehouse" / "manifests" / "validation-suites.json"


def validation_suites_schema_path(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return (
        base
        / "C_Semantic_Treehouse"
        / "manifests"
        / "schemas"
        / "validation-suites.schema.json"
    )


def requirements_lock_path(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / "requirements.lock"


def requirements_in_path(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / "requirements.in"


def bootstrap_lock_path(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / "requirements-bootstrap.lock"


def python_version_file(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / ".python-version"


_PHASE_ID = re.compile(r"^0[1-9]$")


def _validated_phase_id(phase: str) -> str:
    if not isinstance(phase, str) or _PHASE_ID.fullmatch(phase) is None:
        raise ValueError("validation evidence phase must be in the range 01..09")
    return phase


def phase_build_dir(phase: str, root: Path | None = None) -> Path:
    phase = _validated_phase_id(phase)
    base = root if root is not None else repository_root()
    return base / "build" / f"phase-{phase}" / "current"


def phase01_build_dir(root: Path | None = None) -> Path:
    """Compatibility path for Phase 01 doctor and recovery tooling."""
    return phase_build_dir("01", root)


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def prepare_phase_build_dir(phase: str, root: Path | None = None) -> Path:
    """Create one fixed phase output path without traversing links."""
    phase = _validated_phase_id(phase)
    base = (root if root is not None else repository_root()).resolve()
    current = base
    for name in ("build", f"phase-{phase}", "current"):
        current = current / name
        if _is_link_like(current):
            raise ValueError(f"Phase {phase} output component is a link: {name}")
        if current.exists():
            if not current.is_dir():
                raise ValueError(
                    f"Phase {phase} output component is not a directory: {name}"
                )
        else:
            current.mkdir()
    try:
        current.resolve().relative_to(base)
    except ValueError as exc:
        raise ValueError(
            f"Phase {phase} output resolves outside the repository"
        ) from exc
    return current


def prepare_phase01_build_dir(root: Path | None = None) -> Path:
    """Compatibility creator for Phase 01 doctor and recovery tooling."""
    return prepare_phase_build_dir("01", root)


def is_exact_phase_build_dir(
    path: Path, phase: str, root: Path | None = None
) -> bool:
    phase = _validated_phase_id(phase)
    base = root if root is not None else repository_root()
    expected = phase_build_dir(phase, base)
    return os.path.normcase(os.path.abspath(path)) == os.path.normcase(
        os.path.abspath(expected)
    )


def is_exact_phase01_build_dir(path: Path, root: Path | None = None) -> bool:
    """Compatibility boundary for Phase 01 recovery controls."""
    return is_exact_phase_build_dir(path, "01", root)


def phase01_negative_controls_dir(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / "build" / "phase-01" / "negative-controls"


def lock_metadata_path(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    return base / "requirements.lock.json"


def venv_python(root: Path | None = None) -> Path:
    base = root if root is not None else repository_root()
    win = base / ".venv" / "Scripts" / "python.exe"
    if win.exists():
        return win
    return base / ".venv" / "bin" / "python"


def is_repo_venv_interpreter(executable: Path, root: Path | None = None) -> bool:
    base = (root if root is not None else repository_root()).resolve()
    try:
        prefix = Path(sys.prefix).resolve()
        expected_prefix = (base / ".venv").resolve()
    except OSError:
        return False
    if prefix != expected_prefix or Path(sys.base_prefix).resolve() == prefix:
        return False
    # Windows venv executables are copies; Linux commonly uses a symlink to
    # the base binary, so sys.prefix is the authoritative environment boundary.
    return executable.name.lower() in ("python", "python.exe")
