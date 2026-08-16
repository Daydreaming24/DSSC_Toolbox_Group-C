# Model v0.2 详细解读：从基础 Metadata 到验证导向的语义合同

## 1. v0.2 的定位

`model/v0.2` 是在 v0.1 基础上发展出来的第二个模型版本。它的核心目标是把 v0.1 的“基础 data product metadata 描述”推进成一个更适合 onboarding validation 的语义合同。

如果说 v0.1 主要回答：

```text
一个数据产品最少应该怎样被描述？
```

那么 v0.2 开始回答：

```text
一个数据产品要进入 data space，
metadata 至少应该满足哪些可验证条件？
```

这就是 v0.2 和 v0.1 的最大区别。v0.1 只是建立最小描述框架；v0.2 开始让 metadata 具备更强的工程可用性，因为它加入了 API endpoint、单位、时间覆盖范围和更严格的枚举约束。

v0.2 的模型仍然只关注 data product metadata，还没有进入 API record payload。API 返回的一条能耗读数 `EnergyReadingRecord` 会在 v0.3 出现。

## 2. v0.2 目录里为什么有五个文件

v0.2 目录下有五个文件：

```text
C_Semantic_Treehouse/model/v0.2/
  building-energy-ontology.ttl
  data-product-context.jsonld
  data-product-metadata-shapes.ttl
  data-product-valid.jsonld
  data-product-invalid.jsonld
```

和 v0.1 相比，v0.2 多了一个 `data-product-invalid.jsonld`。这是一个很重要的变化，因为 v0.2 不只是给出“合格样例”，还专门给出“失败样例”。

五个文件的职责如下：

| 文件 | 主要职责 | 它回答的问题 |
|---|---|---|
| `building-energy-ontology.ttl` | 定义 v0.2 的类、属性和标准对齐 | v0.2 比 v0.1 多了哪些语义字段？ |
| `data-product-context.jsonld` | 定义 JSON-LD 字段映射和类型提示 | JSON 中的 endpoint/date 字段如何变成 RDF 语义？ |
| `data-product-metadata-shapes.ttl` | 定义更严格的 SHACL 约束 | 哪些字段必填？哪些值只能取固定枚举？ |
| `data-product-valid.jsonld` | 提供通过验证的正例 | 一个合格 v0.2 metadata 长什么样？ |
| `data-product-invalid.jsonld` | 提供故意失败的反例 | validator 应该能抓出哪些错误？ |

可以把 v0.2 看成一个更完整的验证闭环：

```text
ontology 定义更丰富的 metadata 词汇
    ↓
context 把 JSON 字段映射为 RDF IRI，并标注 IRI/date 类型
    ↓
SHACL shapes 定义必填、单值、类型和枚举规则
    ↓
valid example 证明合格 metadata 怎么写
    ↓
invalid example 证明错误 metadata 会被拒绝
```

## 3. v0.2 相比 v0.1 新增了什么

v0.1 要求五个基础字段：

| v0.1 字段 | 含义 |
|---|---|
| `datasetId` | 数据产品标识符。 |
| `providerName` | 数据提供方名称。 |
| `format` | 数据格式。 |
| `frequency` | 数据更新或采样频率。 |
| `spatialCoverage` | 空间覆盖范围。 |

v0.2 保留这些字段，并新增四个字段：

| v0.2 新增字段 | 含义 | 为什么重要 |
|---|---|---|
| `endpointUrl` | 数据产品 API endpoint | 让 data offering 能连接到实际数据服务。 |
| `unit` | 能耗单位 | 保证消费者理解数值含义，例如 `kWh`。 |
| `temporalStart` | 数据时间覆盖起点 | 说明数据从哪一天开始。 |
| `temporalEnd` | 数据时间覆盖终点 | 说明数据到哪一天结束。 |

因此 v0.2 一共要求九个 metadata 字段：

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

这四个新增字段把 metadata 从“能被目录展示”推进到“能支持数据产品接入、验证和消费”。

