# v0.4 Publication Record

本文件记录发布动作与外部动态事实。稳定范围、风险与人工决定分别见
[`release-readiness.md`](release-readiness.md) 和
[`human-decisions.md`](human-decisions.md)。

- 建立日期：2026-08-12（Phase 09 §6.7）
- 最近确认日期：2026-08-16
- Canonical repository：<https://github.com/Daydreaming24/DSSC_Toolbox_Group-C>
- 冲突时以 [`STATUS.md`](STATUS.md) 的追加式更正记录为准

> **仓库已于 2026-08-16 重建（`DEC-P09-COMMIT-IDENTITY-NOREPLY`）。** 本地 Git 历史
> 重建为新的提交序列，既有远程仓库被删除并以同名重建，canonical URL 保持不变但
> `Immutable repository ID` 已更换。因此第 3 节记录的重建前候选 SHA 与 Actions run URL
> 指向已不存在的提交与已删除的仓库，保留为当时确实发生并已核验的历史事实，不再可
> 检索，也不构成当前发布链的有效绑定。当前有效绑定见第 2 节。背景见 `STATUS.md` 的
> 《Phase 09 commit 身份修订与历史重建记录》。

## 1. 稳定目标

| 字段 | 值 |
|---|---|
| Canonical repository URL | `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C` |
| Clone URL | `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| Immutable repository ID | `1335821262`（2026-08-16 重建；重建前为 `1332105560`，已删除） |
| Repository created at | `2026-08-16T10:31:57Z` |
| Owner / name | `Daydreaming24` / `DSSC_Toolbox_Group-C` |
| Visibility | `Public` |
| Default branch | `main` |
| Workflow path | `.github/workflows/validate.yml` |
| Commit author 身份 | `陈凌石 <188458589+Daydreaming24@users.noreply.github.com>` |
| Repository license | 无根 `LICENSE`；v0.4 依据 `DEC-P09-LICENSE-NONE-FINAL-V0.4` 公开托管且不授予通用版权复用许可 |

## 2. 重建后的当前同步候选

本节记录候选提交形成之后已经发生且已独立核验的外部动态事实。记录性提交只描述候选
`436cd3b7…`，不把自身 SHA 当作候选证据。

| 字段 | 值 |
|---|---|
| 候选 commit SHA | `436cd3b79cb081092c606220130b8b2290942e65` |
| 候选 parent | `589e9194fcc3d2549737a992c54dc573531eab10` |
| 本地 clean clone | Windows / Linux 均 `PASS` |
| Remote name / URL | `origin` / `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| Push | 普通 push `main`（无 force） |
| Actions run ID | `31944645429` |
| Actions run URL | https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31944645429 |
| Run event | `push` |
| Run `head_sha` | `436cd3b79cb081092c606220130b8b2290942e65` |
| Ubuntu job | `success` |
| Windows job | `success` |
| Docker job | `success` |
| Resolved SHA | `436cd3b79cb081092c606220130b8b2290942e65` |
| 一键复现 | exit 0 |
| Phase 09 三 checker | exit 0 |

Windows 与 Linux 本地真克隆均以 `--no-local` 创建并保持 tracked tree clean；Linux 证据
来自 WSL2 原生文件系统（Ubuntu 24.04.4 LTS / x86_64）中的独立 clone，使用固定
CPython 3.12.10。远程真克隆从 canonical GitHub URL 匿名创建；一键复现、frozen
104/104、suite `all` 17/17、三个 Phase 09 checker、documentation canonical 与 self-test、
CI canonical 与 59 项 self-test 均通过。

本地 HEAD、远程 `refs/heads/main`、Actions `head_sha` 与远程 clone resolved SHA
四者完全一致。push 为 `589e919..436cd3b` 的 fast-forward。三个必需 job 的精确绑定为：
Ubuntu `95158699831`、Windows `95158699907`、Docker `95158699948`；三者均为
`completed/success` 且 `head_sha` 均等于候选 SHA。

