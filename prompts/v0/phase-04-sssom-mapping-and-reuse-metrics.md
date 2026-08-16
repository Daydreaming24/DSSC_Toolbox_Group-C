# Phase 4 Prompt — SSSOM Mapping and Reuse Metrics

Implement Phase 4 only.

Objective:
Create a semantic mapping table and derive reuse metrics to prove this is a standards-aligned model, not a purely local schema.

Tasks:

1. Create mappings/external-standard-alignment.sssom.tsv with SSSOM-style columns:

   * subject_id
   * subject_label
   * predicate_id
   * object_id
   * object_label
   * mapping_justification
   * confidence
   * author_id
   * mapping_date
   * comment

2. Include mappings for:
   Data Product Metadata:

   * be:DataProductMetadata -> dcat:Dataset or dcat:Resource/application-profile concept
   * dct:identifier
   * be:providerName -> dct:publisher / schema:provider / foaf:name pattern
   * be:endpointUrl -> dcat:endpointURL
   * be:format -> dct:format / dcat:mediaType
   * be:frequency -> dct:accrualPeriodicity
   * be:unit -> QUDT/UCUM unit concept
   * be:spatialCoverage -> dct:spatial
   * be:temporalStart / be:temporalEnd -> OWL-Time or XSD temporal coverage pattern

   Energy Reading Record:

   * be:EnergyReadingRecord -> sosa:Observation
   * be:buildingId -> sosa:hasFeatureOfInterest
   * be:meterId -> sosa:madeBySensor
   * be:timestamp -> sosa:resultTime
   * be:energyKWh -> sosa:hasResult / qudt:numericValue
   * be:unit -> qudt:unit
   * be:location -> dct:spatial / schema:location

3. Create scripts/quality_metrics.py to compute:

   * field coverage: required fields represented in artifacts / required fields
   * constraint strength: number of required fields and restricted values per model version
   * reuse ratio: externally aligned terms / total modeled terms
   * breaking-change risk:

     * v0.1 -> v0.2 should be classified as stricter minor change with validation impact
     * v0.2 -> v0.3 should be classified as additive extension

4. Write quality/model-quality-assessment.md with:

   * coverage
   * constraint strength
   * reuse ratio
   * breaking-change risk
   * interpretation
   * limitations

5. Update Makefile:

   * make quality runs scripts/quality_metrics.py
   * make validate includes quality or runs it after validation

Acceptance criteria:

* SSSOM table is TSV and parseable.
* quality report contains numeric metrics and interpretation.
* reuse ratio must be based on actual artifact/mapping counts.
* breaking-change risk must mention A group and D group impact.

Commands to run:

* make quality
* make validate

Stop after Phase 4.