## 4. `building-energy-ontology.ttl`：验证导向的 metadata vocabulary

文件位置：

```text
C_Semantic_Treehouse/model/v0.2/building-energy-ontology.ttl
```

v0.2 的 ontology 仍然使用 Turtle 语法。它继续定义 `be:DataProductMetadata`，并增加了更完整的数据产品 metadata 属性。

### 4.1 版本声明

v0.2 ontology 的开头是：

```turtle
<https://w3id.org/dssc-demo/building-energy/v0.2>
    a owl:Ontology ;
    owl:versionIRI <https://w3id.org/dssc-demo/building-energy/v0.2> ;
    owl:priorVersion <https://w3id.org/dssc-demo/building-energy/v0.1> ;
    owl:versionInfo "0.2" ;
    dct:title "Building Energy Semantic Model v0.2" ;
    dct:description "Validation-oriented metadata vocabulary for the Building Energy Consumption Data Product." ;
    dct:created "2026-06-25"^^xsd:date .
```

这里比 v0.1 多了一个很重要的字段：

```turtle
owl:priorVersion <https://w3id.org/dssc-demo/building-energy/v0.1>
```

它说明 v0.2 是从 v0.1 演进而来的。这个声明让版本链变得明确：

```text
v0.1 -> v0.2
```

这对模型治理很重要，因为后续解释变化时，可以清楚说明：

```text
v0.2 不是另起炉灶，而是在 v0.1 baseline 上增加更严格的 metadata 要求。
```

### 4.2 核心类仍然是 `be:DataProductMetadata`

v0.2 继续使用同一个核心类：

```turtle
be:DataProductMetadata
    a owl:Class ;
    rdfs:subClassOf dcat:Dataset ;
    rdfs:label "Data Product Metadata" ;
    rdfs:comment "Metadata describing a data product for catalogue discovery, connector offering creation, and SHACL validation." .
```

和 v0.1 相比，这里的 comment 多了两个重点：

```text
connector offering creation
SHACL validation
```

这说明 v0.2 的 metadata 不只是给目录发现用，也开始面向连接器 offering 和验证流程。

### 4.3 新增 `endpointUrl`

v0.2 新增：

```turtle
be:endpointUrl
    a owl:ObjectProperty ;
    rdfs:subPropertyOf dcat:endpointURL ;
    rdfs:label "endpoint URL" ;
    rdfs:comment "IRI of the API endpoint that exposes the data product." ;
    rdfs:domain be:DataProductMetadata .
```

这里有几个值得讲的点。

首先，`endpointUrl` 被定义为：

```text
owl:ObjectProperty
```

这表示它指向的是一个资源 IRI，而不是普通字符串。

其次，它对齐到 DCAT：

```text
rdfs:subPropertyOf dcat:endpointURL
```

也就是说，项目自己的 `be:endpointUrl` 可以被理解为 DCAT 标准中的 endpoint URL 的一种。

这个字段对 A 组很有意义。因为 data offering 不只是一个 metadata 展示页，它需要知道实际 API 在哪里，才能让 consumer 发现并访问服务。

### 4.4 `format` 对齐到 `dct:format`

v0.2 中：

```turtle
be:format
    a owl:DatatypeProperty ;
    rdfs:subPropertyOf dct:format ;
    ...
```

v0.1 里 `be:format` 只是本地属性；v0.2 开始把它明确对齐到 `dct:format`。

这意味着：

```text
项目内叫 be:format；
标准语义上，它是 Dublin Core format 的一个子属性。
```

### 4.5 `frequency` 对齐到 `dct:accrualPeriodicity`

v0.2 中：

```turtle
be:frequency
    a owl:DatatypeProperty ;
    rdfs:subPropertyOf dct:accrualPeriodicity ;
    ...
```

`dct:accrualPeriodicity` 是 Dublin Core 中用于描述资源更新频率的属性。把 `frequency` 对齐到它，说明这里的 `hourly` 不是随便一个字符串，而是在描述数据产品的更新或采样周期。

