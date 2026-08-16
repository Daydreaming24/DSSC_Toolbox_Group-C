# Phase 07：报告、图示与跨组交接契约

## 1. 本阶段解决的问题

Phase 07 是把前面六个阶段的技术产物整理成“可讲、可交接、可展示”的阶段。

在 Phase 01 到 Phase 06 中，项目已经有：

- 版本化模型文件。
- 验证脚本和报告。
- SPARQL 能力问题。
- SSSOM 映射和质量指标。
- governance 文档和 provenance。
- Semantic Treehouse 本地部署证据。

但这些文件分散在不同目录中。Phase 07 的任务是把它们整合成：

1. 两张 Mermaid 图。
2. 四份 C 组核心报告。
3. A/D 组交接文档。
4. AI-assisted but human-governed modeling 说明。

`prompts/phase-07-reports-diagrams-and-handoff-contracts.md` 的目标是：

```text
Write the required C Group reports and cross-group handoff contracts using the generated artifacts.
```

## 2. 新增或重写的文件

根据 `C_Semantic_Treehouse/PHASE_7_SUMMARY.md`，本阶段创建或修改：

| 文件 | 作用 |
|---|---|
| `diagrams/metadata-record-model.mmd` | 展示 provider、metadata、model version、SHACL、endpoint、API record、A/D 组关系。 |
| `diagrams/semantic-governance-flow.mmd` | 展示模型变更、审查、发布、导出、验证、交接、监控和废弃流程。 |
| `C_semantic_model_design.md` | 完整模型设计报告。 |
| `C_semantic_treehouse_usage.md` | Semantic Treehouse 使用和证据报告。 |
| `C_model_versioning_demo.md` | 版本演进说明。 |
| `C_export_for_validation.md` | 导出和验证交接说明。 |
| `handoff/handoff-to-A-offering-metadata.md` | 给 A 组的 data offering metadata contract。 |
| `handoff/handoff-to-D-shacl-validation.md` | 给 D 组的 SHACL validation contract。 |
| `docs/ai-assisted-human-governed-semantic-modeling.md` | AI 辅助但人类治理的建模说明。 |

这些文件把项目从“工程包”变成“展示包”。

## 3. 关系图：metadata 与 record model

`diagrams/metadata-record-model.mmd` 是项目关系图。它的核心节点包括：

```text
Provider: Energy Data Provider Ltd.
Data Product Metadata building-energy-hourly-v1
Semantic Model Version https://w3id.org/dssc-demo/building-energy/v0.3
SHACL Validation DataProductMetadataShape-v0_3
DCAT DataService Endpoint https://api.example.org/energy/buildings/hourly
Energy Reading Record buildingId, meterId, timestamp, energyKWh
A Group Data Offering Metadata
D Group SHACL / ITB Validation
```

图中最重要的关系是：

```text
Metadata -->|"dct:conformsTo"| ModelVersion
Metadata -->|"validated by"| SHACL
Metadata -->|"be:endpointUrl / dcat:endpointURL"| DataService
API -->|"returns"| Record
AGroup -->|"uses common required fields"| Metadata
DGroup -->|"receives shapes and examples"| SHACL
```

这张图非常适合作为研讨开场图，因为它用一张图串起 C 组模型如何服务 A 组 offering 和 D 组 validation。

## 4. 治理流程图

`diagrams/semantic-governance-flow.mmd` 展示 semantic governance lifecycle：

```text
Propose model change
Semantic and domain review
Create version release v0.1 / v0.2 / v0.3
Export artifacts TTL, JSON-LD, SHACL, JSON Schema, OpenAPI, SSSOM
Run validation gates make validate
Publish and handoff A Group + D Group
Monitor usage and issues
Deprecate or replace terms with migration guidance
```

图里有两个关键分支：

```text
Review -->|"changes requested"| Proposal
Validate -->|"fail"| Proposal
Validate -->|"pass"| Publish
```

这说明模型发布不是线性通过，而是有审查和验证失败后的回退机制。

## 5. 模型设计报告

`C_semantic_model_design.md` 是 C 组模型设计主报告。它包含：

