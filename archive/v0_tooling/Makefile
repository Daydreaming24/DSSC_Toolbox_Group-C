.PHONY: help validate validate-rdf validate-shacl validate-jsonld validate-jsonschema validate-openapi test-sparql quality validate-governance check-links-and-paths check-required-files treehouse-clone treehouse-up treehouse-down treehouse-status evidence clean

PACKAGE_DIR := C_Semantic_Treehouse

help:
	@echo "DSSC C Group Semantic Governance Package"
	@echo ""
	@echo "Available targets:"
	@echo "  help                 Show this help message"
	@echo "  validate             Run all currently available validation checks"
	@echo "  validate-rdf         Validate RDF/Turtle artifacts (stub in Phase 0)"
	@echo "  validate-shacl       Validate SHACL cases (stub in Phase 0)"
	@echo "  validate-jsonld      Validate JSON-LD artifacts (stub in Phase 0)"
	@echo "  validate-jsonschema  Validate JSON Schema cases (stub in Phase 0)"
	@echo "  validate-openapi     Validate OpenAPI fragments (stub in Phase 0)"
	@echo "  test-sparql          Run SPARQL competency tests (stub in Phase 0)"
	@echo "  quality              Run model quality metrics (stub in Phase 0)"
	@echo "  validate-governance  Validate governance docs and provenance metadata"
	@echo "  check-links-and-paths Check local Markdown links and script path portability"
	@echo "  check-required-files Verify required minimum/excellent/top-tier deliverables"
	@echo "  treehouse-clone      Clone or fetch Semantic Treehouse upstream for evidence"
	@echo "  treehouse-up         Attempt Semantic Treehouse evidence deployment"
	@echo "  treehouse-down       Stop only the Treehouse compose project started by this harness"
	@echo "  treehouse-status     Capture Treehouse compose/container status"
	@echo "  evidence             Summarize evidence collection status (stub in Phase 0)"
	@echo "  clean                Remove generated caches and temporary files"

validate:
	@python $(PACKAGE_DIR)/scripts/run_all_validations.py
	@$(MAKE) test-sparql
	@$(MAKE) quality
	@$(MAKE) validate-governance
	@$(MAKE) check-links-and-paths
	@$(MAKE) check-required-files
	@$(MAKE) evidence
	@echo "Local validation harness completed."

validate-rdf:
	@python $(PACKAGE_DIR)/scripts/validate_rdf.py

validate-shacl:
	@python $(PACKAGE_DIR)/scripts/validate_shacl.py

validate-jsonld:
	@python $(PACKAGE_DIR)/scripts/validate_jsonld.py

validate-jsonschema:
	@python $(PACKAGE_DIR)/scripts/validate_jsonschema.py

validate-openapi:
	@python $(PACKAGE_DIR)/scripts/validate_openapi.py

test-sparql:
	@python $(PACKAGE_DIR)/scripts/run_sparql_tests.py

quality:
	@python $(PACKAGE_DIR)/scripts/quality_metrics.py

validate-governance:
	@python $(PACKAGE_DIR)/scripts/validate_governance.py

check-links-and-paths:
	@python $(PACKAGE_DIR)/scripts/check_links_and_paths.py

check-required-files:
	@python $(PACKAGE_DIR)/scripts/check_required_files.py

treehouse-clone:
	@sh $(PACKAGE_DIR)/scripts/treehouse_clone_or_update.sh

treehouse-up:
	@sh $(PACKAGE_DIR)/scripts/treehouse_up.sh

treehouse-down:
	@sh $(PACKAGE_DIR)/scripts/treehouse_down.sh

treehouse-status:
	@sh $(PACKAGE_DIR)/scripts/treehouse_status.sh

evidence:
	@echo "Phase 0 stub: evidence collection instructions are in $(PACKAGE_DIR)/evidence/README.md."

clean:
	@echo "Removing generated caches and temporary files."
	@find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" \) -prune -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.tmp" \) -delete
