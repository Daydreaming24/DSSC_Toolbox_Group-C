# Phase 01：核心词汇与版本化语义产物

## 1. 本阶段解决的问题

Phase 01 是项目真正开始“建模”的阶段。Phase 00 只搭了目录和命令入口，Phase 01 则把 C 组任务中的语义模型要求落实为具体文件：

- Turtle ontology：定义类、属性、命名空间和外部标准关系。
- JSON-LD context：把业务字段映射到 RDF IRI。
- SHACL shapes：定义必填字段、数据类型和枚举约束。
- valid / invalid examples：提供正例和负例。
- JSON Schema 和 OpenAPI fragment：把 v0.3 的 API payload 约束连接到 mock API。

`prompts/phase-01-core-vocabulary-and-versioned-semantic-artifacts.md` 给出的目标是：

```text
Create the minimal but standards-aligned semantic model artifacts for v0.1, v0.2, and v0.3.
```

这里有两个关键词：

1. minimal：项目不是做完整能源本体，而是做能支持 DSSC demo 的最小语义契约。
2. standards-aligned：虽然模型很小，但要对齐 DCAT、DCTERMS、SOSA/SSN、QUDT/UCUM、OWL-Time 等标准。

## 2. 为什么要做三个版本

任务计划中 C 组被要求研究模型版本化。`task_plan/DSSC_Toolbox_Research_Task_Plan.md` 对 C 组版本演进的要求是：

```text
v0.1 metadata 基础字段；
v0.2 增加 unit、endpointUrl、temporal coverage 约束；
v0.3 可选扩展 record payload schema。
```

Phase 01 直接按这个要求建立三个版本：

| 版本 | 建模重点 | 项目意义 |
|---|---|---|
| v0.1 | Data Product Metadata 基础字段 | 先证明最小 metadata 模型可表达。 |
| v0.2 | 增加 endpoint、unit、temporal coverage，并强化约束 | 让 metadata 可以支撑 D 组验证和 A 组 offering。 |
| v0.3 | 增加 Energy Reading Record payload 模型 | 把语义模型从 catalogue metadata 延伸到 API 数据结构。 |

最终版本说明也写在 `C_Semantic_Treehouse/C_model_versioning_demo.md` 中：

```text
v0.1 establishes `be:DataProductMetadata` and requires baseline fields:
`datasetId`, `providerName`, `format`, `frequency`, and `spatialCoverage`.
```

```text
v0.2 adds required `endpointUrl`, `unit`, `temporalStart`, and `temporalEnd`.
It also constrains `format` to `JSON`, `frequency` to `hourly`, and `unit` to `kWh`.
```

```text
v0.3 keeps the v0.2 metadata contract and adds `be:EnergyReadingRecord`
with `buildingId`, `meterId`, `timestamp`, `energyKWh`, `unit`, and `location`.
```

## 3. 命名空间与版本 IRI

Phase 01 建立了统一命名空间：

```text
base namespace: https://w3id.org/dssc-demo/building-energy#
prefix: be
```

三个版本 IRI 是：

```text
https://w3id.org/dssc-demo/building-energy/v0.1
https://w3id.org/dssc-demo/building-energy/v0.2
https://w3id.org/dssc-demo/building-energy/v0.3
```

这套 IRI 后来被写入多个文件：

- ontology 的 `owl:versionIRI`
- JSON-LD examples 的 `conformsTo`
- governance namespace policy
- handoff 给 A/B/D 组的说明

例如 `C_Semantic_Treehouse/model/v0.3/data-product-valid.jsonld` 中明确声明：

```json
"conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.3"
```

这意味着下游工具或小组看到这个 metadata 时，可以知道它要按 v0.3 的语义模型和约束验证。

## 4. v0.1：基础 metadata 模型

v0.1 文件包括：

| 文件 | 作用 |
|---|---|
| `model/v0.1/building-energy-ontology.ttl` | 定义基础 ontology。 |
| `model/v0.1/data-product-metadata-shapes.ttl` | 定义 metadata 的 SHACL 约束。 |
| `model/v0.1/data-product-context.jsonld` | 定义 JSON-LD 字段映射。 |
| `model/v0.1/data-product-valid.jsonld` | 合法 metadata 样例。 |

v0.1 只要求五个基础字段：

- `datasetId`
- `providerName`
- `format`
- `frequency`
- `spatialCoverage`

`model/v0.1/data-product-metadata-shapes.ttl` 中可以看到这些约束。例如 `datasetId` 被映射为 `dct:identifier`，并要求出现一次、类型为字符串：

```turtle
sh:path dct:identifier ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:datatype xsd:string ;
sh:message "datasetId is required and must be a single string." ;
```

v0.1 的设计目标是“先可用”。它并不要求 endpoint、unit 和 temporal coverage，因为这些会在 v0.2 中作为更严格的 onboarding 约束加入。

## 5. v0.2：增强 metadata 约束

v0.2 在 v0.1 基础上增加了四个字段：