同一重建轮次中另有一个被取代的提交，保留为失败事实而非已确认候选：其 SHA 为
`589e9194fcc3d2549737a992c54dc573531eab10`，两个本地 clean clone 通过并已普通 push，
但绑定的 Actions run `31944645429` 之前的一次运行（ID `31942910966`）结论为
`completed/failure`——Ubuntu 与 Docker job 成功，Windows PowerShell job 在
`Bootstrap from hash locks` 步骤末尾的 `doctor --profile host` 处失败，原因是 GitHub
`windows-2022` runner 镜像不再提供 Docker，而 `host` profile 对不执行容器轨的原生 job
强制要求 Docker 能力。该提交未通过 §6.10 的三 job 门槛，因此从未构成已确认候选。修复
方式是新增 `host-no-docker` profile，并以候选 `436cd3b7…` 重新完整执行 §6.9–§6.11。
详见 `STATUS.md` 的《Phase 09 CI profile 缺陷修复记录》。

## 3. 历史已确认候选（重建前，指向已删除仓库）

本节保留重建前最后一个已确认候选。它形成于 repository ID `1332105560` 之下；该仓库
已于 2026-08-16 删除，因此下列 commit SHA 与 run URL 不再可解析。这些记录不构成当前
发布链的有效绑定，也不替代新候选所需的 local/remote clean-clone 证据。

| 字段 | 值 |
|---|---|
| 候选 commit SHA | `e305d16a353aa4367bd667af6e8d87c5a32f6bc3` |
| 本地 clean clone | Windows / Linux 均 `PASS` |
| Remote name / URL | `origin` / `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| Push | 普通 push `main`（无 force） |
| Actions run ID | `31763791740` |
| Actions run URL | https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31763791740 |
| Run event | `push` |
| Run `head_sha` | `e305d16a353aa4367bd667af6e8d87c5a32f6bc3` |
| Ubuntu job | `success` |
| Windows job | `success` |
| Docker job | `success` |
| Resolved SHA | `e305d16a353aa4367bd667af6e8d87c5a32f6bc3` |
| 一键复现 | exit 0 |
| Phase 09 三 checker | exit 0 |

更早的重建前候选 `ce234885b6a7a24ba599fbc6eaabf15537c3b829`（run `31712108142`）、
`6cb004fa086df1138256af4cc21cb4fd032bab11`（run `31722370069`）、
`90cf2de062e43743cb179ed9141885e5a6eccfab`（run `31652415581`）与记录性提交
`021796bd73a19c57f3798d70531ccdcde79eb057`（run `31652819982`）同样继续作为历史事实
保留，并同样随旧仓库删除而不再可检索。

## 4. 当前治理状态

| 项 | 状态 |
|---|---|
| v0.4 无通用 license grant | `APPROVED` / `ACCEPTED_LIMITATION` |
| D 组与来源 ZIP 再分发、历史路径公开风险 | `APPROVED` |
| Commit 身份迁移至 GitHub noreply | `APPROVED`（`DEC-P09-COMMIT-IDENTITY-NOREPLY`） |
| P00-R14 最终人工治理责任 | `ACCEPTED_LIMITATION`；维护者（GitHub：`Daydreaming24`）已明确接受责任 |
| 当前已确认候选 | `436cd3b7…` 的 §6.9–§6.11 技术链与动态记录均已完成 |
| 候选更新规则 | 每个发生 tracked 内容变化的新候选均须独立完成 §6.9–§6.11，并在本文件第 2 节原位更新 |

维护者已通过 `DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED` 明确接受 C/D final review、
Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 责任。Phase 06/07
和 mapping 文件的 `PENDING` 状态继续保留为历史/产物事实。当前状态以
[`STATUS.md`](STATUS.md) 最新追加记录为准。

## 5. 未请求动作

| 动作 | 状态 |
|---|---|
| Tag | `NOT_REQUESTED` |
| GitHub Release | `NOT_REQUESTED` |
| Default-branch change | `NOT_REQUESTED` |
| Branch protection | `NOT_REQUESTED` |
| Force push | 禁止 |
