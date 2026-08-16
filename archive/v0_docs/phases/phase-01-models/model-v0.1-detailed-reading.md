# Model v0.1 详细解读：最小 Data Product Metadata 语义模型

## 1. v0.1 的定位

`model/v0.1` 是整个 C 组 Semantic Treehouse 工作的第一个正式模型版本。它的目标不是一次性覆盖完整的建筑能耗数据空间，而是先建立一个最小、清晰、可验证的数据产品 metadata 模型。

在这个项目里，数据产品是：

```text
Building Energy Consumption Data Product
```

也就是一个建筑小时级用电量数据产品。v0.1 要回答的是：

```text
如果一个 provider 要在 data space 中发布这个数据产品，
最少应该提供哪些 metadata，
这些 metadata 在语义上分别代表什么，
机器又该如何识别和验证它们？
```

所以 v0.1 的设计非常克制，只保留五个基础字段：

| 字段 | 含义 |
|---|---|
| `datasetId` | 数据产品的标识符。 |
| `providerName` | 数据提供方名称。 |
| `format` | 数据格式，例如 `JSON`。 |
| `frequency` | 数据更新或采样频率，例如 `hourly`。 |
| `spatialCoverage` | 数据覆盖的地理范围。 |

这里暂时没有 `endpointUrl`、`unit`、`temporalStart`、`temporalEnd`。这些字段到 v0.2 才成为必填项。也就是说，v0.1 是“先把基础 metadata 说清楚”，v0.2 才进入更严格的 onboarding validation。

## 2. 为什么 v0.1 有四个文件

v0.1 目录下有四个文件：

```text
C_Semantic_Treehouse/model/v0.1/
  building-energy-ontology.ttl
  data-product-context.jsonld
  data-product-metadata-shapes.ttl
  data-product-valid.jsonld
```

这四个文件不是重复表达同一件事，而是分别承担四个不同职责：

| 文件 | 主要职责 | 它回答的问题 |
|---|---|---|
| `building-energy-ontology.ttl` | 定义语义词汇 | 这个模型里有哪些类和属性？ |
| `data-product-context.jsonld` | 定义 JSON-LD 字段映射 | JSON 字段如何映射到 RDF IRI？ |
| `data-product-metadata-shapes.ttl` | 定义 SHACL 验证规则 | 什么样的 metadata 才算合格？ |
| `data-product-valid.jsonld` | 提供合法样例 | 一个通过 v0.1 模型的数据实例长什么样？ |

可以把它们理解成一条链：

```text
ontology 定义词汇
    ↓
JSON-LD context 把普通 JSON 字段接到这些词汇上
    ↓
SHACL shapes 规定字段是否必填、类型是否正确
    ↓
valid example 展示一个可以通过验证的 metadata 实例
```

这样做的好处是模型职责清楚。ontology 不负责验证，SHACL 不负责定义业务样例，context 不负责解释所有概念。每个文件只做自己该做的事。

## 3. `building-energy-ontology.ttl`：定义模型的语义词汇

文件位置：

```text
C_Semantic_Treehouse/model/v0.1/building-energy-ontology.ttl
```

这个文件是 v0.1 的语义核心。它使用 Turtle 语法定义本体，也就是这个模型里的类、属性、命名空间和版本信息。

### 3.1 命名空间

文件开头定义了几个 prefix：

```turtle
@prefix be: <https://w3id.org/dssc-demo/building-energy#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
```

其中最重要的是：

```text
be = https://w3id.org/dssc-demo/building-energy#
```

`be` 是本项目自己定义的 Building Energy 命名空间。项目中的本地类和属性都放在这个 namespace 下，例如：

```text
be:DataProductMetadata
be:providerName
be:format
be:frequency
be:spatialCoverage
```

同时，模型也引用了一些外部标准：

