# Phase 3 Prompt — SPARQL Competency Questions and Semantic Tests

Implement Phase 3 only.

Objective:
Add competency-question tests that prove the semantic model can answer meaningful data space governance questions.

Tasks:

1. Create tests/sparql/competency-questions.md with at least 8 competency questions:

   * CQ1: What is the dataset identifier?
   * CQ2: Who is the provider?
   * CQ3: What endpoint URL exposes the data product?
   * CQ4: What format and frequency does the data product use?
   * CQ5: What unit is required by the model?
   * CQ6: What spatial and temporal coverage does the metadata declare?
   * CQ7: Which model version does the metadata conform to?
   * CQ8: What fields define an Energy Reading Record?

2. Create SPARQL queries under tests/sparql/queries/:

   * cq01-dataset-id.rq
   * cq02-provider.rq
   * cq03-endpoint.rq
   * cq04-format-frequency.rq
   * cq05-unit.rq
   * cq06-coverage.rq
   * cq07-conforms-to.rq
   * cq08-record-fields.rq

3. Create expected result files under tests/sparql/expected/.

4. Create scripts/run_sparql_tests.py:

   * Load relevant ontology and examples into an RDF graph.
   * Run each query.
   * Compare results to expected results.
   * Write validation/sparql-competency-question-report.md.

5. Update Makefile:

   * make test-sparql runs scripts/run_sparql_tests.py
   * make validate includes make test-sparql

6. Add a short note in C_semantic_model_design.md explaining competency questions as model quality evidence.

Acceptance criteria:

* make test-sparql passes.
* Report lists every CQ with pass/fail status.
* At least one CQ must check conformance/model version.
* The queries should be simple and explainable.

Commands to run:

* make test-sparql
* make validate

Stop after Phase 3.

