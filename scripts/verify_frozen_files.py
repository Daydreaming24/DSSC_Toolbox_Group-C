#!/usr/bin/env python3
"""Verify byte-preserved repository inputs and v0 archives."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = (
    REPOSITORY_ROOT
    / "docs"
    / "provenance"
    / "manifests"
    / "frozen-files-SHA256SUMS"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify frozen inputs and archived v0 artifacts."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="SHA256SUMS-format manifest (default: repository frozen manifest)",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    manifest = args.manifest.resolve()
    failures: list[str] = []
    checked = 0

    for line_number, raw_line in enumerate(
        manifest.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            expected, relative_name = line.split(maxsplit=1)
        except ValueError:
            failures.append(f"line {line_number}: invalid manifest record")
            continue

        candidate = (REPOSITORY_ROOT / relative_name).resolve()
        try:
            candidate.relative_to(REPOSITORY_ROOT)
        except ValueError:
            failures.append(
                f"line {line_number}: path escapes repository: {relative_name}"
            )
            continue

        if not candidate.is_file():
            failures.append(f"missing: {relative_name}")
            continue

        actual = sha256(candidate)
        checked += 1
        if actual.lower() != expected.lower():
            failures.append(
                f"hash mismatch: {relative_name} "
                f"(expected {expected.lower()}, found {actual.lower()})"
            )
        elif args.verbose:
            print(f"OK  {relative_name}")

    if failures:
        for failure in failures:
            print(f"FAIL  {failure}")
        print(f"Frozen-file verification failed: {len(failures)} error(s).")
        return 1

    print(f"Frozen-file verification passed: {checked} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
