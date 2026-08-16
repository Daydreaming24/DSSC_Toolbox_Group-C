# v0.4 执行状态

本文件只追加已经完成的 Phase 历史记录。既有小节按只读处理；需要修订时在文件末尾新增恢复/修订小节，并保留原记录。

## Phase 00 — 当前状态复核、范围冻结与执行台账

- 审计日期：2026-08-09
- 结论：`COMPLETE`
- 审计 HEAD：`f98d2dfa645301010a18593bb004b68868933cf7`
- 结论边界：本 Phase 只证明迁移基线和工作边界已经复核；不证明正式环境、v0.1–v0.3 当前无回归、v0.4、CI、clean clone 或发布已完成。

### 进入门槛

| 门槛 | 实际证据 | 退出码 | 结果 |
|---|---|---:|---|
| 项目根与 sentinel | `git rev-parse --show-toplevel` 返回当前根；`scripts/verify_frozen_files.py` 存在 | 0 | PASS |
| 指令与 manifest 可读 | 完整读取 Master、人工介入策略、Phase 00、全部指定权威输入、`prompts/v0/**` 与 frozen manifest | 0 | PASS |
| entry Git 状态 | `git status --short --branch` 输出 `## main`；`git status --short` 无输出 | 0 | PASS |
| 既有改动归属 | entry tracked 工作树/index clean；用户确认 ignored `.venv/` 与旧 `build/phase-00/`、`build/phase-01/` 属已 Git 回档尝试；另识别 13 个 ignored `.pyc` 与一个 Git 不跟踪的空 schemas 目录 | 0 | PASS；所有旧残留保留、逐项登记并与本次证据隔离，`accepted=false` |
| 原生冻结校验 | PowerShell 5.1 原生 SHA-256 合同检查格式、存在性、hash 与非零条目数 | 0 | PASS，104 files |
| 修改重叠 | 本次使用新目录 `build/phase-00/reconciliation-2026-08-09/`；没有覆盖既有 ignored 残留或用户 tracked 文件 | 0 | PASS |

### Phase 00 开始时的 Git 快照

`git status --short --branch` 的完整输出：

```text
## main
```

`git status --short` 的完整输出：

```text
[无输出]
```

`git log --oneline --decorate` 的完整输出：

```text
f98d2df (HEAD -> main) clarify 迁移清单.md as a synced summary, not a competing state source
36bea05 fix cross-reference gaps found in prompts/v0.4 consistency audit
c9181b1 simplify Phase 00-09 prompts to match the lean master-prompt/HIP baseline
897a991 reconcile status docs and simplify v0.4 process prompts
d095bd9 polish prompts
5cbdc8c add prompts
39c3e25 init
```

基线事实：`main`、7 commits、234 tracked files、0 remote、0 tag、dirty=false；根 `.git/` 属于当前非 bare 仓库，无 superproject、submodule 或嵌套 `.git/`。完整 `git ls-files` 输出保存在 `build/phase-00/reconciliation-2026-08-09/entry/git-ls-files.txt`。

### 文件变更

| 路径 | 状态 | 用途 |
|---|---|---|
| `README.md` | 修改 | 同步 Phase 00、7-commit Git 状态、回档残留边界与下一步 |
| `迁移清单.md` | 修改 | 同步已证明迁移状态、环境观察与 Phase 00 工作记录 |
| `docs/environment.md` | 修改 | 分离 2026-08-07 迁移观察和 2026-08-09 本次观察 |
| `docs/v0.4/current-state.md` | 新建 | 仓库、迁移、工具、骨架、未完成项与历史证据边界 |
| `docs/v0.4/scope-and-authority.md` | 新建 | 规范性/解释性/历史/可编辑/临时/发布证据矩阵与 Phase 00 边界 |
| `docs/v0.4/risk-register.md` | 新建 | 带日期的 Phase 00 baseline risk snapshot |
| `docs/v0.4/STATUS.md` | 新建 | 本 Phase 追加式完成记录 |
| `docs/v0.4/CHECKPOINT.md` | 新建 | 执行中记录失败恢复与用户授权；收尾后恢复固定空闲占位符 |
| `build/phase-00/reconciliation-2026-08-09/**` | 新建、ignored | 与旧回档残留隔离的 Git、冻结、输入、路径、机器环境和诊断 incident 证据 |

未修改 provenance manifests、冻结输入、历史模型、prompts、`.gitignore`、`.gitattributes`、根 `scripts/**`、CI、环境/lock、Docker/Make 或生成报告。

### 必需 Git 命令及退出码

下表中的 entry 与 final 命令均从仓库根实际执行。完整 stdout 位于对应 `entry/`、`final/` 文件，命令字符串和退出码位于 `command-ledger-entry.tsv` 与 `command-ledger-final.tsv`。

| 命令 | entry 退出码 | final 退出码 |
|---|---:|---:|
| `git status --short --branch` | 0 | 0 |
| `git rev-parse --show-toplevel` | 0 | 0 |
| `git log --oneline --decorate` | 0 | 0 |
| `git remote -v` | 0 | 0 |
| `git ls-files` | 0 | 0 |
| `git diff --check` | 0 | 0 |
| `git diff --stat` | 0 | 0 |
| `git diff --name-status` | 0 | 0 |
| `git diff --cached --check` | 0 | 0 |
| `git diff --cached --stat` | 0 | 0 |
| `git diff --cached --name-status` | 0 | 0 |
| `git status --short` | 0 | 0 |

### 其他审计命令及退出码

| 命令 | 退出码 | 结果/证据 |
|---|---:|---|
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File build/phase-00/reconciliation-2026-08-09/collect-git-evidence.ps1 -Stage entry -RequireClean` | 0 | 27 条 Git/工具命令及退出码；entry dirty=false |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File build/phase-00/reconciliation-2026-08-09/verify-frozen-native.ps1 -EvidenceFile build/phase-00/reconciliation-2026-08-09/frozen-verification-entry.txt` | 0 | `Frozen-file verification passed: 104 file(s).` |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File build/phase-00/reconciliation-2026-08-09/audit-inputs.ps1` | 0 | frozen、ZIP、11-file original-plan、2-file D 输入、5/6/11 历史模型、7 隐私排除均通过；2 项开放风险被如实保留 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File build/phase-00/reconciliation-2026-08-09/audit-repository-paths.ps1` | 0 | Git 归属、修改范围、ZIP 外文本路径/secret、UTF-16、cache/log、嵌套 `.git` 文件/目录与文本质量通过；13 个 ignored cache 和空目录残留另行登记 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File build/phase-00/reconciliation-2026-08-09/collect-git-evidence.ps1 -Stage final` | 0 | 28 条 Git/工具命令及退出码；final 记录当前 Phase 00 文件状态 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File build/phase-00/reconciliation-2026-08-09/verify-frozen-native.ps1 -EvidenceFile build/phase-00/reconciliation-2026-08-09/frozen-verification-final.txt` | 0 | 最终二次校验：`Frozen-file verification passed: 104 file(s).` |
| `git --version` | 0 | 2.45.1.windows.1 |
| `docker --version` | 0 | client 29.4.1 |
| `docker compose version` | 0 | v5.1.3 |
| `docker info --format '{{.ServerVersion}}'` | 0 | server 29.4.1；本次观察 daemon 可连接 |
| PowerShell `Get-Command` 发现 `python`、`py`、`pwsh`、`make`、`sh` | 0 | `python`/`py` 可发现；其余三项未发现；没有执行 Python |
| `Get-Content -Raw/-Encoding UTF8` 与 `rg --files` 读取权威输入、历史 prompts 和清单 | 0 | 全部指定输入完成读取与交叉核对 |

证据工具开发与独立复核中出现的所有非零或作废诊断均保存在 `diagnostic-incidents.md`，其中列出命令或命令类别、退出码、根因与对应成功重跑。首次直接执行 evidence script 被本机策略拒绝，脚本正文未运行；进程级 `-ExecutionPolicy Bypass` 随后退出 0，系统策略保持不变。其余根因是 PowerShell 5.1 parser/compatibility、审计自扫描误报和编辑文本尾随空格。用户在 2026-08-09 明确接受该最小修复集合并授权最终全量回归；修复只涉及 Phase 00 可写文档和 `build/phase-00/**`，保护路径、冻结输入、Git 历史和外部状态未改变。最终验收只使用成功保存并在全部编辑后重跑的 evidence；失败结果未被晋升为 PASS。

### 迁移与输入复核结果

| 类别 | 结果 |
|---|---|
| frozen manifest | 104 records；0 invalid、duplicate、unsafe、missing、hash mismatch、untracked 或 `text` attribute failure |
| v0 核心 ZIP | 130092 bytes；SHA-256 `44f21783e57966c145c19e4c6edd74405bc1ace8ae2f31fae3f4bb92805d1135`；146 entries |
| 原任务 ZIP | 30411 bytes；SHA-256 `ce13a59d3d3834bdc67d74616421ee9b19d262bfda8c4de69bfc7b5193012241`；38 entries（31 files、7 dirs），其中 19 个 `__MACOSX` 与 1 个 `.DS_Store` 元数据条目按既定规则未迁入 |
| original-plan | map=11、当前文件=11、当前 `TargetSHA256` mismatch=0、当前目录 macOS metadata=0；ZIP 本体与中央目录另行核对 |
| D 组 | received=2；D `SHA256SUMS`、supplemental map、frozen manifest 与实际 hash 一致 |
| 历史模型 | v0.1=5、v0.2=6、v0.3=11；实际集合与 frozen manifest 一致 |
| privacy exclusions | 7 records；present=0、tracked=0 |
| ZIP 外的 tracked/拟公开文本树 | 嵌套 `.git` 文件/目录、macOS metadata、迁移 staging、个人 home 与 current-root 泄漏、高置信 secret、敏感文件名、tracked cache/log 均为 0；两份 ZIP 的字节、路径与中央目录使用输入审计 |
| 回档本机残留 | `.venv/`=3638 files、旧 phase-00=12 files、旧 phase-01=2070 files、ignored `.pyc`=13、空 schemas dir=1；均保留，`accepted_as_current_evidence=false` |
| archive hash 范围 | 61 tracked archive files 中 53 项 hash-bound；8 个只读 wrapper 未绑定，登记 `P00-R15` |

### 验收矩阵

| ID | 验收项 | 状态 | 证据 |
|---|---|---|---|
| P00-A01 | 仓库身份 | PASS | `current-state.md`、`repository-summary-entry.json`、entry ledger |
| P00-A02 | 冻结完整性 | PASS | entry native verification exit 0，checked=104；`input-audit.json` |
| P00-A03 | 迁移边界 | PASS | `scope-and-authority.md` |
| P00-A04 | 状态真实性 | PASS | README、环境说明、迁移清单 diff 与历史/当前观察分离 |
| P00-A05 | 风险完整性 | PASS | `risk-register.md`：P00-R01–P00-R16，含 owner、Phase、发布阻塞性和截止状态 |
| P00-A06 | STATUS/CHECKPOINT 就绪 | PASS | 本小节结论为 COMPLETE；`CHECKPOINT.md` 为 Master 规定的空闲占位符 |
| P00-A07 | 修改范围 | PASS | final unstaged=3 个可写 tracked 文档、staged=0、untracked=5 个可写 v0.4 文档、out-of-scope=0；ignored evidence 位于允许的 `build/phase-00/**` |
| P00-A08 | 内容质量 | PASS | final unstaged/staged `--check` 均退出 0；ZIP 外文本路径/secret、tracked cache/log、尾随空格和 final newline 审计通过；人工 diff 审阅完成，13 个 ignored cache 仅作为已登记残留 |
| P00-A09 | 二次冻结校验 | PASS | 所有编辑完成后的最终原生校验退出 0，checked=104 |

### 证据路径

- `build/phase-00/reconciliation-2026-08-09/README.md`
- `build/phase-00/reconciliation-2026-08-09/command-ledger-entry.tsv`
- `build/phase-00/reconciliation-2026-08-09/command-ledger-final.tsv`
- `build/phase-00/reconciliation-2026-08-09/entry/**`
- `build/phase-00/reconciliation-2026-08-09/final/**`
- `build/phase-00/reconciliation-2026-08-09/repository-summary-entry.json`
- `build/phase-00/reconciliation-2026-08-09/repository-summary-final.json`
- `build/phase-00/reconciliation-2026-08-09/machine-environment.json`
- `build/phase-00/reconciliation-2026-08-09/frozen-verification-entry.txt`
- `build/phase-00/reconciliation-2026-08-09/frozen-verification-final.txt`
- `build/phase-00/reconciliation-2026-08-09/input-audit.json`
- `build/phase-00/reconciliation-2026-08-09/repository-path-audit.json`
- `build/phase-00/reconciliation-2026-08-09/diagnostic-incidents.md`
- `docs/v0.4/current-state.md`
- `docs/v0.4/scope-and-authority.md`
- `docs/v0.4/risk-register.md`

### 剩余风险

Phase 00 的开放风险完整保存在只读快照 `risk-register.md`：

- 发布与权限：`P00-R01`–`P00-R05`、`P00-R14`
- 环境与回档残留：`P00-R06`、`P00-R07`
- 验证器与语义兼容性：`P00-R08`–`P00-R11`
- 可选外部证据与执行连续性：`P00-R12`、`P00-R13`
- provenance 覆盖与文档漂移：`P00-R15`、`P00-R16`

这些风险均不改变 Phase 00 的迁移校验结果；标记“阻塞 GitHub 发布”的风险必须在发布前关闭或取得明确批准。

### Phase 01 进入条件

Phase 01 只能在本小节最终标记 `COMPLETE`、最终 frozen verification 仍为 104/104、`CHECKPOINT.md` 为空闲占位符且用户明确要求执行 Phase 01 后开始。进入包包括：

1. 当前 Windows/X64、PowerShell、Git、Docker 观察与正式环境缺口。
2. `scope-and-authority.md` 的永久保护、Phase 可写和证据晋升边界。
3. 环境风险 `P00-R06`、回档残留风险 `P00-R07` 与会话连续性风险 `P00-R13`。
4. 对首次创建/重建 `.venv`、依赖安装及必要镜像 pull/build 的明确人工授权。
5. 使用准确 CPython 3.12 完整补丁号、由该解释器建立的仓库 `.venv`、固定 bootstrap toolchain、精确含 hash lock 与统一 Python 入口。
6. 已回档尝试残留只作诊断参考；Phase 01 依据当前 tracked 源重新建立并验证，不继承旧 COMPLETE/PASS 草稿或全局包。

最终结论：P00-A01–P00-A09 全部通过，Phase 00 为 `COMPLETE`。本阶段在完成 final diff、范围、内容质量和二次冻结校验后停止；Phase 01 尚未开始，等待用户明确指令。

## Phase 01 — 可复现环境、依赖锁与统一入口

- 执行日期：2026-08-09
- 结论：`COMPLETE`
- 执行 HEAD：`8f8359d0db9b3aedbbc8654c7fdccd8fed6efdfe`（`main`；本 Phase 未 commit、push、tag 或修改 remote）
- 授权：用户明确要求在 Git 回档后完整重做 Phase 01；据此重新建立仓库 `.venv`、从 hash lock 安装并 pull/build 固定 Docker 镜像。现有解释器已满足合同，因此没有执行系统安装器或改变系统配置。
- 结论边界：本 Phase 证明 Windows x64 host 与固定 `linux/amd64` 容器的环境、依赖锁、`frozen`/`environment` suite 和统一 dispatcher 可复现；不宣称原生 Linux/macOS、Phase 02 语义 baseline、v0.4 模型、CI 或发布已经完成。

### 进入门槛与回档残留隔离

| 项目 | 结果 |
|---|---|
| Phase 00 / CHECKPOINT | Phase 00=`COMPLETE`；`CHECKPOINT.md` 始终保持固定空闲占位符 |
| entry Git | tracked/index clean；`git status --short --branch` 仅 `## main` |
| entry 原生冻结 | PowerShell `Get-FileHash` 合同 exit 0，104/104；`build/phase-01/current/entry-gate/entry/frozen-native.txt` |
| host 能力 | CPython 3.12.10 AMD64；Docker client/server 29.4.1；Compose 5.1.3；daemon 可连接 |
| 旧 `.venv` / Phase 01 证据 | 全部恢复性迁入 `build/phase-01/residuals/**`；没有删除或晋升旧 PASS。最终 `.venv` 从缺失状态创建，最终证据只引用 `build/phase-01/current/**` |
| 输出边界 | `.venv/`、`build/`、cache 均 ignored；正式结果只写 `build/phase-01/current`；旧根证据、诊断 venv、失败/中间轮与固定控制目标均隔离在 `residuals/` |

### Python 与供应链合同

选择 `CPython 3.12.10`、64-bit，统一写入 `.python-version`、bootstrap、doctor、lock metadata 和 Dockerfile。该补丁号提供官方 Windows AMD64 安装器，并与固定 Linux 3.12.10 镜像一致。

| 字段 | 实际值 |
|---|---|
| 官方 URL | `https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe` |
| package identity | `python-3.12.10-amd64.exe`，26964224 bytes |
| SHA-256 | `67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb` |
| Authenticode | `Valid`；Signer=`Python Software Foundation`；thumbprint=`DE01DAAE82D04F466A576E178F6B07A839238953` |
| 安装 scope | `CurrentUser`；已安装解释器签名同为 `Valid`；选择入口 `py -3.12` |
| 初始 pip 来源 | CPython 3.12.10 标准库 `ensurepip` bundle，版本 `25.0.1` |
| 最终 pip | host/container 均 `25.0.1`；全部安装调用为选定 Python/venv 的 `-I -m pip --isolated`，`PIP_CONFIG_FILE` 固定为 OS null device |
| 正式证据 | `build/phase-01/current/supply-chain/python-3.12.10-windows.machine.json` |

本次没有重新执行安装器：本机准确解释器、安装器 SHA-256 与 Authenticode、已安装解释器签名和 CurrentUser scope 均已重新核验通过。

### 唯一依赖源与 hash lock

根 `requirements.in` / `requirements.lock` 是 runtime 唯一权威源；`C_Semantic_Treehouse/requirements.txt` 只兼容转发 `-r ../requirements.lock`。runtime input 的六个直接依赖均有仓库 import 证据：`rdflib`、`pyshacl`、`PyLD`、`jsonschema`、`PyYAML`、`openapi-spec-validator`。

| 文件/工具 | 值 |
|---|---|
| `requirements.in` | SHA-256 `1bd0f8c61ca2fcc4155312fb91bb1075d25405c30a931d2c8b141d7d85fe3299` |
| `requirements.lock` | 32 distributions；SHA-256 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2` |
| `requirements-bootstrap.in` | `pip==25.0.1`、`pip-tools==7.4.1`、`setuptools==75.8.2`、`wheel==0.45.1`；SHA-256 `fa4d621be23fe64c1a837eb4cb3c1b5a10d1b0f4549665af0702419f2778144e` |
| `requirements-bootstrap.lock` | 9 distributions，全部含 hashes；SHA-256 `8b94bcc369c574d801a5d0923df54b103efc4dfd1bdadb508846a3cd42a81bff` |
| union installed set | 40 distributions；无 duplicate；确定性指纹 `c5b2597632b0a0572b1b8fad26026b4ddd1b7ab82f2029e991e91ce05db19992` |
| metadata | `requirements.lock.json` SHA-256 `d559849f2dc0c25745a697629acac147aee48e82da78c098cb83f178db17ab42` |
| index | `https://pypi.org/simple` |

lock 生成器固定为 pip-tools 7.4.1，规范化 argv 为 `python -m piptools compile --no-config --resolver=backtracking --generate-hashes --allow-unsafe --strip-extras --newline=lf --index-url https://pypi.org/simple --output-file <LOCK> <INPUT>`。在只由 bootstrap lock 建立的 scratch venv 中对两把 lock 自举重编译，exit 均为 0、前后 bytes/SHA-256 完全一致；证据为 `build/phase-01/current/lock-generation/self-hosted-regeneration.json`。

### Bootstrap 与信任边界

Windows PowerShell 5.1 第一次正式 bootstrap 从 `.venv` 缺失状态创建环境，第二次复用同一环境；两次 exit 0、`pip check` exit 0、40 distributions 指纹一致。最终 trust marker SHA-256 为 `b72641959a60d8019ba42bbe69df65dab505c0be75e21b084d2e3130cb5016f1`。

复用前由选定 base Python 以 `-I -S` 静态校验 marker、base executable、两个 lock、bootstrap/venv-contract 源 hash、完整 venv tree fingerprint、`pyvenv.cfg` 和 launcher。全树无跟随审计拒绝 symlink/junction/reparse/special entry；新建环境在首次 venv Python 启动前拒绝 `.pth`、`sitecustomize` 与 `usercustomize` 启动钩子。pip 使用 `--isolated`、OS null config，并清除 target/prefix/root/user 重定向变量。

正式与安全负控：

- `bootstrap-first.json`：`venv_existed_before=false`、exit 0、40 packages。
- `bootstrap-second.json`：before/after 指纹一致、exit 0。
- 顶层 `.venv` junction、整个/嵌套 site-packages junction、未信任 `.pth` 均在 pip/venv launch 前按精确 issue 非零失败；目标内容未改变，payload 未执行。
- 恶意 `PIP_TARGET` / pip config 未产生任何重定向写入；bootstrap 仍 exit 0。
- 5 项证据位于 `build/phase-01/negative-controls/{bootstrap-venv-junction,bootstrap-internal-site-junction,bootstrap-nested-link,untrusted-pth-preflight,pip-redirect-isolation}.json`，全部 `PASS`。

### Suite registry、统一入口与退出合同

- registry：`contract_version=1.0.0`；SHA-256 `4635b3a06966bec1453357964540af9827a1919de7c11ff84269159347f6cb06`。
- schema：SHA-256 `70d436cd0509da2fcec8b602c1bffc5f00490d24c13c2ee47caf84791199802a`。
- 固定七个公开 suite：`frozen`、`environment` 为 `IMPLEMENTED`；`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all` 为 `NOT_IMPLEMENTED`。
- dispatcher 只从受控 Python catalog 解析逻辑 entrypoint；schema 后再做固定 suite set/order、ownership、依赖、cycle、重复、0 component、entrypoint allowlist 与确定性拓扑展开。
- wrapper 固定 host profile；container profile 需要固定环境 marker、Linux/amd64、64-bit 与 non-root 同时成立。wrapper、bootstrap doctor、Make 和 Docker ENTRYPOINT 均以 Python `-I` 启动。

| 轨道 | suite | 退出码 | 程序状态 | component |
|---|---|---:|---|---:|
| Windows host | `frozen` | 0 | `SUCCESS` | 1 executed / 1 PASS |
| Windows host | `environment` | 0 | `SUCCESS` | 1 executed / 1 PASS |
| Windows host | `baseline` | 1 | `ERROR / NOT_IMPLEMENTED` | 0 discovered / 0 executed |
| Windows host | `traceability` | 1 | `ERROR / NOT_IMPLEMENTED` | 0 / 0 |
| Windows host | `v0.4-model` | 1 | `ERROR / NOT_IMPLEMENTED` | 0 / 0 |
| Windows host | `v0.4` | 1 | `ERROR / NOT_IMPLEMENTED` | 0 / 0 |
| Windows host | `all` | 1 | `ERROR / NOT_IMPLEMENTED` | 0 / 0 |
| Docker container | `frozen` | 0 | `SUCCESS` | 1 executed / 1 PASS |
| Docker container | `environment` | 0 | `SUCCESS` | 1 executed / 1 PASS |
| Docker container | `v0.4` | 1 | `ERROR / NOT_IMPLEMENTED` | 0 / 0 |

registry 负控共 12 项，duplicate suite ID、悬空 dependency、cycle、0 component、unknown/suite-mismatched/duplicate entrypoint、duplicate component、NI component、implemented→NI dependency、shell payload 和 unknown-suite path traversal 均以预期 issue/exit 失败关闭；`build/phase-01/negative-controls/summary.json` 为 12/12 PASS。另有 9 项 profile spoof/mismatch、wrapper profile override、恶意 `PYTHONPATH`、绝对路径 value/key、输出目录和 checker return-contract 负控，`contract-controls-summary.json` 为 9/9 PASS。

路径健壮性 runner 从仓库外 CWD，经含空格与中文的 junction 路径运行 PowerShell 5.1 wrapper；target、非 ASCII、空格、外部 CWD、pip inventory、exit 0 与 frozen 104/104 全部绑定为 PASS。隔离结果与随后标准根结果的 normalized SHA-256 均为 `bdc7d78b7d4b5e051e860ad688575ac43ec24dde164c9b55d249d03ff79fac22`。

### Docker 固定发布环境

| 字段 | 实际值 |
|---|---|
| 完整基础引用 | `python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` |
| OCI index digest | `sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` |
| linux/amd64 child | `sha256:97983fa8cc88343512862c62307159a82261c3528dc025f79e5a3f7af43e50b4` |
| final image | `dssc-c-validation:v0.4-env`；ID `sha256:ad1aa805a398113698a84552f4d51336d8e03f0f3e7f09f6ce483a8a3e6533ae`；linux/amd64 |
| runtime identity | image user `dssc`；Compose effective UID/GID `10001:10001`；ENTRYPOINT=`python -I scripts/validate.py --profile container` |
| Compose | root read-only、network none、`cap_drop=ALL`、no-new-privileges、`/tmp` tmpfs |
| mount | 唯一 bind 为 host `build/phase-01/current/docker` → `/workspace/build/phase-01/current`；无 repo source、`.venv`、Docker socket/engine pipe |

`.dockerignore` 静态核对 104 个 frozen records 无排除项，并保留两个 source ZIP。镜像无任何 host mount、network none、read-only 条件下原生 frozen verifier exit 0、104/104；无 mount environment 也 exit 0。Compose static config 与实际 container inspect 全部通过；container environment 显示 `profile=container`、Linux x86_64/64-bit/effective UID 10001，Git 与 Docker client/server/Compose/daemon 均为 `not_required`，精确安装集合为 40，pip 25.0.1。

完整 Docker summary：`build/phase-01/current/docker/docker-evidence-summary.json`；其 runner SHA-256 为 `72cf16d548bdaf816e1275a211ae643a804d0599ed286c8a83e445872d2d7a97`。registry 请求曾出现瞬时 EOF；固定 digest 未变化，受控重试后 manifest/raw/pull/build 均 exit 0。旧 full-repo mount 镜像与失败/中间 Docker 证据只保存在 `residuals/`，没有用于结论。

### 支持矩阵

| 平台 | 状态 | 证据边界 |
|---|---|---|
| Windows 11 / AMD64 host | `SUPPORTED_AND_TESTED` | PowerShell 5.1 bootstrap 两次、doctor、七 suite、路径与负控均实跑 |
| 固定 Linux / amd64 container | `SUPPORTED_AND_TESTED` | Docker Desktop Linux engine；同 locks、container doctor、frozen/environment、NI suite、无挂载探针实跑 |
| 原生 Linux host | `DOCKER_FALLBACK / UNTESTED_NATIVE` | shell/Make 静态语法通过，未在真实原生 Linux host 运行 bootstrap+doctor+environment |
| macOS / 其他 host | `DOCKER_FALLBACK / UNTESTED_NATIVE` | 只声明固定 `linux/amd64` Docker fallback |

### 确定性证据与实际加载源码 hash

正式 result 与 machine inventory 物理分离：result 不含绝对路径、timestamp、cwd/executable/platform 原始信息；machine sidecar 单向记录 `result_file` 与实际 `result_sha256`。`build/phase-01/current/final-evidence-audit.json` 对 13 份 result 检查结果为：normalized=13/13、source freshness=13/13、sidecar binding=13/13、failure_count=0。

正式 suite/doctor 实际加载或显式要求的全部源 hash：

| 路径 | SHA-256 |
|---|---|
| `Dockerfile.validation` | `1e6cc8673a1e7a8841c8216d524ed218b87655a6ea77a0aff441c5cecdb63502` |
| `scripts/bootstrap.ps1` | `e0d10a0c960fbd9b41a77ecedef20814be438a5f9eec1ea196b287bfaacec300` |
| `scripts/bootstrap.sh` | `0e17e43561a023bdcaa4b557bfab9428038438e98181793e3e7f32461dff532e` |
| `scripts/doctor.py` | `39d3a43249ec3470793577b533516e9b0048ab2503121994834635b49e50143f` |
| `scripts/validate.py` | `41203d51bafae7e25aa9d070161bf76456f6290098a5401cc301a40b28bf39d7` |
| `scripts/verify_frozen_files.py` | `ee8db8d2613821222c307b4983187af5c714f1d8a4fc7cf98658515e9ca8738c` |
| `scripts/dssc_validation/__init__.py` | `8b9374a28d7ec2f7c534bf9f4de5f9d3542333de79939dec97803eb892be70f1` |
| `checks_environment.py` | `d599b590d771d58ed4cef4bf19c2bb2a84e1a6bc23d6082b4c7c62b4355b5444` |
| `checks_frozen.py` | `2e920dd8a67abcbf18089767db1b96a22496f1134eee652a5530b9eccd73ff1d` |
| `doctor_core.py` | `950f10b2bbca66264ccb3d11df7a1f66603ae71d1838a1bde81cea3d9dc93a92` |
| `entrypoint_catalog.py` | `6c1a43688f0c0d519d3b0f6ae9d79815f29c36ce114a523d3f8e0e6ad0343eb8` |
| `evidence.py` | `23e4e1607965557e7a42e7cc63f3a717fc0bdcbc960951a2c035f1b6b2d45b22` |
| `hashing.py` | `7daa83ded49ee3a01e6692d0c0269ea640d27f050d13e1af726eb6976bf11fe3` |
| `lock_contract.py` | `4cfcf85b0d09fd05201358df41faf05c780a743dce5f6ced0080b3784f157d4d` |
| `paths.py` | `ff87298c4b85e62b7c92e314afe5c9de7b3c19dae2bfb85a7d7d9a1f87b40a0c` |
| `profile_contract.py` | `c032d9884b06e3d450105125419c083fd9e42db3d6c73fd5a50007556af834b5` |
| `provenance.py` | `6d816acd3cdc4fdf2603288213a0e6a7118a7c2df1b7ecaa874b1c8920543aef` |
| `suite_registry.py` | `6ea31afe0675dff63c18c7871bb936584807289ce49f1d0f72730eb9d7e73ab0` |
| `venv_contract.py` | `02e3b2cd06bc7df292b73af4e2d20f069d56608304929200de2902e376a94539` |

受控 wrapper 与本 Phase evidence runners：

