# DSSC C 组语义治理可复现包（v0.4）

> 状态边界：Phase 00–08 主线为 `COMPLETE`。维护者（GitHub 身份 `Daydreaming24`）已明确接受 P00-R14 所列最终人工治理责任，该风险终态为 `ACCEPTED_LIMITATION`，当前无 `OPEN_BLOCKING` 风险。已确认候选的 Windows/Linux local clean clone、普通 push、GitHub Actions Ubuntu/Windows/Docker 三个必需 job 与 canonical URL remote clean clone 均有核验记录；每个发生 tracked 内容变化的新候选均须独立完成 Phase 09 §6.9–§6.11。有效状态以 [`docs/v0.4/STATUS.md`](docs/v0.4/STATUS.md) 的最新追加记录为准，动态绑定见 [`publication-record.md`](docs/v0.4/publication-record.md)。
>
> v0.4 已公开托管于 [`Daydreaming24/DSSC_Toolbox_Group-C`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C)。仓库当前不授予通用 license；该状态作为已接受限制记录，具体材料边界见 [`NOTICE`](NOTICE) 与 [`THIRD_PARTY_MATERIALS.md`](THIRD_PARTY_MATERIALS.md)。tag、GitHub Release、branch protection 和 default-branch 更改均为 `NOT_REQUESTED`。Semantic Treehouse 为隔离可选轨：受控部署/导入/SHACL 有本地证据，`current runtime=PAUSED`，`publication=NOT RUN`；raw upstream preflight 历史结论保持 `BLOCKED`。Mermaid render/视觉 QA 与外部 ITB/SEMIC 仍为 `DEFERRED`。

维护者：陈凌石（GitHub `Daydreaming24`）。本仓库的迁移、v0.4 模型派生、验证 harness、治理材料与发布工程由维护者完成；共享语义模型的组级归属保留在 [`provenance.jsonld`](C_Semantic_Treehouse/governance/provenance.jsonld)。

本仓库交付 DSSC Toolbox C 组的共享语义模型与治理合同。统一场景是 Building Energy Consumption Data Product：Dataset ID 为 `building-energy-hourly-v1`，当前 metadata profile 使用 `dcat:Dataset`、D 组 SHACL 契约和 JSON-LD；Energy Reading Record 继续复用 v0.3 合同。A 组消费 offering metadata，B 组消费 model/profile URI 与 provenance，D 组消费 Shape、fixtures、oracle 和验证报告。

## 版本与名称边界

| 名称 | 含义 |
|---|---|
| `v0` | 原仓库整体迁移基线、历史流程和归档证据 |
| `v0.1`–`v0.3` | 冻结的历史语义模型版本 |
| `v0.4` | 由 D 组冻结契约派生的当前模型版本；metadata 属于 `wire-profile-breaking` 迁移 |
| `building-energy-hourly-v1` | 场景内 Dataset ID；它独立于仓库和模型版本，保持原值 |

版本、artifact 路径、SHA-256、继承关系和适用 validator 的机器真源是 [`release-manifest.json`](C_Semantic_Treehouse/manifests/release-manifest.json)。命名政策见 [`docs/version-naming.md`](docs/version-naming.md)，v0.3 → v0.4 影响见 [`compatibility-v0.3-v0.4.md`](docs/v0.4/compatibility-v0.3-v0.4.md)。

## 环境与快速验证

固定环境采用 CPython 3.12.10、仓库本地 `.venv`、含 hash 的 locks 和同一个 [`scripts/validate.py`](scripts/validate.py) 编排核心。命令从仓库根目录运行。首次 bootstrap 会联网访问 PyPI；后续核心验证使用已经安装的依赖和仓库内输入，可离线执行。宿主 doctor 还会检查 Git、Docker client/server、Compose 和 daemon。

### 一键复现（推荐入口）

Windows AMD64 / PowerShell 5.1+：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

Linux：

```bash
./scripts/reproduce.sh
```

上述命令从脚本位置解析仓库根，运行对应 bootstrap（严格 hash lock）、仓库 `.venv` 上的 `doctor --profile host`，再通过 `validate` 运行 validation-suites 合同固定的 suite `all`。它们拒绝多余参数，不改 composition，不回落到全局 Python。

### 分步入口（调试）

```powershell
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe -I scripts\doctor.py --profile host
.\scripts\validate.ps1 -Suite all
```

```bash
./scripts/bootstrap.sh
./.venv/bin/python -I scripts/doctor.py --profile host
./scripts/validate.sh --suite all
```

