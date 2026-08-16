# Phase 1 Prompt — Core Vocabulary and Versioned Semantic Artifacts

Implement Phase 1 only.

Objective:
Create the minimal but standards-aligned semantic model artifacts for v0.1, v0.2, and v0.3.

Tasks:

1. Create a compact namespace:

   * base namespace: [https://w3id.org/dssc-demo/building-energy#](https://w3id.org/dssc-demo/building-energy#)
   * prefix: be
   * version IRIs:

     * [https://w3id.org/dssc-demo/building-energy/v0.1](https://w3id.org/dssc-demo/building-energy/v0.1)
     * [https://w3id.org/dssc-demo/building-energy/v0.2](https://w3id.org/dssc-demo/building-energy/v0.2)
     * [https://w3id.org/dssc-demo/building-energy/v0.3](https://w3id.org/dssc-demo/building-energy/v0.3)

2. In model/v0.1 create:

   * building-energy-ontology.ttl
   * data-product-metadata-shapes.ttl
   * data-product-context.jsonld
   * data-product-valid.jsonld

v0.1 scope:

* be:DataProductMetadata class
* baseline fields:

  * datasetId -> dct:identifier
  * providerName -> be:providerName
  * format -> be:format
  * frequency -> be:frequency
  * spatialCoverage -> be:spatialCoverage
* Shape should require these fields.
* Keep unit, endpointUrl, temporalStart, temporalEnd out of v0.1 or mark them as not required.

3. In model/v0.2 create:

   * building-energy-ontology.ttl
   * data-product-metadata-shapes.ttl
   * data-product-context.jsonld
   * data-product-valid.jsonld
   * data-product-invalid.jsonld

v0.2 scope:

* Add endpointUrl, unit, temporalStart, temporalEnd.
* SHACL constraints:

  * datasetId required, xsd:string, max 1
  * providerName required, xsd:string
  * endpointUrl required, IRI
  * format required, allowed "JSON"
  * frequency required, allowed "hourly"
  * unit required, allowed "kWh"
  * spatialCoverage required, xsd:string
  * temporalStart required, xsd:date
  * temporalEnd required, xsd:date
* Invalid example must fail because:

  * missing providerName
  * unit is MWh instead of kWh
  * missing temporalEnd

4. In model/v0.3 create:

   * building-energy-ontology.ttl
   * data-product-metadata-shapes.ttl
   * energy-reading-record-shapes.ttl
   * data-product-context.jsonld
   * energy-reading-record-context.jsonld
   * data-product-valid.jsonld
   * energy-reading-record-valid.jsonld
   * energy-reading-record-invalid.jsonld
   * energy-reading-record.schema.json
   * openapi-fragment.yaml

v0.3 scope:

* Include v0.2 metadata.
* Add be:EnergyReadingRecord class.
* Fields:

  * buildingId
  * meterId
  * timestamp
  * energyKWh
  * unit
  * location
* Align record semantics to SOSA/SSN, QUDT/UCUM, DCTERMS, and XSD dateTime where practical.
* JSON Schema must validate API record payload.
* OpenAPI fragment must describe GET /energy/buildings/hourly returning an array of EnergyReadingRecord.

5. Add minimal comments/rdfs:label/rdfs:comment to every local class and property.

6. Keep files human-readable. Do not generate massive boilerplate.

Acceptance criteria:

* All Turtle files parse syntactically.
* JSON-LD files are valid JSON.
* JSON Schema is valid JSON.
* OpenAPI YAML is valid YAML.
* The version evolution is clear from file contents.

Commands to run if tools exist:

* make validate-rdf
* make validate-jsonld
* make validate-jsonschema
* make validate-openapi

If tools are not installed yet, document that in the phase summary and do not fake validation.

Stop after Phase 1.

