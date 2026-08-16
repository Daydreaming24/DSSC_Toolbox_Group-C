# Model v0.3 详细解读：从 Metadata 合同扩展到 API Record Payload

## 1. v0.3 的定位

`model/v0.3` 是 Phase 01 中最完整的模型版本。它保留 v0.2 已经建立的 data product metadata 合同，并新增 API 返回数据记录的语义模型。

如果用一句话区分三个版本：

```text
v0.1: 定义最小 data product metadata
v0.2: 把 metadata 变成可验证的 onboarding contract
v0.3: 在 metadata contract 之外，增加 API record payload contract
```

所以 v0.3 的关键变化不是继续给 metadata 加字段，而是增加第二层模型：

```text
Energy Reading Record
```

也就是 API 返回的一条建筑能耗读数。

这让 C 组的语义模型从“数据产品描述”延伸到“数据产品实际返回的数据结构”。它不只回答：

```text
这个数据产品应该怎样被描述？
```

还开始回答：

```text
这个数据产品的 API 返回记录应该长什么样？
每条读数有哪些字段？
这些字段的语义是什么？
这些字段如何被 SHACL、JSON Schema 和 OpenAPI 约束？
```

这也是 v0.3 最适合在汇报中展示的地方，因为它把 ontology、JSON-LD、SHACL、JSON Schema、OpenAPI 五类 artifact 串在了一起。

## 2. v0.3 目录里为什么有十个文件

v0.3 目录下有十个文件：

```text
C_Semantic_Treehouse/model/v0.3/
  building-energy-ontology.ttl
  data-product-context.jsonld
  data-product-metadata-shapes.ttl
  data-product-valid.jsonld
  energy-reading-record-context.jsonld
  energy-reading-record-shapes.ttl
  energy-reading-record-valid.jsonld
  energy-reading-record-invalid.jsonld
  energy-reading-record.schema.json
  openapi-fragment.yaml
```

这些文件可以分成三组。

### 2.1 共同语义层

| 文件 | 作用 |
|---|---|
| `building-energy-ontology.ttl` | 定义 metadata 和 record 的共同 ontology。 |

这个 ontology 同时包含：

```text
DataProductMetadata
EnergyReadingRecord
Building
Meter
```

也就是 v0.3 开始在一个 ontology 中描述两类对象：

```text
数据产品 metadata
API 返回的一条读数 record
```

### 2.2 Metadata 层

| 文件 | 作用 |
|---|---|
| `data-product-context.jsonld` | 解释 data product metadata 的 JSON-LD 字段。 |
| `data-product-metadata-shapes.ttl` | 验证 metadata 是否符合 v0.3 合同。 |
| `data-product-valid.jsonld` | 给出一个合格的 v0.3 metadata 样例。 |

这组文件基本继承 v0.2。也就是说，v0.3 没有推翻 v0.2 的 metadata 模型，而是保留九个字段和相同的验证逻辑。

### 2.3 Record Payload 层

| 文件 | 作用 |
|---|---|
| `energy-reading-record-context.jsonld` | 解释 API record 的 JSON-LD 字段。 |
| `energy-reading-record-shapes.ttl` | 用 SHACL 验证 record 的 RDF/JSON-LD 语义结构。 |
| `energy-reading-record-valid.jsonld` | 给出一条合格的能耗读数。 |
| `energy-reading-record-invalid.jsonld` | 给出一条故意失败的能耗读数。 |
| `energy-reading-record.schema.json` | 用 JSON Schema 验证普通 API payload 的 JSON 结构。 |
| `openapi-fragment.yaml` | 描述 API endpoint 和返回的 record schema。 |

这一组是 v0.3 的新增重点。它说明 v0.3 不再只关心 catalogue metadata，也开始约束 API 返回的数据。

## 3. v0.3 相比 v0.2 新增了什么

v0.2 已经有完整 metadata 字段：

```text
datasetId
providerName
endpointUrl
format
frequency
unit
spatialCoverage
temporalStart
temporalEnd
```

v0.3 保留这些字段，并新增一套 record payload 字段：

| v0.3 新增 record 字段 | 含义 |
|---|---|
| `buildingId` | 建筑 ID。 |
| `meterId` | 仪表或传感器 ID。 |
| `timestamp` | 读数时间。 |
| `energyKWh` | 以 kWh 表示的能耗数值。 |
| `unit` | 单位，要求为 `kWh`。 |
| `location` | 读数关联的地点对象。 |

其中 `location` 继续包含：

```text
city
district
```

所以 v0.3 的建模对象从一个变成两个：

| 层次 | 建模对象 | 主要用途 |
|---|---|---|
| Metadata 层 | `DataProductMetadata` | 描述数据产品本身。 |
| Record 层 | `EnergyReadingRecord` | 描述 API 返回的一条能耗读数。 |

