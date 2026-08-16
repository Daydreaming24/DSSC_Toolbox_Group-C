# DSSC C 组 v0.4 分阶段执行 Prompts

本目录定义 DSSC Toolbox C 组从迁移基线推进到可复现 v0.4 发布包的完整执行流程。它继承 v0 的 Phase 0–9 结构，并针对 D 组最终 SHACL 契约、四状态结果、锁定环境、跨平台验证和 GitHub 发布重新设计。

> 设计状态：本目录中的 prompts 已完成流程设计；各 Phase 的工程任务尚未因此自动完成。执行状态必须由实际命令、机器可读结果和 `docs/v0.4/STATUS.md` 中的记录证明。
>
> 2026-08-08 更新：`master-prompt.md`、`human-intervention-policy.md` 已重写为精简版本，去掉了此前引入的 `closure-activation-v1`、`recovery-frontier-v1`、Phase 09 plan-lock/publication-lineage 等一整套自证式治理机制，只保留能真正防止“谎报完成/悄悄放宽标准”的最小规则。`emergency-recovery-prompt.md` 的内容已并入 `human-intervention-policy.md`，该文件现在只是一个重定向说明。Phase 00–09 已按同一套精简规则逐个文件同步完成，全部指向 `docs/v0.4/STATUS.md`/`CHECKPOINT.md`，不再有旧版 HIP/closure-activation 相关措辞；Phase 09 额外去掉了独立的 `release-attestation.yml` 发布 workflow，改为复用 Phase 08 的 `validate.yml` 加真实 GitHub 远程 clone 验证。

## 使用方法

1. 在开始任何 Phase 前完整读取 [`master-prompt.md`](master-prompt.md) 和 [`human-intervention-policy.md`](human-intervention-policy.md)。
2. 先检查 `docs/v0.4/CHECKPOINT.md`：非空闲说明有一个 Phase 中途停下了，必须先按其记录恢复并做完，不能跳过去执行别的 Phase。
3. 按 Phase 00 → Phase 09 顺序执行，一次只执行一个 Phase。每个 Phase 先检查进入门槛，再声明计划和可写范围，然后实施、验证、审查 diff、在 `STATUS.md` 追加阶段记录。
4. 必需门槛未通过时标记 `BLOCKED` 并停止；需要人工选择、纠正或授权时标记 `AWAITING_HUMAN_DECISION` 并停止。两种情况都要先把当前进度写入 `CHECKPOINT.md`。`DEFERRED` 只适用于 prompt 明确标出的非阻塞证据轨（例如 Phase 08 的 Semantic Treehouse）。
5. Phase 内容较多、一次会话跑不完，或者上下文丢失、验证回归、工作树状态不明时，按 [`human-intervention-policy.md`](human-intervention-policy.md) 第 3 节处理，把中断点记入 `CHECKPOINT.md`。
6. prompts 负责过程治理；release manifest、test-case manifest、自动测试和发布证据负责可执行验收。

不要一次性执行全部 Phase。不要把"prompt 已编写"或"文件已存在"当作阶段完成证据。

## 文件与阶段

| 顺序 | Prompt | 核心产出 | 依赖 |
|---|---|---|---|
| 总控 | [`master-prompt.md`](master-prompt.md) | 权威顺序、冻结边界、四状态、STATUS/CHECKPOINT 合同、证据与完成规则 | 无 |
| 人工介入与恢复 | [`human-intervention-policy.md`](human-intervention-policy.md) | 何时停下来找人确认、证据要求、状态不明/失败时的恢复步骤（含原 emergency-recovery 内容） | Master 同级全局约束 |
| 00 | [`phase-00-state-reconciliation-and-scope-freeze.md`](phase-00-state-reconciliation-and-scope-freeze.md) | 当前状态复核、范围冻结、创建 `STATUS.md`/`CHECKPOINT.md` | Master |
| 01 | [`phase-01-reproducible-environment-and-entrypoints.md`](phase-01-reproducible-environment-and-entrypoints.md) | Python 3.12、依赖锁、`.venv`、统一入口、suite 注册表、基础容器 | Phase 00 |
| 02 | [`phase-02-v0-baseline-reproduction.md`](phase-02-v0-baseline-reproduction.md) | v0.1–v0.3 正式无回归基线 | Phase 01 |
| 03 | [`phase-03-d-group-contract-traceability.md`](phase-03-d-group-contract-traceability.md) | D 组规则编号、需求追踪、兼容性决策 | Phase 02 |
| 04 | [`phase-04-v0-4-model-and-release-manifest.md`](phase-04-v0-4-model-and-release-manifest.md) | v0.4 派生模型、统一 release manifest | Phase 03 |
| 05 | [`phase-05-four-state-fixtures-and-validation-harness.md`](phase-05-four-state-fixtures-and-validation-harness.md) | 四状态 fixtures、test-case manifest、fail-closed 验证器 | Phase 04 |
| 06 | [`phase-06-semantic-tests-quality-and-governance.md`](phase-06-semantic-tests-quality-and-governance.md) | SPARQL、质量、SSSOM、governance、provenance | Phase 05 |
| 07 | [`phase-07-documentation-diagrams-and-handoffs.md`](phase-07-documentation-diagrams-and-handoffs.md) | 当前文档、图表、A/B/D 组交接 | Phase 06 |
| 08 | [`phase-08-cross-platform-ci-and-optional-treehouse-evidence.md`](phase-08-cross-platform-ci-and-optional-treehouse-evidence.md) | Windows/Linux/Docker CI、clean-room、可选 Treehouse 证据 | Phase 07 |
| 09 | [`phase-09-final-qa-clean-clone-and-release-readiness.md`](phase-09-final-qa-clean-clone-and-release-readiness.md) | 最终 QA、交付清单、clean clone、GitHub Actions 结果、release readiness | Phase 08 |

