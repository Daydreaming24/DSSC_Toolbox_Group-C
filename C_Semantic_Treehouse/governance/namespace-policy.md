# Namespace Policy

## Historical Project Namespace

The stable project vocabulary namespace for v0.1–v0.3 is:

```text
https://w3id.org/dssc-demo/building-energy#
```

Its preferred prefix is `be:`. Released historical terms remain available for traceability and baseline regression. The inherited v0.3 Energy Reading Record continues to use these exact `be:` IRIs.

Project release identities use the same historical version sequence:

- `https://w3id.org/dssc-demo/building-energy/v0.1`
- `https://w3id.org/dssc-demo/building-energy/v0.2`
- `https://w3id.org/dssc-demo/building-energy/v0.3`
- `https://w3id.org/dssc-demo/building-energy/v0.4`

These IRIs identify releases. They do not rewrite payload vocabulary.

## v0.4 Contract Namespace

The normative v0.4 metadata Shape fixes:

```text
ex:   https://example.org/dssc-energy#
dcat: http://www.w3.org/ns/dcat#
dct:  http://purl.org/dc/terms/
```

The v0.4 metadata target is `dcat:Dataset`. Local wire properties such as `ex:datasetId`, `ex:providerName`, `ex:unit`, `ex:temporalStart`, and `ex:temporalEnd` retain the D-group `ex:` namespace. Standard DCAT and DCTERMS properties are reused directly.

`https://example.org/dssc-energy#` is a contract namespace received from D Group. Its use here records and executes that contract. A future production namespace decision requires an explicit versioned migration and cannot silently change v0.4 bytes.

## Coexistence and Migration Boundary

Both namespaces coexist through explicit version and layer boundaries:

- v0.1–v0.3 metadata and record artifacts retain `be:`.
- v0.4 metadata uses the D-group `ex:/dcat:/dct:` wire profile.
- The inherited v0.3 Energy Reading Record retains `be:` within the v0.4 release package.
- The project v0.4 version IRI supplies release identity in the manifest and provenance.
- v0.4 Dataset payloads omit `dct:conformsTo` under ADR-001 because the normative Closed Shape excludes that property.

Migration requires a deliberate transformation from the v0.3 metadata class and paths to the v0.4 Dataset class and paths. Namespace aliases, dual-path acceptance, and implicit adapters require a new reviewed contract.

## Local Term Rules

- Historical `be:*` terms stay stable and documented after release.
- D-group `ex:*` wire terms preserve their exact received IRIs in v0.4.
- New local terms require a stated semantic gap, labels/comments where an ontology term is created, migration impact, tests, and review.
- Dataset identifier `building-energy-hourly-v1` remains independent of model namespace and version.

## External Reuse Rules

- Prefer direct DCAT/DCTERMS reuse where the normative profile already uses those properties.
- Keep direct external reuse separate from local-term mappings in SSSOM metrics.
- Record SOSA/SSN, QUDT/UCUM, OWL-Time, schema.org, and related alignments with justified mapping predicates and review status.
- Preserve the distinction between exact, close, and related mappings.

## Deprecation Rules

- Released terms and artifacts remain available in their historical version directories.
- A migration entry states the old term, new term, transformation, compatibility effect, and downstream impact.
- Removal, datatype changes, path changes, lexical-value changes, and stricter behavior are evaluated as breaking-change risks.
