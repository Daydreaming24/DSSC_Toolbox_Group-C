# v0.4 Release Readiness

本文件是 Phase 09 §6.7 的发布就绪收口文档。它只读取 Phase 00 只读快照
[`risk-register.md`](risk-register.md) 与 `STATUS.md` 各阶段小节，不回写
`risk-register.md`。

- 审计日期：2026-08-14（§6.7 初稿；§6.8 决定与本轮同步候选发布事实收口后更新风险终态）
- validation-suites 合同：`contract_version=1.6.0`；
  path=`C_Semantic_Treehouse/manifests/validation-suites.json`；
  manifest SHA-256=`09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`
- deliverables path：`C_Semantic_Treehouse/manifests/deliverables.json`（内容 hash 只出现在 ignored runtime evidence）
- 核心发布证据索引：[`../../C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json`](../../C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json)
- 最终目标仓库：`https://github.com/Daydreaming24/DSSC_Toolbox_Group-C`（Public；default branch=`main`；无根 `LICENSE`）
- 通用 license 决定：v0.4 **公开发布但不授予通用版权复用许可**（`DEC-P09-LICENSE-NONE-FINAL-V0.4`，`APPROVED`）
- 最近已确认候选的 SHA、CI run URL/job 结论与远程 clean-clone 绑定统一见 [`publication-record.md`](publication-record.md)，本文件不复制动态值；当前同步周期状态以 `STATUS.md` 最新追加记录为准

终态取值：

| 终态 | 含义 |
|---|---|
| `RESOLVED` | 已由具名 Phase 的 `STATUS.md` 小节关闭，并有稳定证据路径 |
| `ACCEPTED_LIMITATION` | 接受为已知限制；同步写入 final checklist 已知限制 |
| `OPEN_BLOCKING` | Phase 00 登记为阻塞发布且尚未关闭/批准；阻断 Phase 09 `COMPLETE` 与最终发布治理签字；不抹去此前已完成的公开 push、CI 与 clean-clone 事实 |

---

## 1. Phase 00 risk-register 原始风险终态

