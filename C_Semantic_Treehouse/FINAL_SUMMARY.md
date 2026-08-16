# v0.4 Final Summary

DSSC Toolbox C 组语义治理可复现包的交付摘要。  
权威阶段历史：[`docs/v0.4/STATUS.md`](../docs/v0.4/STATUS.md)。  
最终检查表：[`docs/final-checklist.md`](docs/final-checklist.md)。

## 1. 交付了什么

| 类别 | 内容 |
|---|---|
| 场景 | Building Energy Consumption Data Product；Dataset ID `building-energy-hourly-v1` |
| 当前模型 | v0.4 metadata（`dcat:Dataset` + D 组 SHACL）；Energy Reading Record 精确继承 v0.3 |
| 兼容性 | v0.3 → v0.4 metadata 为 `wire-profile-breaking`；record 合同 `change=none` |
| 机器合同 | release / baseline / requirements / test-cases / validation-suites / deliverables manifests |
| 验证层 | 七个公开 suite；统一 `scripts/validate.py`；host + 固定 Linux container |
| 证据 | `evidence/releases/v0.4/` 含 baseline、model 与 Phase 09 core aggregation |
| 交接 | A offering / B provenance / D SHACL handoffs；AI-assisted human-governed 说明 |

## 2. 已证明的核心结果

- Phase 00–08 主线：`COMPLETE`（可选轨可 `DEFERRED`）
- validation-suites：`contract_version=1.6.0`；manifest SHA-256
  `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`
- suite `all`：discovered/executed/passed/failed/skipped = **17/17/17/0/0**
- Phase 09 本地最终 QA（§6.1–§6.6）：deliverables、publication-safety、evidence-freshness 与无自引用 core evidence
- v0.4 已公开托管；最近已确认候选已完成 Phase 09 §6.9–§6.11，其普通 push、GitHub Actions Ubuntu/Windows/Docker 三个必需 job、Windows/Linux local clean clone 与 canonical GitHub URL remote clean clone 均已成功。候选 SHA、run URL/结论与 clone 绑定见 [`publication-record.md`](../docs/v0.4/publication-record.md)。
- 维护者（GitHub 身份 `Daydreaming24`）已明确接受 P00-R14 的最终人工治理责任，该风险终态为 `ACCEPTED_LIMITATION`，当前无 `OPEN_BLOCKING` 风险。每个发生 tracked 内容变化的新候选均须独立完成 Phase 09 §6.9–§6.11；有效状态以 [`STATUS.md`](../docs/v0.4/STATUS.md) 的最新追加记录为准。
- 一键复现入口（只读复核）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

```bash
./scripts/reproduce.sh
```

## 3. 发布与许可边界

当前已确认的公开仓库为 [`Daydreaming24/DSSC_Toolbox_Group-C`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C)。以下事项保持原状态：

1. 仓库当前不授予通用 license；v0.4 公开托管且无通用 license grant 为已接受限制。D 组与来源 ZIP 再分发、ZIP 内历史路径公开风险已有维护者决定。
2. 维护者已明确接受 C/D final review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 责任（P00-R14）；早期产物的 `PENDING` 状态继续保留，后续逐项签字由维护者负责。
3. tag、GitHub Release、branch protection 和 default-branch 更改均为 `NOT_REQUESTED`。
4. Mermaid 渲染/视觉 QA 与外部 ITB/SEMIC 保持 `DEFERRED` / `NOT RUN`。
5. Semantic Treehouse **publication** 保持 `NOT RUN`；runtime 为 `PAUSED`。

## 4. 可选轨摘要

Semantic Treehouse 为隔离可选证据轨：本地受控部署、canonical v0.4 导入、ontology round-trip 与 SHACL 正负控有证据；服务安全暂停并保留数据卷；raw upstream preflight 历史结论保持 `BLOCKED`。  
Mermaid render 与 ITB/SEMIC 为 `DEFERRED`。上述轨不改变核心 `all` 结论。

## 5. 消费者如何开始

1. 阅读根 [`README.md`](../README.md) 与 [`docs/v0.4/README.md`](../docs/v0.4/README.md)  
2. 运行一键复现命令（首次 bootstrap 需 PyPI 网络）  
3. 需要发布前审计时运行 Phase 09 三个 checker（见 [`scripts/README.md`](../scripts/README.md)）  
4. 下游组阅读 `handoff/` 与本目录核心报告  

## 6. 发布就绪指针

- 风险收口：[`docs/v0.4/release-readiness.md`](../docs/v0.4/release-readiness.md)  
- 人工决定：[`docs/v0.4/human-decisions.md`](../docs/v0.4/human-decisions.md)  
- 发布动作记录：[`docs/v0.4/publication-record.md`](../docs/v0.4/publication-record.md)  
- 阶段状态：[`docs/v0.4/STATUS.md`](../docs/v0.4/STATUS.md)
- 核心证据：[`evidence/releases/v0.4/core-report.md`](evidence/releases/v0.4/core-report.md)
