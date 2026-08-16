# Phase 03：SPARQL 能力问题与语义测试

## 1. 本阶段解决的问题

Phase 03 的目标是证明模型不只是“能通过语法和约束检查”，还能够回答 data space 语义治理中的关键问题。换句话说，Phase 02 证明文件可验证，Phase 03 证明模型可查询、可解释、可用于治理决策。

`prompts/phase-03-sparql-competency-questions-and-semantic-tests.md` 写明目标：

```text
Add competency-question tests that prove the semantic model can answer meaningful data space governance questions.
```

Competency Questions 是语义建模中常用的方法：先问模型应该能回答什么问题，再用查询验证模型是否真的表达了这些信息。对本项目来说，这些问题覆盖了数据产品 identifier、provider、endpoint、format、frequency、unit、coverage、model version 和 record fields。

## 2. 为什么要增加 SPARQL 测试

SHACL 主要回答：

> 这个数据是否符合约束？

SPARQL competency questions 主要回答：

> 这个模型能否提供我们需要的语义信息？

二者互补。比如 SHACL 可以检查 `unit` 是否是 `kWh`，而 SPARQL 可以查询“这个数据产品的 unit 是什么”。SHACL 可以检查 `dct:conformsTo` 是否存在，SPARQL 可以查询“这个 metadata 符合哪个模型版本”。

因此 Phase 03 把语义模型从 validation contract 推进一步，变成可查询的 governance graph。

## 3. 新增文件结构

根据 `C_Semantic_Treehouse/PHASE_3_SUMMARY.md`，本阶段创建：

```text
tests/sparql/competency-questions.md
tests/sparql/queries/cq01-dataset-id.rq
tests/sparql/queries/cq02-provider.rq
tests/sparql/queries/cq03-endpoint.rq
tests/sparql/queries/cq04-format-frequency.rq
tests/sparql/queries/cq05-unit.rq
tests/sparql/queries/cq06-coverage.rq
tests/sparql/queries/cq07-conforms-to.rq
tests/sparql/queries/cq08-record-fields.rq
tests/sparql/expected/cq01-dataset-id.tsv
...
scripts/run_sparql_tests.py
```

并生成报告：

```text
validation/sparql-competency-question-report.md
```

这个结构很清楚：

- `competency-questions.md` 说明人类问题。
- `queries/*.rq` 是机器可运行查询。
- `expected/*.tsv` 是期望答案。
- `run_sparql_tests.py` 负责运行查询并比对结果。
- `validation/sparql-competency-question-report.md` 记录通过情况。

## 4. 八个能力问题

Phase 03 覆盖八个 CQ：

| CQ | 问题 | 作用 |
|---|---|---|
| CQ1 | What is the dataset identifier? | 检查数据产品唯一标识。 |
| CQ2 | Who is the provider? | 检查发布方。 |
| CQ3 | What endpoint URL exposes the data product? | 检查 API endpoint。 |
| CQ4 | What format and frequency does the data product use? | 检查数据格式和更新频率。 |
| CQ5 | What unit is required by the model? | 检查单位约束。 |
| CQ6 | What spatial and temporal coverage does the metadata declare? | 检查空间和时间覆盖。 |
| CQ7 | Which model version does the metadata conform to? | 检查版本绑定。 |
| CQ8 | What fields define an Energy Reading Record? | 检查 record 模型字段。 |

这些问题正好覆盖了 C 组模型的两个层次：

- CQ1 到 CQ7 主要针对 Data Product Metadata。
- CQ8 针对 Energy Reading Record。

## 5. 测试图的构建

`validation/sparql-competency-question-report.md` 的 Notes 说明：

```text
The test graph loads v0.3 ontology, v0.3 valid data product metadata,
and v0.3 valid Energy Reading Record.
```

这意味着 SPARQL 测试不是只查一个静态 JSON，而是把以下内容组成 RDF graph：