### 4.6 新增 `unit`

v0.2 新增：

```turtle
be:unit
    a owl:DatatypeProperty ;
    rdfs:label "unit" ;
    rdfs:comment "Required measurement unit for energy values in the data product." ;
    rdfs:domain be:DataProductMetadata ;
    rdfs:range xsd:string .
```

`unit` 在建筑能耗数据里非常关键。因为同样是数字，如果单位不同，含义完全不同：

```text
12.4 kWh
12.4 MWh
```

这两个值相差 1000 倍。因此 v0.2 要求 unit，并在 SHACL 中进一步规定 unit 只能是 `kWh`。

这里还没有使用 QUDT/UCUM 的单位 IRI，而是先使用简单字面量 `kWh`。这是一个 demo 中合理的简化：先保证 validator 能执行单位一致性检查，再在后续 phase 通过映射和治理文档补充更丰富的标准对齐。

### 4.7 `spatialCoverage` 对齐到 `dct:spatial`

v0.2 中：

```turtle
be:spatialCoverage
    a owl:DatatypeProperty ;
    rdfs:subPropertyOf dct:spatial ;
    ...
```

这说明 `spatialCoverage` 描述的是数据产品覆盖的空间范围。当前值是人类可读字符串，例如：

```text
Shenzhen demo district
```

### 4.8 新增 `temporalStart` 和 `temporalEnd`

v0.2 新增两个时间覆盖字段：

```turtle
be:temporalStart
    a owl:DatatypeProperty ;
    rdfs:label "temporal start" ;
    rdfs:comment "Inclusive start date of the data product temporal coverage." ;
    rdfs:domain be:DataProductMetadata ;
    rdfs:range xsd:date .
```

```turtle
be:temporalEnd
    a owl:DatatypeProperty ;
    rdfs:label "temporal end" ;
    rdfs:comment "Inclusive end date of the data product temporal coverage." ;
    rdfs:domain be:DataProductMetadata ;
    rdfs:range xsd:date .
```

这两个字段让 metadata 可以说明：

```text
这个数据产品覆盖从哪一天到哪一天的数据。
```

在 valid example 中：

```text
temporalStart = 2026-05-01
temporalEnd   = 2026-05-02
```

这对 consumer 很有用，因为 consumer 需要知道数据是否覆盖自己关心的时间范围。

## 5. `data-product-context.jsonld`：把新增字段变成可展开语义

文件位置：

```text
C_Semantic_Treehouse/model/v0.2/data-product-context.jsonld
```

v0.2 的 context 继承了 v0.1 的基本思路，但增加了 `endpointUrl`、`unit`、`temporalStart`、`temporalEnd` 的映射。

### 5.1 保留 v0.1 的基础映射

v0.2 仍然保留：

| JSON 字段 | RDF 属性 |
|---|---|
| `datasetId` | `dct:identifier` |
| `providerName` | `be:providerName` |
| `format` | `be:format` |
| `frequency` | `be:frequency` |
| `spatialCoverage` | `be:spatialCoverage` |
| `conformsTo` | `dct:conformsTo` |

这说明 v0.2 没有破坏 v0.1 的基本 metadata 结构，而是在它上面增加约束和字段。

### 5.2 `endpointUrl` 的 IRI 类型

context 中：

```json
"endpointUrl": {
  "@id": "be:endpointUrl",
  "@type": "@id"
}
```

这里的关键是：

```json
"@type": "@id"
```

这表示 `endpointUrl` 的值应该被当作 IRI，而不是普通字符串。

因此 valid example 里的：

```json
"endpointUrl": "https://api.example.org/energy/buildings/hourly"
```

在 JSON-LD 语义中会被理解为一个资源链接。

这和 SHACL 中的要求相呼应：

```text
endpointUrl must be an IRI.
```

### 5.3 `temporalStart` 和 `temporalEnd` 的日期类型

context 中：

