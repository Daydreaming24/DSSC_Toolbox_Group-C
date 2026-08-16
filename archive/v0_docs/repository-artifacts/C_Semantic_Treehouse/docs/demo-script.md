# Five-Minute Demo Script

## 0:00 - 0:30 Repository Structure

Open the repository root and show:

```bat
cmd /c make help
```

Point to the main package directory `C_Semantic_Treehouse/`, the versioned `model/` folder, `validation/`, `governance/`, `mappings/`, `handoff/`, `quality/`, and `evidence/`.

## 0:30 - 1:10 Model Versions

Show the versioned artifacts:

```bat
dir C_Semantic_Treehouse\model
dir C_Semantic_Treehouse\model\v0.1
dir C_Semantic_Treehouse\model\v0.2
dir C_Semantic_Treehouse\model\v0.3
```

Explain:

- v0.1: baseline Data Product Metadata.
- v0.2: stricter metadata with endpoint, unit, and temporal coverage.
- v0.3: additive Energy Reading Record payload schema.

## 1:10 - 1:50 SHACL Validation

Run:

```bat
cmd /c make validate-shacl
```

Open `C_Semantic_Treehouse/validation/pyshacl-validation-report.md`. Highlight that valid metadata conforms and the invalid metadata fails for intended reasons.

## 1:50 - 2:20 Invalid Metadata Failure

Open:

- `C_Semantic_Treehouse/model/v0.2/data-product-invalid.jsonld`
- `C_Semantic_Treehouse/validation/pyshacl-validation-report.md`

Explain the three expected failures: missing `providerName`, `unit = MWh`, and missing `temporalEnd`.

## 2:20 - 3:00 SPARQL Competency Questions

Run:

```bat
cmd /c make test-sparql
```

Open `C_Semantic_Treehouse/validation/sparql-competency-question-report.md`. Show that the model answers dataset ID, provider, endpoint, format/frequency, unit, coverage, version conformance, and record fields.

## 3:00 - 3:40 Semantic Treehouse Evidence

Open:

- `C_Semantic_Treehouse/evidence/semantic-treehouse-local-deployment.md`
- `C_Semantic_Treehouse/evidence/treehouse-smoke-check.txt`

Explain that Semantic Treehouse is a parallel evidence track. The local UI smoke check returned `HTTP/1.1 200 OK` on `http://localhost:4200/`; the independent validation harness remains authoritative.

## 3:40 - 4:20 A/D Handoff

Open:

- `C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md`
- `C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md`

Explain that A Group receives the offering metadata fields and D Group receives the SHACL validation contract, examples, and commands.

## 4:20 - 5:00 Quality Metrics And Final Validation

Run:

```bat
cmd /c make validate
```

Open:

- `C_Semantic_Treehouse/quality/model-quality-assessment.md`
- `C_Semantic_Treehouse/docs/final-checklist.md`

Highlight 100% required field coverage, 78.95% reuse ratio, SPARQL competency questions, CI workflow, provenance metadata, and the AI-assisted human-governed modeling chapter.
