# AI-Assisted But Human-Governed Semantic Modeling

## What AI Can Assist With

AI can accelerate semantic modeling work by drafting:

- initial vocabulary candidates
- standards alignment candidates
- JSON-LD contexts
- SHACL constraint skeletons
- JSON Schema and OpenAPI fragments
- SSSOM mapping rows
- competency questions
- documentation and handoff notes

In this project, AI assistance was used to generate a compact first version of the semantic governance package and validation harness.

## What AI Must Not Decide Alone

AI must not be the final authority for:

- business meaning of fields
- legal or contractual data offering obligations
- governance approval
- release status
- deprecation decisions
- claims of conformance to external standards
- production validator acceptance

These decisions require human semantic reviewers, domain reviewers, and validation evidence.

## Human Review Gates

The human governance gates are:

1. Domain review of required fields and values.
2. Semantic review of external standard alignment.
3. Validation review of SHACL, JSON Schema, OpenAPI, and SPARQL reports.
4. Cross-group review with A Group and D Group before handoff.
5. Release approval following `governance/release-policy.md`.

## Validation Gates

Validator checks are authoritative for machine-checkable claims. Required gates include:

- RDF parse
- JSON-LD expansion
- SHACL valid and invalid cases
- JSON Schema valid and invalid record cases
- OpenAPI structural validation
- SPARQL competency-question tests
- SSSOM parse and quality metrics
- governance/provenance validation

The local command is:

```bat
cmd /c make validate
```

## Risk Controls

Risk controls used in this project:

- Keep the ontology small and explainable.
- Prefer external standards before local terms.
- Require invalid examples to fail for intended reasons.
- Keep Semantic Treehouse as evidence track, not a blocker.
- Record version and provenance metadata.
- Use `dct:conformsTo` so examples identify the model version.
- Document caveats instead of hiding partial deployment issues.

## Audit Trail

The audit trail is distributed across:

- `governance/changelog.md`
- `governance/provenance.jsonld`
- `quality/model-quality-assessment.md`
- `validation/*.md`
- `evidence/semantic-treehouse-local-deployment.md`
- phase summaries `PHASE_0_SUMMARY.md` through `PHASE_6_SUMMARY.md`

Phase 7 adds the final reports, diagrams, and handoff contracts.

## How This Project Used AI Responsibly

AI acted as a semantic modeling assistant, not a governance authority. The generated artifacts were checked by local validation scripts, SPARQL competency questions, quality metrics, and governance validation. Claims about Semantic Treehouse are limited to the evidence captured: local deployment and UI smoke check succeeded, while a backend/root HEAD check timed out and remains a documented caveat.

Human reviewers should treat this package as a validated draft ready for review and handoff, not as an automatically approved production semantic standard.
