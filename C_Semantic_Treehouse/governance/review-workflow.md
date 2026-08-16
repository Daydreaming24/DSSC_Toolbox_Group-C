# Review Workflow

## Proposal and Authority

A semantic change proposal identifies the problem, authority, affected versions, fields and artifacts, compatibility classification, downstream impact, test obligations, and target release. Normative D-group input, accepted ADRs, and machine-readable manifests establish the v0.4 decision boundary.

## C-Group Semantic Review

C Group reviews:

- term and path meaning;
- version identity versus payload vocabulary;
- historical retention and migration guidance;
- external-standard reuse and SSSOM predicates;
- JSON-LD behavior, provenance, and governance consistency;
- A/B/D group impact and evidence freshness.

A named human or auditable group identity records the review outcome. Automated tools and AI agents supply evidence and cannot serve as the approval identity.

## D-Group Contract Verification

D Group verifies that the normative Shape is represented without namespace/path rewriting or constraint weakening. Verification covers named Shapes, targets, severities, paths, messages, constraint components, SPARQL behavior, Closed Shape inventory, and the four-state interpretation.

The repository checker also proves that the released v0.4 Shape is byte-identical to the received D Shape. Any discrepancy returns to the earliest affected Phase and requires a reviewed decision.

## Domain Review

The Domain Reviewer checks:

- the meaning of dataset identity, provider, spatial and temporal coverage;
- `hourly`, `kWh`, and `application/json` interpretations;
- HTTPS endpoint and license expectations;
- temporal-order and exactly-one-Dataset business rules;
- the boundary between metadata and Energy Reading Record payloads.

Domain review records the reviewer identity, date, scope, conclusion, and evidence reference only after the review occurs.

## Automated Gate

Run the fixed repository environment through:

```text
python scripts/validate.py --suite all
```

The wrapper selects the repository virtual environment or the pinned container interpreter. The registry deterministically expands the six non-`all` public suites, the composition check, and the Phase 06 SPARQL, quality, and governance checks. A missing check, schema/semantic manifest failure, stale hash, zero discovery/execution, skipped required case, failed negative control, or exception returns non-zero.

Normalized result JSON, deterministic Markdown, independent environment metadata, source hashes, and manifest/schema hashes form the local automated evidence package.

## Human Release Approval

The Release Approver reviews the complete automated evidence, C Group semantic review, D Group contract verification, Domain Reviewer outcome, known risks, license/source constraints, and downstream handoff. Approval is a distinct human decision with identity, date, scope, conclusion, and evidence references.

The accepted Phase 03 ADR decisions remain valid evidence for their stated migration scope. They do not constitute final v0.4 release approval.

## Publication and External Evidence

After explicit authorization, CI and GitHub may create externally visible evidence. Semantic Treehouse may create an optional independent validation record. Stable provenance records the evidence boundary and points to the publication record or local usage evidence; candidate-specific run, job and clone identifiers remain in the publication record. Failed or unavailable optional evidence retains its actual status.

## Current v0.4 Evidence Status

| Activity | Current status | Truth boundary |
|---|---|---|
| Phase 03 migration ADR decisions | `ACCEPTED` | Group-level decisions recorded in ADR-001, ADR-002, and ADR-003. |
| Phase 06 local automated gate | `PASS` | The unified local run completed with `SUCCESS`; the Phase 06 status record binds the final evidence. |
| C Group v0.4 semantic review | `PENDING` | No final human release review is recorded here. |
| D Group final contract review | `PENDING` | Existing ADR scope remains accepted; final release evidence review remains open. |
| Domain Reviewer review | `PENDING` | No reviewer identity or outcome has been supplied. |
| Release Approver responsibility | `ACCEPTED_LIMITATION` | Maintainer `Daydreaming24` accepted the P00-R14 final responsibility; item-level review/sign-off records remain pending. |
| CI run | `CONFIRMED` | Candidate-bound Ubuntu/Windows/Docker results are recorded in `docs/v0.4/publication-record.md`; every new candidate requires its own run. |
| GitHub repository publication | `CONFIRMED` | Ordinary push and canonical-URL remote-clone evidence are recorded in `docs/v0.4/publication-record.md`; tag and GitHub Release remain `NOT_REQUESTED`. |
| Semantic Treehouse publication | `NOT RUN` | The optional local deployment/import/export/SHACL run completed and its runtime is `PAUSED`; no external Treehouse publication is claimed. |

## Downstream Handoff

- A Group receives the v0.4 wire paths, values, fixtures, test manifest, and migration table.
- D Group receives the byte-bound Shape, requirements traceability, four-state oracle, semantic tests, and exact report assertions.
- B Group receives the release IRI, provenance boundary, and current publication status.
- Every handoff distinguishes completed local evidence from pending human or external activities.
