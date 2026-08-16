# 环境审计

本文件区分迁移时观察、Phase 00 进入快照、Phase 01 可复现环境合同与 Phase 08 跨平台/CI/clean-room 合同。历史观察保持原样；当前执行以固定版本、lock、统一入口和 active-Phase 证据为准。

## 1. 迁移时观察（2026-08-07）

| 组件 | 迁移时观察 | 解释 |
|---|---|---|
| Git | 2.45.1.windows.1 | 当时尚未初始化当前新仓库；该结论作为迁移快照保留 |
| Python | 3.13.7，全局 pip 25.2 | 当时不满足计划的 CPython 3.12 正式环境 |
| Windows PowerShell | 5.1.26100.8875 | 可用于 Windows `.ps1` 入口 |
| Docker client | 29.4.1 | 已安装 |
| Docker Compose | 5.1.3 | 已安装 |
| Docker daemon | 连接失败 | 当时 Docker Desktop/Engine 未运行或 pipe 不可用 |
| GNU Make | 未发现 | Windows 核心流程不得依赖它 |
| `sh` | 未发现 | Linux 脚本需在 Linux/CI/Docker 验收 |
| PowerShell 7 (`pwsh`) | 未发现 | Windows 入口以 PowerShell 5.1+ 为合同 |

迁移后维护者初始化了当前仓库。Git 的现行事实见下一节及 `docs/v0.4/STATUS.md`；本节不随环境变化回写。

## 2. Phase 00 本次观察（2026-08-09）

证据命令包括 `git --version`、`docker --version`、`docker compose version`、`docker info --format '{{.ServerVersion}}'`、PowerShell/.NET 系统信息和 `Get-Command`。机器专属信息保存在 `build/phase-00/reconciliation-2026-08-09/machine-environment.json`；实际绝对仓库路径只进入该环境文件。

| 组件 | 本次观察 | 当前判断 |
|---|---|---|
| OS / architecture | Windows NT 10.0.26200.0，X64 | 当前认证工作将在 Windows host 上进行 |
| Git | 2.45.1.windows.1 | 当前仓库为 `main`、7 个提交、无 remote；Phase 00 entry 工作树 clean |
| Windows PowerShell | 5.1.26100.8875 Desktop | 本次 PowerShell 5.1 审计脚本执行成功；本机策略要求以进程级 `-ExecutionPolicy Bypass` 运行新脚本 |
| Docker client | 29.4.1 | 本次观察可用 |
| Docker server | 29.4.1 | 本次观察 daemon 可连接；该结果不等于固定镜像或容器验证通过 |
| Docker Compose | v5.1.3 | 本次观察可用 |
| `python` / `py` | 命令可发现 | Phase 00 未执行全局 Python，未形成版本或依赖验收 |
| `pwsh` | 未发现 | 继续以 Windows PowerShell 5.1+ 作为 Windows 薄包装合同 |
| GNU Make | 未发现 | Windows 核心流程继续保持独立于 Make |
| `sh` | 未发现 | Linux shell 轨需在 Linux/CI/容器中验证 |
| `.venv/` | ignored 目录已存在，3638 个文件；`pyvenv.cfg` 写明 3.12.10 | 用户确认它来自一次已 Git 回档的 Phase 00/01 agent 尝试；当前没有 lock、doctor、bootstrap 或 STATUS 证明，未被接受为正式环境 |

## 3. Phase 01 固定环境（2026-08-09）

### 3.1 Python、pip 与 lock

| 项 | 固定值 |
|---|---|
| Python implementation / version | CPython 3.12.10 |
| `.python-version` | `3.12.10` |
| CPython `ensurepip` bundle | 25.0.1 |
| 安装执行器 | pip 25.0.1，只通过选定解释器的 `-m pip` 调用 |
| Lock generator | pip-tools 7.4.1 |
| Bootstrap tools | pip 25.0.1、pip-tools 7.4.1、setuptools 75.8.2、wheel 0.45.1 |
| PyPI index | `https://pypi.org/simple` |
| Runtime lock SHA-256 | `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2` |
| Bootstrap lock SHA-256 | `8b94bcc369c574d801a5d0923df54b103efc4dfd1bdadb508846a3cd42a81bff` |