| Prefix | 标准 | 在 v0.1 中的作用 |
|---|---|---|
| `dcat` | Data Catalog Vocabulary | 把数据产品 metadata 对齐到数据集概念。 |
| `dct` | Dublin Core Terms | 使用通用 metadata 属性，如 identifier、title、description。 |
| `owl` | Web Ontology Language | 声明 ontology 和版本信息。 |
| `rdfs` | RDF Schema | 声明类、属性、标签、注释、domain、range。 |
| `xsd` | XML Schema Datatypes | 声明字符串、日期等数据类型。 |

这体现了 v0.1 的一个基本原则：能复用标准词汇的地方尽量复用，项目只定义必要的本地词汇。

### 3.2 Ontology 本身的版本信息

文件中首先声明了 ontology：

```turtle
<https://w3id.org/dssc-demo/building-energy/v0.1>
    a owl:Ontology ;
    owl:versionIRI <https://w3id.org/dssc-demo/building-energy/v0.1> ;
    owl:versionInfo "0.1" ;
    dct:title "Building Energy Semantic Model v0.1" ;
    dct:description "Baseline metadata vocabulary for the Building Energy Consumption Data Product." ;
    dct:created "2026-06-25"^^xsd:date .
```

这段声明的意思是：当前文件描述的是 `v0.1` 版本的 Building Energy Semantic Model。

几个字段值得注意：

| 字段 | 含义 |
|---|---|
| `a owl:Ontology` | 声明这个 IRI 代表一个 ontology。 |
| `owl:versionIRI` | 明确这个 ontology 的版本 IRI。 |
| `owl:versionInfo "0.1"` | 给人看的版本号。 |
| `dct:title` | 模型标题。 |
| `dct:description` | 模型描述。 |
| `dct:created` | 创建日期，类型是 `xsd:date`。 |

这里的版本 IRI 很重要。它让后续 JSON-LD 样例可以通过 `conformsTo` 声明：

```text
我这个 metadata 是按照 v0.1 模型写的。
```

### 3.3 核心类：`be:DataProductMetadata`

v0.1 只定义了一个核心类：

```turtle
be:DataProductMetadata
    a owl:Class ;
    rdfs:subClassOf dcat:Dataset ;
    rdfs:label "Data Product Metadata" ;
    rdfs:comment "Metadata describing a data product for catalogue discovery and data offering creation." .
```

这段的含义是：

```text
be:DataProductMetadata 是一个类；
它是 dcat:Dataset 的子类；
它表示用于 catalogue discovery 和 data offering creation 的数据产品 metadata。
```

为什么要继承 `dcat:Dataset`？

因为 DCAT 是数据目录领域的通用标准。把 `DataProductMetadata` 设为 `dcat:Dataset` 的子类，意味着我们不是完全从零定义一个孤立概念，而是把这个项目的数据产品描述放进已有的数据目录语义体系里。

换句话说：

```text
对项目内部，它是 DataProductMetadata；
对外部标准工具，它也可以被理解为一种 Dataset。
```

这就是 semantic interoperability 的一个小例子。

### 3.4 本地属性

v0.1 定义了四个本地属性：

```text
be:providerName
be:format
be:frequency
be:spatialCoverage
```

每个属性都有类似结构：

```turtle
be:providerName
    a owl:DatatypeProperty ;
    rdfs:label "provider name" ;
    rdfs:comment "Human-readable name of the organization publishing the data product." ;
    rdfs:domain be:DataProductMetadata ;
    rdfs:range xsd:string .
```

这表示：

| 声明 | 含义 |
|---|---|
| `a owl:DatatypeProperty` | 这是一个数据类型属性，值通常是字符串、数字、日期等 literal。 |
| `rdfs:label` | 给人读的短标签。 |
| `rdfs:comment` | 给人读的解释。 |
| `rdfs:domain be:DataProductMetadata` | 这个属性主要用于 DataProductMetadata。 |
| `rdfs:range xsd:string` | 这个属性的值应该是字符串。 |

