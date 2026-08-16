# v0.4 Final Checklist

人读最终检查表。机器可读真源始终是 [`docs/v0.4/STATUS.md`](../../docs/v0.4/STATUS.md)
与 [`manifests/deliverables.json`](../manifests/deliverables.json)。

日期边界：2026-08-14（Phase 09 发布事实同步）。本表通过 [`STATUS.md`](../../docs/v0.4/STATUS.md) 与 [`publication-record.md`](../../docs/v0.4/publication-record.md) 引用候选 SHA、CI run ID/URL 和远程 clone 结果，不复制这些动态值。

## 1. 核心模型与验证（已完成）

- [x] frozen manifest 104/104
- [x] 环境合同：CPython 3.12.10、hash locks、repo `.venv`、doctor
- [x] v0.1–v0.3 baseline 33/33
- [x] D 组 requirements D04-R001–R017 与 ADR-001/002/003
- [x] v0.4 派生模型与 release manifest
- [x] 66-case 四状态 harness（PASS 6 / FAIL 53 / INAPPLICABLE 1 / UNTESTABLE 6）
- [x] SPARQL 20/20、quality、governance
- [x] documentation gate 纳入 `all`
- [x] validation-suites `contract_version=1.6.0`（SHA-256 `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`）
- [x] Windows host suite `all` 17/17
- [x] 固定 Linux validation container / Docker suite `all` 17/17
- [x] Phase 08 WSL2 Linux host、clean-room rehearsal、CI 静态合同

稳定证据：[`../evidence/releases/v0.4/core-report.md`](../evidence/releases/v0.4/core-report.md)、
[`../evidence/releases/v0.4/evidence-index.json`](../evidence/releases/v0.4/evidence-index.json)。

## 2. Phase 09 本地最终 QA（最近已确认候选已完成 §6.1–§6.6）

- [x] deliverables schema + manifest + `check_deliverables.py`
- [x] `check_publication_safety.py`
- [x] `check_evidence_freshness.py`
- [x] 一键复现入口只读复核（`scripts/reproduce.ps1` / `scripts/reproduce.sh` 未改）
- [x] 无自引用 core-results / core-report / evidence-index
- [x] §6.7 稳定最终文档（本表、FINAL_SUMMARY、demo、release-readiness、human-decisions、publication-record、导航）

## 3. 发布门槛

### 3.1 §6.8 内容、身份与仓库决定

- [x] D 组与来源 ZIP 再分发授权（§6.8）
- [x] ZIP 内历史绝对路径公开风险接受（§6.8）
- [x] Commit 作者身份与 GitHub 登录身份（`Daydreaming24` / `daydreaming <188458589+Daydreaming24@users.noreply.github.com>`；`DEC-P09-COMMIT-IDENTITY-NOREPLY`）
- [x] v0.4 公开托管且无通用 license grant 作为已接受限制（无根 `LICENSE`；MIT 草稿已撤回）
- [x] 公开 GitHub 仓库已绑定；最近已确认候选完成普通 push：[`Daydreaming24/DSSC_Toolbox_Group-C`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C)

### 3.2 最近已确认候选的 §6.9–§6.11 发布链事实

- [x] 最近已确认候选完成 candidate commit 与 Windows/Linux local clean clone（§6.9）
- [x] 最近已确认候选配置精确 remote 并普通 push（§6.10；无 force）
- [x] 该 push 触发的 GitHub Actions Ubuntu/Windows/Docker 三个必需 job 全部成功，`head_sha` 等于最近已确认候选
- [x] 最近已确认候选从 canonical GitHub URL 完成 remote clean clone、一键复现与三个 Phase 09 checker
- [x] §6.11 记录性提交将最近已确认候选的 SHA、run URL/结论与 clone 结果写入 [`STATUS.md`](../../docs/v0.4/STATUS.md) / [`publication-record.md`](../../docs/v0.4/publication-record.md)

### 3.3 最终人工治理责任

- [x] 维护者（GitHub 身份 `Daydreaming24`）明确接受 C/D final review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 的最终责任（P00-R14；`DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED`）

P00-R14 终态为 `ACCEPTED_LIMITATION`，当前无 `OPEN_BLOCKING` 风险。每个发生 tracked 内容变化的新候选均须独立完成 Phase 09 §6.9–§6.11；有效状态以 [`STATUS.md`](../../docs/v0.4/STATUS.md) 的最新追加记录为准。tag、GitHub Release、branch protection 和 default-branch 更改均为 `NOT_REQUESTED`。

## 4. 可选轨真实状态

| 轨 | 状态 | 说明 |
|---|---|---|
| Semantic Treehouse | 隔离可选；本地受控部署/导入/SHACL 有证据；`current runtime=PAUSED`；`publication=NOT RUN` | 不进入核心 `all`；raw preflight 历史 `BLOCKED` |
| Mermaid parser/render/视觉 QA | `DEFERRED` | 仅 Phase 07 structural lint |
| 外部 ITB/SEMIC | `DEFERRED` / `NOT RUN` | 无外传授权 |

Treehouse 当前投影：

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`。

## 5. 已知限制（ACCEPTED_LIMITATION）

1. **Frozen 边界（P00-R15）**：104/104 只覆盖 frozen manifest 登记文件，不等于全部永久保护路径均 hash-bound。  
2. **可选外部轨（P00-R12 / P08-R01）**：Mermaid render、ITB/SEMIC 与 Treehouse 运维/运输限制不影响核心 `all` 结论。  
3. **无通用 License**：根目录无 `LICENSE`；项目代码 SPDX `NOASSERTION`。v0.4 公开托管且无通用 license grant 为已接受限制。
4. **第三方再分发已批、SPDX 仍可为 NOASSERTION**：D 组 / ZIP 见 `THIRD_PARTY_MATERIALS.md`。  
5. **最近候选发布链已验证**：最近已确认候选的 Windows/Linux local clean clone、普通 push、三-job CI 与 canonical URL remote clean clone 均已完成，动态绑定见 `publication-record.md`。
6. **人工治理责任（P00-R14）**：维护者已明确接受最终责任；47 行 mapping 继续标记 `PENDING_DOMAIN_REVIEW`，表达逐项签字尚未形成，后续审核与证据留存由维护者负责。

## 6. 一键复现（最终 README 单命令）

Windows：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

Linux：

```bash
./scripts/reproduce.sh
```

Phase 09 最终 QA（在一键复现成功后分开执行）：

```powershell
.\.venv\Scripts\python.exe -I scripts\check_deliverables.py
.\.venv\Scripts\python.exe -I scripts\check_publication_safety.py
.\.venv\Scripts\python.exe -I scripts\check_evidence_freshness.py
```

首次 bootstrap 需要访问 PyPI；依赖安装完成后核心 suite 可离线。

## 7. 相关链接

- [`FINAL_SUMMARY.md`](../FINAL_SUMMARY.md)
- [`demo-script.md`](demo-script.md)
- [`../../docs/v0.4/release-readiness.md`](../../docs/v0.4/release-readiness.md)
- [`../../docs/v0.4/human-decisions.md`](../../docs/v0.4/human-decisions.md)
- [`../../docs/v0.4/publication-record.md`](../../docs/v0.4/publication-record.md)