根 `requirements.in` 是直接依赖的唯一输入，根 `requirements.lock` 是直接与传递依赖的唯一安装 lock。直接依赖固定为代码实际使用的 `rdflib`、`pyshacl`、`PyLD`、`jsonschema`、`PyYAML` 和 `openapi-spec-validator`。`C_Semantic_Treehouse/requirements.txt` 只转发到根 lock。普通 bootstrap 使用 `--require-hashes` 消费已提交 lock，不执行依赖求解。

`requirements.lock.json` 记录生成器、生成命令、索引、输入 hash、lock hash 和自举工具版本。doctor 会校验这些绑定、安装集合、准确版本、意外包、缺失包和 `pip check`。

### 3.2 OS / architecture inventory 与支持矩阵

inventory 只记录本轮实际运行或已知设备。

| 角色/平台 | OS / architecture | 状态 | 本轮用途 |
|---|---|---|---|
| Phase 01/02 执行主机 | Windows 11，NT 10.0.26200，AMD64 | `SUPPORTED_AND_TESTED` | 原生 bootstrap、host doctor、`frozen`/`environment`/`baseline` |
| 固定发布容器 | Linux，amd64 | `SUPPORTED_AND_TESTED` | 固定 digest clean-room build/run、container `frozen`/`environment`/`baseline` |
| WSL2 Linux host | Ubuntu 24.04.4 LTS，WSL2 kernel 6.6.87.2，x86_64 | `SUPPORTED_AND_TESTED`（WSL2 scope） | CPython 3.12.10 cold bootstrap、host doctor、CI policy/self-test、wrapper `all` 与 clean-room rehearsal |
| 独立 / bare-metal Linux host | UNKNOWN | `UNTESTED` / `DOCKER_FALLBACK` | 当前采用已实测 WSL2 或固定 Linux 容器；设备信息由维护者收集 |
| 原生 macOS host | UNKNOWN | `UNTESTED` / `DOCKER_FALLBACK` | 当前采用固定 Linux 容器；设备信息由维护者收集 |
| 其他原生平台 | UNKNOWN | `UNTESTED` | 新增支持前由维护者取得实际 bootstrap、doctor 与 suite 证据 |

Windows 主机使用 PowerShell 5.1 入口，无需 PowerShell 7、GNU Make 或 `sh`。Linux shell 入口已在上述 WSL2 host 实际运行；该证据只覆盖 WSL2，独立 / bare-metal Linux 支持仍需对应机器的 bootstrap、host doctor 和 suite 证据。

### 3.3 固定 Linux 容器

| 项 | 值 |
|---|---|
| 完整基础标签 | `python:3.12.10-slim-bookworm` |
| OCI index digest | `sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` |
| linux/amd64 child manifest | `sha256:97983fa8cc88343512862c62307159a82261c3528dc025f79e5a3f7af43e50b4` |
| 运行用户 | uid/gid `10001:10001`，非 root |
| Profile | `container` |
| 运行期网络 | `none` |
| 宿主挂载 | 单一 Phase 08 evidence bind：`./build/ci/docker:/workspace/build` |

镜像内包含仓库源码和冻结输入。Compose 不挂载宿主源码、`.venv`、Git 目录、其他 build 残留、secret、Docker socket 或 Windows engine pipe；容器根文件系统为只读，`build/ci/docker` 是唯一宿主 evidence sink。registry 仍在容器内选择 active Phase 和实际输出子目录。container doctor 将 Git、Docker client/server/Compose 和 daemon 能力记录为 `not_required`。

## 4. 从零建立环境

### 4.1 Windows AMD64（受支持原生轨）

从官方 Python 发布目录下载 `python-3.12.10-amd64.exe`：

```text
https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
```

执行安装器前核验文件。Phase 01 采用的发布物 SHA-256 为 `67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb`，Authenticode 状态应为 `Valid`，签名者应为 Python Software Foundation。

```powershell
$Installer = (Resolve-Path -LiteralPath .\python-3.12.10-amd64.exe).Path
(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash.ToLowerInvariant()
Get-AuthenticodeSignature -LiteralPath $Installer | Format-List Status,SignerCertificate
```

经授权后可按当前用户 scope 安装；该命令不修改系统级 PATH：