- `endpointUrl`
- `unit`
- `temporalStart`
- `temporalEnd`

并且把 `format`、`frequency`、`unit` 改成受控值：

- `format = JSON`
- `frequency = hourly`
- `unit = kWh`

`model/v0.2/data-product-metadata-shapes.ttl` 中，`unit` 的约束写得很直接：

```turtle
sh:path be:unit ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:in ("kWh") ;
sh:message "unit must be kWh in v0.2." ;
```

`endpointUrl` 不是普通字符串，而是 IRI：

```turtle
sh:path be:endpointUrl ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:nodeKind sh:IRI ;
sh:message "endpointUrl is required and must be an IRI." ;
```

这对 A 组很重要，因为 endpoint 是 data offering 连接真实 API 的入口；对 D 组也很重要，因为 validator 可以检查 metadata 中是否真的提供了可定位的 API 地址。

## 6. v0.2 invalid 样例的设计

Phase 01 还创建了 `model/v0.2/data-product-invalid.jsonld`，用来证明验证不是“只检查文件能不能解析”，而是真的检查业务约束。

这个 invalid 文件故意包含三个问题：

```json
{
  "datasetId": "building-energy-hourly-v1-invalid",
  "endpointUrl": "https://api.example.org/energy/buildings/hourly",
  "format": "JSON",
  "frequency": "hourly",
  "unit": "MWh",
  "spatialCoverage": "Shenzhen demo district",
  "temporalStart": "2026-05-01",
  "conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.2"
}
```

缺失和错误点是：

| 问题 | 为什么重要 |
|---|---|
| 缺少 `providerName` | 无法知道数据产品由谁发布和负责。 |
| `unit` 写成 `MWh` | 单位不一致会导致能耗分析数值含义错误。 |
| 缺少 `temporalEnd` | 数据时间覆盖范围不完整。 |

这三个错误对应 `task_plan/DSSC_Minimal_Energy_Scenario/VALIDATION_GUIDE.md` 中的教学目标：

```text
它们分别覆盖必填字段缺失、枚举值不符合、时间范围不完整。
```

## 7. v0.3：增加 API record payload 模型

v0.3 在 metadata 模型之外，增加第二层模型：Energy Reading Record。

这对应 task plan 中 C 组的要求：

```text
Energy Reading Record 字段：buildingId、meterId、timestamp、energyKWh、unit、location。
```

`model/v0.3/building-energy-ontology.ttl` 中定义：

```turtle
be:EnergyReadingRecord
    a owl:Class ;
    rdfs:subClassOf sosa:Observation ;
    rdfs:label "Energy Reading Record" ;
    rdfs:comment "One API payload record representing an energy reading for a building meter." .
```

这说明一条 API record 被建模为轻量级 `sosa:Observation`。同时，ontology 中还定义了 `be:Building` 和 `be:Meter`：

```turtle
be:Building
    a owl:Class ;
    rdfs:label "Building" ;
    rdfs:comment "A building that is the feature of interest for an energy reading." .
```

```turtle
be:Meter
    a owl:Class ;
    rdfs:subClassOf sosa:Sensor ;
    rdfs:label "Meter" ;
    rdfs:comment "A metering device that produces building energy readings." .
```

这样，v0.3 不只是定义字段名，而是把 record payload 放进“观测、传感器、被观测对象”的语义结构中。

## 8. v0.3 metadata 约束

`model/v0.3/data-product-metadata-shapes.ttl` 继承 v0.2 的 metadata 合同，要求九个字段：

```text
datasetId, providerName, endpointUrl, format, frequency, unit,
spatialCoverage, temporalStart, temporalEnd
```

其中：

- `datasetId` 是一个字符串。
- `endpointUrl` 必须是 IRI。
- `format` 必须是 `JSON`。
- `frequency` 必须是 `hourly`。
- `unit` 必须是 `kWh`。
- `temporalStart` 和 `temporalEnd` 必须是 `xsd:date`。

合法样例 `model/v0.3/data-product-valid.jsonld` 中的核心字段是：

```json
"datasetId": "building-energy-hourly-v1",
"providerName": "Energy Data Provider Ltd.",
"endpointUrl": "https://api.example.org/energy/buildings/hourly",
"format": "JSON",
"frequency": "hourly",
"unit": "kWh",
"spatialCoverage": "Shenzhen demo district",
"temporalStart": "2026-05-01",
"temporalEnd": "2026-05-02"
```

这和统一场景中的 data product 定义保持一致。

## 9. v0.3 record 约束

`model/v0.3/energy-reading-record-shapes.ttl` 要求 record 有六个字段：

```text
buildingId, meterId, timestamp, energyKWh, unit, location
```

其中 `timestamp` 是 `xsd:dateTime`，`energyKWh` 必须非负，`unit` 必须是 `kWh`，`location` 必须是 JSON-LD node：

```turtle
sh:path be:energyKWh ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:minInclusive 0 ;
sh:message "energyKWh is required and must be a non-negative numeric literal." ;
```

