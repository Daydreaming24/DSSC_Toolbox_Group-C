# v0.1-v0.3 baseline reproduction

- profile: `container`
- program_status: `SUCCESS`
- exit_code: `0`
- manifest_sha256: `e8fb57fe2f609c48c0340cf8e3b78d2e8f81d0fe0fd3ab505468cfe315767e43`
- manifest_schema_sha256: `291cb5eae9212735b65fe5bad0bdef383d935b846f5fef07fc8f52c5fc79c6d8`
- registry_contract_version: `1.1.0`
- registry_sha256: `70e3e0655eebbdc59455b401837fd10e6371092d734b8abbef2401d7bb66d459`
- requirements_lock_sha256: `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2`

## Counts

| discovered | executed | passed | failed | skipped |
|---:|---:|---:|---:|---:|
| 33 | 33 | 33 | 0 | 0 |

## Categories

| category | discovered | executed | passed | failed | skipped |
|---|---:|---:|---:|---:|---:|
| rdf | 7 | 7 | 7 | 0 | 0 |
| jsonld | 10 | 10 | 10 | 0 | 0 |
| shacl | 5 | 5 | 5 | 0 | 0 |
| jsonschema | 2 | 2 | 2 | 0 | 0 |
| openapi | 1 | 1 | 1 | 0 | 0 |
| sparql | 8 | 8 | 8 | 0 | 0 |

## Cases

| case | category | expected business | actual business | program | assertions |
|---|---|---|---|---|---:|
| `rdf-v0-1-ontology` | rdf | PASS | PASS | SUCCESS | 3/3 |
| `rdf-v0-1-metadata-shapes` | rdf | PASS | PASS | SUCCESS | 3/3 |
| `rdf-v0-2-ontology` | rdf | PASS | PASS | SUCCESS | 3/3 |
| `rdf-v0-2-metadata-shapes` | rdf | PASS | PASS | SUCCESS | 3/3 |
| `rdf-v0-3-ontology` | rdf | PASS | PASS | SUCCESS | 3/3 |
| `rdf-v0-3-metadata-shapes` | rdf | PASS | PASS | SUCCESS | 3/3 |
| `rdf-v0-3-record-shapes` | rdf | PASS | PASS | SUCCESS | 3/3 |
| `jsonld-v0-1-metadata-context` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-1-metadata-valid` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-2-metadata-context` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-2-metadata-valid` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-2-metadata-invalid` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-3-metadata-context` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-3-metadata-valid` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-3-record-context` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-3-record-valid` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `jsonld-v0-3-record-invalid` | jsonld | PASS | PASS | SUCCESS | 5/5 |
| `shacl-v0-1-metadata-valid` | shacl | PASS | PASS | SUCCESS | 13/13 |
| `shacl-v0-2-metadata-valid` | shacl | PASS | PASS | SUCCESS | 13/13 |
| `shacl-v0-2-metadata-invalid` | shacl | FAIL | FAIL | SUCCESS | 10/10 |
| `shacl-v0-3-metadata-valid` | shacl | PASS | PASS | SUCCESS | 13/13 |
| `shacl-v0-3-record-valid` | shacl | PASS | PASS | SUCCESS | 13/13 |
| `jsonschema-v0-3-record-valid` | jsonschema | PASS | PASS | SUCCESS | 5/5 |
| `jsonschema-v0-3-record-invalid` | jsonschema | FAIL | FAIL | SUCCESS | 5/5 |
| `openapi-v0-3-fragment-valid` | openapi | PASS | PASS | SUCCESS | 5/5 |
| `sparql-cq01-dataset-id` | sparql | PASS | PASS | SUCCESS | 9/9 |
| `sparql-cq02-provider` | sparql | PASS | PASS | SUCCESS | 9/9 |
| `sparql-cq03-endpoint` | sparql | PASS | PASS | SUCCESS | 9/9 |
| `sparql-cq04-format-frequency` | sparql | PASS | PASS | SUCCESS | 9/9 |
| `sparql-cq05-unit` | sparql | PASS | PASS | SUCCESS | 9/9 |
| `sparql-cq06-coverage` | sparql | PASS | PASS | SUCCESS | 9/9 |
| `sparql-cq07-conforms-to` | sparql | PASS | PASS | SUCCESS | 9/9 |
| `sparql-cq08-record-fields` | sparql | PASS | PASS | SUCCESS | 9/9 |