```powershell
$Process = Start-Process -FilePath $Installer -Wait -PassThru -ArgumentList @(
  '/quiet', 'InstallAllUsers=0', 'PrependPath=0',
  'Include_launcher=1', 'InstallLauncherAllUsers=0'
)
if ($Process.ExitCode -ne 0) { throw "CPython installer exit $($Process.ExitCode)" }
py -3.12 -I -S -c "import ensurepip,platform,sys; print(platform.python_implementation(), sys.version); print('ensurepip', ensurepip.version())"
```

随后从仓库根目录建立 `.venv` 并运行正式入口：

```powershell
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe -I scripts\doctor.py --profile host
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
```

也可通过 `-PythonPath` 显式提供已核验的 CPython 3.12.10。bootstrap 从脚本路径解析仓库根。新建环境由所选 base Python `-I -S` 建立；首次成功写入绑定 base、bootstrap/contract、两份 lock 和 venv 全树 fingerprint 的 trust marker。复用时，base Python 会在启动 venv Python 及其 `.pth` 前静态校验 marker、launcher、`pyvenv.cfg` 和全树 symlink/junction 边界。随后仅调用 `.venv\Scripts\python.exe -I -m pip --isolated`，并把 pip 配置文件固定为空设备，阻断 `target/prefix/root/user` 重定向；最后执行 `pip check` 和 host doctor。重复执行保持同一 lock 与安装集合，未知旧 venv 会要求按第 8 节安全重建。

### 4.2 Linux host（WSL2 已实测；bare-metal 为 Docker fallback）

在组织批准来源安装准确 CPython 3.12.10 后，使用 `PYTHON_PATH` 指向该解释器。脚本不修改 shell profile，也不依赖 Make。

```bash
PYTHON_PATH=/absolute/path/to/python3.12 ./scripts/bootstrap.sh
./.venv/bin/python -I scripts/doctor.py --profile host
./scripts/validate.sh --suite frozen
./scripts/validate.sh --suite environment
```

这些命令是 Linux host 合同。Phase 08 在 Ubuntu 24.04.4 LTS / WSL2 / x86_64 上以普通用户实际执行；环境为 CPython 3.12.10、Git 2.43.0、Docker client 29.3.0 / server 29.4.1、Compose 5.1.3。准确 CPython 从已授权的固定 validation image 的停止态容器导出，经 tar 路径与 runtime 身份检查后只读使用；未向容器挂载 Docker socket、宿主 `.venv` 或源码。WSL2 最终 harness 证据位于 `build/phase-08/linux-v8-final/harness-result.json`，clean-room 机器证据位于 `build/clean-room/路径 with space-linux-v8-final/evidence/`。独立 / bare-metal Linux 继续保持 `UNTESTED` / `DOCKER_FALLBACK`。

### 4.3 Docker 发布轨

validation service 固定使用非 root uid/gid `10001:10001`，宿主环境不能通过变量覆盖。Windows/macOS Docker Desktop 可直接使用该映射；原生 Linux fallback 需要把专用输出目录的写权限授予固定 uid/gid：

```bash
test "$(id -u)" -ne 0
sudo install -d -o 10001 -g 10001 build/ci/docker
export DSSC_SOURCE_COMMIT="$(git rev-parse HEAD | tr '[:upper:]' '[:lower:]')"
if [[ -n "$(git status --porcelain)" ]]; then export DSSC_SOURCE_DIRTY=true; else export DSSC_SOURCE_DIRTY=false; fi
```

Windows/macOS Docker Desktop 在构建前由宿主 Git 设置同一来源状态；容器 baseline 对缺失、`unknown` 或格式错误的值失败关闭：

```powershell
$env:DSSC_SOURCE_COMMIT = (git rev-parse HEAD).Trim().ToLowerInvariant()
$env:DSSC_SOURCE_DIRTY = if (@(git status --porcelain).Count -gt 0) { 'true' } else { 'false' }
docker version
docker compose version
docker compose -f docker-compose.validation.yml build --no-cache --pull validation
docker compose -f docker-compose.validation.yml run --rm --entrypoint python validation -I scripts/doctor.py --profile container
docker compose -f docker-compose.validation.yml run --rm --entrypoint python validation -I scripts/check_ci.py --self-test
docker compose -f docker-compose.validation.yml run --rm validation
```

