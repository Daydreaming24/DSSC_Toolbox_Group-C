# Phase 06 Prompt — 语义测试、质量指标与治理

只实施 Phase 06。开始前完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md` 和本文件；进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。

## 1. 目标

以 Phase 05 已验证的 v0.4 模型和四状态结果为真源，扩展版本明确、可重复的 SPARQL semantic tests，建立可追踪的质量指标，累积更新 SSSOM、governance 和 PROV-O-inspired provenance。所有结果必须进入统一 `scripts/validate.py` 编排，并由 `--suite all` fail closed 验收。

本阶段要证明三件事：v0.4 数据与 Shape 能回答关键治理问题；每个质量结论都有明确分子、分母和来源；v0.4 的来源、breaking change、审批状态和发布 gate 可由机器核验。

## 2. 非目标

- 不改变 D 组契约、v0.4 model、fixtures 或四状态 oracle。
- 不新增数据产品业务字段或扩展 ontology 范围。
- 不撰写最终报告、交接文档、CI、Treehouse 或 GitHub 发布材料。
- 不把统计数量或 mapping 行数包装成未经审查的语义质量保证。
- 不填写虚构 reviewer、approval、CI run、发布时间或外部验证结果。

## 3. 权威输入

1. `C_Semantic_Treehouse/manifests/release-manifest.json`
2. `C_Semantic_Treehouse/manifests/baseline-test-cases.json`
3. `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
4. `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
5. `C_Semantic_Treehouse/manifests/schemas/*.schema.json`
6. `C_Semantic_Treehouse/manifests/validation-suites.json`
7. `docs/v0.4/requirements-traceability.md` 和已批准 decision records
8. `build/validation/v0.4/results.json`
9. `docs/v0.4/STATUS.md` 中 Phase 05 小节
10. v0.1–v0.3 的 8 个 SPARQL competency questions、当前 SSSOM、quality 和 governance 文件，作为累积更新基础
11. D 组冻结 TTL，用于核验 Shape 语义，不用于原地编辑

## 4. 进入门槛

- Phase 00–05 均在 `docs/v0.4/STATUS.md` 中记录为 `COMPLETE`。
- Phase 05 小节、四个 manifests 及相应 schemas 均存在、非空、通过 schema/hash/freshness 检查。
- Phase 05 results 显示四种业务状态均被执行，required case 无 skipped，program status 全部为 SUCCESS。
- 下列命令实际退出 0：

```text
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
.\scripts\validate.ps1 -Suite v0.4
```

- `docs/v0.4/CHECKPOINT.md` 为空闲。
- Git diff 已审查，Phase 06 可写路径不存在无法避开的用户改动冲突。

任何进入门槛失败时，先完成安全诊断，把当前进度写入 `CHECKPOINT.md`。需要确认重叠修改归属或其他决定时标记 `AWAITING_HUMAN_DECISION`；确认没有安全路径时标记 `BLOCKED`，不修改 oracle 或早期产物。

## 5. 可写路径与保护路径

### 可写路径

- `C_Semantic_Treehouse/tests/sparql/**`
- `C_Semantic_Treehouse/scripts/run_sparql_tests.py`
- `C_Semantic_Treehouse/scripts/quality_metrics.py`
- `C_Semantic_Treehouse/scripts/validate_governance.py`
- 上述脚本直接依赖的同目录辅助模块
- `C_Semantic_Treehouse/mappings/**`
- `C_Semantic_Treehouse/quality/**`
- `C_Semantic_Treehouse/governance/**`
- `C_Semantic_Treehouse/manifests/validation-suites.json`，仅把本阶段内部 checks 纳入 `all` 并 bump `contract_version`
- `build/phase-06/**`
- `build/validation/{sparql,quality,governance}/**`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`

### 本阶段额外保护路径

- Master 永久保护范围全部只读。
- `C_Semantic_Treehouse/model/v0.4/**`、`fixtures/v0.4/**` 和四个业务 manifests 全部只读。
- `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json` 只读。
- `docs/v0.4/requirements-traceability.md` 和已批准 decisions 只读；若发现不一致，按 `human-intervention-policy.md` 记录问题、说明应回到哪个更早 Phase，并停下来找人确认。
- Phase 07–09 的最终报告、handoff、CI 和 release evidence 不写入。

## 6. 任务

### 6.1 保留历史 CQ 并建立 v0.4 semantic tests

保留原有 8 个 v0 SPARQL query 和 expected TSV 的语义与 oracle。为 v0.4 建立明确版本目录，并把机器清单和 schema 固定为 `C_Semantic_Treehouse/tests/sparql/sparql-test-cases.json` 与 `C_Semantic_Treehouse/tests/sparql/sparql-test-cases.schema.json`；runner 必须从 release manifest 和该测试清单选择 graph、query 与 expected output，禁止硬编码 `v0.3`、使用无约束 glob 或把 0 query 当作成功。JSON Schema 负责字段、类型、相对路径、SHA-256 格式和非空 query 集合；独立跨记录语义校验器负责 duplicate query/artifact IDs、query 到 graph/expected/release/requirement 的 cross-reference、同路径多 hash、必需 CQ 集合与 orphan 文件检查。使用临时清单证明 duplicate ID、悬空引用和 hash 冲突均非零失败。

v0.4 semantic tests 至少覆盖：

- Dataset 数量恰为 1 且节点为 IRI。
- datasetId、title、providerName、spatial 的实际路径和值。
- endpointURL、format、accrualPeriodicity、unit 的实际路径和值。
- temporalStart、temporalEnd 和非倒序关系。
- description/license 的 optional 行为。
- Phase 03/04 批准的 profile/version binding 决定。
- D 组命名 Shapes、severity、constraint component 和 Closed Shape allowed-property inventory。
- release manifest 声明的 v0.3 Energy Reading Record 复用或变更状态。

SELECT 结果以稳定 TSV 比较，行顺序规范化；ASK/COUNT 必须声明精确 expected。空结果只有在 query manifest 明确要求且有业务理由时才可成功。

### 6.2 扩展 SSSOM 与迁移映射

累积更新 `external-standard-alignment.sssom.tsv`，至少记录：

- v0.3 `be:*` metadata 路径到 v0.4 `ex:/dct:/dcat:` 路径的迁移关系。
- v0.4 对 DCAT/DCTERMS 的直接复用。
- 本地 `ex:*` 字段与外部标准的合理 mapping。
- v0.3 record 层继续使用的 SOSA/SSN、QUDT/UCUM、OWL-Time 等映射。

每行必须通过 schema/列检查，包含 mapping predicate、justification、confidence、review status 或等价审计字段。`skos:exactMatch`、`skos:closeMatch`、`skos:relatedMatch` 等谓词按真实语义选择；直接复用 external IRI 与本地映射分开统计。重复或自映射行必须有明确理由，否则验证失败。

### 6.3 重构质量指标

质量计算从 manifests 和实际 RDF/SHACL 图读取，不硬编码 v0.3 或手写完成百分比。至少生成：

1. D 组规范性 requirement 实现覆盖率。
2. requirement 自动测试覆盖率。
3. 必填与可选字段覆盖率。
4. constraint component 分布：min/max count、datatype、pattern、`sh:in`、nodeKind、SPARQL、closed。
5. 四状态自动用例覆盖。
6. 外部标准直接复用率和本地术语映射率，分别给出分子、分母、排除规则。
7. v0.3 → v0.4 breaking-change 风险。
8. release/provenance metadata 完整度。

breaking-change 评估必须明确涵盖：`be:DataProductMetadata` 到 `dcat:Dataset`；`dct:identifier` 到 `ex:datasetId`；其他 `be:*` 到 D 组扁平路径；`JSON` 到 `application/json`；HTTPS、exact-one Dataset、单值、空白、时间顺序和 Closed Shape 新行为；v0.3 record 的实际状态。结论应明确 v0.4 metadata 是不兼容 wire-profile 迁移。

### 6.4 累积更新治理文件

更新以下现行资产并保留 v0.1–v0.3 历史叙述：

- `model-card.md`：v0.4 scope、用户、用途、风险、validation strategy、review status。
- `changelog.md`：新增 v0.4 条目、breaking change、A/B/D 影响。
- `namespace-policy.md`：解释历史 `w3id` namespace 与 D 组 `https://example.org/dssc-energy#` 契约 namespace 的并存和迁移边界。
- `release-policy.md`：D 输入 hash、四状态、manifest、cross-platform 和证据 gate。
- `deprecation-policy.md`：v0.3 → v0.4 field/path migration guidance。
- `review-workflow.md`：C 组语义审查、D 组契约核对、domain review、自动 gate 和人工批准。
- `provenance.jsonld`：v0.4 entity、D 组来源 entity、C 组派生活动、v0.3 derivation/compatibility、当前实际生成的验证 artifact。

provenance 中所有 source path/hash 必须与 manifests 一致。尚未发生的批准、CI、GitHub publication 或 Treehouse run 使用明确 pending 状态，不能写成已完成活动。

### 6.5 实现 fail-closed 检查

- SPARQL runner 每次先运行测试清单 JSON Schema 与跨记录语义校验，再检查 query discovery、manifest 对应、expected 文件、版本选择、精确输出和 freshness。
- quality validator 检查每个指标的来源、分子/分母、零分母、重复规则和生成一致性。
- governance validator 检查必需文件非空、v0.4 changelog、namespace decision、release gates、provenance JSON-LD 可解析、必需实体/关系/hash 存在。
- 每次运行先对 release、baseline test cases、v0.4 requirements、v0.4 test cases 和 validation-suites 执行各自 JSON Schema 与跨记录语义校验；duplicate IDs、悬空 cross-references、同路径 hash 冲突或 suite dependency 异常均非零。
- 在 `validation-suites.json` 的 `all` 组成中加入 SPARQL、quality、governance 三个内部 checks，并 bump 顶层 `contract_version`。不新增公开 suite 名，不修改通用 `scripts/validate.py` dispatcher；本阶段只新增受控 allowlist 中的 checker entrypoint 并登记。
- `all` 继续确定性展开六个非 `all` 公开 suite，再执行本阶段三个内部 checks；任一检查缺失、跳过、0 discovered 或异常均非零。
- validation-suites 语义 checker 验证内部 check ID 唯一、entrypoint 已登记、依赖存在、图无环且 `all` 展开无重复。

### 6.6 生成确定性报告

SPARQL、quality、governance 各自生成机器 JSON 真源和由其确定性生成的 Markdown。环境元数据独立记录。报告使用仓库相对路径，并包含所消费 manifests、SPARQL 测试清单及其 schema 的 hash、validation-suites `contract_version`/registry hash，以及 dispatcher、SPARQL 清单语义 checker、SPARQL/quality/governance checker、报告器和全部实际加载 helper 的源 SHA-256，从而检测陈旧状态。

## 7. 产物

- 版本明确的 v0.4 SPARQL queries、expected TSV、固定路径的 `sparql-test-cases.json`/schema 和跨记录语义 checker
- 累积更新的 `external-standard-alignment.sssom.tsv`
- `C_Semantic_Treehouse/quality/model-quality-assessment.md`
- 更新后的七类 governance/provenance 文件
- `build/validation/sparql/results.json` 与报告
- `build/validation/quality/results.json` 与报告
- `build/validation/governance/results.json` 与报告
- 更新后的 `C_Semantic_Treehouse/manifests/validation-suites.json`
- manifest/suite 语义 negative-control 与 runner/helper 源 hash 证据
- `build/phase-06/**`
- `docs/v0.4/STATUS.md` 中的 Phase 06 小节

## 8. 必需命令

```text
git status --short --branch
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
.\scripts\validate.ps1 -Suite v0.4
.\scripts\validate.ps1 -Suite all
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
git status --short
```

还必须运行 SPARQL/quality/governance 的 deterministic rerun，以及每个 consumed manifest 的 duplicate-ID/悬空 cross-reference 负控、SPARQL 测试清单的 duplicate query/artifact ID、悬空引用和同路径多 hash 负控、suite registry duplicate/dependency/cycle/unknown-entrypoint/0-component/repeated-component/shell-payload 负控；具体内部命令及退出码写入 `STATUS.md`。禁止新增不在统一合同中的公开 suite 名称。

## 9. 验收矩阵

| 验收项 | 通过标准 | 证据 |
|---|---|---|
| 历史 CQ | 8 个历史 CQ 全部执行且 oracle 不变 | SPARQL results |
| v0.4 CQ | 全部发现、执行、精确匹配，版本来源明确 | SPARQL results |
| 零发现保护 | 0 query/缺 expected/跳过 required 均非零 | negative control |
| SSSOM | 列、IRI、predicate、重复、justification 检查通过 | quality results |
| Requirement 覆盖 | 实现和自动测试覆盖均由 manifests 计算 | quality JSON |
| 指标可解释 | 每项有分子、分母、来源与排除规则 | quality assessment |
| Breaking change | v0.3 → v0.4 wire-profile 不兼容事实完整 | assessment/changelog |
| Governance | 七类现行文件完整并包含 v0.4 | governance results |
| Provenance | JSON-LD 可解析，来源 hash、derivation、agent、activity 完整 | governance results |
| 真实状态 | 无虚构 approval/CI/Treehouse/publication | 人工与机器审查 |
| 确定性 | 重跑机器结果稳定 | comparison evidence |
| 全量回归 | `--suite all` 退出 0，无 skipped required | all report |
| Manifest 语义 | 五个既有 manifests 与 SPARQL 测试清单均通过 JSON Schema 和跨记录语义 checker；duplicate IDs、cross refs、hash 冲突均 fail closed | negative-control JSON |
| Suite 合同演进 | all 加入 SPARQL/quality/governance 内部 checks，`contract_version` 已 bump，无新公开 suite | registry/checker JSON |
| Runner 可追溯 | dispatcher、三类 checker、报告器和实际 helper 的源 SHA-256 已记录 | results/environment JSON |
| 完整性/边界 | Phase 前后 frozen 通过，staged/unstaged check、stat、name-status 已审查且未越界 | frozen/diff evidence |

## 10. AWAITING、BLOCKED 与 DEFERRED 规则

- 本阶段没有可延期的主线任务，不允许 `DEFERRED`。
- manifests、Phase 05 results 或 decisions 陈旧；任何 manifest/schema/跨记录语义检查、duplicate-ID/cross-reference negative control 失败；suite `contract_version` 未 bump；证据缺少 runner/helper hash；历史 CQ 回归；v0.4 CQ/quality/governance 任何必需检查失败；provenance 不能解析；指标无法给出可信分母；`all` 非零时，按 `human-intervention-policy.md` 停止写入并完成至多一次只读复现。存在具名修复或需要用户选择时标记 `AWAITING_HUMAN_DECISION`；诊断确认当前没有安全路径时标记 `BLOCKED`。
- 若问题来自 requirement、fixture、model 或 release manifest，记录最早受影响 Phase 和证据，说明需要回到该 Phase 处理，不在本阶段就地绕过或静默修改上游产出。
- Mermaid、Treehouse、ITB/SEMIC 和 GitHub 不属于本阶段；它们的缺席不记为本阶段 DEFERRED。

## 11. 阶段交接

全部验收通过后：

1. 在 `docs/v0.4/STATUS.md` 追加 Phase 06 小节，记录进入门槛、修改、命令/退出码、验收矩阵、证据、风险和 Phase 07 进入条件。
   风险处置引用 Phase 00 baseline snapshot risk ID；不回写该 snapshot，新增风险登记供 Phase 09 汇总。
2. 把 `docs/v0.4/CHECKPOINT.md` 清空回占位符状态。
3. 向 Phase 07 交付：四个业务 manifests、validation-suites `contract_version`/registry hash、SPARQL 测试清单/schema/语义校验证据、SPARQL/quality/governance 机器结果、runner/helper 源 hash、SSSOM、更新后的治理文件和明确的 breaking-change 结论。
4. 列出待人类审批的 governance 项，不把 pending 写成通过。
5. 报告 Git 状态，不 commit、不 push。

## 12. Stop

Phase 06 标记 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。不得开始最终文档、图表、handoff、CI、Treehouse 或 GitHub 发布。
