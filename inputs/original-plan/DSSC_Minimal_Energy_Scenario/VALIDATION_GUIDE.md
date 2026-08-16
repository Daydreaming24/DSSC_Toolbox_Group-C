# Validation Guide

本文件说明场景包中样例文件之间的对应关系、预期验证结果和已知边界。

## 1. Data product metadata validation

用于 D 组的最小 SHACL 验证：

| 文件 | 角色 | 预期 |
|---|---|---|
| `metadata/data-product-valid.jsonld` | 合法 data product metadata | 应通过 `shapes/building-energy-shapes.ttl`。 |
| `metadata/data-product-invalid.jsonld` | 故意错误 metadata | 应失败。 |
| `shapes/building-energy-shapes.ttl` | SHACL shapes | 检查 data product metadata 的必填字段和基础约束。 |

## 2. Valid metadata 为什么应通过

`data-product-valid.jsonld` 满足以下约束：

- `@type` 是 `dcat:Dataset`，会命中 `sh:targetClass dcat:Dataset`。
- `datasetId` 存在且为字符串。
- `dct:title` 存在且为字符串。
- `providerName` 存在且为字符串。
- `endpointUrl` 在 JSON-LD context 中声明为 `@id`，展开后是 IRI，可满足 `sh:nodeKind sh:IRI`。
- `format` 是 `application/json`。
- `unit` 是 `kWh`。
- `spatialCoverage` 存在。
- `temporalStart` 和 `temporalEnd` 都存在，且声明为 `xsd:date`。

## 3. Invalid metadata 预期失败点

`data-product-invalid.jsonld` 故意包含以下问题：

| 问题 | 对应 SHACL 约束 |
|---|---|
| 缺少 `providerName` | `ex:providerName sh:minCount 1` |
| `unit` 是 `MWh` 而不是 `kWh` | `ex:unit sh:hasValue "kWh"` |
| 缺少 `temporalEnd` | `ex:temporalEnd sh:minCount 1` |

这三个错误足够用于教学：它们分别覆盖必填字段缺失、枚举值不符合、时间范围不完整。

## 4. Metadata 层和 record 层不要混淆

本场景故意分成两层：

| 层级 | 文件 | 作用 |
|---|---|---|
| Data product metadata | `metadata/*.jsonld` | 描述数据产品本身，用于 SHACL / SEMIC / ITB validation。 |
| API record payload | `data/building-energy-sample.json` | 模拟 API 返回的业务数据，用于 connector / mock API demo。 |

第一轮研究只要求验证 data product metadata。`building-energy-sample.json` 中的 `buildingId`、`meterId`、`timestamp`、`energyKWh` 等 record 字段由 OpenAPI schema 约束，不强制纳入 SHACL。

如果后续想扩展，可以新增第二个 SHACL shape 或 JSON Schema 来验证 record payload。

## 5. Gaia-X templates 的边界

`gaia-x/*.template.jsonld` 是学习模板，不是可直接通过官方 Gaia-X Compliance Service 的最终 credential。

原因：

- 没有真实可解析的 DID document。
- 没有 cryptographic proof。
- 没有保证满足当前 Gaia-X Trust Framework 的全部 required fields。
- 没有绑定真实 trust anchor。

B 组应把这些模板当作结构理解材料，然后对照 Gaia-X 官方 sample credentials 调整，再调用官方 compliance instance 观察结果。

## 6. OpenAPI mock endpoint 的边界

`mock-api/openapi.yaml` 描述的是研究用 mock API，不代表真实服务已经部署。

A 组可以选择三种方式使用它：

1. 只把它作为 data offering 的 API contract。
2. 用任意 mock server 根据 OpenAPI 启动本地 endpoint。
3. 用静态 JSON 文件 `data/building-energy-sample.json` 代替真实 endpoint。

第一轮研究只要求能解释如何包装为 data offering，不要求生产级 API 服务。
