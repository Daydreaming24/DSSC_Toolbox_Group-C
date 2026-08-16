# Phase 02 Prompt — v0.1–v0.3 锁定环境基线复现

你位于仓库根目录。完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md`、本文件和 `docs/v0.4/STATUS.md` 中 Phase 00–01 小节，只执行 Phase 02。进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后停止。

## 1. 目标

使用 Phase 01 的准确 CPython、hash lock、仓库 `.venv` 和固定 digest 容器，在当前仓库重新验证冻结的 v0.1–v0.3。建立机器可读的 baseline test-case manifest、fail-closed baseline runner、host/Docker 结果和规范化对比，形成 v0.4 开发前的正式无回归基线。

本阶段实现统一入口中的：

```text
.\scripts\validate.ps1 -Suite baseline
```

`frozen` 和 `environment` 必须继续通过；`traceability`、`v0.4-model`、`v0.4` 和 `all` 继续以 `NOT_IMPLEMENTED` 非零退出。

## 2. 非目标

- 不修改 v0.1–v0.3 模型、SPARQL query 或 expected result 来适配新工具。
- 不实现 D 组需求追踪、v0.4 模型、fixture 或四状态完整流程。
- 不把 archive 报告复制为当前证据。
- 不证明 Semantic Treehouse、在线 validator、CI 或 clean clone 已工作。
- 不创建 release manifest；该产物属于 Phase 04。

## 3. 权威输入

完整读取：

- `docs/v0.4/STATUS.md` 中 Phase 01 小节、环境合同和 lock 生成元数据
- `C_Semantic_Treehouse/model/v0.1/**`
- `C_Semantic_Treehouse/model/v0.2/**`
- `C_Semantic_Treehouse/model/v0.3/**`
- `C_Semantic_Treehouse/validation/expected-results.md`
- `C_Semantic_Treehouse/tests/sparql/competency-questions.md`
- `C_Semantic_Treehouse/tests/sparql/queries/**`
- `C_Semantic_Treehouse/tests/sparql/expected/**`
- `C_Semantic_Treehouse/scripts/**`，仅作重构和历史预期参考
- `archive/v0_validation_reports/**`，仅作差异对照
- `docs/v0.4/v0-errata.md`
- 当前 `requirements.lock`
- `C_Semantic_Treehouse/manifests/validation-suites.json` 及 schema

冻结 artifact 和既有 expected TSV 是 baseline oracle。历史报告提供背景信息，不是 oracle 的自动替代品。

## 4. 进入门槛

1. Phase 00 和 Phase 01 均在 `STATUS.md` 中记录为 `COMPLETE`。
2. Windows `.venv` 的 `environment` suite 返回 0。
3. Docker `environment` suite 返回 0。
4. 当前 lock SHA-256 与 `STATUS.md` 中 Phase 01 小节一致。
5. `.\scripts\validate.ps1 -Suite frozen` 返回 0。
6. `baseline` 当前为 `NOT_IMPLEMENTED`，或已有实现经过审查且不会覆盖用户修改。
7. `docs/v0.4/CHECKPOINT.md` 为空闲。
8. 可写路径不存在无法安全合并的既有修改。

任一必需环境轨失败时，先完成安全诊断。需要用户决定时标记 `AWAITING_HUMAN_DECISION`；确认没有安全选项时标记 `BLOCKED`。两种情况都先把当前进度写入 `CHECKPOINT.md`。不得在全局 Python 或另一套临时依赖中生成正式 baseline。

## 5. 可写路径

仅允许创建或修改：

- `C_Semantic_Treehouse/manifests/baseline-test-cases.json`
- `C_Semantic_Treehouse/manifests/schemas/baseline-test-cases.schema.json`
- `C_Semantic_Treehouse/manifests/validation-suites.json`，仅更新 `baseline` 与组合 `all` 的组成和实现状态，并 bump 顶层 `contract_version`
- `scripts/` 下由 Phase 01 受控 entrypoint catalog 发现的 baseline checker 模块和确定性报告生成器；不含通用 dispatcher、doctor 或包装脚本
- `C_Semantic_Treehouse/scripts/**`，仅在统一 runner 明确复用并消除旧 fail-open 风险时修改
- `C_Semantic_Treehouse/validation/README.md`
- `C_Semantic_Treehouse/validation/expected-results.md`，仅补充当前 baseline 执行合同，不改变冻结 oracle
- `C_Semantic_Treehouse/evidence/releases/v0.4/baseline/**`
- `docs/v0.4/baseline-reproduction.md`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`
- `build/phase-02/**`

## 6. 保护路径

除 Master 永久保护范围外，本 Phase 还保护：

- `prompts/**`
- `C_Semantic_Treehouse/manifests/release-manifest.json`
- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
- `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
- `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`
- 除 baseline schema 外的 `C_Semantic_Treehouse/manifests/schemas/**`
- `C_Semantic_Treehouse/model/v0.4/**`
- `C_Semantic_Treehouse/fixtures/v0.4/**`
- governance、mappings、handoff、quality、diagrams 和 `.github/**`
- `archive/v0_validation_reports/**`
- `scripts/validate.py`、`scripts/doctor.py`、`scripts/validate.ps1`、`scripts/validate.sh`、`Makefile`；发现通用 dispatcher 缺陷时按 `human-intervention-policy.md` 记录问题并停下来找人确认，不在本 Phase 直接修改

不得用格式化工具重写冻结 JSON-LD、TTL、YAML、queries 或 TSV。

## 7. 任务

### 7.1 建立 baseline manifest schema

创建 `C_Semantic_Treehouse/manifests/schemas/baseline-test-cases.schema.json`，使用明确 JSON Schema draft。schema 至少要求：

- manifest schema version。
- suite 固定为 `baseline`。
- 每个 case 的唯一 ID、release、validator/category。
- 输入、Shape/schema/query/expected 文件的仓库相对 POSIX 路径和 SHA-256。
- expected business status 和 expected program status。
- SHACL case 使用 JSON Schema `if`/`then` 或 `oneOf` 按 `expected_business_status` 约束 oracle：`PASS` 必须声明预期 target activation 数量大于 0 且 `sh:ValidationResult` 数量为 0，并禁止填写 sourceShape/path/component/severity/message 等结果专属字段；`FAIL` 必须声明 expected sourceShape、path、constraint component、severity、稳定 message 断言和精确结果数量或上下界。非 SHACL case 使用各自 validator 的条件分支，不携带 SHACL report 字段。
- 每个 SHACL case 的 data graph、shapes graph、可选 ontology graph，以及显式 `inference`（默认 `none`）、`advanced`、`abort_on_first`、`meta_shacl`（推荐 `true`）或等价 Shape graph 结构验证开关、Warning/Info 处理策略；配置不能依赖 pySHACL 默认值。
- JSON Schema/OpenAPI/SPARQL case 的明确 oracle。
- case enabled 状态；必需 case 不允许 silent skip。

schema 本身必须拒绝绝对路径、路径逃逸、未知状态和空 case 列表。JSON Schema 之外还必须实现跨记录语义校验器；它检查 duplicate case/artifact IDs、case 到 release/validator/artifact/oracle 的 cross-reference、同一路径 hash 冲突和必需 case 集合。不得声称 JSON Schema 单独完成这些跨记录约束。

### 7.2 建立 baseline test-case manifest

创建 `C_Semantic_Treehouse/manifests/baseline-test-cases.json`，列出全部基线检查。manifest 中不使用 glob；每个 artifact 有实际 hash。

至少覆盖：

1. RDF/Turtle：v0.1–v0.3 的全部 7 个 TTL 文件可解析。
2. JSON-LD：全部 context 和 example 文件可解析并通过本地 context 离线展开。
3. SHACL：
   - v0.1 valid metadata → PASS。
   - v0.2 valid metadata → PASS。
   - v0.2 invalid metadata → 业务 FAIL、程序 SUCCESS，并准确覆盖 `providerName` 缺失、`unit=MWh`、`temporalEnd` 缺失。
   - v0.3 metadata valid → PASS。
   - v0.3 Energy Reading Record valid → PASS。
4. JSON Schema：
   - v0.3 record valid → PASS。
   - v0.3 record invalid → 业务 FAIL、程序 SUCCESS，并检查 required、date-time、number、unit 四类预期错误；格式检查器必须启用。
5. OpenAPI：v0.3 fragment 必须由 `openapi-spec-validator` 完整验证。
6. SPARQL：8 个 query 分别与对应 expected TSV 精确比较。

manifest 的 expected 只能人工编辑，runner 不得根据实际结果自动回写。

### 7.3 实现 manifest-driven baseline runner

实现并登记受控 baseline checker entrypoint；通用 `scripts/validate.py` 只按已校验 registry 调度，不在本阶段修改：

- 首先验证 manifest schema、文件存在性和 hash。
- 发现 0 个 case 或任一必需 case disabled/skipped 时返回非零。
- 按 manifest 顺序稳定执行，报告顺序确定。
- 所有 JSON-LD context 从仓库本地加载；网络请求直接失败并给出明确诊断。
- 所有异常形成程序 `ERROR`，不能转换为预期业务 FAIL。
- 单个 case 的 expected/actual 分开记录。
- 退出码仅在全部 case 程序 SUCCESS 且 oracle 匹配时为 0。
- 证据记录 `scripts/validate.py`、baseline runner、报告生成器和本次实际加载全部 helper 的仓库相对路径与 SHA-256；helper 集合变化会使旧报告陈旧。

禁止在不同 validator 脚本中分别硬编码 `v0.3` 路径。

### 7.4 加固 SHACL 断言

对每个 SHACL case：

- 成功解析 data graph 和 shapes graph。
- data graph 只装载当前 case 数据；shapes、ontology、provenance、manifest 和其他 fixtures 分图传入，禁止合并造成额外类型或目标。
- 从 manifest 显式传递 inference、advanced、abort-on-first、meta-SHACL/Shape graph 结构验证、Warning/Info 策略；默认 `inference=none`、`abort_on_first=false`、`meta_shacl=true`。历史 case 若确需推理或关闭 Meta-SHACL，manifest 必须给出逐 case 理由和 ontology path/hash/等价结构检查。
- 记录 lock 中 pySHACL 的准确版本和每 case 的规范化 engine config；实际配置与 manifest 不一致时程序 ERROR。
- 明确计算预期 target，断言至少一个目标实际被评估。
- 解析 report graph 中的 `sh:ValidationResult`。
- 规范化 source shape、focus node、path、severity、constraint component 和 message。
- valid case 要求 0 个 Violation；若 baseline oracle 不允许 Warning，也要求 0 个 Warning。
- expected invalid 只有在预期路径和约束全部命中、没有未声明的关键差异时才程序 SUCCESS。

v0.2 匿名 PropertyShape 的 blank-node ID 不能作为跨运行稳定 oracle；使用稳定 path、constraint component、severity、message 和结果数量组合断言。

### 7.5 严格验证 JSON Schema、OpenAPI 和 SPARQL

- JSON Schema 使用相应 draft validator 和 `FormatChecker`。
- invalid record 的任意解析错误属于 ERROR；只有 schema errors 命中预期才是成功的负例。
- `openapi-spec-validator` 缺失、导入失败或完整验证异常均为 ERROR；浅层 YAML parse 不能替代。
- SPARQL 比较变量名、行数和值；0 行只在 expected 明确为 0 行时允许。
- RDF 查询结果排序和序列化采用确定性规则。

### 7.6 生成 host、Docker 和对比证据

分别在 Windows `.venv` 和固定容器运行 `baseline`。每次输出：

- 确定性 `result.json`。
- 机器环境 `environment.json`。
- 从 JSON 生成的 Markdown。

确定性结果记录 suite/schema、manifest hash、lock hash、artifact hashes、case counts、expected/actual 和断言。机器环境记录 commit/dirty、OS、architecture、Python、pip 和 validator 版本。

创建规范化比较，允许 OS/architecture 等环境字段不同；case 集合、oracle、artifact hash 和结果必须一致。

### 7.7 比较历史报告

读取 archive 报告并创建 `docs/v0.4/baseline-reproduction.md`：

- 列出历史预期和本次结果的一致项。
- 记录依赖升级带来的报告文本差异。
- 记录旧脚本存在但本次已经消除的 fail-open 风险。
- 明确 archive 不代表当前环境。

审核并清理规范化结果后，把选定的 baseline 证据复制或确定性再生到 `C_Semantic_Treehouse/evidence/releases/v0.4/baseline/`。保留 raw 环境日志在 `build/phase-02/`。

### 7.8 保持未实现 suite fail closed

完成 baseline 后，逐一确认：

- `traceability`
- `v0.4-model`
- `v0.4`
- `all`

均返回非零和 `NOT_IMPLEMENTED`。`all` 不能在 v0.4 尚未实现时仅运行已有 suite 后返回 0。

### 7.9 更新版本化 suite 注册表

只更新 `validation-suites.json` 中的 `baseline` 和受其影响的组合 `all`：

- `baseline` 状态改为 `IMPLEMENTED`，记录 manifest/schema/semantic-checker 组成。
- `all` 更新已纳入组成，仍保持 `NOT_IMPLEMENTED`。
- 每次状态或组成变化都 bump 顶层 `contract_version`，新的 `contract_version` 和 registry SHA-256 进入 host/Docker 证据；不得新增其他合同版本字段。
- 完整运行版本化 suite 注册表的跨记录语义校验；七个固定 suite、dependency 引用和无环条件继续成立。

在临时副本重跑 duplicate suite ID、悬空 dependency、dependency cycle、0 component、unknown entrypoint、重复 component 和 shell-command payload 负控，确保 registry 更新没有削弱 Phase 01 语义门槛。

## 8. 必需产物

- `C_Semantic_Treehouse/manifests/baseline-test-cases.json`
- `C_Semantic_Treehouse/manifests/schemas/baseline-test-cases.schema.json`
- manifest-driven baseline runner
- Windows host baseline JSON/Markdown
- Docker baseline JSON/Markdown
- 规范化跨环境比较结果
- 当前结果与历史报告的差异说明
- 经审核的 `evidence/releases/v0.4/baseline/` 证据
- 更新后的 validation-suites `contract_version`/registry hash 和语义校验证据
- `docs/v0.4/STATUS.md` 中的 Phase 02 小节

`STATUS.md` 的 Phase 02 小节必须记录 discovered/executed/passed/failed/skipped 数量、每个 category 的结果、baseline manifest hash、suite `contract_version`/registry hash、lock hash、runner/helper 源 hash、host/Docker 一致性和任何工具版本差异。

风险处置引用 Phase 00 baseline snapshot 的 risk ID；不回写该 snapshot，新增风险记录在本 Phase 小节并交给 Phase 09 汇总。

## 9. 必需命令

Windows：

```powershell
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
```

前三条必须返回 0；最后一条必须以 `NOT_IMPLEMENTED` 非零退出。

直接 Python 入口：

```text
.\.venv\Scripts\python.exe scripts\validate.py --suite baseline
```

Docker：

```text
docker compose -f docker-compose.validation.yml run --rm validation --suite frozen
docker compose -f docker-compose.validation.yml run --rm validation --suite environment
docker compose -f docker-compose.validation.yml run --rm validation --suite baseline
docker compose -f docker-compose.validation.yml run --rm validation --suite all
```

前三条必须返回 0；最后一条必须以 `NOT_IMPLEMENTED` 非零退出。

必要 negative controls 在不修改 tracked oracle 的临时副本/临时目录中运行，至少证明：

- 空 manifest 失败。
- duplicate case/artifact ID 失败。
- case 到 release/validator/artifact/oracle 的悬空 cross-reference 失败。
- 缺少必需 case 失败。
- artifact hash 不匹配失败。
- SHACL 空目标失败。
- OpenAPI validator 不可导入时失败。
- expected invalid 出现非预期错误时失败。
- SHACL engine config 使用未知值、遗漏必需字段或与 manifest 不符时失败。
- Shape graph 无效或被错误并入 data graph 时失败。
- `PASS` case 携带伪造 sourceShape/result 字段、target activation 为 0 或结果数量非 0 时 schema 失败。
- `FAIL` case 缺少 sourceShape/path/component/severity/message/count 任一必需 oracle 时 schema 失败。

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
| P02-A01 | Manifest schema | schema 有效并拒绝空 cases、绝对路径、未知状态 | schema 自测 |
| P02-A02 | Artifact 完整性 | manifest 所列文件存在且 hash 全匹配 | baseline JSON |
| P02-A03 | RDF/JSON-LD | 所有历史 Turtle 和 JSON-LD 在离线模式通过 | case results |
| P02-A04 | SHACL 正例 | 全部历史正例目标命中且按 oracle PASS | report assertions |
| P02-A05 | SHACL 负例 | v0.2 invalid 精确命中 providerName、unit、temporalEnd | report graph JSON |
| P02-A06 | JSON Schema | 正例通过；负例命中四类预期错误 | schema result JSON |
| P02-A07 | OpenAPI | 完整 validator 实际运行并通过 | tool version、result |
| P02-A08 | SPARQL | 8/8 query 与 expected TSV 精确一致 | query results |
| P02-A09 | 零测试保护 | discovered/executed 非零且 skipped=0 | aggregate JSON |
| P02-A10 | Host/Docker 一致 | 规范化 case IDs、hash、expected/actual 全一致 | comparison JSON |
| P02-A11 | Negative controls | 指定 fail-closed controls 均按预期非零 | control report |
| P02-A12 | 未实现 suite | traceability、v0.4-model、v0.4、all 非零 NOT_IMPLEMENTED | 命令输出 |
| P02-A13 | 证据卫生 | 发布证据无绝对路径、秘密、随机顺序和陈旧 hash | evidence audit |
| P02-A14 | 冻结完整性 | 开始和结束冻结校验返回 0 | 命令输出 |
| P02-A15 | 修改范围 | 无冻结模型/query/expected/archive 变化 | diff 审查 |
| P02-A16 | 跨记录语义 | duplicate IDs、悬空 cross-references 和同路径 hash 冲突均被拒绝 | semantic negative controls |
| P02-A17 | Suite 合同演进 | baseline 已实现；all 仍 NOT_IMPLEMENTED；`contract_version` 已 bump 并记录 hash | registry/checker JSON |
| P02-A18 | Runner 可追溯 | baseline runner、报告器和所有实际加载 helper 的 SHA-256 已记录 | suite evidence |
| P02-A19 | Staged diff | staged/unstaged check、stat、name-status 均审查且未越界 | Git 命令输出 |
| P02-A20 | pySHACL 配置 | 每 case 显式配置、分图隔离、版本固定；错误配置和无效 Shape 均失败 | manifest、engine JSON、negative controls |
| P02-A21 | 状态条件化 oracle | PASS 只声明 target 命中与 0 results；FAIL 完整声明结果 oracle；错配字段由 schema 拒绝 | schema branch tests |

P02-A01 至 P02-A21 全部通过后才可标记 COMPLETE。

## 11. AWAITING 与 BLOCKED 规则

以下情况需要先完成安全诊断：

- 任一冻结 artifact hash 改变。
- host 或 Docker baseline 无法完整运行。
- valid case 失败，或 invalid case 未精确命中 oracle。
- SHACL target 为 0、必需测试为 0、必需测试被 skip。
- pySHACL 版本/配置未记录、依赖默认漂移、graph 隔离失败，或错误配置/无效 Shape negative control 未失败。
- OpenAPI 完整 validator 缺失或降级。
- 8 个 SPARQL 结果不一致且无法在不修改冻结 oracle 的前提下解释。
- host/Docker 的规范化语义结果不同。
- baseline/validation-suites 跨记录语义校验失败，或 duplicate-ID negative control 未被拒绝。
- suite `contract_version` 未随组成变化 bump，或证据缺少 registry/runner/helper hash。
- 必须修改冻结模型或 expected 才能获得成功。

首次出现上述异常时，按 `human-intervention-policy.md` 停止写入，做一次只读复现确认是否稳定重现。存在需要用户判断的修复方案或 oracle 争议时标记 `AWAITING_HUMAN_DECISION`；确认当前没有可批准的安全路径时标记 `BLOCKED`。保存失败 JSON、环境信息和差异，把当前进度写入 `CHECKPOINT.md`，然后停止主线。

## 12. 交接

Phase 03 的进入包必须包含：

- `STATUS.md` 中 Phase 02 `COMPLETE` 小节。
- baseline manifest/schema 路径及 SHA-256。
- validation-suites `contract_version`/registry hash；baseline 为 IMPLEMENTED、all 为 NOT_IMPLEMENTED 的证明。
- host/Docker 一致的规范化 baseline 结果。
- runner/helper 源 hash 清单和 manifest 语义负控结果。
- 当前 validator 版本和 lock hash。
- 已知历史差异及其非阻塞解释。
- 证明 D 组输入和 v0.1–v0.3 仍完整的最终校验。
- `CHECKPOINT.md` 为空闲状态的确认。

Phase 03 应复用 manifest/schema/hash/report 基础设施来实现 `traceability` suite；不得修改 baseline oracle。

## 13. Stop

完成 `STATUS.md` 中 Phase 02 小节、审查 staged/unstaged diff、通过最终冻结校验后立即停止。不要读取 D 组 TTL 后开始分配规则，不要创建 `v0.4-requirements.json`，不要实现 Phase 03。
