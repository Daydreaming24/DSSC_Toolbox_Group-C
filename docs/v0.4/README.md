# v0.4 证据与决策导航

本目录保存 v0.4 的范围、需求、决策、兼容性、派生、复现、发布就绪与阶段历史。

**证据截止（稳定）：** Phase 00–08 主线为 `COMPLETE`。维护者（GitHub 身份 `Daydreaming24`）已明确接受 P00-R14 的最终人工治理责任，该风险终态为 `ACCEPTED_LIMITATION`，当前无 `OPEN_BLOCKING` 风险。已确认候选具有 Phase 09 §6.9–§6.11 的完整核验记录；每个发生 tracked 内容变化的新候选均须独立完成同一技术链。有效状态以 [`STATUS.md`](STATUS.md) 的最新追加记录为准，动态绑定见 [`publication-record.md`](publication-record.md)。suite registry contract 为 `1.6.0`；Windows host 与固定 Docker container 的 suite `all` 均为 17/17。

v0.4 已公开托管于 [`Daydreaming24/DSSC_Toolbox_Group-C`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C)，当前无通用 license grant；该状态为已接受限制。tag、GitHub Release、branch protection 和 default-branch 更改均为 `NOT_REQUESTED`。

## 从哪里开始

| 问题 | 文档 |
|---|---|
| 已完成什么、实际跑过哪些命令？ | [`STATUS.md`](STATUS.md) |
| 当前是否存在未完成中断？ | [`CHECKPOINT.md`](CHECKPOINT.md) |
| 发布风险是否收口？阻塞项有哪些？ | [`release-readiness.md`](release-readiness.md) |
| 许可证/身份/仓库/写动作决定？ | [`human-decisions.md`](human-decisions.md) |
| push / CI / remote clone 记录？ | [`publication-record.md`](publication-record.md) |
| 本轮范围、权威顺序和团队边界是什么？ | [`scope-and-authority.md`](scope-and-authority.md) 与 [`current-state.md`](current-state.md) |
| D 组每条规则怎样进入模型和测试？ | [`requirements-traceability.md`](requirements-traceability.md) |
| 当前模型如何从冻结输入派生？ | [`model-derivation.md`](model-derivation.md) |
| v0.3 → v0.4 是否兼容？ | [`compatibility-v0.3-v0.4.md`](compatibility-v0.3-v0.4.md) 与 [`compatibility-matrix.md`](compatibility-matrix.md) |
| 四种业务状态与程序状态怎样判定？ | [`result-classification.md`](result-classification.md) |
| fixtures 与验证矩阵是什么？ | [`test-plan.md`](test-plan.md) |
| 如何建立固定环境和复现？ | [`reproducibility-contract.md`](reproducibility-contract.md)、[`baseline-reproduction.md`](baseline-reproduction.md) 与 [`../environment.md`](../environment.md) |
| 最终交付清单与检查表？ | [`../../C_Semantic_Treehouse/docs/final-checklist.md`](../../C_Semantic_Treehouse/docs/final-checklist.md)、[`../../C_Semantic_Treehouse/FINAL_SUMMARY.md`](../../C_Semantic_Treehouse/FINAL_SUMMARY.md)、[`../../C_Semantic_Treehouse/manifests/deliverables.json`](../../C_Semantic_Treehouse/manifests/deliverables.json) |
| 核心发布证据索引？ | [`../../C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json`](../../C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json) |
| 如何使用、暂停和重新启用 Semantic Treehouse？ | [`C_semantic_treehouse_user_guide.md`](../../C_Semantic_Treehouse/C_semantic_treehouse_user_guide.md) |
| v0 历史材料有哪些已知问题？ | [`v0-errata.md`](v0-errata.md) |
| 风险基线是什么？ | [`risk-register.md`](risk-register.md)（Phase 00 只读快照）；终态见 `release-readiness.md` |

## 已批准的决策

- [`ADR-001 — dct:conformsTo`](decisions/ADR-001-dct-conforms-to.md)：Closed Shape 与 profile 声明的处理。
- [`ADR-002 — wire profile and version identity`](decisions/ADR-002-wire-profile-and-version-identity.md)：v0.4 metadata 为 breaking wire-profile。
- [`ADR-003 — Energy Reading Record inheritance`](decisions/ADR-003-energy-record-inheritance.md)：record 合同继续复用 v0.3，`change=none`。

