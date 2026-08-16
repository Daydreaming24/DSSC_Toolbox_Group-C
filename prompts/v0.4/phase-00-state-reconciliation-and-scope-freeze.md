# Phase 00 Prompt — 当前状态复核、范围冻结与执行台账

你位于仓库根目录。完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md` 和本文件，只执行 Phase 00。进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后停止。

## 1. 目标

把迁移后的仓库实际状态固化为 v0.4 开发的可信起点：核验 Git、冻结输入、迁移完整性、目录边界和本机观察；修正文档中的过时状态；建立权威矩阵、风险台账，并创建后续所有 Phase 共用的 `docs/v0.4/STATUS.md`（历史记录）和 `docs/v0.4/CHECKPOINT.md`（中断点）。

Phase 00 的完成结果只证明"迁移基线和工作边界已经复核"。它不证明环境已可复现、v0.1–v0.3 已在当前环境通过，也不证明 v0.4 已实现。

## 2. 非目标

- 不安装 Python 依赖，不创建 `.venv`，不启动或配置外部服务。
- 不实现 bootstrap、统一验证器、Docker 验证镜像或 CI。
- 不创建或修改任何 v0.4 模型、fixture、manifest、测试或发布报告。
- 不重新运行旧验证脚本来形成当前 PASS 结论。
- 不配置 Git remote，不 commit、不 push、不打 tag、不改写历史。
- 不为状态记录发明额外的机器验证格式（例如逐字段 hash 绑定的"激活记录"、不可变 JSON projection）。状态记录只使用 `docs/v0.4/STATUS.md` 和 `docs/v0.4/CHECKPOINT.md` 这两份纯 Markdown 文件。

## 3. 权威输入

完整读取并交叉核对：

- `README.md`
- `迁移清单.md`
- `.gitignore`、`.gitattributes`
- `docs/environment.md`
- `docs/version-naming.md`
- `docs/v0.4/README.md`
- `docs/v0.4/v0-errata.md`
- `prompts/v0.4/human-intervention-policy.md`
- `docs/provenance/**`
- `scripts/README.md`
- `scripts/verify_frozen_files.py`
- `inputs/source-archives/SHA256SUMS`
- `inputs/d-group/v0.4/README.md`
- `inputs/d-group/v0.4/SHA256SUMS`
- `prompts/v0/**`，仅用于理解历史流程
- 当前 Git 状态、HEAD、分支、提交数量、remote 和 tracked-files 状态

同时只读抽查四类冻结内容：两份原始 ZIP、`inputs/original-plan/`、D 组两份输入、`model/v0.1/` 至 `model/v0.3/`。

## 4. 进入门槛

进入实施前必须满足：

1. 当前目录可识别为本项目根目录，且存在 `scripts/verify_frozen_files.py`。
2. 能完整读取 Master、`human-intervention-policy.md`、本 Phase 和冻结 manifest。
3. `git status --short --branch` 已执行；任何既有修改均已识别归属。
4. 已使用本阶段的预环境原生 SHA-256 命令核验 `docs/provenance/manifests/frozen-files-SHA256SUMS`，且返回 0；Phase 00 不借用全局 Python。
5. 未发现会被本 Phase 覆盖的用户未提交修改。

任一门槛失败时：只记录可安全获得的事实。需要用户选择、纠正或授权时标记 `AWAITING_HUMAN_DECISION`；客观条件无法满足且当前没有安全选项时标记 `BLOCKED`。写明命令、退出码、受影响路径和下一项允许动作，然后按 `human-intervention-policy.md` 把当前进度写入 `CHECKPOINT.md` 并停止。冻结校验失败时不得继续修正文档来掩盖问题。

## 5. 可写路径

仅允许创建或修改：

- `README.md`
- `迁移清单.md`
- `docs/environment.md`
- `docs/v0.4/current-state.md`
- `docs/v0.4/scope-and-authority.md`
- `docs/v0.4/risk-register.md`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`
- `build/phase-00/**`

若 provenance 说明与其机器 manifest 存在已核实的内部矛盾，先把问题记入 risk register。本 Phase 不直接改写 provenance manifest。

## 6. 保护路径

除 Master 永久保护范围外，本 Phase 还保护：

- `prompts/v0.4/**`
- `.github/**`
- `scripts/**`
- `tools/**`
- `C_Semantic_Treehouse/**`
- `Dockerfile.validation`、`docker-compose.validation.yml`、`Makefile`
- 所有 requirements、lock、环境配置和生成报告

不得通过更改 `.gitignore` 或 `.gitattributes` 隐藏审计问题。

## 7. 任务

### 7.1 复核 Git 和仓库身份

记录以下事实，不把预期值硬编码为断言：

- 当前分支、HEAD、提交数量和 dirty flag（绝对根目录路径本身只进入机器环境清单，不进入确定性结果）。
- remote 是否存在。
- `.git/` 是否属于当前新仓库，仓库内是否出现嵌套 `.git/`。
- 工作树中的既有修改及其归属。

把这些事实和当前 `git status --short` 的完整输出记入 `STATUS.md` 的 Phase 00 小节，作为后续 Phase 判断"哪些改动发生在 Phase 00 之前/之后"的参考。

若观察到仓库已经初始化，应更新仍声称"尚未初始化 Git"的现行文档。历史归档和冻结材料中的旧结论保持原样。

### 7.2 复核迁移完整性

运行预环境原生冻结校验并记录 checked 数量。交叉核对：

- 两份来源 ZIP 的路径、大小和 SHA-256 已登记。
- `inputs/original-plan/` 仅包含登记的有效内容。
- D 组 TTL 与说明文件的 hash 与 `SHA256SUMS` 一致。
- v0.1–v0.3 的文件位于永久保护范围。
- 公开工作树没有意外的 `__MACOSX/`、`.DS_Store`、`._*` 或迁移暂存目录。
- 隐私排除项与 `docs/provenance/manifests/privacy-exclusions.tsv` 一致。

不要解压、重打包、改名或格式化原始 ZIP 和冻结文本。

### 7.3 建立当前状态报告

创建 `docs/v0.4/current-state.md`，至少区分：

- 已完成并由命令证明的迁移事项。
- 已建立但尚未实现的目录骨架。
- 当前可用的系统工具观察。
- 环境、模型、验证、CI、clean clone 和发布仍未完成的事项。
- 历史报告的证据边界。

报告顶部写明审计日期和证据命令；易变化的工具状态标注为"本次观察"。

### 7.4 冻结范围和权威关系

创建 `docs/v0.4/scope-and-authority.md`，用表格列出：

- 路径或信息类别。
- 角色：规范性输入、解释性输入、冻结历史、可编辑源、临时生成物、发布证据。
- 权威优先级。
- 是否可直接修改。
- 修订方法。
- 完整性检查方法。

明确 D 组 TTL 是 v0.4 的规范性可执行契约；D 组说明是解释性材料；冲突通过 issue/decision 和派生文件处理。

### 7.5 建立风险台账

创建带明确审计日期的 `docs/v0.4/risk-register.md`，并在标题/导言声明它是"Phase 00 baseline risk snapshot"。每项包含 ID、事实依据、影响、责任角色、计划处理 Phase、是否阻塞 GitHub 发布和 Phase 00 截止时状态。至少登记：

- 最终 GitHub 仓库名称、可见性、组织/账户归属。
- 仓库 LICENSE 和第三方/学校/D 组材料的再分发授权。
- 冻结 ZIP 内历史绝对路径的公开取舍。
- 初始提交作者邮箱的公开取舍。
- remote 尚未配置时的状态。
- 固定 CPython 3.12、`.venv` 和 hash lock 尚未建立。
- 旧验证器版本硬编码、空目标风险、只读取 `conforms` 和 OpenAPI fail-open。
- `dct:conformsTo` 与 D 组 Closed Shape 的兼容性决定。
- Semantic Treehouse 和外部 validator 只属于后续可选证据轨。
- 单个 Phase 内容较多、一次会话可能跑不完的风险；缓解措施是 `human-intervention-policy.md` 里的 `CHECKPOINT.md` 中断记录机制。
- C 组、D 组和发布审批角色的实际可用性；角色缺失时相关 Phase 应标记 `AWAITING_HUMAN_DECISION`。

Phase 00 COMPLETE 后该 snapshot 保持只读，不能被最终文档当作实时状态。后续风险处置和状态变化分别记录在 `STATUS.md` 对应 Phase 小节，最终由 Phase 09 汇总并引用原 risk ID；不得回写 snapshot 制造历史状态漂移。

### 7.6 校正现行状态文档

- 更新根 README 的"当前状态"和下一步，使其只陈述已证明事实。
- 更新 `docs/environment.md`，把迁移时观察和本次观察分开；保留"正式环境尚待 Phase 01 建立"的结论。
- 更新 `迁移清单.md` 中已经由当前事实证明的状态；保留未完成项目。
- 不更改 `docs/version-naming.md` 的既定含义。

### 7.7 建立 STATUS.md 与 CHECKPOINT.md

按 `master-prompt.md` 第 10 节的格式创建 `docs/v0.4/STATUS.md`：Phase 00 完成时追加第一个 Phase 小节（进入门槛、文件变更、命令及退出码、验收矩阵、证据路径、剩余风险、Phase 01 进入条件）。

创建 `docs/v0.4/CHECKPOINT.md`，初始内容为 `master-prompt.md` 第 10 节给出的空闲占位符。若 Phase 00 本身中途需要暂停（失败、需要人工决定、或单次会话跑不完），按 `human-intervention-policy.md` 的要求先把中断点写入这里再停止。

## 8. 必需产物

- `docs/v0.4/current-state.md`
- `docs/v0.4/scope-and-authority.md`
- `docs/v0.4/risk-register.md`
- `docs/v0.4/STATUS.md`（含 Phase 00 小节）
- `docs/v0.4/CHECKPOINT.md`（空闲占位符，除非 Phase 00 本身中断）
- 已校正的 `README.md`、`docs/environment.md`、`迁移清单.md`
- `build/phase-00/` 中规范化的仓库状态、冻结校验和路径审计机器证据

`STATUS.md` 的 Phase 00 小节必须列出进入门槛、文件 diff、所有命令及退出码、验收矩阵、冻结校验数量、剩余风险和 Phase 01 进入条件。

## 9. 必需命令

从仓库根目录运行并记录实际退出码：

```text
git status --short --branch
git rev-parse --show-toplevel
git log --oneline --decorate
git remote -v
git ls-files
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
git status --short
```

Phase 00 尚未建立仓库 `.venv`，因此不得裸调用 `python`。Windows 使用下面的 PowerShell 原生 SHA-256 检查；Linux 可使用 `sha256sum --check docs/provenance/manifests/frozen-files-SHA256SUMS`。PowerShell 检查必须验证格式、文件存在性、hash 和非零条目数：

```powershell
$manifest = 'docs/provenance/manifests/frozen-files-SHA256SUMS'
$checked = 0
Get-Content -Encoding UTF8 -LiteralPath $manifest | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#')) {
        if ($line -notmatch '^([0-9A-Fa-f]{64})\s+(.+)$') { throw "Invalid manifest record: $line" }
        $expected = $Matches[1].ToLowerInvariant()
        $relative = $Matches[2]
        if (-not (Test-Path -LiteralPath $relative -PathType Leaf)) { throw "Missing frozen file: $relative" }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $relative).Hash.ToLowerInvariant()
        if ($actual -ne $expected) { throw "Frozen hash mismatch: $relative" }
        $checked++
    }
}
if ($checked -eq 0) { throw 'Frozen manifest contains zero records.' }
Write-Output "Frozen-file verification passed: $checked file(s)."
```

使用 PowerShell 或 shell 进行目录和敏感路径检查时，必须记录完整命令或脚本片段的仓库相对位置。不要把包含个人绝对路径的原始扫描结果提交；提交规范化结论和命中项的仓库相对路径。

## 10. 验收矩阵

| ID | 验收项 | 通过条件 | 证据 |
|---|---|---|---|
| P00-A01 | 仓库身份 | 根目录、分支、HEAD、remote 和 dirty 状态均已实际记录 | `current-state.md`、命令退出码 |
| P00-A02 | 冻结完整性 | 冻结校验退出码为 0，checked 数量已记录 | 校验输出、`STATUS.md` |
| P00-A03 | 迁移边界 | 来源、冻结、可写、生成和证据路径均有明确矩阵 | `scope-and-authority.md` |
| P00-A04 | 状态真实性 | README、环境说明和迁移清单不再包含与当前事实冲突的现行声明 | diff 审查 |
| P00-A05 | 风险完整性 | 指定风险均有 owner、处理 Phase 和发布阻塞性；包含单 Phase 跑不完与角色可用性风险；文件明确标为带日期 baseline snapshot | `risk-register.md` |
| P00-A06 | STATUS/CHECKPOINT 就绪 | `STATUS.md` 含格式正确的 Phase 00 小节；`CHECKPOINT.md` 为空闲占位符（或如实记录 Phase 00 自身的中断） | `STATUS.md`、`CHECKPOINT.md` |
| P00-A07 | 修改范围 | unstaged 与 staged 修改均已审查，所有本阶段修改在可写路径内；既有 staged 修改已标明归属且未被覆盖 | `git diff --name-status`、`git diff --cached --name-status` |
| P00-A08 | 内容质量 | unstaged/staged 的 `--check` 均通过，无秘密、个人绝对路径或生成缓存 | 命令输出、人工 diff 审查 |
| P00-A09 | 二次冻结校验 | 完成所有编辑后冻结校验仍返回 0 | 最终命令输出 |

全部 P00-A01 至 P00-A09 通过后才可标记 `COMPLETE`。

## 11. AWAITING 与 BLOCKED 规则

以下情况需要先完成安全的只读诊断：

- 冻结文件缺失或 hash 不匹配。
- 仓库根目录或 Git 身份无法确定。
- 来源/隐私 manifest 与公开树存在无法解释的差异。

诊断后确认当前没有可执行的安全路径时标记 `BLOCKED`。

以下情况直接标记 `AWAITING_HUMAN_DECISION`：

- 待修改路径存在需要用户确认归属或合并方式的重叠修改。
- 当前状态需要用户作出会改变迁移策略、隐私边界、可写范围或权威关系的决定。

两种情况都要按 `human-intervention-policy.md` 把当前进度和证据写入 `CHECKPOINT.md`，然后停止；不修改冻结文件，不自行重迁移，不继续 Phase 01。

## 12. 交接

Phase 01 的进入包必须包含：

- `STATUS.md` 中 Phase 00 小节的 `COMPLETE` 结论。
- 当前环境观察和正式环境缺口。
- 已批准的保护/可写边界。
- 与环境相关的开放风险（引用 `risk-register.md` 中的 risk ID）。
- 通过的最终冻结校验结果。
- `CHECKPOINT.md` 为空闲状态的确认。

明确提示 Phase 01：环境建设必须使用准确 CPython 3.12 补丁号、仓库 `.venv`、含 hash 的精确 lock 和统一 Python 入口；不得继承全局包作为成功依据。

## 13. Stop

完成 `STATUS.md` 中 Phase 00 小节、审查最终 diff 并再次通过冻结校验后立即停止。不要开始安装 Python、生成 lock、创建 `.venv` 或实现 Phase 01 内容。等待用户明确要求执行下一 Phase。