合法 record 样例 `model/v0.3/energy-reading-record-valid.jsonld` 使用：

```json
"buildingId": "BLD-001",
"meterId": "MTR-001",
"timestamp": "2026-05-01T00:00:00+08:00",
"energyKWh": 12.4,
"unit": "kWh",
"location": {
  "city": "Shenzhen",
  "district": "Nanshan"
}
```

这和 `task_plan/DSSC_Minimal_Energy_Scenario/data/building-energy-sample.json` 的 mock API 逻辑一致。

## 10. JSON Schema 与 OpenAPI

Phase 01 让 v0.3 不只停留在 RDF/SHACL 层，还进入 API payload 层。

`model/v0.3/energy-reading-record.schema.json` 定义一个 record object 必须包含：

```json
"required": [
  "buildingId",
  "meterId",
  "timestamp",
  "energyKWh",
  "unit",
  "location"
]
```

并且要求：

- `timestamp` 是 `date-time`。
- `energyKWh` 是 number 且 `minimum: 0`。
- `unit` 的枚举值只能是 `kWh`。
- `location` 必须包含 `city` 和 `district`。

`model/v0.3/openapi-fragment.yaml` 则把这个 record schema 放进 API：

```yaml
paths:
  /energy/buildings/hourly:
    get:
      summary: Return hourly building energy readings.
      responses:
        "200":
          description: Array of energy reading records.
```

这说明 C 组的 semantic model 不只是给 catalogue metadata 用，也能连接 API 文档和 payload validation。

## 11. 与外部标准的初步对齐

Phase 01 已在 ontology 中做了初步标准对齐：

| 本地概念 | 外部标准关系 | 文件证据 |
|---|---|---|
| `be:DataProductMetadata` | `rdfs:subClassOf dcat:Dataset` | `model/v0.3/building-energy-ontology.ttl` |
| `be:endpointUrl` | `rdfs:subPropertyOf dcat:endpointURL` | 同上 |
| `be:format` | `rdfs:subPropertyOf dct:format` | 同上 |
| `be:frequency` | `rdfs:subPropertyOf dct:accrualPeriodicity` | 同上 |
| `be:EnergyReadingRecord` | `rdfs:subClassOf sosa:Observation` | 同上 |
| `be:timestamp` | `rdfs:subPropertyOf sosa:resultTime` | 同上 |
| `be:energyKWh` | `rdfs:subPropertyOf qudt:numericValue` | 同上 |

更完整的 SSSOM 映射在 Phase 04 中加入。

## 12. 本阶段验证情况

`C_Semantic_Treehouse/PHASE_1_SUMMARY.md` 记录本阶段运行了：

```bat
cmd /c make validate-rdf
cmd /c make validate-jsonld
cmd /c make validate-jsonschema
cmd /c make validate-openapi
cmd /c make validate
```

通过项包括：

- Turtle 文件可被 `rdflib` 解析。
- JSON-LD 文件是合法 JSON。
- JSON Schema Draft 7 schema check 通过。
- valid record 通过 JSON Schema。
- invalid record 因缺少 `meterId` 按预期失败。
- OpenAPI YAML 可被 PyYAML 解析，包含 required top-level keys。

当时还没有完整 pySHACL 和 JSON-LD expansion harness，所以 full SHACL 和 JSON-LD expansion 被延后到 Phase 02。

## 13. 对后续阶段的影响

Phase 01 是后续所有阶段的基础：

- Phase 02 用这些模型文件做 RDF、JSON-LD、SHACL、JSON Schema、OpenAPI 验证。
- Phase 03 用 v0.3 ontology 和 examples 做 SPARQL competency questions。
- Phase 04 根据 v0.3 ontology 和字段集合计算 SSSOM 映射和质量指标。
- Phase 05 为这些版本补充 changelog、namespace policy、release policy 和 provenance。
- Phase 07 的报告、图和 handoff 都引用这些 model artifacts。

## 14. 研讨展示建议

介绍 Phase 01 时，可以按“模型演进”讲：

1. v0.1：先建立 metadata 的最低可用版本。
2. v0.2：加入 endpoint、unit、temporal coverage，让 metadata 可以真正被 validator 拒绝或接受。
3. v0.3：加入 API record payload，把 semantic governance 从数据产品描述扩展到数据记录结构。

建议现场打开：

- `C_Semantic_Treehouse/model/v0.3/building-energy-ontology.ttl`
- `C_Semantic_Treehouse/model/v0.3/data-product-metadata-shapes.ttl`
- `C_Semantic_Treehouse/model/v0.3/energy-reading-record.schema.json`
- `C_Semantic_Treehouse/model/v0.3/openapi-fragment.yaml`

然后强调一句：

> Phase 01 的关键不是文件数量多，而是同一个 data product 同时获得了 ontology、JSON-LD、SHACL、JSON Schema 和 OpenAPI 五种可复用表达。