ADRs、requirements 和 manifests 共同约束叙述；机器可读字段、path、hash、expected status 与 suite composition 以 [`release-manifest.json`](../../C_Semantic_Treehouse/manifests/release-manifest.json)、[`v0.4-requirements.json`](../../C_Semantic_Treehouse/manifests/v0.4-requirements.json)、[`v0.4-test-cases.json`](../../C_Semantic_Treehouse/manifests/v0.4-test-cases.json) 和 [`validation-suites.json`](../../C_Semantic_Treehouse/manifests/validation-suites.json) 为准。

## 当前报告与 handoff

- [`C_semantic_model_design.md`](../../C_Semantic_Treehouse/C_semantic_model_design.md)
- [`C_model_versioning_demo.md`](../../C_Semantic_Treehouse/C_model_versioning_demo.md)
- [`C_export_for_validation.md`](../../C_Semantic_Treehouse/C_export_for_validation.md)
- [`C_semantic_treehouse_usage.md`](../../C_Semantic_Treehouse/C_semantic_treehouse_usage.md)
- [`C_semantic_treehouse_user_guide.md`](../../C_Semantic_Treehouse/C_semantic_treehouse_user_guide.md)
- [`handoff-to-A-offering-metadata.md`](../../C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md)
- [`handoff-to-B-model-uri-provenance.md`](../../C_Semantic_Treehouse/handoff/handoff-to-B-model-uri-provenance.md)
- [`handoff-to-D-shacl-validation.md`](../../C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md)
- [`ai-assisted-human-governed-semantic-modeling.md`](../../C_Semantic_Treehouse/docs/ai-assisted-human-governed-semantic-modeling.md)

## Phase 08 / 09 记录与发布入口

| 主题 | 入口 |
|---|---|
| Phase 08 跨平台 / CI 静态 / clean-room / Treehouse 可选轨 | [`STATUS.md`](STATUS.md) 的 Phase 08 小节与 recovery addenda |
| Phase 09 最终 QA、发布事实与当前等待项 | [`STATUS.md`](STATUS.md) 的 Phase 09 小节；外部事实 [`publication-record.md`](publication-record.md)；中断点 [`CHECKPOINT.md`](CHECKPOINT.md) |
| 风险终态（P00 原始 + Phase 01–08 新增） | [`release-readiness.md`](release-readiness.md) |
| 人工决定台账 | [`human-decisions.md`](human-decisions.md) |
| 发布动作与外部动态事实 | [`publication-record.md`](publication-record.md) |
| 最终 deliverables 清单 | [`../../C_Semantic_Treehouse/manifests/deliverables.json`](../../C_Semantic_Treehouse/manifests/deliverables.json) |
| 核心 suite 聚合证据 | [`../../C_Semantic_Treehouse/evidence/releases/v0.4/core-results.json`](../../C_Semantic_Treehouse/evidence/releases/v0.4/core-results.json) |

## 证据分层与状态纪律

- `inputs/`、`archive/` 与 v0.1–v0.3 是冻结来源和历史基线。
- `C_Semantic_Treehouse/model/v0.4/`、manifests、governance 与 mappings 是当前 tracked 源。
- 根 `build/` 保存可重建的 generated results、machine sidecars、negative controls 和诊断材料。
- [`evidence/releases/v0.4/`](../../C_Semantic_Treehouse/evidence/releases/v0.4/) 保存经过审核的 release evidence：baseline、model，以及 Phase 09 的 core aggregation / evidence-index。
- [`STATUS.md`](STATUS.md) 只追加已完成阶段；[`CHECKPOINT.md`](CHECKPOINT.md) 只保存当前未完成中断。

`NOT RUN`、`PENDING`、历史 PASS 和结构 lint 各自保持原语义。Mermaid Phase 07 结果只证明 source 结构；syntax、render 和视觉 QA 保持 `DEFERRED`/`NOT RUN`。Semantic Treehouse publication 与外部 ITB/SEMIC 维持既有可选轨状态。上一已确认候选的 Windows/Linux local clean clone、GitHub 公开 push、候选绑定三-job Actions 与 remote clean clone 已完成；维护者已明确接受 P00-R14 的最终责任，早期 `PENDING` 值继续保留为产物事实。当前状态以 `STATUS.md` 最新追加记录为准；tag、GitHub Release、branch protection 和 default-branch 更改保持 `NOT_REQUESTED`。