`emergency-recovery-prompt.md` 仍保留在目录中，但内容已合并进 `human-intervention-policy.md`，只作为重定向说明，避免旧引用出现死链。

## 阶段状态

- `NOT_STARTED`：尚未执行。
- `IN_PROGRESS`：已通过进入门槛，正在实施。
- `AWAITING_HUMAN_DECISION`：需要人工选择、纠正或授权；阻止当前及后续 Phase 继续。
- `BLOCKED`：必需前置条件或验收项无法满足，没有可执行的安全选项，已记录证据并停止。
- `COMPLETE`：全部必需验收项通过，证据齐全，`STATUS.md` 对应小节已追加。
- `DEFERRED`：仅用于 Phase 08 明确标出的非阻塞证据轨，例如可选 Semantic Treehouse 证据。

已完成 Phase 的记录追加保存在 `docs/v0.4/STATUS.md`（只读历史，追加写入）；当前尚未完成的中断点保存在 `docs/v0.4/CHECKPOINT.md`（空闲时是占位符，随时可被覆盖）。这两个文件由 Phase 00 创建，此后按 `master-prompt.md` 第 10、11 节的规则更新，不再各自维护 phase-summaries 目录或并行的机器可读状态副本。

Phase 09 的最终发布验证需要真实可核查的证据（GitHub Actions run 结果、clean-room clone 结果），在外部证据齐全前保持 `IN_PROGRESS`；不需要额外的 payload/completion 双 commit 或发布沿革归档系统。

## 人工介入与状态恢复

完整规则见 [`human-intervention-policy.md`](human-intervention-policy.md)，这里只列要点：

- 第一次出现非预期失败时，只做一次不改变 tracked 文件的受控复现，然后把根因、证据和可选方案写入 `CHECKPOINT.md` 并停下来找人确认；不要反复重试或自行"修到能过"。
- 装软件、联网、破坏性 Git 操作、发布类动作（commit/push/tag/remote/release）都必须先取得人工确认。
- 任何 "已完成" 声明都必须附真实命令、退出码和结果文件/hash 作为证据；不能用空跑、stub 或"看起来没问题"替代。
- 状态不明、验证从通过变为失败、工作树被意外修改、CI 与本机结果不一致时，按 `human-intervention-policy.md` 第 3 节的诊断步骤处理，不自行猜测或静默修改 oracle/Shape/fixture 来消除失败。

## 固定执行合同

- 公开 suite 仅有 `frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all`。
- `C_Semantic_Treehouse/manifests/validation-suites.json` 版本化记录 suite 的实现状态和组成；Phase 07 冻结最终 `all`，Phase 08–09 只读消费。
- Windows 最终一键复现命令为 `.\scripts\reproduce.ps1`，Linux 为 `./scripts/reproduce.sh`。两者必须建立/校验 `.venv`、消费 lock、运行 doctor 和 `all`。
- 每份 manifest 同时接受 JSON Schema 和跨记录语义校验；重复 ID、断链引用和 hash 篡改必须由 negative control 证明会失败。
- Phase 09 不新建独立发布 workflow：候选 commit push 后复用 Phase 08 的 `validate.yml`，用 `gh run view` 或 Actions 页面确认三个 job 对精确候选 SHA 全部成功，再做一次真正的远程 `git clone` 验证；这些事实随后写进候选之后的一次记录性提交，不构成自引用。

## 统一完成原则

- 每个必需检查均有明确命令、预期退出码、预期结果和证据路径。
- 发现 0 个测试、跳过必需测试、缺少依赖、解析异常或 validator 运行异常都不能形成 PASS。
- 预期为 FAIL 的 fixture 只有在预期 rule、path、severity 和结果断言命中时才算测试成功。
- 业务结果与程序运行状态分开记录：业务结果为 `PASS`、`FAIL`、`INAPPLICABLE`、`UNTESTABLE`；程序状态为 `SUCCESS` 或 `ERROR`。
- 冻结输入和历史版本始终先校验哈希，再开展派生工作。
- 未经用户明确授权，不创建远程仓库、不推送、不打 tag、不改写提交历史。
