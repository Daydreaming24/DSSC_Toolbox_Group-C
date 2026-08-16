# v0.2 五个文件说明

v0.2 在 v0.1 的基础上加强了数据产品元数据的可验证性。它仍然描述“数据产品是什么、由谁提供以及如何获取”，还没有描述具体的建筑能耗读数。

与 v0.1 相比，v0.2 新增了 API 地址、能耗单位和时间覆盖范围，并对部分字段的取值提出了更严格的要求。目录中共有五个相互配合的文件。

## `building-energy-ontology.ttl`

这是 v0.2 的语义词汇表。它保留了 `DataProductMetadata` 类和 v0.1 的基础属性，又增加了 `endpointUrl`、`unit`、`temporalStart` 和 `temporalEnd`。

文件还声明 v0.2 的前一个版本是 v0.1，并把部分项目属性与 DCAT、Dublin Core 等标准词汇关联起来。它负责解释“这些概念和属性是什么意思”，不负责检查数据是否合格。

## `data-product-context.jsonld`

这是 JSON 字段与语义词汇之间的翻译表。它把 `datasetId`、`providerName`、`endpointUrl` 等易读字段映射到完整的 RDF 标识。

它还告诉 JSON-LD 处理工具：`endpointUrl` 是一个 IRI，而 `temporalStart` 和 `temporalEnd` 是日期。这样，普通 JSON 写法就能被正确转换成带有明确类型的 RDF 数据。

## `data-product-metadata-shapes.ttl`

这是 v0.2 的 SHACL 检查清单。一份合格的元数据必须包含九个字段：`datasetId`、`providerName`、`endpointUrl`、`format`、`frequency`、`unit`、`spatialCoverage`、`temporalStart` 和 `temporalEnd`。

每个字段都只能出现一次。除此之外，`endpointUrl` 必须是 IRI，两个时间字段必须是日期，`format` 必须是 `JSON`，`frequency` 必须是 `hourly`，`unit` 必须是 `kWh`。

这个文件负责判断“数据是否满足 v0.2 的接入要求”。

## `data-product-valid.jsonld`

这是一份能够通过 v0.2 验证的正例。它完整填写了九个必填字段，并通过 `conformsTo` 表明自己遵循 v0.2 模型。

这份文件展示了“合格的 v0.2 元数据应该怎样填写”，也可以作为验证工具的成功测试输入。

## `data-product-invalid.jsonld`

这是一份故意写错的反例。它缺少 `providerName` 和 `temporalEnd`，并把只能为 `kWh` 的 `unit` 写成了 `MWh`。

验证工具应当拒绝这份数据并报告相应错误。因此，它用来确认验证规则确实能够发现缺失字段和不允许的取值。

## 五个文件如何配合

可以把 ontology 看作词典，context 看作翻译表，SHACL shapes 看作检查清单，valid JSON-LD 看作合格样例，invalid JSON-LD 看作错误样例。

这五个文件共同形成一个简单的验证闭环：先定义语义和字段映射，再制定检查规则，最后分别用正例和反例确认规则能够接受正确数据、拒绝错误数据。