这个变化非常关键。它说明 C 组的模型不只是给数据目录用，还可以影响 API 文档、mock data、payload validation 和跨组交付。

## 4. `building-energy-ontology.ttl`：同时定义 metadata 和 record

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/building-energy-ontology.ttl
```

v0.3 的 ontology 是三个版本中最丰富的一个。它继承 v0.2 的 metadata vocabulary，并增加 record payload vocabulary。

### 4.1 版本声明

v0.3 ontology 开头是：

```turtle
<https://w3id.org/dssc-demo/building-energy/v0.3>
    a owl:Ontology ;
    owl:versionIRI <https://w3id.org/dssc-demo/building-energy/v0.3> ;
    owl:priorVersion <https://w3id.org/dssc-demo/building-energy/v0.2> ;
    owl:versionInfo "0.3" ;
    dct:title "Building Energy Semantic Model v0.3" ;
    dct:description "Metadata vocabulary plus an Energy Reading Record payload profile." ;
    dct:created "2026-06-25"^^xsd:date .
```

这里的版本链是：

```text
v0.1 -> v0.2 -> v0.3
```

其中：

```turtle
owl:priorVersion <https://w3id.org/dssc-demo/building-energy/v0.2>
```

说明 v0.3 是从 v0.2 演进来的。它不是重写 metadata 模型，而是在 v0.2 的基础上新增 payload 层。

### 4.2 保留 `be:DataProductMetadata`

v0.3 继续定义：

```turtle
be:DataProductMetadata
    a owl:Class ;
    rdfs:subClassOf dcat:Dataset ;
    rdfs:label "Data Product Metadata" ;
    rdfs:comment "Metadata describing a data product for catalogue discovery, connector offering creation, and SHACL validation." .
```

这和 v0.2 的定位一致：data product metadata 仍然是 DCAT `Dataset` 的一种。

所以 v0.3 对 metadata 层是兼容延续：

```text
v0.3 metadata contract = v0.2 metadata contract 的延续
```

### 4.3 新增 `be:EnergyReadingRecord`

v0.3 最重要的新增类是：

```turtle
be:EnergyReadingRecord
    a owl:Class ;
    rdfs:subClassOf sosa:Observation ;
    rdfs:label "Energy Reading Record" ;
    rdfs:comment "One API payload record representing an energy reading for a building meter." .
```

这段的含义是：

```text
EnergyReadingRecord 是一条 API payload record；
它表示某个建筑仪表产生的一次能耗读数；
语义上，它被建模为 SOSA Observation 的一种。
```

这里对齐到 `sosa:Observation` 很有意义。SOSA/SSN 是传感器、观测和采样领域的标准词汇。建筑能耗读数本质上可以看成仪表对建筑能耗的观测结果，因此把 `EnergyReadingRecord` 设为 `sosa:Observation` 的子类是合理的。

这让 record 不只是普通 JSON object，而是具有传感器观测语义。

### 4.4 新增 `be:Building` 和 `be:Meter`

v0.3 还定义：

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

这说明模型背后的语义结构是：

```text
Meter 产生读数；
Building 是读数关注的对象；
EnergyReadingRecord 是一次观测记录。
```

`be:Meter` 被设为 `sosa:Sensor` 的子类，这也和 SOSA 的观测模型对应。

### 4.5 Metadata 属性继续保留

v0.3 继续保留 v0.2 中的 metadata 属性：

```text
be:providerName
be:endpointUrl
be:format
be:frequency
be:unit
be:spatialCoverage
be:temporalStart
be:temporalEnd
```

其中：

| 属性 | 标准对齐 |
|---|---|
| `be:endpointUrl` | `rdfs:subPropertyOf dcat:endpointURL` |
| `be:format` | `rdfs:subPropertyOf dct:format` |
| `be:frequency` | `rdfs:subPropertyOf dct:accrualPeriodicity` |
| `be:spatialCoverage` | `rdfs:subPropertyOf dct:spatial` |

所以 v0.3 并没有削弱 metadata 层，而是继续保留 data offering 和 validation 所需的 metadata contract。

### 4.6 Record 属性：`buildingId` 和 `meterId`

v0.3 新增：

```turtle
be:buildingId
    a owl:DatatypeProperty ;
    rdfs:label "building ID" ;
    rdfs:comment "Identifier of the building feature of interest for the reading." ;
    rdfs:domain be:EnergyReadingRecord ;
    rdfs:range xsd:string .
```

```turtle
be:meterId
    a owl:DatatypeProperty ;
    rdfs:label "meter ID" ;
    rdfs:comment "Identifier of the meter or sensor that produced the reading." ;
    rdfs:domain be:EnergyReadingRecord ;
    rdfs:range xsd:string .