| ID | 阻塞 GitHub 发布 | 最终处置 | 处置说明与证据 |
|---|---|---|---|
| P00-R01 | 是 | `RESOLVED` | 维护者已重建、批准并使用精确目标：owner=`Daydreaming24`、name=`DSSC_Toolbox_Group-C`、URL=`https://github.com/Daydreaming24/DSSC_Toolbox_Group-C`、visibility=`Public`、default branch=`main`。空仓库 `0 refs` 是首次 push 前的历史预检；当前动态引用见 [`publication-record.md`](publication-record.md)。 |
| P00-R02 | 是 | `ACCEPTED_LIMITATION` | 维护者明确批准 v0.4 **公开发布且不授予通用版权复用许可**：无根 `LICENSE`，project-authored 文件保持 SPDX `NOASSERTION`，redistribution classification=`publish-without-license-grant`，decision=`DEC-P09-LICENSE-NONE-FINAL-V0.4`。公开可访问、浏览或 clone 不构成使用、修改或再分发许可；未来如授予许可证，须形成独立明确决定。D 组与来源 ZIP 的具名再分发决定保持独立。见 `NOTICE`、`THIRD_PARTY_MATERIALS.md` 与 [`human-decisions.md`](human-decisions.md)。 |
| P00-R03 | 是 | `RESOLVED` | 维护者接受 ZIP 内历史绝对路径随批准 ZIP 公开；decision `DEC-P09-SOURCE-ZIP-REDIST-APPROVED`；privacy allowlist 与 safety checker 继续约束扫描边界。 |
| P00-R04 | 是 | `RESOLVED` | GitHub 身份 `Daydreaming24`；commit author 为 `daydreaming <188458589+Daydreaming24@users.noreply.github.com>`。原沿用既有本地历史身份的决定已被 `DEC-P09-COMMIT-IDENTITY-NOREPLY` 取代：该身份使用的可路由个人邮箱不适合公开演示场景，发布前已重建本地 Git 历史并以同名重建远程仓库。见 [`human-decisions.md`](human-decisions.md)。 |
| P00-R05 | 是 | `RESOLVED` | `origin`、`main` 普通 push、最近已确认候选绑定的 GitHub Actions 三个必需 job 与 GitHub URL 远程 clean clone 均已实际成功。最近已确认候选的 SHA、run URL/结论与 clone resolved SHA 只以 [`publication-record.md`](publication-record.md) 的动态记录为准；历史结论见 `STATUS.md` Phase 09 §6.10–§6.11。 |
| P00-R06 | 是 | `RESOLVED` | Phase 01：CPython 3.12.10、repo `.venv`、hash locks、bootstrap、doctor 与 host/container environment 证据。`STATUS.md` Phase 01 小节；`requirements.lock` SHA-256 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2`。 |
| P00-R07 | 是 | `RESOLVED` | Phase 01 完成隔离重建；Phase 08 完成本地 clean-room rehearsal（Windows/Linux）；Phase 09 已对最近确认候选完成真正的 Windows/Linux 本地 clean clone 与 GitHub URL 远程 clean clone。当前绑定见 [`publication-record.md`](publication-record.md)；阶段证据见 `STATUS.md` Phase 01、Phase 08 与 Phase 09 §6.9–§6.11。 |
| P00-R08 | 是 | `RESOLVED` | Phase 02–05：统一 baseline/release/v0.4-test-cases manifests、suite registry 与 `all` composition。最终关闭于 Phase 05；`STATUS.md` Phase 05。 |
| P00-R09 | 是 | `RESOLVED` | Phase 05：66/66 四状态 cases、非零 target activation、report graph oracle 与负控。`STATUS.md` Phase 05；fixtures under `C_Semantic_Treehouse/fixtures/v0.4/`。 |
| P00-R10 | 是 | `RESOLVED` | Phase 02 mandatory OpenAPI + Phase 05 依赖 preflight/缺依赖 ERROR。`STATUS.md` Phase 02/05。 |
| P00-R11 | 是 | `RESOLVED` | Phase 03 ADR-001 + Phase 04/05 实现：payload 无 `dct:conformsTo`，ClosedShape Warning → `INAPPLICABLE`。`STATUS.md` Phase 03–05；ADR-001。 |
| P00-R12 | 否 | `ACCEPTED_LIMITATION` | 可选外部证据轨：Mermaid parser/render/视觉 QA 与外部 ITB/SEMIC 为 `DEFERRED`/`NOT RUN`；Semantic Treehouse 为隔离可选轨（见 §2 与 final checklist）。不进入核心 `all`，不阻塞核心本地验收。`STATUS.md` Phase 08。 |
| P00-R13 | 否 | `RESOLVED` | 全阶段使用 `CHECKPOINT.md` 记录中断与恢复；Phase 09 当前中断点亦写入该文件。`STATUS.md` 各 Phase 恢复小节。 |
| P00-R14 | 是 | `ACCEPTED_LIMITATION` | 维护者（GitHub 身份 `Daydreaming24`）于 2026-08-14 明确接受 C/D final semantic/contract review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 的最终责任；decision=`DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED`。Phase 06/07 与 mapping 文件中的 `PENDING` 状态保留为历史/产物事实，不解释为逐项签字。见 [`human-decisions.md`](human-decisions.md) 与 `STATUS.md` 最新追加记录。 |
| P00-R15 | 是 | `ACCEPTED_LIMITATION` | “104/104 frozen” 仅证明 frozen manifest 登记边界，不扩张为全部永久保护文件均 hash-bound。8 个 archive wrapper 保持只读保护但无 frozen record。已在导航/清单/本文件与 final checklist 明确边界。`STATUS.md` Phase 00/04/05/09。 |
| P00-R16 | 是 | `RESOLVED` | Phase 07 同步导航/handoff；Phase 09 §6.7 将 docs 导航更新为含 Phase 08/09、deliverables、release-readiness、human-decisions、publication-record 与 final evidence。`STATUS.md` Phase 07 与本小节。 |

### 1.1 阻塞发布汇总（当前）

当前没有 `OPEN_BLOCKING` 风险。P00-R14 已由维护者明确接受相关人工治理责任，终态为 `ACCEPTED_LIMITATION`；早期产物保留的 `PENDING` 值继续表达逐项签字尚未形成。

P00-R02 已按维护者最终决定收口为 `ACCEPTED_LIMITATION`：v0.4 可以公开发布，公开访问不授予版权复用许可。P00-R01（目标仓库）、P00-R03（历史路径）、P00-R04（身份）与 P00-R05（远程发布链）均已关闭。D 组/ZIP **再分发**仍由各自具名决定覆盖。

---

## 2. Phase 01–08 STATUS 新增风险

下列风险不在 Phase 00 原始快照中，但由后续 Phase 的产物/交接章节登记，供 Phase 09 汇总。

| ID | 来源 Phase | 最终处置 | 说明与证据 |
|---|---|---|---|
| P06-R01 | Phase 06 | `RESOLVED` | “manifest binding 优先于 Phase-local 可写路径”。preflight 已阻止对 hash-bound 历史文件的漂移写入；documentation path/hash checks 继续 fail closed。`STATUS.md` Phase 06 风险处置；Phase 07 文档 gate。 |
| P08-R01 | Phase 08 | `ACCEPTED_LIMITATION` | Docker Hub 对 digest-pinned layer 的 short read/EOF 曾阻断 Treehouse image build。后续 recovery 在运输稳定后完成可选轨部署；该风险作为 Treehouse 可选轨运维限制保留，**不**进入核心 `all`，**不**单独阻塞核心 GitHub 候选的本地验收。恢复条件见 `STATUS.md` Phase 08。 |

### 2.1 可选轨真实状态（不虚构成功）

| 可选轨 | 真实状态 | 边界 |
|---|---|---|
| Semantic Treehouse | 隔离可选轨；受控部署/导入/SHACL 已有本地证据；runtime `PAUSED`；publication=`NOT RUN` | 不进入核心 `all`；raw upstream preflight 历史结论保持 `BLOCKED` |
| Mermaid parser / render / 视觉 QA | `DEFERRED` | Phase 07 仅 structural lint |
| 外部 ITB / SEMIC | `DEFERRED` / `NOT RUN` | 无数据外传授权；uploaded files=0 |

当前 Treehouse 作用域投影（与 documentation checker 合同一致）：

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`。

