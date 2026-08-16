# Master Prompt for Codex

You are working in a local repository for DSSC C Group: Semantic Treehouse / Semantic Model Governance.

Goal:
Build a top-tier, reproducible, engineering-rigorous Semantic Governance Package for the Building Energy Consumption Data Product. The result must satisfy the minimum C Group requirements and exceed them with semantic mappings, validation harness, CI, SPARQL competency questions, provenance/version governance, Semantic Treehouse local deployment evidence, independent validation, model quality metrics, and a written section on AI-assisted but human-governed semantic modeling.

Core scenario:

* Data Product: Building Energy Consumption Dataset API
* Dataset ID: building-energy-hourly-v1
* Provider: Energy Data Provider Ltd.
* Consumer: City Analytics Lab
* Data Space Authority: City Energy Data Space Authority
* Format: JSON
* Frequency: hourly
* Unit: kWh
* Endpoint: [https://api.example.org/energy/buildings/hourly](https://api.example.org/energy/buildings/hourly)
* Spatial Coverage: Shenzhen demo district
* Temporal Coverage: 2026-05-01 to 2026-05-02

Mandatory semantic models:

1. Data Product Metadata
   Fields:

   * datasetId
   * providerName
   * endpointUrl
   * format
   * frequency
   * unit
   * spatialCoverage
   * temporalStart
   * temporalEnd

2. Energy Reading Record
   Fields:

   * buildingId
   * meterId
   * timestamp
   * energyKWh
   * unit
   * location

Versioning:

* v0.1: metadata baseline fields
* v0.2: add unit, endpointUrl, temporal coverage constraints
* v0.3: optional record payload schema extension

Required deliverables:

* README.md
* C_semantic_model_design.md
* C_semantic_treehouse_usage.md
* C_model_versioning_demo.md
* C_export_for_validation.md
* diagrams/metadata-record-model.mmd
* diagrams/semantic-governance-flow.mmd
* model/v0.1, model/v0.2, model/v0.3 artifacts
* mappings/external-standard-alignment.sssom.tsv
* governance/model-card.md
* governance/changelog.md
* governance/namespace-policy.md
* governance/release-policy.md
* governance/deprecation-policy.md
* governance/review-workflow.md
* validation/ reports
* handoff/handoff-to-A-offering-metadata.md
* handoff/handoff-to-D-shacl-validation.md
* quality/model-quality-assessment.md
* evidence/semantic-treehouse-local-deployment.md
* evidence/independent-local-validation.md
* docs/ai-assisted-human-governed-semantic-modeling.md

Engineering requirements:

* Prefer reproducibility over manual steps.
* Provide a Makefile.
* Provide a Docker-based validation harness where practical.
* Provide scripts under scripts/.
* Provide CI workflow under .github/workflows/validate.yml.
* Every artifact must be checked by at least one automated command where possible.
* Do not silently ignore failures. Capture failures in validation reports and evidence files.
* Semantic Treehouse local deployment is a parallel evidence track, not a blocker for the core semantic model package.
* Independent local validation must work even if Semantic Treehouse deployment fails.
* Keep the vocabulary small and standards-aligned. Do not over-engineer a large ontology.

Standards alignment:

* DCAT / DCAT-AP for dataset/data service/catalog metadata
* DCTERMS for identifiers, publisher, format, spatial/temporal coverage where appropriate
* SOSA/SSN for observation/reading semantics
* QUDT or UCUM for units
* OWL-Time or XSD dates/timestamps for temporal coverage
* SHACL for RDF validation
* JSON-LD context for JSON-LD serialization
* JSON Schema and OpenAPI fragment for record payload / API integration
* SSSOM for mapping local terms to external standards
* PROV-O-inspired metadata for provenance/version governance

Operating mode:
For each phase:

1. Inspect current repository state.
2. State the intended changes.
3. Implement the smallest complete set of files for that phase.
4. Run validation commands.
5. Write a phase summary with:

   * files created/modified
   * commands run
   * pass/fail status
   * remaining risks
6. Do not proceed to the next phase unless the phase acceptance criteria are met or a documented blocker exists.

Do not:

* Do not rely on an unavailable hosted Semantic Treehouse instance.
* Do not make the Semantic Treehouse deployment a hard dependency for validation.
* Do not invent screenshots; create placeholder instructions only if screenshots must be captured manually.
* Do not create huge ontologies. Keep the model minimal, explicit, and explainable.
* Do not leave generated artifacts without validation.
* Do not delete user-provided files.
* Do not use absolute Windows paths inside portable scripts except in documentation examples.

Final quality bar:
The repository must demonstrate:

* two semantic models
* v0.1/v0.2/v0.3
* SHACL or equivalent validator artifacts
* Semantic Treehouse usage/deployment record
* relationship diagram
* alignment to DCAT/DCAT-AP, SOSA/SSN, QUDT/UCUM, OWL-Time
* JSON-LD context, SHACL, JSON Schema, OpenAPI fragment
* valid/invalid validation reports
* A/D handoff contracts
* changelog, namespace policy, release policy
* SSSOM table
* CI validation pipeline
* SPARQL competency questions
* provenance/version governance metadata
* Semantic Treehouse + independent local validation dual-path evidence
* model quality assessment: coverage, constraint strength, reuse ratio, breaking-change risk
* AI-assisted but human-governed semantic modeling chapter

