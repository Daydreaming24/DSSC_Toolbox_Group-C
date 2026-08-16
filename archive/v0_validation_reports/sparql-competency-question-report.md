# SPARQL Competency Question Report

Generated: 2026-06-25T10:00:15.892137+00:00

Overall status: PASS

## Checks

### cq01-dataset-id

Status: PASS

Query: `tests/sparql/queries/cq01-dataset-id.rq`
Expected: `tests/sparql/expected/cq01-dataset-id.tsv`

Expected TSV:
```text
datasetId
building-energy-hourly-v1
```

Actual TSV:
```text
datasetId
building-energy-hourly-v1
```

### cq02-provider

Status: PASS

Query: `tests/sparql/queries/cq02-provider.rq`
Expected: `tests/sparql/expected/cq02-provider.tsv`

Expected TSV:
```text
providerName
Energy Data Provider Ltd.
```

Actual TSV:
```text
providerName
Energy Data Provider Ltd.
```

### cq03-endpoint

Status: PASS

Query: `tests/sparql/queries/cq03-endpoint.rq`
Expected: `tests/sparql/expected/cq03-endpoint.tsv`

Expected TSV:
```text
endpointUrl
https://api.example.org/energy/buildings/hourly
```

Actual TSV:
```text
endpointUrl
https://api.example.org/energy/buildings/hourly
```

### cq04-format-frequency

Status: PASS

Query: `tests/sparql/queries/cq04-format-frequency.rq`
Expected: `tests/sparql/expected/cq04-format-frequency.tsv`

Expected TSV:
```text
format	frequency
JSON	hourly
```

Actual TSV:
```text
format	frequency
JSON	hourly
```

### cq05-unit

Status: PASS

Query: `tests/sparql/queries/cq05-unit.rq`
Expected: `tests/sparql/expected/cq05-unit.tsv`

Expected TSV:
```text
unit
kWh
```

Actual TSV:
```text
unit
kWh
```

### cq06-coverage

Status: PASS

Query: `tests/sparql/queries/cq06-coverage.rq`
Expected: `tests/sparql/expected/cq06-coverage.tsv`

Expected TSV:
```text
spatialCoverage	temporalStart	temporalEnd
Shenzhen demo district	2026-05-01	2026-05-02
```

Actual TSV:
```text
spatialCoverage	temporalStart	temporalEnd
Shenzhen demo district	2026-05-01	2026-05-02
```

### cq07-conforms-to

Status: PASS

Query: `tests/sparql/queries/cq07-conforms-to.rq`
Expected: `tests/sparql/expected/cq07-conforms-to.tsv`

Expected TSV:
```text
modelVersion
https://w3id.org/dssc-demo/building-energy/v0.3
```

Actual TSV:
```text
modelVersion
https://w3id.org/dssc-demo/building-energy/v0.3
```

### cq08-record-fields

Status: PASS

Query: `tests/sparql/queries/cq08-record-fields.rq`
Expected: `tests/sparql/expected/cq08-record-fields.tsv`

Expected TSV:
```text
field	label
https://w3id.org/dssc-demo/building-energy#buildingId	building ID
https://w3id.org/dssc-demo/building-energy#energyKWh	energy kWh
https://w3id.org/dssc-demo/building-energy#location	location
https://w3id.org/dssc-demo/building-energy#meterId	meter ID
https://w3id.org/dssc-demo/building-energy#timestamp	timestamp
https://w3id.org/dssc-demo/building-energy#unit	unit
```

Actual TSV:
```text
field	label
https://w3id.org/dssc-demo/building-energy#buildingId	building ID
https://w3id.org/dssc-demo/building-energy#energyKWh	energy kWh
https://w3id.org/dssc-demo/building-energy#location	location
https://w3id.org/dssc-demo/building-energy#meterId	meter ID
https://w3id.org/dssc-demo/building-energy#timestamp	timestamp
https://w3id.org/dssc-demo/building-energy#unit	unit
```

## Notes

- The test graph loads v0.3 ontology, v0.3 valid data product metadata, and v0.3 valid Energy Reading Record.
- CQ7 checks the model version binding through dct:conformsTo.
