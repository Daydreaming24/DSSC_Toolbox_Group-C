# C Group Semantic Governance Package

本目录承载 Building Energy Consumption Data Product 的共享语义模型、机器可读合同、独立验证层、治理材料和 A/B/D 组交接。当前 release manifest 将 `v0.4` 标为 current，并将 metadata 迁移分类为 `wire-profile-breaking`；Energy Reading Record 精确继承 v0.3。Phase 00–08 主线为 `COMPLETE`。维护者（GitHub 身份 `Daydreaming24`）已明确接受 P00-R14 的最终人工治理责任，风险终态为 `ACCEPTED_LIMITATION`，当前无 `OPEN_BLOCKING` 风险。已确认候选具有 Phase 09 §6.9–§6.11 的完整核验记录；每个发生 tracked 内容变化的新候选均须独立完成 Windows/Linux local clean clone、普通 push、候选绑定的 GitHub Actions Ubuntu/Windows/Docker 三个必需 job 与 canonical URL remote clean clone。有效状态以 [`docs/v0.4/STATUS.md`](../docs/v0.4/STATUS.md) 的最新追加记录为准，动态绑定见 [`publication-record.md`](../docs/v0.4/publication-record.md)。

v0.4 已公开托管于 [`Daydreaming24/DSSC_Toolbox_Group-C`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C)。仓库当前不授予通用 license，该状态为已接受限制；tag、GitHub Release、branch protection 和 default-branch 更改均为 `NOT_REQUESTED`。

## Package 地图

| 路径 | 内容 | 权威边界 |
|---|---|---|
| [`model/`](model/) | v0.1–v0.3 冻结模型与 v0.4 派生 metadata artifacts | 路径、角色、版本、来源和 SHA-256 以 release manifest 为准 |
| [`manifests/`](manifests/) | release、baseline cases、v0.4 requirements/test cases、suite registry 及 schemas | 机器可读合同真源 |
| [`fixtures/v0.4/`](fixtures/v0.4/) | PASS、FAIL、INAPPLICABLE、UNTESTABLE fixtures | case、格式、expected 和 hash 以 test-case manifest 为准 |
| [`tests/sparql/`](tests/sparql/) 与 [`sparql/`](sparql/) | 版本绑定的 semantic test manifest、queries 和 expected TSV | Phase 06 已执行 20/20 |
| [`quality/`](quality/) 与 [`mappings/`](mappings/) | 八类指标、breaking-change 评估和 47 行 SSSOM | SSSOM domain review 仍为 `PENDING` |
| [`governance/`](governance/) | model card、changelog、namespace/release/deprecation/review policy、provenance | 自动 gate 已通过；最终人工 review/approval 为 `PENDING` |
| [`handoff/`](handoff/) | A offering、B URI/provenance、D SHACL validation 交接 | Phase 07 当前文档合同 |
| [`diagrams/`](diagrams/) | metadata/record 关系与 semantic governance flow 的 Mermaid source | Phase 07 结构 lint 已通过；render/视觉 QA 为 `NOT RUN/PENDING` |
| [`scripts/`](scripts/) | 当前受控 Phase 06 checker helpers、v0 历史脚本和 Treehouse wrappers | 唯一公开 dispatcher 位于仓库根 `scripts/validate.py` |
| [`evidence/releases/v0.4/`](evidence/releases/v0.4/) | 已审核的 baseline/model/core release evidence | Phase 05–07 raw evidence 可重建于根 `build/`；core-results 为 Phase 09 稳定聚合 |
| [`FINAL_SUMMARY.md`](FINAL_SUMMARY.md) / [`docs/final-checklist.md`](docs/final-checklist.md) / [`docs/demo-script.md`](docs/demo-script.md) | 最终摘要、检查表与演示脚本 | Phase 09 §6.7 稳定文档 |

机器真源入口：

- [`release-manifest.json`](manifests/release-manifest.json)：v0.1–v0.4 releases、artifacts、hash、来源和 record inheritance。
- [`baseline-test-cases.json`](manifests/baseline-test-cases.json)：v0.1–v0.3 的 33-case oracle。
- [`v0.4-requirements.json`](manifests/v0.4-requirements.json)：D04-R001–D04-R017。
- [`v0.4-test-cases.json`](manifests/v0.4-test-cases.json)：66 个 fixtures 与四状态 expected/report assertions。
- [`validation-suites.json`](manifests/validation-suites.json)：七个公开 suite、受控 entrypoint 和 `all` 的有序组成。
- [`deliverables.json`](manifests/deliverables.json)：最终 GitHub candidate 的 tracked publication 文件清单。

## 当前模型与验证层

v0.4 metadata artifacts 位于 [`model/v0.4/`](model/v0.4/)，包括 ontology、JSON-LD context、D 组派生 Shape、canonical valid example 和 `SHA256SUMS`。D 组原始 TTL 保存在 [`inputs/d-group/v0.4/received/`](../inputs/d-group/v0.4/received/)；派生 Shape 与原始 TTL 的字节关系记录在 release manifest。v0.3 record schema、context、Shape 与正反例以 `change=none` 方式复用，避免复制生成虚假新版本。

