# Phase 9 Prompt — Final QA, Evidence Consolidation, and No-Regression Pass

Implement Phase 9 only.

Objective:
Perform a final no-regression pass and consolidate evidence into a grading-ready package.

Tasks:

1. Run:

   * make clean
   * make validate
   * make quality
   * make test-sparql
   * make check-required-files

2. Inspect all generated validation reports:

   * validation/pyshacl-validation-report.md
   * validation/jsonschema-validation-report.md
   * validation/openapi-validation-report.md
   * validation/sparql-competency-question-report.md
   * validation/governance-validation-report.md
   * validation/required-files-report.md
   * validation/path-link-report.md

3. Ensure invalid examples are reported as expected failures, not pipeline failures.

4. Ensure C_semantic_treehouse_usage.md honestly distinguishes:

   * Semantic Treehouse local deployment evidence
   * independent local validation evidence
   * unavailable/failed functions if any

5. Ensure docs/final-checklist.md has no unjustified “done” status.

6. Ensure all cross-group handoff files are clear:

   * A group can use metadata fields and JSON-LD.
   * D group can run SHACL validation.
   * B group can optionally reference model URI/provenance.

7. Create FINAL_SUMMARY.md:

   * What was built
   * How to run validation
   * What evidence proves minimum requirements
   * What evidence proves excellent/top-tier requirements
   * Known limitations
   * Suggested next steps

8. Do not add new conceptual scope in this phase unless needed to fix a gap.

Acceptance criteria:

* make validate passes.
* FINAL_SUMMARY.md exists.
* final checklist has evidence links.
* No false claims.
* Repository is ready for submission/demo.

Commands to run:

* make clean
* make validate
* make quality
* make test-sparql
* make check-required-files
* git status --short

Stop after Phase 9 and provide a concise final summary.