默认容器命令运行 Phase 07 冻结的 `all`，成功时 17/17 required components、0 failed/skipped 并返回 0。聚焦诊断仍可显式追加 `--suite <公开 suite>`；suite composition 始终来自只读 registry。

## 5. 证据与 profile 边界

独立 doctor 保持 Phase 01 兼容输出 `build/phase-01/current/`。suite dispatcher 从受控 suite→owner Phase 映射中选择当前已实现的最高 Phase，并写入 `build/phase-<NN>/current/`：

- `*.result.json` 是跨机器比较用的规范化结果，路径使用仓库相对值，不包含机器绝对路径。
- `*.machine.json` 是机器 sidecar，保存解释器路径、OS、architecture、工具版本和原始诊断；sidecar 记录对应 result 文件名与 SHA-256。
- suite 同时生成由 result 确定性渲染的 `*.md` 摘要。

典型文件名为 `doctor-host.result.json` / `doctor-host.machine.json`、`suite-environment-host.*` 和 `suite-environment-container.*`。baseline 另生成 `baseline-<profile>.result.json`、`.environment.json` 与 `.md`。每份正式 suite result 记录 `contract_version`、registry SHA-256、runtime lock SHA-256，以及 runner 和实际加载 helper 的源文件 SHA-256。host source state 来自 Git；container source state 来自构建参数、镜像 ENV 与 OCI label。

`--profile host` 要求 Git、Docker client/server/Compose 和 daemon 连通。主机 PowerShell/sh 包装固定传递 `host`。`container` 只由固定镜像入口选择，并同时校验 Linux/amd64 与镜像内置 `DSSC_VALIDATION_CONTAINER_CONTRACT`；CLI、环境变量或镜像合同不一致时入口返回非零。

## 6. 网络与离线边界

以下首次供应链动作需要联网并需要相应授权：

- 从 `python.org` 下载已核验的 CPython 安装器；
- 从 `https://pypi.org/simple` 安装 bootstrap/runtime locks；
- 拉取固定 digest 基础镜像并构建 `dssc-c-validation:v0.4`。

依赖和镜像已安装后，`frozen`、`environment`、registry/schema 校验和语义负控不会主动访问网络。host profile 仍要求本机 Docker daemon 可连接。Compose 运行容器时强制 `network_mode: none`。重新创建 `.venv` 时，缺少本机 wheel cache 会再次需要 PyPI 网络。

## 7. 常见诊断

### 7.1 代理与证书

按组织策略在当前进程设置代理或 CA 文件，避免把凭据写入仓库：

```powershell
$env:HTTPS_PROXY = 'http://proxy.example:8080'
$env:REQUESTS_CA_BUNDLE = 'C:\path\to\organization-ca.pem'
$env:SSL_CERT_FILE = $env:REQUESTS_CA_BUNDLE
.\scripts\bootstrap.ps1
```

Linux 使用同名环境变量。bootstrap 固定 pip `--isolated` 并把 `PIP_CONFIG_FILE` 设为系统空设备，因此不读取用户、全局或 venv pip 配置，CA 使用上面的 Requests/OpenSSL 变量。TLS/证书错误先核对系统时间、组织 CA 链、代理对 `pypi.org` / `files.pythonhosted.org` 的放行规则。Docker pull/build 使用 Docker Desktop 或 daemon 自身的代理与 CA 配置；宿主 shell 变量不一定传入 daemon。

### 7.2 PowerShell 执行策略

本机策略阻止 `.ps1` 时使用一次性的进程 scope，不改机器或用户持久策略：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Suite environment
```

### 7.3 Docker daemon 与平台

```powershell
docker context show
docker version
docker info
docker compose version
docker buildx inspect
```

确保 Docker Desktop/Engine 已启动、当前 context 指向可连接的 Linux engine，并允许 `linux/amd64`。`docker version` 需要同时显示 Client 与 Server。Phase 08 Compose 配置审查应只看到 `./build/ci/docker:/workspace/build` 这一 evidence bind，且不得出现宿主源码、`.git`、`.venv`、`/var/run/docker.sock`、其他 daemon/control socket 或 `npipe:////./pipe/docker_engine`。

## 8. `.venv` 安全重建

