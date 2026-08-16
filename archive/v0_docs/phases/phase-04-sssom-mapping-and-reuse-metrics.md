# Phase 04：SSSOM 映射与复用质量指标

## 1. 本阶段解决的问题

Phase 04 的核心问题是：

> 这个模型是不是只定义了一套本地字段，还是和 data space 常用语义标准有清楚对应关系？

Phase 01 已经在 ontology 中使用了 DCAT、DCTERMS、SOSA/SSN、QUDT 等标准；Phase 04 则把这些标准对齐显式整理成 SSSOM-style mapping table，并进一步计算质量指标。

`prompts/phase-04-sssom-mapping-and-reuse-metrics.md` 的目标是：

```text
Create a semantic mapping table and derive reuse metrics to prove this is a
standards-aligned model, not a purely local schema.
```

这一步让模型从“能工作”走向“能解释为什么这样建模”。

## 2. 为什么需要 SSSOM

SSSOM 可以理解为“语义映射表”的一种结构化格式。它不只是写“我们用了 DCAT”，而是逐行说明：

- 本地术语是什么。
- 对齐到哪个外部标准术语。
- 是 exactMatch、closeMatch 还是 subclass/subproperty。
- 映射理由是什么。
- 置信度是多少。
- 谁在什么时候做了这个映射。

在 data space 中，这很重要。因为不同工具链、小组或标准 profile 可能用不同词汇描述同一个概念。例如：

- C 组本地字段叫 `endpointUrl`。
- DCAT 中相关概念是 `dcat:endpointURL`。
- A 组做 offering 时可能更熟悉 API endpoint。
- D 组做 SHACL validation 时需要知道实际 RDF path。

SSSOM 表就是这些语义关系的“翻译表”。

## 3. 新增产物

根据 `C_Semantic_Treehouse/PHASE_4_SUMMARY.md`，本阶段创建：

| 文件 | 作用 |
|---|---|
| `mappings/external-standard-alignment.sssom.tsv` | SSSOM-style 外部标准映射表。 |
| `scripts/quality_metrics.py` | 计算字段覆盖、约束强度、复用比例和 breaking-change risk。 |
| `quality/model-quality-assessment.md` | 人类可读质量评估报告。 |
| `validation/quality-metrics-report.md` | 可纳入 validation 的质量指标报告。 |

同时修改：

- `Makefile`
- `make.cmd`

使 `make quality` 和 `make validate` 能运行质量指标脚本。

## 4. SSSOM 表结构

`mappings/external-standard-alignment.sssom.tsv` 的列包括：

```text
subject_id
subject_label
predicate_id
object_id
object_label
mapping_justification
confidence
author_id
mapping_date
comment
```

这比普通 Markdown 表更适合作为机器可读 evidence。`validation/quality-metrics-report.md` 也确认：

```text
`mappings/external-standard-alignment.sssom.tsv` contains 23 mapping rows.
```

## 5. Data Product Metadata 的映射

SSSOM 表中对 metadata 层的映射包括：

```text
be:DataProductMetadata -> dcat:Dataset
dct:identifier -> dct:identifier
be:providerName -> dct:publisher / schema:provider / foaf:name pattern
be:endpointUrl -> dcat:endpointURL
be:format -> dct:format / dcat:mediaType
be:frequency -> dct:accrualPeriodicity
be:unit -> qudt:unit / unit:KiloW-HR
be:spatialCoverage -> dct:spatial
be:temporalStart -> time:hasBeginning
be:temporalEnd -> time:hasEnd
```

其中 `be:endpointUrl` 的映射是 exactMatch：

```text
be:endpointUrl	endpoint URL	skos:exactMatch	dcat:endpointURL	Endpoint URL
```

comment 说明：

```text
API endpoint URL aligns directly with DCAT DataService endpointURL semantics.
```

这就解释了为什么 ontology 中 `be:endpointUrl` 被定义为 `dcat:endpointURL` 的 subproperty。

## 6. providerName 为什么只是 closeMatch

SSSOM 表中 `be:providerName` 映射到多个外部概念时使用 `skos:closeMatch`，例如：