### Phase 09 最终 QA（与一键复现分开）

```powershell
.\.venv\Scripts\python.exe -I scripts\check_deliverables.py
.\.venv\Scripts\python.exe -I scripts\check_publication_safety.py
.\.venv\Scripts\python.exe -I scripts\check_evidence_freshness.py
```

### Docker 固定 validation 轨

Phase 08/09 已在 Ubuntu 24.04.4 LTS / WSL2 / x86_64 与固定 `linux/amd64` container 上认证核心 `all`。镜像首次 pull/build 需要网络，运行时 Compose 强制 `network_mode: none`：

```powershell
$env:DSSC_SOURCE_COMMIT = (git rev-parse HEAD).Trim().ToLowerInvariant()
$env:DSSC_SOURCE_DIRTY = if (@(git status --porcelain).Count -gt 0) { 'true' } else { 'false' }
docker compose -f docker-compose.validation.yml build validation
docker compose -f docker-compose.validation.yml run --rm validation --suite all
```

最近已确认候选已普通 push 到公开仓库；该候选的 GitHub Actions Ubuntu/Windows/Docker 三个必需 job 全部成功，从 canonical GitHub URL 执行的 remote clean clone 也完成了一键复现和三个 Phase 09 checker。候选绑定、run URL、clone 结论和当前状态见 [`publication-record.md`](docs/v0.4/publication-record.md) 与 [`STATUS.md`](docs/v0.4/STATUS.md) 的最新追加记录。安装、代理、证书、锁和容器安全边界见 [`docs/environment.md`](docs/environment.md) 与 [`reproducibility-contract.md`](docs/v0.4/reproducibility-contract.md)。

## 七个公开 suite

公开 suite 名称固定为以下七个；[`validation-suites.json`](C_Semantic_Treehouse/manifests/validation-suites.json) 是版本、状态、依赖、component 顺序和 `all` 展开的唯一合同。Phase 07 的 documentation check 作为 `all` 的内部 required component 接入，不新增公开 suite。

| Suite | 作用 |
|---|---|
| `frozen` | 校验 frozen manifest 登记的 104 个受保护输入与历史文件字节 |
| `environment` | 校验固定解释器、`.venv`、locks、依赖、`pip check` 与 profile 能力 |
| `baseline` | 按 manifest 复现 v0.1–v0.3 的 33 个必需 case |
| `traceability` | 校验 D 组规则、requirements、ADRs、路径、hash 与双向覆盖 |
| `v0.4-model` | 校验 v0.4 release manifest、派生 artifact、JSON-LD、provenance 与继承合同 |
| `v0.4` | 执行 66 个 fixture、四状态分类、target activation 与 SHACL report oracle |
| `all` | 按 registry 确定性展开上述六个 suite，并运行 SPARQL、quality、governance 与 Phase 07 documentation checks |

未知 suite、空组成、重复 component、required skip、0 discovered/executed、manifest/hash 漂移或 checker 异常都会形成非零退出。

## 业务状态与程序状态

业务状态按 `UNTESTABLE` → `FAIL` → `INAPPLICABLE` → `PASS` 的优先级裁决：

| 状态 | 含义 |
|---|---|
| `UNTESTABLE` | authority、Shape、manifest 和依赖预检成功后，SUT 无法解析/离线加载，或命中 manifest 允许的 validator timeout、crash、服务故障 |
| `FAIL` | validator 成功形成 report graph，且至少出现一个 `sh:Violation`；同时出现 Warning 仍为 FAIL |
| `INAPPLICABLE` | validator 成功、无 Violation，并仅出现契约允许的不适用 Warning；当前映射是 Closed Shape 额外属性 |
| `PASS` | 输入和 Shape 成功解析，目标实际被评估，且没有 Violation 或 Warning |

程序状态独立记录：`SUCCESS` 表示 harness 完整执行且 actual 与 manifest expected 完全一致；`ERROR` 表示零测试、跳过、预期不匹配、authority/report 异常、依赖缺失或编排/证据写入故障。预期业务 `FAIL` 的 case 可以得到程序 `SUCCESS`；`ERROR` 会让 suite 非零退出。完整合同见 [`result-classification.md`](docs/v0.4/result-classification.md)。

## 来源、当前源与证据边界

