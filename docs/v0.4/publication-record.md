# v0.4 Publication Record

本文件记录发布动作与外部动态事实。稳定范围、风险与人工决定分别见
[`release-readiness.md`](release-readiness.md) 和
[`human-decisions.md`](human-decisions.md)。

- 建立日期：2026-08-12（Phase 09 §6.7）
- 最近确认日期：2026-08-14
- Canonical repository：<https://github.com/Daydreaming24/DSSC_Toolbox_Group-C>
- 冲突时以 [`STATUS.md`](STATUS.md) 的追加式更正记录为准

> **本文件当前处于失效待重建状态（2026-08-16）。** 依据
> `DEC-P09-COMMIT-IDENTITY-NOREPLY`，本地 Git 历史已重建、既有远程仓库已删除并以同名
> 重建。因此下文第 2–3 节记录的候选 commit SHA、Actions run ID/URL、job 结论与 resolved
> SHA **全部指向已不存在的提交与已删除的仓库**，第 1 节的 `Immutable repository ID` 也
> 已随重建更换。这些行保留为重建前的历史事实，不再是当前发布链的有效绑定。
>
> 当前候选的绑定将在重新完成 Phase 09 §6.9–§6.11 后，由 §6.11 记录性提交写入本文件与
> [`STATUS.md`](STATUS.md)。在此之前，v0.4 的发布链结论按**未闭合**处理。变更背景见
> `STATUS.md` 末尾的《Phase 09 commit 身份修订与历史重建记录》。

## 1. 稳定目标

| 字段 | 值 |
|---|---|
| Canonical repository URL | `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C` |
| Clone URL | `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| Immutable repository ID | `1332105560` |
| Owner / name | `Daydreaming24` / `DSSC_Toolbox_Group-C` |
| Visibility | `Public` |
| Default branch | `main` |
| Workflow path | `.github/workflows/validate.yml` |
| Repository license | 无根 `LICENSE`；v0.4 依据 `DEC-P09-LICENSE-NONE-FINAL-V0.4` 公开托管且不授予通用版权复用许可 |

## 2. 上一次已确认候选（历史有效事实）

| 字段 | 值 |
|---|---|
| 候选 commit SHA | `ce234885b6a7a24ba599fbc6eaabf15537c3b829` |
| 本地 clean clone | Windows / Linux 均 `PASS` |
| Remote name / URL | `origin` / `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| Push | 普通 push `main`（无 force） |
| Actions run ID | `31712108142` |
| Actions run URL | https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31712108142 |
| Run event | `push` |
| Run `head_sha` | `ce234885b6a7a24ba599fbc6eaabf15537c3b829` |
| Ubuntu job | `success` |
| Windows job | `success` |
| Docker job | `success` |
| Resolved SHA | `ce234885b6a7a24ba599fbc6eaabf15537c3b829` |
| 一键复现 | exit 0 |
| Phase 09 三 checker | exit 0 |

更早的 `90cf2de062e43743cb179ed9141885e5a6eccfab`、run
<https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31652415581>，
以及记录提交 `021796bd73a19c57f3798d70531ccdcde79eb057`、run
<https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31652819982> 继续作为
历史事实保留；它们不替代后续新候选所需的 local/remote clean-clone 证据。

随后已确认候选 `6cb004fa086df1138256af4cc21cb4fd032bab11`、run
<https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31722370069> 及其
Windows/Linux 本地 clean clone、三平台 CI 和 canonical URL 远程 clean clone 也继续作为
历史有效事实保留；其 §6.11 记录提交为 `54adc9f39d473d3703810f45845801e02f8cf6fe`。

## 3. 2026-08-14 人工治理责任收口后的当前同步候选

本节记录候选提交形成之后已经发生且已独立核验的外部动态事实。记录性提交只描述候选
`e305d16a…`，不把自身 SHA 当作候选证据。

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

候选 parent 为 Phase 06–08 恢复提交
`6588e16887255a8010b7739734d6fe98f05d20bf`。Windows/Linux 本地真克隆均以
`--no-local` 创建并保持 tracked tree clean；Linux 成功证据来自 WSL 原生文件系统中的
独立 clone。远程真克隆从 canonical GitHub URL 创建；一键复现、frozen 104/104、suite
`all` 17/17、三个 Phase 09 checker、documentation canonical/100 项 self-test 与 CI
canonical/59 项 self-test 均通过。

必需 job 的精确绑定为：Ubuntu `94655416174`、Windows `94655416113`、Docker
`94655416168`；三个 job 均为 `completed/success` 且 `head_sha` 均等于候选 SHA。候选
SHA、Actions `head_sha` 与远程 clone resolved SHA 三方一致。

## 4. 当前治理状态

| 项 | 状态 |
|---|---|
| v0.4 无通用 license grant | `APPROVED` / `ACCEPTED_LIMITATION` |
| D 组与来源 ZIP 再分发、历史路径公开风险 | `APPROVED` |
| P00-R14 最终人工治理责任 | `ACCEPTED_LIMITATION`；维护者（GitHub：`Daydreaming24`）已明确接受责任 |
| 最近已确认候选 | §6.9–§6.11 技术链与动态记录均已完成，继续作为可核查事实 |
| 候选更新规则 | 每个发生 tracked 内容变化的新候选均须独立完成 §6.9–§6.11，并在本文件原位更新当前同步候选 section |

维护者已通过 `DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED` 明确接受 C/D final review、
Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 责任。Phase 06/07
和 mapping 文件的 `PENDING` 状态继续保留为历史/产物事实。当前状态以
[`STATUS.md`](STATUS.md) 最新追加记录为准；已确认候选的公开 push、CI 与 clone 事实继续有效。

## 5. 未请求动作

| 动作 | 状态 |
|---|---|
| Tag | `NOT_REQUESTED` |
| GitHub Release | `NOT_REQUESTED` |
| Default-branch change | `NOT_REQUESTED` |
| Branch protection | `NOT_REQUESTED` |
| Force push | 禁止 |