```

这两个字段说明一条读数属于哪个建筑、由哪个仪表产生。

在 valid example 中：

```json
"buildingId": "BLD-001",
"meterId": "MTR-001"
```

这让 record 可以被追溯到具体建筑和具体仪表。

### 4.7 Record 属性：`timestamp`

v0.3 定义：

```turtle
be:timestamp
    a owl:DatatypeProperty ;
    rdfs:subPropertyOf sosa:resultTime ;
    rdfs:label "timestamp" ;
    rdfs:comment "Time at which the energy reading applies." ;
    rdfs:domain be:EnergyReadingRecord ;
    rdfs:range xsd:dateTime .
```

这里有两个重点：

| 声明 | 含义 |
|---|---|
| `rdfs:subPropertyOf sosa:resultTime` | 时间字段对齐到 SOSA 的观测结果时间。 |
| `rdfs:range xsd:dateTime` | 值应该是 date-time，而不是普通日期。 |

valid example 中：

```json
"timestamp": "2026-05-01T00:00:00+08:00"
```

它精确到小时，并带有 `+08:00` 时区，符合建筑小时级用电数据的场景。

### 4.8 Record 属性：`energyKWh`

v0.3 定义：

```turtle
be:energyKWh
    a owl:DatatypeProperty ;
    rdfs:subPropertyOf qudt:numericValue ;
    rdfs:label "energy kWh" ;
    rdfs:comment "Numeric energy consumption value expressed in kilowatt-hours." ;
    rdfs:domain be:EnergyReadingRecord ;
    rdfs:range xsd:decimal .
```

这里把能耗数值对齐到：

```text
qudt:numericValue
```

QUDT 是数量、单位和维度领域的常用语义词汇。当前模型没有把 `kWh` 建成完整的 QUDT unit URI，而是把数值属性对齐到 QUDT 的 numeric value，并通过 `unit` 字段要求单位为 `kWh`。

这是一个 demo 中比较轻量的设计：

```text
energyKWh 表示数值；
unit 表示单位 token；
后续 richer profile 可以把 unit 映射到 QUDT/UCUM 的单位标识符。
```

### 4.9 Record 属性：`location`、`city`、`district`

v0.3 定义：

```turtle
be:location
    a owl:ObjectProperty ;
    rdfs:subPropertyOf dct:spatial ;
    rdfs:label "location" ;
    rdfs:comment "Place associated with an energy reading record." ;
    rdfs:domain be:EnergyReadingRecord .
```

这表示 `location` 是和读数相关的地点对象，并对齐到 `dct:spatial`。

同时定义：

```turtle
be:city
    a owl:DatatypeProperty ;
    rdfs:subPropertyOf schema:addressLocality ;
    rdfs:label "city" ;
    rdfs:comment "City value inside the lightweight API location object." ;
    rdfs:range xsd:string .
```

```turtle
be:district
    a owl:DatatypeProperty ;
    rdfs:subPropertyOf schema:containedInPlace ;
    rdfs:label "district" ;
    rdfs:comment "District value inside the lightweight API location object." ;
    rdfs:range xsd:string .
```

这里使用了 schema.org 的地点相关属性做轻量对齐。

valid example 中：

```json
"location": {
  "city": "Shenzhen",
  "district": "Nanshan"
}
```

所以 `location` 是一个嵌套对象，而不是单个字符串。

## 5. Metadata 相关文件：v0.3 继承 v0.2 合同

v0.3 仍然包含 metadata 相关文件：

```text
data-product-context.jsonld
data-product-metadata-shapes.ttl
data-product-valid.jsonld
```

这组文件基本沿用 v0.2 的 metadata 合同，只把版本声明更新为 v0.3。

### 5.1 `data-product-context.jsonld`

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/data-product-context.jsonld
```

这个 context 映射的字段和 v0.2 一致：

| JSON 字段 | RDF 属性或类型 |
|---|---|
| `DataProductMetadata` | `be:DataProductMetadata` |
| `datasetId` | `dct:identifier` |
| `providerName` | `be:providerName` |
| `endpointUrl` | `be:endpointUrl`，并且是 `@id` |
| `format` | `be:format` |
| `frequency` | `be:frequency` |
| `unit` | `be:unit` |
| `spatialCoverage` | `be:spatialCoverage` |
| `temporalStart` | `be:temporalStart`，类型为 `xsd:date` |
| `temporalEnd` | `be:temporalEnd`，类型为 `xsd:date` |
| `conformsTo` | `dct:conformsTo`，并且是 `@id` |

这说明 v0.3 metadata 仍然要求 endpoint、单位和时间覆盖。

### 5.2 `data-product-metadata-shapes.ttl`

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/data-product-metadata-shapes.ttl
```

它定义：

```turtle
be:DataProductMetadataShape-v0_3
    a sh:NodeShape ;
    sh:targetClass be:DataProductMetadata ;
    ...
