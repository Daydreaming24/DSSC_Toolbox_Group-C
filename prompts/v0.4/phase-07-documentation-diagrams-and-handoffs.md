# Phase 07 Prompt — 当前文档、图表与 A/B/D 组 Handoffs

只实施 Phase 07。开始前完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md` 和本文件；进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。

## 1. 目标

把 Phase 00–06 已经由机器证据证明的事实整理为当前、可学习、可演示、可由其他小组执行的 v0.4 文档包。更新两张关系图、四份 C 组核心报告、根/项目 README、A/B/D 三组 handoff 和 AI-assisted human-governed 说明，并用具名 checker 确保字段、路径、命令、状态和证据引用与 manifests 一致。本阶段还要更新并冻结已有 `C_Semantic_Treehouse/manifests/validation-suites.json` 的 `contract_version` 和 `all` suite 组成，使后续 wrapper、Docker 和 CI 消费同一份可审计合同；禁止在 `scripts/` 创建第二份 registry。

本阶段的文档必须清楚区分：冻结来源、历史 v0 结果、当前 v0.4 机器证据、待执行的 Phase 08/09 工作和可选外部证据。

## 2. 非目标

- 不改变模型、Shape、requirements、fixtures、test oracle、quality 算法或 governance policy。
- 不实施 CI、Docker clean-room、Treehouse 部署、外部 ITB/SEMIC 运行或 GitHub 发布。
- 不生成或编造截图、CI URL、外部 validator 结果、人工批准或发布状态。
- 不在文档中引入未进入 manifests 的新字段或概念范围。
- 不把历史 v0 Treehouse/validation evidence 当作当前运行证据。

## 3. 权威输入

1. 四个 manifests：
   - `C_Semantic_Treehouse/manifests/release-manifest.json`
   - `C_Semantic_Treehouse/manifests/baseline-test-cases.json`
   - `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
   - `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
2. `docs/v0.4/requirements-traceability.md` 和批准的 decision records
3. Phase 05 四状态结果
4. Phase 06 SPARQL、quality、governance 和 provenance 结果
5. `docs/v0.4/STATUS.md` 中 Phase 06 小节
6. 原始任务计划中 C 组输出和 A/B/C/D 集成边界
7. 当前治理、SSSOM、模型和 fixtures
8. `archive/` 和 `prompts/v0/`，仅作历史叙述参考
9. Phase 00–06 已建立的 `C_Semantic_Treehouse/manifests/validation-suites.json`、`C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json` 和 `scripts/validate.py` 当前行为；Phase 07 只把 documentation checks 加入已有 registry，验收后该 registry 成为 Phase 08 的只读输入

机器可读 manifests/results 优先于手写字段清单。文档发现不一致时先定位最早受影响 Phase，禁止选择对叙述更方便的一方。

## 4. 进入门槛

- Phase 00–06 均在 `docs/v0.4/STATUS.md` 中记录为 `COMPLETE`。
- Phase 06 小节存在且其验收矩阵全部通过。
- 四个 manifests 及 schemas 通过 schema、path、hash 和 freshness 验证。
- 使用当前 host 对应的显式 `.venv` 解释器或薄包装运行进入检查。Windows 使用 `.\.venv\Scripts\python.exe` 和 `validate.ps1 -Suite ...`；Linux 使用 `./.venv/bin/python` 和 `validate.sh --suite ...`。禁止调用可能回落到全局解释器的裸 `python`。`frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4` 和当前 `all` 均实际退出 0。
- Phase 06 governance 已明确 v0.4 breaking-change、namespace、record reuse 和 `dct:conformsTo`/Closed Shape 决策。
- `docs/v0.4/CHECKPOINT.md` 为空闲。
- 已审查 `git status --short --branch`、未暂存 diff 和 staged diff；可写文档不存在无法安全合并的用户改动，staged 内容的归属和允许路径均已确认。

任一门槛失败时，先完成安全诊断，把当前进度写入 `CHECKPOINT.md`。需要确认重叠修改归属或其他决定时标记 `AWAITING_HUMAN_DECISION`；确认没有安全路径时标记 `BLOCKED`，不通过手工叙述掩盖上游不一致。

## 5. 可写路径与保护路径

### 可写路径

- `README.md`
- `迁移清单.md`，仅依据 Phase 00–07 已通过证据更新状态、checkbox 和稳定证据路径；Phase 08–09 事项保持待执行
- `C_Semantic_Treehouse/README.md`
- `C_Semantic_Treehouse/scripts/README.md`
- `C_Semantic_Treehouse/C_semantic_model_design.md`
- `C_Semantic_Treehouse/C_semantic_treehouse_usage.md`
- `C_Semantic_Treehouse/C_model_versioning_demo.md`
- `C_Semantic_Treehouse/C_export_for_validation.md`
- `C_Semantic_Treehouse/diagrams/metadata-record-model.mmd`
- `C_Semantic_Treehouse/diagrams/semantic-governance-flow.mmd`
- `C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md`
- `C_Semantic_Treehouse/handoff/handoff-to-B-model-uri-provenance.md`
- `C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md`
- `C_Semantic_Treehouse/docs/ai-assisted-human-governed-semantic-modeling.md`
- `scripts/check_documentation.py`
- `C_Semantic_Treehouse/manifests/validation-suites.json`，仅限加入 Phase 07 documentation checks、更新 `all` composition 和按既定规则推进 `contract_version`
- `docs/v0.4/README.md`，仅更新为本目录的证据化导航和截至 Phase 07 的状态边界
- `build/phase-07/**`
- `build/validation/documentation/**`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`

### 本阶段额外保护路径

- Master 永久保护范围全部只读。
- `C_Semantic_Treehouse/model/v0.4/**`、`fixtures/v0.4/**`、`manifests/**`、`mappings/**`、`quality/**`、`governance/**` 只读；唯一例外是上方明确列出的 `manifests/validation-suites.json`。
- `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json` 只读；registry 更新后必须继续通过该 schema。
- Phase 05/06 的机器结果只读。
- `scripts/validate.py`、所有既有 suite 实现和 Phase 01–06 checker 只读；上游逻辑缺陷返回其所属 Phase。
- `docs/v0.4/current-state.md`、`scope-and-authority.md`、`risk-register.md`、`reproducibility-contract.md`、`baseline-reproduction.md`、`v0-errata.md`、`requirements-traceability.md`、`compatibility-matrix.md`、`result-classification.md`、`test-plan.md`、`model-derivation.md`、`compatibility-v0.3-v0.4.md` 和 `docs/v0.4/decisions/**` 只读。
- `docs/v0.4/STATUS.md` 中 Phase 00–06 的历史小节只读，只能追加新小节，不能改写。
- `.github/**`、Docker/跨平台入口和 release evidence 留给 Phase 08/09。

## 6. 任务

### 6.1 更新根 README、迁移清单与项目 README

根 README 至少包含：

- C 组定位、统一 Building Energy 场景和 v0.4 当前状态。
- v0、v0.1–v0.3、v0.4 和 Dataset ID 的命名边界。
- frozen inputs、current source、generated `build/`、reviewed release evidence 的区别。
- 环境前提和 Phase 01 已建立的 Windows/Linux/Docker 命令；只写实际存在并已验证的入口。
- `frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all` suite 说明。
- 四种业务状态和 `SUCCESS/ERROR` 程序状态说明。
- 首次安装/镜像下载的网络需求与核心运行的离线边界。
- 当前限制、可选证据和后续 Phase 08/09 状态。

`C_Semantic_Treehouse/README.md` 聚焦 package 内 artifacts、manifests、验证层、governance、handoffs 和证据导航，移除旧 `make.cmd` 等已归档入口的现行声明。

把 `C_Semantic_Treehouse/scripts/README.md` 从 v0 迁移占位说明更新为现行脚本索引，区分统一根 dispatcher、受控 checker entrypoints、历史参考脚本和仍待 Phase 08 验证的 Treehouse wrappers；不得再次把 package 脚本声明为第二个权威入口。

把 `docs/v0.4/README.md` 从目录骨架说明更新为当前导航，链接 requirements、decisions、`STATUS.md`、`CHECKPOINT.md`、兼容性、模型派生和复现合同；状态明确截止 Phase 07，Phase 08/09 保持待执行。

同步核对根 `迁移清单.md`。只勾选由 Phase 00–07 实际证据证明的事项，给出稳定的 `STATUS.md` 小节路径；Docker cross-platform、实际 CI、GitHub remote、tag/release 等 Phase 08–09 项继续保持未完成。清单顶部状态必须带证据截止 Phase，不能继续声称已经被 Git 状态或当前 artifacts 推翻的旧事实。

### 6.2 更新四份 C 组核心报告

#### `C_semantic_model_design.md`

覆盖 scope、DSSC 架构位置、两层模型、D 组契约、v0.4 字段/IRI/datatype/cardinality、JSON-LD、SHACL、record contract、标准复用、competency questions、约束策略、局限和 future work。

#### `C_semantic_treehouse_usage.md`

覆盖工具定位、v0 历史证据、当前尚未执行或实际已有的 v0.4 状态、独立 validation harness、Phase 08 可选部署路径、UI/API/import/export 证据门槛、风险与 fallback。没有当前证据的功能明确标记 `NOT RUN`。

#### `C_model_versioning_demo.md`

覆盖 v0.1–v0.4 演进、兼容性矩阵、v0.3 → v0.4 wire-profile breaking change、namespace/path/value 迁移、record reuse、deprecation 和 A/B/D 影响。v0.4 的编号属于本项目模型序列，不能用"minor"掩盖不兼容性。

#### `C_export_for_validation.md`

覆盖 D 原始 Shape 与 C 派生 artifact、hash、release/test manifests、fixtures、四状态、report graph 字段、统一命令、expected 结果、SEMIC/ITB/pySHACL 的职责边界和 D 组 handoff checklist。

四份报告中的 artifact 表必须可由自动检查与 release manifest 对照；禁止维护第二份无校验字段真源。

### 6.3 更新 Mermaid 图

至少更新：

1. `diagrams/metadata-record-model.mmd`：Provider、`dcat:Dataset` v0.4 metadata、v0.3 record、D Shape、四状态 harness、A offering、B provenance、D validation。
2. `diagrams/semantic-governance-flow.mmd`：D 冻结输入 → requirement/decision → release manifest → fixtures/test manifest → validation → semantic/domain review → handoff → release/monitor/deprecate；Treehouse 为可选旁支。

本阶段只对 Mermaid source 做确定性的结构 lint：检查文件非空、声明预期图类型、包含规定节点/边/标签、没有占位符和断裂的本地引用。该 lint 不调用 Mermaid parser，不证明 Mermaid 语法有效，也不证明图能够渲染。真实 renderer、渲染成功和视觉 QA 属于 Phase 08 的明确可选轨；本阶段不得把结构 lint 写成 syntax PASS 或 render PASS。

### 6.4 更新 A 组 handoff

`handoff-to-A-offering-metadata.md` 至少包含：

- v0.4 required/optional 字段表，IRI、JSON key、datatype、cardinality、allowed value。
- canonical JSON-LD 示例的 manifest 引用。
- endpoint HTTPS、format/frequency/unit、temporal order 和 extra property 行为。
- v0.3 → v0.4 migration table。
- 批准的 `dct:conformsTo`/Closed Shape 处理方式。
- A 组发布 offering 前可运行的精确命令和 expected status。

### 6.5 更新 D 组 handoff

`handoff-to-D-shacl-validation.md` 至少包含：

- D 组冻结 TTL 的路径/hash 和 C 组派生 Shape 的 artifact/hash。
- `v0.4-requirements.json`、`v0.4-test-cases.json` 和 fixture 路径。
- 单命令验证及程序退出语义。
- 四状态确定性优先级。
- focus node、path、source shape、constraint component、severity、message/value 的 report 解读。
- expected FAIL 与 harness ERROR 的区别。
- ITB test suite/test case/SUT/validation service 的映射建议。
- 外部 SEMIC/ITB 尚未执行时明确 `NOT RUN`。

### 6.6 更新 B 组 handoff

`handoff-to-B-model-uri-provenance.md` 至少包含 model/profile URI、版本与来源 hash、provenance entity/activity/agent、可引用字段、兼容性限制，以及"该信息不构成 Gaia-X 或法律合规证明"的适用边界。

### 6.7 更新 AI-assisted human-governed 文档与 demo 导航

记录 AI 可协助的审计、fixture/代码/文档生成；D 契约、semantic/domain review、自动 validator、发布授权等人工/机器 gate；保留 prompt、manifest、diff、报告和 provenance 审计轨。严禁声称 AI 自主批准语义或发布。

仅在本阶段已具名可写的根/package README 和 AI 治理文档中增加 demo 导航；`C_Semantic_Treehouse/docs/demo-script.md` 与 final checklist 保持只读，由 Phase 09 收口。

### 6.8 实施文档一致性验证

创建具名 checker `scripts/check_documentation.py`，至少验证：

- Markdown 相对链接存在且大小写一致。
- 文档引用的 artifact、manifest、suite、命令真实存在。
- 字段、状态、hash 和版本声明与 manifests 一致。
- ZIP 外无个人绝对路径、临时目录、旧解释器路径和过时现行命令。
- `NOT RUN`、`PARTIAL`、历史证据和当前证据不会被自动汇总为 DONE。
- Mermaid source 通过上述结构 lint；报告必须明确其不构成 syntax/render 验证。
- 发现 0 个文档或跳过 required check 时非零退出。

checker 必须提供不改动 tracked 文件的 negative controls，并在临时目录或 `build/phase-07/` 中证明以下输入分别非零：broken link、仓库外/个人绝对路径、未知 suite 或 artifact 引用、与 manifest 不一致的字段/hash/status、0 个发现文档、缺必需 Mermaid 节点/边、把 `NOT RUN` 错写为 DONE。negative control 若未执行或意外返回 0，本阶段阻塞。

### 6.9 冻结 suite registry

先以只读检查确认统一 dispatcher 已能从 `C_Semantic_Treehouse/manifests/validation-suites.json` 加载 suite 定义，并能在不修改 `scripts/validate.py` 的情况下把 registry 新登记的 required check 纳入 `all`。通用 registry/schema 加载或 dispatcher 能力缺失属于 Phase 01 入口合同缺陷；截至 Phase 06 的 `all` 聚合/执行缺陷属于 Phase 06。发现任一缺陷时按 `human-intervention-policy.md` 记录问题、说明应回到哪个更早 Phase，并停下来找人确认；取得确认后从对应 Phase 修复并重新验收。Phase 07 不修改 dispatcher。

确认前置能力后，更新已有 `C_Semantic_Treehouse/manifests/validation-suites.json`，按现有 schema 记录 `contract_version`、每个固定 suite 的稳定名称和实现状态，以及 `all` 的有序组成。只增加 Phase 07 documentation checks 并按既定版本规则推进 `contract_version`；不得创建新 registry、改变无关 suite 或重写历史定义。`all` 必须完整包含截至 Phase 07 的全部必需检查，包括文档 checker，并禁止重复、未知或可选外部轨进入 required composition。

`scripts/check_documentation.py` 同时使用 `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json` 校验 registry 的结构、`contract_version`、`all` composition 和当前实现的一致性。记录 registry SHA-256；Phase 08 将该文件作为只读输入，CI、reproduce wrappers 和 Docker 只调用已冻结的 `all`，不能在 Phase 08 静默改变组成或版本。

## 7. 产物

- 当前根 README、迁移清单、`docs/v0.4/README.md`、package README 与 package scripts README
- 四份更新后的 C 组核心报告
- 两个 Mermaid source
- A/B/D 三份可执行 handoff
- 更新后的 AI-assisted human-governed 文档
- `build/validation/documentation/results.json` 和 Markdown 报告
- 文档 checker negative-control 结果
- `scripts/check_documentation.py`、统一 dispatcher、报告器和全部实际加载 helper 的源文件 SHA-256 清单
- 更新后的 `C_Semantic_Treehouse/manifests/validation-suites.json`、`contract_version` 及 SHA-256 记录
- 两张图的 Mermaid 结构-lint 结果；本阶段不产出 render/syntax PASS
- `build/phase-07/**`
- `docs/v0.4/STATUS.md` 中的 Phase 07 小节

## 8. 必需命令

先运行 Git 工作区和 staged 状态审计：

```text
git status --short --branch
git diff --check
git diff --cached --check
git diff --stat
git diff --cached --stat
git diff --name-status
git diff --cached --name-status
```

在 Windows host 使用：

```powershell
.\.venv\Scripts\python.exe scripts\verify_frozen_files.py
.\.venv\Scripts\python.exe scripts\doctor.py --profile host
.\.venv\Scripts\python.exe scripts\check_documentation.py --self-test
.\scripts\validate.ps1 -Suite all
```

在 Linux host 使用：

```bash
./.venv/bin/python scripts/verify_frozen_files.py
./.venv/bin/python scripts/doctor.py --profile host
./.venv/bin/python scripts/check_documentation.py --self-test
./scripts/validate.sh --suite all
```

必须使用当前 host 对应的一组命令；若同时具备两类环境可两组都运行。还必须使用显式 `.venv` 解释器运行一次 `scripts/check_documentation.py` 正常检查和 deterministic rerun。最后重复全部 unstaged/staged diff 审计与冻结校验。`STATUS.md` 必须记录实际命令和退出码；不得写裸 `python`，不得把 PowerShell 参数写成 `--suite all`，不得把 Linux 参数写成 `-Suite all`，不得新增公开 suite 名称。

## 9. 验收矩阵

| 验收项 | 通过标准 | 证据 |
|---|---|---|
| README/迁移清单 | 环境、suite、四状态、网络和证据边界准确；清单状态截至 Phase 07 且 checkbox 有证据 | documentation results |
| 四份报告 | 必需章节完整，引用真实 v0.4 artifacts/results | content checks |
| 版本说明 | 明确 v0.3 → v0.4 wire-profile breaking change | versioning report check |
| Mermaid source | 两图仅通过结构 lint，必需关系完整；报告不声称 syntax/render PASS | diagram checks |
| A handoff | 字段、示例、迁移和命令与 manifest 一致 | handoff checks |
| D handoff | hash、四状态、report 断言、ITB mapping 完整 | handoff checks |
| B handoff | URI/provenance/适用边界完整 | handoff checks |
| AI 治理 | 人工与 validator gate 明确，无自主批准声明 | content check |
| 链接与路径 | 0 broken link，0 非允许绝对路径，0 过时入口 | documentation JSON |
| Checker negative controls | broken link/path/manifest/status/zero-discovery/Mermaid 结构错误均被拒绝 | self-test JSON |
| Checker 可追溯 | documentation checker、dispatcher、报告器和实际 helper 的源 SHA-256 进入证据 | documentation environment JSON |
| Suite registry | `contract_version` 固定，`all` composition 完整有序，schema/hash 已核验 | registry check/hash |
| Registry dispatcher | 新 documentation check 仅通过 registry 即进入 `all`，`scripts/validate.py` 无修改 | dispatcher/diff evidence |
| 真实性 | Treehouse/CI/外部 validator 未运行时明确 NOT RUN | status scan |
| 全量回归 | `--suite all` 退出 0，无 required skip | all report |
| 完整性/边界 | frozen 前后通过，unstaged/staged/untracked 逐项审计且仅在可写范围 | frozen/diff evidence |

## 10. AWAITING、BLOCKED 与 DEFERRED 规则

- Phase 07 的文档、handoff、Mermaid 结构 lint、checker negative controls 和 suite registry 都是必需项，不允许标记 `DEFERRED`。
- 缺少上游机器证据、文档与 manifest 冲突、broken links、未允许绝对路径、过时命令、虚假完成声明、必需章节缺失、negative control 未拒绝、suite registry 不完整、dispatcher 无法只靠 registry 加载 documentation check 或 `all` 非零时，按 `human-intervention-policy.md` 停止并完成至多一次只读复现；存在具名修复时标记 `AWAITING_HUMAN_DECISION`，确认没有安全路径时标记 `BLOCKED`。
- Mermaid 真实解析/渲染/视觉 QA、Semantic Treehouse 和外部 ITB/SEMIC 运行由 Phase 08 明确分类；它们当前保持 `NOT RUN`，不记作本阶段通过或延期。
- 发现 Phase 00–06 的模型、oracle、环境、quality、governance 或 checker 逻辑错误时，记录证据、说明需要回到哪个最早受影响 Phase，标记 `AWAITING_HUMAN_DECISION` 并停止；不得修改受保护文件或在报告中重解释错误。

## 11. 阶段交接

全部验收通过后：

1. 在 `docs/v0.4/STATUS.md` 追加 Phase 07 小节，记录进入门槛、修改、命令/退出码、验收矩阵、证据、真实的 NOT RUN 项、风险和 Phase 08 进入条件。
   风险处置引用 Phase 00 baseline snapshot risk ID；不回写该 snapshot，新增风险登记供 Phase 09 汇总。
2. 把 `docs/v0.4/CHECKPOINT.md` 清空回占位符状态。
3. 向 Phase 08 交付：验证通过的 quickstart、统一命令、图表 source、可选证据计划、当前环境限制、文档 checker/negative-control 结果，以及 `C_Semantic_Treehouse/manifests/validation-suites.json` 的 `contract_version` 和 SHA-256。
4. 报告 unstaged、staged、untracked Git 状态，不 commit、不 push。

## 12. Stop

Phase 07 标记 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。不得开始 CI、Docker clean-room、Treehouse、外部 validator 或 GitHub 发布。
