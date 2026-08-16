# v0.4 Human Decisions Ledger

本文件记录 Phase 09 发布相关的人工决定。每项使用 `APPROVED`、`DENIED` 或
`NOT_REQUESTED`，并附批准主体与范围。不得用 `DEFERRED` 规避必需发布门槛。

- 建立日期：2026-08-12（Phase 09 §6.7）
- §6.8 修订：2026-08-13 — 撤回 MIT；最终批准 v0.4 公开发布但不授予通用版权复用许可；维护者绑定并使用既有 Public repository
- P00-R14 修订：2026-08-14 — 维护者（GitHub 身份 `Daydreaming24`）明确接受最终人工治理责任，并授权按 Phase 09 证据链收口该风险
- 机器真源冲突时以 [`STATUS.md`](STATUS.md) 为准
- 本文件 **不** 写入当前候选/HEAD 的动态 CI run ID/URL 或“CI 已成功”声明

## 1. 内容与身份

| 决定项 | 状态 | 批准主体 | 范围 / 备注 |
|---|---|---|---|
| Repository license / no-license choice | `APPROVED`（final-for-v0.4） | 维护者 | 批准 v0.4 **公开发布但不授予通用版权复用许可**；不添加根 `LICENSE`；project-authored 文件 SPDX `NOASSERTION`，redistribution classification=`publish-without-license-grant`；decision `DEC-P09-LICENSE-NONE-FINAL-V0.4`。公开访问、浏览或 clone 不构成使用、修改或再分发许可；未来许可证须独立明确决定。MIT 草稿 **WITHDRAWN**。 |
| D 组文件再分发授权 | `APPROVED` | 维护者 | 允许随公开候选再分发 D 组 received Shape/说明及 v0.4 byte-copy Shape；`DEC-P09-D-GROUP-REDIST-APPROVED` |
| 两份来源 ZIP 再分发授权 | `APPROVED` | 维护者 | 允许随公开候选再分发两份 `inputs/source-archives/` ZIP 及相关 provenance；`DEC-P09-SOURCE-ZIP-REDIST-APPROVED` |
| ZIP 内历史绝对路径公开风险接受 | `APPROVED` | 维护者 | 接受 privacy allowlist 覆盖的 ZIP 内历史路径随 ZIP 公开；同属 `DEC-P09-SOURCE-ZIP-REDIST-APPROVED` |
| Commit author name/email（原决定） | `SUPERSEDED` | 维护者 | 原批准继续使用既有本地历史身份。该身份使用可路由的个人邮箱地址；由于 v0.4 仓库将在与维护者真实身份绑定的场合公开演示，该决定于发布前作废，由下一条取代。原地址不在本表复述。 |
| Commit author name/email（v0.4 发布最终） | `APPROVED` | 维护者 | 使用 GitHub noreply 身份 `daydreaming <188458589+Daydreaming24@users.noreply.github.com>`。发布前将本地 Git 历史重建为单一提交，删除远程仓库并以同名重建，使公开历史不含既往个人邮箱；`git checkout --orphan` 保留原 index，因此 tree 内 blob 与重建前逐字节一致。GitHub 侧同时启用 *Keep my email addresses private* 与 *Block command line pushes that expose my email*。decision `DEC-P09-COMMIT-IDENTITY-NOREPLY`。 |
| GitHub 登录身份 | `APPROVED` | 维护者 | `Daydreaming24`（仓库 owner） |
| P00-R14 最终人工治理责任 | `APPROVED`（responsibility accepted） | 维护者（GitHub：`Daydreaming24`） | 明确接受 C Group final semantic review、D Group final contract review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 的最终责任，并批准在当前候选完成 Phase 09 §6.9–§6.11 后收口 Phase 09；decision `DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED`。Phase 06/07 的 `PENDING` 记录与 47 条 mapping 的 `PENDING_DOMAIN_REVIEW` 保留为历史/产物事实；本决定不虚构逐项追溯签字。 |

### 1.1 已知非发布决定（历史，供参考）

| 决定 | 状态 | 记录位置 |
|---|---|---|
| ADR-001 / ADR-002 / ADR-003 | `ACCEPTED`（2026-08-10） | `docs/v0.4/decisions/`；`STATUS.md` Phase 03 |
| Phase 08 Treehouse finding-specific opt-in | `APPROVED` | `STATUS.md` Phase 08 |
| Phase 08/09 documentation clean-room allowlist 最小修复 | `APPROVED` | `STATUS.md` Phase 08 recovery addendum |
| 曾带 MIT 初始化的同名仓库 | **WITHDRAWN / 已由维护者重建为空仓库** | 首次 push 前曾以 0 refs 完成预检；其后按批准普通 push 填充，当前动态事实见 [`publication-record.md`](publication-record.md) |