| 入口/runner | SHA-256 |
|---|---|
| `scripts/validate.ps1` | `fe5041b1dc215a8d717ad98678878dccf4c18064a75f3ec681d47043ee85c4e5` |
| `scripts/validate.sh` | `7b12358f02aad62ce8f29625a81e93b3bbbe013676c7e0f52c5a7dfe28de7bef` |
| `run_bootstrap_evidence.ps1` | `3bcc00c14075b40498bd6c804c4425f8d4ac4432afb192f3f6d61564d48fae75` |
| `installed_inventory.py` | `6af0ad7b155af46ab69acde4c78f8066309c07654c7984cf2b0dbf0132f56442` |
| `run_host_suite_matrix.ps1` | `e3a8cbe4c38805a02ebc72616464e9f3d801c7bf2d2e47a7617f51d50d706167` |
| `run_registry_controls.py` | `1078c8a107aa32e97ec84bb1f3f102d3b294df9d10d7ff89fc7aadc01c1f93fc` |
| `run_phase01_contract_controls.py` | `858449371604dcb3ded0378c003082e55f3013d44e2331a6f28496b084921bf0` |
| `test_path_robustness.ps1` | `0ca8e2f4ea9e8258b51b5ea4ca0bae0954ecb677ca22d6f7301f26926d5db0ed` |
| `run_docker_evidence.ps1` | `72cf16d548bdaf816e1275a211ae643a804d0599ed286c8a83e445872d2d7a97` |
| `audit_final_evidence.py` | `58ce68784df7f37c5832116c4307127af2e6f7842a1addc88825031aa7d44444` |

其余 5 个 venv/pip 边界 runner 的 hashes 完整记录在 `final-evidence-audit.json.tool_hashes`；正式 suite result 自身记录每次实际加载的 15/16 个 Python/helper hashes，doctor result 记录 13 个源 hashes。

### 网络访问与外部状态

- PyPI：`https://pypi.org/simple`，用于 bootstrap-tool/runtime hash lock 生成与 Windows/Docker lock 安装；所有解析 artifact 由 lock SHA-256 校验。
- Docker Hub：官方 `library/python` 固定 digest的 manifest/raw、linux/amd64 pull 与 build；registry 瞬时 EOF 后仅对同一固定引用重试。
- python.org：只记录并重新核验已缓存的官方安装器、SHA-256 与签名；本次未下载安装或执行安装器。
- suite/doctor/container validation 均未访问业务网络；Compose 强制 `network_mode: none`。
- 没有 clone/fetch、外部服务写入、remote/tag/release、Docker daemon socket mount或系统配置改变。

### 必需命令、Git 与冻结收口

| 命令类别 | 退出码/结果 |
|---|---|
| Windows bootstrap first / second | 0 / 0 |
| host doctor (`profile=host`) | 0 / PASS |
| host `frozen` / `environment` | 0 / 0 |
| host 五个 NI suite | 各 1，均 `NOT_IMPLEMENTED` |
| registry / contract controls | runner 0；12/12 与 9/9 PASS |
| venv/pip boundary controls | runner 均 0；内部预期拒绝为非零 |
| path robustness / 标准 frozen 恢复 | 0 / 0 |
| Docker manifest/pull/build/inspect/no-mount frozen | 0；no-mount=104/104 |
| Docker Compose `frozen` / `environment` / `v0.4` | 0 / 0 / 1（NI） |
| final evidence audit | 0；13 results、0 failures |
| `git diff --check` / cached check | `0 / 0` |
| `git diff --stat` / name-status（unstaged + staged） | `全部退出 0；明细已审查` |
| native frozen / `.venv` frozen after STATUS | `0 / 0；104/104` |
| Phase 01 allowlist / protected paths | `PASS；out-of-scope=0，protected diff=0` |

Linux shell 文件已在 index 中登记为 mode `100755`；本 Phase 未暂存其他路径。最终 staged/unstaged 明细与保护范围在本小节写入后重新审计。

### 验收矩阵

| ID | 状态 | 证据摘要 |
|---|---|---|
| P01-A01 | PASS | CPython 3.12.10 x64 在 `.python-version`、host、locks、Docker 一致 |
| P01-A02 | PASS | root input/lock 唯一权威；旧 requirements 只转发 |
| P01-A03 | PASS | runtime 32、bootstrap 9，全部准确 pin+hash；自举重编译 byte-identical |
| P01-A04 | PASS | Windows 从 `.venv` 缺失状态创建；40 packages；pip check=0 |
| P01-A05 | PASS | 第二次 bootstrap 依赖/marker/lock 不漂移 |
| P01-A06 | PASS | 同 locks 在固定 digest linux/amd64 镜像安装；container environment PASS |
| P01-A07 | PASS | host/container `frozen` 与 `environment` 真实执行成功 |
| P01-A08 | PASS | 五个未实现 suite 各自非零、NI、0 discovered/executed |
| P01-A09 | PASS | Windows 核心流为 PowerShell 5.1+Python，不依赖 Make/sh/PowerShell 7 |
| P01-A10 | PASS | 仓库外 CWD、空格、中文 junction 路径实测 |
| P01-A11 | PASS | `.venv`/build/cache ignored，未进入 tracked diff |
| P01-A12 | PASS | entry、host、container、final 原生冻结均 104/104 |
| P01-A13 | PASS | tracked/untracked 修改全部位于 Phase 01 allowlist |
| P01-A14 | PASS | 七 suite、contract 1.0.0、registry/schema hash 固定 |
| P01-A15 | PASS | 12 个 registry 跨记录/路径负控按精确 code 失败关闭 |
| P01-A16 | PASS | 每份 suite 记录 validate/doctor/实际加载 helper hashes；freshness=13/13 |
| P01-A17 | PASS | staged/unstaged check、stat、name-status 与 100755 mode 完成审查 |
| P01-A18 | PASS | host daemon gates PASS；container Docker/Git not_required；无 socket mount |
| P01-A19 | PASS | ensurepip/pip/tool lock 固定；全局 pip 不参与；host/container pip=25.0.1 |
| P01-A20 | PASS | Windows host 与固定 Linux container 实测；其他 host 仅 Docker fallback/UNTESTED |
| P01-A21 | PASS | registry 驱动、受控 catalog、确定性展开与 checker return contract fail-closed |
| P01-A22 | PASS | 官方安装器 identity/hash/Authenticode/scope 与解释器签名完整记录 |

### Phase 00 风险处置

- `P00-R06`：Phase 01 范围内关闭。正式 CPython 3.12.10、repo `.venv`、hash locks、bootstrap、doctor 与双轨证据齐备。
- `P00-R07`：Phase 01 的“隔离重建”义务完成。全部回档残留恢复性隔离，最终环境从缺失状态重建；Phase 09 的 clean-room 发布复核仍按原计划执行。
- `P00-R13`：保持 `CONTROLLED`。本次通过追加式 STATUS、空闲 `CHECKPOINT.md`、current/residual 分离和可重跑 runner 保持会话连续性。
- `P00-R08`：仅 suite registry/dispatcher 层面部分缓解，继续 `OPEN`，按 Phase 02/05 实现和关闭；本 Phase 未宣称语义 baseline 已完成。

不回写 Phase 00 `risk-register.md` 快照。

### 证据路径

- `build/phase-01/current/final-evidence-audit.json`
- `build/phase-01/current/host/bootstrap-{first,second}.{json,log}`
- `build/phase-01/current/doctor-host.{result,machine}.json`
- `build/phase-01/current/suite-*-host.{result,machine}.json`
- `build/phase-01/current/path-robustness/**`
- `build/phase-01/current/docker/docker-evidence-summary.json`
- `build/phase-01/current/docker/suite-*-container.{result,machine}.json`
- `build/phase-01/current/lock-generation/self-hosted-regeneration.json`
- `build/phase-01/current/supply-chain/python-3.12.10-windows.machine.json`
- `build/phase-01/negative-controls/summary.json`
- `build/phase-01/negative-controls/contract-controls-summary.json`
- `build/phase-01/negative-controls/{bootstrap-venv-junction,bootstrap-internal-site-junction,bootstrap-nested-link,untrusted-pth-preflight,pip-redirect-isolation}.json`
- `build/phase-01/residuals/**`（只作残留/失败/中间轮诊断，`accepted_as_current_evidence=false`）

最终结论：P01-A01–P01-A22 全部通过，Phase 01 为 `COMPLETE`。`CHECKPOINT.md` 为空闲占位符；Phase 02 尚未开始。

## Phase 01 恢复/复验记录 — Phase-aware suite evidence 输出

- 恢复日期：2026-08-09
- 结论：`COMPLETE`
- 触发 Phase：Phase 02 入口审计发现通用 dispatcher 和 Docker 把 suite 证据固定写入 `build/phase-01/current`，与后续 Phase 的可写边界冲突。
- 人工授权：用户批准修改通用输出/Docker 合同、使用原固定 base digest 与 locks 重建镜像、重跑 Phase 01 回归、追加本恢复记录，并同步更新相关环境/入口文档。

### 最小恢复集

- `scripts/validate.py`：从固定 suite→owner Phase 映射与 registry 实现状态确定 active suite-evidence Phase；将 `evidence_phase` 和受限 `output_dir` 传入 checker context；owner 错配失败关闭。
- `scripts/dssc_validation/paths.py` / `evidence.py`：新增仅接受 `01..09` 的 Phase-aware 路径/原子 writer，保留 standalone doctor 与 Phase 01 工具的默认 `01` 兼容合同。
- `Dockerfile.validation` / `docker-compose.validation.yml`：保持只读根文件系统、`network_mode: none`、non-root、cap-drop 和无 Docker socket；预建并窄挂载 Phase 01/02 两个 evidence current 目录。
- `README.md`、`docs/environment.md`、`docs/v0.4/reproducibility-contract.md`、`scripts/README.md`：同步 active-Phase suite 输出和两个窄 Docker 挂载合同。

### 恢复验证

