# Phase 0 Prompt — Repository Audit and Project Scaffold

You are in the repository root. Implement Phase 0 only.

Objective:
Create a clean, reproducible scaffold for the C Group Semantic Governance Package. Do not create full semantic artifacts yet. Establish directories, conventions, placeholder reports, Makefile targets, and acceptance criteria.

Tasks:

1. Inspect the current directory.
2. Create this structure if missing:

C_Semantic_Treehouse/
README.md
C_semantic_model_design.md
C_semantic_treehouse_usage.md
C_model_versioning_demo.md
C_export_for_validation.md
diagrams/
model/
v0.1/
v0.2/
v0.3/
mappings/
governance/
validation/
handoff/
quality/
evidence/
docs/
scripts/
tests/
sparql/
fixtures/
.github/workflows/

3. Create a root-level or package-level Makefile with these targets, even if some are temporary stubs:

   * make help
   * make validate
   * make validate-rdf
   * make validate-shacl
   * make validate-jsonld
   * make validate-jsonschema
   * make validate-openapi
   * make test-sparql
   * make quality
   * make treehouse-up
   * make treehouse-down
   * make evidence
   * make clean

4. Create README.md with:

   * project purpose
   * C Group scope
   * minimum/excellent/top-tier checklist
   * quickstart commands
   * expected final directory structure
   * rule that independent local validation must work even if Semantic Treehouse fails

5. Create docs/engineering-harness.md explaining:

   * why Docker/local validation is used
   * why Semantic Treehouse is evidence track, not blocker
   * how CI and local validation relate

6. Create evidence/README.md with instructions for collecting:

   * Docker compose logs
   * screenshots
   * Semantic Treehouse UI/API notes
   * failed deployment logs if deployment fails

7. Create validation/README.md documenting expected validation categories:

   * RDF parse
   * JSON-LD expansion
   * SHACL valid case
   * SHACL invalid case
   * JSON Schema record validation
   * OpenAPI lint
   * SPARQL competency questions

8. Add .gitignore for generated caches, logs, virtualenvs, node_modules, temporary screenshots, and local env files, but do not ignore final validation reports.

Acceptance criteria:

* tree command or equivalent shows the expected scaffold.
* make help works.
* README gives a clear project overview.
* No semantic content is deeply implemented yet.
* Phase summary is written at the end.

Commands to run:

* pwd
* find . -maxdepth 3 -type f | sort
* make help

Stop after Phase 0.

