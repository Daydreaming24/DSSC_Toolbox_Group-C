# Model Quality Assessment

## Coverage

- Required fields represented in v0.3 shapes: 15/15 (100.00%)
- Missing required fields: none

## Constraint Strength

| Version | Required field constraints | Restricted value/type/node constraints | Interpretation |
|---|---:|---:|---|
| v0.1 metadata | 5 | 5 | Baseline metadata requirements only. |
| v0.2 metadata | 9 | 9 | Stricter onboarding validation for endpoint, unit, and temporal coverage. |
| v0.3 metadata | 9 | 9 | Same metadata contract as v0.2. |
| v0.3 record | 6 | 6 | Payload-level constraints for Energy Reading Record. |

## Reuse Ratio

- Local modeled terms in v0.3 ontology: 19
- Local modeled terms aligned in SSSOM: 15
- Reuse ratio: 15/19 (78.95%)
- SSSOM mapping rows: 23

The reuse ratio is computed from actual v0.3 ontology local terms and the unique local `be:*` subjects in `mappings/external-standard-alignment.sssom.tsv`.

## Breaking-Change Risk

### v0.1 -> v0.2

Classification: stricter minor change with validation impact.

- Added required `endpointUrl`, `unit`, `temporalStart`, and `temporalEnd` constraints.
- A Group impact: data offering metadata must include endpoint, unit, and temporal coverage before publication.
- D Group impact: validator shapes reject incomplete v0.1-style metadata under v0.2 rules.

### v0.2 -> v0.3

Classification: additive extension.

- Metadata constraints remain compatible with v0.2.
- Energy Reading Record payload model, SHACL shape, JSON Schema, and OpenAPI fragment are added.
- A Group impact: connector/API documentation can reference the record schema.
- D Group impact: payload validation can be added as an optional second validation layer without breaking metadata validation.

## Interpretation

The model is small but standards-aligned. Metadata fields are validated for onboarding, record fields are represented as a payload profile, and local terms are mapped to DCAT/DCTERMS, SOSA/SSN, QUDT/UCUM, OWL-Time, and schema.org patterns.

## Limitations

- Provider, location, and temporal coverage are still lightweight literals/objects rather than full organization, place, or OWL-Time interval nodes.
- Unit is validated as the literal `kWh`; richer profiles should use QUDT or UCUM identifiers directly.
- Reuse ratio measures mapping coverage, not full semantic equivalence.
- Constraint strength is a count-based indicator; it does not assess business adequacy of each constraint.