| 项目 | 结果 |
|---|---|
| host doctor | exit 0，CPython 3.12.10、pip 25.0.1、lock/pip check/Git/Docker 全部 PASS |
| host `frozen` / `environment` | exit 0 / 0；`frozen`=104/104 |
| host `baseline` | exit 1，`NOT_IMPLEMENTED`；恢复时 registry 仍为 contract `1.0.0` |
| 原 registry / contract 负控 | 12/12 与 9/9 PASS |
| active-phase 新增负控 | canonical Phase 01=`01`；owner=`99`、phase=`99` 均被拒绝；0 implemented 安全回退 `01` |
| Docker rebuild | 使用原 base `python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` 和原 locks；依赖层命中 cache；最终 image ID `sha256:8f333e846c1e68d5ce046ab809b02c68dc7daf8c613694ceb9370842e01e9b07` |
| Docker `frozen` / `environment` | exit 0 / 0；Linux/amd64、non-root；证据 `evidence_phase=01` |
| Compose 边界 | 恰好两个 Phase 01/02 evidence bind；无源码、`.git`、`.venv`、socket/engine-pipe mount |
| lock / 冻结 | lock SHA-256 仍为 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2`；冻结 104/104 |
| Git/diff | `git diff --check` exit 0；保护的冻结 model/query/expected/archive 无改动 |

首次 Docker build 外层命令曾被误设为约 5 秒超时（exit 124）；对同一固定构建给予合理上限后 exit 0，随后两次最终源码重建与 Docker suite 均通过。旧固定 `pythonpath-isolation-final` 诊断目录在重跑前可恢复性迁入 `build/phase-01/residuals/phase02-recovery-2026-08-09/`，没有删除历史内容。

恢复后 Phase 01 的解释器、locks、`frozen`/`environment`、受控 registry、profile 和 Docker 安全边界保持通过。本记录不改写原 Phase 01 小节；Phase 02 可继续实现 baseline。

## Phase 02 — v0.1–v0.3 baseline reproduction（COMPLETE）

- 完成日期：2026-08-09
- 分支 / 执行起点 HEAD：`main` / `957ddef353b673363bc8d4961fd5a38edb107d8f`
- 结论：`COMPLETE`
- 范围：只完成 Phase 02；没有创建 Phase 03 traceability 产物，没有修改冻结 model、SPARQL query/expected TSV、archive、D 组输入或旧历史报告。

Phase 02 入口审计先按人工介入合同进入 `AWAITING_HUMAN_DECISION`：通用 dispatcher、evidence writer 与 Docker 仅允许 Phase 01 输出。用户随后批准方案 1–4、原 digest/locks 镜像重建、Phase 01 回归和恢复记录，并追加批准同步更新四份写死 Phase 01 路径的文档。恢复结果记录在上一小节；本 Phase 的 suite evidence 现由 registry 中最高 `IMPLEMENTED` owner Phase 选择，standalone doctor 继续保持 Phase 01 兼容输出。用户批准 outer suite envelope 保留 component counts，33-case counts 进入 baseline 确定性结果。

### Manifest、schema 与 suite 合同

| 合同 | 状态 / SHA-256 |
|---|---|
| baseline manifest | `C_Semantic_Treehouse/manifests/baseline-test-cases.json`；`e8fb57fe2f609c48c0340cf8e3b78d2e8f81d0fe0fd3ab505468cfe315767e43` |
| baseline schema | Draft 2020-12；`291cb5eae9212735b65fe5bad0bdef383d935b846f5fef07fc8f52c5fc79c6d8` |
| suite registry | `contract_version=1.1.0`；`70e3e0655eebbdc59455b401837fd10e6371092d734b8abbef2401d7bb66d459` |
| suite registry schema | `70d436cd0509da2fcec8b602c1bffc5f00490d24c13c2ee47caf84791199802a` |
| runtime lock | `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2` |

Manifest 固定 33 个 enabled+required cases、37 个受 SHA-256 约束的 artifacts，以及 v0.1/v0.2/v0.3、六个 validator 和完整 case/artifact ID 顺序。schema 校验先于语义校验；语义层拒绝重复 ID、缺失/额外 case、disabled/skipped、悬空或错误 release/validator/artifact/oracle 引用、同路径 hash 冲突、不安全路径、错误 artifact role 和 hash mismatch。所有实际读取的 ontology、shape、context、data、schema、OpenAPI、SPARQL query/expected TSV 与两份 reference 均进入 manifest。

Registry 的 `baseline` 已由 `NOT_IMPLEMENTED` 更新为 `IMPLEMENTED`，依赖 `environment`，只携带受控 `baseline.reproduction -> check_baseline` component。`all` 已记录 baseline 纳入组合，继续保持 `NOT_IMPLEMENTED` 且无 component；`traceability`、`v0.4-model` 与 `v0.4` 同样保持 `NOT_IMPLEMENTED`。

### 33-case 当前结果

Host 与 Docker 的确定性 baseline 结果均为：

| Category | discovered | executed | passed | failed | skipped |
|---|---:|---:|---:|---:|---:|
| RDF | 7 | 7 | 7 | 0 | 0 |
| JSON-LD | 10 | 10 | 10 | 0 | 0 |
| SHACL | 5 | 5 | 5 | 0 | 0 |
| JSON Schema | 2 | 2 | 2 | 0 | 0 |
| OpenAPI | 1 | 1 | 1 | 0 | 0 |
| SPARQL | 8 | 8 | 8 | 0 | 0 |
| **合计** | **33** | **33** | **33** | **0** | **0** |

两项预期业务负例 `shacl-v0-2-metadata-invalid` 与 `jsonschema-v0-3-record-invalid` 的 actual business status 为 `FAIL`，精确命中 oracle 后 actual program status 为 `SUCCESS`；其余 31 项业务状态为 `PASS`。因此 33 项全部属于 harness PASS。

- RDF：7 个 Turtle 文件逐个 parse，并精确断言 30/32/54/62/101/62/40 triples。
- JSON-LD：10 项均通过纯本地 loader 离线展开；4 个 context 得 0 个顶层节点，6 个 example 各得 1；HTTP(S)、未声明 context 与其他 URL scheme 在网络调用前拒绝。
- SHACL：5 项 target activation 均非零；data/shapes/ontology 分图，显式使用 `inference=none`、`advanced=false`、`abort_on_first=false`、`meta_shacl=true`、`allow_warnings=false`、`allow_infos=false`，并禁用 OWL imports。4 个正例 0 `ValidationResult`；v0.2 invalid 精确得到 providerName/temporalEnd/unit 三个 `sh:Violation`。匿名 PropertyShape 规范化为 `{kind, owner_node_shape}`，不比较不稳定 blank-node ID。
- JSON Schema：使用 `Draft7Validator` + `FormatChecker`，正例 0 error；负例精确枚举 required/format/type/enum 四个结构化 error，各 1，无额外 error。
- OpenAPI：实际 import 并执行锁定 `openapi-spec-validator` 的完整验证；缺失/import/验证异常均进入程序 `ERROR`。
- SPARQL：8/8 使用显式 v0.3 ontology + metadata-valid + record-valid 共享图；变量、row count 与排序后 UTF-8 TSV bytes/hash 全部等于冻结 expected，重复行保持，blank node、`SERVICE` 与网络路径被拒绝。

### Host、Docker 与跨环境一致性

| 轨道 | suite | 退出码 / 结果 |
|---|---|---|
| Windows host | `frozen` | 0；104/104 |
| Windows host | `environment` | 0；`SUCCESS` |
| Windows host | `baseline` | 0；outer 2/2 components，nested 33/33 cases |
| Windows host | `traceability` / `v0.4-model` / `v0.4` / `all` | 各 1；`NOT_IMPLEMENTED` |
| Docker linux/amd64 | `frozen` | 0；104/104 |
| Docker linux/amd64 | `environment` | 0；`SUCCESS` |
| Docker linux/amd64 | `baseline` | 0；outer 2/2 components，nested 33/33 cases |
| Docker linux/amd64 | `all` | 1；`NOT_IMPLEMENTED` |

Host result SHA-256 为 `3d7cd75294063d49e5ca307d46fa7170f97509746b04659d054e49df6caab68d`；container result 为 `e0943c148d35f63c99fe18b49a36cdf30e79d0e5c02ba65c7feaedf9fe6865b6`。剔除 profile 后的规范化语义 SHA-256 在两轨均为 `4a7aad0ff7fe0b5bb5767aab94dc5eadc57bbf387e0fb01448950c1bc268dee7`，case IDs、manifest/schema/registry/lock/artifact/source hashes、expected/actual、assertions 与 counts 完全相同，differences 为空。比较证据 SHA-256 为 `ce789f0a0f4b4fccc5e96d026f36654507d36db2c8ff9ba12bd973743ff65c82`。

两轨均使用 CPython 3.12.10、pip 25.0.1、RDFLib 7.6.0、PyLD 2.0.4、pySHACL 0.40.1、jsonschema 4.26.0、PyYAML 6.0.3、openapi-spec-validator 0.9.0。预期机器差异仅在 OS/platform/architecture/path：host 为 Windows AMD64，container 为 Linux amd64。host source state 来自 Git；container 由镜像 build args、ENV 与 OCI label 绑定；两者均记录 commit `957ddef353b673363bc8d4961fd5a38edb107d8f`、dirty=`true`。

固定容器继续使用 base `python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` 和原 locks；最终 image ID/repo digest 为 `sha256:cbd62bff463dbb40fbfc2171eea69d77d426154d3c93dcb00fbc5347a3ebb3d9`。实际 inspect 证明 Linux/amd64、non-root `10001:10001`、read-only root、network none、`cap_drop=ALL`、no-new-privileges、`/tmp` tmpfs，并且恰好只有 Phase 01/02 两个可写 evidence bind；没有源码、`.git`、`.venv`、secret 或 Docker socket/engine pipe mount。

### Fail-closed controls 与确定性

- baseline/schema/runner 负控：37/37 PASS，failed=0、skipped=0；JSON SHA-256 `4e242d820d7108efe5d3a2e188d9d92d30cf0977cf56db14459d63ae7870e12b`。覆盖 prompt 指定的空 manifest、duplicate IDs、悬空/错误 cross-reference、缺 case、hash mismatch、target=0、OpenAPI import 缺失、预期负例额外错误、SHACL config 漂移、无效/合并 Shape graph、PASS/FAIL oracle schema 分支、same-path conflict、不安全路径和 disabled/skipped。
- registry/dispatcher/Docker 合同负控：30/30 PASS，failed=0、skipped=0；JSON SHA-256 `a50bdb3f83c0dff80e47341af8e46c43baeb138ec1e9e044411559265c77eb24`。覆盖 registry 跨记录语义、owner Phase 99/mismatch、active Phase 02、NI owner 07 忽略、路径/link 边界、catalog scope、两个窄挂载与 Docker source provenance。
- 两个 control runner 和各自 JSON 均连续运行两次 byte-identical；正式 host baseline result/Markdown 连续运行 byte-identical；发布器连续运行两次产生相同 comparison/audit/README hashes。
- baseline negative-control runner SHA-256：`11161bb8382d5f5839f7db696327af27d9039ddde0cc5ef0562d2e8f8b44b1da`；Phase 02 contract-control runner：`9b80891b3040c57d701140ce8a427764046b7dfb55e2ca1e92c57b3f9871f12a`。

### Runner、报告器与证据 provenance

| 路径 | SHA-256 |
|---|---|
| `scripts/validate.py` | `cb25014e0bdf27dbf03a0fe070ad4c9287eca8d64475f84198fc7320ba8544bc` |
| `scripts/dssc_validation/paths.py` | `8dd89398afb1547a33603dfe987404784b882107d8fc5bbc55d1a6b0c61a37f5` |
| `scripts/dssc_validation/evidence.py` | `915a4e343d0c815f2b2de32196e810f6109ab163ef9658f2f688702662a17bad` |
| `scripts/dssc_validation/entrypoint_catalog.py` | `a102a5b2ae8509a83fa609dd182c35ad31d25c2f8936d969160851ae3f89e33c` |
| `scripts/dssc_validation/baseline_manifest.py` | `2af85f6324713e8557a538146e188301c183bfea2d0ab9743180fdc27a90c564` |
| `scripts/dssc_validation/baseline_runner.py` | `9aad1e47b14c7dd5bbe5816ba6814ff5b3130a9280ad79850abb213a77ca7673` |
| `scripts/dssc_validation/baseline_report.py` | `0458ba11edba2fff16476f52f0733cdaa9d6067cbb8e1bf913430e37f59503ae` |
| `scripts/dssc_validation/checks_baseline.py` | `977ab6ed8387defba0c48507179527bd321f8c6a4851f50177c5c49a5ec5cdba` |
| `scripts/publish_baseline_evidence.py` | `94cb9191e6682573ca257cb6d8c0ad256335e4559bf6f0f63eecb101a855ec0a` |
| `Dockerfile.validation` | `85d7ffc8e431341d73d62b9805e3446d11bf23e44dc2dc5074779710439c02c4` |
| `docker-compose.validation.yml` | `254087cb113aec1c28bb8d61468140e1ef205093c1a2a84c371d8d680f1affe0` |

正式 baseline result 记录 18 个本次实际加载/显式要求的 `scripts/**` source hashes，host/container 完全一致且 freshness issues 为空；上表列出 Phase 02 核心文件，完整清单保存在两份 result 的 `source_hashes`。result 不含绝对路径、timestamp 或机器环境；独立 environment/machine sidecar 绑定对应 result 文件名与实际 SHA-256。Markdown 由 result JSON 确定性生成并逐字复核。

经审核的发布目录 `C_Semantic_Treehouse/evidence/releases/v0.4/baseline/` 保存 host/container result、Markdown、规范化 comparison、两份 control JSON、Docker identity、安全说明与 release audit。机器绝对路径、raw environment、build/inspect logs 只保存在 ignored `build/phase-02/**`。release audit 为 9/9 core files PASS，SHA-256 `6655d444cc663d9f350718e4cd0cabd63777120a0faedc0bd8b2bdc4b35b69f1`；绝对路径、敏感 token pattern、timestamp、陈旧 hash 与非确定顺序均为 0。

### 历史对照与依赖漂移

历史 archive 继续只作为预期行为与诊断文本对照，当前 PASS 全部由锁定环境重新执行。旧环境没有记录精确解析版本，因此只将文本变化描述为依赖漂移的合理推断。允许差异包括 Markdown 布局、异常类/行列、raw pySHACL result 顺序、blank-node 展示和引号格式；稳定 case/status/hash/oracle 不允许漂移。

与历史脚本相比，当前执行合同显式强化：SHACL 从旧 `inference=rdfs`/`meta_shacl=false` 转为 manifest 固定的 `none`/`true` 并解析 report graph；JSON Schema 从任意首错强化为精确四错；OpenAPI 缺包由旧 fail-open 改为 `ERROR`；JSON-LD 禁止默认网络 loader；RDF/JSON-LD/SPARQL 使用固定完整 case 集。新 SHACL 配置仍得到相同的 4 个正例与 3 个预期 violations；8 个 SPARQL TSV 与历史 frozen oracle 完全一致。完整说明见 `docs/v0.4/baseline-reproduction.md`。

### Phase 00 风险处置

- `P00-R08`：v0.1–v0.3 baseline 部分关闭。统一 manifest/schema、suite registry 和 33-case runner 已防止固定脚本集合漏检；v0.4 组成仍交 Phase 05。
- `P00-R09`：baseline 部分关闭。5 个历史 SHACL case 已证明 target activation、分图、显式配置和结构化 report oracle；D 组 v0.4 SHACL 合同仍交 Phase 05。
- `P00-R10`：baseline 部分关闭。OpenAPI validator 现为锁定且 mandatory，import/完整验证负控失败关闭；v0.4 验证轨仍交 Phase 05。
- `P00-R13`：保持 `CONTROLLED`。本 Phase 的首次通用输出缺陷经 `CHECKPOINT.md` 暂停、人工授权、Phase 01 恢复回归和追加记录后解决；收口时恢复空闲 checkpoint。

不回写 Phase 00 `risk-register.md` 快照。本 Phase没有新增需要交给用户裁决的语义/oracle 风险。

### 验收矩阵

| ID | 状态 | 证据摘要 |
|---|---|---|
| P02-A01 | PASS | Draft 2020-12 schema 自校验；空 cases、绝对路径、未知状态和 SHACL 条件分支均拒绝 |
| P02-A02 | PASS | 37/37 artifacts 存在、普通文件、SHA-256 匹配 |
| P02-A03 | PASS | RDF 7/7、JSON-LD 10/10 离线通过 |
| P02-A04 | PASS | 4 个 SHACL 正例 target 非零、0 results |
| P02-A05 | PASS | v0.2 invalid 精确命中 providerName/unit/temporalEnd 三项 |
| P02-A06 | PASS | JSON Schema 正例通过；负例精确 required/format/type/enum 四错 |
| P02-A07 | PASS | mandatory 完整 OpenAPI validator 实际运行通过 |
| P02-A08 | PASS | SPARQL 8/8 与 expected TSV bytes/hash 一致 |
| P02-A09 | PASS | 33 discovered/executed/passed，0 failed/skipped |
| P02-A10 | PASS | host/container 规范化 semantic hash 相同，differences=0 |
| P02-A11 | PASS | baseline 37 项与合同 30 项 fail-closed controls 全部通过 |
| P02-A12 | PASS | traceability、v0.4-model、v0.4、all 均非零 `NOT_IMPLEMENTED` |
| P02-A13 | PASS | 发布证据 audit 无绝对路径、秘密、timestamp、陈旧 hash和随机顺序 |
| P02-A14 | PASS | 入口与收口 frozen 均 104/104 |
| P02-A15 | PASS | 冻结 model/query/expected/archive/D 组输入无 diff |
| P02-A16 | PASS | duplicate IDs、悬空 cross-reference、same-path conflict 均拒绝 |
| P02-A17 | PASS | baseline IMPLEMENTED、all NI、contract 1.1.0 与 registry hash 已记录 |
| P02-A18 | PASS | dispatcher、runner、报告器和全部实际加载 helper hashes 已记录且两轨一致 |
| P02-A19 | PASS | staged/unstaged check、stat、name-status 与 scope/protected diff 完成审查 |
| P02-A20 | PASS | 每个 SHACL case 显式配置/分图；config、invalid Shape、merge 负控均拒绝 |
| P02-A21 | PASS | PASS/FAIL oracle schema 分支及六个 FAIL 必需字段负控全部通过 |

### 证据路径

- `build/phase-02/current/baseline-host.{result.json,environment.json,md}`
- `build/phase-02/current/docker/baseline-container.{result.json,environment.json,md}`
- `build/phase-02/current/baseline-host-container-comparison.json`
- `build/phase-02/current/negative-controls.json`
- `build/phase-02/current/phase02-contract-controls.json`
- `build/phase-02/current/docker-image.json`
- `build/phase-02/current/suite-*-host.{result,machine.json,md}`
- `build/phase-02/current/docker/suite-*-container.{result,machine.json,md}`
- `build/phase-02/current/docker-*.log` 与 raw inspect/environment 诊断
- `C_Semantic_Treehouse/evidence/releases/v0.4/baseline/`

最终结论：P02-A01–P02-A21 全部通过，Phase 02 为 `COMPLETE`。Phase 03 的进入包为本小节、baseline manifest/schema 及 hashes、registry contract/hash、host/container 等价结果、runner/helper hashes、当前 validator versions、历史差异说明和空闲 `CHECKPOINT.md`。Phase 02 在此停止。

## Phase 01/02 恢复/复验记录 — Phase 01–09 动态 evidence 边界

- 恢复日期：2026-08-10
- 触发 Phase：Phase 03
- 结论：`COMPLETE`
- 人工授权：当前用户批准 evidence 输出随 active Phase 自动演进，并批准修改共享 Docker/基线输出合同、同步说明、按原固定 base digest 与 locks 重建镜像及从最早受影响 Phase 起回归。旧发布 evidence 保持只读。

Phase 03 入口审计确认：registry 激活 owner Phase `03` 后，dispatcher 会把全部 suite evidence 切换到 `build/phase-03/current`；原镜像和 Compose 只提供 Phase 01/02 可写目录，容器的只读根文件系统会阻止 Phase 03 证据落盘。本次恢复把固定计划范围 `01..09` 一次性声明为九个窄 evidence sink，active Phase 继续完全由受控 suite registry 选择。

### 恢复修改与隔离合同

- `Dockerfile.validation` 预建并授权 `/workspace/build/phase-01/current` 至 `/workspace/build/phase-09/current`。
- `docker-compose.validation.yml` 为九个 Phase 分别声明一个 `current/docker` bind；源码、`.git`、`.venv`、secret、Docker socket 和 engine pipe 均不挂载。
- `checks_baseline.py` / `baseline_report.py` 接受 registry 选择的 `02..09` 精确 active-Phase 输出目录；33-case oracle、manifest 和 expected 均保持不变。
- `publish_baseline_evidence.py` 的历史发布输入仍固定为 Phase 02；共享 runtime 安全审计更新为九个精确挂载。既有 release evidence 没有执行或覆盖。
- 根 README、环境文档、复现合同和 scripts README 已同步当前九挂载合同。

固定镜像继续使用 `python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` 和原两份 hash locks；最终 image ID 为 `sha256:94c279517625695724468ee1e53135d0c15ab1e8c9238237cba27c4576118265`。构建参数/labels 绑定 HEAD `d701b5ea19ad254bba448d24e8a6c17f62892059` 与 `dirty=true`。

运行时 inspect 的 16 项断言全部通过：Linux/amd64、image user `dssc`、runtime uid/gid `10001:10001`、只读根、`network_mode=none`、非 privileged、`cap_drop=ALL`、no-new-privileges、仅 `/tmp` tmpfs、恰好九个可写 evidence bind、零禁止挂载、source commit/dirty labels 一致，审计容器 exit 0。host/container 的 `frozen`、`environment`、`baseline` 均返回 0；baseline 仍为 33/33，规范化 semantic hash 在两轨同为 `aefe17f52ea00e40922ae1eb417fd05266dbd38f67a58a39ad5b8a442c1486ca`。

本恢复记录追加于历史 Phase 01/02 之后；原完成小节和 Phase 02 发布 evidence 均保持原字节。

## Phase 03 — D 组契约审计、需求追踪与兼容性决策（COMPLETE）

- 执行日期：2026-08-10（Asia/Shanghai）
- 结论：`COMPLETE`
- 授权边界：当前用户把三类 ADR 审批身份确认为组级可审计身份，批准严格服从 D 组 TTL，并接受 ADR-001/002/003；用户同时批准上一恢复小节的共享合同修改。组级身份为“项目维护方/当前用户”“DSSC Toolbox C 组”“DSSC Toolbox D 组”。
- 范围：冻结 D 组可执行契约的 requirements、追踪、兼容、四状态分类、planned test obligations、三项 ADR 和 traceability suite。v0.4 发布模型、release manifest、fixtures、`v0.4-test-cases.json`、完整四状态 validator、CI 与发布仍留给后续 Phase。

### 权威输入与契约审计

D 组 TTL 是规范性可执行合同，说明文件提供解释和差异发现。traceability evidence 对 D `SHA256SUMS`、Phase 00 frozen manifest 与实际字节执行三方绑定：

| 输入 | SHA-256 | 结果 |
|---|---|---|
| `building-energy-shapes_D.ttl` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` | D checksum / frozen manifest / actual 三方一致 |
| `初始TTL到最终TTL修改说明.md` | `d95a98be50641dbf4c131818547756183bf795edc426668c7c43c00f934bc7b4` | D checksum / frozen manifest / actual 三方一致 |
| D `SHA256SUMS` | `0f1e1535e99c38f86bb5673470d6ceb88bcf98a544a4a28553b7db7cbb3d6caf` | 严格两记录解析通过 |
| frozen manifest | `b30fd69c39deec2c54cdb4bddfb6de7daf38964d56cbd66b4b333e7eae44e310` | 两个 received 原件记录一致 |

Turtle 解析得到 179 triples；Meta-SHACL `conforms=true`、0 result；确定性抽取为 4 个命名 NodeShape、12 个命名 PropertyShape、76 条精确 constraint record、10 类 component 和 2 个 SPARQL constraint。16/16 命名 Shape 的 target kind/predicate/value/owner、path、severity、显式 message、constraint value 与 registry 双向一致。TTL 第 14–18 行的 `PASS → FAIL → INAPPLICABLE → UNTESTABLE` 头部被逐字定位，R016/R017 映射精确绑定。

说明与 TTL 的唯一登记差异为 `D04-I001`：`ex:BuildingEnergyDatasetShape` 没有显式 `sh:message`，NodeShape 级 NodeKind 结果没有 path。`D04-R002` 忠实登记 `messages=[]`、`path=null`，引擎默认文本只作非规范诊断。

原始只读样例 smoke audit 通过：valid 为 13 triples、1 Dataset、0 result，业务 `PASS`；invalid 为 10 triples、1 Dataset、恰好 3 个 Violation，精确命中 `ProviderNameShape/MinCount`、`UnitShape/In`、`TemporalEndShape/MinCount`，业务 `FAIL`。

### Requirements、分类与决策

| 产物 | SHA-256 | 冻结内容 |
|---|---|---|
| `v0.4-requirements.json` | `67391a561c61aa540535463df371e2aa5a0c4f8fff93b45c52a18b0067258ae1` | `D04-R001..R017`、70 planned cases、48 obligations、16 SHACL locators、2 header locators |
| requirements schema | `32a65c25e7a425e8550a17c42ed413c961ac004c3a9778b379bca52cc03d99fb` | Draft 2020-12；路径、状态、source、target、term、正负义务结构门槛 |
| requirements traceability | `34733351a9310b4174f6aa3f9428d24d32128a841f7b479bf9e826d1a31461cc` | 由机器 registry 确定性渲染并逐字检查 |
| compatibility matrix | `46aed6d0a615be0864017b32c0774f6451f7ee7d0a0214ea272f34a7131e3ebd` | v0.3→v0.4 wire-profile breaking migration 与 record 子契约边界 |
| result classification | `423b39e77b9555211cc30f071dbb9d4bc14b27e68daaffc631b1a60e63deb93e` | `UNTESTABLE → FAIL → INAPPLICABLE → PASS` 与独立程序 `ERROR` |
| test plan | `ef4c65dfac849d1f5d4165d0db9300eb6f58fe417d4881fe281a0b665236fe1f` | 70 个 planned case；四状态、单轴变异、受控 fault injection、authority ERROR 边界 |

三份 ADR 均为 `ACCEPTED`，日期 2026-08-10，并分别记录三个组级身份、批准范围和用户决定证据：

- ADR-001（SHA-256 `1f32a23a955cedc4c4b06a10a3ea82efd4ad2be3890562193838ac706b18988a`）：v0.4 Dataset payload 移除 `dct:conformsTo`；版本身份进入 Phase 04 release manifest/provenance；Closed Warning 保持 `INAPPLICABLE` 语义。
- ADR-002（SHA-256 `fcefb0a0aa615cc194d7077b2a20f0dcd62a19d446c163abe8adb8b8d39aa759`）：D `ex:/dcat:/dct:` IRI 是 wire contract；项目 v0.4 version IRI 位于版本身份层。
- ADR-003（SHA-256 `d1bdfe0a533261bcff6bad0306c0436de7c6a415db19decf159dc34993729286`）：只继承五个精确 v0.3 Energy Reading Record artifacts；整个 v0.3 metadata/ontology bundle不声明 wire compatible。

### Suite、负控与执行证据

suite registry 从 contract `1.1.0` 演进到 `1.2.0`，SHA-256 为 `eda7fbf416a287d46a3369606632c55fa6efe6a21e448c272651a54d621781cd`。`traceability` 为 `IMPLEMENTED`，唯一受控 component 是 `traceability.contract-audit/check_traceability`；`all` 继续 `NOT_IMPLEMENTED` 并保持固定六 suite 组成。

requirements checker 同时执行 Draft schema、repo-relative path/hash、稳定 ID、duplicate、双向 cross-reference、source constraint conflict、component/obligation/case coverage及三份 ADR 顶部状态/三组审批表校验。D extractor 进一步执行精确 target provenance、header 与 TTL 双向比较。正式 traceability result 记录 22 个实际加载/显式要求的仓库源码 SHA-256，source issues 为 0。

最终负控连续两轮均 exit 0，22/22 PASS、0 failed/skipped；每个 mutation 都由被测 checker 非零拒绝并命中稳定 code，两份 16,456-byte summary 逐字节一致，SHA-256 `1657a71189a3a19ee8ded2def17440d6d3c7cb046a72ba214afcac2c44248d29`。覆盖 source hash、缺 Shape requirement、重复 requirement/case/obligation、悬空 decision/source/case、空 obligations、未知 business status/severity、未接受 ADR、component/conflicting mapping，以及 suite duplicate/dangling/cycle/0 component/unknown entrypoint/duplicate component/duplicate dependency/shell payload；shell sentinel 未生成。runner SHA-256 为 `d06a32af0034b53ce452ff1637e0e6c6a1cc3ee439aaa67eea2038ce79559613`。

最终命令结果：

| 轨道 | suite/入口 | 退出码与结果 |
|---|---|---|
| host | `frozen` | 0；104/104 |
| host | `environment` | 0；SUCCESS |
| host | `baseline` | 0；33/33 nested cases |
| host | `traceability` | 0；SUCCESS |
| direct | `.venv\Scripts\python.exe scripts\validate.py --suite traceability` | 0；SUCCESS |
| host | `v0.4-model` / `v0.4` / `all` | 各 exit 1；`NOT_IMPLEMENTED` |
| Docker | `frozen` / `environment` / `baseline` / `traceability` | 各 exit 0；SUCCESS |
| Docker | `v0.4` | exit 1；`NOT_IMPLEMENTED` |

本机持久 PowerShell 执行策略会在脚本正文前阻止直接调用 `.ps1`；host 命令沿用 Phase 00/01 已批准的进程级 `-ExecutionPolicy Bypass`，脚本内容和系统策略均未改写。

traceability host/container result SHA-256 分别为 `b0a26c08aa88a1827bebedcfa620fb7571c51197a8ef4bbce443e567083f105f` 与 `96e83d80d77280b41aadaea08d515cbf8ccc4357b2a81c03093c1fe65c99defb`；规范化 semantic hash 在两轨同为 `1818615b4cabb8a75ab134f8ee95b4032fab6168b940266ae0e408e17b2ab07e`，differences=0。

### 风险处置

- `P00-R08`：requirements/suite 组成与 traceability 已有机器真源并 fail closed；完整 v0.4 case manifest/runner 仍由 Phase 05 继续关闭。
- `P00-R09`：本 Phase 已冻结 target activation、report graph 结构断言与四状态 oracle；执行层实现留给 Phase 05。
- `P00-R11`：由 ADR-001 关闭 Phase 03 决策义务；v0.4 payload 遵循 D Closed Shape，版本声明进入 release manifest/provenance。
- `P00-R13`：保持 `CONTROLLED`。本 Phase 对审批和 Docker 上游边界使用 CHECKPOINT 暂停、取得用户决定后恢复，并在收口时恢复空闲占位符。
- `P00-R14`：Phase 03 的 C/D/维护方组级审批可用性和三项决定已解决；Phase 09 的 Release Approver 等发布角色仍按原风险继续跟踪。
- `P00-R15` / `P00-R16`：证据边界与受保护文档未扩张；继续按原计划留给 Phase 05/07/09。

### P03 验收矩阵

| ID | 结果 | 证据摘要 |
|---|---|---|
| P03-A01 | PASS | D checksum、frozen manifest、实际字节三方一致 |
| P03-A02 | PASS | Turtle 179 triples；Meta-SHACL 0 result；抽取两次确定性一致 |
| P03-A03 | PASS | 16/16 named Shapes、76 constraints、10 components、2 SPARQL 与四状态 header 全覆盖 |
| P03-A04 | PASS | R001–R017 各含 source、边界和正负/边界义务 |
| P03-A05 | PASS | 四状态优先级、程序 ERROR、target=0、未知结果行为已冻结 |
| P03-A06 | PASS | type/path/value/strictness 迁移与 record 继承边界完整登记 |
| P03-A07 | PASS | 三 ADR 均含三组身份、日期、范围、结论与用户证据，状态 ACCEPTED |
| P03-A08 | PASS | 70 planned cases、48 obligations；四状态和 authority ERROR 全覆盖 |
| P03-A09 | PASS | source valid PASS/0 result；invalid FAIL/精确 3 Violation |
| P03-A10 | PASS | host/Docker traceability 均 0，规范化 hash 相同 |
| P03-A11 | PASS | 22/22 指定 requirements/suite 负控稳定拒绝，两轮字节一致 |
| P03-A12 | PASS | v0.4-model、v0.4、all 均保持非零 NOT_IMPLEMENTED |
| P03-A13 | PASS | frozen 104/104；environment/baseline 两轨继续通过；baseline 33/33 等价 |
| P03-A14 | PASS | received D 原件、冻结 model、fixtures、baseline manifest/oracle、旧 evidence 无修改；D README 组级责任文字是用户修改；共享 Docker/harness 变更有明确授权 |
| P03-A15 | PASS | duplicate、悬空引用、冲突映射、source/component/case 双向语义均 fail closed |
| P03-A16 | PASS | traceability IMPLEMENTED、all NI、contract 1.2.0 与 registry hash 已记录 |
| P03-A17 | PASS | validate、extractor、checker、reporter 与全部实际加载 helper hashes 已记录且两轨一致 |
| P03-A18 | PASS | staged/unstaged check、stat、name-status、scope/protected diff 完成审查；index 为空 |

### Phase 04 进入包

- requirements manifest/schema 路径与上述 SHA-256；稳定 ID 为 `D04-R001..D04-R017`。
- `source-contract-audit.json`（SHA-256 `7934bd7eb9d4638a54490e47e41a2d1019a5b57063cd58afaaa15cfb19c9edd1`）及 valid/invalid smoke 结果。
- 三份 `ACCEPTED` ADR、compatibility matrix、result-classification 和 planned test obligations。
- suite registry `1.2.0` / SHA-256 `eda7fbf416a287d46a3369606632c55fa6efe6a21e448c272651a54d621781cd`，以及 host/container normalized equality 证据。
- Phase 04 必须从 D wire paths 和 ADR 派生 v0.4 模型/release manifest；正式 fixtures 与 `v0.4-test-cases.json` 继续留给 Phase 05。
- `CHECKPOINT.md` 已恢复空闲占位符。

### 证据路径

- `build/phase-03/current/traceability-host.result.json`
- `build/phase-03/current/docker/traceability-container.result.json`
- `build/phase-03/current/traceability-host-container-comparison.json`
- `build/phase-03/current/source-contract-audit.{json,md}`
- `build/phase-03/current/baseline-host-container-comparison.json`
- `build/phase-03/current/docker-runtime-contract.json`
- `build/phase-03/current/suite-*-host.{result.json,machine.json,md}`
- `build/phase-03/current/docker/suite-*-container.{result.json,machine.json,md}`
- `build/phase-03/negative-controls/summary-final-{3,4}.json`
- `build/phase-03/tools/run_phase03_controls.py`

最终结论：P03-A01–P03-A18 全部通过，Phase 03 为 `COMPLETE`。Phase 03 在最终 frozen、Git staged/unstaged 与保护范围复核后停止；Phase 04 尚未开始。

## Phase 04 — v0.4 派生模型与统一 Release Manifest（COMPLETE）

- 完成日期：2026-08-10（Asia/Shanghai）
- 结论：`COMPLETE`
- 执行 HEAD / source state：`6f993661e7c4d8be6a5d92b933bc366682a13372` / `dirty=true`
- 范围：从冻结 D Shape 和 Phase 03 requirements/ADR 派生 v0.4 metadata 发布模型、统一 v0.1–v0.4 release manifest、`v0.4-model` suite、contract smoke 与发布证据。正式四状态 fixtures、`v0.4-test-cases.json`、完整 `v0.4`/`all` suite、handoff 和发布继续留给后续 Phase。

### 人工介入与授权记录

本 Phase 发生两次稳定、可复现的 Phase 04 内部断点，均依照人工介入策略写入 `CHECKPOINT.md`、取得当前用户明确授权后恢复：

1. 首次 model 预检发现 pySHACL 在 `meta_shacl=true` 时增补调用方 ShapesGraph，以及 RDFLib `Namespace.format` 名称碰撞。用户授权让 pySHACL 使用内部 throwaway ShapesGraph、把 canonical predicate 改为 `dct["format"]`，并同步 `D04-R017` checker hash、requirements hash 与 traceability 文档。修复后原 data/shapes graph 三元组集合保持不变，JSON-LD 13 triples / 1 个 IRI Dataset，contract smoke 6/6 PASS。
2. 发布证据审计连续两次得到逐字节相同的 3 个误报，SHA-256 均为 `f1dabe1f937622a9d68c4683bac17191f897cddc248878f41187be2281222abb`。用户授权把 build-only 临时路径正则收窄为带路径分隔符的 `case-*` segment，并给 Docker audit 补充 `source_state.source=container-image-build-args`。修复后 publish plan 为 `READY`、10 个输入审计、7 个发布候选、0 issue，SHA-256 `20beb8cd3d37a76761df2cc59cbcd55ce8681e6f01317e0da977ec8713b481f3`。

Docker 重建另有明确动作授权：沿用现有 `Dockerfile.validation`、两份 locks 和固定 base digest，以上述 source commit/dirty 构建 `dssc-c-validation:v0.4-env`。新 image ID 为 `sha256:4e19f9cf2962abc51e4c15d345f4244eb8e5f949d52b9a2d1f515d2a3b955fcf`，base digest 为 `sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db`。

### v0.4 模型派生

| 产物 | SHA-256 | 验证结果 |
|---|---|---|
| `model/v0.4/README.md` | `388e4dd823c60b55772946eb7fa37e90c2e5cf52e8300b784bba29ae4364873c` | 权威来源、byte-copy、version/wire namespace、ADR 与 record 继承边界完整 |
| `building-energy-ontology.ttl` | `c2139583d8b2c92fbd805db49f9a30e883c1aea27cb704063c3ea9d0456df5d9` | 32 triples；version/prior/breaking 与五个 D wire local properties 断言通过 |
| `data-product-metadata-shapes.ttl` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` | 10,375 bytes、179 triples，与冻结 D source 字节及 hash 完全一致 |
| `data-product-context.jsonld` | `f46d3056239cc1cb7d678707e749b33e336564e5fce23ffcccd528eae6cbe391` | 本地离线展开，字段与 IRI/date coercion 精确匹配 |
| `data-product-valid.jsonld` | `9acc287ae274e549becd15852231b325c43e1dbddc14e9f2459f4c490420f239` | 13 triples、恰好 1 个 IRI Dataset、canonical graph 精确匹配 |
| `SHA256SUMS` | `66cd79dd5cd05299c6a07010b087b4da87b138045223aa39449548ea7c46484a` | 稳定排序，覆盖五个发布 artifact，不含自身 |

`.gitattributes` SHA-256 为 `9c356619eeaff5c742b21b92fb4d07cbc64441e3d58ff5da034ee38456fc7df1`。目标 Shape 具有唯一精确规则 `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl -text`；`git check-attr` 得到 `text=unset`，byte-copy audit SHA-256 为 `31c79a2aacda3ec982cd662694609dbe286c60ffffe28e42e4df21702cb209fc`。

派生说明 `docs/v0.4/model-derivation.md` SHA-256 为 `3af86aed2945f59f72a3b205a8d2f58391026282879eff34153ac50aef10e926`；兼容说明 `docs/v0.4/compatibility-v0.3-v0.4.md` SHA-256 为 `5d57c914657842f98bb5ab3750acc6dd1c6aede9db4c4b4fb0c8b946a5c544b2`。

### Release manifest、requirements 与 suite 合同

| 合同 | 状态 / SHA-256 |
|---|---|
| release manifest | `7d75676b898fdbc00c9b1da78900054aec5f426690822e07970200b5fd88076a` |
| release manifest schema | Draft 2020-12；`9029520a45dfc9933cbd254d9cbf4c65e7669ecbd0b20cf916c793a09ac695d3` |
| requirements entry hash | `67391a561c61aa540535463df371e2aa5a0c4f8fff93b45c52a18b0067258ae1` |
| requirements final hash | `53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e` |
| requirements schema | `32a65c25e7a425e8550a17c42ed413c961ac004c3a9778b379bca52cc03d99fb` |
| Phase 03 semantic projection | `8a6d4bee6c06623915e4fa2664d465b666e087db9caf0b315ef2f5831bd0e3fe` / 79,254 bytes，前后逐字节一致 |
| requirements traceability | `136bd48ff8851937e1425156b506a9a47f97677fb517ca8ebfef63a413926530` |
| suite registry | `contract_version=1.3.0`；`1ae6361e956c2bf41f86e987caf0879ce4483f76f9f1e042b0442edb3f049829` |
| suite registry schema | `70d436cd0509da2fcec8b602c1bffc5f00490d24c13c2ee47caf84791199802a` |

统一 manifest 含 30 个 artifacts：v0.1/v0.2/v0.3 分别有 4/5/10 个 frozen artifacts，v0.4 为唯一 current release并含 6 个本地派生产物和 5 个继承产物。Draft schema 与跨记录语义审计均为 0 issue；current/prior/source/requirement/validator/inheritance references 全部闭合，历史 artifact hashes 与冻结 manifest 一致。

依据已接受 ADR-003，v0.4 的 Energy Reading Record 继承集恰为五个 `change=none` artifacts：

| 继承 artifact | SHA-256 |
|---|---|
| `energy-reading-record-context.jsonld` | `9727da9b8650dc444d719113a6978a3a26a59bfd1fde011a98e4c1f4b476f748` |
| `energy-reading-record-invalid.jsonld` | `e516f6a8e4ea811170c72e922b86ac7ea46594046704d01a55a2c8e13cd8f358` |
| `energy-reading-record-shapes.ttl` | `84d1eee9cfeecd1791117552611e83d36af7df4f3b4c783ddbd75d45bae66c9a` |
| `energy-reading-record-valid.jsonld` | `8f7509ad08fb9a62cdff1d6c904801c9421c3ce768bdd9ecb651cd480aa158e1` |
| `energy-reading-record.schema.json` | `dd07414e3752bf582bf5e721009064e16d7be3e1e06d60daaad08000869ccfa9` |

v0.3 OpenAPI SHA-256 `d0f52629f625f7b6656854e352be01b9c40b8d2a943dca0423b70cff168a473c` 保持为 v0.3 frozen release artifact；ADR-003 的 v0.4 inherited set 保持上述五项。

R001–R017 的 implementation coverage 为 17/17。`D04-R017` 引用的 `model_contract.py` SHA-256 已同步为 `75e975db21b07fd2efe7210ddee4feb95682ab0821fbaaeaf4e765feda50686c`；`model_validation.py` SHA-256 为 `f454b22c0cdc7c6400a2f13d8ef7d42bc7b04c6d5d6b9c573d87fff489929100`。source semantics、severity、path、message、planned cases、test obligations 和 expected status 均保持 Phase 03 语义。

`v0.4-model` 已登记为 `IMPLEMENTED`；`all` 已纳入该 component并继续为 `NOT_IMPLEMENTED`，公开必需的 `v0.4` 继续为 `NOT_IMPLEMENTED`。

### Contract smoke、Host/Docker 与负控

`v0.4-model` 在 host/container 均得到 11/11 checks、6/6 smoke、0 failed、0 skipped、0 source-hash issue。smoke 结果为：

- canonical valid：业务 `PASS`，target 实际命中，0 Violation、0 Warning；
- frozen source invalid：业务 `FAIL`，恰好 3 个 Violation，精确命中 `D04-R005` / `ProviderNameShape`、`D04-R008` / `UnitShape`、`D04-R012` / `TemporalEndShape`；
- conformsTo control：业务 `INAPPLICABLE`，0 Violation、恰好 1 个 `DatasetClosedShape` Warning；
- 0 Dataset、2 Dataset、temporal reversed controls：各自业务 `FAIL` 并命中对应 SPARQL constraint。

所有 SHACL 调用固定 `advanced=true`、`inference=none`、`meta_shacl=true`、禁用 OWL imports，并对 report graph、target、source shape、severity和结果数执行结构化断言。每项提交 data graph 与 ontology/Shape 保持分图。

| 轨道 | suite/入口 | 退出码与结果 |
|---|---|---|
| host | `frozen` | 0；104/104 |
| host | `environment` | 0；SUCCESS |
| host | `baseline` | 0；33/33 nested cases |
| host | `traceability` | 0；SUCCESS |
| host | `v0.4-model` | 0；11/11 checks、6/6 smoke |
| direct | `.venv\Scripts\python.exe scripts\validate.py --suite v0.4-model` | 0；SUCCESS |
| host | `v0.4` / `all` | 各 exit 1；`NOT_IMPLEMENTED` |
| Docker | `baseline` / `traceability` / `v0.4-model` | 各 exit 0；SUCCESS |
| Docker | `v0.4` | exit 1；`NOT_IMPLEMENTED` |

host result SHA-256 为 `77d062ec2a5e9feb307629deeff23ff52841c12d0f93cf84843d4eae7fbd03a3`；container result 为 `f81b169f32fcb5473ee185e6c1fbd39b7e817ebd9ea115f4aa0caa34c754467c`。两轨规范化 semantic SHA-256 同为 `e25c0511a66f20cda0cc8471c6cc1f53c9fa4597ae141d17254b88ec029a0aaa`，`normalized_equal=true`；comparison SHA-256 为 `5a1cbd23a914463e6d14127a7db96f0dc029431985db43a7716c59d146c06a46`。

Phase 04 负控连续两轮均为 38/38 PASS、0 failed、0 skipped，两份 summary 逐字节一致，SHA-256 均为 `5695a95216b5c896b1cbb110e75eecec604b9377b3c0f0ce11c3ce05e58d1fcb`。覆盖不安全路径、artifact 缺失/空/hash 漂移、D source/byte-copy 改变、历史 frozen/record inheritance 漂移、current release 基数、duplicate IDs、prior/inheritance cycle、各类悬空引用、同路径多 hash、requirements implementation coverage、target=0，以及 suite duplicate/dangling/cycle/0 component/unknown entrypoint/duplicate component/dependency/shell payload。runner SHA-256 为 `0cd8773254f233b1788be1f17caafc2d1e2ba221636ad33bff5a6af302f5529d`。

正式 model result 在两轨记录 27 个实际加载或显式要求的源文件 SHA-256，freshness issue 为 0。核心源包括：

| 路径 | SHA-256 |
|---|---|
| `scripts/validate.py` | `cb25014e0bdf27dbf03a0fe070ad4c9287eca8d64475f84198fc7320ba8544bc` |
| `checks_model.py` | `8245ca66163ffa3311ee1eafbfef2f828726f195891abfd7b9f30e121abee5a8` |
| `model_contract.py` | `75e975db21b07fd2efe7210ddee4feb95682ab0821fbaaeaf4e765feda50686c` |
| `model_validation.py` | `f454b22c0cdc7c6400a2f13d8ef7d42bc7b04c6d5d6b9c573d87fff489929100` |
| `model_report.py` | `1990c1bdc49662daad1b89c65364218c11d59b9ac646bc1a0a1b1ffc5c772f35` |
| `release_manifest.py` | `1969407851cfb24b502236b3308edf795633d73d0a6c3e97b63fe421f7141741` |
| `entrypoint_catalog.py` | `e919ae67a42a53df466447b53d12d8604b92fb78b149471144d1db250800190e` |
| `traceability_report.py` | `f359f4f816aec03ae3a87db62043f28d53b5fb2f9f3b558c88d1fa09b5ff9a18` |
| `hashing.py` | `7daa83ded49ee3a01e6692d0c0269ea640d27f050d13e1af726eb6976bf11fe3` |

### 发布证据

`C_Semantic_Treehouse/evidence/releases/v0.4/model/` 保存两轨确定性 result/Markdown、规范化 comparison、负控、Git attribute audit、README 和 release audit。机器环境 JSON、Docker image audit 与 raw 执行材料留在 ignored `build/phase-04/**`。

`model-release-audit.json` 对 8 个被审计文件得到 8/8 PASS、0 failed；绝对路径、敏感 pattern、timestamp、机器输入发布、陈旧 source hash 和非规范 JSON 均为 0。其 SHA-256 为 `3d92df64fb80b2937e5ac2d475df926980f131967940e0cc71e310c663977d22`；evidence README SHA-256 为 `646e3f9e8c64e763b624e1be81d8a50b0b4a6c9b056c3dba89ab1d5d2e2ba104`。

### 风险处置

- `P00-R08`：统一 release manifest/schema、v0.1–v0.4 artifact 单一真源和 `v0.4-model` suite 已建立；Phase 05 继续用正式 case manifest 和完整 runner 关闭剩余测试组成风险。
- `P00-R09`：本 Phase 的六项 smoke 已执行非零 target、report graph、source shape、severity 与 constraint 命中断言；R001–R017 的完整四状态 oracle 继续由 Phase 05 实现。
- `P00-R10`：v0.3 OpenAPI 继续作为 frozen artifact 受 baseline mandatory validator 保护，baseline 33/33 保持通过；Phase 05 继续验证完整 v0.4 组合的 fail-closed 边界。
- `P00-R11`：Phase 04 实现已落实 ADR-001。canonical payload 不含 `dct:conformsTo`，临时 control 精确得到 ClosedShape Warning / `INAPPLICABLE`，该兼容性风险关闭。
- `P00-R13`：保持 `CONTROLLED`。两次稳定断点均通过 CHECKPOINT、最小复现和明确人工授权恢复；Docker rebuild 也使用独立明确授权。收口后恢复固定空闲占位符。
- `P00-R15`：发布证据清楚区分 hash-bound result 与只留在 `build/**` 的机器输入，没有扩张“104 个 frozen records”的证明范围；继续交 Phase 05/09。
- `P00-R16`：受保护导航/provenance 文档保持原字节，本 Phase 的派生、兼容和 evidence 文档提供当前事实；原风险继续交 Phase 07/09。

### P04 验收矩阵

| ID | 结果 | 证据摘要 |
|---|---|---|
| P04-A01 | PASS | D Shape source/target 均 10,375 bytes、同一 SHA-256；精确 `-text` 与 `text=unset` 已审计 |
| P04-A02 | PASS | ontology 32 triples；version/prior/breaking、精确五个 D local properties 和 namespace 边界通过 |
| P04-A03 | PASS | context 本地离线展开；canonical 为 13 triples、恰好 1 个 IRI Dataset |
| P04-A04 | PASS | release Draft schema 通过；绝对路径、逃逸、空/重复 release、未知 origin 等负控被拒绝 |
| P04-A05 | PASS | v0.1–v0.3 共 19 个 frozen artifacts 与 baseline/frozen hashes 一致 |
| P04-A06 | PASS | v0.4 是唯一 current；6 个派生和 5 个继承 artifact、source、requirements 引用均存在且 hash 匹配 |
| P04-A07 | PASS | ADR-003 五个 record artifacts 均可解析、hash 与 v0.3 一致、`change=none` |
| P04-A08 | PASS | R001–R017 implementation coverage=17/17；Phase 03 semantic projection 逐字节不变 |
| P04-A09 | PASS | canonical valid target 非零，0 Violation、0 Warning |
| P04-A10 | PASS | source invalid 精确得到 R005/R008/R012 三个 Violation |
| P04-A11 | PASS | conformsTo control 仅得到 ClosedShape Warning，业务状态 `INAPPLICABLE` |
| P04-A12 | PASS | host/container `v0.4-model` 均 exit 0；规范化 hash 相同 |
| P04-A13 | PASS | 38/38 指定负控连续两轮稳定失败关闭，summary byte-identical |
| P04-A14 | PASS | host `v0.4`/`all` 与 Docker `v0.4` 均为非零 `NOT_IMPLEMENTED` |
| P04-A15 | PASS | host frozen/environment/baseline/traceability 全部通过；Docker baseline/traceability 通过；最终 frozen 104/104 |
| P04-A16 | PASS | 未创建 fixtures 或 test-case manifest；D input、历史模型、baseline evidence 与保护路径无修改 |
| P04-A17 | PASS | duplicate IDs、悬空 cross-reference、prior/inheritance cycle、同路径多 hash 均被稳定拒绝 |
| P04-A18 | PASS | `v0.4-model=IMPLEMENTED`、`all=NOT_IMPLEMENTED`、contract 1.3.0 与 registry hash 已记录 |
| P04-A19 | PASS | validate、release/model checker 与 27 个实际加载/必需 helper hashes 已记录，两轨 source issues=0 |
| P04-A20 | PASS | staged/unstaged check、stat、name-status、untracked allowlist 与 protected diff 全部完成审查，index 为空且无越界 |

### Phase 05 进入包

- release manifest/schema 路径与 SHA-256；
- v0.4 `SHA256SUMS`、D Shape byte-copy 和 Git attribute audit；
- requirements final hash、entry hash及语义投影不变证明；
- canonical valid、source invalid、conformsTo、0/2 Dataset 和 temporal reversed 的 report graph 断言；
- ADR-003 五项 record inheritance 清单；
- suite contract `1.3.0`、registry hash、38/38 manifest/requirements/suite/model 负控和 27 个 runner/helper source hashes；
- Phase 03 的 70 个 planned cases与 48 个 test obligations；
- `CHECKPOINT.md` 已恢复空闲占位符。

Phase 05 应从 release manifest 和 requirements registry 加载 artifact、规则与 oracle，并创建 `fixtures/v0.4/**`、`C_Semantic_Treehouse/manifests/v0.4-test-cases.json` 和完整 `v0.4` suite；当前 Phase 不提前创建这些产物，也不使 `v0.4` 或 `all` 返回 0。

### 证据路径

- `C_Semantic_Treehouse/evidence/releases/v0.4/model/`
- `build/phase-04/current/v0.4-model-host.{result.json,environment.json,md}`
- `build/phase-04/current/docker/v0.4-model-container.{result.json,environment.json,md}`
- `build/phase-04/current/v0.4-model-host-container-comparison.json`
- `build/phase-04/current/git-attribute-audit.json`
- `build/phase-04/current/docker-image-audit.json`
- `build/phase-04/current/publish-plan.json`
- `build/phase-04/negative-controls/summary-run-{1,2}.json`
- `build/phase-04/negative-controls/run_phase04_controls.py`

最终结论：P04-A01–P04-A20 全部通过，Phase 04 为 `COMPLETE`。在最终 frozen、Git staged/unstaged/范围审计和空闲 CHECKPOINT 确认后停止；Phase 05 尚未开始。

## Phase 01 恢复/复验记录 — `all` Phase 05 owner 与受控入口接线（COMPLETE）

- 恢复日期：2026-08-10（Asia/Shanghai）
- 触发 Phase：Phase 05
- 结论：`COMPLETE`
- 人工授权：用户明确授权仅把 `scripts/validate.py` 的 `_FIXED_SUITE_OWNER_PHASE["all"]` 从 `"07"` 改为 `"05"`，并在 registry 同步 `all.owner_phase="05"`；随后又具名授权 `scripts/dssc_validation/entrypoint_catalog.py` 仅新增八个受控 v0.4/all 入口及 v0.4 延迟加载 helper。

### 最小恢复集

- `scripts/validate.py` 仅有上述一行 owner 映射变化；dispatcher 的 suite 展开、证据路由、退出码、registry 校验和 component 调用逻辑保持原样。
- `scripts/dssc_validation/entrypoint_catalog.py` 仅新增七个 v0.4 entrypoint、一个 `all` composition entrypoint及局部 `_lazy_v04` helper；既有五个 entrypoint、suite allowlist 与 resolve 行为保持原样。最终 SHA-256 为 `da2ab1dc199237e1dc6c5ffad3f087a0c368dfc377b24d0567bfa404c87aaf84`。
- 延迟加载确保 Phase 01–04 suite 在 catalog/registry import 阶段不加载 `checks_v04`；fresh interpreter 的 catalog→registry、checks_v04→catalog→registry、registry→checks_v04 三种顺序均无循环依赖。

### 恢复验证

| 项目 | 结果 |
|---|---|
| Python 编译 | validate、catalog、checks_all、checks_v04 与全部 v04 helper：exit 0 |
| catalog/registry fresh import | 13 个受控入口；v0.4 延迟加载成立；registry schema/semantic 0 issue |
| `frozen` | exit 0；104/104 |
| `environment` | exit 0；SUCCESS |
| 下游 Phase 02–05 | baseline、traceability、v0.4-model、v0.4、all 均 exit 0 |
| staged/unstaged | `diff --check` 均 exit 0；index 为空 |

Phase 01 原 `COMPLETE` 小节未改写，系统 PowerShell policy、平台包装、doctor 与其他 dispatcher 文件均保持原字节。该恢复仅使 Phase 05 首次启用的 `all` 把临时证据写入 `build/phase-05/**`。

## Phase 04 恢复/复验记录 — validation suite registry 1.4.0 绑定（COMPLETE）

- 恢复日期：2026-08-10（Asia/Shanghai）
- 触发 Phase：Phase 05
- 结论：`COMPLETE`
- 人工授权：用户明确授权在 Phase 05 registry 定稿后，仅同步修改 `release-manifest.json.validationSuiteRegistry.sha256` 与 `.contractVersion` 两个字段，并从 Phase 04 重新验收。

### 最小恢复集

| 绑定 | 原值 | 恢复后值 |
|---|---|---|
| registry SHA-256 | `1ae6361e956c2bf41f86e987caf0879ce4483f76f9f1e042b0442edb3f049829` | `f9f0493603e858de2806ae54f11d9687c21e40626e511315be4ece5517d987b7` |
| contract version | `1.3.0` | `1.4.0` |

`release-manifest.json` 的其余字段保持原样；恢复后文件 SHA-256 为 `91070e1ea8d40b982e0dce12855c195d62c90d426f16b759777e24a4520e2e6a`，schema SHA-256 仍为 `9029520a45dfc9933cbd254d9cbf4c65e7669ecbd0b20cf916c793a09ac695d3`。release schema、跨记录 path/hash、唯一 current release、历史 frozen artifacts、ADR-003 五项继承与 registry contract 绑定由 `v0.4-model` 实际复验，exit 0；随后 v0.4/all 均 exit 0。

Phase 04 原 `COMPLETE` 小节及发布 evidence 未改写。此追加记录是当前 registry 1.4.0 绑定的恢复真源。

## Phase 05 — 四状态 Fixtures 与 Fail-Closed 验证 Harness（COMPLETE）

- 完成日期：2026-08-10（Asia/Shanghai）
- 结论：`COMPLETE`
- 执行 HEAD / source state：`e369c35d2977b121e622c66b28cb8630d121378d` / `dirty=true`
- 范围：v0.4 test-case manifest/schema、D04-PC001–D04-PC066 独立 fixtures、四状态 classifier、SHACL report graph 断言、target activation、fail-closed harness、确定性报告、registry 1.4.0、v0.4/all 受控入口及 Phase 01/04 最小恢复。Phase 06 的 SPARQL/quality/governance 内部 checks 尚未开始。

### 进入门槛与人工介入

Phase 00–04 的 `COMPLETE` 记录、Phase 04 release/model/compatibility 证据、D Shape SHA-256 `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`、release/requirements schema 与跨记录引用均在实施前核验。初始 frozen、environment、baseline、traceability、v0.4-model 均 exit 0；进入时 HEAD 为上述 commit、工作树 clean，lock SHA-256 为 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2`。

本 Phase 的三组保护边界均通过 `CHECKPOINT.md` 暂停、根因诊断和当前用户具名授权恢复：

1. Phase 05 registry 状态/组成变化必然使 Phase 04 release binding 陈旧；授权只同步 release manifest 的两个 registry 绑定字段。
2. `all=IMPLEMENTED` 若仍由 Phase 07 owner 路由会写入后续 Phase 路径；授权只修改 validate 的一行 owner 映射，并同步 registry owner。
3. 静态 entrypoint catalog 需要认识 v0.4/all components；授权只新增八个受控映射、v0.4 延迟加载 helper 和仅检查 composition 的 `checks_all.py`。

实施中曾向历史 hash-bound `C_Semantic_Treehouse/validation/expected-results.md` 增加 v0.4 说明，`v0.4-model` 随即以 baseline artifact hash mismatch 非零拒绝。该本轮新增段落被精确撤回，文件恢复原 SHA-256 `f8865dc12d4c511e074de87f2bdfbdab5954a9a1be734bd75a66523642eb862d` 且当前无 diff；随后 `v0.4-model` exit 0。失败证明确认保护绑定会 fail closed，历史 oracle 未被改写。

### Manifest、fixtures 与引擎合同

| 真源 | SHA-256 / 结果 |
|---|---|
| `v0.4-test-cases.json` | `87e367ea285ddc7feb5fa7f3f4b6c0035be0b768de5e56398ac422abaf494e5a`；66 cases |
| test-case schema | `267a3786fe4e6c246a8318e5ba1c124a2319cb40e772db3f9332b18daac4d571`；Draft 2020-12 四状态互斥分支 |
| v0.4 requirements | `53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e`；D04-R001–D04-R017 全覆盖 |
| release manifest | `91070e1ea8d40b982e0dce12855c195d62c90d426f16b759777e24a4520e2e6a` |
| suite registry | `contract_version=1.4.0`；`f9f0493603e858de2806ae54f11d9687c21e40626e511315be4ece5517d987b7` |
| fixture matrix | `779c42faa2a3945281bd12011672fe8b9db8fb928c32ca0b75e9d6b6e64c4074` |

66 个 case 各有独立 manifest 记录、fixture assertion ID、仓库相对路径、格式和实际字节 SHA-256：PASS 6、FAIL 53、INAPPLICABLE 1、UNTESTABLE 6。canonical PASS 只包含必填字段；其余业务 fixtures覆盖合法可选字段、相等时间边界、0/2/blank-node Dataset、字符串/枚举/endpoint/temporal/optional 字段边界、Closed Warning + Violation 优先级，以及 SUT parse/offline-load 与预检后的 timeout/crash/service-runtime 注入。HTTP context fetch 被离线 loader 拒绝，每个 fixture 单独形成 data graph。

引擎固定 pySHACL `0.40.1`、RDFLib `7.6.0`、`advanced=true`、`inference=none`、`abort_on_first=false`、`meta_shacl=true`、`allow_warnings=false`、`allow_infos=false`、`do_owl_imports=false`。每次 suite 都核对 release/D/派生 Shape 三方 hash、重新解析 Shape graph，并在执行任何 SUT 前完成 authority、manifest、dependency、registry 与 fixture byte preflight。

### Harness、report 与负控结果

- canonical run：66 discovered / 66 executed / 66 passed / 0 failed / 0 skipped；业务分布 PASS 6、FAIL 53、INAPPLICABLE 1、UNTESTABLE 6。
- 60 个可形成 report 的 case 完成 467 条 oracle 断言并规范化 65 个 results；逐项提取 focus node、path、source shape、constraint component、severity、message 与 value，全部映射 requirement ID。PC059 仅 ClosedShape Warning→INAPPLICABLE；PC060 Warning+Violation→FAIL。
- target activation 对 60 个 report case 均非零；PASS case 恰有一个 Dataset。D04-PC002、PC003、PC049 分别实际命中 cardinality 0/2 Dataset 与 temporal-order 三个 SPARQL 控制。
- 34/34 manifest/schema/semantic/registry controls 通过，覆盖状态分支、duplicate IDs、悬空引用、hash 漂移、同路径多 hash、failure-stage/reason、registry duplicate/dependency/cycle/0 component/unknown entrypoint/duplicate component/shell payload及 all 展开不完整。
- 13/13 runtime/report controls 通过，覆盖 unknown severity/source、不可解析 report、conforms/result 冲突、Warning+Violation 优先级、0 discovery、缺必需 case、发现非零但执行为 0、必需 case skipped、Shape/核心依赖/harness preflight 故障和 allowlisted fault 在预检未完成时必须 ERROR。
- 6/6 failure-boundary controls 通过；D04-PC067–D04-PC070 均为 `program_status=ERROR`、无业务状态，`planned_case_coverage.pending=[]`。意外 validator runtime 与 PC064 在 authority preflight 未完成时同样保持 ERROR。
- aggregate verdict 由生产核心和负控共享同一 fail-closed 函数；`ZERO_EXECUTED` 与 `REQUIRED_TEST_SKIPPED` 注入均得到 `ERROR/exit 1`。
- canonical core 连续两次均为 379,937 bytes、SHA-256 `53837ff5cde56dec35dc41cd9622554faccf5b0c8208f778affa3be9b0e706cd`，逐字节一致；独立 environment sidecar 排除在确定性比较外。
- v0.4 registry 有七个 Phase 05 components；带依赖展开为 10 components。`all` 精确按 frozen、environment、baseline、traceability、v0.4-model、v0.4、all.composition 顺序展开 13 components，全部 PASS，未加入 Phase 06 内部 checks。

### 正式命令与退出码

Windows host 使用 Phase 00/01 已批准的进程级执行策略参数；包装脚本选择仓库 `.venv` 并调用唯一 `scripts/validate.py` Python 编排核心，系统 policy 与包装正文保持原样。

| 命令 | 结果 |
|---|---|
| `git status --short --branch` | exit 0；`## main`，改动归属已审计 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Suite frozen` | exit 0；104/104；收尾再次 exit 0 |
| 同入口 `-Suite environment` | exit 0；SUCCESS |
| 同入口 `-Suite baseline` | exit 0；SUCCESS |
| 同入口 `-Suite traceability` | exit 0；SUCCESS |
| 同入口 `-Suite v0.4-model` | exit 0；SUCCESS |
| 同入口 `-Suite v0.4` | exit 0；10/10 components；canonical evidence refresh 再次 exit 0 |
| 同入口 `-Suite all` | exit 0；13/13 components；内含 frozen 104/104 |
| `.venv\Scripts\python.exe -m py_compile <validate/catalog/checks_v04/checks_all/v04 helpers>` | exit 0 |
| aggregate `ZERO_EXECUTED` / `REQUIRED_TEST_SKIPPED` 直接注入 | exit 0；两项均裁决 `ERROR/1` |
| results source/manifest/fixture/input freshness audit | exit 0；114 bindings checked，0 mismatch |
| `git diff --check` / `--stat` / `--name-status` | 各 exit 0；范围已阅读 |
| 三项对应 `git diff --cached ...` | 各 exit 0；index 为空 |
| `git status --short` | exit 0；82 个 tracked/untracked entries，均归属本 Phase 或三项具名恢复 |

RDFLib 会对设计用于错误 datatype 的 fixture 词法值 `not-a-date-time` 输出非致命转换 traceback；相应负例仍由结构化 oracle 判断，suite machine result 与退出码均为 SUCCESS/0。

### 机器证据与 source provenance

| 证据 | SHA-256 |
|---|---|
| `build/validation/v0.4/results.json` | `53837ff5cde56dec35dc41cd9622554faccf5b0c8208f778affa3be9b0e706cd` |
| `build/validation/v0.4/report.md` | `e83f1fdcbf0db7b8d473982b34dc09e8b04ae11f62a41949197f5ff9ea89dad4` |
| `build/validation/v0.4/run-environment.json` | `790530f0d2bb6e6fa65ee46c0603a126533fe0ea9f59235794f83430c1bf6fa5` |
| `build/phase-05/manifest-validation.json` | `f8e5eac30c37bce46f085aee90c638bbb2fb524b79cf025205a1c39f3d7a82` |
| `build/phase-05/negative-controls.json` | `9fe1299c1664d65f0b9477629c0207337caecee2164eca8f624af717fd8c45ce` |
| `build/phase-05/determinism.json` | `cf784e4bd67891b668cc3853e2fd8cd481c982f0e508ff34ed882ae981359c17` |
| `suite-v0.4-host.result.json` | `b189e9847675f65ab9309e0ca0b2d9830500a26ac9012b032b541b85c5c5c675` |
| `suite-all-host.result.json` | `0692ded7512920659c8263a7159db0c3b34288a339f11c943390e8e50ed84a8a` |

`results.json` 记录 35 个实际加载/显式必需 source hashes、8 个 consumed manifest hashes、66 个 fixture hashes、2 个 Shape input hashes，`source_hash_issues=[]`。核心 source 如下；完整集合以该 JSON 为准：

| 路径 | SHA-256 |
|---|---|
| `scripts/validate.py` | `0ead93869a34eacc497412679a2fb4365f2743a2fbbc24e61283c3a5fa9b497f` |
| `entrypoint_catalog.py` | `da2ab1dc199237e1dc6c5ffad3f087a0c368dfc377b24d0567bfa404c87aaf84` |
| `checks_all.py` | `8f8e606c0382905f35c95c33cd5c381d425176e8a99167cdacd1c34c1e67b012` |
| `checks_v04.py` | `dfb0e7244179db957eb4e3fedbbf79b2e02716fe18196b513724c9e1bd157302` |
| `v04_classifier.py` | `166dacd3fb078bd4cd2bb88dc02e9def3276a6113a6fa355317623874d538bcd` |
| `v04_controls.py` | `5dca90834bc813009d2025eaf9c4b3d31e1ec47151b14c6a6dab0b84b8c65f75` |
| `v04_harness.py` | `b05bcca7edc65ad9004e097bacc2c4e41ef318c4409bde39ebc22b2dbcd507ae` |
| `v04_manifest.py` | `f94ffa122f44e6d9454baef980beaf4ae2c44d0718732914842d2499c7162845` |
| `v04_report.py` | `400dfeed74c0c2200e2123aaa18fff4c0237a06f6b5bcf5b87e693e0a1f0ba69` |
| `v04_reporter.py` | `e3630c2d03685e78ae67a738999ced2104210c5709c440b41d3f84036adb0743` |

### 风险处置

- `P00-R08`：正式 test manifest/schema、registry 1.4.0、v0.4/all IMPLEMENTED 与确定性六-suite 展开已形成单一真源；本 Phase 关闭。
- `P00-R09`：66/66 cases、非零 target、完整 report graph oracle、0 Dataset、PC059/PC060 与 unknown-report 负控均已实际执行；本 Phase 关闭。
- `P00-R10`：Phase 02 mandatory OpenAPI 继续由 all 回归；Phase 05 的 pySHACL/core-dependency preflight 和缺依赖负控稳定 ERROR；本 Phase 关闭。
- `P00-R11`：保持关闭，ADR-001 由 PC059=INAPPLICABLE 与 PC060=FAIL 再确认。
- `P00-R13`：保持 `CONTROLLED`；三次边界暂停、具名用户决定、顺序恢复和本追加记录均可追溯，收口后 CHECKPOINT 恢复空闲占位符。
- `P00-R14`：Phase 05 所需保护文件授权已具名取得；Phase 09 Release Approver 义务继续 OPEN。
- `P00-R15`：104 frozen 的证明边界未扩张；保持 OPEN 至 Phase 09。
- `P00-R16`：受保护导航/provenance 原文保持不变；当前机器真源已明确，继续交 Phase 07/09 同步。

以上处置不回写 Phase 00 `risk-register.md` baseline snapshot；后续 Phase 09 在新增风险汇总中消费本节。

### P05 验收矩阵

| ID | 结果 | 证据摘要 |
|---|---|---|
| P05-A01 | PASS | test manifest/schema 有效；66 paths/IDs/hashes 可解析 |
| P05-A02 | PASS | PASS、FAIL/INAPPLICABLE、UNTESTABLE oracle 分支互斥；schema mutation 非零拒绝 |
| P05-A03 | PASS | duplicate、悬空 cross-reference、同路径多 hash、fixture 漂移均被语义负控拒绝 |
| P05-A04 | PASS | D04-R001–D04-R017 均关联实际执行 case，missing=[] |
| P05-A05 | PASS | 四状态实际分布 6/53/1/6，66/66 SUCCESS |
| P05-A06 | PASS | 467 条 Shape/path/severity/component/message/count oracle 断言全部通过 |
| P05-A07 | PASS | PC060 的 Warning+Violation 稳定裁决 FAIL |
| P05-A08 | PASS | PC059 仅 ClosedShape Warning，稳定裁决 INAPPLICABLE |
| P05-A09 | PASS | parse/offline-load 与预检后 timeout/crash/service fault 均为受控 UNTESTABLE；authority/harness 故障保持 ERROR |
| P05-A10 | PASS | 60 个 report case target 非零；0/2 Dataset 与 temporal SPARQL 实际命中 |
| P05-A11 | PASS | 0 discovery、缺必需 case、0 executed、required skipped 均非零裁决 |
| P05-A12 | PASS | 两次规范化 core JSON 字节一致 |
| P05-A13 | PASS | baseline、v0.4-model、v0.4、all 均 exit 0 |
| P05-A14 | PASS | Phase 前后及 all 内 frozen 均 104/104 |
| P05-A15 | PASS | v0.4/all IMPLEMENTED；contract 1.4.0；all 精确展开 13 components |
| P05-A16 | PASS | validate/classifier/parser/semantic checker/reporter 及全部加载 helper hashes 已记录，0 freshness issue |
| P05-A17 | PASS | 34+13+6 负控 53/53 PASS，0 failed/skipped，PC067–PC070 pending=[] |
| P05-A18 | PASS | staged/unstaged diff、stat、name-status、保护范围和82项工作树归属完成审查；index 为空 |

### Phase 06 进入包

- release manifest `91070e1ea8d40b982e0dce12855c195d62c90d426f16b759777e24a4520e2e6a`；v0.4 requirements `53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e`；test cases `87e367ea285ddc7feb5fa7f3f4b6c0035be0b768de5e56398ac422abaf494e5a`。
- suite registry `1.4.0` / `f9f0493603e858de2806ae54f11d9687c21e40626e511315be4ece5517d987b7`；normalized result `53837ff5cde56dec35dc41cd9622554faccf5b0c8208f778affa3be9b0e706cd`；完整 runner/helper hashes 位于 `results.json/source_hashes`。
- ADR-001 `1f32a23a955cedc4c4b06a10a3ea82efd4ad2be3890562193838ac706b18988a`、ADR-002 `fcefb0a0aa615cc194d7077b2a20f0dcd62a19d446c163abe8adb8b8d39aa759`、ADR-003 `d1bdfe0a533261bcff6bad0306c0436de7c6a415db19decf159dc34993729286` 继续为兼容性/版本/继承真源。
- ADR-003 的五项 v0.3 `change=none` 继承保持精确：record schema `dd07414e3752bf582bf5e721009064e16d7be3e1e06d60daaad08000869ccfa9`、context `9727da9b8650dc444d719113a6978a3a26a59bfd1fde011a98e4c1f4b476f748`、shapes `84d1eee9cfeecd1791117552611e83d36af7df4f3b4c783ddbd75d45bae66c9a`、valid `8f7509ad08fb9a62cdff1d6c904801c9421c3ce768bdd9ecb651cd480aa158e1`、invalid `e516f6a8e4ea811170c72e922b86ac7ea46594046704d01a55a2c8e13cd8f358`。
- Phase 06 在现有七个公开 suite 名下加入内部 SPARQL/quality/governance checks，并按合同变化 bump registry contract/version/hash；不得创建新公开 suite 名。

### 证据路径

- `build/validation/v0.4/{results.json,report.md,run-environment.json}`
- `build/phase-05/{manifest-validation.json,negative-controls.json,determinism.json,fixture-matrix.json}`
- `build/phase-05/current/suite-*-host.{result.json,machine.json,md}`
- `C_Semantic_Treehouse/manifests/{v0.4-test-cases.json,validation-suites.json,release-manifest.json}`
- `C_Semantic_Treehouse/fixtures/v0.4/{pass,fail,inapplicable,untestable}/`

最终结论：P05-A01–P05-A18 全部通过，Phase 05 为 `COMPLETE`。工作树保留本 Phase 与三项具名恢复的全部改动，未 commit、未 push；Phase 06 尚未开始。

## Phase 06 — 语义测试、质量指标与治理（COMPLETE）

- 完成日期：2026-08-10（Asia/Shanghai）
- 结论：`COMPLETE`
- 执行 HEAD / source state：`62e3391d935acc67b0402b3fc422f819330d705e` / `dirty=true`
- 范围：版本绑定 SPARQL semantic tests、SSSOM、八类质量指标、breaking-change 评估、七类治理/PROV-O-inspired provenance、五-manifest fail-closed 预检、registry 1.5.0 与统一 `all` 编排。

### 进入门槛与人工介入

Phase 00–05 的 `COMPLETE` 记录、Phase 05 四状态结果、四个业务 manifests、对应 schemas、requirements traceability、D 组输入与固定 lock 均在实施前以只读方式核验。进入时 HEAD 为上述 commit、工作树 clean、`CHECKPOINT.md` 为空闲占位符；`frozen` 为 104/104，`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4` 均为 `SUCCESS/exit 0`。直接调用 PowerShell wrapper 受宿主 execution policy 在校验器启动前拒绝；沿用 Phase 05 已批准的进程级 `-ExecutionPolicy Bypass` 调用后全部通过，系统 policy 与 wrapper 正文保持原样。

本 Phase 两次按人工介入策略暂停，并在取得当前用户具名决定后恢复：

1. registry 合同从 1.4.0 演进到 1.5.0 必然使 release binding 与 Phase 05 编排断言陈旧。用户明确授权四项最小接线：在 `entrypoint_catalog.py` 登记三个仅允许用于 `all` 的固定 logical entrypoint；新增不接受 shell/module/path payload 的 `checks_phase06.py` adapter；在 `checks_all.py` 固定三个 Phase 06 components；registry 定稿后仅同步 release manifest 的 registry SHA-256 与 contract version 两个字段。
2. SPARQL 子任务曾向 hash-bound 的历史 `competency-questions.md` 追加 v0.4 说明。五-manifest preflight 立即以 `BASELINE_MANIFEST_INVALID` / `artifact_hash_mismatch` 返回 `FAIL/ERROR`，原始 quality 失败结果 SHA-256 为 `7aa3183b7ed4576ac4dafd6c87ae328d0250704aaca9cb836afdee368629c5f3`。用户明确授权把该文件精确恢复为 HEAD 历史字节；最终 SHA-256 为 `dc8bb2a44e4f222efb36d3461098b8b926428b6af7a90aafba4236606bfd2218`，baseline manifest、历史 8 个 query 与 expected TSV 均无 diff。随后从最早受影响的 baseline 顺序复验到 `all`，全部 exit 0；失败证据保存在 `build/phase-06/recovery/quality-failure-historical-cq-hash.json`。

`scripts/validate.py` dispatcher、D 组输入、v0.4 model、fixtures、四个业务 manifests、manifest schemas、traceability、decisions 与全部历史 oracle 保持原字节。release manifest 最终 diff 只有获授权的两个 registry 绑定字段。

### Suite registry 与统一编排

`validation-suites.json` 的 `contract_version` 已从 `1.4.0` bump 为 `1.5.0`，最终 SHA-256 为 `0a189cc1db272d52fd789aade3bf416bb33262d5781bf5f2f468344a654126dd`。七个公开 suite ID 保持 `frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all`；`all` 仍按固定顺序展开六个非 `all` suite，再执行 `all.composition`、`all.semantic-sparql`、`all.quality`、`all.governance`。最终展开 16 个 components，0 failed、0 skipped。

release manifest 仅把 `validationSuiteRegistry.sha256` 更新为上述 hash、`contractVersion` 更新为 `1.5.0`，最终文件 SHA-256 为 `b7b15ddf0860c90e3404361f2b304c742cd7d0c00b9c5217398f049f6d9ec9d5`。registry schema/跨记录语义、entrypoint 唯一性、allowlist、依赖存在性、无环、`all` 无重复展开均通过。由于获授权范围保持 `all.owner_phase="05"` 与 dispatcher 路由不变，统一 suite 的临时 result 继续位于 `build/phase-05/current/`；Phase 06 三类组件真源位于固定 `build/validation/{sparql,quality,governance}/`，负控与确定性旁证位于 `build/phase-06/`。

核心编排/source SHA-256：

| 路径/角色 | SHA-256 |
|---|---|
| `scripts/validate.py` dispatcher | `0ead93869a34eacc497412679a2fb4365f2743a2fbbc24e61283c3a5fa9b497f` |
| `entrypoint_catalog.py` | `0d16ea36da31c0dbfc6525aad74652b7db77ddba09f8a421f08f79f2f8575e6e` |
| `checks_all.py` | `aa7048653a2916c05d58da9a94e3807b9a2664eb291007ac7c0fb58f03c03965` |
| `checks_phase06.py` | `ddca05f9a48b9ce2610ad85863bc583a47f77ef9c2136c7b0761a33aa5710331` |
| SPARQL runner / manifest checker / reporter | `f5a94041a79d2ec167400552d230730da14d89796dac63f66247517f26794049` / `208f23827db067a1e35034084651e5fbe8eec1f5278372692ff8c9402d5f69f3` / `a1c9f4198ba544b6a7bce99892ecfd975265f915a827b93720e9ef463a4232eb` |
| quality checker | `c54ddaa84cc76633e268c950d7950284dd925a78d4674dcdffdbac7a900a3c76` |
| governance checker / contract helper | `19bd419f3c8dc1a4afc036e136d6d2430432dd39dd9ff15091cbfeb26a07ef67` / `5c6248412496c13592d7dcf80425aebf506fc6971fe68b54ebe0be4c6d46227d` |

### SPARQL semantic tests

新增固定 `sparql-test-cases.json` 与 Draft 2020-12 schema，SHA-256 分别为 `6a86950dd10b1ecddfc33b62bd02f4f4d9615712748e19943bddae28fb9e4d45`、`9de54fd4e8e657678f8b0ab5ae09278624a592070f51731351d48e8c8e2bfd87`。manifest 精确登记 20 个 required CQ 与 40 个 query/expected artifacts：历史 v0.3 8 个、新增 v0.4 12 个；SELECT 15、ASK 4、COUNT 1。20/20 均发现、执行并精确匹配，0 failed、0 skipped。

v0.4 CQ 覆盖 exact-one Dataset 与 IRI node、核心 metadata 路径/值、distribution 路径/值、temporal 值与顺序、optional description/license、profile/version binding、D 命名 Shapes/severity/constraint components、Closed Shape allowed-property inventory，以及 v0.3 Energy Reading Record 的 `change=none` 继承合同。runner 每次先执行五-manifest 与 SPARQL manifest schema/语义预检，再按 release/requirement binding 选择 graph、query 和 expected；无无界 glob 或硬编码 v0.3 成功路径。

SPARQL 负控 21/21，通过 duplicate query/artifact ID、悬空 graph/expected/release/requirement、同路径多 hash、0 query、缺 expected、required skipped、orphan 及五个 authority manifest 的 duplicate/dangling 变异。两次规范化 results/Markdown 逐字节一致。

### SSSOM、质量指标与 breaking change

`external-standard-alignment.sssom.tsv` 累积为 47 行，SHA-256 `0fd0c09721df2ea3973fb45f7b12a9b204e55ad5171e6f716cf854c1fb0977a8`：migration 10、direct reuse 9、external alignment 15、inherited record alignment 13。列、IRI、predicate、confidence、justification、review status、重复与 self-mapping 语义检查通过；0 duplicate、0 unjustified self-mapping。47/47 映射均真实标记为 `PENDING_DOMAIN_REVIEW`。

八类指标全部由 manifests 与实际 RDF/SHACL 图计算，并记录 numerator、denominator、sources 与 exclusions：

| 指标 | 结果 |
|---|---|
| D 组规范性 requirement 实现覆盖 | 16/16 |
| requirement 自动测试覆盖 | 17/17 |
| required/optional 字段覆盖 | 12/12（10 required、2 optional） |
| constraint component 分布 | 8/8 类；closed 1、datatype 10、`sh:in` 3、maxCount 12、minCount 10、nodeKind 3、pattern 6、SPARQL 2 |
| 四状态自动用例覆盖 | 4/4；PASS 6、FAIL 53、INAPPLICABLE 1、UNTESTABLE 6 |
| 外部标准直接复用 | 7/12；直接复用审计 7/7，本地术语合理映射 5/5 |
| breaking-change 事实 | 20/20 |
| release/provenance metadata | 15/15 |

quality 的 20/20 负控覆盖零分母、重复规则、伪造百分比、来源漂移、SSSOM 列/IRI/predicate/justification/review status 与生成一致性。结论为 `INCOMPATIBLE_WIRE_PROFILE`：v0.4 metadata 是不兼容 wire-profile 迁移；Energy Reading Record 继续精确继承 v0.3 合同，`change=none`。

### Governance 与 provenance

累计更新 `model-card.md`、`changelog.md`、`namespace-policy.md`、`release-policy.md`、`deprecation-policy.md`、`review-workflow.md` 与 `provenance.jsonld`，保留 v0.1–v0.3 历史叙述并增加 v0.4 当前事实。governance 21/21 checks、五-manifest preflight 5/5、负控 12/12，0 failed/skipped；JSON-LD 离线 expansion 得到 34 个实体且通过 source path/hash、agent、activity、derivation、compatibility 与 validation artifact 断言。provenance SHA-256 为 `ad90f9c447edb534270932673024af492c94e455b94233d4ef0eeff62e73572d`。

本地 Phase 06 automated gate 已按实际统一运行更新为 `PASS`。C Group 最终语义审查、D Group 最终契约审查、Domain Reviewer、Release Approver、CI、GitHub publication 与 Semantic Treehouse run 均保持 `PENDING`；没有填写虚构 reviewer、approval、时间、URL、run ID 或 outcome。governance 规范化核心两次字节一致，机器环境单独写入 sidecar。

### 正式命令与退出码

| 命令 | 结果 |
|---|---|
| `git status --short --branch` | exit 0；进入时 `## main`，收口改动范围已审计 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Suite frozen` | exit 0；104/104；进入、全量运行内及最终收尾均通过 |
| 同入口 `-Suite environment` | exit 0；`SUCCESS` |
| 同入口 `-Suite baseline` | exit 0；`SUCCESS`；历史 CQ 恢复后再次通过 |
| 同入口 `-Suite traceability` | exit 0；`SUCCESS` |
| 同入口 `-Suite v0.4-model` | exit 0；`SUCCESS` |
| 同入口 `-Suite v0.4` | exit 0；66-case 四状态验证 `SUCCESS` |
| 同入口 `-Suite all` | 两次 exit 0；16/16 PASS、0 failed/skipped；两次 result SHA-256 均为 `b3e794b940fd1ac859a24162405e43fbd09476ece035c5805959f7c20ebeee31` |
| `.venv\Scripts\python.exe -m py_compile <dispatcher/catalog/adapters/SPARQL/quality/governance sources>` | exit 0 |
| `.venv\Scripts\python.exe C_Semantic_Treehouse\scripts\run_sparql_tests.py --self-test` | exit 0；canonical 20/20、负控 21/21、确定性 PASS |
| `.venv\Scripts\python.exe C_Semantic_Treehouse\scripts\quality_metrics.py` | exit 0；8 metrics、负控 20/20、确定性 PASS |
| `.venv\Scripts\python.exe C_Semantic_Treehouse\scripts\validate_governance.py` | exit 0；21/21、manifest 5/5、负控 12/12、确定性 PASS |
| `.venv\Scripts\python.exe -I build\phase-06\run_phase06_controls.py` | exit 0；五项 canonical preflight + 19 项 manifest/suite 变异，共 24/24 |
| provenance strict JSON + PyLD offline expansion | exit 0；34 expanded entities |
| 当前结果/source/manifest/schema/output hash 审计 | exit 0；453 条文件断言、190 个唯一文件与 15 条 SPARQL output 指纹，0 mismatch/missing |
| deterministic core 绝对路径/敏感信息扫描 | exit 0；17 个证据文件、0 命中；machine environment sidecar 按合同隔离 |
| `git diff --check` / `--stat` / `--name-status` | 各 exit 0；17 个 tracked 修改、31 个 untracked 文件，全部归属 Phase 06 或具名授权 |
| 三项对应 `git diff --cached ...` | 各 exit 0；index 为空 |
| `git status --short` | exit 0；保护路径、历史 CQ/oracle 与 `scripts/validate.py` 无 diff |

RDFLib 会为设计负例 `not-a-date-time` 输出非致命 `xsd:dateTime` 转换 traceback；结构化 oracle 与 suite 最终状态均为 `SUCCESS/0`。

### 机器证据

| 证据 | SHA-256 |
|---|---|
| `build/validation/sparql/results.json` | `30ddf952b7e9d8b681fd44bfacd411800b7f96b98db6f56916e4390317f5f22d` |
| `build/validation/sparql/report.md` | `284416a4715aa4d8275e5b5f82aafed8d394698ead2d0189dcc52ed1f0d03cf7` |
| `build/phase-06/sparql/negative-controls.json` | `6a873823ff75a8d269dba6d6a99568d215a6f1c1c39993b84e940c44aa1b5a36` |
| `build/phase-06/sparql/determinism.json` | `32440df8117a4492ddee11c34af77f32765df7193ae4050c09e59d505c7c8122` |
| `build/validation/quality/results.json` | `7e08cc85af120ea1b9e80d4ebb016f0a958c2a4ea87cf300308ace955f0269e5` |
| `build/validation/quality/report.md` | `d59926f6278bfbb506d8d4b9906cd3757eee79b840e97faaf56d0cb20db05415` |
| `C_Semantic_Treehouse/quality/model-quality-assessment.md` | `d8b20992929d32c4d9e94ecddaac0aafa7472a83ddbff3a9b23b4565d8d1d8ad` |
| `build/phase-06/quality/negative-controls.json` | `201b4d9332d2c50b33cb76f877c92cf7e79d0b1004f3a93a1f805fbe5a95ea4b` |
| `build/phase-06/quality/determinism.json` | `dbb33f69b75d074433214e08d5816d18bf3100d4e7f4b4d204ae6d7c89898a01` |
| `build/validation/governance/results.json` | `b4b0a245c908447f716468057fe7255b0c1c4dc21ed5ff771bc0461f14f7a7c5` |
| `build/validation/governance/report.md` | `b522de4dbe49ef696821a353f9b029c045d71d5cc8778b84c9170de0841a2d4d` |
| `build/phase-06/governance/manifest-preflight.json` | `aa9d4859797271127b098a3cd62aba3eb27d4ae33816a169172007cbdca958e1` |
| `build/phase-06/governance/negative-controls.json` | `36834139f3baed789bc11dbcb597c87558a26e6bcfe44a3b0e590d3996078591` |
| `build/phase-06/governance/determinism.json` | `03ea0f2db6f3c7f67db5cc0abada662a914c9e4e5ee4018706c8e0170bb3973a` |
| `build/phase-06/manifest-suite-negative-controls.json` | `afce8170098e0719cf1eceea7c4863bb6f35c85a40c9acab2e0ea83b2df492a1` |
| `build/phase-06/all-determinism.json` | `f53d562031eb3f8c0b6d221ecf43949c88d3e887c43571ef7bad4f001e6e2a97` |
| `build/phase-05/current/suite-all-host.result.json` | `b3e794b940fd1ac859a24162405e43fbd09476ece035c5805959f7c20ebeee31` |
| `build/phase-06/recovery/quality-failure-historical-cq-hash.json` | `7aa3183b7ed4576ac4dafd6c87ae328d0250704aaca9cb836afdee368629c5f3` |

三份 `run-environment.json` 独立记录机器元数据，排除在规范化确定性比较之外。结果文件记录五个 consumed manifests、相应 schemas、SPARQL manifest/schema、registry 版本/hash，以及 dispatcher、checker、reporter 与所有实际加载 helper 的 source SHA-256；最终 freshness issue 为 0。

### P06 验收矩阵

| ID | 结果 | 证据摘要 |
|---|---|---|
| P06-A01 | PASS | 历史 v0.3 CQ 8/8 required 全执行；query/expected/oracle 原字节 |
| P06-A02 | PASS | v0.4 CQ 12/12；总计 20/20 精确匹配，版本来源明确 |
| P06-A03 | PASS | 0 query、缺 expected、required skipped 均由负控非零拒绝 |
| P06-A04 | PASS | SSSOM 47 行；列/IRI/predicate/duplicate/justification/review status 检查通过 |
| P06-A05 | PASS | requirement 实现 16/16、自动测试 17/17，均由 manifest 计算 |
| P06-A06 | PASS | 八类指标均有分子、分母、来源与排除规则 |
| P06-A07 | PASS | breaking-change 20/20；结论 `INCOMPATIBLE_WIRE_PROFILE`；record `change=none` |
| P06-A08 | PASS | 七类 governance 文件包含 v0.4；21/21 checks |
| P06-A09 | PASS | provenance JSON-LD 可解析；来源 hash、derivation、agent、activity 完整 |
| P06-A10 | PASS | approval/CI/GitHub/Treehouse 与最终人工 reviews 均保持真实 `PENDING` |
| P06-A11 | PASS | SPARQL、quality、governance 与 `all` 各自双跑结果一致 |
| P06-A12 | PASS | `all` exit 0；16/16 components、0 failed/skipped |
| P06-A13 | PASS | 五-manifest 5/5 与 SPARQL manifest/schema 通过；各类 duplicate/cross-ref/hash 负控 fail closed |
| P06-A14 | PASS | registry 1.5.0；七个公开 suite 不变；`all` 纳入三个固定内部 checks |
| P06-A15 | PASS | dispatcher/checker/reporter/helper source hashes 已记录，freshness 0 issue |
| P06-A16 | PASS | Phase 前后 frozen 104/104；staged/unstaged、stat、name-status 与保护范围审计通过 |

### 风险处置与待人工治理项

- `P00-R08`、`P00-R09`、`P00-R10`：保持 Phase 05 已关闭结论；本 Phase 的版本绑定 CQ、零发现保护、manifest 语义与统一全量回归再次确认关闭。
- `P00-R11`：保持关闭；wire-profile breaking-change、Closed Shape 与 v0.3 record 继承事实再次确认。
- `P00-R13`：保持 `CONTROLLED`；两次中断均有 CHECKPOINT、最小失败证据、具名授权、精确恢复和顺序复验。
- `P00-R14`：保持 `OPEN`；C/D final review、Domain Reviewer 与 Release Approver 仍待真人完成。
- `P00-R15`：保持 `OPEN` 至 Phase 09；104/104 只证明 frozen manifest 登记边界。
- `P00-R16`：保持 `OPEN`，交 Phase 07/09 同步受保护导航与 provenance 叙述。
- `P00-R12`：保持 `OPEN` 至 Phase 08 可选证据轨；Treehouse、Mermaid、ITB/SEMIC 缺席不影响本 Phase 核心验收。
- `P00-R01`–`P00-R05` 继续按 Phase 09 的发布目标、许可、隐私、提交身份元数据与远程发布链决策处理；`P00-R06` 保持关闭，`P00-R07` 的 Phase 01 隔离义务已完成且 Phase 09 clean-room 复核保留。
- 新增 `P06-R01`（`CONTROLLED`）：Phase 可写目录中的历史文件仍可能受早期 manifest 精确 hash 保护。preflight 已实际阻止漂移，文件已按具名授权恢复；Phase 09 汇总时应把“manifest binding 优先于 Phase-local 写路径”纳入发布审计规则。

待人工治理项：C Group v0.4 final semantic review、D Group final contract review、Domain Reviewer review、47 条 SSSOM mapping 的 domain review，以及 Release Approver 最终决定。CI、GitHub publication 与 Semantic Treehouse 属尚未执行的外部活动，继续为 `PENDING/NOT RUN`；本 Phase 未把它们记为 `DEFERRED` 或通过。

以上处置不回写 Phase 00 baseline risk snapshot；Phase 09 在新增风险汇总中消费本节。

### Phase 07 进入包与条件

Phase 07 接收四个业务 manifests 及 schemas、registry `1.5.0`/hash、SPARQL manifest/schema/语义与确定性证据、三类机器 results/reports、runner/helper source hashes、47 行 SSSOM、七类治理文件和明确的 breaking-change 结论。进入时继续要求 Phase 00–06 `COMPLETE`、`CHECKPOINT.md` 为空闲占位符、七个 suite 全部 exit 0、最终 staged/unstaged 范围审计通过，并原样携带上述人工/外部 pending 事实。

最终结论：P06-A01–P06-A16 全部通过，Phase 06 为 `COMPLETE`。`CHECKPOINT.md` 已恢复固定空闲占位符；工作树保留本 Phase 与两项具名恢复的全部改动，未 commit、未 push；Phase 07 尚未开始。

## Phase 07 — 当前文档、图表与 A/B/D 组 Handoffs（COMPLETE）

- 完成日期：2026-08-10（Asia/Shanghai）
- 结论：`COMPLETE`
- 执行 HEAD / source state：`be39016b5ff1ea8ba9b4aa3c20c66e953009d9a0` / `dirty=true`
- 范围：当前 README/迁移导航、四份 C 组核心报告、两张 Mermaid source、A/B/D handoff、AI-assisted human-governed 说明、documentation checker/negative controls，以及 registry 1.6.0 的 required `all` composition。

### 进入门槛与具名恢复

Phase 00–06 的 `COMPLETE` 记录、P06-A01–P06-A16、四个业务 manifests/schemas、批准 ADR、四状态结果、SPARQL/quality/governance 结果和真实 `PENDING/NOT RUN` 边界均在实施前核验。初始 HEAD 为上述 commit，工作树/index 为空，`CHECKPOINT.md` 为空闲占位符；`frozen` 104/104，`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4` 与进入时的 `all` 均 exit 0。

本 Phase 按人工介入策略完成两次暂停、具名授权和顺序恢复：

1. 只读审计证明 Phase 01 的受控 entrypoint catalog 与 Phase 06 的 exact `all` composition 没有预留 documentation entrypoint；registry 字节变化还会触发 Phase 04 release binding 与 Phase 06 quality/governance version 断言。用户明确回复“允许”，授权最小修改 `scripts/dssc_validation/entrypoint_catalog.py`、`C_Semantic_Treehouse/manifests/release-manifest.json`、`scripts/dssc_validation/checks_all.py`、`C_Semantic_Treehouse/scripts/quality_metrics.py`、`C_Semantic_Treehouse/scripts/governance_contract.py`，并按 Phase 01 → 04 → 06 顺序恢复。
2. 第一轮恢复使 provenance 中三个既有 SHA-256 freshness binding 合法陈旧；governance 两次稳定以相同三项 binding 失败。用户明确回复“授权”，批准只同步 `C_Semantic_Treehouse/governance/provenance.jsonld` 中 release manifest、suite registry 与 Phase 06 manifest-preflight 的 hash。恢复后 governance/provenance validation exit 0。

`scripts/validate.py` 保持原字节，SHA-256 为 `0ead93869a34eacc497412679a2fb4365f2743a2fbbc24e61283c3a5fa9b497f`。D 组输入、模型、Shape、requirements、fixtures、test oracle、quality 算法、governance policy、历史 Phase 00–06 小节和七个公开 suite 名称均保持既有合同。

### 当前文档包与真实性边界

- 13 份 required Markdown 与 2 张 Mermaid source 全部发现；0 broken/case-mismatched local links、0 未允许绝对/临时路径、0 stale runner、0 unknown artifact/suite。
- 根 README、迁移清单、package README、package scripts README 与 `docs/v0.4/README.md` 已同步当前入口、证据层次、四业务状态/程序状态、离线边界和 Phase 08/09 状态。
- 四份核心报告各含 11 行 release-manifest artifact projection，ID、version、role、path 与 SHA-256 逐项一致；v0.3 → v0.4 明确为 `wire-profile-breaking`，Energy Reading Record 保持 v0.3 `change=none` 继承。
- A handoff 固定 D04-R003–D04-R015 字段投影、D04-R013 temporal order、HTTPS endpoint、迁移与精确命令；D handoff 固定 D/C Shape、requirements/test manifests、四状态优先级、report graph 与 ITB mapping；B handoff 固定 model/profile URI、path/hash、PROV entity/activity/agent、兼容性与 Gaia-X/法律边界。
- AI-assisted human-governed 文档记录人工/机器 gates、发布授权边界和 prompt/manifest/diff/report/provenance 审计轨；AI 不具发布审批权。
- 两张 Mermaid 仅通过确定性结构 lint。Mermaid parser、render 与视觉 QA 为 `NOT RUN`；Semantic Treehouse v0.4、外部 SEMIC/ITB、CI、最终 Docker clean-room、clean clone、GitHub publication/tag/release 均为 `NOT RUN/PENDING`。

### Documentation checker、负控与确定性

`scripts/check_documentation.py` 的 standalone canonical 为 `PASS/SUCCESS`：13 documents、2 diagrams、15 discovered、19/19 checks、0 failed、0 skipped。19 项检查覆盖 required discovery、Markdown links、绝对/临时路径、命令/suite、suite table、repository reference、artifact projection、表内与行内 path/hash、A 字段、真实 test-case status、四状态计数、hash declarations、真实性状态、required content、Mermaid structure、suite registry、dispatcher envelope 与 source-hash coverage。

self-test 的 46/46 controls 全部得到实际非零退出，0 failed/skipped；覆盖 broken link/image/reference、大小写、Windows/POSIX/home path、未知/带引号 suite、裸解释器与 stale runner、artifact/table/path/hash/ID/field/status 漂移、0 discovery、Mermaid comment/quoted-label decoy、以及 `NOT RUN` 向 DONE/PASS/矛盾完成状态的改写。每项记录 target path、fixture SHA-256/bytes、override SHA-256、observed issue code 与 `actual_exit_code=1`。

standalone 结果与 environment sidecar 记录 29 个实际加载 checker/dispatcher/reporter/helper source hashes，`source_hash_issues=[]`；统一 `all` 结果记录 39 个聚合 source hashes，亦无 freshness issue。两个独立 canonical run 的 `results.json`、`report.md`、`run-environment.json` 三项 SHA-256 分别完全相同，确定性结论为 `BYTE_IDENTICAL/PASS`。

### Suite registry 与统一 dispatcher

`validation-suites.json` 的 `contract_version` 从 `1.5.0` 推进为 `1.6.0`，SHA-256 为 `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`。七个公开 suite 及顺序保持 `frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all`；checker 精确冻结每个 suite 的 `status`、`owner_phase`、`depends_on` 和有序 components。

`all` 依次展开六个 constituent suites，再执行 `all.composition`、`all.semantic-sparql`、`all.quality`、`all.governance`、`all.documentation`，总计 17 个 required components。documentation logical entrypoint 仅允许 `all`，并通过不可变精确类型 adapter 绑定 `check_documentation.run_documentation_check`；dispatcher 传入 suite、contract version 与 registry SHA-256，checker再与磁盘 registry 交叉核验。最终 `all` 为 `SUCCESS`：17/17、0 failed、0 skipped。`all.owner_phase="05"` 保持原合同，因此 suite 聚合结果继续位于 `build/phase-05/current/`。

release manifest 的 registry binding 精确为 1.6.0/上述 hash，文件 SHA-256 为 `d6910f4f384f507df263c2fc03187fcb3221f8b9f8f68274f5661c231dd2313a`。provenance 只同步三项获授权 binding，最终 SHA-256 为 `d6cc32e1c26137695a6542f4ec419550443c47362cd772ffe64675dfc02af608`；Phase 06 manifest-preflight SHA-256 为 `83731951cbada4aca7bcab83cb4266b6d74d4db3588fe7546bd07a24c8a2adac`。

核心实现 SHA-256：

| 路径/角色 | SHA-256 |
|---|---|
| `scripts/check_documentation.py` checker/reporter/dispatcher adapter | `6cc7528ffa8913c480e0145d673fbb64c1789886e2f6e138d0876efa000351a4` |
| `scripts/validate.py` unchanged dispatcher | `0ead93869a34eacc497412679a2fb4365f2743a2fbbc24e61283c3a5fa9b497f` |
| `scripts/dssc_validation/entrypoint_catalog.py` | `aef63d7df168d80a7614f5ff49c4681f431feb8f52a0c9e12eca0fa27821c088` |
| `scripts/dssc_validation/checks_all.py` | `1d539eb983ff138a4151c1abe6800cc4293c133744a96d7e94be499e8a7d4b35` |
| `C_Semantic_Treehouse/scripts/quality_metrics.py` | `c024762d54bc4d1fdb55e41ad21485c495f1126cb83f1a9ceb9509c42ff66d83` |
| `C_Semantic_Treehouse/scripts/governance_contract.py` | `d152ea3604ee5fd87f24abdb23fa27dadae892ccd733b0b3ed068bc2252739d6` |

### 正式命令与退出码

| 命令 | 结果 |
|---|---|
| 初始与收口 `git status --short --branch` 及 unstaged/staged diff check/stat/name-status | 各 exit 0；index 为空；范围逐项审计通过 |
| `.\.venv\Scripts\python.exe scripts\verify_frozen_files.py` | exit 0；104/104；进入、正式运行后与最终收口均通过 |
| `.\.venv\Scripts\python.exe scripts\doctor.py --profile host` | exit 0；host overall `PASS`，CPython 3.12.10 repo venv、lock 与 pip check 通过 |
| `.\.venv\Scripts\python.exe -m py_compile scripts\dssc_validation\entrypoint_catalog.py scripts\check_documentation.py` | exit 0 |
| `.\.venv\Scripts\python.exe scripts\check_documentation.py --self-test` | exit 0；canonical PASS；46/46 controls PASS |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Suite all` | exit 0；17/17、0 failed/skipped；documentation 经 registry 实际进入 `all` |
| `.\.venv\Scripts\python.exe scripts\check_documentation.py` 两次 | 两次 exit 0；19/19、0 failed/skipped；三份输出逐字节一致 |
| 最终 result/source/registry/release/provenance/evidence SHA-256 审计 | exit 0；当前字节与 evidence binding 一致，0 source hash issue |

宿主 execution policy 继续要求进程级 `-ExecutionPolicy Bypass`；wrapper 正文与系统 policy 保持原样。`all` 中设计负例 `not-a-date-time` 会输出 RDFLib 非致命转换 traceback；结构化结果与最终进程状态为 `SUCCESS/exit 0`。

### 机器证据

| 证据 | SHA-256 |
|---|---|
| `build/validation/documentation/results.json` | `7c920661917921bf9e01151789cf56ca34e09a4a3f84b93697e7bd4ffa1816d6` |
| `build/validation/documentation/report.md` | `6ef7f684d4a0d569cada1aea21eaf64a834bb54bdbc4a45d4ab86ad7c638fd34` |
| `build/validation/documentation/run-environment.json` | `52246f483cb4549e695c08a2f27bdcbc386360788840852ccb8ddc800ff66ba9` |
| `build/phase-07/documentation-negative-controls.json` | `dedb08f3b5720e1d4bf92b8ccbba0ac5cb2e5aef150bd0e47b21b27db2d3720d` |
| `build/phase-07/documentation-determinism.json` | `b8f22c7aef45c077d9c398abd38224bdbb9e60e370af5d218bb21ce520c60371` |
| `build/phase-05/current/suite-all-host.result.json` | `a7accfdbbaff3e29153d57316d39f1b751e4531ca287047c442deadf8a12c84f` |

### P07 验收矩阵

| ID | 结果 | 证据摘要 |
|---|---|---|
| P07-A01 | PASS | README/迁移清单覆盖环境、七 suite、四状态、网络、证据层次与 Phase 08/09 边界 |
| P07-A02 | PASS | 四份报告章节完整；每份 11 个 artifact rows 与 release manifest 精确一致 |
| P07-A03 | PASS | v0.3 → v0.4 明确为 wire-profile breaking change；record `change=none` |
| P07-A04 | PASS | 两张 Mermaid 仅报告结构 lint PASS；syntax/render/visual QA 保持 NOT RUN |
| P07-A05 | PASS | A handoff 字段、canonical example、迁移、HTTPS/format/frequency/unit/temporal/Closed Shape 与命令一致 |
| P07-A06 | PASS | D handoff 的 authority/derived hash、四状态、report assertions、ITB mapping 与 external NOT RUN 完整 |
| P07-A07 | PASS | B handoff 的 URI/version/hash、PROV 方向、兼容性和法律边界完整 |
| P07-A08 | PASS | AI 治理文档固定 human/validator/release gates，无自主批准声明 |
| P07-A09 | PASS | 0 broken/case-mismatched links，0 未允许绝对路径，0 stale command |
| P07-A10 | PASS | 46/46 negative controls 均实际非零拒绝，0 failed/skipped |
| P07-A11 | PASS | checker、dispatcher、reporter 与全部实际加载 helper source hashes 进入 result/environment，0 issue |
| P07-A12 | PASS | registry 1.6.0、schema、release hash binding、七-suite 投影与 `all` 有序 composition 精确 |
| P07-A13 | PASS | documentation 仅由 registry 接入 `all`；精确 catalog target/allowlist 通过；`scripts/validate.py` 无 diff |
| P07-A14 | PASS | Treehouse/CI/Mermaid render/外部 validator/发布继续为真实 NOT RUN/PENDING |
| P07-A15 | PASS | `all` exit 0；17/17 required components，0 failed/skipped |
| P07-A16 | PASS | frozen 最终 104/104；staged/unstaged/untracked 与授权保护范围审计通过 |

### 风险处置与待人工/外部项

- `P00-R13`：保持 `CONTROLLED`；两次中断均具有直接失败证据、最小具名授权、顺序恢复与最终回归。
- `P00-R14`：保持 `OPEN`；C Group final semantic review、D Group final contract review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 继续等待真人完成。
- `P00-R15`：保持 `OPEN` 至 Phase 09；104/104 证明 frozen manifest 登记边界。
- `P00-R16`：当前 README/handoff/provenance 已同步 Phase 07 真源；Phase 09 最终发布文档/provenance 同步义务继续 `OPEN`。
- `P00-R12`：保持 `OPEN` 至 Phase 08 可选外部证据轨；Treehouse、Mermaid parser/render、SEMIC/ITB 当前 `NOT RUN`。
- `P00-R01`–`P00-R05`：继续交 Phase 09 处理发布目标、许可、隐私、提交身份元数据与远程发布链。
- `P06-R01`：保持 `CONTROLLED`；manifest binding 优先于 Phase-local 可写路径，preflight 与 documentation path/hash checks 均继续 fail closed。

### Phase 08 进入包与条件

Phase 08 接收验证通过的 quickstart、统一 Windows/Linux/Docker 命令说明、13 份当前文档、两张 Mermaid source、A/B/D handoff、AI 治理说明、documentation results/environment、46 项负控、确定性证据，以及 registry `1.6.0` / `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`。Phase 08 只读消费该 registry，并通过冻结后的 `all` 运行 CI/reproduce/Docker 路径；任何 composition/version 变化返回其所属阶段处理。Mermaid renderer、Semantic Treehouse、SEMIC/ITB 继续按可选证据计划分类，不构成 Phase 07 核心完成条件。

最终结论：P07-A01–P07-A16 全部通过，Phase 07 为 `COMPLETE`。`CHECKPOINT.md` 已恢复固定空闲占位符；工作树保留 Phase 07 与两次具名恢复的全部改动，index 为空，未 commit、未 push；Phase 08 尚未开始。

## Phase 08 — 跨平台、CI、Clean-room 与可选 Treehouse 证据（COMPLETE）

- 完成日期：2026-08-11（Asia/Shanghai）。
- 结论：`COMPLETE`。required core 在 Windows PowerShell、WSL2 Linux、固定 Linux validation container、Windows/Linux clean-room 与本地 CI policy 轨全部通过。
- 冻结合同：suite registry 继续为 `contract_version=1.6.0`、SHA-256=`09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`；schema、七个公开 suite 名称及 `all` composition 均无 diff；最终 frozen 为 104/104。
- 发布边界：实际 GitHub Actions、remote clean clone、tag、release 与 publication 继续为 `NOT RUN`，由 Phase 09 在发布授权后完成。

### Required matrix

| Gate | 结果 | 证据 |
|---|---|---|
| Windows host / wrappers | `PASS`；最终 frozen 104/104、host doctor、`validate.ps1 -Suite all` 17/17、`reproduce.ps1` 17/17 均 exit 0 | `build/phase-05/current/suite-all-host.result.json`；`build/phase-08/core-consolidated-v8.json` |
| WSL2 Linux native | `PASS`；Ubuntu 24.04 / x86_64，reproduce、frozen、doctor、CI normal/self-test 与 `validate.sh --suite all` 六项均 exit 0 | `build/phase-08/linux-v8-final/harness-result.json` |
| 固定 validation container | `PASS`；linux/amd64、非 root、read-only root、network none、cap drop、no-new-privileges；doctor、pip check、CI 与显式/默认 `all` 均 exit 0 | `build/phase-08/docker/final-v3-result.json`；`build/phase-08/docker/inspection-summary.json` |
| Windows / Linux clean-room | `PASS`；两轨均从 `.venv=ABSENT` 开始，3/3 命令通过，source 未改变，临时运行面已清理 | `build/clean-room/路径 with space-win-v6-final/evidence/rehearsal-result.json`；`build/clean-room/路径 with space-linux-v8-final/evidence/rehearsal-result.json` |
| CI static policy | `PASS`；normal exit 0、0 issue、双跑逐字节一致；self-test 59/59 | `build/ci/check-ci.result.json`；`build/ci/check-ci-self-test.result.json` |
| Documentation truth contract | `PASS`；canonical 19/19；self-test 59/59；Treehouse 各阶段状态使用结构化 external evidence | `build/validation/documentation/results.json`；`build/phase-07/documentation-negative-controls.json` |
| 单一验证核心 / registry | `PASS`；Windows、Linux、Docker、reproduce、CI 均消费同一 frozen registry 与 `scripts/validate.py` 编排 | `build/phase-08/core-consolidated-v8.json` |
| GitHub Actions 实际 run | `NOT RUN`；Phase 09 publication gate | `build/phase-08/github-actions-status.json` |

### Semantic Treehouse 可选轨

Treehouse 可选轨总体状态为 `DEFERRED`，本次实际尝试为 `BLOCKED_AFTER_CONTROLLED_RETRY`，required core impact 为 `NONE`。

| 阶段 | 真实状态 | 证据与边界 |
|---|---|---|
| 固定 upstream | `已完成` | tag `v4.3.0` 固定到 commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf`；detached sparse checkout/materialization、required hash、license、clean/ignored residue 与 `core.autocrlf=false` 均核验 |
| raw Compose preflight | `BLOCKED` | exit 1；33 `BLOCK`、46 `REVIEW`、`execution_authorized=false`；原始结论保持不变，见 `build/evidence/treehouse/preflight.json` |
| finding-specific human opt-in | `APPROVED` | 用户批准已展示风险、部署前修复、固定提交物化及更窄的 production runtime attempt；raw preflight 继续保持 `BLOCKED` |
| production `PrepareOnly` | `已完成` | exit 0；闭包仅 `sth` + `sth-db2`，`APP_ENV=prod`、loopback `127.0.0.1:18014`、DB 零宿主端口、internal network、项目卷、无 bind/extra-host；pull/build/up/container/volume/migration/smoke counters 全为 0，见 `build/evidence/treehouse/runtime-boundary-prepare-only.json` |
| image build | `BLOCKED_AFTER_CONTROLLED_RETRY` | `treehouse_up.ps1` exit 1；digest-pinned FrankenPHP layer 预期 20,064,658 bytes，收到 2,407,954 bytes 后 short read / unexpected EOF；受控重试额度已用完，见 `build/evidence/treehouse/runtime-build-controlled-transport-retry-error.json` |
| deployment | `NOT DEPLOYED` | 应用镜像没有完成；image inspect、Compose up 与服务启动均未发生 |
| workload / migration / UI / API | `NOT RUN` | 无应用或数据库 container，无 migration，无 localhost 页面或 API endpoint，因此无 UI/API 结果 |
| model import / export / publication | `NOT RUN` | 均在批准范围之外，零输入、零导出、零发布 |
| 最终资源状态 | `STOPPED` | project containers=0、network=0、volumes=0、target app image=0；只读 status exit 0，见 `build/evidence/treehouse/runtime-status.json` |

八个 Treehouse lifecycle wrappers 已完成固定 commit、跨平台换行、绝对网络超时、全量 ignored/secret residue 拒绝、fresh-only 项目资源、随机私有 runtime secrets、production Compose 投影、digest-pinned build、镜像检查、bounded readiness、首次 migration、localhost 首跳 smoke、精确标签清理与脱敏证据合同。PowerShell parser 4/4、WSL shell syntax 4/4、diff check 均通过；静态汇总见 `build/evidence/treehouse/runtime-wrapper-static-validation.json`。秘密值扫描覆盖 48 个 runtime/evidence 文件，exact secret、绝对仓库路径与用户名命中均为 0。

### 其他可选轨

| Track | 状态 | 边界 |
|---|---|---|
| Mermaid parser/render/视觉 QA | `DEFERRED` | 当前只保留 Phase 07 deterministic structural lint；没有 renderer 或人工视觉结论 |
| 外部 ITB/SEMIC | `DEFERRED` | 没有数据外传授权；uploaded files=0、uploaded bytes=0 |

统一索引为 `build/phase-08/optional-evidence-index.json`。所有可选轨均保持与 required `all` 隔离。

### 最终命令与结果

| 命令 | 结果 |
|---|---|
| `.\.venv\Scripts\python.exe scripts\verify_frozen_files.py` | exit 0；104/104 |
| `.\.venv\Scripts\python.exe scripts\doctor.py --profile host` | exit 0；overall `PASS` |
| `.\.venv\Scripts\python.exe scripts\check_ci.py --self-test` | exit 0；59/59 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Suite all` | exit 0；17/17 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1` | exit 0；doctor 与 17/17 `all` 通过 |
| `.\.venv\Scripts\python.exe -I scripts\check_documentation.py` | exit 0；19/19 |
| `.\.venv\Scripts\python.exe -I scripts\check_documentation.py --self-test` | exit 0；59/59 |
| `.\.venv\Scripts\python.exe -I scripts\check_treehouse_compose.py --self-test` 双跑 | 两次 exit 0；28/28；输出字节一致 |
| raw Treehouse preflight 命令 | 预期 exit 1；`BLOCKED`，33/46，`execution_authorized=false` |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\C_Semantic_Treehouse\scripts\treehouse_up.ps1` | exit 1；镜像构建受 registry short-read/EOF 阻断，未启动 workload |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\C_Semantic_Treehouse\scripts\treehouse_status.ps1` | exit 0；`STOPPED`，零 project resources |

### 风险与 Phase 09 交接

- `P00-R12` 保持 `OPEN`：Treehouse、Mermaid renderer 与外部 ITB/SEMIC 继续作为隔离可选轨；本阶段保存了真实尝试、失败、零资源影响与恢复步骤。
- `P00-R13` 保持 `CONTROLLED`：网络传输失败、wrapper 诊断缺陷与每次修复均有独立证据；最终 helper 对 unavailable exit code 和 BuildKit hard-failure markers fail closed。
- 新增 `P08-R01`（`OPEN/DEFERRED`）：Docker Hub 对 digest-pinned layer 的重复 short read / unexpected EOF 阻断 Treehouse image build。恢复条件是 registry transport 稳定、取得新的人工批准、从零资源状态重新执行 checkout 与 `PrepareOnly` gates；当前不再自动重试。
- `P00-R14`、`P00-R15`、`P00-R16` 继续交 Phase 09：真人语义/合同/发布审核、真实 GitHub run、remote clean clone、tag/release、最终 provenance 与发布证据仍待完成。

最终结论：P08 required core 全部通过，Semantic Treehouse 的构建失败被隔离为可选轨 `DEFERRED`，Phase 08 为 `COMPLETE`。工作树保留本阶段与已授权真实性恢复的改动；index 为空；未 commit、未 push、未配置或触发远程发布。

## Phase 08 Semantic Treehouse recovery addendum — 2026-08-12

本 addendum 仅记录获批准的后续恢复结果；前述 checkout、preflight、受控 build failure、cleanup 与 `STOPPED` 记录继续保留为对应时间点的历史证据。恢复使用同一固定 upstream `v4.3.0` / commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf`、Compose project `dssc-semantic-treehouse-v04` 与 loopback 端口 `18014`。

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=RUNNING`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=NOT RUN`; `model import=NOT RUN`; `export=NOT RUN`; `publication=NOT RUN`。

| Recovery stage | 当前结果 | 当前证据与边界 |
|---|---|---|
| fixed checkout/materialization | `PASS` | exact lock、detached clean checkout 与 materialization 已通过；`build/evidence/treehouse/checkout-wrapper.json` |
| canonical raw Compose preflight | `BLOCKED` | canonical 结果继续为 33 `BLOCK`、46 `REVIEW`、`execution_authorized=false`；`build/evidence/treehouse/preflight.json` |
| human opt-in | `APPROVED` | 用户批准部署恢复、network options、Windows label projection、singleton network/port projection 修复，以及 Phase 07 documentation checker 的当前真实性投影同步 |
| production `PrepareOnly` | `PASS` | zero mutation counters、production/loopback/双网络/项目卷边界通过；`build/evidence/treehouse/runtime-boundary-prepare-only.json` |
| image build and inspection | `PASS` | digest-pinned database image 与项目 app image 均通过运行前检查；`build/evidence/treehouse/runtime-up.json` |
| deployment and workload | `PASS` | `sth`、`sth-db2` 均 healthy，exact container/network/volume labels 与 context binding 通过；成功 runtime 被保留 |
| database migration | `PASS` | production migration 完成，成功 state marker 记录 migration 状态；`build/phase-08/treehouse-runtime/runtime-state.json` |
| root loopback smoke | `PASS` | `http://127.0.0.1:18014/` 返回 HTTP 200 |
| API loopback availability smoke | `PASS` | `http://127.0.0.1:18014/api/environment/info` 返回 HTTP 200 |
| current runtime | `RUNNING` | `build/evidence/treehouse/runtime-status.json`：两容器 healthy、应用双网络、数据库仅 internal network、DB 零宿主端口、应用 binding `127.0.0.1:18014:80`、state/context binding 有效 |
| UI workflow | `NOT RUN` | 未执行浏览器 UI 交互或视觉验证 |
| model import | `NOT RUN` | 未执行模型导入或语义比对 |
| export | `NOT RUN` | 未产生导出 bytes 或比较报告 |
| publication | `NOT RUN` | 未执行 tag、release、远程 workflow 或外部发布 |

恢复后的当前服务状态为 `RUNNING`，仅通过 `127.0.0.1:18014` 暴露应用。Semantic Treehouse 仍为隔离的可选证据轨；Phase 08 required core 的 `COMPLETE` 结论和 frozen `all` composition 保持不变。

### Recovery closeout commands and evidence

| 命令 | 结果 |
|---|---|
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\C_Semantic_Treehouse\scripts\treehouse_up.ps1 -HttpPort 18014` | exit 0；获批的唯一 deployment attempt 已消费；production migration、root/API loopback availability smoke 均通过 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\C_Semantic_Treehouse\scripts\treehouse_status.ps1` | exit 0；`RUNNING`；两容器 healthy，app 双网络，DB internal-only，宿主绑定仅为 `127.0.0.1:18014:80` |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Suite all` | exit 0；17/17 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1` | exit 0；bootstrap、doctor 与 17/17 `all` 通过 |
| `.\.venv\Scripts\python.exe -I -B scripts\clean_room.py --mode manifest-only --dry-run --run-id treehouse-recovery-closeout-20260812` | exit 0；440 candidates、0 untracked、`write_performed=false` |

成功收口为 `build/evidence/treehouse/deployment-success-closeout-2026-08-12.json`（SHA-256 `2f338189903eb17e65170992cb2447d36ab2d8c4c9dec61b98b6b1f1efedd5d6`）；最终脱敏扫描为 `build/evidence/treehouse/deployment-success-evidence-scan-2026-08-12.json`（SHA-256 `b082038eb31ba1b693b7b9d22af6a4b66d4665d01cc9319739c84a53474e6bf4`）；统一可选轨索引为 `build/phase-08/optional-evidence-index.json`（SHA-256 `fdaa39c189fac4e6aa317854fffb7f0f82264a96f368b401e13ca900d985a31f`）。扫描的 25 个显式绑定全部匹配，14 类 secret/path/credential 指标均为 0；含 JSON-escaped 仓库路径的旧失败 raw 已在 `historical-evidence-integrity-2026-08-12.json` 中标为 `PARTIAL` 并从 PASS 扫描集合排除。

最终本地回归：frozen 104/104、host doctor `PASS`、CI policy 0 issues、CI negative controls 59/59、documentation 19/19、documentation negative controls 80/80、Treehouse compose checker 45/45。未执行成功运行态的 down；未执行 Git commit、push、tag、release、远程 workflow 或外部发布。

## Phase 08 Semantic Treehouse UI/import recovery addendum — 2026-08-12

本 addendum 记录用户批准方案 A 及后续 Phase 07 文档真实性投影恢复。前述 2026-08-11 build failure、`STOPPED`、2026-08-12 deployment recovery 的 UI/import/export `NOT RUN` 均继续作为对应时点的历史记录。Phase 08 required core 仍为 `COMPLETE`，registry 仍为 `1.6.0` / `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`，`all` composition 无变化。

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=RUNNING`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=NOT RUN`。

### 登录与存储恢复

确定根因为 production runtime 与 dev-only fake Admin IdP 的配置冲突。派生 runtime 继续使用 `APP_ENV=prod`、`APP_DEBUG=0`，新增显式 `STH_LOCAL_REVIEW_LOGIN=1`；production 放行条件同时要求 `Account.id=admin`，`jsonLogin` 的 dev-only guard 保持原样。补丁固定上游 `SecurityController.php` preimage `14332816e463349182363e2446799e88ce2f7c78bfdf2b63487e12d7f2a1c06d` 与 postimage `f694f53157af74fc706fda6a36dd63e4d033d7f3620703290246edbaac0312b1`，只进入派生 image，上游 checkout 仍 clean。Linux wrapper 同步把 `SERVER_HOST_NAME` 规范化为当前 `http://127.0.0.1:<port>`。

应用 upload volume 已从无效的 `/var/www/data` 改为 Treehouse 实际目录 `/app/var/user_data`。恢复只重建 app；DB container 未重建、app/DB 两个 volume 均保留、删除数为 0。两 wrapper 的 auth smoke 证明 admin/`ROLE_ADMINISTRATOR`，客户端 cookie/session material 不进入持久 evidence；服务端 Symfony session 仍按上游 PDO handler 工作。

| 检查 | 结果 | 证据 |
|---|---|---|
| derived auth/storage recovery | `PASS` | `build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json`；SHA-256 `1be09b7b3393f72feaf3920fc075077cd5f7e60c211c30b680d0528e8ab033d9` |
| real browser login | `PASS` | Edge 实际完成 `/login` → Admin → `/`，可见 `admin`、Administrator/User roles 与 Logout；见 `build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json` |
| current runtime | `RUNNING` | app/DB healthy，app 仅 `127.0.0.1:18014:80`，DB 零宿主端口，runtime state/context valid；`build/evidence/treehouse/runtime-status-ui-import-recovery-2026-08-12.json` |

### Canonical v0.4 six-asset import

源目录始终只读，六件固定 hash 与 `SHA256SUMS` 均通过。Treehouse 映射为：ontology 进入 `OntologyVersion.content`；SHACL 进入 RDF binding `userShacls`；valid JSON-LD 进入 example；context、README、checksum manifest 进入 message-model version documentation。由于上游 MIME detector 无法下载无扩展名附件，checksum manifest 在 Treehouse 中命名 `SHA256SUMS.txt`，其 bytes/hash 仍与 canonical `SHA256SUMS` 完全一致；恢复与零 DB 引用的孤儿文件清理记录在 `v0.4-import-mime-storage-recovery-2026-08-12.json`。

| 工件 | canonical SHA-256 | Treehouse 映射与验证 |
|---|---|---|
| `building-energy-ontology.ttl` | `c2139583d8b2c92fbd805db49f9a30e883c1aea27cb704063c3ea9d0456df5d9` | content byte hash `PASS`；32 triples；classes endpoint `PASS`；TTL export 32 triples 且 RDF-isomorphic `PASS` |
| `data-product-metadata-shapes.ttl` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` | RDF binding `userShacls` download hash `PASS` |
| `data-product-context.jsonld` | `f46d3056239cc1cb7d678707e749b33e336564e5fce23ffcccd528eae6cbe391` | documentation download hash `PASS` |
| `data-product-valid.jsonld` | `9acc287ae274e549becd15852231b325c43e1dbddc14e9f2459f4c490420f239` | example raw endpoint hash `PASS` |
| `README.md` | `388e4dd823c60b55772946eb7fa37e90c2e5cf52e8300b784bba29ae4364873c` | documentation download hash `PASS` |
| `SHA256SUMS` | `66cd79dd5cd05299c6a07010b087b4da87b138045223aa39449548ea7c46484a` | Treehouse `SHA256SUMS.txt` download hash `PASS`；bytes unchanged |

导入后的唯一 inventory 为一个专用 project、两个 specifications/two versions、一个 RDF binding、四个 FileObjects 与一个 example。message model 关联 ontology version，root class 为 `dcat:Dataset`；binding 五个 validator/schema/business/codelist flags 均为 false。当前运行闭包没有 SHACL validator 服务，因此 SHACL attachment/import 为 `PASS`，Treehouse SHACL validator execution 保持 `NOT RUN`。

首次 30 秒导入请求在 Windows Python 对 chunked collection response 的读取处超时，`v0.4-import-timeout-error-2026-08-12.json` 保留该真实失败。传输层改为 gzip + bounded incremental read 后完成幂等恢复。另一次 checksum 下载暴露上游 MIME limitation，原始 500 与恢复 evidence 均保留。最终首次成功 evidence 为 `build/evidence/treehouse/v0.4-import-2026-08-12.json`（SHA-256 `561bbe99db541eb955fc07a2a422326af2e0f2cc9edc21bde75aabc9b33ee98c`）。

仅 app 被再次 force-recreate，DB container ID 不变、两个 volumes 保留、删除数为 0；`runtime-app-restart-persistence-2026-08-12.json` 为 `PASS`。重启后导入器对 project、ontology content、message model、三份 docs、binding config、SHACL 与 example 全部报告 `reused`，source immutability 与 RDF-isomorphic round-trip 再次 `PASS`；`build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json` SHA-256 为 `3e36cc658ff5bde8c341b8f40a7b785b7173461e7ee151487cabe354330c51fb`。同一 Edge session 重载后仍可见登录态、ontology v0.4 与 Export control。

### Phase 07 文档真实性投影与最终回归

用户具名批准按 Phase 07 路由最小更新 `scripts/check_documentation.py` 与六份 Treehouse current-status 文档。checker 现在要求 current UI/import/export 为 `PASS`，publication 与 SHACL validator execution 为 `NOT RUN`；historical table 继续要求旧时点的 `BLOCKED` / `NOT DEPLOYED` / `NOT RUN`，并保留和扩充 negative controls。canonical normal check 为 13 documents / 2 diagrams / 0 issues；self-test 为 83/83。

| 命令 | 最终结果 |
|---|---|
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Suite all` | exit 0；17/17；`program_status=SUCCESS` |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1` | exit 0；bootstrap、doctor 与 17/17 `all` 通过 |
| `.\.venv\Scripts\python.exe scripts\verify_frozen_files.py` | exit 0；104/104 |
| `.\.venv\Scripts\python.exe scripts\doctor.py --profile host` | exit 0；overall `PASS` |
| `.\.venv\Scripts\python.exe -I scripts\check_documentation.py` | exit 0；13 documents / 2 diagrams / 0 issues |
| `.\.venv\Scripts\python.exe -I scripts\check_documentation.py --self-test` | exit 0；83/83 |
| `.\.venv\Scripts\python.exe -I scripts\check_treehouse_compose.py --self-test` | exit 0；45/45 |
| PowerShell AST、`bash -n`、WSL `sh -n`、24 个 shell Python heredocs、`git diff --check` | 全部 `PASS` |

新增增量索引为 `build/phase-08/optional-evidence-index-ui-import-recovery-2026-08-12.json`；原 `optional-evidence-index.json` 保持历史 bytes。8 个 current evidence 的 secret/path/cookie scan 为 0 findings，见 `ui-import-evidence-scan-2026-08-12.json`。未执行 SHACL validator、browser form-based import、publication、Git commit、push、tag、release 或远程 workflow；成功运行态保持 `RUNNING`。

## Phase 08 Semantic Treehouse SHACL validator 与暂停 addendum — 2026-08-12

本 addendum 记录用户随后批准的 validator 部署、真实 SHACL 执行、幂等复验与安全暂停。前文全部 `NOT RUN`、`RUNNING`、`STOPPED`、`BLOCKED` 和 build failure 内容继续作为对应时点的历史记录。当前投影为：

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`。

### Validator 固定输入与安全边界

上游 validator manifest 固定为 `europe-west4-docker.pkg.dev/sacred-sol-99413/sth-public/shacl-validator@sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`。派生 image ID 为 `sha256:54f94cfc085c530ff07989c283ee4511710f91b0f61affe3162266fd929b6492`，以 UID/GID `65532:65532` 运行。validator 只连接 project-scoped internal network，不发布宿主端口，不使用 bind mount；rootfs 只读，全部 Linux capabilities 被移除，启用 `no-new-privileges`，资源上限为 512 MiB、1 CPU、128 PIDs。应用继续只有 `127.0.0.1:18014:80` 的 loopback binding，数据库无宿主端口。验证请求和响应 payload、cookie/session、container environment 与 secrets 均未写入证据，canonical sources 保持只读。

EasyRDF 的 Turtle→RDF/XML serialization 对四个 `sh:pattern` literal 产生 lexical-form drift。受限 local-review 派生 app 补丁只在 `includeGeneratedSchema=false` 时向 validator 传递 raw canonical user SHACL Turtle；补丁前后 PHP 文件 SHA-256 分别为 `fe57919b417be57aaa0721ac39fb553bdf3039b70bb967ea04f0939be8acf657` 与 `a2d16768bac59bbd217e12ca3c6c2789063987717d17bccaf845c4a417463964`。源 shape 与送验 shape 均为 179 triples，canonical SHACL SHA-256 保持 `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`。

### SHACL 正控、负控与幂等复验

Treehouse RDF binding 仅将 `validatorEnabled` 与 `validateSchema` 更新为 `true`，其 user SHACL、example 与其余 validator flags 保持不变。相对 JSON-LD context 在内存中展开，working copy 未落盘；展开前后均解析为 13 triples 且 RDF-isomorphic。canonical valid example 的正控返回 HTTP 200、`syntax_valid=true`、`schema_valid=true`、零 schema errors。负控只在内存中删除 `datasetId`，返回 HTTP 200、`syntax_valid=true`、`schema_valid=false` 和一个 violation。第二次执行复用既有 binding，正控与负控的结果及 response hashes 均与首次一致。

| 证据 | 结果 | SHA-256 |
|---|---|---|
| `build/evidence/treehouse/shacl-validator-execution-2026-08-12.json` | 首次真实 Treehouse API SHACL 正控/负控均 `PASS` | `c2ac94e0f9a95a903baa71d72fcc0031b206b7740d4235b97f8271b7526001f3` |
| `build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json` | binding `REUSED`，幂等复验 `PASS` | `36c8226d0918c5961b45866a8bf023a194ae46c153d0d55ef811e7023d4229df` |
| `build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json` | 安全暂停与持久化保留 `PASS` | `9d95565d852694368544e50c293b80113428730c414a9f342df35b84758cf11a` |

新增脱敏扫描 `build/evidence/treehouse/shacl-validator-evidence-scan-2026-08-12.json` 为 `PASS`、0 findings，SHA-256 为 `6c41740f04b49580e7193f88b19dd05652c398beb699b3ad0bb4ea5c4c289601`；扫描确认 cookie/session、完整 validator request、绝对本地路径和 5 个 synthetic secret values 均未进入三份证据。增量索引为 `build/phase-08/optional-evidence-index-shacl-validator-2026-08-12.json`；前两个 optional evidence indices 保持原 bytes。

### 当前暂停状态

完成验证后依次停止 application、SHACL validator、database。三个 container 均保留且为 exited；project 的 ingress、database internal、validator internal networks 均保留；`dssc-semantic-treehouse-v04-sth-app-data` 与 `dssc-semantic-treehouse-v04-sth-db2-data` 两个 named volumes 均存在。操作未删除 container、network 或 volume，也未执行 prune。暂停后 `127.0.0.1:18014` 不可达，符合 `PAUSED` 边界。publication、Git commit、push、tag、release 与远程 workflow 仍未执行。

用户已批准沿 Phase 07 路由更新 checker 与六份 current-status 投影。`scripts/check_documentation.py` 现在强制要求 `current runtime=PAUSED`、`SHACL validator execution=PASS`、`publication=NOT RUN`，并要求三份新 evidence 与 validator digest、安全边界、正负控/幂等复验/EasyRDF 四 pattern local-review patch、PAUSED 持久化 token 各出现一次。historical status 规则保持原值。canonical normal check 为 14 documents / 2 diagrams / 0 issues；self-test 为 90/90，包含状态降级、证据替换与运行边界漂移负控。Python compile 与 `git diff --check` 通过。

### 收尾回归与最终只读核对

| 检查 | 最终结果 |
|---|---|
| `.\.venv\Scripts\python.exe scripts\verify_frozen_files.py` | exit 0；104/104 |
| `.\.venv\Scripts\python.exe scripts\doctor.py --profile host` | exit 0；overall `PASS` |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Suite all` | exit 0；`program_status=SUCCESS`；预期负向 fixture 的无效 dateTime 诊断未改变套件成功结论 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1` | exit 0；bootstrap、host doctor 与 `all` suite 均通过 |
| `.\.venv\Scripts\python.exe -I scripts\check_documentation.py` 双跑 | 两次 exit 0；14 documents / 2 diagrams / 0 issues；结果 bytes 一致 |
| `.\.venv\Scripts\python.exe -I scripts\check_documentation.py --self-test` 双跑 | 两次 exit 0；90/90；结果 bytes 一致 |
| `.\.venv\Scripts\python.exe -I scripts\check_treehouse_compose.py --self-test` 双跑 | 两次 exit 0；45/45；stdout bytes 一致 |
| canonical raw Compose preflight closeout | 预期 exit 1；`BLOCKED`；33 blocking / 46 review；`execution_authorized=false` |

raw preflight closeout 写入新文件 `build/evidence/treehouse/preflight-shacl-validator-closeout-2026-08-12.json`，SHA-256 为 `1d0f4dfdabbce77ba8b10bc1995293e03e905516c645c454695edc8e16cce49c`；该 hash 与历史 `preflight.json` 完全一致，历史文件未被覆盖。增量 evidence index SHA-256 为 `62c06cd0f1144ebbdc7a35dd6bcf30133dbf74bb9022594df342089da884755f`，其中 4/4 evidence hashes 均匹配。

最终只读 Docker 核对确认 application、validator 与 database 三个 container 均为 `exited`，restart policy 均为 `no`，`127.0.0.1:18014` 的监听数为 0；两个 named volumes 与三个 project networks 全部保留。固定 upstream checkout 为 detached clean，HEAD 精确匹配 `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf`，9 个 locked source hashes 全部匹配。收尾回归期间服务始终保持 `PAUSED`；未执行 Git commit、push、tag、release、远程 workflow 或外部 publication。

## Phase 08 recovery addendum — documentation clean-room allowlist（2026-08-12）

- 结论：`COMPLETE`
- 触发：Phase 09 §6.5 在 Docker validation container 上执行默认 `all` 时，`all.documentation` 失败；host `all` 与 standalone documentation 均通过。
- 人工授权：维护者批准四点最小修复——补 `GENERATED_OUTPUT_PATHS`、修复 user_guide 对 lock 的链接表述、允许 tracked `upstream.lock.json` 进入 clean-room 镜像、重跑 host `all` + Docker no-cache + compose `all` 后从 Phase 09 §6.5 重验。
- **不**要求重启 Semantic Treehouse 服务；Treehouse 保持 `PAUSED` 历史状态；未重跑 Treehouse workload。

### 根因

1. Phase 08 SHACL addendum 将三份 ignored 运行证据路径写入文档，但未同步列入 `GENERATED_OUTPUT_PATHS`；host 磁盘存在这些文件时通过，compose 空 `build/` 挂载时 `REFERENCE_PATH_MISSING`。
2. user_guide 使用 Markdown 链接指向 `tools/semantic-treehouse/upstream.lock.json`，而 `.dockerignore` 排除 `tools/semantic-treehouse/**`（仅保留 README），镜像内无 lock → `BROKEN_LINK`。
3. SHACL 收尾回归只重跑了 host `all`/documentation，未重跑 Docker clean-room `all`。

### 最小修改集

| 路径 | 变更 |
|---|---|
| `scripts/check_documentation.py` | `GENERATED_OUTPUT_PATHS` 增加 `build/evidence/treehouse` 与三份 SHACL evidence 路径 |
| `.dockerignore` | 增加 `!tools/semantic-treehouse/upstream.lock.json`（tracked 权威锁进入镜像；upstream clone 仍排除） |
| `C_Semantic_Treehouse/C_semantic_treehouse_user_guide.md` | 去掉对 lock 的相对 Markdown 链接，改为 plain path 表述，并明确 upstream 检出目录为可选外部材料 |

| 路径 | 修复后 SHA-256 |
|---|---|
| `scripts/check_documentation.py` | `77f6f7eecfb1347548e8becb67acc9e2e9b7c372460400406af696f5b42abcc6` |
| `.dockerignore` | `87b8b68708b21dcf4068854499958c1ec67de1421b83135b2f53a9bdf6cab7e0` |
| `C_Semantic_Treehouse/C_semantic_treehouse_user_guide.md` | `3d48b9be194422b563d567207d74776e4f11f38b8bafecb800178818c2a62ac3` |

### 复验

| 检查 | 结果 |
|---|---|
| host `check_documentation.py` | exit 0 |
| host `check_documentation.py --self-test` | exit 0；90/90 |
| host `validate.ps1 -Suite all` | exit 0；17/17 SUCCESS；result SHA-256 `36c687e90a453dfb741de05e3a5fb8dbaae56abd5030fb29012f4ecd4664578a` |
| Docker `build --no-cache` | exit 0；image `sha256:b8f401ef9f47ecf5b270a73643f6f4cbd822817eaefc81e8d78b4c52cb4449d2`；镜像内可见 `upstream.lock.json` |
| Docker compose default `all` | exit 0；17/17 SUCCESS，含 `all.documentation`；result SHA-256 `775a226e0fade94fe7c89343c3094c7a3fa660aaf5104d003168251d5a2f54a8`；contract `1.6.0` / `09c74417…d51836` |

未修改 validation-suites 合同、`scripts/validate.py`、reproduce 脚本、模型/fixtures/oracle。本 addendum 追加于历史 Phase 08 小节之后；原 COMPLETE 与 Treehouse 可选轨状态不改写。

## Phase 09 — 最终 QA、Clean Clone 与发布就绪（IN_PROGRESS）

- 开始日期：2026-08-12（Asia/Shanghai）。
- 阶段整体结论：COMPLETE（§6.1–§6.11 已完成；候选 SHA / CI 三 job / 远程 clean clone 已确认）。
- 工作树基线 HEAD（进入本 Phase 时）：`b7115c800ae4feebc045dcddfbc831a0261c208d`。
- 本阶段未修改 `validation-suites.json`、`validation-suites.schema.json`、`scripts/validate.py` 或 Phase 08 的 `scripts/reproduce.ps1` / `scripts/reproduce.sh`。
- §6.5 阻塞修复按维护者授权在 Phase 08 recovery addendum 完成；修复后 Docker clean-room `all` 已通过。
- §6.7 复验前对 §6.1–§6.6 的只读核验：三 checker exit 0；validation-suites/core evidence/reproduce 脚本 hash 与 STATUS 记录一致；负控摘要 12/12、10/10、11/11。

### §6.1 冻结并验证 Validation-Suites 合同 — COMPLETE

| 项 | 值 |
|---|---|
| 结论 | `COMPLETE` / `PASS` |
| `contract_version` | `1.6.0` |
| registry SHA-256 | `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836` |
| schema SHA-256 | `70d436cd0509da2fcec8b602c1bffc5f00490d24c13c2ee47caf84791199802a` |
| Phase 08 对照 | 与 Phase 08 记录的 `1.6.0` / `09c74417…d51836` **完全一致** |
| 公开 suite 集合与顺序 | `frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all` |
| `all` depends_on | 上述六个非 `all` suite 的固定顺序 |
| `all` 自有 components | `all.composition`、`all.semantic-sparql`、`all.quality`、`all.governance`、`all.documentation` |
| `all` 展开 component 数 | 17（六个 constituent + 五个 `all.*`） |
| 双向核对 | registry ↔ `PUBLIC_SUITE_IDS` ↔ `checks_all` 期望 composition ↔ `validate.py` owner_phase ↔ entrypoint catalog 全通过（15/15） |
| 负例控制 | 12/12 全部 fail-closed（临时副本仅写 `build/phase-09/negative-controls/validation-suites/`） |

#### 负例覆盖（reason codes）

| Case ID | reason_code | 结果 |
|---|---|---|
| `zero-suites` / `semantic-zero-suites` | `ZERO_SUITES` | PASS |
| `zero-components` / `expand-zero-components` | `ZERO_COMPONENTS` | PASS |
| `duplicate-suite-id` | `DUPLICATE_SUITE_ID` | PASS |
| `unknown-suite-cli` | `UNKNOWN_SUITE`（`validate.py --suite not-a-public-suite` 非零退出） | PASS |
| `unknown-entrypoint` / `missing-implementation-dependency` / `missing-registry-file` | `UNKNOWN_ENTRYPOINT` / `MISSING_IMPLEMENTATION` / `MISSING_REGISTRY` | PASS |
| `missing-or-wrong-report-dir` | `MISSING_REPORT_PATH`（错误 evidence 目录被 `is_exact_phase_build_dir` 拒绝） | PASS |
| `all-drop-required-component` / `all-drop-composition-component` | `ALL_REQUIRED_COMPONENT_REMOVED`（相对 `EXPECTED_ALL_COMPONENTS` 的 composition gate） | PASS |

#### 机器证据（ignored）

| 路径 | SHA-256 |
|---|---|
| `build/phase-09/6_1-freeze-and-audit.json` | `730b811d595c071893e056acb09f8f7267d86dbe913a55b7a39f8e677ff6424c` |
| `build/phase-09/6_1-contract-audit.json` | `246bbc2c8e6e49f1c6ee8e01d22af3d9c333b40756f18a7d284dad34e7ecf231` |
| `build/phase-09/negative-controls/validation-suites/summary.json` | `a2ddb131f036c67dfb9e781e2660adedc525c85dafa0282b6e9b52dca452af65` |
| `build/phase-09/6_1-freeze-and-audit.md` | `627577d336a7f42729ddafc293a62fdb5d086f534464ac3bacab504ff47544c1` |
| runner：`build/phase-09/tools/run_phase09_6_1_contract_audit.py` | `1c80f648b173b11139951a4cec3727b4390a5d9981412fc482efb127d7c07871` |

#### §6.1 对后续步骤的冻结绑定

后续 §6.2 `deliverables.json` 与 §6.6 `core-results.json` 必须引用：

- `contract_version` = `1.6.0`
- registry path = `C_Semantic_Treehouse/manifests/validation-suites.json`
- registry SHA-256 = `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`
- schema 作为普通 deliverable 单独记录 hash = `70d436cd0509da2fcec8b602c1bffc5f00490d24c13c2ee47caf84791199802a`

报告路径合同（只读确认）：`build/phase-{active}/current/suite-{suite}-{profile}.{result.json,machine.json,md}`；失败语义：unknown suite → exit 2，registry/component 失败 → exit 1，成功 → exit 0。

### §6.2 建立最终 Deliverables Manifest — COMPLETE

| 项 | 值 |
|---|---|
| 结论 | `COMPLETE` / `PASS` |
| schema | `C_Semantic_Treehouse/manifests/schemas/deliverables.schema.json` |
| schema SHA-256 | `4b20e76483ee9a04cadc6ce105d998916d3abb90bb8c7648eaa7b4842ec287a8` |
| manifest | `C_Semantic_Treehouse/manifests/deliverables.json` |
| entry count | 初建 445；§6.3 落地两个 checker 后再生为 **447**（排除自身；覆盖全部当前 tracked candidate + Phase 09 新增候选文件） |
| checker | `scripts/check_deliverables.py` |
| checker SHA-256 | `ca0523e696a07e14d39f53d232886d5c5e5482e2410e9fb2b93aec5e5df73383` |
| evidence-index skeleton | `C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json`（§6.6 再定稿 core-results 绑定） |
| evidence-index SHA-256 | `07a8b7395c531353e74b1fb665b3c44ca247a88028c190134eec1b0655f135e6` |
| validation-suites 绑定 | `contract_version=1.6.0`；manifest SHA-256=`09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`（与 §6.1 / Phase 08 一致） |
| 正式检查 | `check_deliverables.py` exit 0；issue_count=0（§6.3 再生后仍 exit 0） |
| 负例控制 | 10/10 全部 fail-closed（临时副本仅写 `build/phase-09/negative-controls/deliverables/`） |
| 当前 runtime SHA-256（ignored only） | 以最新 `check_deliverables.py` / `check_evidence_freshness.py` 结果为准（§6.3 后随 STATUS 再生；不嵌入固定自引用） |

#### 自引用隔离

- `deliverables.json` **不**列出自身，也 **不**嵌入自身 hash。
- checker **不**硬编码 `deliverables.json` 的预期 hash；其 runtime SHA-256 只写入 ignored 证据 `build/phase-09/6_2-deliverables-check.json` 的 `stats.deliverables_runtime_sha256`。
- schema、`check_deliverables.py`、`evidence-index.json` 作为普通 deliverable 记录实际 SHA-256。
- required-files 存在性/hash 检查只消费 `deliverables.json`，不在 checker 内维护第二套 required 文件名清单；coverage anchors 仅验证“必须被清单列出”。

#### 许可证决策（中期）

在 §6.8 维护者正式决定前，manifest 使用明确的 INTERIM / KNOWN_SOURCE decision ID，而非静默省略：

| decision_id | status | 用途 |
|---|---|---|
| `DEC-P09-INTERIM-NOASSERTION` | INTERIM | 仓库候选整体 SPDX 暂为 `NOASSERTION` |
| `DEC-SCENARIO-CC-BY-4.0` | KNOWN_SOURCE | `inputs/original-plan/**` 场景数据 CC-BY-4.0（仅约束场景数据） |
| `DEC-P09-D-GROUP-PENDING` | INTERIM | D 组材料与 byte-copy Shape 再分发待 §6.8 |
| `DEC-P09-SOURCE-ZIP-PENDING` | INTERIM | 来源 ZIP 再分发与 ZIP 内历史路径风险待 §6.8 |

#### 负例覆盖（reason codes）

| Case ID | reason_code | 结果 |
|---|---|---|
| `duplicate-id` | `DUPLICATE_ID` | PASS |
| `case-path-collision` | `CASE_PATH_COLLISION` | PASS |
| `path-escape` | `PATH_ESCAPE` | PASS |
| `absolute-path` | `ABSOLUTE_PATH` | PASS |
| `missing-file` | `MISSING_FILE` | PASS |
| `empty-file` | `EMPTY_FILE` | PASS |
| `stale-hash` | `STALE_HASH` | PASS |
| `unknown-role` | `UNKNOWN_ROLE`（schema 亦拒绝） | PASS |
| `missing-license-decision` | `MISSING_LICENSE_DECISION` / `NOASSERTION_WITHOUT_DECISION` | PASS |
| `empty-entries` | `EMPTY_ENTRIES` | PASS |

#### 机器证据（ignored）

正式结果与负例摘要写在 `build/phase-09/`（gitignored）。稳定 tracked 产物 hash 见上表 schema/checker/evidence-index 行；`deliverables.json` 自身 runtime hash 只出现在 ignored check report 中。

| 路径 | 角色 |
|---|---|
| `build/phase-09/6_2-deliverables-check.json` | 正式 checker 机器结果（ok=true, issue_count=0） |
| `build/phase-09/6_2-deliverables-audit.json` | §6.2 汇总审计 |
| `build/phase-09/6_2-deliverables-audit.md` | §6.2 人读摘要 |
| `build/phase-09/negative-controls/deliverables/summary.json` | 10/10 负例摘要 |
| `build/phase-09/tools/generate_deliverables_manifest.py` | manifest 生成器（可重跑） |
| `build/phase-09/tools/run_phase09_6_2_deliverables_controls.py` | 负例 runner（可重跑） |

#### §6.2 对后续步骤的约束

- §6.3 起的 publication-safety / evidence-freshness 检查可绑定 deliverables runtime hash，但不得把该 hash 回写进 tracked `deliverables.json`。
- 任何候选文件增删或内容变化后，必须重新运行 generator 更新 `deliverables.json`，再跑 `check_deliverables.py`。
- §6.6 更新 `evidence-index.json` / core evidence 后必须再生 deliverables。
- §6.8 许可证/再分发正式决定后，必须把 INTERIM decision 升级为 APPROVED/DENIED，并再生 deliverables。

### §6.3 建立最终安全、隐私和 Freshness 检查 — COMPLETE

| 项 | 值 |
|---|---|
| 结论 | `COMPLETE` / `PASS` |
| publication safety checker | `scripts/check_publication_safety.py` |
| publication safety SHA-256 | `4a3a05ba09978814bb7d844d579142ffd2968ac8d32d039b37228ccb914606e6` |
| evidence freshness checker | `scripts/check_evidence_freshness.py` |
| evidence freshness SHA-256 | `97ae1bdaba99217cae9cac1d018bdd93c3fdee54ffb0e31182e10d8ec2606993` |
| 正式检查 | 两者均 exit 0；`issue_count=0` |
| 负例控制 | 11/11 全部 fail-closed（仅写 `build/phase-09/negative-controls/scanners/`） |
| 依赖边界 | 仅标准库 + Phase 01 lock 已声明依赖；由仓库 `.venv` 以 `-I` 运行；无临时 `pip install` |
| validation-suites 绑定 | `1.6.0` / `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836` |
| lock 绑定 | `requirements.lock` SHA-256 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2` |
| deliverables runtime（ignored only） | 447 entries；runtime SHA-256 仅写入 `build/phase-09/6_2-deliverables-check.json` / freshness 结果，不回写 tracked 文档 |

#### Publication safety 覆盖

- ZIP **外** tracked 文本：Windows 用户目录绝对路径、POSIX home 绝对路径；主机临时目录环境变量/展开 token；私钥 PEM 头、高置信 token、credential 型 env 赋值。
- 禁止 tracked 的 secret/cache/macOS 文件名与 `tools/semantic-treehouse/upstream/**` 被跟踪。
- 两份来源 ZIP：文件名、size、SHA-256 与批准值一致；ZIP **内**含个人绝对路径的条目 **仅** 可通过 `docs/provenance/manifests/privacy-exclusions.tsv` 具名 allowlist 放行（无全局 ignore 旁路）。
- Git 作者清单 + 近 200 条 commit message 敏感内容扫描；作者身份正式决定仍属 §6.8。
- tracked 树大小/大文件、`.gitattributes`（`eol=lf` + source-archives `-text`）、shell 脚本 git mode `100755`、`.github/workflows/validate.yml` 的 `permissions.contents: read`。
- deliverables 中 D 组 / 来源 ZIP / 场景 CC-BY-4.0 / 仓库级 INTERIM `NOASSERTION` 决策 ID 存在性。

#### Evidence freshness 覆盖

- 四个上游 manifests 存在且非空，并与 `deliverables.json` 中记录 hash 一致。
- 当前 validation-suites `contract_version`/`manifest_sha256` 与 Phase 08/§6.1 冻结值一致；`deliverables.json` 内声明的 suites 绑定同步校验。
- `requirements.lock` 绑定 Phase 01 固定 hash。
- 核心 validator/harness/Phase 09 checker 源文件 hash 记入结果。
- `evidence-index.json` 中全部 `*.result.json`：artifact/input hash、manifest/lock 绑定复核；历史 harness `source_hashes` 作为执行时代指纹保留，**不**强制与当前磁盘相等（除非证据声明 `source_hash_policy=must-match-disk`）。

#### 负例覆盖（reason codes）

| Case ID | reason_code | 结果 |
|---|---|---|
| `secret-canary` | `SECRET_CANARY` | PASS |
| `windows-user-path` | `WINDOWS_USER_PATH` / `PERSONAL_ABSOLUTE_PATH` | PASS |
| `posix-home-path` | `POSIX_HOME_PATH` / `PERSONAL_ABSOLUTE_PATH` | PASS |
| `env-canary` | `ENV_CREDENTIAL`（兼 `SECRET_CANARY`） | PASS |
| `private-key-header` | `PRIVATE_KEY_MATERIAL` | PASS |
| `zip-global-ignore-rejected` | `WINDOWS_USER_PATH`（证明全局 ignore 声明不能放行） | PASS |
| `stale-input-hash` | `STALE_INPUT_HASH` | PASS |
| `stale-report-hash` | `STALE_REPORT_HASH` | PASS |
| `wrong-validation-suites-hash` | `WRONG_VALIDATION_SUITES_HASH` | PASS |
| `expired-evidence` | `EVIDENCE_EXPIRED` | PASS |
| `old-manifest-evidence` | `EVIDENCE_OLD_MANIFEST` | PASS |

#### 机器证据（ignored）

| 路径 | 角色 |
|---|---|
| `build/phase-09/6_3-publication-safety.json` | 正式 safety 结果（ok=true） |
| `build/phase-09/6_3-evidence-freshness.json` | 正式 freshness 结果（ok=true） |
| `build/phase-09/6_3-scanners-audit.md` | §6.3 人读摘要 |
| `build/phase-09/negative-controls/scanners/summary.json` | 11/11 负例摘要 |
| `build/phase-09/tools/run_phase09_6_3_scanner_controls.py` | 负例 runner（可重跑） |

#### §6.3 对后续步骤的约束

- §6.4 只读复核 `scripts/reproduce.ps1` / `reproduce.sh`，不修改 Phase 08 脚本。
- 候选文件再变化时：再生 deliverables → `check_deliverables.py` → 两个 §6.3 checker。
- 不得把 deliverables runtime hash、当前 HEAD/CI run 写回 tracked 发布证据（§6.6/§6.11 规则）。

### §6.4 只读复核 Phase 08 一键复现入口 — COMPLETE

| 项 | 值 |
|---|---|
| 结论 | `COMPLETE` / `PASS` |
| 范围 | 只读复核；**未**修改 `scripts/reproduce.ps1`、`scripts/reproduce.sh` 或 bootstrap/validate 包装器 |
| `scripts/reproduce.ps1` | tracked；1637 bytes；mode `100644`；SHA-256 `761ef0a4ddfa5f58a7e679767f2f31b153efafa78138fd4104b3d1dbaa15a1d7` |
| `scripts/reproduce.sh` | tracked；568 bytes；mode `100755`；SHA-256 `c6dd3e3d3ea3af4e341ab4fcf8bfd4a0371f1997fa813e50e966f81ba60505dd` |
| Phase 08 hash 对照 | 与 `build/phase-08/linux-v8-final/windows-export-evidence/source-manifest.json` 及 deliverables 条目 **完全一致** |
| PowerShell 合同 | `#Requires -Version 5.1`；`param()` 无参数；`$PSScriptRoot` 解析仓库根 |
| Linux shell 合同 | `set -euo pipefail`；`BASH_SOURCE` + `pwd -P` 解析仓库根；`bash -n` exit 0 |
| validation-suites 绑定 | 运行 `all` 后 result 记录 `contract_version=1.6.0`、registry SHA-256=`09c74417…d51836`（与 §6.1 / Phase 08 一致） |

#### 委托链（静态证明）

1. **仓库根解析**：脚本从自身位置解析根目录，不依赖调用时 CWD；支持经绝对路径调用（空格 / 非 ASCII CWD 实测 arg-reject 路径）。
2. **Bootstrap**：分别调用 `scripts/bootstrap.ps1` / `scripts/bootstrap.sh`；严格消费 `requirements.lock` 与 `requirements-bootstrap.lock`（`--require-hashes`）；创建或复用仓库 `.venv`；以 `.venv` Python `-I` 运行 `doctor.py --profile host`。
3. **Validation**：分别调用 `validate.ps1 -Suite all` / `validate.sh --suite all`；显式使用仓库 `.venv` Python `-I`、`--profile host`；不回落到全局 Python。
4. **`all` composition**：固定 validation-suites 合同中的 `all`；不含可改 composition 的参数；不 skip；不自动重写 expected files。
5. **退出码**：bootstrap 非零则立即返回；否则返回 validate 退出码；多余参数 exit 2。

`doctor` 与 frozen 校验分别经 bootstrap 与 `all` 展开的 `frozen.manifest` component 执行（本轮 Windows 实跑均 SUCCESS）。

#### 运行时证明

| 证明项 | 结果 |
|---|---|
| Windows `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1` | **exit 0** |
| suite=`all` | `program_status=SUCCESS`；counts discovered/executed/passed/failed/skipped = **17/17/17/0/0** |
| 组件（17） | `frozen.manifest`、`environment.doctor`、`baseline.reproduction`、`traceability.contract-audit`、`v0.4-model.release-contract`、6×`v0.4.*`、`all.composition`、`all.semantic-sparql`、`all.quality`、`all.governance`、`all.documentation` 全部 SUCCESS |
| suite result | `build/phase-05/current/suite-all-host.result.json`（`all` 的 owner_phase=`05`，路径符合 Phase 01 恢复合同） |
| suite result SHA-256 | `98f6ba9b08ccbfe31d70a72831386f6cb077bd10fc99f8eac5c75f47db6fc740` |
| lock 绑定 | `requirements.lock` SHA-256 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2` |
| `reproduce.ps1` 多余参数 | exit **2** |
| `reproduce.sh` 多余参数（Git Bash） | exit **2** |
| 外部 CWD（`build/phase-09/path-space test/中文`）+ 绝对脚本路径 arg-reject | exit **2** |
| `bash -n` reproduce/bootstrap/validate.sh | 各 exit **0** |
| Linux 全量 `./scripts/reproduce.sh` | §6.4 **未重跑**；脚本字节与 Phase 08 一致；Phase 08 clean-room `linux-v8-final` 在含空格路径下 native reproduce exit 0（`harness-result.json` status=PASS） |

#### 联网 / 离线边界

- **首次 bootstrap**：需要访问 PyPI（`https://pypi.org/simple`）按 hash lock 安装 bootstrap 与 runtime 依赖。
- **本轮运行**：复用已有 `.venv`（日志为 Requirement already satisfied）；pip 重校验过程中出现瞬时 SSL 重试警告，**未导致失败**。
- **doctor + 核心 suite**：依赖安装完成后不依赖业务网络。
- **幂等**：重复运行在既有 `.venv` 上应保持 package 集合与确定性 suite 结果稳定；完整确定性复跑矩阵留给 §6.5。

#### README 单命令（§6.7 写入；§6.4 不改 README）

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

```bash
./scripts/reproduce.sh
```

Phase 09 的 deliverables / publication-safety / evidence-freshness 检查在一键复现成功后由本阶段命令**分开**执行，不并入 reproduce 脚本。

#### 机器证据（ignored）

| 路径 | 角色 |
|---|---|
| `build/phase-09/6_4-reproduce-entry-audit.json` | §6.4 机器审计（status=PASS） |
| `build/phase-09/6_4-reproduce-entry-audit.md` | §6.4 人读摘要 |
| `build/phase-09/6_4-reproduce-ps1.stdout.log` / `.stderr.log` / `.exit-code` | Windows 实跑日志 |
| `build/phase-09/6_4-ps1-arg-reject.*` / `6_4-sh-arg-reject.*` | 参数拒绝证据 |
| `build/phase-09/6_4-path-cwd-arg-reject.*` | 空格/非 ASCII CWD 路径证据 |
| `build/phase-09/tools/write_6_4_audit.py` | 审计生成器（可重跑） |
| Phase 08：`build/phase-08/linux-v8-final/harness-result.json` | Linux reproduce.sh clean-room 上游证据 |

#### §6.4 对后续步骤的约束

- §6.5 起可在当前工作区与 clean clone 中重复运行上述单命令，并追加 Phase 09 三个 checker / documentation / CI / Docker 矩阵。
- 若任一 reproduce 脚本缺失、hash 与 Phase 08 不符、接口不完整或行为失败，必须回到 Phase 08 修复并重新验收到本阶段；Phase 09 **不得**修补这些脚本。
- 最终 README 只登记上述两条已存在命令，不新建或编辑对应脚本。

### §6.5 从零运行全部本地核心验证 — COMPLETE

| 项 | 值 |
|---|---|
| 结论 | `COMPLETE` / `PASS` |
| 日期 | 2026-08-12 |
| validation-suites 绑定 | host 与 container 均 `contract_version=1.6.0` / registry SHA-256 `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836` |
| lock 绑定 | `requirements.lock` SHA-256 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2` |
| 上游恢复 | Phase 08 recovery addendum（documentation clean-room allowlist）完成后重验；**未**重启 Treehouse |

#### 对 §6.1–§6.4 的复验

| 小节 | 复验结论 | 备注 |
|---|---|---|
| §6.1 | `PASS` | registry/schema hash、负例目录与 audit 仍有效；合同零修改 |
| §6.2 | `PASS`（再生后） | schema/checker hash 不变；manifest 随候选文件变化再生 |
| §6.3 | `PASS` | publication-safety 与 evidence-freshness 均 exit 0 |
| §6.4 | `PASS` | reproduce 脚本 hash 不变；Windows 一键复现合同保持 |

#### Windows 主机（修复后正式结果）

| 命令 / 检查 | 退出码 | 结果 |
|---|---:|---|
| 首次 §6.5 `reproduce.ps1`（阻塞诊断轮） | 0 | suite `all` SUCCESS；当时 host result SHA-256 `98f6ba9b…fc740` |
| 修复后 `validate.ps1 -Suite all` | 0 | discovered/executed/passed/failed/skipped = **17/17/17/0/0** |
| 正式 host result | — | `build/phase-05/current/suite-all-host.result.json` SHA-256 `36c687e90a453dfb741de05e3a5fb8dbaae56abd5030fb29012f4ecd4664578a` |
| `check_deliverables` / `check_publication_safety` / `check_evidence_freshness` | 0 / 0 / 0 | issue_count=0 |
| `check_documentation` + `--self-test` | 0 / 0 | 14 documents / 2 diagrams；**90/90** |
| `check_ci` + `--self-test` | 0 / 0 | workflow policy PASS |

17 个 component 全部 `SUCCESS`（含 `all.documentation`）。`source_hash_issues=[]`；required skipped=0。预期负向 fixture 的非法 `dateTime` stderr 诊断不改变 suite 成功结论。

#### Docker / Linux validation container（修复后正式结果）

| 命令 | 退出码 | 结果 |
|---|---:|---|
| `docker compose … build --no-cache` | 0 | image `sha256:b8f401ef9f47ecf5b270a73643f6f4cbd822817eaefc81e8d78b4c52cb4449d2`；镜像含 tracked `upstream.lock.json` |
| compose 默认 `--suite all` | **0** | `program_status=SUCCESS`；counts **17/17/17/0/0** |
| container result | — | `build/ci/docker/phase-05/current/suite-all-container.result.json` SHA-256 `775a226e0fade94fe7c89343c3094c7a3fa660aaf5104d003168251d5a2f54a8` |
| `all.documentation` | SUCCESS | 与 host 同一 contract `1.6.0` / `09c74417…d51836` |

#### 诊断轮（已作废为 PASS 依据，仅作过程证据）

| 轮次 | 结果 | 证据 |
|---|---|---|
| 首次 Docker `all`（修复前） | exit 1；`all.documentation` ERROR | `build/phase-09/6_5-local-core-validation.json`（`BLOCKED_ON_DOCKER_DOCUMENTATION`） |
| Phase 08 最小修复 + 重验 | host/Docker 均 17/17 | 见上方正式结果与 Phase 08 recovery addendum |

#### 机器证据（ignored）

| 路径 | 角色 |
|---|---|
| `build/phase-09/6_5-recovery/local-core-validation-recovered.json` | 修复后 §6.5 正式机器审计（status=`PASS`） |
| `build/phase-09/6_5-recovery/*` | documentation/self-test、host all、Docker build/compose 日志与 exit codes |
| `build/phase-09/6_5-local-core-validation.json` | 修复前诊断（保留，不作为 PASS） |
| `build/phase-05/current/suite-all-host.result.json` | 正式 host suite 结果 |
| `build/ci/docker/phase-05/current/suite-all-container.*` | 正式 container suite 结果 |

### §6.6 固化无自引用的 Tracked 发布证据 — COMPLETE

| 项 | 值 |
|---|---|
| 结论 | `COMPLETE` / `PASS` |
| 日期 | 2026-08-12 |
| 范围 | 仅创建/更新第 5.1 节四个 release evidence 文件；未写入 commit SHA、CI run、remote-clone 或 deliverables 内容 hash |
| generator | `build/phase-09/tools/generate_core_release_evidence.py`（ignored，可重跑） |

#### Tracked 产物

| 路径 | SHA-256 | 角色 |
|---|---|---|
| `C_Semantic_Treehouse/evidence/releases/v0.4/core-results.json` | `869e8e94573216204bab1aefb5069aa81495532a4daa861410d6541b4bf06d40` | 上游 suite `all` 确定性聚合 |
| `C_Semantic_Treehouse/evidence/releases/v0.4/core-report.md` | `3dcd3160ecd7c89bf83f3a12f5b299a04e267c3cfe7235ca41fe0448dc3759c8` | 由 `core-results.json` 确定性渲染 |
| `C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json` | `1e41baeb5fb38ad2cb1a77cce1d2ac518e5aebc12d96cb9027c26168c9101898` | 稳定路径/role 索引（9 entries） |
| `C_Semantic_Treehouse/evidence/releases/v0.4/README.md` | `34c8c15418d1c99ee972e9d81be616331bb7ecc2227d9002f0d06ce81600827a` | 稳定内容说明 + push 后动态事实边界 |

#### `core-results.json` 绑定与 gate 摘要

| 绑定 | 值 |
|---|---|
| validation-suites | path=`C_Semantic_Treehouse/manifests/validation-suites.json`；schema path 已记录；`contract_version=1.6.0`；manifest SHA-256=`09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`；schema SHA-256=`70d436cd0509da2fcec8b602c1bffc5f00490d24c13c2ee47caf84791199802a` |
| 四个上游 manifests | release / baseline / requirements / v0.4-test-cases 均记录 path+SHA-256（与 freshness checker 一致） |
| lock | `requirements.lock` SHA-256 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2` |
| deliverables | **仅稳定 path** `C_Semantic_Treehouse/manifests/deliverables.json`；**不**嵌入 runtime hash |
| source_hashes | 39 个 validator/harness 源文件；`source_hash_issues=[]` |
| suite `all` gate | program_status=`SUCCESS`；counts **17/17/17/0/0**；required_skipped=0；17 components 全部 SUCCESS |
| host result content SHA-256 | `36c687e90a453dfb741de05e3a5fb8dbaae56abd5030fb29012f4ecd4664578a`（与 §6.5 正式结果一致） |
| container result content SHA-256 | `775a226e0fade94fe7c89343c3094c7a3fa660aaf5104d003168251d5a2f54a8`（与 §6.5 正式结果一致） |
| 平台一致性 | contract/registry/counts/source_hashes/component statuses 均 host==container |

#### 无自引用审计

明确 **排除** 并写入 `exclusions` 映射（值为 `excluded`，非真实绑定）：

- deliverables 内容 hash
- Phase 09 `check_deliverables` / `check_publication_safety` / `check_evidence_freshness` 自检结果
- 实时 timestamp 字段
- 当前 commit SHA
- CI run ID / URL
- remote-clone 绑定

`core-report.md` 由同一 generator 从 `core-results.json` 二次渲染比对，byte-identical。raw environment/logs 仍只留在 ignored `build/**`。

#### deliverables 再生与最终 QA 复验

| 步骤 | 结果 |
|---|---|
| `generate_deliverables_manifest.py` | entry count **449**（较 §6.3 的 447 增加 `core-results.json` + `core-report.md`） |
| deliverables runtime SHA-256（ignored only） | 以 `build/phase-09/6_6-postcheck-summary.json` / 最新 `check_deliverables.py` 结果为准；**不**回写 tracked 文件 |
| `check_deliverables.py` | exit 0；issue_count=0 |
| `check_publication_safety.py` | exit 0；issue_count=0 |
| `check_evidence_freshness.py` | exit 0；issue_count=0 |

#### 机器证据（ignored）

| 路径 | 角色 |
|---|---|
| `build/phase-09/tools/generate_core_release_evidence.py` | §6.6 生成器 |
| `build/phase-09/6_6-core-evidence-generate.json` | 生成摘要（status=PASS） |
| `build/phase-09/6_6-check-deliverables.json` | 再生后 deliverables checker |
| `build/phase-09/6_6-check-publication-safety.json` | 再生后 safety checker |
| `build/phase-09/6_6-check-evidence-freshness.json` | 再生后 freshness checker |
| `build/phase-09/6_6-postcheck-summary.json` | 三 checker 汇总 |

#### §6.6 对后续步骤的约束

- §6.7 文档只记录稳定路径/合同/限制，不得写入当前 HEAD SHA、run ID/URL 或“当前 CI 已成功”。
- 候选文件再变化时：重跑 `generate_core_release_evidence.py`（若 gate 结果变化）→ 再生 deliverables → 三 checker。
- push / CI / 远程 clone 的动态事实只在 §6.10–§6.11 完成后进入后续记录性提交。

### §6.7 完成稳定最终文档 — COMPLETE

| 项 | 值 |
|---|---|
| 结论 | `COMPLETE` / `PASS` |
| 日期 | 2026-08-12 |
| 范围 | 第 5.1 节列出的稳定文档；**未**写入当前 HEAD SHA、run ID/URL、“当前 CI 已成功”或临时 `build/` 路径作为发布完成证明 |
| 进入前复核 | §6.1–§6.6 产物与三 checker 复验通过（见阶段头部） |

#### 新建 / 更新的稳定文档

| 路径 | 动作 | 要点 |
|---|---|---|
| `docs/v0.4/release-readiness.md` | 新建 | P00-R01–R16 逐项终态；Phase 01–08 新增风险 P06-R01、P08-R01；可选轨真实状态；本地门槛 vs 外部门槛 |
| `docs/v0.4/human-decisions.md` | 新建 | 内容/身份/repository 模式/外部写动作全部 `NOT_REQUESTED`；历史 ADR/opt-in 仅作参考 |
| `docs/v0.4/publication-record.md` | 新建 | push/CI/clone/tag 字段模板；当前均为 `NOT RUN` |
| `C_Semantic_Treehouse/docs/final-checklist.md` | 新建 | 已完成核心/§6.1–§6.7 与未完成发布门槛；已知限制（ACCEPTED_LIMITATION） |
| `C_Semantic_Treehouse/docs/demo-script.md` | 新建 | 25–40 分钟演示路径；强制诚实披露未完成外部门槛 |
| `C_Semantic_Treehouse/FINAL_SUMMARY.md` | 新建 | 交付摘要与明确“未宣称”列表 |
| `docs/v0.4/README.md` | 更新 | 从“截至 Phase 07”导航升级为含 Phase 08/09、release-readiness、decisions、publication-record、deliverables、evidence-index |
| `scripts/README.md` | 更新 | 增加 Phase 09 三 checker 调用方式、输入输出与 fail-closed 语义；保留 Treehouse 作用域投影 token |
| `README.md` | 更新 | 最终一键复现单命令；Phase 09 checker；证据/文档导航 |
| `迁移清单.md` | 更新 | 依 Phase 00–08 证据刷新 checkbox；§6.9–§6.11 门槛保持未完成 |
| `C_Semantic_Treehouse/README.md` | 更新 | deliverables、core evidence、FINAL_SUMMARY/demo/checklist、reproduce 入口 |

#### 风险收口摘要（P09-A18 本地记录）

| 类别 | 终态计数（截至 §6.7） |
|---|---|
| Phase 00 原始风险 `RESOLVED` | P00-R06、R07、R08、R09、R10、R11、R13、R16 |
| Phase 00 原始风险 `ACCEPTED_LIMITATION` | P00-R12、R15 |
| Phase 00 原始风险 `OPEN_BLOCKING` | P00-R01、R02、R03、R04、R05、R14 |
| 新增风险 | P06-R01=`RESOLVED`；P08-R01=`ACCEPTED_LIMITATION` |

`OPEN_BLOCKING` 项阻断 Phase 09 `COMPLETE` 与正式公开推送，须在 §6.8–§6.11 关闭或取得明确批准。完整表见 `docs/v0.4/release-readiness.md`（只读 `risk-register.md`，未回写）。

#### deliverables 再生与 checker 复验

| 步骤 | 结果 |
|---|---|
| `generate_deliverables_manifest.py` | entry count **455**（较 §6.6 的 449 增加 6 份 §6.7 文档） |
| deliverables runtime SHA-256（ignored only） | 以 `build/phase-09/6_7/postcheck-summary.json` / 最新 `check_deliverables.py` 为准；**不**回写 tracked 固定自引用 |
| `check_deliverables.py` | exit 0；issue_count=0 |
| `check_publication_safety.py` | exit 0；issue_count=0 |
| `check_evidence_freshness.py` | exit 0；issue_count=0 |
| `check_documentation.py` | exit 0；14 documents / 2 diagrams；`program_status=SUCCESS` |
| `check_documentation.py --self-test` | exit 0；**90/90** |

未修改 `scripts/check_documentation.py`（只读消费）。core-results / core-report 未因文档变化重写（gate 结果未变）。

#### 机器证据（ignored）

| 路径 | 角色 |
|---|---|
| `build/phase-09/6_7/check-deliverables.json` | §6.7 deliverables checker |
| `build/phase-09/6_7/check-publication-safety.json` | §6.7 safety checker |
| `build/phase-09/6_7/check-evidence-freshness.json` | §6.7 freshness checker |
| `build/phase-09/6_7/postcheck-summary.json` | 三 checker + documentation 汇总 |
| `build/validation/documentation/results.json` | documentation normal run |
| `build/phase-07/documentation-negative-controls.json` | documentation self-test 90/90 |

#### §6.7 对后续步骤的约束

- §6.8 起任何许可证/再分发/身份/repository 决定形成后，必须升级 INTERIM decision、更新 LICENSE/NOTICE（若批准）、再生 deliverables 并重跑最终 QA。
- tracked 文档在候选 commit 形成前仍不得写入当前动态 SHA/run 事实。
- 不得把本地 checker 通过误报为 GitHub Actions 已成功。

### §6.8 完成人工发布决定和远程预检 — 目标绑定 COMPLETE（License 延期；写动作未执行）

| 项 | 值 |
|---|---|
| 结论 | 空仓库目标已绑定；再分发/身份已批；**通用 License 延期**；commit/remote/push 未授权 |
| 日期 | 2026-08-12 |
| 目标仓库 | `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C` |
| Clone URL | `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| 远程预检 | `git ls-remote` **0 refs**（空仓库；无 License 初始 commit） |
| Visibility / owner | Public / `Daydreaming24` |
| 通用 License | 无根 `LICENSE`；`DEC-P09-LICENSE-NONE-INTERIM`；MIT WITHDRAWN |
| 再分发 | D 组 / 来源 ZIP / 历史路径均为 `APPROVED` |
| 身份 | GitHub `Daydreaming24`；author `daydreaming`（邮箱已按 `DEC-P09-COMMIT-IDENTITY-NOREPLY` 脱敏，见本文件末尾追加的身份修订记录） |
| 本地 remote | **无**（尚未 `git remote add`） |
| 外部写动作 | create-repo 维护者完成；local commit / remote add / push = `NOT_REQUESTED` |
| 风险 | P00-R01=`RESOLVED`；P00-R02/R05/R14=`OPEN_BLOCKING`；P00-R03/R04=`RESOLVED` |

空远程意味着首次 push **不必** 合并无关 LICENSE 历史；仍禁止 force push。

### §6.10 Push、CI 确认与远程 Clean Clone — COMPLETE

| 项 | 值 |
|---|---|
| 候选 commit SHA | `90cf2de062e43743cb179ed9141885e5a6eccfab` |
| Remote | `origin` → `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git` |
| Push | 普通 `git push -u origin main`（无 force） |
| CI run | https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31652415581 |
| Run `head_sha` | `90cf2de062e43743cb179ed9141885e5a6eccfab`（等于候选） |
| Ubuntu job | `success` |
| Windows job | `success` |
| Docker job | `success` |
| 远程 clean clone | 真正 `git clone` 至 ignored `build/remote-clean-clone` 策略目录；resolved SHA 等于候选；`reproduce.ps1` exit 0；三 Phase 09 checker exit 0 |

### §6.11 记录发布确认 — COMPLETE

本记录性提交描述**已经确认完成的候选 commit** `90cf2de…` 的外部事实（CI run URL/结论、远程 clone），不构成对该记录性提交自身的自引用。

| 验收 | 状态 |
|---|---|
| P09-A13 CI 确认 | PASS |
| P09-A14 远程 clean clone | PASS |
| P09-A16 最终有效状态 | PASS（本小节完成后） |

### 未完成 / 可选后续

| 项 | 状态 |
|---|---|
| Tag | `NOT_REQUESTED` |
| GitHub Release | `NOT_REQUESTED` |
| Branch protection | `NOT_REQUESTED` |
| P00-R14 最终人工治理角色 | 仍可并行处理；不阻断已推送候选的 CI/clone 确认事实 |
| 通用 License | 仍延期（无根 `LICENSE`） |

Phase 09 有效状态：`COMPLETE`（三项外部事实与候选 SHA 一致）。

## Phase 01 / 04 / 06 / 07 / 08 / 09 发布后恢复审计（2026-08-13）— `IN_PROGRESS`

本节是追加式更正记录。它不改写上方历史执行记录。2026-08-13 对 Phase 09
指令逐项复核后确认：此前的 `COMPLETE` 结论遗漏了稳定文档漂移、current core
evidence 源码 hash 新鲜度，以及 P00-R14 仍为 `OPEN_BLOCKING` 三项事实。因此，
上方 `COMPLETE` 仅保留为当时记录；本节起的有效 Phase 09 状态取代该结论。

### 1. 恢复路由与修改边界

Phase 09 历史修复提交曾修改较早 Phase 的受保护路径：

| 恢复到 Phase | 历史变更 | 本轮复核范围 |
|---|---|---|
| Phase 01 | `c15fe1e…` / `90cf2de…` 修改 `bootstrap.sh` 与 `doctor_core.py` | host/container doctor、锁与完整 `all` 回归 |
| Phase 04 | `e0a27e8…` 修改 release manifest 与其加载器 | release/model、traceability、provenance 与 core evidence 重新绑定 |
| Phase 06 | `e0a27e8…` 修改 provenance 与 B handoff | governance、provenance、handoff 与文档投影复核 |
| Phase 07 | `c15fe1e…` 修改 CI checker；当前审计发现 documentation checker 对仓库发布状态 fail-open | 修复 checker，重跑 canonical 与全部 negative controls |
| Phase 08 | `c15fe1e…` 修改 workflow/CI/Docker 证据权限路径 | CI policy/self-test、Windows/Linux 入口与固定 Docker 轨复核 |
| Phase 09 | core evidence 与 deliverables 曾未绑定后续 validator/文档变化 | 强制 `source_hash_policy=must-match-disk`、重生成 core evidence 与 deliverables |

当前只修正发布状态、检查器合同、证据与清单；模型、Shape、fixtures、suite
composition 和冻结输入均未改变。`risk-register.md` 继续保持 Phase 00 只读快照，
最终处置写入 `release-readiness.md`。

### 2. 状态与决定更正

| 项 | 有效状态 |
|---|---|
| P00-R02 | `ACCEPTED_LIMITATION`：维护者批准 v0.4 公开托管且不授予通用版权复用许可；无根 `LICENSE`；decision=`DEC-P09-LICENSE-NONE-FINAL-V0.4` |
| P00-R14 | 唯一 `OPEN_BLOCKING`：C/D final review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 仍待具名真人完成；agent 不代签 |
| GitHub repository / ordinary push / CI / remote clone | 上一候选的实际成功事实继续有效；动态绑定见 `publication-record.md` |
| 当前同步候选 | tracked tree 已变化，必须重新执行 §6.9–§6.11；旧 run/clone 不作为新候选证据 |
| Phase 09 有效状态 | `IN_PROGRESS`；新候选技术链完成后转为 `AWAITING_HUMAN_DECISION`，直至 P00-R14 关闭 |
| Tag / GitHub Release / default-branch change / branch protection | `NOT_REQUESTED` |

### 3. 已完成的恢复验证（候选形成前）

| 验证 | 结果 |
|---|---|
| Docker Desktop / daemon | `PASS`；client/server `29.7.2` |
| Phase 07/08 恢复基线 | `c4e3492…`；7 个上游文档/checker 修复独立提交，其后 Phase 09 diff 均在 §5.1 allowlist |
| host doctor | `PASS`；CPython `3.12.10`、pip `25.0.1`、lock `d92c7a…`、Docker/Compose/daemon 全部 PASS |
| host suite `all` | `SUCCESS`；17/17/17/0/0；frozen 104/104 |
| 固定 Docker image | `--no-cache --pull` 重建成功；source commit/dirty build args 显式绑定 |
| container doctor | `PASS` |
| container CI policy self-test | `PASS`；59/59 |
| container suite `all` | `SUCCESS`；17/17/17/0/0；frozen 104/104 |
| container Phase 09 checker | `PASS`；deliverables 使用严格 clean-room filesystem inventory（457 项、唯一省略 `build/.gitkeep`）；safety/freshness issue_count=0；错误容器契约负控均被拒绝 |
| Windows 显式 suites | `PASS`；`frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all` 均 exit 0 |
| core evidence generator | `PASS`；host result content SHA-256=`36e67467e7f2d9786c247534d7fea9d6e73d5d05f389ea953f9a697e07241810`；container=`0eb4b65da47359e50dec05e26f01cdc35fb80f00edb06702a44435a6445663ae`；core-results=`c353fe43f30b112003bb5fa7990408a1510a33953fd77ca6dafc8c628ba4d72c` |
| deliverables / publication-safety | `PASS`；457/457 required、tracked=458、issue_count=0；safety issue_count=0 |
| evidence-freshness self-test | `PASS`；3/3（missing/weakened policy 均被拒绝） |
| evidence-freshness canonical | `PASS`；issue_count=0；core source hashes 与磁盘一致 |
| documentation canonical | `PASS`；14 documents / 2 diagrams |
| documentation self-test | `PASS`；100/100（含历史/当前候选隔离、字段冲突与跨行状态回退负控） |
| CI policy / self-test | `PASS`；canonical issue_count=0；59/59 controls |

### 4. 当前恢复点

稳定文档、core evidence、deliverables、三个 Phase 09 checker、三组负控、Windows
显式 suites 与单命令，以及 Docker 无缓存验证均已通过。下一步为：执行最终 Git/staged
审计，形成新候选并在本地 clean clones 中复核 Windows/Linux 单命令与全部 checker，
随后执行 ordinary push、候选绑定 CI、canonical URL remote clean clone，最后以 §6.11
记录性提交追加动态事实。

在该链完成前，`CHECKPOINT.md` 保持活动中断点；候选提交自身不写入其尚未发生的
SHA/run/clone 动态绑定。

### 5. §6.9–§6.11 同步候选确认（2026-08-13）— `AWAITING_HUMAN_DECISION`

本小节追加于同步候选完成本地 clean clone、普通 push、候选绑定 CI 与 canonical URL
远程 clean clone 之后，取代上方“当前恢复点”的 `IN_PROGRESS` 状态。记录性提交只描述
已经存在且不会再变的候选 `ce234885…`，不把自身 SHA 当作候选证据。

| 验证 | 结果 |
|---|---|
| 候选 commit | `ce234885b6a7a24ba599fbc6eaabf15537c3b829`；parent=`c4e3492c7d8f82f9507274883f951b918ac90310`；23 个 Phase 09 路径全部位于 §5.1 allowlist |
| 本地 Windows clean clone | `PASS`；真正 `git clone --no-local`；resolved SHA 等于候选；`reproduce.ps1` exit 0；suite `all` 17/17；最终 checker 与 documentation/CI 检查通过；tracked 工作树 clean |
| 本地 Linux clean clone | `PASS`；WSL 真正 `git clone --no-local`；resolved SHA 等于候选；固定 CPython 3.12.10 clean-room 中 `reproduce.sh` exit 0；suite `all` 17/17；最终 checker 与 documentation/CI 检查通过；tracked 工作树 clean |
| Remote / push | `origin`=`https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git`；普通 push `main`（无 force）成功 |
| GitHub Actions | run [`31712108142`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31712108142)；event=`push`；`head_sha=ce234885b6a7a24ba599fbc6eaabf15537c3b829`；conclusion=`success` |
| 必需 job | Ubuntu=`success`；Windows=`success`；Docker=`success` |
| 远程 clean clone | 从 canonical GitHub URL 真正 clone 至 ignored `build/remote-clean-clone/candidate-ce23488-windows`；resolved SHA 等于候选；`reproduce.ps1` exit 0；doctor PASS；frozen 104/104；suite `all` 17/17；三个 Phase 09 checker exit 0；documentation/CI 静态检查 exit 0；tracked 工作树 clean |
| 三方 SHA 一致性 | 本地候选 SHA = Actions `head_sha` = 远程 clone resolved SHA；精确值均为 `ce234885b6a7a24ba599fbc6eaabf15537c3b829` |
| ignored 动态证据 | `build/ci-verification/run-31712108142.json`、`build/ci-verification/summary.txt`、`build/remote-clean-clone/summary.txt` |

| 验收 | 状态 |
|---|---|
| P09-A13 候选绑定 CI | `PASS` |
| P09-A14 远程 clean clone | `PASS` |
| P09-A15 无候选自引用 | `PASS` |
| §6.11 动态事实记录 | `PASS` |
| P09-A18 风险台账收口 | `AWAITING_HUMAN_DECISION`；P00-R14 仍为唯一 `OPEN_BLOCKING` |

Phase 09 当前有效状态：`AWAITING_HUMAN_DECISION`。技术候选同步与外部验证链已经完成；
具名真人仍须完成或明确接受 P00-R14 所列 C/D final review、Domain Reviewer、47 条
SSSOM domain review 与 Release Approver 责任。P00-R14 关闭前不宣称 Phase 09
`COMPLETE`。Tag、GitHub Release、default-branch change 与 branch protection 继续保持
`NOT_REQUESTED`。

### 6. documentation 终态负控恢复（2026-08-13）— `IN_PROGRESS`

上一小节对候选 `ce234885b6a7a24ba599fbc6eaabf15537c3b829`、Actions run
[`31712108142`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31712108142)
与远程 clean clone 的成功记录继续作为历史事实有效。将该候选写入 current publication
section 后，documentation canonical 20/20 通过，完整 100 项 self-test 暴露负控助手仍以
全文件唯一字段定位 `Push` / run / job / clone 行；历史与当前候选同时存在时会 fail
closed。该缺口已在独立 Phase 07 恢复提交中改为当前候选 section-scoped 定位，并继续
要求目标行精确唯一。

checker 修复使 tracked tree 不再等于 `ce234885…`。因此上一小节 `AWAITING_HUMAN_DECISION`
作为该历史候选完成技术链后的状态保留；本节起当前有效状态恢复为 `IN_PROGRESS`。
新候选提交尚未形成，旧 run/clone 不作为新候选证据。下一步为：完成 publication-record
历史/current 隔离、再生 deliverables、重跑 documentation 100/100 与最终 QA，创建新候选，
随后完整重做 local Windows/Linux clean clones、普通 push、精确 SHA GitHub CI、canonical
URL remote clone 与 §6.11 记录提交。技术链再次完成后转为 `AWAITING_HUMAN_DECISION`；
P00-R14 继续是唯一 `OPEN_BLOCKING`。

## Phase 09 README / 发布链最终同步记录（2026-08-14）— `AWAITING_HUMAN_DECISION`

本节是追加式 §6.11 记录，取代上方 documentation 终态负控恢复小节的当前
`IN_PROGRESS` 状态。它只记录已经完成并独立核验的候选动态事实，不把本记录性提交的
SHA 当作候选证据。

| 验证 | 结果 |
|---|---|
| 候选 commit | `6cb004fa086df1138256af4cc21cb4fd032bab11`；parent=`62a1859ed38c09b39f75f90066484db5f6813d42`；8 个变更路径全部位于 Phase 09 §5.1 allowlist；候选树不含自身 SHA/run/clone 动态绑定 |
| 本地 Windows clean clone | `PASS`；`git clone --no-local`；resolved SHA 等于候选；`reproduce.ps1` exit 0；doctor PASS；frozen 104/104；suite `all` 17/17；三个 Phase 09 checker、documentation 100/100 与 CI 59/59 通过；tracked tree clean |
| 本地 Linux clean clone | `PASS`；WSL `git clone --no-local`；固定 CPython 3.12.10；`reproduce.sh` exit 0；doctor PASS；frozen 104/104；suite `all` 17/17；三个 Phase 09 checker、documentation 100/100 与 CI 59/59 通过；tracked tree clean |
| Remote / push | `origin`=`https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git`；普通 push `main`（无 force）成功 |
| GitHub Actions | run [`31722370069`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31722370069)；event=`push`；`head_sha=6cb004fa086df1138256af4cc21cb4fd032bab11`；conclusion=`success` |
| 必需 job | Ubuntu=`success`（job `94522226347`）；Windows=`success`（job `94522226378`）；Docker=`success`（job `94522226389`） |
| 远程 clean clone | 从 canonical GitHub URL 真正 clone 至 ignored `build/remote-clean-clone/candidate-6cb004f-windows`；resolved SHA 等于候选；`reproduce.ps1` exit 0；doctor PASS；frozen 104/104；suite `all` 17/17；三个 Phase 09 checker exit 0；documentation canonical/100 项 self-test 与 CI canonical/59 项 self-test 通过；tracked tree clean |
| 三方 SHA 一致性 | 本地候选 SHA = Actions `head_sha` = 远程 clone resolved SHA = `6cb004fa086df1138256af4cc21cb4fd032bab11` |
| ignored 动态证据 | `build/ci-verification/run-31722370069.json`、`build/ci-verification/summary.txt`、`build/remote-clean-clone/summary.txt` |

| 验收 | 状态 |
|---|---|
| P09-A01–P09-A17 | `PASS`；静态、本地、候选绑定 CI、远程 clone 与 §6.11 动态记录均满足 |
| P09-A18 风险台账收口 | `AWAITING_HUMAN_DECISION`；P00-R14 仍为唯一 `OPEN_BLOCKING` |
| P00-R02 | `ACCEPTED_LIMITATION`；v0.4 公开托管且不授予通用版权复用许可 |
| Tag / GitHub Release / default-branch change / branch protection | `NOT_REQUESTED` |

Phase 09 当前有效状态为 `AWAITING_HUMAN_DECISION`。技术候选同步、外部验证链与
§6.11 动态事实记录均已完成。具名真人仍须完成或明确接受 P00-R14 所列 C/D final
review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 责任；agent
不代签。P00-R14 关闭前不宣称 Phase 09 `COMPLETE`。

## Phase 06–08 人工治理状态投影恢复（2026-08-14）— `COMPLETE`

本节是追加式完成记录。维护者（GitHub 身份 `Daydreaming24`）在当前请求中明确接受
P00-R14 所列最终人工治理责任；只读审计随后发现 Phase 06–08 的现行治理、handoff 与
跨平台文档仍投影旧的 `PENDING` / 当前候选叙述。按 Master/HIP 从最早受影响 Phase
恢复并顺序验收到 Phase 08，结果如下。

| 决定 / 恢复 | 完成事实 |
|---|---|
| P00-R14 人工决定 | `APPROVED`（responsibility accepted）；维护者接受 C Group final semantic review、D Group final contract review、Domain Reviewer、47 条 SSSOM domain review 与 Release Approver 的最终责任；decision=`DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED` |
| 风险终态 | `ACCEPTED_LIMITATION`；当前无 `OPEN_BLOCKING` 风险。47 条 mapping 的 `PENDING_DOMAIN_REVIEW` 与 semantic/domain/D/release 逐项 review 记录继续保留，未虚构逐项签字 |
| Phase 06 恢复 | governance 四份现行文档、`provenance.jsonld` 与 `governance_contract.py` 同步责任、候选绑定 CI、GitHub repository publication、Treehouse 本地可选运行/未发布边界；`evidenceRef` 现在校验安全 regular 非空 UTF-8 文件及必需支撑 token |
| Phase 07 恢复 | 两份核心模型文档、AI 治理文档与 B 组 provenance handoff 同步 responsibility-accepted / confirmed / completed-local-optional 投影；逐项 review 保持 `PENDING` |
| Phase 08 恢复 | Treehouse usage、environment 与 reproducibility contract 改为时间无关的“每个 tracked 内容变化候选独立重验”规则；Treehouse runtime=`PAUSED`、publication=`NOT RUN` 保持真实 |
| 保护边界 | validation-suites、release/baseline/requirements/test manifests、模型、Shape、fixtures、oracle 与 suite composition 均未修改；frozen 104/104 |

| 顺序回归 | 结果 |
|---|---|
| Phase 06 governance | canonical 21/21；强化后的逐节点/逐字段/evidence-content negative controls 22/22；manifest/suite controls 24/24；SPARQL self-test 与 quality 均 `SUCCESS` |
| Phase 07 documentation | canonical `PASS`（14 documents / 2 diagrams）；self-test 100/100 |
| Phase 08 CI policy | canonical `PASS`；self-test 59/59 |
| Windows host | suite `all` 17/17/17/0/0；required skipped=0 |
| Docker clean-room | `--no-cache --pull` build 成功；manifest-list SHA-256=`9f8e155ed32824b49fe21277708978129e136cd36c427eaf1c7345e92941daa4`；container suite `all` 17/17/17/0/0 |

远程只读/权限预检同样完成：repository ID=`1332105560`、Public、default branch=`main`、
`origin=https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git`；Git Credential Manager
列出的 GitHub identity 唯一为 `Daydreaming24`，普通 `git push --dry-run origin main`
exit 0 且未显示 credential。当前请求授权创建本地候选 commit 并普通 push `main:main`；
force push 禁止，manual workflow rerun、tag、GitHub Release、default-branch change 与 branch
protection 均为 `NOT_REQUESTED`。

本节确认 Phase 06–08 恢复已经完成。恢复产生 tracked 内容变化，因此新的 Phase 09 候选
仍须独立完成 §6.9–§6.11；该尚未完成的唯一执行点记录在 `CHECKPOINT.md`，本节不把旧
run/clone 绑定到新候选。

## Phase 09 人工责任收口与最终发布确认（2026-08-14）— `COMPLETE`

本节是追加式 §6.11 完成记录，取代上方 Phase 06–08 恢复完成后“新候选仍须独立验证”
的执行点。它只记录已经发生并独立核验的候选动态事实；本记录性提交自身不作为候选
SHA、Actions run 或 clean-clone 证据。

维护者（GitHub 身份 `Daydreaming24`）已通过
`DEC-P09-P00-R14-RESPONSIBILITY-ACCEPTED` 明确接受 C Group final semantic review、
D Group final contract review、Domain Reviewer、47 条 SSSOM domain review 与 Release
Approver 的最终责任。P00-R14 终态为 `ACCEPTED_LIMITATION`，当前无
`OPEN_BLOCKING` 风险。47 条 mapping 的 `PENDING_DOMAIN_REVIEW` 与治理产物中的逐项
`PENDING` 继续保留为真实产物状态；本决定未虚构逐项审核结论或签字。

| 验证 | 完成事实 |
|---|---|
| 恢复基线 | `6588e16887255a8010b7739734d6fe98f05d20bf`；Phase 06→07→08 现行状态投影、治理证据合同与跨平台文档恢复已独立提交并顺序验收 |
| 候选 commit | `e305d16a353aa4367bd667af6e8d87c5a32f6bc3`；parent=`6588e16887255a8010b7739734d6fe98f05d20bf`；5 个变更路径全部位于 Phase 09 §5.1 allowlist；候选树不含自身 SHA/run/clone 动态绑定 |
| 候选前 host QA | frozen 104/104；suite `all` 17/17；deliverables 457/457；publication safety 扫描 913 项；freshness 扫描 226 项；三项 checker 均 0 issue；documentation canonical/100 项 self-test 与 CI canonical/59 项 self-test 均通过 |
| 本地 Windows clean clone | `PASS`；真正 `git clone --no-local` 至 ignored `build/clean-clone/candidate-e305d16-windows`；resolved SHA 等于候选；`reproduce.ps1` exit 0；doctor PASS；frozen 104/104；suite `all` 17/17；三个最终 checker、documentation 100/100 与 CI 59/59 通过；tracked tree clean |
| 本地 Linux clean clone | `PASS`；WSL 原生文件系统真正 `git clone --no-local` 至 `/tmp/dssc-candidate-e305d16-linux-native-20260814`；固定 CPython 3.12.10；`reproduce.sh` exit 0；doctor PASS；frozen 104/104；suite `all` 17/17；三个最终 checker、documentation 100/100 与 CI 59/59 通过；tracked tree clean |
| Remote / push | `origin=https://github.com/Daydreaming24/DSSC_Toolbox_Group-C.git`；普通 push `main:main`（无 force）成功 |
| GitHub Actions | run [`31763791740`](https://github.com/Daydreaming24/DSSC_Toolbox_Group-C/actions/runs/31763791740)；workflow=`Validate C Semantic Governance Package`；event=`push`；branch=`main`；`head_sha=e305d16a353aa4367bd667af6e8d87c5a32f6bc3`；`completed/success` |
| 必需 job | Windows PowerShell 5.1 validation=`success`（job `94655416113`）；Docker clean-room validation=`success`（job `94655416168`）；Ubuntu native Python validation=`success`（job `94655416174`）；三者 `head_sha` 均等于候选 |
| 远程 clean clone | 从 canonical GitHub URL 真正 clone 至 ignored `build/remote-clean-clone/candidate-e305d16-windows-20260814`；resolved SHA 等于候选；`reproduce.ps1` exit 0；doctor PASS；frozen 104/104；suite `all` 17/17；deliverables 457/457、safety 913、freshness 226 均 0 issue；documentation 100/100 与 CI 59/59；tracked tree clean |
| 三方 SHA 一致性 | 本地候选 SHA = Actions `head_sha` = 远程 clone resolved SHA = `e305d16a353aa4367bd667af6e8d87c5a32f6bc3` |
| ignored 动态证据 | `build/ci-verification/run-31763791740.json`、`build/ci-verification/summary.txt`、`build/remote-clean-clone/summary.txt` |

| 验收 | 状态 |
|---|---|
| P09-A01–P09-A17 | `PASS`；静态范围、证据、清单、Windows/Linux 本地 clone、候选绑定三平台 CI、远程 clone 与 §6.11 动态记录均满足 |
| P09-A18 风险台账收口 | `PASS`；P00-R14=`ACCEPTED_LIMITATION`，当前无 `OPEN_BLOCKING` |
| P00-R02 | `ACCEPTED_LIMITATION`；v0.4 公开托管且不授予通用版权复用许可，无根 `LICENSE` |
| Tag / GitHub Release / manual rerun / default-branch change / branch protection | `NOT_REQUESTED` |
| Force push | 禁止；本轮未执行 |

Phase 09 当前有效状态为 `COMPLETE`。候选 `e305d16a…` 的本地双平台 clean clone、普通
push、精确 SHA 三平台 GitHub Actions 与 canonical URL 远程 clean clone 已完整闭合；
`CHECKPOINT.md` 已恢复为空闲占位符。本次窄范围记录性提交适用 §6.11 无需重跑的规则；
此后任何改变模型、验证逻辑或发布证据实质内容的 tracked 变化都形成新候选，并须再次独立
完成 §6.9–§6.11。

## Phase 09 commit 身份修订与历史重建记录 — 2026-08-16

本小节按 `scope-and-authority.md` 第 1 节"受影响 Phase 恢复后追加修订小节"的规则追加。
它修订本文件早前 Phase 09 小节中记录的 commit author 身份，并说明为此执行的历史重建。
既有各阶段结论、验收矩阵与技术证据不因本次修订改变。

| 项目 | 记录 |
|---|---|
| 决定 | `DEC-P09-COMMIT-IDENTITY-NOREPLY`；维护者批准 |
| 原状态 | 早前决定沿用既有本地历史身份，其邮箱为可路由的个人地址；40 个 commit 的 author/committer 与四份文档正文均含该地址 |
| 触发原因 | v0.4 仓库将在与维护者真实身份绑定的场合公开演示，公开历史中的个人邮箱不再适合保留。该地址不构成凭证，本次修订按隐私处置而非安全事件处理 |
| 新身份 | `daydreaming <188458589+Daydreaming24@users.noreply.github.com>` |
| 文档脱敏 | `STATUS.md`、`human-decisions.md`、`release-readiness.md`、`final-checklist.md` 四处就地脱敏；`human-decisions.md` 将原决定标记为 `SUPERSEDED` 并追加最终决定，不改写原决定曾经存在的事实 |
| 历史重建 | 本地历史压缩为单一提交；使用 `git checkout --orphan` 保留原 index，因此提交树内的 blob 与重建前逐字节一致，`.gitattributes` 的 `-text` 边界与 frozen 字节绑定不受影响 |
| 远程处置 | 删除既有远程仓库并以同名重建，canonical URL 保持 `https://github.com/Daydreaming24/DSSC_Toolbox_Group-C` |
| 失效证据 | 重建前所有候选 SHA、GitHub Actions run URL/job ID 与远程 clone resolved SHA 随原仓库一并失效；`publication-record.md` 以本次重建后的新候选绑定为准 |
| 边界 | 删除远程仓库减少后续暴露面，不构成对既已公开内容的追溯撤回 |
| GitHub 侧设置 | 已启用 *Keep my email addresses private* 与 *Block command line pushes that expose my email* |

本次修订改变 tracked 内容并重建历史，因此形成新候选，须重新独立完成 Phase 09
§6.9–§6.11：Windows/Linux 本地 clean clone、普通 push、候选绑定的 Ubuntu/Windows/Docker
三个必需 job 与 canonical URL 远程 clean clone。在该链完成并由 §6.11 记录性提交写入
`publication-record.md` 与本文件之前，Phase 09 的发布链结论按未闭合处理。