- Scope and purpose。
- DSSC architecture position。
- Reuse-first design principle。
- Namespace policy。
- Conceptual model。
- Data Product Metadata model。
- Energy Reading Record model。
- Alignment to DCAT/DCAT-AP, SOSA/SSN, QUDT/UCUM, OWL-Time。
- SHACL constraint strategy。
- JSON-LD serialization strategy。
- OpenAPI / JSON Schema relationship。
- Competency questions。
- Model quality summary。
- Limitations。
- Future extensions。

报告开头说明：

```text
This package defines a small, governable semantic model for the Building Energy Consumption Data Product.
It covers two related models:

- Data Product Metadata: catalogue, connector offering, and SHACL validation metadata for `building-energy-hourly-v1`.
- Energy Reading Record: one API payload record returned by `GET /energy/buildings/hourly`.
```

这可以作为整个项目的总解释。

## 6. Reuse-first 设计原则

`C_semantic_model_design.md` 中写：

```text
Local `be:*` terms are used only where the assignment requires compact field names
or where the demo needs a lightweight profile.
External standards are reused through subclassing, subproperties, JSON-LD context mappings,
and the SSSOM table.
```

这句话对应 Phase 04。它说明本项目不是把所有字段都私有化，而是在 minimal profile 和标准复用之间做平衡。

## 7. Treehouse 使用报告

`C_semantic_treehouse_usage.md` 汇总 Phase 06 的 Treehouse evidence。它开头明确定位：

```text
Semantic Treehouse is treated as a semantic model governance and publication tool.
In this package it is an evidence track, not the only source of truth.
```

它还列出 Docker evidence：

```text
The smoke check shows `http://localhost:4200/` returning `HTTP/1.1 200 OK`.
The backend/root port `http://localhost:8014/` is mapped by Compose,
but the root HEAD check timed out after 5 seconds.
```

这份报告的价值是：既满足 C 组需要研究 Semantic Treehouse 的要求，又避免夸大实际 UI 工作流完成度。

## 8. 版本演进报告

`C_model_versioning_demo.md` 把 v0.1、v0.2、v0.3 讲成一个演进故事。

它的 compatibility matrix 很适合展示：

```text
v0.1 to v0.2 | Stricter minor change with validation impact
v0.2 to v0.3 | Additive extension
```

对 A 组影响：

```text
A Group should use the v0.3 metadata contract for data offering metadata:

- include all nine required metadata fields
- include `dct:conformsTo = https://w3id.org/dssc-demo/building-energy/v0.3`
- expose the API endpoint as a data service endpoint
```

对 D 组影响：

```text
D Group receives the versioned SHACL shapes and examples.
```

这份报告把模型版本化和跨组使用联系起来。

## 9. 导出验证报告

`C_export_for_validation.md` 列出 v0.3 的导出产物：

```text
- Ontology: `model/v0.3/building-energy-ontology.ttl`
- Metadata SHACL: `model/v0.3/data-product-metadata-shapes.ttl`
- Record SHACL: `model/v0.3/energy-reading-record-shapes.ttl`
- Data product JSON-LD context: `model/v0.3/data-product-context.jsonld`
- Record JSON-LD context: `model/v0.3/energy-reading-record-context.jsonld`
- JSON Schema: `model/v0.3/energy-reading-record.schema.json`
- OpenAPI fragment: `model/v0.3/openapi-fragment.yaml`
- SSSOM mappings: `mappings/external-standard-alignment.sssom.tsv`
```

它还解释 `DataProductMetadataShape-v0_3` 的九个字段约束，以及 `EnergyReadingRecordShape-v0_3` 的六个字段约束。

这份文件特别适合给 D 组，因为它把“拿哪些文件、预期什么结果、怎么运行 validator”都集中写清楚。

## 10. 给 A 组的 handoff

`handoff/handoff-to-A-offering-metadata.md` 是给 connector/offering 方向的交接契约。它列出 A 组需要包含的字段：

```text
datasetId | building-energy-hourly-v1
providerName | Energy Data Provider Ltd.
endpointUrl | https://api.example.org/energy/buildings/hourly
format | JSON
frequency | hourly
unit | kWh
spatialCoverage | Shenzhen demo district
temporalStart | 2026-05-01
temporalEnd | 2026-05-02
```

并给出 JSON-LD example，其中包括：

```json
"conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.3"
```

它还建议 A 组：

```text
- A link or attachment to `model/v0.3/openapi-fragment.yaml`.
- A statement that payload records conform to `model/v0.3/energy-reading-record.schema.json`.
- The unit contract `kWh`, because D Group validation rejects other units under this profile.
```

这说明 C 组成果可以直接进入 A 组 data offering 描述。

## 11. 给 D 组的 handoff

`handoff/handoff-to-D-shacl-validation.md` 明确 D 组接收哪些文件：

```text
Metadata validation:

