# Phase 05：来源、版本治理与机器可读 provenance

## 1. 本阶段解决的问题

Phase 05 的核心目标是把前面做出的语义模型从“一组技术文件”提升为“可治理的语义资产”。

Phase 01 到 Phase 04 已经完成：

- 有版本化模型文件。
- 有 SHACL、JSON-LD、JSON Schema、OpenAPI。
- 有 SPARQL competency questions。
- 有 SSSOM 映射和质量指标。

但如果一个 semantic model 要在 data space 中被多个小组或工具复用，还必须回答治理问题：

1. 这个模型适合谁用？
2. 哪些用途不在范围内？
3. 版本怎么发布？
4. 命名空间怎么维护？
5. 字段将来废弃怎么办？
6. 谁审查模型变更？
7. 每个版本的来源和演进关系如何记录？

`prompts/phase-05-provenance-and-version-governance-metadata.md` 因此要求：

```text
Add governance documentation and machine-readable version/provenance metadata.
```

## 2. 为什么语义模型需要治理

在 data space 里，语义模型不是普通代码片段。它会影响：

- A 组如何发布 data offering metadata。
- D 组如何写 SHACL/ITB validation。
- B 组是否能引用模型 URI 和 provenance。
- Consumer 如何理解数据产品字段含义。
- Data Space Authority 如何审查版本和变更。

如果模型字段随意修改，下游组会立刻受到影响。例如 v0.2 把 `unit` 固定为 `kWh`，D 组 validator 就会拒绝 `MWh`；A 组如果漏填 `temporalEnd`，offering metadata 也会失败。

所以 Phase 05 的价值不只是“补文档”，而是把模型作为一个有生命周期的公共契约来管理。

## 3. 新增产物

根据 `C_Semantic_Treehouse/PHASE_5_SUMMARY.md`，本阶段创建：

| 文件 | 作用 |
|---|---|
| `governance/model-card.md` | 描述模型名称、范围、用户、用途、风险和审查状态。 |
| `governance/changelog.md` | 记录 v0.1、v0.2、v0.3 的版本变化。 |
| `governance/namespace-policy.md` | 规定 base namespace、version IRIs、本地术语和外部复用规则。 |
| `governance/release-policy.md` | 规定 release criteria、validation gates、semantic versioning 和 rollback。 |
| `governance/deprecation-policy.md` | 规定字段废弃和兼容性处理。 |
| `governance/review-workflow.md` | 定义 proposal、automated checks、semantic/domain review、approval、release、handoff。 |
| `governance/provenance.jsonld` | PROV-O-inspired 机器可读 provenance。 |
| `scripts/validate_governance.py` | 检查治理文件是否存在、关键内容是否完整、provenance 是否可解析。 |
| `validation/governance-validation-report.md` | 治理验证报告。 |

同时更新 `Makefile` 和 `make.cmd`，增加：

```text
make validate-governance
```

并将治理验证纳入 `make validate`。

## 4. Model Card：说明模型能做什么、不能做什么

`governance/model-card.md` 是语义模型的“说明书”。它定义模型名称：

```text
Building Energy Semantic Model
```

并说明范围：

```text
This model governs the shared semantics for the Building Energy Consumption Data Product.
It covers two layers:

- Data Product Metadata for catalogue, connector offering, and SHACL validation.
- Energy Reading Record for API payload, JSON Schema, OpenAPI, and optional SHACL validation.
```

这对应 Phase 01 建立的两个层次模型。

Model Card 还明确列出 intended users：

```text
- C Group: semantic model owners and maintainers.
- A Group: connector and data offering implementers.
- D Group: SHACL/ITB validation designers.
- B Group: optional Gaia-X service offering or credential authors.
- Data Space Authority: reviewer and approver of semantic releases.
```

这使模型的使用方边界非常清楚。C 组维护模型，A 组消费 metadata contract，D 组消费 validation contract，B 组可选引用 provenance。

## 5. Out-of-Scope：防止过度声明

Model Card 中的 Out-of-Scope 非常适合研讨时引用：

```text
- Production energy market settlement.
- Legal compliance certification.
- Full building information modeling.
- Full geospatial or temporal reasoning.
- Replacement for connector, compliance, or ITB tooling.
```

这说明项目很清楚自己的范围：它是研究用 semantic governance package，不是生产能源结算系统，不替代 A/B/D 组工具，也不声称完成完整 BIM、GIS 或法律合规。

这种“说明不做什么”的部分，在研究项目中很重要，因为它降低了不必要的过度承诺。

## 6. Changelog：版本变化可追踪

