# DSSC Toolbox 小组研究任务设计方案

本文给出一个可执行的研究方案，围绕 4 个方向展开：

1. FIWARE FDF / TNO TSG：data exchange 与 connector。
2. Gaia-X Compliance Service + Registry：trust / compliance。
3. Semantic Treehouse：semantic model governance。
4. Interoperability Test Bed，SEMIC Validator 作为子任务：conformance / validation。

## 一、总体目标

研究结束时，小组应交付：

1. 一套 data space 工具链架构图，说明各工具的位置和关系。
2. 每个方向一份技术调研报告，包含源码结构、核心概念、部署方式、API/UI 流程、典型用例、优缺点。
3. 每个方向一个最小可运行 demo 或可复现实验。
4. 一个集成场景 demo，串起 semantic model、connector、compliance 和 validation。
5. 一份最终对比矩阵，说明各工具适合什么研究问题、不适合什么场景。

## 二、统一研究场景

### 2.1 场景选择

已检查现成样例。官方资料能覆盖局部需求，但没有一个单一、轻量、现成的场景能同时覆盖本项目的 4 个方向：

- FIWARE FDF 有 Minimal Viable Dataspace / local deployment 样例。
- Gaia-X 有 sample credentials / service characteristics / compliance instance。
- Semantic Treehouse 有 SHACL output 和 message model 示例。
- SEMIC Validator 有在线和 API validation 服务。

因此本方案采用手动构建的最小场景包：

`D:\DSSC_Minimal_Energy_Scenario`

配套说明：

- `D:\DSSC_Toolbox_Optimized_Scenario.md`
- `D:\DSSC_Minimal_Energy_Scenario\README.md`
- `D:\DSSC_Minimal_Energy_Scenario\VALIDATION_GUIDE.md`

### 2.2 场景名称

**Building Energy Consumption Data Product**

简要描述：

> Provider `Energy Data Provider Ltd.` publishes an hourly building energy data product in the data space. Consumer `City Analytics Lab` discovers the offering and requests access. The data space authority requires shared semantic metadata, basic Gaia-X trust/compliance description, and metadata validation.


### 2.3 场景角色

| 角色 | 名称 | 说明 |
|---|---|---|
| Provider | Energy Data Provider Ltd. | 发布建筑能耗数据产品。 |
| Consumer | City Analytics Lab | 发现并申请访问数据。 |
| Data Space Authority | City Energy Data Space Authority | 制定 semantic、compliance 和 validation 规则。 |

### 2.4 数据产品定义

| 属性 | 值 |
|---|---|
| Data Product | Building Energy Consumption Dataset API |
| Dataset ID | `building-energy-hourly-v1` |
| Format | JSON |
| Frequency | hourly |
| Unit | kWh |
| Endpoint | `https://api.example.org/energy/buildings/hourly` |
| License | CC-BY-4.0 for research demo |
| Spatial Coverage | Shenzhen demo district |
| Temporal Coverage | 2026-05-01 to 2026-05-02 |

### 2.5 场景包文件

| 文件 | 用途 |
|---|---|
| `README.md` | 场景说明和分组使用方式。 |
| `VALIDATION_GUIDE.md` | 样例一致性、预期验证结果和边界说明。 |
| `data/building-energy-sample.json` | mock API 返回数据。 |
| `mock-api/openapi.yaml` | 极简 API 描述，供 connector 组包装 data offering。 |
| `metadata/data-product-valid.jsonld` | Valid data product metadata for SHACL validation. |
| `metadata/data-product-invalid.jsonld` | 故意构造的错误 metadata，用于失败案例。 |
| `shapes/building-energy-shapes.ttl` | 最小 SHACL constraints。 |
| `gaia-x/legal-participant.template.jsonld` | Gaia-X LegalParticipant 学习模板。 |
| `gaia-x/service-offering.template.jsonld` | Gaia-X ServiceOffering 学习模板。 |

## 三、分组安排

| 小组 | 负责方向 | 核心工具 | 最终交付 |
|---|---|---|---|
| A 组 | Data exchange / connector | FIWARE FDF / TNO TSG | Connector 流程图、部署记录、发布/消费 demo。 |
| B 组 | Trust / compliance | Gaia-X Compliance Service + Registry | Gaia-X compliance flow and minimal credential demo. |
| C 组 | Semantic model governance | Semantic Treehouse | 一个 data product metadata semantic model。 |
| D 组 | Conformance / validation | ITB + SEMIC SHACL Validator | 一个 SHACL validation demo 和 ITB test suite 设计。 |