- `C_Semantic_Treehouse/model/v0.3/data-product-metadata-shapes.ttl`
- `C_Semantic_Treehouse/model/v0.3/data-product-valid.jsonld`
- `C_Semantic_Treehouse/model/v0.2/data-product-invalid.jsonld`
```

运行命令：

```bat
cmd /c make validate-shacl
cmd /c make validate-jsonschema
cmd /c make validate
```

invalid case 解释：

```text
`model/v0.2/data-product-invalid.jsonld` must fail because:

- `providerName` is missing.
- `unit` is `MWh`, but the allowed value is `kWh`.
- `temporalEnd` is missing.
```

这份 handoff 让 D 组可以直接把 C 组的 shapes 和 examples 放入 ITB/SEMIC validation story。

## 12. AI 辅助但人类治理

`docs/ai-assisted-human-governed-semantic-modeling.md` 说明 AI 在本项目中的角色。它写：

```text
AI can accelerate semantic modeling work by drafting:

- initial vocabulary candidates
- standards alignment candidates
- JSON-LD contexts
- SHACL constraint skeletons
- JSON Schema and OpenAPI fragments
- SSSOM mapping rows
- competency questions
- documentation and handoff notes
```

但也明确：

```text
AI must not be the final authority for:

- business meaning of fields
- legal or contractual data offering obligations
- governance approval
- release status
- deprecation decisions
- claims of conformance to external standards
- production validator acceptance
```

这份文档让项目可以在研讨中讨论 AI-assisted development 的边界：AI 可以辅助起草，但验证、审查和发布仍由人类和 validator gates 决定。

## 13. 本阶段验收情况

`PHASE_7_SUMMARY.md` 记录：

```text
cmd /c make validate - pass.
Mermaid static header check for both `.mmd` files - pass.
```

报告还说明：

```text
Mermaid diagrams: static syntax header check passed (`flowchart LR` and `flowchart TD`).
```

限制是：

```text
Mermaid CLI (`mmdc`) is not installed, so diagram validation was a static syntax check rather than a full render.
```

这也是后来 final checklist 的 partial 项之一。

## 14. 对后续阶段的影响

Phase 07 的报告和交接文件直接支撑：

- Phase 08 的 demo script。
- Phase 08 的 final checklist。
- Phase 09 的 final summary。
- 后续研讨和介绍材料。

换句话说，从 Phase 07 开始，项目已经可以讲给别人听了。

## 15. 研讨展示建议

介绍 Phase 07 时，可以按“从技术文件到交接包”来讲：

1. 打开 `diagrams/metadata-record-model.mmd`，说明 C 组模型如何连接 A 组和 D 组。
2. 打开 `C_semantic_model_design.md`，说明两个模型和标准对齐。
3. 打开 `C_model_versioning_demo.md`，说明 v0.1/v0.2/v0.3。
4. 打开 `handoff/handoff-to-A-offering-metadata.md`，说明 A 组拿什么。
5. 打开 `handoff/handoff-to-D-shacl-validation.md`，说明 D 组怎么验证。

可以总结：

> Phase 07 的意义是把前面所有工程产物变成可沟通的项目成果：有图、有报告、有交接契约，也有对 AI 辅助建模边界的治理说明。

