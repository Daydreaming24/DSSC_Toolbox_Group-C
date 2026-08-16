# v0.4 当前状态报告

审计日期：2026-08-09
审计范围：Phase 00 迁移基线、仓库身份、冻结输入、路径边界与本机工具观察
本次证据目录：`build/phase-00/reconciliation-2026-08-09/`

本报告使用以下实际命令和 PowerShell 5.1 审计脚本形成：

- `git status --short --branch`、`git rev-parse --show-toplevel`、`git log --oneline --decorate`、`git remote -v`、`git ls-files`
- unstaged/staged 的 `git diff --check`、`--stat`、`--name-status` 与 `git status --short`
- `build/phase-00/reconciliation-2026-08-09/verify-frozen-native.ps1`
- `build/phase-00/reconciliation-2026-08-09/audit-inputs.ps1`
- `build/phase-00/reconciliation-2026-08-09/audit-repository-paths.ps1`
- `build/phase-00/reconciliation-2026-08-09/collect-git-evidence.ps1`

Phase 00 没有调用 Python、安装依赖、启动外部服务或运行旧验证器。本报告证明当前迁移基线与工作边界已经复核；环境复现、历史模型当前验证、v0.4 实现、CI 和发布仍需后续 Phase 的独立证据。

## 1. 仓库身份

以下 Git 事实来自 Phase 00 进入时的 clean 工作树：

| 项目 | 实际结果 |
|---|---|
| 规范化仓库根 | `<REPO_ROOT>`；`git rev-parse --show-toplevel` 退出 0，实际绝对根仅保存在 `machine-environment.json` |
| 分支 | `main` |
| HEAD | `f98d2dfa645301010a18593bb004b68868933cf7` |
| 提交数量 | 7 |
| tracked files | 234 |
| entry dirty flag | `false`；工作树和 index 均为空差异 |
| remote | 0 个；`git remote -v` 无输出 |
| tag | 0 个 |
| Git 元数据 | 根 `.git/` 为目录，属于当前仓库；非 bare，无 superproject、submodule 或嵌套 `.git/` |

`git log --oneline --decorate` 显示当前历史从本仓库的 `init` 开始，随后形成 6 个本仓库流程与文档提交。迁移来源仓库的旧 Git 历史没有进入当前 `.git/`。

## 2. 已完成并由命令证明的迁移事项

| 事项 | 本次结果 | 证据 |
|---|---|---|
| 冻结 manifest | 104 条记录均存在、格式有效、SHA-256 一致、已 tracked，并应用 `text: unset` | `frozen-verification-entry.txt`、`input-audit.json` |
| v0 核心来源 ZIP | 130092 bytes；SHA-256 `44f21783e57966c145c19e4c6edd74405bc1ace8ae2f31fae3f4bb92805d1135`；中央目录 146 条目（145 文件、1 目录） | `input-audit.json` |
| 原任务计划 ZIP | 30411 bytes；SHA-256 `ce13a59d3d3834bdc67d74616421ee9b19d262bfda8c4de69bfc7b5193012241`；中央目录 38 条目 | `input-audit.json` |
| ZIP 路径安全 | 两份 ZIP 的中央目录均无 rooted、drive、`..` 或嵌套 `.git` 条目；Phase 00 本阶段未解压或重打包 | `input-audit.json` |
| `inputs/original-plan/` | 冻结迁移 map 登记 11 项；当前目录有 11 项、无 macOS 元数据，路径集合及 `TargetSHA256` 与 map 一致；任务 ZIP 本体 hash 与 38-entry 中央目录另行核对一致，其中 20 个元数据条目按既定规则未迁入 | `input-audit.json` |
| D 组输入 | 2 个 received 文件与 D 组 `SHA256SUMS`、supplemental map、frozen manifest 四方一致 | `input-audit.json` |
| v0.1–v0.3 模型 | v0.1 为 5 文件、v0.2 为 6 文件、v0.3 为 11 文件；实际集合与 frozen manifest 完全一致 | `input-audit.json` |
| 迁移路径快照 | 221 条记录无重复，当前均存在且 tracked | `input-audit.json` |
| 隐私排除 | manifest 登记 7 项；对应公开目标均不存在且未 tracked | `input-audit.json`、`repository-path-audit.json` |
| ZIP 外的 tracked/拟公开文本树卫生 | 无 `__MACOSX/`、`.DS_Store`、`._*`、迁移暂存目录、个人 home 路径、高置信 secret、敏感文件名或 tracked cache/log；两份冻结 ZIP 的字节、路径与中央目录另行审计 | `repository-path-audit.json`、`input-audit.json` |

除 `machine-environment.json` 中按合同允许的实际仓库根外，广义 Windows 绝对路径扫描命中冻结原任务计划中的通用 `D:\DSSC_*` 历史场景位置，以及本报告与 `docs/v0.4/v0-errata.md` 对这些事实的说明。拟公开命中不包含用户名、用户 home 或当前工作区路径；扫描证据只保存仓库相对文件名与行号，不保存匹配原文。

冻结校验的证据边界是 manifest 登记的 104 项。`archive/**` 当前有 61 个 tracked 文件，其中 53 个进入 frozen manifest；其余 8 个是迁移说明 wrapper，受永久只读策略与 `-text` 保护，但没有逐文件 frozen hash。该覆盖差异已登记为 `P00-R15`，Phase 00 没有改写 provenance 或 manifest。

## 3. 已建立但尚未实现的目录骨架

