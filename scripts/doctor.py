#!/usr/bin/env python3
"""DSSC environment doctor entrypoint.

Requires an explicit --profile host|container. Wrappers and the container image
must pass profile explicitly (or set DSSC_VALIDATION_PROFILE=container inside
the fixed image). Profile is never inferred from missing Docker CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dssc_validation.doctor_core import doctor_main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(doctor_main())