独立 harness 通过根 dispatcher 运行，核心验证不依赖 Semantic Treehouse、在线 validator、GPU、数据库或私有密钥：

一键复现（仓库根）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

```bash
./scripts/reproduce.sh
```

分步 suite：

```powershell
.\scripts\validate.ps1 -Suite all
```

```bash
./scripts/validate.sh --suite all
```

七个公开 suite 是 `frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4` 和 `all`。Phase 07 documentation check 作为 `all` 内部 component 接入；package 内脚本不构成第二个公开 dispatcher。脚本分工见 [`scripts/README.md`](scripts/README.md) 与根 [`../scripts/README.md`](../scripts/README.md)。

## 证据导航

- 历史 baseline 已审核 evidence：[`evidence/releases/v0.4/baseline/README.md`](evidence/releases/v0.4/baseline/README.md)
- v0.4 model 已审核 evidence：[`evidence/releases/v0.4/model/README.md`](evidence/releases/v0.4/model/README.md)
- Phase 09 核心聚合：[`evidence/releases/v0.4/core-report.md`](evidence/releases/v0.4/core-report.md) 与 [`evidence-index.json`](evidence/releases/v0.4/evidence-index.json)
- 当前 Phase 05–09 生成结果：仓库根下 ignored `build/` 目录中的 validation 与 phase sinks（可重建 raw evidence；clean clone 后首次运行前可不存在）
- 完成历史、命令退出码与风险：[`docs/v0.4/STATUS.md`](../docs/v0.4/STATUS.md)、[`docs/v0.4/release-readiness.md`](../docs/v0.4/release-readiness.md)
- 公开 push、候选 CI 与远程 clean clone：[`docs/v0.4/publication-record.md`](../docs/v0.4/publication-record.md)
- 当前中断点：[`docs/v0.4/CHECKPOINT.md`](../docs/v0.4/CHECKPOINT.md)

## 报告、handoff 与演示路径

建议按 [`docs/demo-script.md`](docs/demo-script.md) 演示，或按以下顺序：

1. [`FINAL_SUMMARY.md`](FINAL_SUMMARY.md) 与 [`docs/final-checklist.md`](docs/final-checklist.md)
2. [`C_semantic_model_design.md`](C_semantic_model_design.md)：两层模型、D 组契约与字段/Shape 设计。
3. [`C_model_versioning_demo.md`](C_model_versioning_demo.md)：v0.1–v0.4 演进与 breaking-change 影响。
4. [`diagrams/metadata-record-model.mmd`](diagrams/metadata-record-model.mmd) 和 [`diagrams/semantic-governance-flow.mmd`](diagrams/semantic-governance-flow.mmd)：关系与治理流图源。
5. [`C_export_for_validation.md`](C_export_for_validation.md)：manifests、fixtures、四状态和 D 组验证导出。
6. [`handoff-to-A-offering-metadata.md`](handoff/handoff-to-A-offering-metadata.md)、[`handoff-to-B-model-uri-provenance.md`](handoff/handoff-to-B-model-uri-provenance.md)、[`handoff-to-D-shacl-validation.md`](handoff/handoff-to-D-shacl-validation.md)：下游执行合同。
7. [`C_semantic_treehouse_user_guide.md`](C_semantic_treehouse_user_guide.md)：Semantic Treehouse 登录、模型浏览、安全暂停、恢复与完整收尾。
8. [`C_semantic_treehouse_usage.md`](C_semantic_treehouse_usage.md) 与 [`ai-assisted-human-governed-semantic-modeling.md`](docs/ai-assisted-human-governed-semantic-modeling.md)：可选工具轨、证据门槛和人工治理边界。

2026-08-11 的 Semantic Treehouse 历史时点已固定 `v4.3.0` / commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf` 并完成 bounded checkout/materialization；canonical raw preflight 保持 `BLOCKED`，用户 finding-specific opt-in 已批准，零操作 `PrepareOnly` 边界已核验。当时 image build 的 controlled retry 因 Docker Hub short read/unexpected EOF 阻断，deployment 为 `NOT DEPLOYED`，workload/container、migration、UI/API/import/export/publication 均为 `NOT RUN`。

2026-08-12 的恢复 addendum 已完成受控部署、登录、canonical v0.4 六资产导入、ontology RDF-isomorphic round-trip 与 SHACL validator 正负控；application、validator 与 database 随后安全暂停，containers、networks 和两个数据卷均保留。Semantic Treehouse publication、Mermaid parser/render/视觉 QA 与外部 ITB/SEMIC 仍保持原有 `NOT RUN` / `DEFERRED` 状态。最近已确认候选的 GitHub 公开 push、实际 Actions 三个必需 job 与 remote clean clone 已完成；最新绑定见发布动作记录。历史 v0 Treehouse/validation 材料保留在 [`archive/`](../archive/) 中，用于追溯，不构成当前运行证据。