重建只作用于当前仓库根目录的字面路径 `.venv/`。先确认仓库 marker、目标父目录、目录类型和 reparse-point/symlink 状态；发现链接时停止并人工核对目标。

```powershell
$RepoRoot = (Resolve-Path -LiteralPath .).Path
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'requirements.lock'))) {
  throw 'Run this command from the repository root'
}
$Target = Join-Path $RepoRoot '.venv'
$Item = Get-Item -LiteralPath $Target -Force
if (-not $Item.PSIsContainer -or ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
  throw 'Expected a real .venv directory; inspect the target manually'
}
if ($Item.Parent.FullName -ne $RepoRoot -or $Item.Name -ne '.venv') {
  throw 'Refusing to remove a target outside the repository .venv boundary'
}
$Links = @(Get-ChildItem -LiteralPath $Target -Force -Recurse |
  Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
if ($Links.Count -ne 0) {
  throw 'Internal reparse points require individual manual inspection before rebuild'
}
Remove-Item -LiteralPath $Target -Recurse -Force
.\scripts\bootstrap.ps1
```

Linux 对应边界检查：

```bash
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel)"
target="${repo_root}/.venv"
[[ "$(dirname "${target}")" == "${repo_root}" && "$(basename "${target}")" == ".venv" ]]
[[ -d "${target}" && ! -L "${target}" ]]
[[ -z "$(find "${target}" -type l -print -quit)" ]]
rm -rf -- "${target}"
./scripts/bootstrap.sh
```

上述检查发现内部链接时停止递归删除，先逐项核对链接及其目标。通过检查后，删除 `.venv/` 不影响 lock、冻结输入、模型、archive、prompts 或用户的其他文件。Phase 01 doctor/environment 结论引用 `build/phase-01/current/`；Phase 02 baseline 结论引用 `build/phase-02/current/`；suite envelope 随最高 `IMPLEMENTED` owner Phase 输出。

## 9. Phase 08 跨平台、CI 与 clean-room 合同

### 9.1 冻结核心与单命令入口

七个公开 suite 均为 `IMPLEMENTED`。registry `contract_version=1.6.0`，`C_Semantic_Treehouse/manifests/validation-suites.json` SHA-256 为 `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`；`all` 精确展开 17 个 required components。Phase 08 的 wrapper、Docker 与 CI 只消费该文件。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

```bash
./scripts/reproduce.sh
```

两者均不接收 suite 参数，依次调用既有 lock bootstrap 和平台 wrapper 的固定 `all`。Windows 本机持久 ExecutionPolicy 保持不变；上面的进程级 bypass 只允许已审核仓库脚本在当前子进程运行。

### 9.2 CI 与证据输出

`.github/workflows/validate.yml` 的三个 required job 为 `ubuntu-native`、`windows-powershell` 和 `docker-clean-room`。workflow 静态合同由 `scripts/check_ci.py` 解析 YAML 并 fail closed；`--self-test` 在临时目录执行危险 trigger、权限、credential、浮动 action/runner、弱化 job 与 artifact 的 negative controls。Phase 08 只形成了本地静态证据；后续已确认候选完成候选绑定的实际 GitHub Actions 三 job。每个发生 tracked 内容变化的新候选均须独立重验，最新动态 run 绑定见 [`docs/v0.4/publication-record.md`](v0.4/publication-record.md)。

`scripts/clean_room.py` 将 tracked 与必要 untracked release-candidate 文件导出到经过边界核验的 `build/clean-room/` 子目录，排除 `.venv`、`build`、cache、secret、本机配置和 Treehouse upstream，并记录源清单、排除清单、SHA-256 与隔离输出。它产生的是 release-candidate rehearsal；上一已确认候选完成了真实 remote clean clone，每个 tracked 候选变化后都必须重新执行。

WSL2 host 轨在独立 ext4 seed 中实际运行 `reproduce.sh`、frozen、host doctor、CI normal/self-test 和 wrapper `all`，并在私有 mount namespace 中另做 cold clean-room。该轨使用 WSL host 预存 Docker daemon endpoint；未创建 socket bind mount，也未运行 Semantic Treehouse workload。

### 9.3 可选证据历史边界（2026-08-11 受控尝试）

