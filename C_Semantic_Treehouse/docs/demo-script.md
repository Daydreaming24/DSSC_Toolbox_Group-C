# v0.4 Demo Script

建议 25–40 分钟的真人演示路径。目标是展示**可独立复现的语义治理合同**，而不是可选外部服务。

## 0. 开场边界（1 分钟）

明确说明：

- 当前交付是 C 组共享语义模型 + 独立验证层 + 治理材料  
- 核心证据来自统一 suite registry 与锁定环境，不依赖 GPU/私有密钥  
- Semantic Treehouse publication、Mermaid render 与外部 ITB·SEMIC 是可选轨，保持 `NOT RUN` / `DEFERRED`；最近已确认候选的 GitHub 公开 push、三-job CI 与远程 clean clone 均为 `PASS`
- 维护者（GitHub 身份 `Daydreaming24`）已明确接受 P00-R14 的最终人工治理责任，风险终态为 `ACCEPTED_LIMITATION`；每个发生 tracked 内容变化的新候选均须独立完成 Phase 09 §6.9–§6.11，有效状态以 [`STATUS.md`](../../docs/v0.4/STATUS.md) 最新追加记录为准

## 1. 场景与版本（3 分钟）

1. 打开根 [`README.md`](../../README.md)：Dataset ID `building-energy-hourly-v1`  
2. 打开 [`C_semantic_model_design.md`](../C_semantic_model_design.md)：metadata 与 record 两层  
3. 打开 [`C_model_versioning_demo.md`](../C_model_versioning_demo.md)：v0.1–v0.4 与 `wire-profile-breaking`

## 2. 机器真源（5 分钟）

按顺序打开：

1. [`manifests/release-manifest.json`](../manifests/release-manifest.json)  
2. [`manifests/v0.4-requirements.json`](../manifests/v0.4-requirements.json)（D04-R001–R017）  
3. [`manifests/v0.4-test-cases.json`](../manifests/v0.4-test-cases.json)（66 cases）  
4. [`manifests/validation-suites.json`](../manifests/validation-suites.json)（`contract_version=1.6.0`，七个公开 suite）  
5. [`manifests/deliverables.json`](../manifests/deliverables.json)（最终 publication 文件清单）

强调：人读文档与 manifests 冲突时以 manifests + `STATUS.md` 为准。

## 3. 一键复现（8–12 分钟）

在仓库根执行（Windows 示例）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

期望：

- bootstrap 使用 hash lock 与仓库 `.venv`  
- doctor `--profile host` 通过  
- suite `all` 17/17 SUCCESS  

可选展示 Phase 09 最终 QA（不并入 reproduce）：

```powershell
.\.venv\Scripts\python.exe -I scripts\check_deliverables.py
.\.venv\Scripts\python.exe -I scripts\check_publication_safety.py
.\.venv\Scripts\python.exe -I scripts\check_evidence_freshness.py
```

## 4. 四状态与 oracle（5 分钟）

1. 打开 [`C_export_for_validation.md`](../C_export_for_validation.md)  
2. 展示一个 PASS fixture 与一个 FAIL fixture 路径（`fixtures/v0.4/`）  
3. 说明业务状态优先级：`UNTESTABLE` → `FAIL` → `INAPPLICABLE` → `PASS`  
4. 说明程序 `SUCCESS` 可与业务 `FAIL` 并存；`ERROR` 使 suite 非零退出  

## 5. 证据与风险诚实披露（4 分钟）

1. [`evidence/releases/v0.4/core-report.md`](../evidence/releases/v0.4/core-report.md)  
2. [`docs/v0.4/release-readiness.md`](../../docs/v0.4/release-readiness.md) — 风险终态  
3. [`docs/final-checklist.md`](final-checklist.md) — 已完成 vs 发布门槛  

必须口头声明：

- 最近已确认候选的 Windows/Linux local clean clone、GitHub 公开 push、实际 Actions Ubuntu/Windows/Docker 三个必需 job 与 canonical URL remote clean clone 已完成；最新绑定、run URL 和结论见 [`publication-record.md`](../../docs/v0.4/publication-record.md)
- v0.4 已公开托管，仓库当前无通用 license grant；该状态为已接受限制。D 组/来源 ZIP 再分发与历史路径公开风险已有维护者决定
- P00-R14 的 C/D final review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 责任已由维护者明确接受；早期 `PENDING` 状态继续如实展示
- tag、GitHub Release、branch protection 和 default-branch 更改为 `NOT_REQUESTED`

## 6. 下游交接（4 分钟）

1. A：[`handoff/handoff-to-A-offering-metadata.md`](../handoff/handoff-to-A-offering-metadata.md)  
2. B：[`handoff/handoff-to-B-model-uri-provenance.md`](../handoff/handoff-to-B-model-uri-provenance.md)  
3. D：[`handoff/handoff-to-D-shacl-validation.md`](../handoff/handoff-to-D-shacl-validation.md)  

## 7. 可选 Treehouse 旁路（仅在环境已暂停可展示时，0–5 分钟）

若维护者允许只读回顾证据（**不要**把 publication 说成已完成）：

- 当前投影：`current runtime=PAUSED`；`publication=NOT RUN`；`SHACL validator execution=PASS`  
- 用户指南：[`C_semantic_treehouse_user_guide.md`](../C_semantic_treehouse_user_guide.md)  
- 边界：核心 `all` 不依赖 Treehouse  

## 8. 收尾

分发指针：

- [`FINAL_SUMMARY.md`](../FINAL_SUMMARY.md)  
- [`docs/v0.4/STATUS.md`](../../docs/v0.4/STATUS.md)  
- [`docs/v0.4/human-decisions.md`](../../docs/v0.4/human-decisions.md)  
- [`docs/v0.4/publication-record.md`](../../docs/v0.4/publication-record.md)
