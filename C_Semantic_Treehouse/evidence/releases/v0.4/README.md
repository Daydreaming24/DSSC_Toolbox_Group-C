# v0.4 Release Evidence

This directory holds **stable, tracked** release evidence for the
v0.4 GitHub candidate. Historical phase packages remain under
`baseline/` and `model/`. Final core aggregation is in
`core-results.json` / `core-report.md`.

## Stable tracked contents

| Path | Role |
|---|---|
| `core-results.json` | Aggregated suite `all` gate results and contract bindings |
| `core-report.md` | Deterministic human-readable rendering of `core-results.json` |
| `evidence-index.json` | Index of stable evidence paths and roles |
| `baseline/**` | Phase 02 audited baseline host/container evidence |
| `model/**` | Phase 04 audited model/release-manifest evidence |
| `README.md` | This file |

### Core gate snapshot (stable)

- validation-suites `contract_version`: `1.6.0`
- validation-suites manifest SHA-256: `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`
- suite `all` counts: 17/17/17/0/0 (discovered/executed/passed/failed/skipped)
- host result content SHA-256: `5a1504a1bfb00d4fde676d101298a6d4db5afc4f143332a664ef569629edd34f`
- container result content SHA-256: `fa72bc651c705b74f3984ff03912118d247b77d6d810fe0ce461628559bef28c`
- both platforms: **SUCCESS**

Raw environment inventories, Docker build logs, Phase 09 checker
self-results, and full suite result JSON remain under ignored
`build/**` directories. Only content hashes of the formal host and
container suite results are recorded as stable fingerprints.

## Dynamic facts (verify after push; not written here)

The following are **out of scope** for this tracked directory until
Phase 09 §6.10 / §6.11 complete on an already-committed candidate:

1. **Candidate commit SHA** for the publication commit itself.
2. **GitHub Actions** `validate.yml` run ID / URL and the three-job
   (Ubuntu / Windows / Docker) conclusion for that exact SHA.
3. **Remote clean clone** resolved SHA and one-command reproduce
   outcome from the GitHub canonical URL.

Those dynamic facts must not be embedded in the candidate commit
that they describe (no self-reference). After push + CI + remote
clone succeed, a later record-only commit may document them in
`docs/v0.4/STATUS.md` / `publication-record.md`.

## Safety and freshness

Any content prepared for publication must pass
`scripts/check_publication_safety.py` and
`scripts/check_evidence_freshness.py`. Those checker results are
ignored runtime evidence under `build/phase-09/**`, not tracked
release evidence.