`governance/changelog.md` 记录三个版本：

### v0.1

```text
Added:

- `be:DataProductMetadata` class.
- baseline fields: `datasetId`, `providerName`, `format`, `frequency`, `spatialCoverage`.
- baseline metadata SHACL shape.
- JSON-LD context and valid metadata example.
```

### v0.2

```text
Added:

- `endpointUrl`
- `unit`
- `temporalStart`
- `temporalEnd`
- controlled values for `format = JSON`, `frequency = hourly`, and `unit = kWh`
- invalid metadata example for validation failure demonstration
```

并说明它是：

```text
Stricter minor change from v0.1 with validation impact.
```

### v0.3

```text
Added:

- `be:EnergyReadingRecord` class.
- Energy Reading Record fields: `buildingId`, `meterId`, `timestamp`, `energyKWh`, `unit`, `location`.
- Record-level SHACL shape.
- Energy Reading Record JSON-LD context.
- Energy Reading Record JSON Schema.
- OpenAPI fragment for `GET /energy/buildings/hourly`.
- SPARQL competency questions covering metadata and record fields.
```

并说明它是 additive extension from v0.2。

Changelog 让版本演进可以被展示、审查和回溯。

## 7. Namespace Policy：稳定 URI 和本地术语规则

`governance/namespace-policy.md` 规定 base namespace：

```text
https://w3id.org/dssc-demo/building-energy#
```

prefix：

```text
be
```

version IRIs：

```text
https://w3id.org/dssc-demo/building-energy/v0.1
https://w3id.org/dssc-demo/building-energy/v0.2
https://w3id.org/dssc-demo/building-energy/v0.3
```

它还规定：

```text
Version IRIs identify model releases. They must be used in `dct:conformsTo`
links from data product metadata.
```

这解释了为什么 `model/v0.3/data-product-valid.jsonld` 要包含：

```json
"conformsTo": "https://w3id.org/dssc-demo/building-energy/v0.3"
```

Namespace Policy 还要求：

```text
Every local class and property must have `rdfs:label` and `rdfs:comment`.
```

这也是 Phase 01 中 ontology 为本地 class/property 增加 label 和 comment 的原因。

## 8. External Reuse Rules：优先复用标准

Namespace Policy 中明确规定：

```text
- Prefer DCAT/DCTERMS for catalogue and data service metadata.
- Prefer SOSA/SSN for observation, sensor, and feature-of-interest patterns.
- Prefer QUDT/UCUM for unit identifiers in richer profiles.
- Prefer OWL-Time or XSD temporal datatypes for temporal coverage.
- Record all non-trivial alignments in `mappings/external-standard-alignment.sssom.tsv`.
```

这和 Phase 04 的 SSSOM 映射直接连接。也就是说，SSSOM 不是随意添加的加分项，而是 namespace policy 要求的一部分。

## 9. Release Policy：发布前必须过验证门

`governance/release-policy.md` 把模型发布条件写得非常具体：

```text
A model release is eligible when:

- Required artifacts exist for the target version.
- RDF/Turtle files parse.
- JSON-LD files expand.
- SHACL valid cases pass.
- SHACL invalid cases fail for expected reasons.
- JSON Schema record cases pass/fail as expected when record schema is in scope.
- OpenAPI fragments parse and pass available structural validation.
- SPARQL competency questions pass when relevant.
- SSSOM mapping table is parseable.
- Quality metrics are generated.
- Governance/provenance validation passes.
```

它还列出 required gates：

```text
1. `make validate-rdf`
2. `make validate-jsonld`
3. `make validate-shacl`
4. `make validate-jsonschema`
5. `make validate-openapi`
6. `make test-sparql`
7. `make quality`
8. `make validate-governance`
9. `make validate`
```

这说明项目的 release 不是靠人工说“差不多可以”，而是要通过一组机器验证和报告检查。

## 10. Semantic Versioning 解释

Release Policy 定义四类版本变化：

```text
- Patch: documentation corrections or typo fixes that do not change model meaning.
- Minor: additive fields, optional constraints, mappings, or validation reports.
- Stricter minor with validation impact: new required constraints that do not remove existing fields but can reject older metadata.
- Major: removed fields, changed datatypes, changed field meaning, or incompatible validation behavior.
```

这个解释和 Phase 04 的 breaking-change risk 对齐：

- v0.1 到 v0.2 是 stricter minor with validation impact。
- v0.2 到 v0.3 是 additive extension。

## 11. Review Workflow：人类审查与自动检查结合

`governance/review-workflow.md` 定义了八步流程：

