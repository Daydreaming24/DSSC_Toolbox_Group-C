# Building Energy Semantic Model — Model Card

## Version Scope and History

The governed release line is cumulative:

- v0.1 introduced the `be:DataProductMetadata` catalogue metadata baseline.
- v0.2 tightened metadata validation with endpoint, unit, and temporal coverage requirements.
- v0.3 retained the v0.2 metadata contract and added the Energy Reading Record payload contract, JSON Schema, context, SHACL Shape, examples, and OpenAPI fragment.
- v0.4 introduces the D-group Building Energy metadata wire profile. It keeps all v0.1–v0.3 artifacts frozen and inherits the five v0.3 Energy Reading Record artifacts with `change: none`.

The project version IRI for the current release is `https://w3id.org/dssc-demo/building-energy/v0.4`. The dataset identifier remains `building-energy-hourly-v1`; it identifies the data product and does not identify the model release.

## v0.4 Scope

v0.4 governs one metadata submission graph containing exactly one IRI-valued `dcat:Dataset`. The normative wire paths are the D-group `ex:/dct:/dcat:` paths, with `ex:` fixed to `https://example.org/dssc-energy#`. The profile covers dataset identity, title, provider, spatial coverage, accrual periodicity, unit, temporal boundaries, endpoint, format, optional description, optional license, and the Closed Shape allowed-property inventory.

The v0.3 metadata-to-v0.4 metadata change is a wire-profile breaking migration. The inherited v0.3 Energy Reading Record remains a separate, compatible record sub-contract. v0.4 does not introduce a new record payload version.

## Intended Users

- C Group: semantic model owners, migration authors, and governance maintainers.
- A Group: connector and offering implementers that emit v0.4 Dataset metadata.
- D Group: owners and reviewers of the normative SHACL contract and result mappings.
- B Group: service-offering or credential authors that reference the release identity outside the Dataset payload.
- Domain Reviewer: energy-data subject-matter reviewer.
- Release Approver: human authority that decides whether the evidence is sufficient for publication.

## Intended Use

- Implement the frozen D-group Shape without rewriting its namespace, paths, severities, or constraint components.
- Validate the four business outcomes `PASS`, `FAIL`, `INAPPLICABLE`, and `UNTESTABLE`, while keeping harness `SUCCESS`/`ERROR` separate.
- Guide an explicit v0.3-to-v0.4 metadata transformation.
- Preserve and regression-test the historical v0.1–v0.3 line and the inherited record contract.
- Produce deterministic, hash-bound evidence for semantic review and release decisions.

## Out-of-Scope Use

- Production energy-market settlement, billing, or legal certification.
- Full building-information, organization, place, sensor, or OWL-Time modeling.
- A claim that the `example.org` D-group contract namespace is a production publication namespace.
- A compatibility adapter that silently accepts both v0.3 and v0.4 metadata paths.
- A substitute for connector, ITB, CI, GitHub, or Semantic Treehouse execution evidence.

## Standards and Contract Reuse

- DCAT and DCTERMS are used directly for Dataset type, title, spatial coverage, frequency, endpoint, format, description, and license.
- SHACL supplies cardinality, datatype, pattern, enumeration, node-kind, SPARQL, severity, and Closed Shape semantics.
- JSON-LD serializes the canonical metadata example.
- PROV-O-inspired JSON-LD records agents, entities, activities, use, generation, derivation, attribution, and association.
- SOSA/SSN, QUDT/UCUM, OWL-Time, and schema.org remain documented alignments for the inherited v0.3 record and future richer profiles.

## Risks and Limitations

- The D-group `https://example.org/dssc-energy#` namespace is contractual input. Publication under an authoritative long-lived namespace requires a future approved change.
- Metadata unit remains the literal `kWh`. A QUDT or UCUM IRI profile would require new requirements and tests.
- Provider and spatial coverage are strings, and temporal coverage uses `xsd:date`; this profile intentionally avoids richer organization, place, and interval nodes.
- `dct:conformsTo` is excluded from the v0.4 Dataset payload because the normative Closed Shape does not allow it. Release identity is carried by the release manifest and provenance.
- An undeclared Dataset property produces the approved Closed Shape Warning and maps to `INAPPLICABLE` when no Violation is present.
- The metadata migration changes class, paths, format lexical value, cardinalities, HTTPS rules, blank-value handling, temporal ordering, and Closed Shape behavior. Downstream transformation is required.
- Automated evidence supports a human decision. Release approval, CI, GitHub publication, and Semantic Treehouse execution remain separately evidenced activities.

## Validation Strategy

The unified `scripts/validate.py --suite all` route performs schema and cross-record semantic checks before running governance assertions. The Phase 06 governance component consumes and hash-binds the release, baseline, requirements, v0.4 test-case, and validation-suite manifests and their schemas. It then checks:

- all seven governance/provenance files for regular-file, UTF-8, non-empty, and required-content properties;
- JSON-LD strict parsing and expansion;
- v0.4, D-source, C-derivation, v0.3 compatibility/inheritance, agent, and validation-artifact relations;
- manifest/source/artifact path and SHA-256 freshness;
- truthful, evidence-bound external states;
- negative controls and a byte-identical normalized rerun.

Machine-specific environment metadata is stored separately from the deterministic result and Markdown report.

## Maintenance Owner

The City Energy Data Space Authority is the conceptual owner. DSSC C Group maintains this research package and coordinates D-group contract verification and downstream handoff.

The named repository maintainer is 陈凌石 (Chen Lingshi; GitHub `Daydreaming24`). He carried out the migration of the v0–v0.3 material into this repository, the derivation of the v0.4 model from the frozen D-group contract, and the reproducible validation, governance and release engineering of the v0.4 package. He is also the human who accepted the P00-R14 final governance responsibilities recorded in `docs/v0.4/human-decisions.md`.

## Review Status

The v0.4 package completed automated Phase 06 validation and has confirmed Phase 09 candidate-bound CI and GitHub publication evidence. The three accepted migration ADRs retain their recorded group-level approvals. The maintainer has accepted the P00-R14 final human-governance responsibilities; item-level review records remain pending. Semantic Treehouse publication remains separately pending and cannot be inferred from local validation or repository publication.