```json
"temporalStart": {
  "@id": "be:temporalStart",
  "@type": "xsd:date"
},
"temporalEnd": {
  "@id": "be:temporalEnd",
  "@type": "xsd:date"
}
```

这表示：

```text
temporalStart 和 temporalEnd 不是普通字符串，而是 xsd:date 类型的值。
```

因此：

```json
"temporalStart": "2026-05-01"
```

会被解释为日期 literal。

这个设计让 metadata 具有更明确的数据类型，也方便 validator 或 RDF 工具处理。

### 5.4 `unit` 的映射

context 中：

```json
"unit": "be:unit"
```

目前 unit 还是简单字面量：

```json
"unit": "kWh"
```

这和 ontology 中的 `rdfs:range xsd:string` 以及 SHACL 中的 `sh:in ("kWh")` 对应。

## 6. `data-product-metadata-shapes.ttl`：v0.2 的核心验证规则

文件位置：

```text
C_Semantic_Treehouse/model/v0.2/data-product-metadata-shapes.ttl
```

这个文件是 v0.2 最关键的工程文件。它把 v0.2 的模型要求写成机器可执行的 SHACL 约束。

核心 shape 是：

```turtle
be:DataProductMetadataShape-v0_2
    a sh:NodeShape ;
    sh:targetClass be:DataProductMetadata ;
    ...
```

意思是：

```text
所有 be:DataProductMetadata 实例都应该按 v0.2 的规则检查。
```

### 6.1 基础字段仍然必填

v0.2 继续要求：

```text
datasetId
providerName
spatialCoverage
```

这些字段都必须：

```text
minCount = 1
maxCount = 1
datatype = xsd:string
```

也就是说，它们必须出现一次，且只能出现一次，值必须是字符串。

### 6.2 `endpointUrl` 必须是 IRI

SHACL 中：

```turtle
sh:path be:endpointUrl ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:nodeKind sh:IRI ;
sh:message "endpointUrl is required and must be an IRI." ;
```

这表示：

```text
endpointUrl 必须出现一次；
它不能只是任意 literal；
它必须是 IRI。
```

这一点和 JSON-LD context 的 `@type: @id` 互相配合。

### 6.3 `format` 被限制为 `JSON`

SHACL 中：

```turtle
sh:path be:format ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:in ("JSON") ;
sh:message "format must be JSON in v0.2." ;
```

v0.1 只要求 `format` 是字符串；v0.2 则要求它必须等于：

```text
JSON
```

这说明 v0.2 开始使用枚举约束。它不是只看字段有没有，而是检查字段值是否符合项目约定。

### 6.4 `frequency` 被限制为 `hourly`

SHACL 中：

```turtle
sh:path be:frequency ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:in ("hourly") ;
sh:message "frequency must be hourly in v0.2." ;
```

这和项目场景一致：数据产品是建筑小时级用电量数据，因此频率应为 `hourly`。

### 6.5 `unit` 被限制为 `kWh`

SHACL 中：

```turtle
sh:path be:unit ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:in ("kWh") ;
sh:message "unit must be kWh in v0.2." ;
```

这条规则非常重要，因为它直接防止单位混乱。

如果某个 metadata 写：

```json
"unit": "MWh"
```

那么它虽然是一个字符串，但不在允许列表里，因此应该验证失败。

这正是 v0.2 invalid example 故意测试的错误之一。

### 6.6 `temporalStart` 和 `temporalEnd` 必须是日期

SHACL 中：

```turtle
sh:path be:temporalStart ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:datatype xsd:date ;
sh:message "temporalStart is required and must be an xsd:date." ;
```

```turtle
sh:path be:temporalEnd ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:datatype xsd:date ;
sh:message "temporalEnd is required and must be an xsd:date." ;
```

这表示两个时间覆盖字段都必须存在，且值必须符合 `xsd:date`。

当前 shape 检查的是：

```text
是否存在；
是否单值；
是否是 date 类型。
```

它还没有检查：

```text
temporalStart 是否早于 temporalEnd。
```

