# Phase 7 Prompt — Reports, Diagrams, and Handoff Contracts

Implement Phase 7 only.

Objective:
Write the required C Group reports and cross-group handoff contracts using the generated artifacts.

Tasks:

1. Create diagrams/metadata-record-model.mmd:

   * Provider publishes Data Product Metadata
   * Metadata conforms to semantic model version
   * Metadata validated by SHACL
   * Metadata references DataService endpoint
   * API returns Energy Reading Record
   * Record relates to Building and Meter
   * A group uses metadata for offering
   * D group validates metadata

2. Create diagrams/semantic-governance-flow.mmd:

   * propose model change
   * review
   * version release
   * export artifacts
   * validate
   * publish/handoff
   * monitor/deprecate

3. Write C_semantic_model_design.md:
   Required sections:

   * Scope and purpose
   * DSSC architecture position
   * Reuse-first design principle
   * Namespace policy
   * Conceptual model
   * Data Product Metadata model
   * Energy Reading Record model
   * Alignment to DCAT/DCAT-AP, SOSA/SSN, QUDT/UCUM, OWL-Time
   * SHACL constraint strategy
   * JSON-LD serialization strategy
   * OpenAPI / JSON Schema relationship
   * Competency questions
   * Model quality summary
   * Limitations
   * Future extensions

4. Write C_semantic_treehouse_usage.md:
   Required sections:

   * Tool positioning
   * Local deployment path
   * Docker evidence
   * UI/API functionality to confirm
   * Message model workflow
   * Export workflow
   * Validator workflow
   * Issues encountered
   * Independent validation fallback
   * Assessment: strengths, weaknesses, deployment risks

5. Write C_model_versioning_demo.md:
   Required sections:

   * Versioning policy
   * v0.1 baseline
   * v0.2 stricter metadata constraints
   * v0.3 record payload extension
   * Compatibility matrix
   * Changelog
   * Deprecation policy
   * Impact on A group
   * Impact on D group
   * Evidence files

6. Write C_export_for_validation.md:
   Required sections:

   * Exported artifacts
   * SHACL shapes summary
   * JSON-LD context summary
   * JSON Schema / OpenAPI summary
   * Valid examples
   * Invalid examples
   * Expected validation results
   * Comparison with existing building-energy-shapes.ttl if available
   * Validator options: Semantic Treehouse, SEMIC Validator, pySHACL
   * Handoff checklist for D group

7. Create handoff/handoff-to-A-offering-metadata.md:

   * required metadata fields
   * JSON-LD example
   * dct:conformsTo model version URI
   * endpoint/DataService recommendation
   * what A group should include in data offering

8. Create handoff/handoff-to-D-shacl-validation.md:

   * files D group receives
   * commands to validate
   * expected valid/invalid results
   * explanation of invalid case
   * how to include this in ITB/SEMIC validation story

9. Create docs/ai-assisted-human-governed-semantic-modeling.md:

   * what AI can assist with
   * what AI must not decide alone
   * human review gates
   * validation gates
   * risk controls
   * audit trail
   * how this project used AI responsibly as a semantic modeling assistant

Acceptance criteria:

* All required report files exist and refer to concrete artifacts.
* Diagrams are valid Mermaid syntax.
* Handoff docs are actionable.
* No report claims Semantic Treehouse success unless evidence exists.
* The AI-assisted chapter clearly states human governance and validator checks are authoritative.

Commands to run:

* make validate
* find . -maxdepth 3 -type f | sort

Stop after Phase 7.