```text
be:providerName	provider name	skos:closeMatch	dct:publisher	Publisher
```

comment 写道：

```text
Minimal profile stores provider as a string; richer profiles should model an organization node.
```

这说明项目没有过度声称 `providerName` 等同于 `dct:publisher`。在严格 DCAT 模型中，publisher 通常应该是组织资源，而本 demo 中 provider 是字符串。因此使用 closeMatch 是更诚实的语义关系。

这也是 Phase 04 的价值之一：它不仅列出对齐，还标出对齐的强弱。

## 7. Energy Reading Record 的映射

record 层的映射包括：

```text
be:EnergyReadingRecord -> sosa:Observation
be:buildingId -> sosa:hasFeatureOfInterest
be:meterId -> sosa:madeBySensor
be:timestamp -> sosa:resultTime
be:energyKWh -> sosa:hasResult / qudt:numericValue
be:unit -> qudt:unit
be:location -> dct:spatial / schema:location
```

例如 `be:timestamp` 是 exactMatch：

```text
be:timestamp	timestamp	skos:exactMatch	sosa:resultTime	Result Time
```

comment：

```text
Reading timestamp aligns with SOSA result time.
```

而 `be:buildingId` 是 closeMatch：

```text
be:buildingId	building ID	skos:closeMatch	sosa:hasFeatureOfInterest
```

原因是当前模型用字符串 ID 表示 building，而完整 SOSA 图中应连接到一个 feature-of-interest resource。

## 8. 质量指标一：字段覆盖率

`quality/model-quality-assessment.md` 中写：

```text
Required fields represented in v0.3 shapes: 15/15 (100.00%)
Missing required fields: none
```

这 15 个字段来自两个层次：

- Metadata 9 个字段：`datasetId`、`providerName`、`endpointUrl`、`format`、`frequency`、`unit`、`spatialCoverage`、`temporalStart`、`temporalEnd`
- Record 6 个字段：`buildingId`、`meterId`、`timestamp`、`energyKWh`、`unit`、`location`

字段覆盖率 100% 说明 task plan 要求的字段都在 v0.3 shapes 中被表示出来。

## 9. 质量指标二：约束强度

`quality/model-quality-assessment.md` 给出约束强度表：

```text
v0.1 metadata | 5 required constraints | 5 restricted value/type/node constraints
v0.2 metadata | 9 required constraints | 9 restricted value/type/node constraints
v0.3 metadata | 9 required constraints | 9 restricted value/type/node constraints
v0.3 record   | 6 required constraints | 6 restricted value/type/node constraints
```

这张表可以解释模型演进：

- v0.1：最小 metadata，只有基础字段。
- v0.2：metadata 变严格，新增 endpoint、unit、temporal coverage。
- v0.3：metadata 约束保持 v0.2，新增 record payload 约束。

也就是说，v0.3 的复杂度不是靠任意扩展字段堆出来的，而是有明确层次：metadata 保持稳定，payload 增加新层。

## 10. 质量指标三：复用比例

`quality/model-quality-assessment.md` 中写：

```text
Local modeled terms in v0.3 ontology: 19
Local modeled terms aligned in SSSOM: 15
Reuse ratio: 15/19 (78.95%)
SSSOM mapping rows: 23
```

这里的 reuse ratio 不是说 78.95% 的字段直接用了外部 IRI，而是说 v0.3 ontology 中 19 个本地 `be:*` terms 里，有 15 个在 SSSOM 中和外部标准术语建立了映射。

`validation/quality-metrics-report.md` 也记录：

```text
Field coverage: 15/15 (100.00%)
Reuse ratio: 15/19 (78.95%)
SSSOM rows: 23
```

这个指标可以作为展示中的量化亮点。

## 11. 质量指标四：breaking-change risk

Phase 04 还要求分析版本变化对下游的风险。报告把变化分成两类。

### v0.1 到 v0.2

`quality/model-quality-assessment.md` 写：

```text
Classification: stricter minor change with validation impact.
```

原因：

