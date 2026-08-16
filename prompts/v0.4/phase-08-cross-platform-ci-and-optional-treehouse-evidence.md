# Phase 08 Prompt — 跨平台、CI、Clean-room 与可选 Treehouse 证据

只实施 Phase 08。开始前完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md` 和本文件；进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。

## 1. 目标

把同一个 `scripts/validate.py` 编排核心接入 Windows PowerShell 5.1+、Linux shell、Docker 和 GitHub Actions，完成 `scripts/reproduce.ps1`/`scripts/reproduce.sh` 单命令复现和本地 clean-room rehearsal，并为 Semantic Treehouse、Mermaid 完整渲染和外部 ITB/SEMIC 建立严格隔离、可真实延期的证据轨。所有入口只消费 Phase 07 已冻结的 `C_Semantic_Treehouse/manifests/validation-suites.json`，不得修改其 `contract_version` 或 `all` composition。

核心结果是可核验的跨平台/CI 工程合同：依赖和镜像固定、wrapper 无第二套逻辑、CI fail closed、报告始终上传、干净环境可从锁文件运行。实际 GitHub run 和 GitHub remote clean clone 由 Phase 09 在获得发布授权后完成。

## 2. 非目标

- 不改变 model、requirements、fixtures、test oracle、SPARQL、quality、governance 或 handoff 语义。
- 不自动 commit、配置 remote、push、打 tag、创建 GitHub repository/release 或改写历史。
- 不要求 Semantic Treehouse、Mermaid renderer、ITB 或 SEMIC 成为核心 `--suite all` 依赖。
- 不声称 Treehouse import/export、UI/API、CI 或外部 validator 成功，除非当前阶段确实运行且保存证据。
- 不删除非本项目 Docker container、network 或 volume。
- 不修复 Phase 00–07 的环境、模型、oracle、suite、文档或 checker 逻辑；发现缺陷时返回对应最早 Phase。

## 3. 权威输入

1. Phase 01 的 Python 完整补丁版本、`requirements.lock`、lock hash、bootstrap/doctor/validate wrappers 和基础容器决定
2. 四个 manifests 及 schemas
3. Phase 05/06 的机器结果
4. Phase 07 已验证 README、报告、图表和 handoffs
5. `docs/v0.4/STATUS.md` 中 Phase 07 小节
6. `docs/environment.md`
7. `tools/semantic-treehouse/README.md` 和 v0 Treehouse 脚本，仅作风险参考
8. `archive/v0_ci/`、`archive/v0_tooling/`，仅作历史参考，禁止直接恢复为现行入口
9. `C_Semantic_Treehouse/manifests/validation-suites.json`、`C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`、`STATUS.md` 中 Phase 07 小节记录的 `contract_version` 和 SHA-256；本阶段只读并在每个环境证据中重复记录 hash

## 4. 进入门槛

- Phase 00–07 全部在 `docs/v0.4/STATUS.md` 中记录为 `COMPLETE`。
- Phase 07 小节和 documentation validation 结果存在且 freshness/hash 通过。
- 使用当前 native host 对应的显式 `.venv` 解释器和薄包装完成进入检查。Windows 实际命令以 `.\.venv\Scripts\python.exe scripts\doctor.py --profile host`、`.\scripts\validate.ps1 -Suite all` 为准；Linux native host 以 `./.venv/bin/python scripts/doctor.py --profile host`、`./scripts/validate.sh --suite all` 为准。固定 validation container 使用镜像内固定 `python scripts/doctor.py --profile container`，不要求容器预存仓库 `.venv`。禁止 native host 使用裸 `python`，当前 `all` 必须实际退出 0。
- `requirements.lock` 可由锁定 Python 安装，hash mode 和 `pip check` 已通过。
- Docker 轨若要执行，daemon 必须可连接。需要用户启动/配置 Docker 时标记 `AWAITING_HUMAN_DECISION`；经确认仍客观不可用且没有安全路径时 Phase 08 为 `BLOCKED`。该项不能 DEFERRED。
- `C_Semantic_Treehouse/manifests/validation-suites.json` 的 `contract_version`/hash 与 `STATUS.md` 中 Phase 07 小节一致，通过既有 schema，`all` 已包含 Phase 00–07 的全部 required checks。
- `docs/v0.4/CHECKPOINT.md` 为空闲。
- 已审查 `git status --short --branch`、unstaged diff 和 staged diff；可写 CI/tooling 文件中的用户修改已识别并可安全保留。

任一门槛失败时，先完成安全诊断，把当前进度写入 `CHECKPOINT.md`。需要确认重叠修改归属或启动/配置 Docker 时标记 `AWAITING_HUMAN_DECISION`；确认没有安全路径时标记 `BLOCKED`。

## 5. 可写路径与保护路径

### 可写路径

- `.github/workflows/validate.yml`
- `Dockerfile.validation`
- `docker-compose.validation.yml`
- `scripts/reproduce.ps1`
- `scripts/reproduce.sh`
- `scripts/clean_room.py`
- `scripts/check_ci.py`
- `scripts/check_treehouse_compose.py`
- `scripts/README.md`，仅增加本阶段具名 reproduce、CI、clean-room 和可选证据脚本的用法/边界
- `tools/semantic-treehouse/README.md`
- `tools/semantic-treehouse/upstream.lock.json`
- `C_Semantic_Treehouse/scripts/treehouse_clone_or_update.ps1`
- `C_Semantic_Treehouse/scripts/treehouse_clone_or_update.sh`
- `C_Semantic_Treehouse/scripts/treehouse_up.ps1`
- `C_Semantic_Treehouse/scripts/treehouse_up.sh`
- `C_Semantic_Treehouse/scripts/treehouse_down.ps1`
- `C_Semantic_Treehouse/scripts/treehouse_down.sh`
- `C_Semantic_Treehouse/scripts/treehouse_status.ps1`
- `C_Semantic_Treehouse/scripts/treehouse_status.sh`
- `.gitignore`、`.gitattributes`、`.dockerignore`，仅允许为本阶段具名的 build、Treehouse upstream、reproduce/clean-room 文件增加精确规则；禁止扩大通配范围、重排或删除无关既有规则
- `docs/environment.md`
- `docs/v0.4/reproducibility-contract.md`
- `C_Semantic_Treehouse/C_semantic_treehouse_usage.md`，仅限同步本阶段可选轨的真实状态和 evidence 引用
- `C_Semantic_Treehouse/scripts/README.md`，仅限同步具名 Treehouse wrappers/preflight 的实际状态和证据入口
- `build/phase-08/**`
- `build/clean-room/**`
- `build/ci/**`
- `build/evidence/{treehouse,mermaid,itb-semic}/**`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`

### 本阶段额外保护路径

- Master 永久保护范围全部只读。
- `C_Semantic_Treehouse/model/**`、`fixtures/**`、`manifests/**`、`tests/**`、`mappings/**`、`quality/**`、`governance/**`、`handoff/**`、`diagrams/**` 只读。
- Phase 05–07 的机器结果只读。
- `C_Semantic_Treehouse/manifests/validation-suites.json`、`C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`、`scripts/validate.py`、`scripts/doctor.py`、`scripts/bootstrap.ps1`、`scripts/bootstrap.sh`、`scripts/validate.ps1`、`scripts/validate.sh`、`Makefile`、`scripts/check_documentation.py` 和 Phase 00–06 checker 全部只读。
- `docs/v0.4/STATUS.md` 中 Phase 00–07 的历史小节、`docs/v0.4/requirements-traceability.md`、`risk-register.md`、`decisions/**` 和其他既有决策/风险文档全部只读。
- 除本阶段明确列出的 `reproducibility-contract.md` 外，其他 `docs/v0.4/**` 全部只读。
- 除本阶段可精准更新的 `C_semantic_treehouse_usage.md` 与 package `scripts/README.md` 外，Phase 07 的 README、核心报告、handoff、AI 治理文档和图表全部只读。
- `C_Semantic_Treehouse/evidence/releases/v0.4/**` 留给 Phase 09 审核固化。
- 已有 Git remote、提交、tag 和远程状态只读，除非用户另行明确授权；当前 Phase 仍不得 push。

## 6. 任务

### 6.1 固化薄包装合同

审查以下既有入口并以只读方式验证：

- Windows PowerShell 5.1+：显式调用 `.venv\Scripts\python.exe`。
- Linux shell：显式调用 `.venv/bin/python`。
- Make：只转发到同一个 Python 入口，不能实现验证规则；本阶段只读复验。
- Docker：容器内调用同一个 `scripts/validate.py`。

wrapper 必须可靠定位脚本自身对应的仓库根，支持空格和非 ASCII 路径，原样传递 suite 参数和退出码。Windows 核心流程不得依赖 GNU Make、POSIX shell 或 PowerShell 7。若这些既有入口存在缺陷，记录证据，说明应回到 Phase 01 修复，并停下来找人确认；本阶段不得修改它们。

创建并完成两个单命令入口：

- `scripts/reproduce.ps1`：兼容 Windows PowerShell 5.1，定位仓库根，调用既有 `bootstrap.ps1`，随后固定调用 `validate.ps1 -Suite all`，原样返回失败退出码。
- `scripts/reproduce.sh`：定位仓库根，调用既有 `bootstrap.sh` 创建/核验仓库 `.venv`，随后固定调用 `validate.sh --suite all`，原样返回失败退出码。

两者不得接受改变 suite composition 的参数，不得内嵌第二套验证规则，不得回落到全局 Python。已存在 `.venv` 时仍必须核对 Python/lock/`pip check`，不得把陈旧环境当作成功。两个入口都要在全新隔离目录实际运行，并覆盖含空格和非 ASCII 的路径；`reproduce.sh` 的从零测试可以在单独的 clean Linux container 中由 bootstrap 创建 `.venv`，不能复用或挂载宿主 `.venv`。

### 6.2 加固 Docker 发布验证

`Dockerfile.validation` 至少满足：

- 基础 Python image 使用完整版本 tag 和 digest。
- 从含 hashes 的 `requirements.lock` 安装，依赖/hash 不匹配立即失败。
- 运行 `pip check`。
- 使用非 root 用户执行验证。
- `.dockerignore` 或等价边界排除 `.git`、`.venv`、`build`、cache、secret 和 Treehouse upstream。
- 工作目录和 entrypoint 不依赖宿主绝对路径。
- 默认执行 `python scripts/validate.py --suite all`。
- 容器 doctor 固定使用 `python scripts/doctor.py --profile container`；镜像内 Python 是已锁定运行时，不要求仓库 `.venv`。
- validation container 禁止挂载 `docker.sock` 或其他 daemon/control socket。

`docker-compose.validation.yml` 只编排该验证镜像，不嵌入第二套规则，不挂载宿主 `.venv`，并使报告写入明确的 `build/` 目标。至少执行一次无缓存 build 和一次容器验证。

### 6.3 建立 GitHub Actions workflow

创建现行 `.github/workflows/validate.yml`，至少包含：

1. Ubuntu 原生 Python job。
2. Windows PowerShell job。
3. Docker clean-room job。

每个 job 必须运行 frozen/environment/baseline/traceability/v0.4-model/v0.4/all 中适用的完整合同，并具备：

- workflow 只允许 `push`、`pull_request` 和 `workflow_dispatch` 触发；`push.branches` 只列经批准的默认/集成分支，`pull_request.branches` 只列经批准的目标分支，禁止全分支通配、含糊的 `branches-ignore` 组合和把未经校验的 `workflow_dispatch` input 拼接进 shell。
- 禁止 `pull_request_target`、`workflow_run` 驱动的未审查代码执行和任何等价高权限 PR 模式。
- 明确 runner label；避免 `*-latest`。
- Python 完整补丁版本。
- GitHub Actions 以完整 commit SHA 固定，并用注释标明发布版本。
- `permissions: contents: read`。
- checkout 使用 `persist-credentials: false`；PR job 不获得写权限或 repository secrets。
- 每个 validation job 使用 `timeout-minutes: 30`，并配置 concurrency cancellation。
- lock hash 安装与 `pip check`。
- 核心步骤无 `continue-on-error`。
- `if: always()` 上传 `build/` 下机器 JSON、Markdown 和环境清单。
- `if-no-files-found` 不能静默成功。
- job summary 清楚区分业务状态和程序状态。
- 不需要 secrets，也不执行 Treehouse/外部 validator。

创建具名 `scripts/check_ci.py`。workflow 必须通过 YAML 解析和静态 policy 检查，至少验证 triggers/branch filters、禁止 `pull_request_target`、只读权限、checkout credentials、action SHA、runner、timeout、lock 安装、required jobs、无 `continue-on-error` 和 always-upload。checker 同时提供可由后续只读导入的确定性通用 policy API（permissions、action pins、checkout、runner、timeout、shell、artifact），并把 `validate.yml` 专属的三触发器/三 job profile 与通用谓词分开；后续 release workflow 可以复用通用谓词，同时采用更窄的发布触发器 profile。

`check_ci.py --self-test` 必须在临时目录中运行 negative controls，分别证明以下配置被非零拒绝：`pull_request_target`、缺少任一 required trigger、无 branch filter、全分支通配/不安全 branch 规则、未经校验的 dispatch input shell 拼接、写权限、`persist-credentials: true`、浮动 action tag、`*-latest`、`continue-on-error`、缺少 required job、缺少/弱化 artifact upload。negative control 未执行或意外返回 0 时本阶段阻塞。仅有 workflow 文件不等于 CI 已通过；实际 run 由 Phase 09 验收。

### 6.4 本地 clean-room rehearsal

通过具名 `scripts/clean_room.py` 建立可重复的 clean-room 脚本/流程：

- 将当前 release candidate 的源文件复制或导出到 `build/clean-room/` 的新目录，明确排除 `.venv`、`build`、cache、external upstream、secret 和本机配置。
- 记录导出文件清单和 hashes，确保未遗漏当前候选中的必要 tracked/untracked 文件。
- 在隔离目录从 lock bootstrap，运行 `doctor` 和 `--suite all`。
- 验证结束后没有源目录污染；隔离目录中的生成物只位于允许的 build 路径。
- 路径报告规范化，不把临时绝对路径写入稳定结果。
- clean-room 脚本只能写入经过解析核验的 `build/clean-room/`，不能删除该目录外内容；源清单、排除清单和输出 hash 必须由机器记录。

这一步称为 release-candidate clean-room rehearsal。Phase 09 必须对已提交 commit 执行真正 `git clone`，两者不得混淆。

### 6.5 跨平台实际运行

分别记录 native host 与 validation container：

- Windows native host 必须实际运行 `.\.venv\Scripts\python.exe scripts\doctor.py --profile host`、`.\scripts\validate.ps1 -Suite all` 和 `.\scripts\reproduce.ps1`。
- 若有 Linux native host，必须实际运行 `./.venv/bin/python scripts/doctor.py --profile host`、`./scripts/validate.sh --suite all` 和 `./scripts/reproduce.sh`。
- 固定 Linux validation container 必须使用镜像内固定 Python 运行 `python scripts/doctor.py --profile container` 和 `python scripts/validate.py --suite all`；不得要求预存仓库 `.venv`，不得挂载宿主 `.venv` 或 `docker.sock`。
- `reproduce.sh` 的从零 Linux 证据应在另一 clean Linux container/目录中运行，让脚本自行 bootstrap `.venv`，与 validation image 的 container profile 证据分开。

各轨分别记录 OS/architecture/Python/pip/validator/lock hash、`C_Semantic_Treehouse/manifests/validation-suites.json` 的 `contract_version`/hash 和退出码，禁止把 container profile 报告成 native-host profile。

若当前已有经用户授权的 GitHub remote，可以只读查看已有 Actions 运行；不得触发 push 或修改远程。远程 run 不存在时记录 `NOT RUN — Phase 09 publication gate`，不能标为 DEFERRED 或 PASS。

### 6.6 Semantic Treehouse 可选证据轨

仅在 Docker 核心 gate 已通过，并且用户对"执行第三方 Semantic Treehouse Docker workload"给出本次明确 opt-in 后尝试。缺少 opt-in 时保持 `NOT RUN` 或 `DEFERRED`，不得 clone 后自动 build/up。

在任何第三方 image build、pull、Compose `up` 或 container execution 前，必须对固定 upstream commit 做静态安全预检，并把报告展示给用户。创建具名 `scripts/check_treehouse_compose.py`，至少检查：

- `privileged: true`。
- `docker.sock`（包括 `/var/run/docker.sock`）或其他 daemon/control socket 挂载。
- host bind mounts，特别是仓库外、home、root、credential 和可写系统路径。
- `cap_add`、`devices`、`security_opt` 和高权限 user。
- `network_mode: host`、额外网络和对外监听。
- 全部 published ports、绑定地址、冲突和暴露范围。
- `.env`/secret/config 的来源、自动复制行为和日志泄漏风险。
- 每个第三方 image 是否固定 digest，build context/Dockerfile 是否在固定 commit 内。
- volume 删除、container name、project name 和 cleanup 边界。

出现上述高风险配置、未固定 image digest、无法理解的 build script 或超出已批准边界的资源访问时，禁止执行并向用户请求针对该风险的二次 opt-in；未获批准则记录 DEFERRED。不得静默编辑第三方 upstream 来掩盖风险。

通过 opt-in 和静态预检后：

- 用版本锁文件记录 upstream URL、完整 commit、预期 license/reference 和 compose 入口。
- 精确 fetch/checkout 固定 commit；禁止跟随默认分支更新。
- clone 位于 Git 忽略目录，验证 HEAD 与 lock 一致。
- 使用唯一 Compose project name 和可配置端口。
- 只管理带本项目 Compose label 的 resources；默认 down 不删除 volume。
- 记录 Docker/Compose、upstream commit、命令、容器状态和 smoke URL。
- 使用隔离的、Git 忽略的最小配置；不得自动复制真实 `.env`。日志在进入证据前扫描 token、`.env`、credential、用户名和绝对路径。
- import、export、UI/API 功能分别记录 `PASS`、`FAILED` 或 `NOT RUN`；只有实际操作才可 PASS。

Treehouse 启动失败必须保存真实 exit code、静态预检、opt-in decision、清理后的日志、影响分析和 independent validation fallback。失败可标记该可选轨为 `DEFERRED`，不影响 Phase 08 核心门槛。

### 6.7 Mermaid 与外部 ITB/SEMIC 可选证据

- 若使用真实 Mermaid renderer，固定工具版本/容器 digest，保存 parser/render exit code，渲染到 `build/evidence/mermaid/` 并由人工检查可读性、截断、重叠、连线和标签；缺工具或失败可 DEFERRED。Phase 07 只有 structure-lint PASS，不能称为 source syntax PASS。
- ITB/SEMIC 只允许使用公开、明确版本的实例/工具。任何向外部服务上传 fixture、Shape、report 或 repository 内容前，另行取得明确的数据外传授权，向用户列明目标 endpoint/operator、待上传文件及 hashes、数据分类、可能包含的信息、retention/terms 和返回结果保存方式。没有数据外传授权时禁止上传并记录 DEFERRED。
- 获得授权后记录请求边界、输入 hashes、实际结果和外部服务版本；不得上传来源 ZIP、secret、个人路径或未列明文件。
- 两条可选轨均不能修改 core oracle，也不能进入 required CI job。

### 6.8 更新环境与证据边界说明

更新 `docs/environment.md` 和 `docs/v0.4/reproducibility-contract.md`，准确记录：支持平台、完整工具版本、首次下载网络边界、离线核心运行条件、`reproduce.ps1`/`.sh` 单命令、Docker 命令、CI job、clean-room rehearsal、suite registry `contract_version`/hash、可选证据状态和 Phase 09 尚需完成的实际 GitHub run/remote clone。

同步更新 `scripts/README.md`，只登记本阶段实际存在并已验证的 `reproduce`、CI policy、clean-room 和 Treehouse preflight 入口；统一引用底层 validator，不复制规则说明或宣称远程 CI 已运行。

若 Treehouse 可选轨状态或 evidence 引用变化，可以精准更新 `C_Semantic_Treehouse/C_semantic_treehouse_usage.md` 和 `C_Semantic_Treehouse/scripts/README.md` 的对应状态/路径段落。更新后必须用 Phase 07 的只读 `scripts/check_documentation.py` 重新运行正常检查和 negative controls；发现文档 checker 逻辑缺陷时说明应回到 Phase 07 处理并停下来找人确认，不在 Phase 08 修改 checker。

### 6.9 冻结 registry 与上游缺陷路由

Phase 开始和结束均计算 `C_Semantic_Treehouse/manifests/validation-suites.json` SHA-256，并核对其 schema 与 `contract_version`，写入 host、Docker、clean-room 和 CI 静态证据。`contract_version`、hash 或 `all` composition 发生变化时立即标记 `AWAITING_HUMAN_DECISION` 并说明需要回到 Phase 07 处理。

发现缺陷时按来源确定最早受影响 Phase：环境/lock/bootstrap/wrapper/核心编排为 Phase 01；baseline 为 Phase 02；traceability/decision 为 Phase 03；model/release manifest 为 Phase 04；fixtures/四状态 harness 为 Phase 05；SPARQL/quality/governance 为 Phase 06；文档/checker/suite registry 为 Phase 07。记录证据和归属 Phase，标记 `AWAITING_HUMAN_DECISION` 并停止；Phase 08 只修复本阶段具名 CI、reproduce、clean-room 和可选证据文件。

## 7. 产物

- Phase 01 既有 Windows/Linux/Make 薄包装的只读复验证据
- `scripts/reproduce.ps1` 和 `scripts/reproduce.sh` 单命令入口及实际运行证据
- 固定版本和 digest 的 Docker 验证入口
- `.github/workflows/validate.yml`
- `scripts/check_ci.py`、CI static/policy 结果和 negative-control 结果
- `scripts/clean_room.py`
- Treehouse Compose 静态安全预检及 opt-in 记录（若尝试）
- `build/clean-room/` rehearsal 清单、环境和验证结果
- Windows 与 Linux-container 执行证据
- 可选 Treehouse/Mermaid/ITB-SEMIC 证据或真实 DEFERRED 记录
- 更新后的环境与复现说明
- 更新后的 `scripts/README.md`
- 可选轨状态变化时精准更新的 `C_semantic_treehouse_usage.md` 及文档复验结果
- package scripts README 中具名 Treehouse wrapper/preflight 的真实状态（若变化）
- 各环境记录的只读 suite registry `contract_version`/hash
- `build/phase-08/**`
- `docs/v0.4/STATUS.md` 中的 Phase 08 小节

## 8. 必需命令

先审计 unstaged、staged 和 untracked 状态：

```text
git status --short --branch
git diff --check
git diff --cached --check
git diff --stat
git diff --cached --stat
git diff --name-status
git diff --cached --name-status
```

Windows host 必须实际运行：

```powershell
.\.venv\Scripts\python.exe scripts\verify_frozen_files.py
.\.venv\Scripts\python.exe scripts\doctor.py --profile host
.\.venv\Scripts\python.exe scripts\check_ci.py --self-test
.\scripts\validate.ps1 -Suite all
.\scripts\reproduce.ps1
```

Linux native host 可用时必须实际运行：

```bash
./.venv/bin/python scripts/verify_frozen_files.py
./.venv/bin/python scripts/doctor.py --profile host
./.venv/bin/python scripts/check_ci.py --self-test
./scripts/validate.sh --suite all
./scripts/reproduce.sh
```

固定 Linux validation container 必须实际运行：

```bash
python scripts/doctor.py --profile container
python scripts/check_ci.py --self-test
python scripts/validate.py --suite all
```

该 validation container 使用镜像内锁定 Python，不要求仓库 `.venv`，不得挂载宿主 `.venv` 或 `docker.sock`。另在 clean Linux container/目录中执行 `./scripts/reproduce.sh`，由它从 lock 创建 `.venv` 并完成 `all`。

还必须运行并记录：

- 使用显式 `.venv` Python 的 `scripts/check_ci.py` 正常检查和 deterministic rerun。
- Docker 无缓存 build 和默认 `--suite all` 入口。
- `scripts/clean_room.py` 及隔离目录中的 doctor（native 为 `--profile host`，validation image 为 `--profile container`）、对应 wrapper `all` 和 reproduce 单命令。
- `scripts/check_documentation.py` 正常检查与 `--self-test`；只读执行。
- suite registry `contract_version`/hash 在 host、Docker、clean-room 中一致。
- Treehouse 仅在 opt-in + 静态安全预检后执行；Mermaid/ITB-SEMIC 仅在各自授权后执行。

最后重复全部 unstaged/staged diff 审计、Git status 和显式 `.venv` frozen 校验。具体 wrapper/Docker 命令写入 `STATUS.md`；native host 不得使用裸 `python`，固定 validation container 使用镜像内锁定的 `python`；PowerShell 固定 `-Suite all`，Linux wrapper 固定 `--suite all`，不得增加公开 suite 名称。

## 9. 验收矩阵

| 验收项 | 通过标准 | 证据 |
|---|---|---|
| Windows wrapper | PowerShell 5.1+ 实际调用同一核心并退出 0 | host run evidence |
| Linux native/container | native 可用时以 `.venv` + host profile 验证；固定 container 以镜像 Python + container profile 验证，二者身份不混淆 | platform results |
| 单命令复现 | `reproduce.ps1`/`.sh` 从 bootstrap 到 all 均成功并 fail closed | reproduce evidence |
| Docker lock | image digest、hash lock、pip check、非 root 全部满足 | build/run evidence |
| Docker clean | 无宿主 `.venv`/secret/cache 泄漏，报告在 build | image inspection |
| Docker privilege boundary | validation container 未挂载 `docker.sock`、宿主 `.venv` 或其他 daemon socket | compose/image inspection |
| CI workflow | 3 jobs、3 个批准 trigger、安全 branch、无 pull_request_target、action SHA、只读权限、timeout、fail-closed、always-upload | static policy JSON |
| CI checker negative controls | 高权限/危险 trigger、浮动 action、弱化 job/upload 等均被拒绝 | self-test JSON |
| CI 真实性 | 未有远程 run 时明确 NOT RUN，未宣称 PASS | STATUS.md |
| Clean-room rehearsal | 隔离 bootstrap + all 通过，文件清单/hash 完整 | clean-room results |
| 单一核心 | wrappers/Make/Docker/CI 不含第二套规则；Makefile 保持只读 | code/diff inspection |
| 路径兼容 | 空格和非 ASCII 仓库路径测试通过 | path test evidence |
| 核心无回归 | 宿主、Windows wrapper、Linux container、Docker 均成功 | consolidated results |
| 可选轨真实性 | 每项有 PASS/FAILED/NOT RUN/DEFERRED 和证据 | optional evidence index |
| Treehouse 安全 | 第三方执行有用户 opt-in、静态预检、digest/权限/挂载/网络/端口/.env 审查 | preflight/decision |
| 外部数据 | ITB/SEMIC 上传有独立数据外传授权；未授权时零上传 | egress decision/log |
| Mermaid 可选 QA | 只有真实 renderer + 人工视觉检查才可 PASS | render/visual record |
| 文档同步 | Treehouse 状态引用精准，Phase 07 checker/negative controls 重跑通过 | documentation results |
| Registry 冻结 | Phase 07 `contract_version`/hash 在全部环境一致、schema 有效且文件无 diff | registry evidence |
| Ignore/attributes 边界 | 三个文件仅含本阶段具名目标的精确增量，无泛化通配或无关重排 | focused diff |
| 完整性/边界 | frozen 前后通过，unstaged/staged/untracked 逐项审计且未越界 | frozen/diff evidence |

## 10. AWAITING、BLOCKED 与 DEFERRED 规则

### 必须暂停

- Docker daemon/构建不可用，Windows 必需入口或 `reproduce.ps1` 失败，Linux container 或 `reproduce.sh` 失败，lock/digest/action pin 不满足，clean-room rehearsal 失败，workflow static policy/negative controls 失败，核心 `all` 非零，registry `contract_version`/hash 改变，或发现第二套验证逻辑时，先完成安全诊断并把当前进度写入 `CHECKPOINT.md`。存在可批准的启动、配置、修复或路由选项时标记 `AWAITING_HUMAN_DECISION`；诊断确认当前没有安全路径时标记 `BLOCKED`。
- 上游逻辑问题按 6.9 路由到最早受影响 Phase，取得用户确认后才恢复；不得在本阶段修改受保护实现。
- 实际 GitHub Actions 尚未运行不会单独阻止 Phase 08；它是 Phase 09 的必需发布门槛，当前必须记录 `NOT RUN`。

### 允许 DEFERRED

仅以下独立证据轨可以 DEFERRED：

- Semantic Treehouse deployment/UI/API/import/export；缺用户 opt-in、静态安全预检未通过或高风险未获二次批准时保持 DEFERRED，禁止执行。
- Mermaid 完整渲染与视觉 QA。
- 外部 ITB/SEMIC 实际运行；缺数据外传授权时保持 DEFERRED，禁止上传。

DEFERRED 必须包含尝试条件、实际命令/退出码或未尝试理由、日志/状态路径、影响和恢复步骤。DEFERRED 不得改变核心 Phase 08 的 COMPLETE 判断。

## 11. 阶段交接

核心验收全部通过后：

1. 在 `docs/v0.4/STATUS.md` 追加 Phase 08 小节，分别列出 required matrix、optional evidence matrix 和风险。
   风险处置引用 Phase 00 baseline snapshot risk ID；不回写该 snapshot，新增风险登记供 Phase 09 汇总。
2. 把 `docs/v0.4/CHECKPOINT.md` 清空回占位符状态；可选轨在各自条目中保留 `DEFERRED`，不能把整个 Phase 标为 DEFERRED。
3. 向 Phase 09 交付：跨平台与 reproduce 结果、Docker digest、workflow 静态/negative-control 检查、clean-room rehearsal、suite registry `contract_version`/hash、可选证据的 opt-in/egress 状态，以及"实际 GitHub Actions/remote clone 尚待发布授权"的明确门槛。
4. 报告 unstaged、staged、untracked Git 状态，不 commit、不 push、不配置 remote。

## 12. Stop

Phase 08 标记 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。不得自行执行 GitHub push、tag、release、远程 workflow 或最终证据固化。