`SHACL validator manifest digest=sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`; `SHACL validator security boundary=non-root/internal-only/zero-host-port/read-only-rootfs/drop-all/no-new-privileges/resource-bounded`; `SHACL validation controls=positive-pass/negative-fail/idempotent-recheck-pass/EasyRDF-4-pattern-local-review-patch`; `PAUSED persistence=containers-networks-app-db-volumes-preserved`。

---

## 3. 本地最终 QA 门槛（§6.1–§6.6，稳定）

| 门槛 | 状态 | 稳定证据 |
|---|---|---|
| validation-suites 合同冻结 | `PASS` | `STATUS.md` Phase 09 §6.1；registry 与 Phase 08 hash 一致 |
| deliverables manifest + schema + checker | `PASS` | `C_Semantic_Treehouse/manifests/deliverables.json`；`scripts/check_deliverables.py` |
| publication-safety / evidence-freshness | `PASS` | `scripts/check_publication_safety.py`；`scripts/check_evidence_freshness.py` |
| Phase 08 一键复现入口只读复核 | `PASS` | `scripts/reproduce.ps1` / `scripts/reproduce.sh`（未修改） |
| 本地核心验证 host + Docker `all` | `PASS` | suite `all` 17/17；core-results / core-report |
| 无自引用 tracked 发布证据 | `PASS` | `evidence/releases/v0.4/{core-results.json,core-report.md,evidence-index.json,README.md}` |