如果后续要增强模型，可以加入跨字段比较逻辑，但这超出了 v0.2 的最小演示目标。

## 7. `data-product-valid.jsonld`：一个合格 v0.2 metadata

文件位置：

```text
C_Semantic_Treehouse/model/v0.2/data-product-valid.jsonld
```

valid example 是：

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
  "conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.2"
}
```

### 7.1 它为什么合格

这个样例满足 v0.2 的所有要求：

| 字段 | 样例值 | 是否满足 v0.2 |
|---|---|---|
| `datasetId` | `building-energy-hourly-v1` | 是，字符串且单值。 |
| `providerName` | `Energy Data Provider Ltd.` | 是，字符串且单值。 |
| `endpointUrl` | `https://api.example.org/energy/buildings/hourly` | 是，IRI。 |
| `format` | `JSON` | 是，符合枚举。 |
| `frequency` | `hourly` | 是，符合枚举。 |
| `unit` | `kWh` | 是，符合枚举。 |
| `spatialCoverage` | `Shenzhen demo district` | 是，字符串且单值。 |
| `temporalStart` | `2026-05-01` | 是，`xsd:date`。 |
| `temporalEnd` | `2026-05-02` | 是，`xsd:date`。 |

### 7.2 它比 v0.1 样例更接近真实 data offering

v0.1 样例只能说明：

```text
这个数据产品是谁提供的、格式是什么、频率是什么、覆盖哪里。
```

v0.2 样例进一步说明：

```text
API endpoint 在哪里；
能耗单位是什么；
数据覆盖的日期范围是什么。
```

这让 metadata 更适合传递给 A 组作为 data offering 的输入，也更适合传递给 D 组做 validation demo。

### 7.3 `conformsTo` 指向 v0.2

valid example 的最后一行是：

```json
"conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.2"
```

这表示当前 metadata 声称自己遵循 v0.2 模型。

它和 v0.1 样例最大的区别是版本 IRI 不同：

```text
v0.1 example -> conformsTo v0.1
v0.2 example -> conformsTo v0.2
```

这样下游工具和读者都能清楚知道应该用哪一版 shape 来解释和验证数据。

## 8. `data-product-invalid.jsonld`：故意失败的反例

文件位置：

```text
C_Semantic_Treehouse/model/v0.2/data-product-invalid.jsonld
```

invalid example 是 v0.2 非常重要的新增文件。它的内容是：