| 区域 | 内容与用途 | 状态 |
|---|---|---|
| `inputs/`、`archive/`、`prompts/v0/`、`C_Semantic_Treehouse/model/v0.1/`–`C_Semantic_Treehouse/model/v0.3/` | frozen inputs 与 v0 历史基线 | 只读；历史 PASS 仅证明历史执行 |
| `C_Semantic_Treehouse/model/v0.4/`、`C_Semantic_Treehouse/manifests/`、`C_Semantic_Treehouse/governance/`、`C_Semantic_Treehouse/mappings/` | 当前受控源与机器合同 | tracked；由 manifests、schemas、hash 和 checker 约束 |
| `build/` | 每次运行生成的 raw result、machine sidecar、负控和诊断 | generated、Git ignored；可重建，不自动成为发布证据 |
| `C_Semantic_Treehouse/evidence/releases/v0.4/` | 已审核并复制入库的 release evidence | baseline、model，以及 Phase 09 core-results / core-report / evidence-index |
| `C_Semantic_Treehouse/manifests/deliverables.json` | 最终 GitHub candidate 的机器可读交付清单 | 由 `check_deliverables.py` 校验；不嵌入自身 hash |

冻结输入校验 104/104 只覆盖 frozen manifest 登记边界。D 组与来源 ZIP 再分发、ZIP 内历史路径公开风险、提交身份和公开仓库目标已有明确决定；上一已确认候选的公开 push、实际 CI 与 remote clean clone 已完成。v0.4 的公开托管不授予仓库代码和文档通用 license，该状态为已接受限制。维护者已明确接受 P00-R14 的最终人工治理责任；47 条 SSSOM 与早期治理产物保留真实 `PENDING` 状态。tag、GitHub Release、branch protection 和 default-branch 更改保持 `NOT_REQUESTED`。

## 文档、交接与演示导航

- Package 导航：[`C_Semantic_Treehouse/README.md`](C_Semantic_Treehouse/README.md)
- 最终摘要 / 检查表 / 演示脚本：[`FINAL_SUMMARY.md`](C_Semantic_Treehouse/FINAL_SUMMARY.md)、[`final-checklist.md`](C_Semantic_Treehouse/docs/final-checklist.md)、[`demo-script.md`](C_Semantic_Treehouse/docs/demo-script.md)
- 模型设计：[`C_semantic_model_design.md`](C_Semantic_Treehouse/C_semantic_model_design.md)
- 版本演进：[`C_model_versioning_demo.md`](C_Semantic_Treehouse/C_model_versioning_demo.md)
- 验证导出：[`C_export_for_validation.md`](C_Semantic_Treehouse/C_export_for_validation.md)
- Treehouse 边界：[`C_semantic_treehouse_usage.md`](C_Semantic_Treehouse/C_semantic_treehouse_usage.md)
- Treehouse 日常使用、安全暂停与恢复：[`C_semantic_treehouse_user_guide.md`](C_Semantic_Treehouse/C_semantic_treehouse_user_guide.md)
- A/B/D handoffs：[`handoff/`](C_Semantic_Treehouse/handoff/)
- AI-assisted human-governed：[`ai-assisted-human-governed-semantic-modeling.md`](C_Semantic_Treehouse/docs/ai-assisted-human-governed-semantic-modeling.md)
- v0.4 证据导航：[`docs/v0.4/README.md`](docs/v0.4/README.md)
- 发布就绪 / 人工决定 / 发布记录：[`release-readiness.md`](docs/v0.4/release-readiness.md)、[`human-decisions.md`](docs/v0.4/human-decisions.md)、[`publication-record.md`](docs/v0.4/publication-record.md)
- 核心发布证据：[`evidence/releases/v0.4/`](C_Semantic_Treehouse/evidence/releases/v0.4/)
- 迁移待办：[`迁移清单.md`](迁移清单.md)
- 环境与脚本：[`scripts/README.md`](scripts/README.md)

Mermaid source 已在 Phase 07 通过结构 lint；parser、renderer 和视觉 QA 保持 `DEFERRED/NOT RUN`。Semantic Treehouse 历史时点与恢复过程见 `STATUS.md` Phase 08；当前作用域投影为 `current runtime=PAUSED` 且 `publication=NOT RUN`。外部 ITB/SEMIC 保持 `DEFERRED/NOT RUN`。最近已确认候选的 GitHub 公开 push、Actions 三个必需 job 与 remote clean clone 已完成；当前状态以 `STATUS.md` 最新追加记录为准。tag、GitHub Release、branch protection 和 default-branch 更改保持 `NOT_REQUESTED`。这些可选轨不改变核心 `all` 的结论。
