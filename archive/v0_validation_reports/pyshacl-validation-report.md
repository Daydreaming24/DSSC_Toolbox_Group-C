# pySHACL Validation Report

Generated: 2026-06-25T10:00:12.809912+00:00

Overall status: PASS

## Checks

### v0.1 valid metadata conforms

Status: PASS

Data graph: `model/v0.1/data-product-valid.jsonld`
Shapes graph: `model/v0.1/data-product-metadata-shapes.ttl`
Expected: conforms
Actual conforms: True

```text
Validation Report
Conforms: True
```

### v0.2 valid metadata conforms

Status: PASS

Data graph: `model/v0.2/data-product-valid.jsonld`
Shapes graph: `model/v0.2/data-product-metadata-shapes.ttl`
Expected: conforms
Actual conforms: True

```text
Validation Report
Conforms: True
```

### v0.2 invalid metadata fails as expected

Status: PASS

Data graph: `model/v0.2/data-product-invalid.jsonld`
Shapes graph: `model/v0.2/data-product-metadata-shapes.ttl`
Expected: does not conform
Actual conforms: False

```text
Validation Report
Conforms: False
Results (3):
Constraint Violation in InConstraintComponent (http://www.w3.org/ns/shacl#InConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:in ( Literal("kWh") ) ; sh:maxCount Literal("1", datatype=xsd:integer) ; sh:message Literal("unit must be kWh in v0.2.") ; sh:minCount Literal("1", datatype=xsd:integer) ; sh:path be:unit ]
	Focus Node: <https://w3id.org/dssc-demo/building-energy/data-product/building-energy-hourly-v1-invalid>
	Value Node: Literal("MWh")
	Result Path: be:unit
	Message: unit must be kWh in v0.2.
Constraint Violation in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:datatype xsd:date ; sh:maxCount Literal("1", datatype=xsd:integer) ; sh:message Literal("temporalEnd is required and must be an xsd:date.") ; sh:minCount Literal("1", datatype=xsd:integer) ; sh:path be:temporalEnd ]
	Focus Node: <https://w3id.org/dssc-demo/building-energy/data-product/building-energy-hourly-v1-invalid>
	Result Path: be:temporalEnd
	Message: temporalEnd is required and must be an xsd:date.
Constraint Violation in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Violation
	Source Shape: [ sh:datatype xsd:string ; sh:maxCount Literal("1", datatype=xsd:integer) ; sh:message Literal("providerName is required and must be a string.") ; sh:minCount Literal("1", datatype=xsd:integer) ; sh:path be:providerName ]
	Focus Node: <https://w3id.org/dssc-demo/building-energy/data-product/building-energy-hourly-v1-invalid>
	Result Path: be:providerName
	Message: providerName is required and must be a string.
```

### v0.3 data product metadata conforms

Status: PASS

Data graph: `model/v0.3/data-product-valid.jsonld`
Shapes graph: `model/v0.3/data-product-metadata-shapes.ttl`
Expected: conforms
Actual conforms: True

```text
Validation Report
Conforms: True
```

### v0.3 energy reading record conforms

Status: PASS

Data graph: `model/v0.3/energy-reading-record-valid.jsonld`
Shapes graph: `model/v0.3/energy-reading-record-shapes.ttl`
Expected: conforms
Actual conforms: True

```text
Validation Report
Conforms: True
```

## Notes

- Invalid metadata is expected to fail because providerName is missing, unit is MWh, and temporalEnd is missing.
- Expected invalid cases count as harness success when they fail for the intended constraints.