```json
{
  "@context": "data-product-context.jsonld",
  "@id": "https://w3id.org/dssc-demo/building-energy/data-product/building-energy-hourly-v1-invalid",
  "@type": "DataProductMetadata",
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

它故意包含三个错误：

| 错误 | 对应 SHACL 规则 | 为什么应该失败 |
|---|---|---|
| 缺少 `providerName` | `providerName minCount 1` | 数据产品没有声明提供方。 |
| `unit = MWh` | `unit sh:in ("kWh")` | 单位不符合 v0.2 约定。 |
| 缺少 `temporalEnd` | `temporalEnd minCount 1` | 时间覆盖范围不完整。 |

### 8.1 缺少 `providerName`

v0.2 shape 要求：

```text
providerName 必须出现一次。
```

但 invalid example 里没有：

```json
"providerName": "..."
```

所以 validator 应该报告 providerName 缺失。

这不是小问题。没有 providerName，consumer 或 data space authority 就不知道这个数据产品由哪个组织发布和负责。

### 8.2 `unit` 写成了 `MWh`

invalid example 中：

```json
"unit": "MWh"
```

但是 v0.2 只允许：

```text
kWh
```

因此它违反：

```turtle
sh:in ("kWh")
```

这个错误特别适合演示语义治理的价值。因为 `MWh` 不是语法错误，也不是 JSON 错误；它是业务语义错误。普通 JSON parser 不会拒绝它，但 SHACL validator 可以拒绝。

### 8.3 缺少 `temporalEnd`

invalid example 只有：

```json
"temporalStart": "2026-05-01"
```

但没有：

```json
"temporalEnd": "..."
```

这意味着数据产品只说明了开始日期，没有说明结束日期，时间覆盖范围不完整。

### 8.4 invalid example 的意义

这个文件的意义不是“给一个坏数据看看”，而是证明：

```text
v0.2 的模型可以区分合格 metadata 和不合格 metadata。
```

它也能帮助 D 组展示 validation：

```text
valid metadata 应该通过；
invalid metadata 应该失败；
失败原因应该能解释为缺字段、枚举错误、时间范围不完整。
```

这比只提供 valid example 更有说服力。

## 9. v0.2 的端到端读取方式

如果把 v0.2 五个文件串起来看，工作流如下。

### 第一步：ontology 定义更完整的 metadata 词汇

`building-energy-ontology.ttl` 定义：

```text
DataProductMetadata 仍然是核心类；
endpointUrl、unit、temporalStart、temporalEnd 被加入；
format、frequency、spatialCoverage 开始更明确地对齐到 DCTERMS/DCAT。
```

### 第二步：context 解释 JSON 字段和类型

`data-product-context.jsonld` 定义：

```text
endpointUrl 是 be:endpointUrl，值应作为 IRI；
temporalStart 和 temporalEnd 是 xsd:date；
unit 是 be:unit；
conformsTo 指向模型版本 IRI。
```

### 第三步：valid example 给出合格实例

`data-product-valid.jsonld` 展示一个完整 metadata：

```text
它有 providerName；
有 endpointUrl；
format 是 JSON；
frequency 是 hourly；
unit 是 kWh；
有完整 temporalStart 和 temporalEnd。
```

### 第四步：SHACL shape 执行验证

`data-product-metadata-shapes.ttl` 检查：

```text
九个字段是否都存在；
字段是否单值；
endpointUrl 是否是 IRI；
format/frequency/unit 是否在允许值中；
temporalStart/temporalEnd 是否是 date。
```

### 第五步：invalid example 证明约束有效

`data-product-invalid.jsonld` 故意违反规则：

```text
缺 providerName；
unit 用 MWh；
缺 temporalEnd。
```

这样 v0.2 就形成了一个正反都能跑的验证 demo。

## 10. v0.2 和 v0.1 的关键差异

| 维度 | v0.1 | v0.2 |
|---|---|---|
| 主要目标 | 建立最小 metadata baseline | 建立验证导向 metadata 合同 |
| 字段数量 | 5 个 | 9 个 |
| API endpoint | 无 | 必填 `endpointUrl` |
| 单位 | 无 | 必填 `unit = kWh` |
| 时间覆盖 | 无 | 必填 `temporalStart` 和 `temporalEnd` |
| 枚举约束 | 基本没有 | `format=JSON`、`frequency=hourly`、`unit=kWh` |
| 反例文件 | 无 | 有 `data-product-invalid.jsonld` |
| 版本关系 | 起始版本 | 声明 `owl:priorVersion v0.1` |

最重要的变化是：

```text
v0.1 证明 metadata 可以被语义化；
v0.2 证明 metadata 可以被治理和拒绝。
```

这也是从“模型描述”到“模型治理”的转折点。

## 11. v0.2 和 A 组、D 组的关系

### 11.1 对 A 组的意义

A 组关注 data offering、connector、API 或 mock data。v0.2 对 A 组有用，因为它明确要求：

```text
endpointUrl
format
frequency
unit
temporal coverage
```

这些字段可以作为 data offering metadata 的共同约束。

特别是 `endpointUrl`，它让 offering 不只是“目录里有个数据产品”，而是可以连接到具体 API。

### 11.2 对 D 组的意义

D 组关注 SEMIC Validator / ITB / SHACL validation。v0.2 对 D 组很有用，因为它提供：

```text
SHACL shape
valid metadata
invalid metadata
```

这三者刚好构成 validator demo 的输入：

```text
用同一套 shape 验证 valid example，应通过；
用同一套 shape 验证 invalid example，应失败；
失败原因对应缺字段、枚举错误、时间范围不完整。
```

因此 v0.2 是 C 组向 D 组交付验证材料的关键版本。

## 12. v0.2 刻意没有做什么

v0.2 比 v0.1 强很多，但它仍然是一个最小 demo 模型，没有试图解决所有问题。

### 12.1 没有 API record payload

v0.2 只描述 data product metadata，还没有定义一条 API 返回数据记录的结构。

也就是说，它还没有：

```text
EnergyReadingRecord
buildingId
meterId
timestamp
energyKWh
location
```

这些内容会在 v0.3 出现。

### 12.2 没有 JSON Schema 和 OpenAPI

v0.2 没有 `energy-reading-record.schema.json`，也没有 `openapi-fragment.yaml`。

因为 v0.2 还停留在 metadata validation 层；API payload validation 是 v0.3 的重点。

### 12.3 没有复杂单位体系

v0.2 中 `unit` 使用简单字面量：

```text
kWh
```

它没有直接使用 QUDT 或 UCUM 的单位 URI。这个选择让 demo 更容易验证，但也意味着更丰富的单位语义需要后续映射或治理文件补充。

### 12.4 没有跨字段时间逻辑

v0.2 检查 `temporalStart` 和 `temporalEnd` 是否存在、是否是日期，但没有检查：

```text
temporalStart <= temporalEnd
```

这是一个可以扩展的地方，但不是 v0.2 的核心目标。

## 13. 研讨时可以怎么讲

介绍 v0.2 时，可以用下面这段逻辑：

```text
v0.2 是在 v0.1 baseline 上增加验证能力的版本。
它保留了 datasetId、providerName、format、frequency、spatialCoverage，
同时新增 endpointUrl、unit、temporalStart 和 temporalEnd。
这些新增字段让 metadata 不只是能被展示，还能支撑 data offering、API 连接、单位一致性和时间覆盖说明。
v0.2 的 SHACL shape 开始限制字段取值，例如 format 必须是 JSON，frequency 必须是 hourly，unit 必须是 kWh。
此外，v0.2 专门加入 invalid example，证明 validator 能抓出 providerName 缺失、unit 错误和 temporalEnd 缺失。
所以 v0.2 的关键意义是：它把 data product metadata 从基础描述推进成了可验证、可拒绝、可交付给其他组的语义合同。
```

一句话总结：

```text
v0.2 让 metadata 从“写得出来”变成“验得出来”。
```

## 14. 适合现场打开的文件顺序

如果现场讲解 v0.2，建议按这个顺序打开：

1. `data-product-valid.jsonld`

   先看合格 metadata 新增了哪些字段。

2. `data-product-invalid.jsonld`

   再看故意失败的 metadata，理解 validator 要抓什么。

3. `data-product-metadata-shapes.ttl`

   对照 valid/invalid 样例，看每条 SHACL 规则如何生效。

4. `data-product-context.jsonld`

   解释 `endpointUrl` 为什么是 IRI，`temporalStart` 和 `temporalEnd` 为什么是 `xsd:date`。

5. `building-energy-ontology.ttl`

   最后回到 ontology，看新增属性和 DCAT/DCTERMS 的标准对齐。

这个顺序从样例出发，再进入规则和语义定义，对听众最友好。

## 15. v0.2 到 v0.3 的过渡

v0.2 完成的是 metadata 层面的验证导向建模。它还没有触及 API 返回数据本身。

v0.3 会在 v0.2 基础上继续扩展：

| v0.2 已完成 | v0.3 继续增加 |
|---|---|
| Data product metadata | Energy reading record payload |
| SHACL metadata validation | Record-level SHACL validation |
| Valid/invalid metadata examples | Valid/invalid record examples |
| endpoint/unit/temporal coverage | JSON Schema and OpenAPI fragment |

因此三个版本的关系可以这样理解：

```text
v0.1: 最小 metadata baseline
v0.2: 验证导向 metadata contract
v0.3: metadata contract + API payload contract
```