```

v0.3 metadata shape 仍然要求九个字段：

```text
datasetId
providerName
endpointUrl
format
frequency
unit
spatialCoverage
temporalStart
temporalEnd
```

并继续要求：

```text
endpointUrl 必须是 IRI
format 必须是 JSON
frequency 必须是 hourly
unit 必须是 kWh
temporalStart / temporalEnd 必须是 xsd:date
```

换句话说：

```text
v0.3 没有放松 v0.2 的 metadata validation；
它只是把 validation 范围继续扩展到 record payload。
```

### 5.3 `data-product-valid.jsonld`

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/data-product-valid.jsonld
```

v0.3 的 metadata valid example 是：

```json
{
  "@context": "data-product-context.jsonld",
  "@id": "https://w3id.org/dssc-demo/building-energy/data-product/building-energy-hourly-v1",
  "@type": "DataProductMetadata",
  "datasetId": "building-energy-hourly-v1",
  "providerName": "Energy Data Provider Ltd.",
  "endpointUrl": "https://api.example.org/energy/buildings/hourly",
  "format": "JSON",
  "frequency": "hourly",
  "unit": "kWh",
  "spatialCoverage": "Shenzhen demo district",
  "temporalStart": "2026-05-01",
  "temporalEnd": "2026-05-02",
  "conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.3"
}
```

它和 v0.2 valid example 基本一致，主要区别是：

```text
conformsTo 指向 v0.3
```

这说明 metadata 现在声明自己遵循 v0.3 版本模型。

## 6. `energy-reading-record-context.jsonld`：解释 API record 字段

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/energy-reading-record-context.jsonld
```

这是 v0.3 新增的 JSON-LD context，专门用于解释 API record payload。

### 6.1 Record 类型映射

context 中：

```json
"EnergyReadingRecord": "be:EnergyReadingRecord"
```

因此 record 样例中可以写：

```json
"@type": "EnergyReadingRecord"
```

机器会理解为：

```text
@type = be:EnergyReadingRecord
```

这样 SHACL validator 才知道它应该用 `be:EnergyReadingRecordShape-v0_3` 进行检查。

### 6.2 Record 字段映射

字段映射如下：

| JSON 字段 | RDF 属性 |
|---|---|
| `buildingId` | `be:buildingId` |
| `meterId` | `be:meterId` |
| `timestamp` | `be:timestamp` |
| `energyKWh` | `be:energyKWh` |
| `unit` | `be:unit` |
| `location` | `be:location` |
| `city` | `be:city` |
| `district` | `be:district` |

### 6.3 `timestamp` 的类型

context 中：

```json
"timestamp": {
  "@id": "be:timestamp",
  "@type": "xsd:dateTime"
}
```

这表示：

```text
timestamp 应该被理解为 xsd:dateTime。
```

所以：

```json
"timestamp": "2026-05-01T00:00:00+08:00"
```

不是普通文本，而是 date-time typed literal。

### 6.4 `energyKWh` 的类型

context 中：

```json
"energyKWh": {
  "@id": "be:energyKWh",
  "@type": "xsd:decimal"
}
```

这表示能耗值应该被理解为 decimal。

同时，JSON Schema 又从普通 JSON 层要求：

```text
energyKWh 必须是 number
minimum = 0
```

这就是 v0.3 的双层约束：JSON-LD/SHACL 管语义，JSON Schema 管 API payload JSON 结构。

## 7. `energy-reading-record-shapes.ttl`：record 的 SHACL 约束

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/energy-reading-record-shapes.ttl
```

这个文件定义：

```turtle
be:EnergyReadingRecordShape-v0_3
    a sh:NodeShape ;
    sh:targetClass be:EnergyReadingRecord ;
    ...
```

意思是：

```text
所有 be:EnergyReadingRecord 实例都应该按这个 shape 验证。
```

### 7.1 `buildingId` 必填

```turtle
sh:path be:buildingId ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:datatype xsd:string ;
sh:message "buildingId is required and must be a string." ;
```

这表示：

```text
每条能耗读数必须指明建筑 ID。
```

### 7.2 `meterId` 必填

```turtle
sh:path be:meterId ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:datatype xsd:string ;
sh:message "meterId is required and must be a string." ;
```

这表示：

```text
每条读数必须说明由哪个 meter/sensor 产生。
```

invalid example 中故意缺少 `meterId`，因此应当失败。

### 7.3 `timestamp` 必须是 dateTime

```turtle
sh:path be:timestamp ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:datatype xsd:dateTime ;
sh:message "timestamp is required and must be an xsd:dateTime." ;
```

这表示：

```text
每条读数必须有一个时间戳，并且应该是 xsd:dateTime。
```

