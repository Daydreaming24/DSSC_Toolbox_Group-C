# Minimal Energy Data Product Scenario

这个场景是为当前 DSSC Toolbox 研究任务手动构建的轻量样例。目标不是模拟真实能源数据空间的全部复杂度，而是提供一组足够小、足够清楚、能被 4 个研究小组共同使用的材料。


可复用的官方材料包括：

- FIWARE Data Space Connector 的 Minimal Viable Dataspace 本地部署：https://github.com/FIWARE/data-space-connector
- Gaia-X Service Characteristics 的 sample credentials / instances：https://gaia-x.gitlab.io/technical-committee/service-characteristics-working-group/service-characteristics/
- Semantic Treehouse 的 SHACL output 示例：https://www.semantic-treehouse.nl/docs/wizard/shacl-output/
- SEMIC SHACL Validator 在线服务和 API：https://www.itb.ec.europa.eu/shacl/semic-shacl/upload

因此本目录构建一个最小可复用场景：**Building Energy Consumption Data Product**。

## 场景

一个能源数据提供方 `Energy Data Provider Ltd.` 想在 data space 中发布一个建筑小时级用电量数据产品；数据消费者可以发现该 offering，并在满足 trust / compliance 与 metadata validation 后访问数据。

## 参与方

| 角色 | 名称 | 作用 |
|---|---|---|
| Provider | Energy Data Provider Ltd. | 发布建筑能耗数据产品。 |
| Consumer | City Analytics Lab | 发现并申请访问数据，用于城市能耗分析。 |
| Data Space Authority | City Energy Data Space Authority | 设定语义、合规和验证规则。 |

## 数据产品

| 字段 | 值 |
|---|---|
| Data Product | Building Energy Consumption Dataset API |
| Dataset ID | `building-energy-hourly-v1` |
| Format | JSON |
| Frequency | hourly |
| Unit | kWh |
| Access mode | API / mock endpoint |
| License | CC-BY-4.0 for research demo |
| Spatial coverage | Shenzhen demo district |
| Temporal coverage | 2026-05-01 to 2026-05-02 |

## 文件说明

| 文件 | 用途 |
|---|---|
| `data/building-energy-sample.json` | mock API 返回数据，供 FIWARE / TNO 组模拟 data exchange。 |
| `metadata/data-product-valid.jsonld` | 合法 data product metadata，供 SEMIC / SHACL validation 使用。 |
| `metadata/data-product-invalid.jsonld` | 故意缺字段和错误单位的 metadata，用于 validation 失败案例。 |
| `shapes/building-energy-shapes.ttl` | 最小 SHACL shapes，定义必填字段和约束。 |
| `gaia-x/legal-participant.template.jsonld` | Gaia-X participant credential 学习模板，不保证直接通过官方 compliance。 |
| `gaia-x/service-offering.template.jsonld` | Gaia-X service offering credential 学习模板，不保证直接通过官方 compliance。 |
| `mock-api/openapi.yaml` | 一个极简 API 描述，供 connector 组包装为 data offering。 |
| `VALIDATION_GUIDE.md` | 样例一致性说明、预期验证结果和已知边界。 |

## 各小组如何使用

### A 组：FIWARE FDF / TNO TSG

使用：

- `mock-api/openapi.yaml`
- `data/building-energy-sample.json`
- `metadata/data-product-valid.jsonld`

任务：

1. 把 `Building Energy Consumption Dataset API` 当成 provider 的 data offering。
2. 用 mock API 或静态 JSON 代表真实数据源。
3. 在 FIWARE FDF 或 TNO TSG 中描述、发布、发现这个 offering。
4. 记录 provider、consumer、contract negotiation、transfer process 的关键步骤。

### B 组：Gaia-X Compliance Service + Registry

使用：

- `gaia-x/legal-participant.template.jsonld`
- `gaia-x/service-offering.template.jsonld`

任务：

1. 先把模板当成概念学习材料。
2. 对照 Gaia-X 官方 sample credentials 补齐真实 required fields。
3. 调用官方 Compliance Service 或 lab instance，观察成功/失败返回。
4. 说明 Registry 中 shapes、schemas、trust anchors 对验证结果的影响。

注意：这两个 template 是教学模板，不保证直接通过官方 Gaia-X compliance。真正验证时应基于官方 sample credentials 调整。

### C 组：Semantic Treehouse

使用：

- `shapes/building-energy-shapes.ttl`
- `metadata/data-product-valid.jsonld`

任务：

1. 在 Semantic Treehouse 中建立一个 `Building Energy Consumption` message model / vocabulary。
2. 先建模 data product metadata 字段：`datasetId`、`providerName`、`endpointUrl`、`format`、`frequency`、`unit`、`spatialCoverage`、`temporalStart`、`temporalEnd`。
3. 再把 mock data record 字段作为可选子模型：`buildingId`、`meterId`、`timestamp`、`energyKWh`、`unit`、`location`。
4. 研究如何生成或导出 SHACL。
5. 与本目录中的 `building-energy-shapes.ttl` 对比。

### D 组：ITB + SEMIC Validator

使用：

- `metadata/data-product-valid.jsonld`
- `metadata/data-product-invalid.jsonld`
- `shapes/building-energy-shapes.ttl`

任务：

1. 用 SHACL validator 验证 valid metadata 应通过。
2. 验证 invalid metadata 应失败。
3. 分析失败报告中的 focus node、path、message。
4. 设计如何把这一步纳入 ITB test suite。

## 最小集成目标

1. C 组定义数据产品语义模型和 SHACL shapes。
2. A 组把数据产品发布为 data offering。
3. B 组验证 provider / service offering 的 Gaia-X credential。
4. D 组验证 metadata 是否符合 semantic constraints。
5. 最终形成一个轻量 data space onboarding 流程：
   - 先有语义模型。
   - 再发布数据产品。
   - 再做 trust / compliance。
   - 最后做 conformance / validation。


