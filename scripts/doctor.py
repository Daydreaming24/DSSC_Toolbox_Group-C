#!/usr/bin/env python3
"""DSSC environment doctor entrypoint.

Requires an explicit --profile host|host-no-docker|container. Wrappers and the
container image must pass profile explicitly (or set
DSSC_VALIDATION_PROFILE=container inside the fixed image). Profile is never
inferred from missing Docker CLI.

`host` is the full host profile and requires Git plus Docker client, server,
Compose and a reachable daemon. `host-no-docker` keeps every host gate,
including the repository `.venv` isolation and Git, but declares the Docker
capability gates out of scope; it is for native validation runners that never
execute the container track, which is certified separately by the `container`
profile. `container` is selected only by the fixed image entrypoint.
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