valid example 中：

```json
"timestamp": "2026-05-01T00:00:00+08:00"
```

invalid example 中：

```json
"timestamp": "not-a-date-time"
```

这个值在语义上不是合法时间。实际 validator 是否报告 format 错误，取决于使用的 JSON-LD/SHACL 或 JSON Schema format 检查配置；但从模型意图看，它显然是故意错误。

### 7.4 `energyKWh` 必须非负

```turtle
sh:path be:energyKWh ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:minInclusive 0 ;
sh:message "energyKWh is required and must be a non-negative numeric literal." ;
```

这表示：

```text
能耗值必须出现一次，并且不能是负数。
```

这里 SHACL shape 强调的是非负数值。JSON Schema 则进一步要求 `energyKWh` 必须是 JSON number。

### 7.5 `unit` 必须是 `kWh`

```turtle
sh:path be:unit ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:in ("kWh") ;
sh:message "unit must be kWh for Energy Reading Record." ;
```

这和 metadata 层的 unit 约束保持一致。

invalid example 中：

```json
"unit": "MWh"
```

这应该被拒绝，因为 v0.3 record 的单位也只能是 `kWh`。

### 7.6 `location` 必须是 JSON-LD node

```turtle
sh:path be:location ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:nodeKind sh:BlankNodeOrIRI ;
sh:message "location is required and must be represented as a JSON-LD node." ;
```

这表示：

```text
location 不能只是一个普通字符串；
它应该是一个 JSON-LD node，也就是一个嵌套对象或 IRI。
```

valid example 中的 location 是：

```json
"location": {
  "city": "Shenzhen",
  "district": "Nanshan"
}
```

这符合“嵌套地点节点”的设计。

## 8. `energy-reading-record-valid.jsonld`：一条合格的能耗读数

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/energy-reading-record-valid.jsonld
```

valid record 是：

```json
{
  "@context": "energy-reading-record-context.jsonld",
  "@id": "https://w3id.org/dssc-demo/building-energy/reading/BLD-001-MTR-001-202605010000",
  "@type": "EnergyReadingRecord",
  "buildingId": "BLD-001",
  "meterId": "MTR-001",
  "timestamp": "2026-05-01T00:00:00+08:00",
  "energyKWh": 12.4,
  "unit": "kWh",
  "location": {
    "city": "Shenzhen",
    "district": "Nanshan"
  },
  "conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.3"
}
```

### 8.1 它表达了什么

这条 record 可以用业务语言解释为：

```text
在 2026-05-01 00:00:00 +08:00，
建筑 BLD-001 的仪表 MTR-001 记录到 12.4 kWh 的能耗，
地点是深圳南山区，
这条记录符合 v0.3 模型。
```

### 8.2 它为什么合格

| 字段 | 样例值 | 合格原因 |
|---|---|---|
| `buildingId` | `BLD-001` | 字符串，且存在。 |
| `meterId` | `MTR-001` | 字符串，且存在。 |
| `timestamp` | `2026-05-01T00:00:00+08:00` | date-time 格式。 |
| `energyKWh` | `12.4` | JSON number，且非负。 |
| `unit` | `kWh` | 符合枚举。 |
| `location` | `{ city, district }` | 嵌套地点对象。 |

这条记录同时适合作为：

```text
JSON-LD semantic example
SHACL record validation input
JSON Schema validation input
OpenAPI response example 的语义基础
```

## 9. `energy-reading-record-invalid.jsonld`：record 层面的失败样例

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/energy-reading-record-invalid.jsonld
```

invalid record 是：

```json
{
  "@context": "energy-reading-record-context.jsonld",
  "@id": "https://w3id.org/dssc-demo/building-energy/reading/invalid-001",
  "@type": "EnergyReadingRecord",
  "buildingId": "BLD-001",
  "timestamp": "not-a-date-time",
  "energyKWh": "12.4",
  "unit": "MWh",
  "location": {
    "city": "Shenzhen",
    "district": "Nanshan"
  },
  "conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.3"
}
```

它故意包含多个问题：

| 错误 | 为什么不合格 |
|---|---|
| 缺少 `meterId` | record 无法说明由哪个仪表产生。 |
| `timestamp = not-a-date-time` | 不是合法 date-time。 |
| `energyKWh = "12.4"` | 在 JSON Schema 层它是字符串，不是 number。 |
| `unit = MWh` | 不符合 `kWh` 枚举。 |

这里要特别区分两种验证：

```text
SHACL 主要检查 JSON-LD 展开后的 RDF 语义图；
JSON Schema 主要检查原始 JSON payload 的结构和类型。
```

因此，某些错误可能更容易被 JSON Schema 捕获，例如：

```text
energyKWh 是字符串而不是 number
```

而某些错误则是 SHACL 和 JSON Schema 都能表达，例如：

