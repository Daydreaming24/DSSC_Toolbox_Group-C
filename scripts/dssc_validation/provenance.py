"""Hash repository Python sources actually loaded by the current process."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from types import ModuleType

from dssc_validation.hashing import sha256_file


def _module_source(module: ModuleType) -> Path | None:
    source = None
    try:
        source = inspect.getsourcefile(module)
    except (OSError, TypeError):
        source = None
    raw = source or getattr(module, "__file__", None)
    if not raw:
        return None
    try:
        return Path(raw).resolve()
    except OSError:
        return None


def collect_loaded_source_hashes(
    root: Path,
    required_relpaths: tuple[str, ...] = (),
) -> tuple[dict[str, str], list[str]]:
    """Return sorted hashes and fail-closed issues for required source files."""
    root = root.resolve()
    candidates: set[Path] = set()
    issues: list[str] = []

    for relpath in required_relpaths:
        path = (root / relpath).resolve()
        if not path.is_file():
            issues.append(f"required source missing: {relpath}")
        else:
            candidates.add(path)

    for module in tuple(sys.modules.values()):
        if not isinstance(module, ModuleType):
            continue
        path = _module_source(module)
        if path is None or path.suffix.lower() != ".py":
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if relative.parts and relative.parts[0] == "scripts":
            candidates.add(path)

    hashes: dict[str, str] = {}
    for path in sorted(candidates, key=lambda item: item.as_posix()):
        try:
            relative = path.relative_to(root).as_posix()
            hashes[relative] = sha256_file(path)
        except (OSError, ValueError) as exc:
            issues.append(f"cannot hash loaded source {path.name}: {exc}")
    return hashes, issues