四个属性的含义如下：

| 属性 | 用途 |
|---|---|
| `be:providerName` | 数据产品发布组织的名称。 |
| `be:format` | 数据产品 payload 使用的序列化格式。 |
| `be:frequency` | 数据产品预期更新频率或累积周期。 |
| `be:spatialCoverage` | 数据产品覆盖的空间范围。 |

### 3.5 为什么 ontology 里没有 `datasetId`

v0.1 的 JSON 样例里有 `datasetId`，但 ontology 文件里没有定义 `be:datasetId`。

这是一个有意的设计，而不是遗漏。

因为 `datasetId` 在 JSON-LD context 中被映射到了标准属性：

```json
"datasetId": "dct:identifier"
```

也就是说，项目没有新造一个 `be:datasetId`，而是直接使用 Dublin Core Terms 里的 `dct:identifier`。这是合理的，因为 identifier 是非常通用的 metadata 概念，没必要在本地 namespace 里重复定义。

这个选择也能用于展示项目的标准对齐思路：

```text
通用字段用外部标准；
项目特有字段才使用 be namespace。
```

## 4. `data-product-context.jsonld`：把 JSON 字段接到 RDF 语义上

文件位置：

```text
C_Semantic_Treehouse/model/v0.1/data-product-context.jsonld
```

JSON-LD context 的作用是：让普通 JSON 字段具有 RDF 语义。

普通 JSON 里写：

```json
"providerName": "Energy Data Provider Ltd."
```

机器只知道这是一个叫 `providerName` 的字段，但不知道它对应哪个正式语义属性。

JSON-LD context 通过下面的映射告诉机器：

```json
"providerName": "be:providerName"
```

于是这条 JSON 字段就可以被理解为 RDF 语义属性：

```text
https://w3id.org/dssc-demo/building-energy#providerName
```

### 4.1 prefix 映射

context 里首先定义 prefix：

```json
"be": "https://w3id.org/dssc-demo/building-energy#",
"dcat": "http://www.w3.org/ns/dcat#",
"dct": "http://purl.org/dc/terms/",
"xsd": "http://www.w3.org/2001/XMLSchema#"
```

这些 prefix 让后面的映射可以写得更短。例如：

```json
"providerName": "be:providerName"
```

等价于完整 IRI：

```text
https://w3id.org/dssc-demo/building-energy#providerName
```

### 4.2 类型映射

context 中有：

```json
"DataProductMetadata": "be:DataProductMetadata"
```

这意味着 JSON-LD 样例里可以写：

```json
"@type": "DataProductMetadata"
```

机器展开后会理解为：

```text
@type = https://w3id.org/dssc-demo/building-energy#DataProductMetadata
```

这和 ontology 中定义的类对应起来。

### 4.3 字段映射

v0.1 的字段映射如下：

| JSON 字段 | RDF 属性 |
|---|---|
| `datasetId` | `dct:identifier` |
| `providerName` | `be:providerName` |
| `format` | `be:format` |
| `frequency` | `be:frequency` |
| `spatialCoverage` | `be:spatialCoverage` |

其中 `datasetId -> dct:identifier` 是标准复用；其他几个字段使用项目自己的 `be` namespace。

### 4.4 `conformsTo` 的特殊处理

context 中还有一段：

```json
"conformsTo": {
  "@id": "dct:conformsTo",
  "@type": "@id"
}
```

这段有两个含义：

| 配置 | 含义 |
|---|---|
| `"@id": "dct:conformsTo"` | `conformsTo` 对应 Dublin Core 的 `dct:conformsTo`。 |
| `"@type": "@id"` | `conformsTo` 的值不是普通字符串，而应该被理解为一个 IRI。 |

所以样例里：

```json
"conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.1"
```

不是一个普通文本，而是指向 v0.1 模型版本的 IRI。

这一点对于版本化很重要：下游验证工具或其他小组看到这个字段，就知道这个 metadata 声称自己遵循的是 v0.1 语义模型。