```text
meterId 缺失
unit 不在 kWh 枚举中
```

这正是 v0.3 同时提供 SHACL 和 JSON Schema 的原因：它们关注的层次不同，但可以互补。

## 10. `energy-reading-record.schema.json`：API payload 的 JSON Schema

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/energy-reading-record.schema.json
```

这个文件使用 JSON Schema Draft 7，定义一条 Energy Reading Record 在普通 JSON API payload 中应该长什么样。

### 10.1 Required 字段

schema 中：

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

这表示 API 返回的一条 record 必须包含六个字段：

```text
buildingId
meterId
timestamp
energyKWh
unit
location
```

### 10.2 JSON-LD 元字段是可选的

schema 允许可选的：

```text
@context
@id
@type
conformsTo
```

这说明 API payload 可以是 JSON-LD 风格，也可以保留这些语义元数据。

其中：

```json
"@id": {
  "type": "string",
  "format": "uri"
}
```

要求 `@id` 如果出现，应是 URI 字符串。

### 10.3 字段类型约束

主要字段约束如下：

| 字段 | JSON Schema 约束 |
|---|---|
| `buildingId` | string，`minLength: 1` |
| `meterId` | string，`minLength: 1` |
| `timestamp` | string，`format: date-time` |
| `energyKWh` | number，`minimum: 0` |
| `unit` | string，enum 只能是 `kWh` |
| `location` | object，必须包含 `city` 和 `district` |

这和 record SHACL shape 对应，但不是完全重复。

可以这样理解：

```text
SHACL 面向 RDF/JSON-LD 语义图；
JSON Schema 面向 API 返回的 JSON 文档结构。
```

### 10.4 `additionalProperties: false`

schema 末尾有：

```json
"additionalProperties": false
```

这表示除了 schema 中列出的字段，不允许出现其他未声明字段。

这个约束让 API payload 更稳定。consumer 可以相信返回对象不会随意多出未治理的字段。

location 内部也有：

```json
"additionalProperties": false
```

这表示 location 中也只允许：

```text
city
district
```

## 11. `openapi-fragment.yaml`：把 record schema 放进 API 文档

文件位置：

```text
C_Semantic_Treehouse/model/v0.3/openapi-fragment.yaml
```

OpenAPI fragment 描述一个最小 API：

```yaml
openapi: 3.0.3
info:
  title: Building Energy Consumption Dataset API
  version: 0.3.0
```

### 11.1 API endpoint

核心 path 是：

```yaml
paths:
  /energy/buildings/hourly:
    get:
      summary: Return hourly building energy readings.
```

这和 metadata 中的 endpointUrl 对应：

```json
"endpointUrl": "https://api.example.org/energy/buildings/hourly"
```

也就是说，metadata 里声明的 endpoint，OpenAPI 里给出了接口结构说明。

### 11.2 Query parameters

OpenAPI 里定义了三个可选 query 参数：

| 参数 | 含义 |
|---|---|
| `buildingId` | 按建筑 ID 过滤。 |
| `from` | 查询开始时间。 |
| `to` | 查询结束时间。 |

其中 `from` 和 `to` 的 schema 是：

```yaml
type: string
format: date-time
```

这和 record 的 timestamp 类型保持一致。

### 11.3 Response schema

OpenAPI 中：

```yaml
responses:
  "200":
    description: Array of energy reading records.
    content:
      application/json:
        schema:
          type: array
          items:
            $ref: "#/components/schemas/EnergyReadingRecord"
```

这表示：

```text
GET /energy/buildings/hourly 返回一个数组；
数组中的每个元素都是 EnergyReadingRecord。
```

### 11.4 Components 中的 EnergyReadingRecord

OpenAPI 的 `components.schemas.EnergyReadingRecord` 定义了和 JSON Schema 类似的结构：

```text
required:
  buildingId
  meterId
  timestamp
  energyKWh
  unit
  location
```

这让 API 文档和语义模型保持一致。

所以 v0.3 的 API 层连接关系是：

```text
metadata endpointUrl
    ↓
OpenAPI path /energy/buildings/hourly
    ↓
OpenAPI response schema EnergyReadingRecord
    ↓
JSON Schema / SHACL / ontology 中的 EnergyReadingRecord
```

这是 v0.3 最漂亮的一条链。

## 12. v0.3 的端到端读取方式

如果把 v0.3 文件串起来看，可以分两条路线。

### 12.1 Metadata 路线

```text
data-product-valid.jsonld
    ↓
data-product-context.jsonld
    ↓
data-product-metadata-shapes.ttl
    ↓