## 四、统一研究问题

每个小组都必须回答：

1. 这个工具在 data space 架构中属于哪一层？
2. 它解决的问题是什么，不解决的问题是什么？
3. 它的输入是什么，输出是什么？
4. 它依赖哪些标准或协议？
5. 它和其他工具如何配合？
6. 它是否适合本地部署？部署成本在哪里？
7. 它是否适合二次开发？源码结构是否清晰？
8. 它的成熟度、维护活跃度、license 风险如何？
9. 如果真实 data space 使用它，最大风险是什么？

## 五、第 0 阶段：准备和分工

时间：0.5-1 天。

任务：

1. 确认每组负责人。
2. 通读 `D:\DSSC_Minimal_Energy_Scenario\README.md`。
3. 阅读 `D:\DSSC_Minimal_Energy_Scenario\VALIDATION_GUIDE.md`，理解样例边界。
4. 建立共享仓库或共享文件夹。
5. 统一记录模板：`tool-overview.md`、`deployment-notes.md`、`api-notes.md`、`demo-steps.md`、`issues-and-risks.md`。
6. 统一 citation 规则：所有结论必须附官网、源码、文档或实际实验截图。

交付：小组分工表、工具链接表、统一研究模板。

## 六、A 组：FIWARE FDF / TNO TSG

### A1. 目标

理解 data space connector 如何支持数据发布、发现、访问协商和数据交换。

建议主次分工：

- 主线：FIWARE FDF，做端到端 data exchange 流程。
- 辅线：TNO TSG，做 Dataspace Protocol / participant agent 机制分析。

### A2. 具体任务

1. 阅读 FIWARE FDF 文档和本地部署文档。
2. 画出 FIWARE FDF 的组件图：connector / control plane、data plane、catalogue、identity / trust component、provider / consumer。
3. 尝试本地部署最小环境，失败也要保留日志和原因。
4. 创建最小 data offering：
   - 名称：Building Energy Consumption Dataset API
   - provider：Energy Data Provider Ltd.
   - endpoint contract：`D:\DSSC_Minimal_Energy_Scenario\mock-api\openapi.yaml`
   - mock data：`D:\DSSC_Minimal_Energy_Scenario\data\building-energy-sample.json`
   - metadata：`D:\DSSC_Minimal_Energy_Scenario\metadata\data-product-valid.jsonld`
5. 模拟 consumer 发现并请求数据。
6. 记录 contract negotiation 或 transfer process 的关键状态。
7. 对比 TNO TSG：是否更接近协议研究、与 FIWARE FDF 的组件边界有什么不同、哪个更适合作为教学 demo。

### A3. 最小 demo

至少完成一项：

- Provider 发布一个 data offering，consumer 能看到 metadata。
- Consumer 发起访问请求，系统产生 negotiation / transfer 状态。
- 用 mock endpoint 或静态 JSON 完成一次数据访问说明。

### A4. 输出

- `A_connector_architecture.md`
- `A_fiware_deployment_notes.md`
- `A_tno_tsg_comparison.md`
- `A_data_exchange_demo.md`
- 一张 provider-consumer 流程图。

## 七、B 组：Gaia-X Compliance Service + Registry

### B1. 目标

理解 Gaia-X 如何把 trust / compliance 转化为机器可执行的验证流程。

这组不要求一开始完整本地部署 Gaia-X stack，优先使用官方 stable / lab instance 调用 API，再分析源码和 Registry 的作用。

### B2. 具体任务

1. 阅读 Gaia-X Trust Framework 中关于 Self-Description、Credential、Compliance Service、Registry 的部分。
2. 解释 Verifiable Credential、Verifiable Presentation、Self-Description、SHACL shape、Trust Anchor、public key、revocation。
3. 找到 Compliance Service 的 API 入口和请求格式。
4. 阅读场景包中的模板：
   - `D:\DSSC_Minimal_Energy_Scenario\gaia-x\legal-participant.template.jsonld`
   - `D:\DSSC_Minimal_Energy_Scenario\gaia-x\service-offering.template.jsonld`
5. 明确说明：这两个模板是学习模板，没有 proof，不保证直接通过官方 compliance。
6. 基于 Gaia-X 官方 sample credentials 准备一个可提交的最小 participant credential 或 service offering credential。
7. 调用 Compliance Service 做验证。
8. 观察验证失败时的错误信息，记录缺失字段或格式错误。
9. 研究 Registry 在验证过程中提供什么：shapes、schemas、trust anchors、valid / revoked keys。
10. 输出 Gaia-X compliance flow。

