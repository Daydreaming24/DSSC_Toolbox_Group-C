# Phase 5 Prompt — Provenance and Version Governance Metadata

Implement Phase 5 only.

Objective:
Add governance documentation and machine-readable version/provenance metadata.

Tasks:

1. Create governance/model-card.md with:

   * model name
   * scope
   * intended users
   * intended use
   * out-of-scope use
   * standards reused
   * validation strategy
   * risks
   * maintenance owner
   * review status

2. Create governance/changelog.md with entries:

   * v0.1 baseline metadata
   * v0.2 stricter metadata constraints
   * v0.3 record payload schema extension

3. Create governance/namespace-policy.md:

   * base namespace
   * version IRIs
   * local term rules
   * external reuse rules
   * deprecation rules

4. Create governance/release-policy.md:

   * release criteria
   * validation gates
   * semantic versioning interpretation
   * evidence required for release
   * rollback policy

5. Create governance/deprecation-policy.md:

   * how to deprecate fields
   * replacement field documentation
   * compatibility expectations

6. Create governance/review-workflow.md:

   * proposal
   * automated checks
   * semantic reviewer
   * domain reviewer
   * approval
   * release
   * publication
   * downstream handoff

7. Create governance/provenance.jsonld with PROV-O-inspired metadata:

   * model versions as prov:Entity
   * generation activity
   * responsible agent
   * derivation relation v0.2 from v0.1, v0.3 from v0.2
   * generatedAtTime
   * validation reports as generated artifacts

8. Add a script scripts/validate_governance.py:

   * parse governance/provenance.jsonld as JSON-LD if possible
   * verify all expected governance files exist
   * write validation/governance-validation-report.md

9. Update Makefile:

   * make validate-governance
   * include governance validation in make validate

Acceptance criteria:

* Governance docs are complete enough to be included in the final report.
* provenance.jsonld is parseable.
* changelog explicitly describes v0.1/v0.2/v0.3.
* release policy uses validation gates.

Commands to run:

* make validate-governance
* make validate

Stop after Phase 5.

