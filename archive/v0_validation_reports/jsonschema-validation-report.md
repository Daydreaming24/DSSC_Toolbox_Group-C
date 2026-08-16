# JSON Schema Validation Report

Generated: 2026-06-25T10:00:13.970028+00:00

Overall status: PASS

## Checks

### Energy Reading Record schema is valid

Status: PASS

`model/v0.3/energy-reading-record.schema.json` is a valid Draft 7 schema.

### Valid Energy Reading Record passes

Status: PASS

`model/v0.3/energy-reading-record-valid.jsonld` conforms.

### Invalid Energy Reading Record fails as expected

Status: PASS

`model/v0.3/energy-reading-record-invalid.jsonld` failed as expected. First error: 'meterId' is a required property

## Notes

- The invalid record intentionally violates required field, type/format, and unit constraints.
- JSON Schema reports the first validation error for the expected invalid example.