```text
1. Proposal
2. Automated Checks
3. Semantic Reviewer
4. Domain Reviewer
5. Approval
6. Release
7. Publication
8. Downstream Handoff
```

其中 Automated Checks 要求：

```sh
make validate
```

Semantic Reviewer 检查：

```text
- term naming
- external standards reuse
- SSSOM mappings
- JSON-LD context behavior
- SHACL constraint clarity
- version compatibility
```

Domain Reviewer 检查：

```text
- energy data meaning
- required business fields
- unit interpretation
- temporal and spatial coverage
- API payload plausibility
```

这说明模型治理不是只靠 AI 或脚本，也需要语义专家和领域专家审查。

## 12. Provenance JSON-LD：机器可读来源记录

`governance/provenance.jsonld` 使用 PROV-O-inspired 结构记录：

- C Group 是 agent。
- model generation 是 activity。
- v0.1、v0.2、v0.3 是 entity。
- v0.2 derived from v0.1。
- v0.3 derived from v0.2。
- validation reports 也是 generated artifacts。

其中 C 组 agent 是：

```json
{
  "@id": "https://w3id.org/dssc-demo/agents/c-group",
  "@type": "Agent",
  "title": "DSSC C Group",
  "description": "Semantic model governance owner for the Building Energy research package."
}
```

v0.3 entity 写明：

```json
{
  "@id": "https://w3id.org/dssc-demo/building-energy/v0.3",
  "@type": "Entity",
  "title": "Building Energy Semantic Model v0.3",
  "description": "Metadata model plus Energy Reading Record payload schema extension.",
  "wasDerivedFrom": "https://w3id.org/dssc-demo/building-energy/v0.2"
}
```

这让模型版本演进关系可被机器读取，而不只是写在 Markdown 中。

## 13. 治理验证脚本

Phase 05 增加 `scripts/validate_governance.py`。它检查：

- governance 文件是否存在且非空。
- model card 是否包含 required sections。
- changelog 是否包含 v0.1/v0.2/v0.3。
- release policy 是否包含 validation gates。
- namespace policy 是否包含 base namespace 和 version IRIs。
- provenance JSON-LD 是否可解析。

`validation/governance-validation-report.md` 中记录：

```text
Overall status: PASS
```

并确认：

```text
`governance/provenance.jsonld` parsed and expanded into 12 top-level node(s).
```

## 14. 本阶段验收情况

`PHASE_5_SUMMARY.md` 记录运行：

```bat
cmd /c make validate-governance
cmd /c make validate
```

通过项：

- 所有 expected governance files 存在且非空。
- `model-card.md` 包含 required sections。
- `changelog.md` 明确描述 v0.1、v0.2、v0.3。
- `release-policy.md` 使用 validation gates。
- `namespace-policy.md` 包含 base namespace 和 version IRIs。
- `provenance.jsonld` 可通过 JSON-LD processing 展开。
- `make validate-governance` 通过。
- `make validate` 包含 governance validation 并通过。

## 15. 本阶段限制

`PHASE_5_SUMMARY.md` 也说明：

```text
Provenance uses research-demo timestamps and identifiers; production use would require
real approval timestamps and reviewer identities.
```

这提醒听众：当前 package 是研究 demo 级别，虽然治理结构完整，但生产发布还需要真实审批人、真实时间戳和组织流程。

## 16. 对后续阶段的影响

Phase 05 的治理文件支撑：

- Phase 07 的报告中关于 namespace、versioning、release、deprecation、review workflow 的章节。
- Phase 08 required-file check 和 final checklist。
- Phase 09 final summary 中 excellent/top-tier requirements 的证明。
- B 组 handoff 中引用 model URI 和 provenance。

最终 `FINAL_SUMMARY.md` 中把 governance metadata 列为 top-tier evidence：

```text
Governance metadata | `governance/changelog.md`; `governance/provenance.jsonld`; `governance/release-policy.md`
```

## 17. 研讨展示建议

讲 Phase 05 时，可以强调：

> 语义模型不是一次性文件，而是 data space 中可发布、可审查、可追溯的公共契约。

建议现场打开：

- `governance/model-card.md`
- `governance/changelog.md`
- `governance/release-policy.md`
- `governance/review-workflow.md`
- `governance/provenance.jsonld`
- `validation/governance-validation-report.md`

可以重点展示 release gates 和 provenance 的 derivation 关系：

```text
v0.2 wasDerivedFrom v0.1
v0.3 wasDerivedFrom v0.2
```

这样听众会理解 C 组做的不只是“字段表”，而是一个小型语义治理流程。