- Semantic Treehouse：本条冻结 2026-08-11 的受控尝试，当时可选轨总体为 `DEFERRED`，实际尝试状态为 `BLOCKED_AFTER_CONTROLLED_RETRY`，deployment 为 `NOT DEPLOYED`。固定 `v4.3.0` / commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf` 的 bounded sparse checkout/materialization 已完成；静态 checker self-test 与 materialization 核验通过。canonical raw upstream preflight 保持 `BLOCKED`（33 `BLOCK`、46 `REVIEW`、`execution_authorized=false`），用户随后批准已呈现风险、部署前修复和更窄的 production runtime attempt。
- Treehouse `PrepareOnly`：边界核验通过，目标闭包为 `sth` + `sth-db2`，应用模式为 `prod`，UI 仅绑定 `127.0.0.1:18014`，数据库无宿主端口，内部网络、项目级 volume、无 bind/extra-host/privileged/capability/device；operation counters 证明无 pull/build/up/container/volume/migration/smoke。
- Treehouse build/deployment：镜像构建已尝试；最终 controlled retry 下载 digest-pinned FrankenPHP layer 时发生 short read/unexpected EOF（2,407,954 / 20,064,658 bytes）。清理后项目 container/network/volume/target image 均为 0。deployment 为 `NOT DEPLOYED`，workload/container、migration、UI、API、import、export、publication 均为 `NOT RUN`。传输稳定后重新尝试需要新的人工批准。
- Mermaid renderer/视觉 QA：`DEFERRED`。Phase 07 的证据仍只证明 structure lint；未宣称 parser、render 或视觉 PASS。
- 外部 ITB/SEMIC：`DEFERRED`。没有数据外传授权，上传文件数与字节数均为 0。

决定、raw preflight、runtime boundary、build failure 与恢复条件分别记录在 `build/evidence/{treehouse,mermaid,itb-semic}/`。这些可选轨不进入 required CI job，也不改变核心 `all`。

### 9.4 Semantic Treehouse recovery addendum（2026-08-12）

用户批准恢复后，固定 checkout、`PrepareOnly`、镜像构建与检查、workload、数据库迁移、root/API loopback availability smoke 均已完成。9.3 节保留较早受控失败及清理结果的历史记录。

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`。

`SHACL validator manifest digest=sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`; `SHACL validator security boundary=non-root/internal-only/zero-host-port/read-only-rootfs/drop-all/no-new-privileges/resource-bounded`; `SHACL validation controls=positive-pass/negative-fail/idempotent-recheck-pass/EasyRDF-4-pattern-local-review-patch`; `PAUSED persistence=containers-networks-app-db-volumes-preserved`。

当前 `sth`、`shacl-validator` 与 `sth-db2` 均已停止并保留为 exited containers。运行时唯一宿主应用入口为 `http://127.0.0.1:18014/`，数据库和 validator 宿主端口数为 0。prod admin-only local-review 登录、cookie 非持久化与 `/app/var/user_data` 存储边界记录在 `build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json`。

canonical six-asset v0.4 API import 记录在 `build/evidence/treehouse/v0.4-import-2026-08-12.json`；重启后的 inventory、关系与 ontology TTL RDF-isomorphic export round-trip 记录在 `build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json`。真实浏览器登录及导入后 inventory/model view 记录在 `build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json`。

SHACL validator 以 upstream manifest digest `sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b` 为固定输入；派生 non-root image 使用 UID/GID `65532:65532`、internal network、零宿主端口与 bind mounts、read-only rootfs、`cap_drop=ALL`、no-new-privileges 及 CPU/memory/PID 限制。canonical 正控报告 `schema_valid=true`，内存删除 `datasetId` 的负控报告 `schema_valid=false` 和一个 violation。首次执行与 binding reused 幂等复验见 `build/evidence/treehouse/shacl-validator-execution-2026-08-12.json`、`build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json`。

EasyRDF 的 Turtle→RDF/XML 转换改变四个 `sh:pattern` literal lexical forms；受限 local-review 派生 app 补丁仅在 generated schema disabled 时转发 raw canonical Turtle，canonical SHACL bytes 不变。验证后依次停止 application、validator、database，全部 containers/networks 以及 app/DB named volumes 均保留，见 `build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json`。publication 未执行。