### B3. 最小 demo

必须完成：

- 提交一个故意不完整 credential，得到失败原因。
- 提交一个尽量完整的最小 credential，得到验证结果或更具体的失败原因。
- 说明 Registry 中哪些 shapes / trust anchors 影响验证结果。

### B4. 输出

- `B_gaiax_concepts.md`
- `B_compliance_api_demo.md`
- `B_registry_role_analysis.md`
- `B_gaiax_validation_flow.md`

## 八、C 组：Semantic Treehouse

### C1. 目标

理解 data space 中共同语义模型如何被定义、维护、发布和治理。

### C2. 具体任务

1. 阅读 Semantic Treehouse 文档。
2. 部署或使用可访问实例，确认基本 UI / API 功能。
3. 为统一场景设计两个层次的最小 semantic model：
   - Data Product Metadata：描述数据产品本身，用于 catalogue、connector offering 和 SHACL validation。
   - Energy Reading Record：描述 API 返回的一条能耗读数，用于 mock API 和 OpenAPI schema。
4. Data Product Metadata 字段：datasetId、providerName、endpointUrl、format、frequency、unit、spatialCoverage、temporalStart、temporalEnd。
5. Energy Reading Record 字段：buildingId、meterId、timestamp、energyKWh、unit、location。
6. 研究模型版本化：v0.1 metadata 基础字段；v0.2 增加 unit、endpointUrl、temporal coverage 约束；v0.3 可选扩展 record payload schema。
7. 研究是否能导出 RDF / JSON-LD / SHACL / documentation。
8. 将导出结果与 `D:\DSSC_Minimal_Energy_Scenario\shapes\building-energy-shapes.ttl` 对比。
9. 把 metadata 模型交给 D 组做 SHACL validation。
10. 把 metadata 字段交给 A 组作为 data offering metadata 的共同约束。

### C3. 最小 demo

必须完成：

- 创建一个最小 vocabulary / semantic model。
- 展示模型版本变化。
- 导出或记录可被 validator 使用的表示形式。

### C4. 输出

- `C_semantic_model_design.md`
- `C_semantic_treehouse_usage.md`
- `C_model_versioning_demo.md`
- `C_export_for_validation.md`
- 一张 metadata model 与 record model 的关系图。

## 九、D 组：Interoperability Test Bed + SEMIC Validator

### D1. 目标

理解 data space 中 conformance testing 和 validation 如何执行。

主线是 ITB，SEMIC SHACL Validator 作为子任务。研究时不要只停留在在线上传文件，而要理解 validator 如何被嵌入测试流程。

### D2. 具体任务

1. 阅读 ITB overview 和 installation / testing guide。
2. 解释 ITB 的核心概念：test suite、test case、conformance statement、actor、system under test、validation service。
3. 阅读 `D:\DSSC_Minimal_Energy_Scenario\VALIDATION_GUIDE.md`。
4. 使用 SEMIC SHACL Validator 或其他 SHACL validator 验证：
   - `D:\DSSC_Minimal_Energy_Scenario\metadata\data-product-valid.jsonld`
   - `D:\DSSC_Minimal_Energy_Scenario\metadata\data-product-invalid.jsonld`
   - `D:\DSSC_Minimal_Energy_Scenario\shapes\building-energy-shapes.ttl`
5. 解释 valid case 为什么应通过。
6. 解释 invalid case 为什么应失败，至少指出：缺少 `providerName`、`unit` 是 `MWh` 而不是 `kWh`、缺少 `temporalEnd`。
7. 研究如何把 validator 纳入 ITB test suite。
8. 设计 data space onboarding validation 流程：participant 提交 metadata，validator 检查 metadata，ITB 输出测试结果。

### D3. 最小 demo

必须完成：

- Valid metadata 通过 SHACL validation。
- Invalid metadata 被 validator 拒绝，并解释错误。
- 画出如何用 ITB 组织更完整的 conformance testing。

进阶：本地部署 ITB，创建简单 test suite，调用 validator 作为测试步骤。

### D4. 输出

- `D_itb_overview.md`
- `D_semic_shacl_validation_demo.md`
- `D_validation_error_analysis.md`
- `D_itb_test_suite_design.md`

## 十、集成任务