## 5. `data-product-metadata-shapes.ttl`：定义 v0.1 的合格标准

文件位置：

```text
C_Semantic_Treehouse/model/v0.1/data-product-metadata-shapes.ttl
```

ontology 负责定义概念和属性，但它通常不负责强制验证“字段必须出现几次”。这个任务交给 SHACL shapes。

v0.1 的 SHACL 文件定义了一个 NodeShape：

```turtle
be:DataProductMetadataShape-v0_1
    a sh:NodeShape ;
    sh:targetClass be:DataProductMetadata ;
    ...
```

这表示：

```text
所有类型为 be:DataProductMetadata 的节点，
都应该按照这个 shape 进行验证。
```

### 5.1 `datasetId` 约束

`datasetId` 在 SHACL 中对应的是 `dct:identifier`：

```turtle
sh:path dct:identifier ;
sh:minCount 1 ;
sh:maxCount 1 ;
sh:datatype xsd:string ;
sh:message "datasetId is required and must be a single string." ;
```

这段规则表示：

| 约束 | 含义 |
|---|---|
| `sh:path dct:identifier` | 要检查的 RDF 属性是 `dct:identifier`。 |
| `sh:minCount 1` | 至少出现一次。 |
| `sh:maxCount 1` | 最多出现一次。 |
| `sh:datatype xsd:string` | 值必须是字符串。 |
| `sh:message` | 验证失败时给出的解释。 |

换成业务语言就是：

```text
每个 data product metadata 必须有且只有一个 datasetId，
而且 datasetId 必须是字符串。
```

### 5.2 其他四个字段的约束

其余四个字段也都遵循同样模式：

```text
providerName 必须出现一次，值是 string
format 必须出现一次，值是 string
frequency 必须出现一次，值是 string
spatialCoverage 必须出现一次，值是 string
```

注意，v0.1 对 `format` 和 `frequency` 还没有做枚举限制。

也就是说，在 v0.1 中：

```text
format 只要求是字符串，不强制必须等于 JSON；
frequency 只要求是字符串，不强制必须等于 hourly。
```

这些更严格的取值限制会在 v0.2 加入。

### 5.3 ontology 和 SHACL 的区别

这里很容易混淆，所以汇报时可以特别解释：

```text
ontology 说明字段是什么意思；
SHACL 说明字段是否合格。
```

比如 ontology 里说：

```text
be:providerName 的 range 是 xsd:string。
```

这是一种语义声明，表示这个属性预期是字符串。

SHACL 里说：

```text
providerName minCount = 1, maxCount = 1, datatype = xsd:string。
```

这才是可以被 validator 执行的验证规则。

所以，两者是互补关系：

| 文件 | 作用 |
|---|---|
| ontology | 定义模型语义，便于理解和复用。 |
| SHACL shapes | 定义机器可执行的合规检查。 |

## 6. `data-product-valid.jsonld`：一个最小合格实例

文件位置：

```text
C_Semantic_Treehouse/model/v0.1/data-product-valid.jsonld
```

这个文件给出了一个符合 v0.1 模型的 metadata 样例：

```json
{
  "@context": "data-product-context.jsonld",
  "@id": "https://w3id.org/dssc-demo/building-energy/data-product/building-energy-hourly-v1",
  "@type": "DataProductMetadata",
  "datasetId": "building-energy-hourly-v1",
  "providerName": "Energy Data Provider Ltd.",
  "format": "JSON",
  "frequency": "hourly",
  "spatialCoverage": "Shenzhen demo district",
  "conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.1"
}
```

### 6.1 `@context`

```json
"@context": "data-product-context.jsonld"
```

这表示当前 JSON-LD 文件使用同目录下的 context 文件来解释字段含义。

没有 context 时，`datasetId`、`providerName` 只是普通 JSON key。有了 context 后，它们就可以映射到正式 RDF 属性。

