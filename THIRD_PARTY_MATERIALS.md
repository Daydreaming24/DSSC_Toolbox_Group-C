# Third-Party and Externally Constrained Materials

This file summarizes materials that are not solely project-authored under a
general repository license, and records the maintainer redistribution decisions
made in Phase 09 §6.8. Machine-readable bindings live in
`C_Semantic_Treehouse/manifests/deliverables.json`.

## 1. Repository software (project-authored)

| Item | Location | License / decision |
|---|---|---|
| Project-authored code, scripts, models derived by Group C, docs, CI, evidence indexes | repository tree (except items below) | **Published without a general copyright license grant** — SPDX `NOASSERTION` — redistribution `publish-without-license-grant` — `DEC-P09-LICENSE-NONE-FINAL-V0.4` (`APPROVED`) |

There is **no** root `LICENSE` file. A prior MIT draft was withdrawn. The
maintainer has made a final-for-v0.4 decision to publish the repository without
granting a general copyright reuse license. Public availability, browsing,
downloading, or cloning does not grant permission to use, modify, or
redistribute project-authored materials. Any future license grant requires a
separate explicit decision and corresponding repository update.

## 2. Scenario data (CC-BY-4.0)

| Item | Location | License / decision |
|---|---|---|
| Original-plan scenario inputs | `inputs/original-plan/**` | **CC-BY-4.0** for that scenario data only — `DEC-SCENARIO-CC-BY-4.0` (`KNOWN_SOURCE`) |

This constraint does **not** license repository code, D-group materials, or
source ZIP archives.

## 3. D-group contract materials

| Item | Location | Decision |
|---|---|---|
| Received D Shape and change note | `inputs/d-group/v0.4/received/**` | Redistribution with the public candidate **APPROVED** — `DEC-P09-D-GROUP-REDIST-APPROVED` |
| Byte-copy / derived v0.4 Shape | `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl` | Same D-group redistribution decision |

SPDX for these paths remains `NOASSERTION` at the file level where no separate
SPDX grant was supplied by D group; publication is authorized by the maintainer
decision above and noticed here.

## 4. Source ZIP archives and historical path disclosure

| Item | Location | Decision |
|---|---|---|
| Core reproducible package ZIP and related provenance | `inputs/source-archives/**` (core package) | Redistribution with the public candidate **APPROVED** — `DEC-P09-SOURCE-ZIP-REDIST-APPROVED` |
| Task-plan ZIP and related provenance | `inputs/source-archives/**` (task plan) | Same decision |
| ZIP-internal historical absolute paths | bytes inside the approved ZIPs; allowlisted in `docs/provenance/privacy-exclusions.*` | Public disclosure risk **ACCEPTED** under the same decision |

File-level SPDX for the ZIP bytes remains `NOASSERTION` where no separate
upstream grant is recorded; the maintainer explicitly authorizes redistribution
and accepts the historical-path disclosure risk for this student publication.

## 5. Optional / non-core third-party (not required for core `all`)

| Item | Notes |
|---|---|
| Semantic Treehouse upstream under `tools/semantic-treehouse/` | Optional isolation track; not part of core `all`; only tracked pointer/docs ship with the candidate |

## 6. Decision ledger

Authoritative human decision statuses, including the final-for-v0.4 no-license
choice: `docs/v0.4/human-decisions.md`.
Release risk closure for license/redistribution: `docs/v0.4/release-readiness.md`.