4 个小组完成各自最小 demo 后，需要做一次集成。

### 集成目标

构建一个小型 data space 工具链故事：

1. C 组定义 Building Energy Consumption semantic model。
2. D 组验证 metadata 是否符合模型约束。
3. A 组用该模型发布一个 data offering。
4. B 组为 participant 或 service offering 准备 Gaia-X credential 并验证。

### 集成输入

- C 组：semantic model / fields / shapes。
- A 组：data offering metadata / OpenAPI / mock data。
- B 组：credential / compliance result。
- D 组：validation report。

### 集成输出

- `integration_demo.md`
- `integration_architecture.png` 或 Mermaid 图。
- `final_tool_comparison_matrix.md`
- `remaining_issues.md`

## 十一、最终报告结构

建议最终报告使用以下结构：

1. Executive Summary
2. Data Space 工具链总览
3. 统一研究场景
4. 工具一：FIWARE FDF / TNO TSG
5. 工具二：Gaia-X Compliance Service + Registry
6. 工具三：Semantic Treehouse
7. 工具四：Interoperability Test Bed + SEMIC Validator
8. 集成实验
9. 对比矩阵
10. 风险和限制
11. Future work

## 十二、对比矩阵模板

| 维度 | FIWARE FDF / TNO TSG | Gaia-X Compliance + Registry | Semantic Treehouse | ITB + SEMIC Validator |
|---|---|---|---|---|
| data space 层级 | Connector / data exchange | Trust / compliance | Vocabulary / semantic governance | Conformance / validation |
| 是否负责数据交换 | 是 | 否 | 否 | 否 |
| 是否负责 compliance | 部分相关 | 是 | 否 | 部分相关 |
| 是否负责 semantic model | 否 | 使用 semantic rules | 是 | 验证 semantic rules |
| 是否适合本地部署 | 中等难度 | 中高难度 | 中等难度 | 中等难度 |
| 最小 demo 难度 | 中 | 中高 | 中 | 低到中 |
| 学术研究价值 | 高 | 高 | 高 | 高 |
| 工程复现风险 | 中高 | 中高 | 中 | 中 |

## 十三、时间安排建议

项目周期预计为 6 周：

| 周次 | 任务 |
|---|---|
| 第 1 周 | 读文档、跑 quickstart、画初版架构图。 |
| 第 2 周 | 完成每组最小 demo。 |
| 第 3 周 | 深入源码和 API，记录关键流程。 |
| 第 4 周 | 做 valid / invalid case、错误分析、风险分析。 |
| 第 5 周 | 4 组集成，串起统一场景。 |
| 第 6 周 | 整理最终报告、demo、展示材料。 |

如果项目周期只有 3 周：

| 周次 | 任务 |
|---|---|
| 第 1 周 | 快速读文档，完成概念图和最小部署尝试。 |
| 第 2 周 | 每组完成最小 demo 和问题记录。 |
| 第 3 周 | 做集成故事、最终报告和展示。 |

## 十四、风险控制

### 部署风险

部分工具部署较重，尤其是 FIWARE FDF、Gaia-X stack、ITB。不要把所有时间都花在完整生产部署上。

控制方式：优先使用官方 demo / online instance / lab instance；本地部署只要求最小可运行；如果部署失败，必须保留失败日志和原因分析。

### 概念风险

Gaia-X 和 semantic validation 的概念门槛较高。

控制方式：B 组先写概念词典；D 组先做简单 SHACL example；C 组提供最小模型，first pass 避免复杂 ontology。

### 集成风险

4 组工具未必能天然无缝集成。

控制方式：集成目标是流程级集成，不强求所有工具自动互调；允许用文件和 API 调用连接流程；重点展示数据如何从 semantic model 到 offering，再到 compliance 和 validation。

## 十五、最终验收标准

项目完成时，至少应满足：

1. 每个方向都有一份 5-10 页技术说明。
2. 每个方向都有一个最小 demo 或可复现实验。
3. 至少有 2 个实际 API 调用、部署截图或 validation report。
4. 至少有 1 个 valid case 和 1 个 invalid case。
5. 能用一张图解释 4 类工具在 data space 中如何配合。
6. 能清楚说明每个工具不负责什么。

如果能额外完成以下内容，则认为研究质量较高：

1. 成功本地部署至少 2 个工具。
2. 完成一个跨组集成 demo。
3. 对源码模块做出结构分析。
4. 总结出真实落地时的成本、风险和替代方案。
