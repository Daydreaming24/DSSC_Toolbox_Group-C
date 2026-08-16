# Phase 01 Prompt — 可复现环境、依赖锁与统一入口

你位于仓库根目录。完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md`、本文件和 `docs/v0.4/STATUS.md` 中 Phase 00 小节，只执行 Phase 01。进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后停止。

## 1. 目标

建立 v0.4 主线的可复现环境合同，并在当前 Windows 主机实际创建仓库 `.venv`。交付准确 CPython 3.12 补丁版本、直接依赖清单、精确且含 hash 的 lock、Windows/Linux bootstrap、环境 doctor、统一 Python 验证入口和固定 digest 的基础容器。

本阶段完成后，以下两个 suite 必须真实可用：

```text
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
```

`baseline`、`traceability`、`v0.4-model`、`v0.4` 和 `all` 尚未实现时必须打印 `NOT_IMPLEMENTED` 并返回非零。

## 2. 非目标

- 不声明 v0.1–v0.3 已在锁定环境中无回归；该结论属于 Phase 02。
- 不实现 D 组需求追踪、v0.4 模型、fixtures 或四状态验证器。
- 不复用旧 Make/Docker/CI 报告作为当前证据。
- 不配置 GitHub Actions、remote、commit、push 或 tag。
- 不安装 Semantic Treehouse、ITB/SEMIC、Mermaid、数据库、GPU 或 ML 工具。
- 不为环境/入口合同发明额外的机器验证格式（例如逐字段 hash 绑定的"phase guard"、不可变 activation record）。状态记录只使用 `docs/v0.4/STATUS.md` 和 `docs/v0.4/CHECKPOINT.md`。

## 3. 权威输入

完整读取：

- `docs/v0.4/STATUS.md` 中 Phase 00 小节、`docs/v0.4/current-state.md`、`scope-and-authority.md`、`risk-register.md`
- `docs/environment.md`
- `scripts/README.md`、`scripts/verify_frozen_files.py`
- `C_Semantic_Treehouse/requirements.txt`，仅作直接依赖候选来源
- `C_Semantic_Treehouse/scripts/**`，仅用于发现实际 imports 和旧风险
- `archive/v0_tooling/**`、`archive/v0_ci/**`，仅作历史参考
- `.gitignore`、`.gitattributes`
- 当前机器的 Python launcher、Python、pip、Git、PowerShell、Docker client/server 和 Compose 版本输出

直接依赖至少覆盖 `rdflib`、`pyshacl`、`pyld`、`jsonschema`、`PyYAML` 和 `openapi-spec-validator`。任何新增依赖都必须由实际代码需要证明。

## 4. 进入门槛

1. Phase 00 在 `STATUS.md` 中记录为 `COMPLETE`。
2. `STATUS.md` 中 Phase 00 小节存在，且其最终冻结校验通过。
3. `docs/v0.4/CHECKPOINT.md` 为空闲；若非空闲，先按其记录恢复并做完 Phase 00，不得跳过来开始 Phase 01。
4. Phase 00 的预环境原生冻结校验返回 0；完成 bootstrap 后还必须由 `.venv` 的 `frozen` suite 再次核验。
5. 可确定一个对 Windows 和 Linux 都可获得的准确 CPython 3.12 补丁版本；不得继续使用 `3.12.x`。
6. 当前机器允许在仓库创建 `.venv`，且 Docker 发布验证所需 daemon 可连接。
7. 可写路径不存在会被覆盖的用户修改。

准确 Python 版本或 Docker daemon 暂不可用时，先完成安全的诊断和文档记录。需要用户安装、启动、选择来源或批准外部动作时标记 `AWAITING_HUMAN_DECISION` 并停止；确认仍客观不可用且没有安全选项时标记 `BLOCKED`。两种情况都先把当前进度写入 `CHECKPOINT.md`。本阶段要求 host 和 Docker 两条环境轨都通过，不能以单轨成功标记 COMPLETE。

## 5. 可写路径

仅允许创建或修改：

- `.python-version`
- `requirements.in`
- `requirements.lock`
- 必要的 lock 生成元数据文件，例如 `requirements.lock.json`
- 如采用独立 bootstrap 工具链：`requirements-bootstrap.in`、`requirements-bootstrap.lock` 及其生成元数据
- `C_Semantic_Treehouse/manifests/validation-suites.json`
- `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`
- `.gitignore`
- `.dockerignore`
- `Dockerfile.validation`
- `docker-compose.validation.yml`
- `Makefile`
- `scripts/bootstrap.ps1`
- `scripts/bootstrap.sh`
- `scripts/doctor.py`
- `scripts/validate.py`
- `scripts/validate.ps1`
- `scripts/validate.sh`
- `scripts/README.md`
- `scripts/` 下由上述入口直接需要的共享模块，明确排除现有 `scripts/verify_frozen_files.py`
- `C_Semantic_Treehouse/requirements.txt`，仅用于消除第二权威源或增加清晰兼容转发
- `README.md` 的环境 quickstart
- `docs/environment.md`
- `docs/v0.4/reproducibility-contract.md`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`
- `build/phase-01/**`

`.venv/` 是本地生成物，必须被忽略，不能进入 Git。

## 6. 保护路径

除 Master 永久保护范围外，本 Phase 还保护：

- `prompts/**`
- `C_Semantic_Treehouse/model/v0.4/**`
- `C_Semantic_Treehouse/fixtures/**`
- `C_Semantic_Treehouse/manifests/**`，本阶段明确可写的 validation-suites registry 及其 schema 除外
- `C_Semantic_Treehouse/tests/**`
- `C_Semantic_Treehouse/validation/**`
- `C_Semantic_Treehouse/evidence/**`
- `.github/**`
- `scripts/verify_frozen_files.py`；统一入口只可调用或复用，不得修改
- governance、mappings、handoff、quality 和 diagrams

Phase 01 不重构 package-level 旧验证脚本；统一入口只提供环境和冻结校验能力。

## 7. 任务

### 7.1 固定 Python 和平台合同

选择并记录一个准确 CPython 3.12 补丁版本。选择依据至少包括 Windows x64 官方安装能力、Linux 容器可用性和直接依赖兼容性。把同一个值写入：

- `.python-version`
- bootstrap 版本检查
- doctor 预期
- Docker 基础镜像完整标签
- `docs/environment.md`
- `docs/v0.4/reproducibility-contract.md`

若当前 Windows 缺少该版本，按 `human-intervention-policy.md` 向用户展示来源、目标版本、安装 scope 和预期系统变更，取得确认后再执行安装，或在无法获得确认时记录可复核的安装步骤并标记 `AWAITING_HUMAN_DECISION`。不得用全局 Python 3.13 创建正式 `.venv`。

安装 CPython 属于本阶段供应链门槛：只接受官方 `python.org` 发布物或学校/组织批准的软件包源中的准确版本。记录最终 URL/package identity、文件 SHA-256，并验证 Windows Authenticode 或对应发布签名。签名/hash 未验证时不得执行安装器。禁止运行网络返回的临时脚本、`curl | shell`、未校验镜像或浮动包版本。Docker 基础镜像继续使用完整标签和 digest，并记录实际 resolved digest。

同时在 `docs/environment.md` 和 reproducibility contract 建立团队 OS/architecture inventory 与 support matrix。只登记实际报告或实际运行的组合，并区分 `SUPPORTED_AND_TESTED`、`DOCKER_FALLBACK`、`UNTESTED`：

- Windows host（当前实际 architecture）是必需的原生开发/验证平台。
- 固定 digest 的 Linux 容器是必需的发布验证平台，并记录容器 architecture。
- macOS 和其他未实际运行的 host 仅声明 Docker fallback；不得声称原生支持。
- 新增原生支持状态必须有相应机器的 bootstrap、doctor 和 environment suite 实际证据。

inventory 不得虚构团队成员设备。无法获得的信息写 `UNKNOWN` 并注明收集责任人；Windows host 或固定 Linux 容器未实测会阻塞 Phase 01 COMPLETE。

### 7.2 建立唯一依赖源和 hash lock

1. 根 `requirements.in` 只列直接依赖及必要的兼容性范围/marker。
2. 使用已记录版本的 lock 生成工具产生 `requirements.lock`。
3. lock 必须：
   - 固定全部直接和传递依赖的准确版本。
   - 包含 `--hash=sha256:...`。
   - 能在目标 Windows 和 Linux 平台安装。
   - 不依赖本地 editable package、绝对路径或未固定 VCS branch。
4. 普通 bootstrap 只消费已提交 lock，使用 `--require-hashes`；不在 bootstrap 中重新求解依赖。
5. 记录 lock 生成工具、版本、命令、索引来源和 lock SHA-256。
6. 处理 `C_Semantic_Treehouse/requirements.txt`，使根 `requirements.in`/`requirements.lock` 成为唯一权威来源；兼容入口必须清楚转发，不能保留另一套浮动安装建议。

同时固定"执行安装的 pip"准确版本和来源。可使用选定 CPython 的 `ensurepip` 作为初始引导，再把 Windows `.venv` 与容器规范化到同一个固定 pip 版本。bootstrap 全程只能调用选定解释器或 `.venv` 的 `-m pip`，禁止调用任意全局 `pip`/`pip.exe`。若采用独立 bootstrap-tool lock，它必须准确固定 pip、lock generator 等工具并包含 SHA-256 hashes，接受与 runtime lock 同等级别的安装验证。doctor、环境证据和 summary 记录 ensurepip 来源、最终 pip 版本及 bootstrap-tool lock hash（如适用）。

首次创建/更新 `.venv` 并安装依赖、首次 pull/build 固定 Docker image，按 `human-intervention-policy.md` 先取得用户确认。

### 7.3 Windows bootstrap

实现兼容 Windows PowerShell 5.1 的 `scripts/bootstrap.ps1`：

- `$ErrorActionPreference = 'Stop'`。
- 从脚本自身路径解析仓库根目录，正确处理空格和非 ASCII。
- 优先通过明确参数或 `py` launcher 找到准确 CPython 版本。
- 创建或复用根 `.venv`。
- 显式调用 `.venv\Scripts\python.exe`，不依赖 activation。
- 校验虚拟环境解释器版本。
- 以 `--require-hashes -r requirements.lock` 安装。
- 运行 `pip check` 和 doctor。
- 重复执行幂等；失败时保留清楚的非零退出码。

### 7.4 Linux bootstrap

实现 `scripts/bootstrap.sh`：

- 使用严格 shell 选项并从脚本位置解析根目录。
- 检查准确 Python 版本。
- 显式使用 `.venv/bin/python`。
- 与 Windows 消费同一 lock。
- 运行 `pip check` 和 doctor。
- 不要求 GNU Make，不修改用户 shell profile。

### 7.5 Doctor

`scripts/doctor.py` 优先只用标准库完成环境检查；需要读取发行版 metadata 时可使用 Python 标准接口。它必须支持 `--profile host|container`，并输出实际 profile 和 capabilities。包装入口显式传递 profile；容器可通过镜像中固定的 `DSSC_VALIDATION_PROFILE=container` 做受控自动选择。禁止依据"找不到 Docker CLI"这一现象猜测 profile。至少报告：

- repo root 是否正确。
- OS 和 architecture。
- 当前 Python implementation、完整版本和是否来自仓库 `.venv`。
- pip 版本。
- lock SHA-256。
- 每个直接依赖的安装状态和实际版本。
- `pip check` 结果。
- Git 版本。
- Docker client、server 和 Compose capability。
- 关键目录的可读/可写性。

`host` profile 把 Docker client/server/Compose 和 daemon 连通性作为 Phase 01 发布环境门槛；`container` profile 只要求容器自身的 Python、lock、依赖和仓库输入，不要求容器内安装 Docker CLI，也不要求访问宿主 daemon。缺少非本 profile 的 capability 应记录为 `not_required`，不能记录为 PASS 或故障。支持机器可读 JSON 输出。确定性结果与机器环境信息分离；规范化报告不包含绝对路径。

### 7.6 统一 Python 入口

实现 `scripts/validate.py`，suite 名称固定为：

- `frozen`
- `environment`
- `baseline`
- `traceability`
- `v0.4-model`
- `v0.4`
- `all`

本阶段行为：

- `frozen` 调用或复用冻结校验逻辑，发现 0 个 manifest 条目时失败。
- `environment` 运行 Python、venv/容器解释器、lock、依赖和 `pip check` 检查，并按显式/受控 profile 应用 capability 门槛。
- 其余 suite 返回非零、程序状态 `ERROR`，并明确输出 `NOT_IMPLEMENTED`。
- 未知 suite 返回非零并列出合法值。
- 从脚本位置解析仓库根。
- 输出 JSON 到 `build/phase-01/`，Markdown 可由 JSON 确定性生成。

`scripts/validate.py` 必须先使用 schema 和跨记录语义校验后的 `validation-suites.json` 确定性展开公开 suite 与内部 checks。dispatcher 只接受逻辑 entrypoint ID，并从固定 Python checker package 的受控 entrypoint catalog/allowlist 解析；registry 不得携带 shell command、可执行字符串、任意模块路径或任意参数。未知 entrypoint、0 component、重复 component、重复 ID、悬空引用、dependency cycle 或非确定性展开均返回非零。后续 Phase 通过新增受控 checker module/entrypoint 并更新 registry 接入 `all`，不修改通用 dispatcher。

Windows/Linux 包装只选择正确解释器并透传参数。Make 只调用包装或统一 Python 入口，不复制检查逻辑。

### 7.7 建立版本化 suite 注册表

创建：

- `C_Semantic_Treehouse/manifests/validation-suites.json`
- `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`

注册表通过 `$schema` 指向固定 JSON Schema，顶层合同版本字段只能是 `contract_version`，并准确包含七个 suite：`frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all`。每个 suite 至少记录唯一 ID、实现状态、依赖 suite、当前组成和负责 Phase；`IMPLEMENTED` suite 还必须具有非空、受控的逻辑 component/entrypoint，`NOT_IMPLEMENTED` suite 不得携带可执行占位 command 或伪装成已实现的 component。本阶段只把 `frozen`、`environment` 标记为已实现；其余保持 `NOT_IMPLEMENTED`。任何 suite 状态、依赖或组成变化都必须 bump 顶层 `contract_version`；不得引入其他合同版本字段。

JSON Schema 负责字段、类型和枚举。另实现跨记录语义校验器，至少检查：

- suite ID 无重复且集合恰好为七个固定名称。
- dependency 引用都指向已登记 suite；已实现 component 引用都指向已登记内部检查。
- 依赖图无环；`all` 的组合与当前阶段进度一致。
- `IMPLEMENTED` 状态与实际入口行为一致。
- `IMPLEMENTED` suite 的 component 逻辑 entrypoint 存在于受控 catalog；`NOT_IMPLEMENTED` suite 没有可执行占位 entrypoint；registry 中不存在 shell command、模块路径注入或未允许参数。
- 每个已实现 suite 展开后 component 数量大于 0、顺序确定且无重复；调用未实现 suite 在展开或执行任何 component 前返回非零 `NOT_IMPLEMENTED`。
- `contract_version` 及 registry SHA-256 被每个 suite 证据记录。

语义校验器不得根据实际代码自动改写 registry。使用临时副本执行 duplicate suite ID、悬空 dependency、依赖环、0 component、unknown entrypoint 和 shell-command payload negative controls，全部必须非零失败。

### 7.8 Docker 发布环境

实现根 `Dockerfile.validation` 和 `docker-compose.validation.yml`：

- 基础镜像使用准确 Python 标签及不可变 digest。
- 记录镜像 index/architecture 边界。
- 仅复制 lock 后先安装依赖，以保留构建缓存。
- 安装使用 `--require-hashes`。
- 使用非 root 用户运行验证。
- 工作目录固定且不把宿主 `.venv` 带入容器。
- `.dockerignore` 排除 `.git`、`.venv`、`build`、cache、本机 `.env`/secret 和可选外部 upstream，同时保留核心验证需要的冻结输入与模型。
- 容器 profile 不安装 Docker CLI、不挂载 `/var/run/docker.sock` 或 Windows engine pipe；宿主 Docker 只负责启动 clean-room 容器。
- `ENTRYPOINT` 或等效设计直接调用同一个 `scripts/validate.py`，Compose 能透传 suite。
- 生成物写到挂载的 `build/`。

容器环境不得依赖 GNU Make 才能运行核心验证。

### 7.9 文档和本机配置

更新文档，提供：

- Windows 从零安装准确 Python、bootstrap、doctor 和 validate 命令。
- Linux 对应命令。
- Docker build/run 命令。
- 首次下载、包索引、镜像 pull 的联网需求。
- 后续核心验证的离线边界。
- 代理、证书、执行策略和 Docker daemon 常见诊断。
- 删除并安全重建 `.venv` 的精确目标边界。

随后在当前 Windows 主机真实创建 `.venv`，不能只编写脚本。

## 8. 必需产物

- 准确 Python 版本文件和环境合同
- `requirements.in`、含 hash 的 `requirements.lock` 及生成元数据
- Windows/Linux bootstrap
- doctor 和统一验证入口
- Windows/Linux/Make 薄包装
- 固定标签与 digest 的 Dockerfile 和 Compose
- `validation-suites.json`、其 schema 和跨记录语义校验器
- 更新后的 quickstart、环境说明
- `build/phase-01/` 中的 host/Docker 机器证据
- `docs/v0.4/STATUS.md` 中的 Phase 01 小节

`STATUS.md` 的 Phase 01 小节必须记录 Python 选择依据、安装器 URL/package identity、文件 SHA-256、Authenticode/发布签名与安装 scope、lock 工具版本、lock hash、固定 pip 版本/来源、镜像 digest、suite `contract_version`/registry hash、验证 runner 与全部实际加载 helper 的 SHA-256、网络访问、命令退出码和 host/Docker 差异。

风险处置按 Phase 00 baseline snapshot 的 risk ID 写入本 Phase 小节；不回写 `docs/v0.4/risk-register.md`，新增风险交给 Phase 09 汇总。

## 9. 必需命令

根据当前主机从仓库根目录运行：

```powershell
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe scripts\doctor.py --profile host
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
.\scripts\validate.ps1 -Suite v0.4
.\scripts\validate.ps1 -Suite all
```

前两项 suite 必须返回 0；后五项必须逐一返回非零并包含 `NOT_IMPLEMENTED`。

团队 inventory 中存在并计划声明原生支持的 Linux host 时运行；当前没有该 host 时记录 `DOCKER_FALLBACK`，使用后面的固定 Linux container 作为必需 Linux 轨，且不得宣称原生 Linux 已测试：

```bash
./scripts/bootstrap.sh
./.venv/bin/python scripts/doctor.py --profile host
./scripts/validate.sh --suite frozen
./scripts/validate.sh --suite environment
./scripts/validate.sh --suite traceability
```

最后一条必须返回非零并包含 `NOT_IMPLEMENTED`。

Docker：

```text
docker version
docker compose version
docker build --file Dockerfile.validation --tag dssc-c-validation:v0.4-env .
docker compose -f docker-compose.validation.yml run --rm validation --suite frozen
docker compose -f docker-compose.validation.yml run --rm validation --suite environment
docker compose -f docker-compose.validation.yml run --rm validation --suite v0.4
```

最后一条必须返回非零并包含 `NOT_IMPLEMENTED`。

Docker `environment` 证据必须显示 `profile=container`；Docker CLI/server/Compose capability 为 `not_required`。Windows/真实 Linux host 证据必须显示 `profile=host` 并实际证明 daemon 连通。检查 Compose 配置，确认没有 Docker socket/engine pipe mount。

完成后运行：

```text
.\scripts\validate.ps1 -Suite frozen
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
git status --short
```

还必须在 `build/phase-01/negative-controls/` 的临时 registry 副本上运行 duplicate suite ID、悬空 cross-reference、dependency cycle、0 component、unknown entrypoint 和 shell-command payload 语义负控。正式 suite 证据记录 `validation-suites.json` 的 `contract_version`/registry hash，以及 `scripts/validate.py`、`scripts/doctor.py` 和实际加载 helper 的源文件 SHA-256。另证明全局 `pip` 不参与 bootstrap，并比较 Windows/容器最终 pip 版本。

## 10. 验收矩阵

| ID | 验收项 | 通过条件 | 证据 |
|---|---|---|---|
| P01-A01 | Python 固定 | 一个准确 CPython 3.12 补丁号在所有入口一致 | `.python-version`、doctor、Dockerfile |
| P01-A02 | 唯一依赖源 | root input/lock 为唯一权威源，旧文件无冲突建议 | 文件审查 |
| P01-A03 | Hash lock | 所有解析依赖准确固定且包含 hash | lock、生成元数据 |
| P01-A04 | Windows bootstrap | 从未激活状态创建 `.venv`、安装 lock、`pip check` 通过 | host JSON、退出码 |
| P01-A05 | 幂等性 | 第二次 bootstrap 成功且依赖/lock 结果不漂移 | 两次运行证据 |
| P01-A06 | Linux/Docker 安装 | 同一 lock 在固定 digest 容器安装，container profile 的 Python/lock/依赖通过 | Docker JSON |
| P01-A07 | 统一入口 | `frozen`、`environment` 均真实执行且成功 | suite JSON |
| P01-A08 | 未实现保护 | `baseline`、`traceability`、`v0.4-model`、`v0.4`、`all` 五项逐一返回 NOT_IMPLEMENTED 非零 | negative-control 输出 |
| P01-A09 | Windows 独立性 | Windows 核心命令不依赖 Make、sh 或 PowerShell 7 | 脚本与运行证据 |
| P01-A10 | 路径健壮性 | 入口基于脚本位置定位根目录，能处理空格和非 ASCII | 测试记录 |
| P01-A11 | 生成物边界 | `.venv`、build、缓存未进入 Git | `git status`、ignore 检查 |
| P01-A12 | 冻结完整性 | 编辑前后冻结校验返回 0 | 命令输出 |
| P01-A13 | 修改范围 | 所有 tracked 修改均在 Phase 01 allowlist | diff 审查 |
| P01-A14 | Suite 注册表 | 七个固定 suite、状态和依赖完整，`contract_version` 与 registry hash 已记录 | registry/schema、suite JSON |
| P01-A15 | 跨记录语义 | duplicate ID、悬空引用和依赖环均被语义校验器拒绝 | negative-control JSON |
| P01-A16 | Runner 可追溯 | runner、doctor 和全部实际加载 helper 的源 SHA-256 进入证据 | environment/suite JSON |
| P01-A17 | Staged diff | staged/unstaged 的 check、stat、name-status 均已审查且未越界 | Git 命令输出 |
| P01-A18 | Capability profiles | host profile 要求 Docker daemon；container profile 不要求 Docker-in-Docker且无 socket mount | doctor JSON、Compose 审查 |
| P01-A19 | Pip 工具链 | installer pip 版本和来源固定，Windows/容器一致，bootstrap 不调用全局 pip；独立 tool lock 如存在则含 hash | doctor、bootstrap/lock 证据 |
| P01-A20 | OS/architecture 支持 | Windows host 与固定 Linux 容器实测；macOS/其他仅声明 Docker fallback或UNTESTED | inventory/support matrix、suite evidence |
| P01-A21 | 安全 dispatcher | registry 驱动确定性展开；0 component、unknown entrypoint、重复/cycle/shell payload 均失败 | semantic negative controls |
| P01-A22 | Python 供应链 | 安装源获批准，URL/package、SHA-256、Authenticode/签名和安装 scope 均已核验记录 | supply-chain evidence |

P01-A01 至 P01-A22 全部通过后才可标记 COMPLETE。

## 11. AWAITING 与 BLOCKED 规则

以下情况需要先完成安全的只读诊断，确认没有可执行的安全路径时标记 `BLOCKED`：

- 无法获得或运行选定的准确 CPython 版本。
- Windows 或 Linux 无法从同一 hash lock 安装。
- Docker daemon 不可连接或固定 digest 无法解析。
- host/container profile 选择不受控、容器错误要求 Docker daemon，或 Compose 挂载 Docker socket/engine pipe。
- installer pip 未固定、Windows/容器不一致、bootstrap 调用全局 pip，或 bootstrap-tool lock 缺少 hash。
- Windows host 或固定 Linux 容器未实际运行，或文档对未测试 host 声称原生支持。
- CPython 安装器 hash/签名无法验证，或唯一可用路径要求执行未校验脚本/镜像。
- 依赖冲突、`pip check` 失败或安装绕过 hash。
- bootstrap 借用了全局包或依赖 activation 才能成功。
- 未实现 suite 返回 0。
- validation-suites registry 缺少固定 suite、存在重复/悬空引用/依赖环，或其状态与入口行为不一致。
- dispatcher 接受 registry 中的任意 shell/module 命令，或未拒绝 0 component/unknown entrypoint。
- 证据缺少 `contract_version`/registry hash 或 runner/helper 源 hash。
- 需要改动冻结文件或超出允许范围才能继续。

安装器来源/scope、`.venv` lock 安装、镜像 pull/build 或其他供应链动作尚未取得用户确认时标记 `AWAITING_HUMAN_DECISION`。两种情况都先按 `human-intervention-policy.md` 把当前进度和证据写入 `CHECKPOINT.md`，再停止；不把单个平台成功写成阶段 COMPLETE。

## 12. 交接

Phase 02 的进入包必须包含：

- `STATUS.md` 中 Phase 01 `COMPLETE` 小节。
- 准确 Python 版本、lock hash 和镜像 digest。
- 固定 pip 版本/来源、bootstrap-tool lock hash（如适用）和团队 OS/architecture support matrix。
- Windows `.venv` 和 Docker environment suite 的成功证据。
- 统一入口的 suite/exit-code 合同。
- validation-suites `contract_version`/registry hash、跨记录语义校验和 duplicate-ID 负控证据。
- runner/helper 源 hash 清单。
- 尚未实现 suite 的 NOT_IMPLEMENTED negative-control 证据。
- 环境和网络边界的剩余风险。
- `CHECKPOINT.md` 为空闲状态的确认。

Phase 02 只能扩展 `baseline` suite，并继续保持 `traceability`、`v0.4-model`、`v0.4` 和 `all` 的非零 NOT_IMPLEMENTED 状态，除非当前阶段明确实现其组合语义。

## 13. Stop

完成 `STATUS.md` 中 Phase 01 小节、审查 staged/unstaged diff、再次通过冻结校验后立即停止。不要运行或修复 v0.1–v0.3 语义基线，不要创建 validation-suites registry 之外的业务 manifest，不要开始 Phase 02。