### 6.2 `@id`

```json
"@id": "https://w3id.org/dssc-demo/building-energy/data-product/building-energy-hourly-v1"
```

这是当前 metadata 实例的全局标识符。它让这个 data product metadata 成为一个可以被引用的 RDF 资源。

### 6.3 `@type`

```json
"@type": "DataProductMetadata"
```

结合 context，这会被解释为：

```text
be:DataProductMetadata
```

因此 SHACL validator 可以知道这个节点应该被 `be:DataProductMetadataShape-v0_1` 检查。

### 6.4 五个业务字段

样例中提供了 v0.1 要求的五个字段：

| 字段 | 样例值 | 解释 |
|---|---|---|
| `datasetId` | `building-energy-hourly-v1` | 数据产品 ID。 |
| `providerName` | `Energy Data Provider Ltd.` | 数据提供方。 |
| `format` | `JSON` | 数据格式。 |
| `frequency` | `hourly` | 小时级频率。 |
| `spatialCoverage` | `Shenzhen demo district` | 深圳示范区域。 |

这些字段都满足 v0.1 SHACL shape 的要求：出现一次，并且是字符串。

### 6.5 `conformsTo`

```json
"conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.1"
```

这表示当前实例声明自己符合 v0.1 版本模型。

这个字段不会替代验证本身。它更像是 metadata 的版本声明：

```text
我声称自己是按照 v0.1 写的；
validator 仍然可以用 v0.1 shape 来实际检查我是否合格。
```

## 7. v0.1 的端到端读取方式

如果把四个文件串起来看，v0.1 的工作流是这样的：

### 第一步：ontology 定义概念

`building-energy-ontology.ttl` 定义：

```text
有一种东西叫 DataProductMetadata；
它是 dcat:Dataset 的子类；
它可以有 providerName、format、frequency、spatialCoverage 等属性。
```

### 第二步：context 解释 JSON 字段

`data-product-context.jsonld` 定义：

```text
JSON 里的 datasetId 是 dct:identifier；
JSON 里的 providerName 是 be:providerName；
JSON 里的 DataProductMetadata 是 be:DataProductMetadata。
```

### 第三步：valid example 提供实例

`data-product-valid.jsonld` 提供一个具体 metadata：

```text
building-energy-hourly-v1 是一个 DataProductMetadata；
它由 Energy Data Provider Ltd. 发布；
格式是 JSON；
频率是 hourly；
覆盖 Shenzhen demo district；
符合 v0.1。
```

### 第四步：SHACL 检查实例是否合格

`data-product-metadata-shapes.ttl` 检查：

```text
datasetId 是否存在？
providerName 是否存在？
format 是否存在？
frequency 是否存在？
spatialCoverage 是否存在？
这些字段是否都是单值 string？
```

如果都满足，v0.1 metadata 就是合格的。

## 8. v0.1 刻意没有做什么

v0.1 的价值不在于完整，而在于最小可用。因此它刻意没有做以下事情。

### 8.1 没有 `endpointUrl`

v0.1 还没有要求数据产品必须给出 API endpoint。

这是因为 v0.1 先关注 catalogue metadata 的最小描述；endpoint 是后续 data offering 和 API 接入更关心的字段，因此放到 v0.2。

### 8.2 没有 `unit`

v0.1 没有要求能耗单位。

这意味着 v0.1 还不能很好地支持数值解释和单位一致性检查。v0.2 加入 `unit = kWh` 后，才开始对单位进行治理。

### 8.3 没有 `temporalStart` 和 `temporalEnd`

v0.1 没有时间覆盖范围。

这让 v0.1 只能说明数据产品大致是什么，不能完整说明这个数据产品覆盖哪段时间。时间范围也会在 v0.2 变成必填。

### 8.4 没有 API record schema

v0.1 只描述 data product metadata，不描述 API 返回的一条能耗读数。

