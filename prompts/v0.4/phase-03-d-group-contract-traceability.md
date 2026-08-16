# Phase 03 Prompt — D 组契约审计、需求追踪与兼容性决策

你位于仓库根目录。完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md`、本文件和 `docs/v0.4/STATUS.md` 中 Phase 00–02 小节，只执行 Phase 03。进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后停止。

## 1. 目标

把冻结的 D 组最终 SHACL TTL 转化为完整、稳定、可机读、可审查的 v0.4 requirements registry。为每条规范规则分配稳定 ID，追踪 source shape/path/severity/message/constraint component，建立 v0.3→v0.4 wire-profile 兼容矩阵、四状态分类规范、fixture 测试义务和阻塞性设计决策。

本阶段实现：

```text
.\scripts\validate.ps1 -Suite traceability
```

`frozen`、`environment`、`baseline` 必须继续通过；`v0.4-model`、`v0.4` 和 `all` 继续以 `NOT_IMPLEMENTED` 非零退出。

## 2. 非目标

- 不创建或修改 `model/v0.4/` 中的发布 artifact。
- 不复制、适配或发布 D 组 Shape。
- 不创建正式 fixture 文件或 `v0.4-test-cases.json`。
- 不实现完整四状态 validator；本阶段只冻结分类 oracle 和测试义务。
- 不更新治理、SSSOM、handoff、图表、CI 或最终 README 声明。
- 不修改任何 D 组收到的文件来解决矛盾。

## 3. 权威输入

按 Master 权威顺序完整读取：

- `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`
- `inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md`
- `inputs/d-group/v0.4/README.md`
- `inputs/d-group/v0.4/SHA256SUMS`
- `inputs/project/v0.4/806.md`
- `inputs/original-plan/DSSC_Minimal_Energy_Scenario/metadata/data-product-valid.jsonld`
- `inputs/original-plan/DSSC_Minimal_Energy_Scenario/metadata/data-product-invalid.jsonld`
- `inputs/original-plan/DSSC_Minimal_Energy_Scenario/shapes/building-energy-shapes.ttl`
- `C_Semantic_Treehouse/model/v0.3/building-energy-ontology.ttl`
- `C_Semantic_Treehouse/model/v0.3/data-product-context.jsonld`
- `C_Semantic_Treehouse/model/v0.3/data-product-metadata-shapes.ttl`
- v0.3 Energy Reading Record artifacts
- `docs/v0.4/v0-errata.md`
- Phase 02 baseline manifest、结果和 runner 基础设施
- `C_Semantic_Treehouse/manifests/validation-suites.json` 及 schema

D 组 TTL 是规范性可执行契约。修改说明中的自然语言用于解释和发现问题；它不能改写 TTL 的实际行为。

## 4. 进入门槛

1. Phase 00–02 均在 `STATUS.md` 中记录为 `COMPLETE`。
2. `frozen`、`environment`、`baseline` suites 在当前 host 返回 0。
3. Docker `baseline` suite 返回 0。
4. D 组 `SHA256SUMS` 与冻结 manifest 均通过。
5. D 组 TTL 能作为 Turtle 解析；若无法解析，记录输入 hash 和解析错误。需要 D 组提供、纠正或确认输入时标记 `AWAITING_HUMAN_DECISION`；已经确认当前没有可用规范输入或安全替代路径时标记 `BLOCKED`。
6. `docs/v0.4/CHECKPOINT.md` 为空闲。
7. requirements registry 路径没有会被覆盖的用户修改。

若 D TTL 与说明存在差异，可继续完成不受影响的只读审计；任何会改变 v0.4 实现的未决语义冲突必须标记 `AWAITING_HUMAN_DECISION` 并停止，直到取得规定角色的明确 decision。两种停止情况都先把当前进度写入 `CHECKPOINT.md`。

## 5. 可写路径

仅允许创建或修改：

- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
- `C_Semantic_Treehouse/manifests/schemas/v0.4-requirements.schema.json`
- `C_Semantic_Treehouse/manifests/validation-suites.json`，仅更新 `traceability` 及组合 `all` 的状态/组成并 bump `contract_version`
- `scripts/` 下由 Phase 01 受控 entrypoint catalog 发现的 traceability checker、TTL extractor 和确定性报告生成器；不含通用 dispatcher、doctor 或包装脚本
- `docs/v0.4/requirements-traceability.md`
- `docs/v0.4/compatibility-matrix.md`
- `docs/v0.4/result-classification.md`
- `docs/v0.4/test-plan.md`
- `docs/v0.4/decisions/**`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`
- `build/phase-03/**`

若需要为 manifest schema 建立通用、已在 Phase 02 使用的 helper，这属于上游共享合同变更：按 `human-intervention-policy.md` 停下来说明需要改动的内容和影响，取得确认后再改，并重新运行 Phase 02 baseline。

## 6. 保护路径

除 Master 永久保护范围外，本 Phase 还保护：

- `prompts/**`
- `C_Semantic_Treehouse/manifests/baseline-test-cases.json` 及其 schema
- `C_Semantic_Treehouse/manifests/release-manifest.json`
- `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
- `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`
- `C_Semantic_Treehouse/model/v0.4/**`
- `C_Semantic_Treehouse/fixtures/v0.4/**`
- `C_Semantic_Treehouse/evidence/**`
- `C_Semantic_Treehouse/tests/sparql/**`
- governance、mappings、handoff、quality、diagrams、`.github/**`
- `scripts/validate.py`、`scripts/doctor.py` 和平台包装；发现 dispatcher 缺陷时按 `human-intervention-policy.md` 记录问题并停下来找人确认，不在本 Phase 直接修改

不得让 traceability checker 自动修改 expected requirements registry。

## 7. 任务

### 7.1 审计 D 组输入完整性和 SHACL 结构

1. 校验 D 组 TTL 和说明文件 hash。
2. 解析 TTL，运行 shapes graph 的 Meta-SHACL 检查。
3. 确定性提取：
   - 所有命名 NodeShape、PropertyShape。
   - targetClass、targetNode。
   - property 引用和 Closed Shape allowlist。
   - path、severity、message。
   - min/max count、datatype、nodeKind、minLength、pattern、`sh:in`。
   - SPARQL constraint 及 query hash。
4. 把 TTL header 中的四状态说明作为来源定位信息记录；它不伪装成 SHACL constraint。
5. 对照修改说明，登记一致项、表述差异和需决策问题。

### 7.2 建立 requirements schema

创建 `C_Semantic_Treehouse/manifests/schemas/v0.4-requirements.schema.json`。至少要求：

- schema version、profile ID、normative source path/hash。
- 唯一且符合 `D04-RNNN` 格式的 requirement ID。
- 规范性/操作性来源类型。
- target、source shape、path、severity、message、constraint components。
- 人类可读业务规则。
- 正/负边界和 test obligations。
- 预期业务状态。
- v0.3 compatibility impact。
- implementation 状态和后续 artifact/fixture/evidence 引用字段。
- issue/decision 引用。

schema 应允许本阶段把后续 artifact/fixture 标为 `PLANNED`，同时要求每条规则至少一个明确 test obligation。它必须拒绝空规则集、绝对路径、未知状态和缺少 source locator 的记录。

JSON Schema 之外必须实现 requirements 跨记录语义校验器，检查 duplicate requirement/test-obligation IDs、source shape/component 的双向覆盖、requirement 到 decision/planned case/source locator 的 cross-reference、同一 source constraint 的冲突映射和 planned case ID 冲突。duplicate IDs 和悬空引用必须通过临时 registry negative controls 证明会非零失败。

### 7.3 建立稳定规则编号

在 `C_Semantic_Treehouse/manifests/v0.4-requirements.json` 至少登记以下规则；TTL 提取若发现额外规范约束，必须追加新 ID，不能静默合并：

| ID | 规范要求 | 主要 source shape |
|---|---|---|
| `D04-R001` | 提交图恰好包含一个 `dcat:Dataset` | `ex:DatasetCardinalityShape` |
| `D04-R002` | Dataset 节点必须是 IRI | `ex:BuildingEnergyDatasetShape` |
| `D04-R003` | `ex:datasetId` 必填、单值、非空白 `xsd:string` | `ex:DatasetIdShape` |
| `D04-R004` | `dct:title` 必填、单值、非空白 `xsd:string` | `ex:TitleShape` |
| `D04-R005` | `ex:providerName` 必填、单值、非空白 `xsd:string` | `ex:ProviderNameShape` |
| `D04-R006` | `dct:spatial` 必填、单值、非空白 `xsd:string` | `ex:SpatialShape` |
| `D04-R007` | `dct:accrualPeriodicity` 必填、单值 string、精确为 `hourly` | `ex:FrequencyShape` |
| `D04-R008` | `ex:unit` 必填、单值 string、精确为 `kWh` | `ex:UnitShape` |
| `D04-R009` | `dct:format` 必填、单值 string、精确为 `application/json` | `ex:FormatShape` |
| `D04-R010` | `dcat:endpointURL` 必填、单值 HTTPS IRI | `ex:EndpointUrlShape` |
| `D04-R011` | `ex:temporalStart` 必填、单值 `xsd:date` | `ex:TemporalStartShape` |
| `D04-R012` | `ex:temporalEnd` 必填、单值 `xsd:date` | `ex:TemporalEndShape` |
| `D04-R013` | temporalStart 不晚于 temporalEnd | `ex:TemporalOrderShape` |
| `D04-R014` | `dct:description` 可缺省；出现时最多一个 string | `ex:DescriptionShape` |
| `D04-R015` | `dct:license` 可缺省；出现时最多一个 HTTPS IRI | `ex:LicenseShape` |
| `D04-R016` | Dataset 的未声明属性产生 Warning 并映射 INAPPLICABLE | `ex:DatasetClosedShape` |
| `D04-R017` | SUT 输入解析/离线加载失败，或全部权威合同与依赖预检成功后的受控 validator/service runtime timeout、crash、基础设施故障映射 UNTESTABLE | TTL header 的结果映射说明 |

对于包含多个 SHACL component 的业务规则，registry 必须逐项列出 component，测试义务必须覆盖 min/max/type/value/pattern 等边界，不能只保留一句汇总描述。

### 7.4 冻结四状态分类

创建 `docs/v0.4/result-classification.md`，采用 Master 的确定性优先级：

1. 权威 Shape、manifest、harness 与必需依赖预检成功后，SUT 输入无法解析/离线加载，或 test manifest 具名且受控的 validator/service runtime fault 使可信验证无法完成 → `UNTESTABLE`。
2. report graph 至少一个 `sh:Violation` → `FAIL`；同时有 Warning 仍为 FAIL。
3. 无 Violation，且出现获准映射的 `ex:DatasetClosedShape` Warning → `INAPPLICABLE`。
4. 解析和验证成功、预期目标命中、无 Violation/Warning → `PASS`。

同时规定：

- pySHACL 的 `conforms` 布尔值不能直接充当业务状态。
- 未识别 source shape/severity、缺失 report 字段或结果结构异常形成程序 `ERROR`；业务判断不可被记录为可信 PASS。
- test manifest 的 expected business status 与 harness `SUCCESS`/`ERROR` 分开。
- 目标节点为 0 时程序 ERROR。
- `DatasetCardinalityShape` 的固定 `targetNode ex:ValidationSubmission` 需要在后续 harness 中显式断言已执行。

### 7.5 建立 v0.3→v0.4 兼容矩阵

`docs/v0.4/compatibility-matrix.md` 至少记录：

| v0.3 | v0.4 wire profile | 影响 |
|---|---|---|
| `be:DataProductMetadata` | `dcat:Dataset` | type 改变 |
| `dct:identifier` | `ex:datasetId` | path 改变 |
| 无显式 title 要求 | `dct:title` 必填 | 新必填字段 |
| `be:providerName` | `ex:providerName` | path 改变 |
| `be:endpointUrl` | `dcat:endpointURL` | path 与 HTTPS 强度改变 |
| `be:format = "JSON"` | `dct:format = "application/json"` | path/value 改变 |
| `be:frequency` | `dct:accrualPeriodicity` | path 改变 |
| `be:unit` | `ex:unit` | path 改变 |
| `be:spatialCoverage` | `dct:spatial` | path 改变 |
| `be:temporalStart/End` | `ex:temporalStart/End` | path 与顺序约束改变 |
| 未声明 optional | description/license 显式可选 | profile 增补 |
| `dct:conformsTo` 存在 | Closed Shape 未列入 allowlist | 产生 INAPPLICABLE |

结论写明：v0.4 是 wire-profile breaking migration，版本名称沿项目既定序列继续使用 v0.4。

### 7.6 形成阻塞性 ADR

至少创建并解决：

1. `docs/v0.4/decisions/ADR-001-dct-conforms-to.md`
   - 建议决定：被 D Shape 验证的 Dataset payload 不携带 `dct:conformsTo`；版本信息进入 release manifest/provenance；payload 携带时按当前 Closed Shape 映射 INAPPLICABLE。
2. `docs/v0.4/decisions/ADR-002-wire-profile-and-version-identity.md`
   - D 组 `ex:/dcat:/dct:` 是 wire paths；项目稳定 version IRI 不得重写这些路径。
3. `docs/v0.4/decisions/ADR-003-energy-record-inheritance.md`
   - D 组变更只针对 metadata；Energy Reading Record 保持 v0.3 合同，由 release manifest 显式继承，除非有新权威需求。

每个 ADR 包含 context、decision、依据、后果、替代方案、状态和人工批准记录。批准主体必须覆盖以下人类角色：

- 项目维护者或当前用户，确认仓库和发布决策。
- C 组相关语义/领域审阅者，确认模型、namespace、兼容性和 record 继承影响。
- D 组契约相关审阅者，确认 D TTL 的解释、Closed Shape 和四状态映射。

同一自然人可在项目明确允许时承担多个角色，但每个角色都要分别记录姓名或可审计身份、批准日期、批准范围和证据引用。AI、自动化 agent 和验证器只能整理选项与证据，不能自批、代签、推断沉默即批准，也不能把自己列为 reviewer。任何必需人工角色未明确批准、批准证据缺失，或 ADR 仍为 `PROPOSED` 时，Phase 03 必须标记 `AWAITING_HUMAN_DECISION` 并停止；不得由 AI 将状态直接改为 `ACCEPTED` 后继续。`human-intervention-policy.md` 里的一般性人工确认不能替代这里要求的三类具名角色批准。

### 7.7 建立测试义务计划

创建 `docs/v0.4/test-plan.md`。本阶段只定义 planned case IDs、单轴变异、覆盖规则和预期状态，不创建 fixture 文件或 test-case manifest。

至少覆盖：

- 0、1、2 个 Dataset；IRI 和 blank node。
- datasetId/title/providerName/spatial 的缺失、多值、非 string、空串、空白串。
- frequency 的缺失、多值、非 string、错误值和大小写错误。
- unit/format 的缺失、多值绕过、非 string、错误值。
- endpoint 的缺失、多值、普通 string、HTTP IRI、HTTPS IRI。
- temporalStart/End 的缺失、多值、错误 datatype、边界相等和倒序。
- description/license 的缺省、合法值、多值、错误类型/scheme。
- 单一额外属性 → INAPPLICABLE。
- 额外属性与 Violation 同时出现 → FAIL。
- 作为 SUT 的 malformed JSON、无效 JSON-LD、SUT 所需本地 context 缺失，以及全部权威合同/依赖预检通过后的受控 validator timeout/crash/service runtime fault → UNTESTABLE；权威 Shape、manifest、harness 或核心依赖故障形成程序 `ERROR`。

优先让一个 planned fixture 只引入一个主要变异。每条 requirement 至少有一个正向和一个负向/边界 test obligation；操作性 R017 必须有可控的 harness fault injection 计划。

### 7.8 实现 traceability suite

实现并登记受控 traceability checker entrypoint，使 registry 驱动的 `traceability`：

- 校验 requirements manifest schema、路径和 source hashes。
- 解析 D TTL 并与 registry 双向比较。
- 检查所有命名 Shape、component、path、severity、message 和 SPARQL constraint 均有 requirement 覆盖。
- 检查所有 requirement 至少有 test obligations。
- 检查 compatibility/ADR 引用存在且阻塞性 ADR 已接受。
- 检查规则 ID、source shape 和 planned case ID 唯一。
- 生成确定性 JSON 和 Markdown。
- 在证据中记录 requirements manifest/schema、suite registry、`scripts/validate.py`、TTL extractor、traceability checker、报告生成器和全部实际加载 helper 的仓库相对路径与 SHA-256。

后续 artifact/fixture 尚未创建的 `PLANNED` 引用在本阶段可接受；缺少测试义务不可接受。

### 7.9 源契约只读烟测

在不创建发布模型的情况下，以 D 原始 TTL 验证冻结原始 valid/invalid metadata，作为契约理解证据：

- valid 样例应无 Violation/Warning，且目标实际命中。
- invalid 样例应命中 providerName、unit、temporalEnd 对应规则。

若实际行为与 D 组说明不同，把差异登记为 issue。差异会影响实现时标记 `AWAITING_HUMAN_DECISION` 并停止；经确认不存在可执行的安全契约时使用 `BLOCKED`。不得修改原件或 expected 以获得一致。

### 7.10 更新版本化 suite 注册表

只更新 `validation-suites.json` 中的 `traceability` 和组合 `all`：

- `traceability` 标记 `IMPLEMENTED`，组成明确指向 requirements schema、跨记录语义 checker、D TTL 双向覆盖和 ADR 审批检查。
- `all` 纳入 traceability 组成，仍保持 `NOT_IMPLEMENTED`，因为后续公开必需 suite 尚未齐备。
- 状态或组成变化必须 bump 顶层 `contract_version`；新的 `contract_version`/registry SHA-256 进入 host/Docker 证据。
- 不新增公开 suite 名或其他合同版本字段。

重跑 validation-suites 的 duplicate ID、悬空 dependency、dependency cycle、0 component、unknown entrypoint、重复 component 和 shell-command payload negative controls。

## 8. 必需产物

- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
- `C_Semantic_Treehouse/manifests/schemas/v0.4-requirements.schema.json`
- `docs/v0.4/requirements-traceability.md`
- `docs/v0.4/compatibility-matrix.md`
- `docs/v0.4/result-classification.md`
- `docs/v0.4/test-plan.md`
- 三份已接受 ADR
- traceability suite 和 source-contract audit 报告
- 更新后的 validation-suites `contract_version`/registry hash 和语义校验证据
- `docs/v0.4/STATUS.md` 中的 Phase 03 小节

Markdown 追踪表应由或可机械核对机器 registry，不能形成第二套不一致 oracle。

本阶段对风险的处置引用 Phase 00 baseline snapshot risk ID 并写入 Phase 03 小节；`docs/v0.4/risk-register.md` 保持只读，新风险登记供 Phase 09 汇总。

## 9. 必需命令

Host：

```powershell
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
```

前四条必须返回 0；最后一条必须以 `NOT_IMPLEMENTED` 非零退出。

直接入口：

```text
.\.venv\Scripts\python.exe scripts\validate.py --suite traceability
```

Docker：

```text
docker compose -f docker-compose.validation.yml run --rm validation --suite baseline
docker compose -f docker-compose.validation.yml run --rm validation --suite traceability
docker compose -f docker-compose.validation.yml run --rm validation --suite v0.4
```

前两条必须返回 0；最后一条必须以 `NOT_IMPLEMENTED` 非零退出。

在 `build/phase-03/negative-controls/` 的临时 manifest 上证明以下情况非零失败：

- source hash 错误。
- 删除一个命名 Shape 的 requirement。
- 重复 requirement ID。
- 重复 planned case/test-obligation ID。
- requirement 到 decision、source shape 或 planned case 的悬空 cross-reference。
- 空 test obligations。
- 未知 business status/severity。
- 阻塞性 ADR 未接受。
- validation-suites 重复 suite ID、悬空 dependency、dependency cycle、0 component、unknown entrypoint、重复 component 或 shell-command payload。

完成后运行：

```text
.\scripts\validate.ps1 -Suite frozen
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
git status --short
```

## 10. 验收矩阵

| ID | 验收项 | 通过条件 | 证据 |
|---|---|---|---|
| P03-A01 | D 输入完整性 | TTL/说明 hash 与冻结 manifest 一致 | traceability JSON |
| P03-A02 | SHACL 结构 | Turtle 和 Meta-SHACL 通过，提取结果稳定 | contract audit |
| P03-A03 | 规则覆盖 | 所有命名 Shape、components、SPARQL 和操作性映射均有稳定 requirement ID | 双向覆盖结果 |
| P03-A04 | 规则细度 | R001–R017 各自包含 source、边界和 test obligations | requirements JSON |
| P03-A05 | 四状态 | 优先级、程序状态、空目标和未知结果处理无歧义 | classification 文档/schema |
| P03-A06 | 兼容矩阵 | v0.3→v0.4 所有 type/path/value/constraint 变化已记录 | compatibility matrix |
| P03-A07 | ADR 人工批准 | conformsTo、wire identity、record inheritance 均有维护者/用户、C 组领域审阅者、D 组契约审阅者的可审计批准；AI 不在批准主体中 | ADR 文件、批准证据 |
| P03-A08 | 测试计划 | 每条 requirement 有正向和负向/边界义务，四状态均覆盖 | test-plan、checker |
| P03-A09 | 源烟测 | 冻结 valid/invalid 的实际结果与契约说明一致 | report graph audit |
| P03-A10 | Host/Docker | traceability 在两环境返回 0且规范化结果一致 | comparison JSON |
| P03-A11 | Negative controls | 指定 registry 破坏均被 checker 拒绝 | control report |
| P03-A12 | 未实现 suite | v0.4-model、v0.4、all 返回 NOT_IMPLEMENTED 非零 | 命令输出 |
| P03-A13 | 回归保护 | baseline 继续通过，冻结校验前后返回 0 | suite 输出 |
| P03-A14 | 修改范围 | 无 model、fixture、baseline oracle 或冻结输入变化 | diff 审查 |
| P03-A15 | 跨记录语义 | duplicate IDs、悬空 cross-references 和冲突映射均被 requirements checker 拒绝 | semantic-control JSON |
| P03-A16 | Suite 合同演进 | traceability 已实现、all 仍 NOT_IMPLEMENTED，`contract_version` 已 bump 并记录 hash | registry/checker JSON |
| P03-A17 | Runner 可追溯 | validate、extractor、checker、报告器和实际加载 helper 的源 SHA-256 已记录 | suite evidence |
| P03-A18 | Staged diff | staged/unstaged check、stat、name-status 均审查且未越界 | Git 命令输出 |

P03-A01 至 P03-A18 全部通过后才可标记 COMPLETE。

## 11. AWAITING 与 BLOCKED 规则

以下情况需要先完成安全诊断：

- D TTL hash 不匹配、无法解析或 Meta-SHACL 失败。
- 任一命名 Shape、constraint component 或状态映射无法追踪。
- 任一 requirement 缺少测试义务。
- requirements/validation-suites 的跨记录语义校验或 duplicate-ID negative control 失败。
- `contract_version` 未随组成变化 bump，或证据缺少 registry/runner/helper hash。
- traceability 在 host/Docker 结果不同。
- 唯一可行路径要求修改 D 原件或 baseline oracle。

TTL 与说明/样例存在会影响实现的冲突、四状态/unknown-result 行为未确定，或 ADR 尚未取得规定人类角色批准时标记 `AWAITING_HUMAN_DECISION`。其余情况经诊断确认没有可批准的安全路径时标记 `BLOCKED`。两种情况都按 `human-intervention-policy.md` 把提取结果、冲突定位和所需决定写入 `CHECKPOINT.md`，然后停止主线。

## 12. 交接

Phase 04 的进入包必须包含：

- `STATUS.md` 中 Phase 03 `COMPLETE` 小节。
- requirements manifest/schema 路径和 SHA-256。
- 完整规则 ID 清单和 TTL 双向覆盖证据。
- 已接受的三个 ADR，以及维护者/用户、C 组领域审阅者、D 组契约审阅者的身份、日期、范围和批准证据引用。
- compatibility matrix 和 result-classification oracle。
- planned test obligations；明确正式 fixtures/test-case manifest 留给 Phase 05。
- 冻结 valid/invalid 源烟测结果。
- validation-suites `contract_version`/registry hash 和 runner/helper 源 hash 清单。
- `CHECKPOINT.md` 为空闲状态的确认。

Phase 04 必须从这些决定派生模型和 release manifest，不得重新解释或弱化 D 组约束。

## 13. Stop

完成 `STATUS.md` 中 Phase 03 小节、审查 staged/unstaged diff、通过 baseline 和最终冻结校验后立即停止。不要复制 D TTL 到 `model/v0.4/`，不要创建 release manifest 或 fixtures，不要开始 Phase 04。