- 新增 required `endpointUrl`、`unit`、`temporalStart`、`temporalEnd`。
- 旧的 v0.1-style metadata 在 v0.2 下可能失败。

对 A 组影响：

```text
data offering metadata must include endpoint, unit, and temporal coverage before publication.
```

对 D 组影响：

```text
validator shapes reject incomplete v0.1-style metadata under v0.2 rules.
```

### v0.2 到 v0.3

报告写：

```text
Classification: additive extension.
```

原因是 metadata 约束保持兼容，只新增 record payload 模型、SHACL shape、JSON Schema 和 OpenAPI fragment。

对 A 组影响：

```text
connector/API documentation can reference the record schema.
```

对 D 组影响：

```text
payload validation can be added as an optional second validation layer without breaking metadata validation.
```

这个分析让版本演进不只是文件夹变化，而是明确说明对下游小组的影响。

## 12. 与模型设计报告的关系

`C_semantic_model_design.md` 在 “Model Quality Summary” 中引用 Phase 04 的结果：

```text
- field coverage: 15/15 required fields represented, 100.00%
- reuse ratio: 15/19 local modeled terms externally aligned, 78.95%
- SSSOM mapping rows: 23
- v0.1 to v0.2: stricter minor change with validation impact
- v0.2 to v0.3: additive extension
```

这说明 Phase 04 的指标不是孤立报告，而是进入了最终模型设计说明。

## 13. 本阶段验收情况

`PHASE_4_SUMMARY.md` 记录运行：

```bat
cmd /c make quality
cmd /c make validate
```

通过项：

- SSSOM TSV 可解析。
- quality report 包含 numeric metrics 和 interpretation。
- reuse ratio 基于实际 v0.3 ontology local terms 和 SSSOM mapping subjects。
- breaking-change risk 明确提到 A 组和 D 组影响。
- full validation 包含 `make quality` 并通过。

## 14. 本阶段的限制

`quality/model-quality-assessment.md` 也诚实说明：

```text
Reuse ratio measures mapping coverage, not full semantic equivalence.
```

这句话很重要。SSSOM 映射能说明本地术语和外部标准有关系，但不能自动证明完全等价，也不能替代专家语义审查。

同一文件还指出：

```text
Provider, location, and temporal coverage are still lightweight literals/objects
rather than full organization, place, or OWL-Time interval nodes.
```

这体现了项目的 minimal profile 取舍：为了 demo 可运行，暂时不引入完整 organization/place/time interval 建模。

## 15. 对后续阶段的影响

Phase 04 的结果支撑：

- Phase 05 的 governance docs 中“standards reused”部分。
- Phase 07 的 `C_semantic_model_design.md` 和最终报告中的 standards alignment 说明。
- Phase 08 final checklist 中的 excellent 和 top-tier 证据。
- Phase 09 final summary 中对 top-tier requirements 的证明。

`docs/final-checklist.md` 中把 SSSOM mapping table 标为 done：

```text
SSSOM semantic mapping table | done | `mappings/external-standard-alignment.sssom.tsv`
```

## 16. 研讨展示建议

介绍 Phase 04 时，可以这样讲：

> Phase 04 解决的是“我们的字段是不是孤立自创”的问题。通过 SSSOM 表，项目逐行说明每个本地术语怎样对齐 DCAT、DCTERMS、SOSA/SSN、QUDT/UCUM、OWL-Time 和 schema.org；通过质量指标，又量化了字段覆盖率、约束强度、复用比例和版本变更风险。

建议现场展示：

- `C_Semantic_Treehouse/mappings/external-standard-alignment.sssom.tsv`
- `C_Semantic_Treehouse/quality/model-quality-assessment.md`
- `C_Semantic_Treehouse/validation/quality-metrics-report.md`

可以重点说三个数字：

```text
Field coverage: 15/15 (100.00%)
Reuse ratio: 15/19 (78.95%)
SSSOM rows: 23
```

最后强调：

> 这些数字不是为了看起来漂亮，而是为了说明 C 组模型是一个标准对齐的 lightweight profile，而不是一份只对本项目有意义的本地字段表。