场景数据 CC-BY-4.0（`inputs/original-plan/**`）为已知来源约束
（`DEC-SCENARIO-CC-BY-4.0`），只约束该场景数据。

## 2. Repository 模式

| 模式 | 状态 | 精确目标 |
|---|---|---|
| 创建新 repository | `NOT_REQUESTED`（本轮） | 维护者网页重建同名空仓库是已完成历史事实，见 §1.1；本轮 agent 不创建 repository |
| 使用既有 repository | `APPROVED` | 以下精确目标（由空仓库完成首次普通 push 后持续使用） |

### 2.1 精确目标（当前绑定）

| 字段 | 值 |
|---|---|
| Owner | `Daydreaming24` |
| Repository name | `DSSC_Toolbox_Group-C` |
| Display 意图 | DSSC Toolbox - Group C |
| Visibility | Public（GitHub 页面可复核） |
| Default branch | `main` |
| Canonical URL | `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C` |
| Clone URL (HTTPS) | `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| 初始化策略（历史） | **空仓库**；无 README / .gitignore / License 初始 commit；随后只以批准的普通 push 填充 |
| 只读预检（历史） | 首次 push 前 `git ls-remote` 对 clone URL无输出（0 refs） |
| 当前发布链 | remote、`main` 普通 push、GitHub Actions 三个必需 job 与远程 clean clone 已有实际成功历史；最新动态 SHA/run/clone 绑定见 [`publication-record.md`](publication-record.md) |

## 3. 外部写动作（逐项）

| 动作 | 状态 | 备注 |
|---|---|---|
| 创建 GitHub repository | `NOT_REQUESTED`（本轮） | 维护者重建是历史事实；本轮只使用下表绑定的既有 immutable repository |
| 创建本地候选 commit | `APPROVED` | 维护者 2026-08-12 明确授权首轮「§6.9 + remote add + push」，并在当前请求中再次明确要求完成修改后提交并同步远程 |
| 新增 Git remote / 使用精确 remote URL | `APPROVED` | remote 名 `origin`；URL 精确为 `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| push 精确 branch | `APPROVED` | `main` → `origin/main`；维护者当前再次要求同步；**禁止** force push |
| 手工重跑 `validate.yml` | `NOT_REQUESTED` | |
| 设置或更改 default branch | `NOT_REQUESTED` | |
| 设置 branch protection / required checks | `NOT_REQUESTED` | |
| 创建 tag | `NOT_REQUESTED` | |
| 创建 GitHub Release | `NOT_REQUESTED` | |

## 4. 当前决定与发布边界

1. 无根 `LICENSE`；`DEC-P09-LICENSE-NONE-FINAL-V0.4` 为本次 v0.4 的最终 `APPROVED` 决定：允许公开发布，不授予通用版权复用许可。
2. D 组 / ZIP / 历史路径再分发 `APPROVED`。
3. 最终仓库 URL 已绑定并使用；首次 push 前的空仓库预检与随后成功的 push/CI/远程 clone 均为历史事实，动态绑定统一见 [`publication-record.md`](publication-record.md)。
4. 维护者当前再次授权完成新候选 commit 并向同一 `origin/main` 普通 push；任何候选内容变化后均须按 Phase 09 §6.9–§6.11 独立重跑本地 clean clone、CI 与远程 clean clone。
5. 维护者（GitHub 身份 `Daydreaming24`）已通过 `DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED` 明确接受 P00-R14 所列最终人工治理责任；早期产物的 `PENDING` 标记继续保留。tag、GitHub Release、default branch 变更与 branch protection 均保持 `NOT_REQUESTED`。

## 5. 当前结论

**目标仓库：已绑定、Public、default branch 为 `main`，并已有成功普通 push/CI/remote-clone 历史。**

**通用 License：v0.4 已最终批准“公开发布但不授予通用版权复用许可”（无根 LICENSE）。**

**再分发：已批准。**

**外部写动作：新候选 commit 与向精确 `origin/main` 普通 push 已获维护者当前授权；tag/Release/protection 未请求。**

**Phase 09：P00-R14 已按维护者明确责任接受决定收口为 `ACCEPTED_LIMITATION`，当前无 `OPEN_BLOCKING` 风险。任何 tracked 候选内容变化均须独立完成 Phase 09 §6.9–§6.11；已完成事实以 `STATUS.md` 最新追加记录为准，进行中的唯一恢复点以 `CHECKPOINT.md` 为准。**