| 区域 | 当前内容 | 当前判断 |
|---|---|---|
| `C_Semantic_Treehouse/model/v0.4/` | 仅有“待实现” README | v0.4 Shape 与发布模型尚未创建 |
| `C_Semantic_Treehouse/fixtures/v0.4/` | 四状态目录、`.gitkeep` 与说明 | PASS/FAIL/INAPPLICABLE/UNTESTABLE fixtures 尚未创建 |
| `C_Semantic_Treehouse/evidence/releases/v0.4/` | 仅有证据边界说明 | 当前发布证据尚未生成 |
| `C_Semantic_Treehouse/manifests/` | tracked tree 中不存在；本机有一个 Git 不跟踪的空 `manifests/schemas/` 回档残留目录 | release、test-case、suite 和 deliverables manifests 尚未建立 |
| 根 `scripts/` | tracked 内容为 `verify_frozen_files.py` 与待实现说明；本机另有 ignored Python cache 残留 | bootstrap、doctor、统一验证器和跨平台包装尚未实现 |
| `.github/workflows/` | 仅有 `.gitkeep` | 当前 CI workflow 尚未实现 |
| 根工具链文件 | 无正式 `requirements.in`、hash lock、`Makefile`、Dockerfile 或 Compose 文件 | 环境与容器合同尚未建立 |

这些目录或占位文件证明边界已经预留，不构成实现或验证成功证据。

## 4. 当前可用系统工具观察

本节均为 2026-08-09 的本次观察，属于易变化的机器环境信息；实际绝对仓库路径与采集时间只在 `machine-environment.json` 中保存。

| 组件 | 本次观察 | 证据边界 |
|---|---|---|
| OS / architecture | Windows NT 10.0.26200.0，X64 | PowerShell/.NET 只读观察 |
| Windows PowerShell | 5.1.26100.8875 Desktop | 本次审计脚本使用该版本运行 |
| Git | 2.45.1.windows.1 | `git --version` |
| Docker client | 29.4.1 | `docker --version` |
| Docker server | 29.4.1，可连接 | `docker info --format '{{.ServerVersion}}'` |
| Docker Compose | v5.1.3 | `docker compose version` |
| `python` / `py` | 命令可发现；Phase 00 未执行 | 只做 `Get-Command` 发现，不形成解释器验收 |
| `pwsh` / `make` / `sh` | 未发现 | 本次 `Get-Command` 观察 |
| `.venv/` | 已存在且被 `.gitignore` 忽略；3638 个文件；`pyvenv.cfg` 写明 3.12.10 | 来自一次已由用户确认回档的早期 Phase 00/01 尝试；未被当前 lock、doctor 或 STATUS 接受 |

现存 `.venv/` 没有被 Phase 00 调用、修改或删除。Phase 01 仍需获得人工确认，依据固定 CPython 3.12 完整补丁号和 hash lock 正式建立或重建环境，并执行 doctor 与负控验收。

## 5. 已回档尝试的本地残留

用户确认：ignored 的旧 `build/phase-00/`、`build/phase-01/` 和 `.venv/` 来自此前运行到 Phase 01 后因问题执行 Git 回档的尝试。

- 旧 `build/phase-00/` 中有 12 个本次证据目录之外的文件。
- `build/phase-01/` 中有 2070 个文件，并含一份旧的 Phase 01 COMPLETE 草稿。
- 仓库中另有 13 个 ignored `.pyc`：4 个 CPython 3.13 历史 cache，以及 9 个与已回档 Phase 01 尝试同批出现的 CPython 3.12 cache；`C_Semantic_Treehouse/manifests/schemas/` 是本地空目录。
- 这些旧证据所声称的 tracked 环境、lock、入口和状态文件在当前 HEAD 中不存在。
- 本次证据写入独立的 `build/phase-00/reconciliation-2026-08-09/`，没有覆盖旧残留。

当前状态只接受本次复核、当前 tracked 源与 `docs/v0.4/STATUS.md` 的已完成历史；`CHECKPOINT.md` 为空闲占位符。旧残留保留作诊断参考，不提供当前 PASS、COMPLETE 或可复现性证明。其后续隔离与环境重建风险见 `P00-R06`、`P00-R07`。

公开/tracked tree 与本 Phase 变更中没有生成 cache 或 log。上述 ignored cache 仍属于本机状态，已在路径审计的 `pre_existing_ignored_cache_or_log_residue` 中逐项登记；Phase 00 依照保护边界保留原状。

## 6. 尚未完成的事项

- 正式 CPython 3.12 环境、仓库 `.venv` 生命周期、bootstrap toolchain、精确 hash lock、`pip check` 和 doctor 尚未验收。
- v0.1–v0.3 尚未在当前正式环境运行无回归验证；本阶段只证明其冻结字节完整。
- D 组 TTL 与说明已完成静态交叉阅读；原样例的历史 PASS/FAIL 说明没有在本阶段重跑 validator。
- v0.4 需求追踪、兼容性决定、模型、fixtures、四状态 harness、suite registry 与报告尚未实现。
- Windows/Linux/Docker 统一入口、固定镜像 digest、CI、clean clone 与发布检查尚未完成。
- GitHub 仓库名称、可见性、账户归属、remote、许可证、材料再分发、ZIP 隐私例外和提交身份公开取舍尚未批准。
- C 组、D 组和发布审批角色的实际可用性尚待项目组确认。

## 7. 历史报告的证据边界

`archive/v0_validation_reports/`、`archive/v0_phase_summaries/`、旧 CI、旧 Docker/Make 入口、旧 Semantic Treehouse 记录和 `prompts/v0/**` 证明 v0 历史内容与历史执行。它们包含已知的版本硬编码、只读 `conforms`、空目标和 OpenAPI fail-open 风险，也没有与当前 lock、HEAD 和环境绑定。

因此，历史 PASS 只作为历史基线与重构参考。当前环境、v0.1–v0.3 无回归、v0.4、CI、clean clone 和发布结论均需由后续 Phase 重新形成证据。
