# v0.3 十个文件说明

v0.3 是三个版本中最完整的一版。它保留了 v0.2 的数据产品元数据合同，同时新增了 API 返回的单条建筑能耗记录模型。因此，它既说明“数据产品怎样被描述”，也说明“数据产品实际返回的数据应该是什么样”。

目录中的十个文件可以

## 共同语义层

### `building-energy-ontology.ttl`

这是整个 v0.3 的语义词汇表。除了原有的 `DataProductMetadata`，它还定义了 `EnergyReadingRecord`、`Building` 和 `Meter`，以及建筑编号、仪表编号、时间、能耗值和地点等属性。

文件还把这些概念与 DCAT、SOSA、QUDT 和 Schema.org 等标准词汇关联起来。例如，能耗记录被视为一种 SOSA observation，仪表被视为一种 sensor。它负责统一解释元数据和能耗记录中的概念。

## 数据产品元数据层

### `data-product-context.jsonld`

这是元数据字段的 JSON-LD 翻译表。它把 `datasetId`、`endpointUrl`、`temporalStart` 等易读的 JSON 字段映射到完整的语义标识，并说明 URL 和日期等字段的类型。

### `data-product-metadata-shapes.ttl`

这是元数据的 SHACL 检查清单，基本延续 v0.2 的规则。它要求九个元数据字段完整且单值，并检查 URL、日期、格式、频率和单位是否符合要求。

### `data-product-valid.jsonld`

这是一份能够通过元数据验证的正例。它描述数据产品的提供方、API 地址、格式、频率、单位、空间范围和时间范围，并声明自己遵循 v0.3。

## 能耗记录与 API 层

### `energy-reading-record-context.jsonld`

这是能耗记录字段的 JSON-LD 翻译表。它解释 `buildingId`、`meterId`、`timestamp`、`energyKWh`、`unit` 和 `location` 等字段的语义，并把时间标记为日期时间、能耗值标记为十进制数。

### `energy-reading-record-shapes.ttl`

这是能耗记录的 SHACL 检查清单。每条记录必须包含建筑编号、仪表编号、时间、能耗值、单位和地点；能耗值不能小于零，单位必须是 `kWh`，时间必须是正确的日期时间。

### `energy-reading-record-valid.jsonld`

这是一条合格的能耗记录正例。它表示某栋建筑的某个仪表在指定时间记录了 `12.4 kWh`，并给出了城市和行政区。

### `energy-reading-record-invalid.jsonld`

这是一条故意写错的反例。它缺少 `meterId`，时间格式错误，把能耗值写成字符串，并使用了不允许的 `MWh` 单位。它用来确认验证工具能够识别错误记录。

### `energy-reading-record.schema.json`

这是面向普通 JSON API 数据的结构检查规则。它同样要求六个核心字段，检查时间、非负数值和固定单位，并进一步要求 `location` 中包含 `city` 和 `district`。它还禁止未定义的额外字段。

SHACL 主要检查转换成 RDF 后的语义数据，而 JSON Schema 可以直接检查普通 JSON 请求或响应。

### `openapi-fragment.yaml`

这是 API 合同片段。它描述了 `GET /energy/buildings/hourly` 接口、可使用的查询参数，以及成功响应中的能耗记录数组。

它让前面的能耗记录结构进入 API 文档，使接口实现方和数据使用方能够按照同一套字段约定工作。

## 十个文件如何配合

ontology 统一定义概念，两个 context 分别翻译元数据和能耗记录，两个 SHACL shapes 检查 RDF 语义数据，JSON Schema 检查普通 JSON 结构，OpenAPI 描述实际接口，正例和反例则用于验证这些规则是否按预期工作。

因此，v0.3 把“语义定义、数据验证和 API 交付”连接成了一套完整但轻量的合同。