1. `model/v0.3/building-energy-ontology.ttl`
2. `model/v0.3/data-product-valid.jsonld`
3. `model/v0.3/energy-reading-record-valid.jsonld`

这样，查询既可以看到 ontology 中定义的类和属性，也可以看到实例数据中的真实值。

## 6. CQ1：查询 dataset identifier

报告中 CQ1 的结果是：

```text
Expected TSV:
datasetId
building-energy-hourly-v1

Actual TSV:
datasetId
building-energy-hourly-v1
```

这说明 `data-product-valid.jsonld` 中的：

```json
"datasetId": "building-energy-hourly-v1"
```

通过 JSON-LD context 映射成 RDF 后，可以被 SPARQL 查询出来。

这对 catalogue 和 data offering 很重要，因为 dataset ID 是跨工具链引用同一个数据产品的关键标识。

## 7. CQ2：查询 provider

报告中 CQ2 的结果是：

```text
providerName
Energy Data Provider Ltd.
```

这对应 `model/v0.3/data-product-valid.jsonld`：

```json
"providerName": "Energy Data Provider Ltd."
```

从治理角度看，provider 是责任归属信息。它不仅是展示字段，也关系到数据产品由谁维护、谁发布、谁接受审查。

## 8. CQ3：查询 endpoint

CQ3 的结果是：

```text
endpointUrl
https://api.example.org/energy/buildings/hourly
```

这个 endpoint 同时出现在：

- `task_plan/DSSC_Toolbox_Scenario.md`
- `C_Semantic_Treehouse/model/v0.3/data-product-valid.jsonld`
- `C_Semantic_Treehouse/model/v0.3/openapi-fragment.yaml`
- `C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md`

这说明 endpoint 在任务场景、语义 metadata、API 文档和 A 组交接之间保持一致。

## 9. CQ4：查询 format 和 frequency

CQ4 的结果是：

```text
format	frequency
JSON	hourly
```

这两个字段连接了数据产品发现和消费侧预期：

- `format = JSON` 告诉使用方 payload 采用 JSON。
- `frequency = hourly` 告诉使用方数据是小时级更新或采样。

v0.2/v0.3 SHACL 中也把它们约束为固定值：

```turtle
sh:in ("JSON") ;
sh:message "format must be JSON in v0.3." ;
```

```turtle
sh:in ("hourly") ;
sh:message "frequency must be hourly in v0.3." ;
```

SPARQL 证明这些值不仅被约束，也能被查询出来。

## 10. CQ5：查询 unit

CQ5 的结果是：

```text
unit
kWh
```

这和 SHACL、JSON Schema、OpenAPI 都保持一致：

- metadata `unit` 必须是 `kWh`。
- record `unit` 必须是 `kWh`。
- OpenAPI enum 只有 `kWh`。
- invalid examples 中 `MWh` 会失败。

在研讨中可以强调：单位字段虽然看似简单，但它是能源数据互操作的关键。如果 metadata 说 kWh、payload 却返回 MWh，会导致下游分析错误。

## 11. CQ6：查询 coverage

CQ6 的结果是：

```text
spatialCoverage	temporalStart	temporalEnd
Shenzhen demo district	2026-05-01	2026-05-02
```

这对应统一场景中的：

```text
Spatial Coverage | Shenzhen demo district
Temporal Coverage | 2026-05-01 to 2026-05-02
```

在 data space 中，coverage 能帮助 consumer 判断数据是否覆盖自己需要的地区和时间范围。Phase 03 证明这些范围信息不是只写在说明文档中，而是存在于可查询的语义 metadata 中。

## 12. CQ7：查询模型版本

CQ7 是本阶段最有治理意义的问题。报告中写：

```text
modelVersion
https://w3id.org/dssc-demo/building-energy/v0.3
```

并在 Notes 中强调：

```text
CQ7 checks the model version binding through dct:conformsTo.
```