### 3.1 §6.8 决定与既有发布事实（当前）

| 门槛 | 状态 |
|---|---|
| 通用 License | `APPROVED` final-for-v0.4 — 公开发布但不授予通用版权复用许可；无根 `LICENSE`；`DEC-P09-LICENSE-NONE-FINAL-V0.4`；MIT 草稿已撤回 |
| D 组 / ZIP / 历史路径再分发 | `APPROVED` |
| 身份 | `APPROVED`（Daydreaming24 / 既有 author） |
| 最终仓库 URL | **已绑定并已使用** Public repository `DSSC_Toolbox_Group-C`；default branch=`main` |
| `NOTICE` / `THIRD_PARTY_MATERIALS.md` | 已更新为 final-for-v0.4 的“公开发布、不授予通用版权复用许可”叙述 |
| local clean clone / remote add / ordinary push / CI / remote clean clone | 最近已确认候选的 Windows/Linux local clean clone、普通 push、候选绑定三-job CI 与 canonical URL remote clean clone 均已通过；当前动态证据见 [`publication-record.md`](publication-record.md) |
| tag / GitHub Release / branch protection | `NOT_REQUESTED` |

### 3.2 最终治理门槛处置

| 门槛 | 状态 |
|---|---|
| P00-R14 最终人工治理角色 | `ACCEPTED_LIMITATION`；维护者已明确接受责任 |

P00-R14 的 reviewer 可用性与最终责任风险已由维护者（GitHub 身份 `Daydreaming24`）明确接受。47 条 mapping 与 Phase 06/07 治理产物继续保留真实 `PENDING` 状态，后续逐项签字由维护者负责。每个发生 tracked 内容变化的新候选均须独立完成 §6.9–§6.11；已确认候选的 push、CI 三 job 与远程 clean clone 作为可核查事实保留，动态证据见 [`publication-record.md`](publication-record.md)，有效状态以 `STATUS.md` 最新追加记录为准。

---

## 4. 长期责任

1. 维护者（GitHub 身份 `Daydreaming24`）承担 P00-R14 的 C/D final review、Domain Reviewer、SSSOM domain review 与 Release Approver 长期责任；后续形成逐项审核时保留可核查签字依据。
2. 任何候选文件变化后：必要时重跑 core evidence generator → 再生 deliverables → 三个 Phase 09 checker → documentation/CI 检查 → 新候选的本地 clean clone、普通 push、CI 与远程 clean clone。
3. 将来若授予项目通用许可证，须形成独立明确决定并同步根 `LICENSE`、NOTICE、第三方台账与 deliverables；不得把当前 Public 可访问状态解释为许可证。
4. tag、GitHub Release、default branch 变更与 branch protection 继续为 `NOT_REQUESTED`，需要各自独立授权。
5. 可选轨（Treehouse / Mermaid render / ITB-SEMIC）恢复需独立授权，且不得改写核心 `all` composition。
6. 发布后变更须保持 validation-suites `contract_version`/hash 与 deliverables 清单同步，禁止第二套硬编码 required-files 列表。

---

## 5. 相关文档

- [`human-decisions.md`](human-decisions.md) — 人工决定台账（§6.8 已记录批准项）
- [`publication-record.md`](publication-record.md) — 最近已确认候选、push、CI 与 remote-clone 的动态证据真源
- [`STATUS.md`](STATUS.md) — 机器可读阶段真源
- [`../../C_Semantic_Treehouse/docs/final-checklist.md`](../../C_Semantic_Treehouse/docs/final-checklist.md) — 最终检查表与已知限制
- [`../../C_Semantic_Treehouse/FINAL_SUMMARY.md`](../../C_Semantic_Treehouse/FINAL_SUMMARY.md) — 交付摘要
