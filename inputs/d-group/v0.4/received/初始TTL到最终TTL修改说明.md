# 初始 TTL 到最终 TTL 的修改说明


最终版继续使用原始 metadata 的字段路径：`dcat:Dataset`、`ex:datasetId`、`dct:title`、`ex:providerName`、`dcat:endpointURL`、`dct:format`、`ex:unit`、`dct:spatial`、`ex:temporalStart`、`ex:temporalEnd`。原始 metadata 无需改字段即可验证。

## Dataset 数量规则的实现修正

最终版删除了先前存在 `$this` 预绑定问题的聚合子查询，改为直接检测两种不合规情况：

- 没有 `dcat:Dataset`；
- 存在两个不同的 `dcat:Dataset`。

本次数量规则修复未改动原有字段路径、namespace、metadata 结构或其他字段约束。

| 修改项 | 初始 TTL | 最终 TTL | 修复效果 |
|---|---|---|---|
| Dataset 数量 | 无全图数量约束 | 新增 `DatasetCardinalityShape`，使用 `BIND + NOT EXISTS + EXISTS` 检查数量 | 0 个或 2 个及以上 Dataset 均 FAIL；恰好 1 个才可通过 |
| Dataset 节点类型 | 未限制 | 新增 `sh:nodeKind sh:IRI` | 匿名 Dataset（blank node）FAIL |
| datasetId、title、providerName、spatial | 仅检查字符串类型 | 增加 `sh:minLength 1` 和 `sh:pattern "\\S"` | 空字符串、纯空格和 Tab 等无意义值 FAIL |
| frequency | 未检查 | 新增 `dct:accrualPeriodicity`：必填、单值、`sh:in ("hourly")` | 缺失、`daily`、大小写不一致或多值均 FAIL |
| unit | `sh:hasValue "kWh"`，可同时混入 `MWh` | 改为 `minCount + maxCount + datatype + sh:in ("kWh")` | `kWh` 与 `MWh` 同时存在时 FAIL |
| format | `sh:hasValue "application/json"`，可同时混入其他格式 | 改为 `minCount + maxCount + datatype + sh:in ("application/json")` | `application/json` 与 `text/csv` 同时存在时 FAIL |
| spatial、temporalStart、temporalEnd | 没有单值限制 | 增加 `sh:maxCount 1` | 同一字段的多个冲突值 FAIL |
| endpoint URL | 仅要求 IRI | 增加 `sh:pattern "^https://"`，并保留单值和 IRI 检查 | HTTP、普通字符串、多个 endpoint 均 FAIL |
| 时间范围关系 | 只检查两个字段是否为日期 | 新增 `TemporalOrderShape` 的 SPARQL 约束 | `temporalStart > temporalEnd` 时 FAIL |
| description | 未声明 | 新增可选字段规则：最多一个 `xsd:string` | 未填写可通过；多值或非字符串 FAIL |
| license | 未声明 | 新增可选字段规则：最多一个 HTTPS IRI | 未填写可通过；HTTP、普通字符串或多值 FAIL |
| profile 外字段 | 未限制 | 新增 `DatasetClosedShape`、`sh:closed true` | 未声明属性产生 `Warning`，由 ITB Test Case 映射为 `INAPPLICABLE` |
| 验证报告定位 | 所有规则为匿名 PropertyShape | 改为命名 Shape，并增加 `sh:name`、`sh:severity`、`sh:message` | D 组可依据 source shape、path、severity 和 message 映射验证结果 |

## 原始样例验证结果

| 样例 | 最终 TTL 结果 |
|---|---:|
| `data-product-valid.jsonld` | PASS |
| `data-product-invalid.jsonld` | FAIL：缺少 `providerName`、`temporalEnd`，且 `unit = MWh` |