这说明 metadata 能告诉 validator 或下游工具“我符合哪个模型版本”。如果将来存在 v0.4 或 v1.0，不同 data product 可以通过 `dct:conformsTo` 指向不同版本，从而避免版本混淆。

## 13. CQ8：查询 Energy Reading Record 字段

CQ8 的结果列出了 record 模型字段：

```text
field	label
https://w3id.org/dssc-demo/building-energy#buildingId	building ID
https://w3id.org/dssc-demo/building-energy#energyKWh	energy kWh
https://w3id.org/dssc-demo/building-energy#location	location
https://w3id.org/dssc-demo/building-energy#meterId	meter ID
https://w3id.org/dssc-demo/building-energy#timestamp	timestamp
https://w3id.org/dssc-demo/building-energy#unit	unit
```

这里查询的不是一个 record 实例中的值，而是 ontology 中定义的 record 字段和 label。它证明 v0.3 确实新增了 API payload 语义层，而不只是 metadata 层。

## 14. 严格 TSV 比对

`PHASE_3_SUMMARY.md` 提醒：

```text
Expected SPARQL results are exact TSV comparisons, so future model changes must update expected files intentionally.
```

这意味着 Phase 03 的测试对变更很敏感。如果模型字段、label、结果顺序或值发生变化，就需要同步更新 expected TSV。这是一种很好的 governance 机制：模型变化不能“偷偷发生”，必须显式更新预期结果。

## 15. Makefile 集成

Phase 03 更新了：

- `Makefile`
- `make.cmd`

让命令：

```bat
cmd /c make test-sparql
```

可以运行 `scripts/run_sparql_tests.py`。

同时 `make validate` 也包含 SPARQL 测试。也就是说，从 Phase 03 开始，整体 validation 不只包含语法和约束，还包含 competency question evidence。

## 16. 与模型设计报告的关系

Phase 03 修改了 `C_semantic_model_design.md`，加入 competency questions 作为模型质量证据。该文件中写：

```text
SPARQL competency questions in `tests/sparql/competency-questions.md`
verify that the RDF graph can answer governance questions about dataset identifier,
provider, endpoint, format, frequency, unit, coverage, model version, and record fields.
```

这句话可以直接用于展示：SPARQL 不是额外炫技，而是语义模型质量评估的一部分。

## 17. 本阶段验收情况

`PHASE_3_SUMMARY.md` 记录运行：

```bat
cmd /c make test-sparql
cmd /c make validate
```

通过项：

- `make test-sparql` 成功运行测试脚本。
- 报告列出所有八个 CQ 的 pass/fail 状态。
- CQ7 检查 `dct:conformsTo` 模型版本绑定。
- `make validate` 包含 SPARQL 测试并成功退出。

## 18. 对后续阶段的影响

Phase 03 的 SPARQL 测试后来成为：

- Phase 04 quality 之外的另一类模型质量证据。
- Phase 07 报告和 demo script 中展示模型能力的材料。
- Phase 08 final checklist 中的 Top-tier evidence。
- Phase 09 final summary 中证明 top-tier requirement 的文件。

最终 `docs/final-checklist.md` 把 SPARQL competency questions 标为 done：

```text
SPARQL competency questions | done |
`tests/sparql/competency-questions.md`; `validation/sparql-competency-question-report.md`
```

## 19. 研讨展示建议

介绍 Phase 03 时，可以用一句话开场：

> Phase 02 证明模型能被 validator 检查，Phase 03 证明模型能回答语义治理问题。

建议现场展示：

1. 打开 `tests/sparql/competency-questions.md`，说明八个问题。
2. 运行：

```bat
cmd /c make test-sparql
```

3. 打开 `validation/sparql-competency-question-report.md`，重点展示 CQ7 和 CQ8。

其中 CQ7 讲版本治理，CQ8 讲 v0.3 record payload 扩展。这两个问题最能体现 C 组不只是字段整理，而是在做语义模型治理。