building-energy-ontology.ttl
```

这条路线说明：

```text
数据产品 metadata 如何声明自己符合 v0.3；
metadata 字段如何映射到 RDF；
metadata 如何通过 SHACL 验证；
metadata 类和属性如何在 ontology 中定义。
```

### 12.2 Record Payload 路线

```text
energy-reading-record-valid.jsonld
    ↓
energy-reading-record-context.jsonld
    ↓
energy-reading-record-shapes.ttl
    ↓
energy-reading-record.schema.json
    ↓
openapi-fragment.yaml
    ↓
building-energy-ontology.ttl
```

这条路线说明：

```text
API 返回的一条 record 长什么样；
record 字段如何映射到 RDF；
record 如何被 SHACL 验证；
record 如何被 JSON Schema 验证；
record 如何出现在 OpenAPI response 中；
record 的类和属性如何在 ontology 中定义。
```

两条路线合在一起，就是 v0.3 的完整价值：

```text
既能治理 data product metadata，
又能治理 API payload record。
```

## 13. v0.3 和 v0.2 的关键差异

| 维度 | v0.2 | v0.3 |
|---|---|---|
| Metadata 合同 | 有 | 保留 |
| Metadata valid example | 有 | 有，版本更新为 v0.3 |
| Metadata invalid example | 有 | 未新增，v0.2 已覆盖 metadata 失败案例 |
| Record ontology | 无 | 新增 `EnergyReadingRecord` |
| Record SHACL | 无 | 新增 `energy-reading-record-shapes.ttl` |
| Record context | 无 | 新增 `energy-reading-record-context.jsonld` |
| Record valid/invalid examples | 无 | 新增 |
| JSON Schema | 无 | 新增 `energy-reading-record.schema.json` |
| OpenAPI | 无 | 新增 `openapi-fragment.yaml` |

最重要的变化是：

```text
v0.2 管 data product metadata；
v0.3 同时管 metadata 和 API record payload。
```

## 14. v0.3 和外部标准的对齐

v0.3 的 standards-aligned 特征比 v0.1 和 v0.2 更明显。

| 本地概念或属性 | 对齐标准 | 含义 |
|---|---|---|
| `be:DataProductMetadata` | `dcat:Dataset` | 数据产品 metadata 是一种数据集描述。 |
| `be:endpointUrl` | `dcat:endpointURL` | endpoint 对齐数据服务 endpoint。 |
| `be:format` | `dct:format` | 数据格式对齐 Dublin Core format。 |
| `be:frequency` | `dct:accrualPeriodicity` | 频率对齐更新周期。 |
| `be:spatialCoverage` | `dct:spatial` | 空间覆盖对齐 spatial metadata。 |
| `be:EnergyReadingRecord` | `sosa:Observation` | 一条读数是一次观测。 |
| `be:Meter` | `sosa:Sensor` | 仪表是一种 sensor。 |
| `be:timestamp` | `sosa:resultTime` | 时间戳是观测结果时间。 |
| `be:energyKWh` | `qudt:numericValue` | 能耗数值对齐 QUDT numeric value。 |
| `be:city` | `schema:addressLocality` | 城市对齐 schema.org 地址 locality。 |
| `be:district` | `schema:containedInPlace` | 区域位置关系对齐 schema.org。 |

这说明 v0.3 不是只定义本地字段，而是在尽量把本地数据结构挂到已有语义标准上。

## 15. v0.3 对 A 组和 D 组的意义

### 15.1 对 A 组的意义

A 组可以使用 v0.3 metadata contract 作为 data offering metadata 的共同约束：

```text
datasetId
providerName
endpointUrl
format
frequency
unit
spatialCoverage
temporalStart
temporalEnd
```

同时，A 组还可以用：

```text
energy-reading-record.schema.json
openapi-fragment.yaml
```

来说明 mock API 或 offering API 的返回结构。

也就是说，v0.3 给 A 组的不只是 metadata 字段，还包括 API payload 的 contract。

### 15.2 对 D 组的意义

D 组可以验证两类对象：

```text
DataProductMetadata
EnergyReadingRecord
```

对应材料包括：

```text
data-product-metadata-shapes.ttl
energy-reading-record-shapes.ttl
energy-reading-record.schema.json
data-product-valid.jsonld
energy-reading-record-valid.jsonld
energy-reading-record-invalid.jsonld
```

这让 D 组的 validation demo 更丰富：

```text
先验证 metadata 是否合格；
再验证 API record 是否合格；
最后展示 invalid record 为什么失败。
```

## 16. v0.3 刻意没有做什么

v0.3 已经是 Phase 01 中最完整的模型，但它仍然是一个 minimal demo profile。

### 16.1 没有完整能源领域 ontology

v0.3 只定义与 demo 相关的最小类和属性：

```text
DataProductMetadata
EnergyReadingRecord
Building
Meter
```

它没有尝试覆盖完整建筑能源系统，例如楼层、房间、设备类型、负载类型、价格、碳排放等。

### 16.2 没有完整 QUDT/UCUM 单位 URI

`unit` 仍然使用简单字面量：

```text
kWh
```

虽然 `energyKWh` 对齐到了 `qudt:numericValue`，但单位本身没有建成 QUDT/UCUM 的 URI。这是一个有意识的简化，方便 demo 中做枚举验证。

### 16.3 没有复杂观测关系建模

v0.3 定义了 `EnergyReadingRecord`、`Building`、`Meter`，但 record 中仍然使用：

```text
buildingId
meterId
```

而不是更复杂的 RDF object links，例如：

```text
sosa:madeBySensor
sosa:hasFeatureOfInterest
```

这也是为了保持 payload 接近普通 API JSON，降低 demo 复杂度。

### 16.4 OpenAPI 只是 fragment

`openapi-fragment.yaml` 是最小片段，不是完整生产级 API specification。

它用于说明：

```text
这个 endpoint 返回 EnergyReadingRecord 数组；
record schema 和语义模型对齐。
```

它没有包含认证、错误码、分页、完整 server 配置等生产 API 细节。

## 17. 研讨时可以怎么讲

介绍 v0.3 时，可以用这段逻辑：

```text
v0.3 保留 v0.2 的 metadata contract，同时新增 EnergyReadingRecord。
这意味着 C 组的模型不再只描述数据产品本身，也开始描述 API 实际返回的一条能耗读数。
在 ontology 中，EnergyReadingRecord 被建模为 sosa:Observation，meter 被建模为 sosa:Sensor，timestamp 对齐到 sosa:resultTime，energyKWh 对齐到 qudt:numericValue。
在约束层，v0.3 同时提供 SHACL shape 和 JSON Schema：SHACL 负责 RDF/JSON-LD 语义图，JSON Schema 负责普通 API payload 的 JSON 结构。
最后，OpenAPI fragment 把 EnergyReadingRecord 放到 GET /energy/buildings/hourly 的 response 中，让 metadata endpoint、API 文档和 record schema 连接起来。
所以 v0.3 的关键意义是：它把 semantic governance 从 catalogue metadata 扩展到了 API payload。
```

一句话总结：

```text
v0.3 让同一个数据产品同时拥有 metadata 合同和 API record 合同。
```

## 18. 适合现场打开的文件顺序

如果现场讲 v0.3，建议按这个顺序打开：

1. `data-product-valid.jsonld`

   先说明 v0.3 仍然保留 v0.2 的 metadata 合同。

2. `energy-reading-record-valid.jsonld`

   让大家看到新增的 API record 长什么样。

3. `energy-reading-record-invalid.jsonld`

   展示 record 层面会出现哪些错误。

4. `energy-reading-record.schema.json`

   解释 API payload 的 JSON 结构约束。

5. `openapi-fragment.yaml`

   展示 API endpoint 如何返回 record 数组。

6. `energy-reading-record-shapes.ttl`

   说明 SHACL 如何验证 record 的 RDF/JSON-LD 语义结构。

7. `building-energy-ontology.ttl`

   最后回到 ontology，看 `EnergyReadingRecord`、`Building`、`Meter` 和外部标准的对齐。

这个顺序从具体例子出发，再进入 schema、OpenAPI 和 ontology，对听众更友好。

## 19. v0.3 的整体价值

v0.3 是 Phase 01 的收束版本。它把前两个版本的积累整合起来：

```text
v0.1 的最小 metadata baseline
v0.2 的 validation-oriented metadata contract
v0.3 的 API record payload extension
```

最终形成一个可交付的语义模型包：

| 能力 | v0.3 如何提供 |
|---|---|
| 语义定义 | `building-energy-ontology.ttl` |
| Metadata JSON-LD 映射 | `data-product-context.jsonld` |
| Record JSON-LD 映射 | `energy-reading-record-context.jsonld` |
| Metadata SHACL 验证 | `data-product-metadata-shapes.ttl` |
| Record SHACL 验证 | `energy-reading-record-shapes.ttl` |
| Metadata 正例 | `data-product-valid.jsonld` |
| Record 正反例 | `energy-reading-record-valid.jsonld` / `energy-reading-record-invalid.jsonld` |
| API payload JSON 验证 | `energy-reading-record.schema.json` |
| API 文档连接 | `openapi-fragment.yaml` |

因此，v0.3 最值得强调的是：

```text
它不是单一文件，而是一组互相对齐的语义产物。
```

ontology 说明概念含义，JSON-LD context 连接 JSON 字段和 RDF 语义，SHACL 负责语义验证，JSON Schema 负责 API payload 结构验证，OpenAPI 把 record schema 放进接口文档。

这就是 C 组 Semantic Treehouse 工作在 Phase 01 中的完整模型表达。

