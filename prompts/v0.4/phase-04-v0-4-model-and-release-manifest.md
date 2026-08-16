# Phase 04 Prompt — v0.4 派生模型与统一 Release Manifest

你位于仓库根目录。完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md`、本文件、`docs/v0.4/STATUS.md` 中 Phase 00–03 小节和已接受 ADR，只执行 Phase 04。进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后停止。

## 1. 目标

从冻结的 D 组 TTL 和 Phase 03 requirements registry 派生完整、可追溯的 v0.4 metadata 发布模型；保留 v0.3 Energy Reading Record 合同并通过 manifest 显式继承；建立覆盖 v0.1–v0.4 的统一 release manifest、schema、artifact hashes 和 model smoke suite。

本阶段实现：

```text
.\scripts\validate.ps1 -Suite v0.4-model
```

`frozen`、`environment`、`baseline`、`traceability` 必须继续通过；`v0.4` 和 `all` 继续以 `NOT_IMPLEMENTED` 非零退出。完整四状态 fixtures 和 `v0.4-test-cases.json` 属于 Phase 05。

## 2. 非目标

- 不修改 D 组收到的 TTL 或说明。
- 不改写 v0.1–v0.3，也不把 v0.3 metadata Shape 改名充当 v0.4。
- 不创建 PASS/FAIL/INAPPLICABLE/UNTESTABLE fixture 集合。
- 不创建 `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`。
- 不实现最终 `v0.4` 或 `all` suite。
- 不完成 SPARQL 扩展、质量、SSSOM、governance、provenance、handoff、图表、CI 或发布。
- 不通过复制 record 文件制造没有语义变化的新版本，除非课程的物理自包含要求已形成显式新 ADR。

## 3. 权威输入

完整读取：

- `C_Semantic_Treehouse/manifests/v0.4-requirements.json` 及 schema
- `docs/v0.4/requirements-traceability.md`
- `docs/v0.4/compatibility-matrix.md`
- `docs/v0.4/result-classification.md`
- Phase 03 已接受的 ADR
- D 组 TTL、说明和 `SHA256SUMS`
- 原始 valid/invalid metadata
- v0.1–v0.3 全部模型 artifact 和冻结 hashes
- v0.3 Energy Reading Record Shape、context、JSON Schema、OpenAPI 和 examples
- `docs/version-naming.md`
- 现有 governance release/namespace/changelog 文档，仅用于避免冲突，不在本阶段全面改写
- Phase 02 baseline manifest 和 Phase 03 traceability 结果
- `C_Semantic_Treehouse/manifests/validation-suites.json` 及 schema

v0.4 wire paths 和约束完全由 D 组 TTL决定。项目 version IRI、artifact packaging 和 record 继承由 Phase 03 已接受 ADR 决定。

## 4. 进入门槛

1. Phase 00–03 均在 `STATUS.md` 中记录为 `COMPLETE`。
2. `frozen`、`environment`、`baseline`、`traceability` 在 host 返回 0。
3. Docker `traceability` 返回 0。
4. `v0.4-requirements.json` hash 与 `STATUS.md` 中 Phase 03 小节一致。
5. `ADR-001`、`ADR-002`、`ADR-003` 状态均为 `ACCEPTED`，且记录了 Phase 03 要求的人类批准主体、日期、范围和证据；AI 不能成为批准者。
6. D 组输入和 v0.1–v0.3 冻结校验通过。
7. `docs/v0.4/CHECKPOINT.md` 为空闲。
8. `model/v0.4/` 中只有已知骨架或可安全保留的用户修改。

任何阻塞性 ADR 未接受、D Shape hash 漂移或 requirements 不能机械覆盖 Shape 时，先完成安全诊断。这类问题多半根源在 Phase 03：需要回去补齐 ADR 批准或修正 registry 时标记 `AWAITING_HUMAN_DECISION` 并说明应该回到哪个 Phase；确认当前没有安全路径时标记 `BLOCKED`。两种情况都先把当前进度写入 `CHECKPOINT.md`。

## 5. 可写路径

仅允许创建或修改：

- `C_Semantic_Treehouse/model/v0.4/**`
- `C_Semantic_Treehouse/manifests/release-manifest.json`
- `C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json`
- `C_Semantic_Treehouse/manifests/validation-suites.json`，仅更新 `v0.4-model` 和组合 `all` 并 bump `contract_version`
- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`，仅补充 implementation artifact/hash 引用；规则语义和 oracle 字段不得改变
- `.gitattributes`，仅允许为 D Shape 的字节级派生目标增加精确 `-text` 规则
- `docs/v0.4/requirements-traceability.md`，仅同步已实现 artifact 引用
- `docs/v0.4/model-derivation.md`
- `docs/v0.4/compatibility-v0.3-v0.4.md`
- `scripts/` 下由 Phase 01 受控 entrypoint catalog 发现的 release-manifest/model checker、hash 和报告模块；不含通用 dispatcher、doctor 或包装脚本
- `C_Semantic_Treehouse/evidence/releases/v0.4/model/**`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`
- `build/phase-04/**`

若修改 requirements registry 的 implementation 引用，必须保存 Phase 03 原 hash、新 hash和"语义字段未变化"的机器比较证据。

## 6. 保护路径

除 Master 永久保护范围外，本 Phase 还保护：

- `prompts/**`
- `C_Semantic_Treehouse/manifests/baseline-test-cases.json` 及 schema
- `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
- 除 release schema 外的 manifest schemas；requirements schema 只有发现自相矛盾时可触发 BLOCKED，不能在本 Phase 静默放宽
- `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`
- `C_Semantic_Treehouse/fixtures/v0.4/**`
- `C_Semantic_Treehouse/tests/sparql/**`
- governance、mappings、handoff、quality、diagrams、`.github/**`
- Phase 02 baseline 发布证据
- `scripts/validate.py`、`scripts/doctor.py` 和平台包装；发现 dispatcher 缺陷时按 `human-intervention-policy.md` 记录问题并停下来找人确认，不在本 Phase 直接修改

不得通过修改 `.gitattributes` 让派生 Shape 的 hash 比较失真。

## 7. 任务

### 7.1 建立 v0.4 发布目录

将 `C_Semantic_Treehouse/model/v0.4/README.md` 从骨架更新为真实发布说明，并创建：

- `building-energy-ontology.ttl`
- `data-product-metadata-shapes.ttl`
- `data-product-context.jsonld`
- `data-product-valid.jsonld`
- `SHA256SUMS`

目录 README 至少说明：

- metadata wire profile 的权威来源。
- D Shape 的派生方式。
- version IRI 与 wire namespace 的区别。
- `dct:conformsTo` 的 ADR 处理。
- Energy Reading Record 的 v0.3 继承关系。
- fixtures/harness 的规范位置、manifest 引用和状态由 `C_Semantic_Treehouse/manifests/v0.4-test-cases.json` 与 `docs/v0.4/STATUS.md` 独立追踪；本 model README 只描述稳定接口和引用，不写会随阶段推进而陈旧的"待完成/已完成"状态。

`SHA256SUMS` 使用仓库相对 POSIX 路径、稳定排序并覆盖本目录的发布 artifacts；它不列出自身，避免递归 hash。

### 7.2 字节级派生 D Shape

默认把：

```text
inputs/d-group/v0.4/received/building-energy-shapes_D.ttl
```

以字节级副本派生为：

```text
C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl
```

要求：

- source 和 target SHA-256 完全相同。
- release manifest 标记 `transformation: byte-copy`。
- 不在派生 Shape 内增加 provenance 注释、格式化或换行转换。
- provenance、version 和适配说明放入 manifest/README/derivation 文档。
- 在 `.gitattributes` 中为该目标文件增加精确 `-text` 规则，并用 `git check-attr -a -- <path>` 证明 Git checkout 不会进行行尾转换；不得把整个可编辑 v0.4 目录粗略设为 binary。

若已接受 ADR 明确要求适配，仍保留上述字节副本为 normative contract，并另建名称清楚的 adaptation；release manifest 必须分别标记角色。没有已接受 ADR 时不得适配。

### 7.3 创建 v0.4 ontology/profile 描述

`building-energy-ontology.ttl` 应：

- 使用项目已批准的 v0.4 version IRI，并声明 prior version。
- 明确本版本是 metadata wire-profile breaking migration。
- 复用标准 `dcat:Dataset`，声明 D wire profile 使用的必要 `ex:` 本地属性。
- 对本地属性提供最小、准确的 label/comment/domain/range。
- 保持 `ex:`、`dcat:`、`dct:` 路径与 D Shape 一致。
- 不把旧 `be:*` metadata paths 偷换回 v0.4 wire profile。
- 不声称改变 Energy Reading Record；record 合同由 release manifest 引用 v0.3。

ontology 提供语义说明，不能弱化或替代 SHACL 约束。

### 7.4 创建本地 JSON-LD context 和 canonical valid example

`data-product-context.jsonld` 应把项目字段映射到 D 组准确 paths，包括 Dataset type、datasetId、title、description、providerName、license、spatial、frequency、unit、temporalStart/End、endpointUrl 和 format。IRI/date coercion 与 Shape 一致。

`data-product-valid.jsonld` 应：

- 使用本地 sibling context，离线可展开。
- 恰好包含一个 IRI `dcat:Dataset`。
- 保留场景 Dataset ID `building-energy-hourly-v1`。
- 使用 `application/json`、`hourly`、`kWh`、HTTPS endpoint 和合法日期顺序。
- 根据 ADR 不在受 Closed Shape 约束的 Dataset 上写 `dct:conformsTo`。
- 可包含合法 description/license，以证明可选字段；Phase 05 另建无可选字段 PASS fixture。

原始 valid metadata 是场景来源。新文件是带明确 provenance 的派生产物，不能覆盖原始文件。

### 7.5 建立 release manifest schema

创建 `C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json`。至少要求：

- schema version 和唯一 `currentRelease`。
- releases 数组包含 v0.1、v0.2、v0.3、v0.4。
- 每个 release 的 ID、status、version IRI、root、prior release、compatibility classification。
- 每个 artifact 的 role、仓库相对 POSIX path、media type、SHA-256、origin 类型。
- derived artifact 的 source path/hash 和 transformation。
- inherited artifact 的 `inheritedFrom`、path/hash 和 `change: none`。
- normative inputs、applicable validators 和 requirement registry 引用。
- 禁止绝对路径、路径逃逸、glob 和未知 origin/status。

manifest 不列出自身 hash，避免递归。其 hash记录在验证证据中。

JSON Schema 之外必须实现 release manifest 跨记录语义校验器，检查 duplicate release/artifact IDs、current/prior/inherited/source/requirement/validator cross-references、继承环、同一路径多 hash、currentRelease 唯一性和 v0.1–v0.4 完整集合。使用临时副本证明 duplicate IDs 与各类悬空引用均非零失败。

### 7.6 建立统一 release manifest

创建 `C_Semantic_Treehouse/manifests/release-manifest.json`：

- v0.1–v0.3 标记 `frozen`，artifact paths/hashes 与冻结文件一致。
- v0.4 标记 `current`，列出本阶段新 metadata artifacts。
- v0.4 normative source 指向 D TTL 及 hash。
- v0.4 requirements 指向 `v0.4-requirements.json` 及当前 hash。
- compatibility 明确为 wire-profile breaking。
- version identity 与 ADR 一致。
- 不使用不存在的 fixture/test-case 路径。

Energy Reading Record 使用 manifest 继承：

- `inheritedFrom: v0.3`
- Shape、context、valid/invalid examples、JSON Schema、OpenAPI 的实际 v0.3 path/hash
- `change: none`

若课程要求物理自包含且已有新 ADR，可字节复制 record artifacts；hash 和继承说明仍需保留，且不得修改冻结源。

### 7.7 记录派生和兼容性

创建 `docs/v0.4/model-derivation.md`：

- 每个 v0.4 artifact 的来源、转换、source/target hash。
- D Shape 的 byte-copy 证明。
- context/example/ontology 的人工派生依据和审查点。
- requirements implementation 引用的更新。

创建 `docs/v0.4/compatibility-v0.3-v0.4.md`：

- wire-profile breaking 影响。
- A/D 组未来集成影响，完整 handoff 留给 Phase 07。
- record 不变范围。
- payload 版本标记策略。
- 升级时需要的字段/path/value 转换。

### 7.8 更新 requirements implementation 链接

只更新 `v0.4-requirements.json` 的 implementation 部分：

- 每条 D 规则映射到发布 Shape 和必要 ontology/context artifact。
- source semantics、severity、path、message、test obligations 和预期状态保持与 Phase 03 完全一致。
- 保存语义字段规范化前后比较。任何语义变化都说明 Phase 03 的产出可能需要修正：按 `human-intervention-policy.md` 停下来，说明发现的具体差异和证据，取得用户确认后再决定是回到 Phase 03 修正，还是在记录清楚的前提下于 Phase 04 内调整。不得自行静默改写 Phase 03 语义来让本阶段通过。

### 7.9 实现 release/model checker

实现并登记受控 `v0.4-model` checker entrypoint；通用 dispatcher 依据 registry 调用并执行：

1. 验证 release manifest schema。
2. 检查所有路径在仓库内、文件存在、非空且 hash 匹配。
3. 检查 v0.1–v0.3 entries 与冻结 manifest 一致。
4. 检查 v0.4 Shape 与 D 原件字节/hash 一致。
5. 消费 Phase 03 的 D Meta-SHACL 通过证据，同时在本次运行重新校验 Shape hash 并解析全部新 Turtle；陈旧证据不能替代当前 hash/parse。
6. 解析并离线展开 context/example。
7. 检查 requirements implementation coverage。
8. 解析继承的 record artifacts，并检查其 hashes。
9. 运行最小 contract smoke。
10. 生成确定性 JSON、机器环境 JSON 和 Markdown。
11. 证据记录 release/requirements/suite manifests 与 schemas、`scripts/validate.py`、release/model checker、hash/JSON-LD/SHACL/report helper 的仓库相对路径和 SHA-256。

### 7.10 最小 contract smoke

本阶段 smoke 只证明发布模型可供 Phase 05 使用：

validator 调用必须显式启用 D 契约依赖的 SHACL-SPARQL/advanced 能力、固定 inference 策略并记录 lock 中的 pySHACL 版本；不得依赖库默认值。每个 fixture 的提交数据单独构成 data graph，ontology、Shape、manifest 和 provenance 不得合并进该 graph，以免改变全图 Dataset cardinality。另使用临时 0 Dataset、2 Dataset 和 temporal 倒序 controls，证明提交数量与时间顺序 SPARQL constraints 确实执行。

- canonical v0.4 valid example：目标实际命中、0 Violation、0 Warning。
- 冻结原始 invalid example：业务 FAIL，至少准确命中：
  - `D04-R005` / `ex:ProviderNameShape`
  - `D04-R008` / `ex:UnitShape`
  - `D04-R012` / `ex:TemporalEndShape`
- 一个只在临时目录加入 `dct:conformsTo` 的 canonical copy：无 Violation，命中 `ex:DatasetClosedShape` Warning，结果符合 ADR 的 INAPPLICABLE 预期。

smoke 必须解析 report graph 和 target；不得以 `conforms` 布尔值代替。临时 copy 不进入 model 或 fixtures。

### 7.11 保持后续 suite fail closed

完成后确认 `v0.4` 和 `all` 仍返回非零 `NOT_IMPLEMENTED`。`v0.4-model` 不能发现或声称已执行 Phase 05 fixtures。

### 7.12 更新版本化 suite 注册表

只更新 `validation-suites.json` 中的 `v0.4-model` 和组合 `all`：

- `v0.4-model` 标记 `IMPLEMENTED`，组成指向 release schema、跨记录语义 checker、artifact/hash/derivation/inheritance 检查和 contract smoke。
- `all` 纳入 `v0.4-model`，仍保持 `NOT_IMPLEMENTED`；公开必需 `v0.4` suite 尚未实现。
- 任何状态或组成变化 bump 顶层 `contract_version`，新的 `contract_version`/registry SHA-256 进入 host/Docker 证据。
- 不新增公开 suite 名或其他合同版本字段。

重跑 validation-suites duplicate ID、悬空 dependency、dependency cycle、0 component、unknown entrypoint、重复 component 和 shell-command payload negative controls。

## 8. 必需产物

- `C_Semantic_Treehouse/model/v0.4/` 中完整 metadata 发布 artifact 和 SHA256SUMS
- `C_Semantic_Treehouse/manifests/release-manifest.json`
- `C_Semantic_Treehouse/manifests/schemas/release-manifest.schema.json`
- 更新后的 requirements implementation 链接及语义不变证明
- release/model checker 与 `v0.4-model` suite
- model derivation 和 compatibility 文档
- host/Docker model smoke 结果及规范化比较
- 经审核的 `evidence/releases/v0.4/model/` 证据
- 更新后的 validation-suites `contract_version`/registry hash 和语义校验证据
- `docs/v0.4/STATUS.md` 中的 Phase 04 小节

Phase 04 小节使用 Phase 00 baseline snapshot risk ID 记录风险处置；不回写 `docs/v0.4/risk-register.md`，新增风险留在 `STATUS.md` 并交给 Phase 09 汇总。

## 9. 必需命令

Host：

```powershell
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
.\scripts\validate.ps1 -Suite v0.4
.\scripts\validate.ps1 -Suite all
```

前五条必须返回 0；最后两条必须以 `NOT_IMPLEMENTED` 非零退出。

直接入口：

```text
.\.venv\Scripts\python.exe scripts\validate.py --suite v0.4-model
```

Docker：

```text
docker compose -f docker-compose.validation.yml run --rm validation --suite baseline
docker compose -f docker-compose.validation.yml run --rm validation --suite traceability
docker compose -f docker-compose.validation.yml run --rm validation --suite v0.4-model
docker compose -f docker-compose.validation.yml run --rm validation --suite v0.4
```

前三条必须返回 0；最后一条必须以 `NOT_IMPLEMENTED` 非零退出。

在 `build/phase-04/negative-controls/` 的临时副本上证明以下情况非零失败：

- release manifest 使用绝对路径或 `../` 路径逃逸。
- artifact 缺失、为空或 hash 不匹配。
- D source hash 或 byte-copy target 改变。
- v0.1–v0.3 frozen entry 漂移。
- record inherited hash 漂移。
- currentRelease 缺失、重复或不等于 v0.4。
- duplicate release/artifact IDs，或 prior/inherited/source/requirement/validator 悬空 cross-reference。
- requirements implementation 遗漏一条规则。
- requirements duplicate ID，或 implementation artifact/decision 的悬空 cross-reference。
- SHACL target 为 0。
- validation-suites duplicate suite ID、悬空 dependency、dependency cycle、0 component、unknown entrypoint、重复 component 或 shell-command payload。

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
| P04-A01 | D Shape 派生 | release Shape 与冻结 D TTL 字节和 SHA-256 完全一致，目标文件具有精确 `-text` 属性 | hash/byte compare JSON、`git check-attr` |
| P04-A02 | v0.4 ontology | Turtle 可解析，version/prior/breaking 边界和 D wire terms 准确 | parser/result review |
| P04-A03 | Context/example | 本地离线展开成功，canonical graph 恰好一个 IRI Dataset | JSON-LD result |
| P04-A04 | Release schema | 拒绝绝对路径、路径逃逸、空/重复 release 和未知 origin | schema controls |
| P04-A05 | 历史 releases | v0.1–v0.3 artifact hashes 与冻结 manifest 一致 | manifest checker |
| P04-A06 | v0.4 release | current release 唯一，artifact/source/requirements 引用全部存在且 hash 匹配 | checker JSON |
| P04-A07 | Record 继承 | 所有继承 artifact 可解析、hash 与 v0.3 一致、change=none | inheritance audit |
| P04-A08 | Requirements 实现 | R001–R017 全部映射到 artifact，Phase 03 语义字段零变化 | semantic diff JSON |
| P04-A09 | Valid smoke | canonical valid 目标命中、0 Violation/Warning | report graph JSON |
| P04-A10 | Invalid smoke | 原始 invalid 准确命中 R005、R008、R012 | report assertions |
| P04-A11 | conformsTo ADR | 临时 control 仅命中 ClosedShape Warning 并符合 INAPPLICABLE 决策 | control JSON |
| P04-A12 | Host/Docker | v0.4-model 两环境返回 0且规范化结果一致 | comparison JSON |
| P04-A13 | Negative controls | 指定 manifest/hash/target 破坏均非零失败 | control report |
| P04-A14 | 后续 suite 保护 | v0.4、all 均返回 NOT_IMPLEMENTED 非零 | 命令输出 |
| P04-A15 | 全链回归 | frozen、environment、baseline、traceability 均继续通过 | suite outputs |
| P04-A16 | 修改范围 | 无 fixture、test-case manifest、冻结路径或越界文档变化 | diff 审查 |
| P04-A17 | 跨记录语义 | duplicate IDs、悬空 cross-references、继承环和同路径多 hash 均被拒绝 | semantic-control JSON |
| P04-A18 | Suite 合同演进 | v0.4-model 已实现、all 仍 NOT_IMPLEMENTED，`contract_version` 已 bump 并记录 hash | registry/checker JSON |
| P04-A19 | Runner 可追溯 | validate、release/model checker 和所有实际加载 helper 的 SHA-256 已记录 | suite evidence |
| P04-A20 | Staged diff | staged/unstaged check、stat、name-status 均审查且未越界 | Git 命令输出 |

P04-A01 至 P04-A20 全部通过后才可标记 COMPLETE。

## 11. AWAITING 与 BLOCKED 规则

以下情况需要先完成安全诊断：

- D source 与发布 Shape 无法保持批准的派生关系。
- 实现要求修改 Phase 03 规则语义、severity、path、message 或 expected 状态。
- canonical valid 产生 Violation/Warning或目标为 0。
- 原始 invalid 未准确命中 R005、R008、R012。
- version IRI/wire namespace/conformsTo/record inheritance 与接受的 ADR 冲突。
- release manifest 存在路径逃逸、缺失 artifact、hash 漂移或无法解析的继承引用。
- release/requirements/validation-suites 跨记录语义校验失败，或 duplicate-ID negative control 未被拒绝。
- `contract_version` 未随组成变化 bump，或证据缺少 registry/runner/helper hash。
- v0.1–v0.3 baseline 回归。
- host/Docker model 结果不同。
- 必须创建 fixture 或弱化约束才能通过 model smoke。

发现某条 ADR 缺少规定的人类批准证据、或批准主体包含 AI 代批时，标记 `AWAITING_HUMAN_DECISION` 并说明应回到 Phase 03 补齐。根因确认属于 Phase 04 自身且存在可执行修复方案时同样标记 `AWAITING_HUMAN_DECISION`；诊断确认当前没有可批准的安全路径时标记 `BLOCKED`。两种情况都按 `human-intervention-policy.md` 把 manifest/model checker 的机器结果、最小差异和当前进度写入 `CHECKPOINT.md`，然后停止。

## 12. 交接

Phase 05 的进入包必须包含：

- `STATUS.md` 中 Phase 04 `COMPLETE` 小节。
- release manifest/schema 路径和 SHA-256。
- v0.4 artifact `SHA256SUMS` 和 D Shape byte-copy 证明。
- 更新后 requirements registry hash及语义不变证明。
- canonical valid、原始 invalid 和 conformsTo control 的 report graph 断言。
- record inheritance 清单。
- validation-suites `contract_version`/registry hash、manifest 语义负控和 runner/helper 源 hash 清单。
- Phase 03 test obligations；明确 Phase 05 将其实现为 `fixtures/v0.4/**` 和 `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`。
- `CHECKPOINT.md` 为空闲状态的确认。

Phase 05 必须读取 release manifest 和 requirements registry，不得在 validator 中重新硬编码 artifact 或 oracle。

## 13. Stop

完成 `STATUS.md` 中 Phase 04 小节、审查 staged/unstaged diff、通过 `v0.4-model`、baseline 和最终冻结校验后立即停止。不要创建正式 fixtures、`v0.4-test-cases.json`，不要使 `v0.4` 或 `all` 返回 0，不要开始 Phase 05。
