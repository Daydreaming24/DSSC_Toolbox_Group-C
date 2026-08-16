# v0.1 四个文件说明

v0.1 用来描述一个建筑能耗数据产品的基本信息，例如数据集编号、提供方、数据格式、更新频率和覆盖区域。它关注的是“怎样说明这个数据产品”，还没有描述具体的建筑能耗读数。

这一版本包含四个相互配合的文件。它们分别负责定义词汇、连接 JSON 与语义模型、检查数据，以及提供示例。

## `building-energy-ontology.ttl`

这是语义词汇表。它说明模型中有哪些概念和属性，以及这些词汇的含义。

在 v0.1 中，它定义了 `DataProductMetadata` 这个核心类，以及 `providerName`、`format`、`frequency` 和 `spatialCoverage` 四个项目属性。它还声明了模型版本，并把 `DataProductMetadata` 与标准的 `dcat:Dataset` 概念关联起来。

这个文件负责解释“词是什么意思”，不负责判断某个字段是否必填。

## `data-product-context.jsonld`

这是 JSON 字段与 RDF 语义词汇之间的翻译表。它让人们可以继续使用简短、易读的 JSON 字段名，同时让机器知道每个字段对应的完整语义标识。

例如，`datasetId` 对应标准属性 `dct:identifier`，`providerName` 对应本项目定义的 `be:providerName`。

这个文件负责解释“JSON 字段对应哪个语义词汇”，不负责制定验证规则。

## `data-product-metadata-shapes.ttl`

这是 v0.1 的数据检查清单，使用 SHACL 编写。它规定一份合格的 `DataProductMetadata` 必须包含 `datasetId`、`providerName`、`format`、`frequency` 和 `spatialCoverage`。

这五个字段都必须出现一次，并且值必须是字符串。如果数据缺少字段、字段重复或类型不正确，验证工具就会报告错误。

这个文件负责判断“数据是否符合要求”。

## `data-product-valid.jsonld`

这是一份符合 v0.1 要求的示例数据。它描述了一个按小时更新的建筑能耗数据产品，并填写了提供方、格式和覆盖区域等信息。

文件通过 `@context` 使用前面的字段映射，并通过 `conformsTo` 表明自己遵循 v0.1 模型。它也可以作为 SHACL 验证的测试输入。

这个文件负责展示“合格的数据实际写成什么样”。

## 四个文件如何配合

可以把这四个文件理解为一套分工明确的材料：ontology 是词典，context 是翻译表，SHACL shapes 是检查清单，valid JSON-LD 是填写完成的合格样例。

因此，阅读 v0.1 时可以先用 ontology 理解概念，再用 context 理解 JSON 字段，接着查看 shapes 掌握合格条件，最后通过 valid JSON-LD 观察完整写法。