API payload 层面的 `EnergyReadingRecord` 会在 v0.3 出现。

### 8.5 没有 invalid example

v0.1 只提供 valid example，没有专门的 invalid example。

这也符合 v0.1 的定位：它主要用于建立 baseline。到 v0.2 时，模型约束变严格，才加入一个故意失败的 metadata 样例，用于展示 validator 能发现问题。

## 9. v0.1 的设计特点

### 9.1 Minimal

v0.1 只保留五个字段，避免一开始就把模型做得过大。

这对课程项目或 demo 很重要，因为模型太复杂会让后续验证、汇报和跨组交付变得难以控制。

### 9.2 Standards-aligned

v0.1 使用了 DCAT 和 DCTERMS：

| 本地设计 | 标准对齐 |
|---|---|
| `be:DataProductMetadata` | `rdfs:subClassOf dcat:Dataset` |
| `datasetId` | `dct:identifier` |
| `conformsTo` | `dct:conformsTo` |

这说明项目不是只写一个本地 JSON 格式，而是在尽量接入已有语义标准。

### 9.3 Version-aware

v0.1 有明确版本 IRI：

```text
https://w3id.org/dssc-demo/building-energy/v0.1
```

样例中也通过 `conformsTo` 指向这个版本。

这样后续出现 v0.2 和 v0.3 时，不同文件可以清楚声明自己遵循哪个模型版本。

### 9.4 Human-readable

ontology 中每个本地类和属性都有 `rdfs:label` 与 `rdfs:comment`。

这对研讨和项目交付很有帮助，因为别人不需要猜 `be:frequency` 是什么意思，可以直接读注释理解。

## 10. 研讨时可以怎么讲

介绍 v0.1 时，可以按下面这段逻辑讲：

```text
v0.1 是 C 组语义模型的 baseline。
它先定义一个 DataProductMetadata 类，并把它对齐到 DCAT 的 Dataset。
然后它要求每个数据产品至少提供 datasetId、providerName、format、frequency 和 spatialCoverage。
这些字段通过 JSON-LD context 映射到 RDF 语义属性，再由 SHACL shape 检查是否必填、是否为单值字符串。
所以 v0.1 的重点不是字段多，而是建立了一套完整的语义建模闭环：ontology 定义含义，context 连接 JSON，SHACL 执行验证，valid example 提供可运行样例。
```

如果要用一句话总结：

```text
v0.1 把建筑能耗数据产品的最小 metadata 从普通 JSON 提升成了可解释、可验证、可版本化的语义资源。
```

## 11. 适合现场打开的文件顺序

如果现场要带大家看代码，建议按这个顺序打开：

1. `data-product-valid.jsonld`

   先让大家看到一个普通 JSON-LD metadata 长什么样。

2. `data-product-context.jsonld`

   再解释 JSON 字段如何映射到 RDF 语义。

3. `building-energy-ontology.ttl`

   然后看这些语义词汇在哪里被定义。

4. `data-product-metadata-shapes.ttl`

   最后看 validator 如何判断这个 metadata 是否合格。

这个顺序对听众比较友好，因为它从“看得懂的样例”出发，再逐步进入语义模型和验证规则。

## 12. v0.1 和后续版本的关系

v0.1 是后续版本的基础：

| 版本 | 在 v0.1 基础上做了什么 |
|---|---|
| v0.2 | 增加 `endpointUrl`、`unit`、`temporalStart`、`temporalEnd`，并加入枚举约束和 invalid example。 |
| v0.3 | 保留 v0.2 metadata 合同，再增加 `EnergyReadingRecord`、record SHACL、JSON Schema 和 OpenAPI fragment。 |

因此，v0.1 可以理解为项目的第一层语义地基：

```text
v0.1: 描述一个 data product 是什么
v0.2: 描述一个 data product 怎样才适合 onboarding validation
v0.3: 描述 API 返回的数据记录应该长什么样
```

