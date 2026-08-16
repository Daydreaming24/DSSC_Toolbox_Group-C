# v0.4 可复现环境合同

> 建立阶段：Phase 01；Phase 02–07 扩展统一 suite；Phase 08 固化跨平台、CI 与 clean-room
> 状态：七个公开 suite 与 `all` 已冻结；Phase 08 本地静态/平台证据在 `build/phase-08/`、`build/ci/` 与 `build/clean-room/`。上一已确认候选已完成实际 GitHub run 与 canonical URL remote clone；每个新候选仍须重跑并在 `publication-record.md` 记录动态绑定。当前有效状态以 `STATUS.md` 最新追加记录为准。

## 1. 固定解释器

| 项 | 值 |
|---|---|
| 实现 | CPython |
| 准确版本 | **3.12.10** |
| 版本文件 | `.python-version` |
| Windows 安装器 | `https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe` |
| 安装器 SHA-256 | `67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb` |
| Windows 签名 / scope | Authenticode `Valid`，Python Software Foundation；当前用户安装 |
| 选择依据 | 3.12 系列最后一个提供官方 Windows 二进制安装器的完整维护版；3.12.11+ 为仅源码安全修复，不适合作为 Windows 主机门槛。Linux 容器使用同版本官方 `python:3.12.10-slim-bookworm` 镜像。六项直接依赖在 Windows 与 Linux hash lock 安装中通过。 |

**禁止**使用全局 Python 3.13 创建正式 `.venv`。

## 2. 固定 pip 工具链

| 项 | 值 |
|---|---|
| CPython `ensurepip` | **25.0.1**（标准库 bundle） |
| pip | **25.0.1** |
| pip-tools | **7.4.1** |
| setuptools | 75.8.2 |
| wheel | 0.45.1 |
| 安装方式 | 仅 `<venv-or-container-python> -I -m pip --isolated`；`PIP_CONFIG_FILE` 固定为系统空设备 |
| Bootstrap lock | `requirements-bootstrap.lock`，SHA-256 `8b94bcc369c574d801a5d0923df54b103efc4dfd1bdadb508846a3cd42a81bff` |
| 禁止 | 调用全局 `pip` / `pip.exe` |

初始引导使用选定 CPython 的 `ensurepip`。新建环境首次成功后写入 trust marker，绑定 base interpreter、bootstrap/contract、两份 lock 与 venv 全树 fingerprint；复用时先由 base Python `-I -S` 验证 marker 和全树，再启动 venv Python。pip 还以 `--isolated` 加系统空配置文件阻断配置及 `target/prefix/root/user` 重定向，随后通过含 hash 的 bootstrap lock 规范化工具链。`requirements.lock.json` 记录 pip-tools 生成命令、`https://pypi.org/simple` 索引、输入/输出 hash，并声明已完成 self-hosted regeneration。

## 3. 唯一依赖权威源

| 文件 | 角色 |
|---|---|
| `requirements.in` | 直接依赖及兼容范围（唯一输入） |
| `requirements.lock` | 全部直接+传递依赖的准确版本与 `--hash=sha256:...`；SHA-256 `d92c7ae708283c04a916da2a9c810a19fbcc65b1fcb154792099e5a3924baeb2` |
| `C_Semantic_Treehouse/requirements.txt` | 仅作兼容转发；权威内容来自根 input/lock |

普通 bootstrap **只消费**已提交 lock（`--require-hashes`），不在 bootstrap 中重新求解依赖。

直接依赖集合为 `rdflib`、`pyshacl`、`PyLD`、`jsonschema`、`PyYAML` 和 `openapi-spec-validator`。doctor 对 runtime/bootstrap 两份 lock 做 exact-pin/hash/来源检查，并要求已安装发行版集合与两份 lock 的并集准确一致。

## 4. OS / architecture support matrix

只登记实际报告或实际运行的组合。

| 平台 | Architecture | 状态 | 证据要求 |
|---|---|---|---|
| Windows host | AMD64 (x86_64) | **SUPPORTED_AND_TESTED**（Phase 01 必需） | bootstrap + doctor host + frozen/environment suites |
| Linux container（固定 digest） | linux/amd64 | **SUPPORTED_AND_TESTED**（Phase 01 必需发布轨） | Docker build/run environment suite，`profile=container` |
| WSL2 Linux host | x86_64 | **SUPPORTED_AND_TESTED**（Phase 08，WSL2 scope） | Ubuntu 24.04.4 LTS；cold bootstrap + doctor host + CI self-test + wrapper all + clean-room |
| Linux host（独立 / bare-metal） | UNKNOWN | **UNTESTED / DOCKER_FALLBACK** | 当前无独立 Linux host 实测；使用已实测 WSL2 或固定容器轨 |
| macOS host（原生） | UNKNOWN | **UNTESTED / DOCKER_FALLBACK** | 未原生测试；使用同一固定 Docker 轨 |
| 其他 | UNKNOWN | **UNTESTED** | 不得声称原生支持 |

新增原生支持必须在对应机器上产生 bootstrap、doctor 与 environment suite 实际证据后，再改本表。

## 5. 团队 OS/architecture inventory

| 角色/机器 | OS | Arch | 用途 | 备注 |
|---|---|---|---|---|
| Phase 01 执行主机 | Windows 10/11 (NT 10.0.26200) | AMD64 | 原生开发与验证 | 当前会话实测 |
| Phase 08 WSL2 host | Ubuntu 24.04.4 LTS / WSL2 kernel 6.6.87.2 | x86_64 | Linux host bootstrap、doctor、CI、all、clean-room | CPython 3.12.10；Git 2.43.0；Docker 29.3.0/29.4.1；Compose 5.1.3 |
| Docker Desktop Linux engine | Linux | amd64 | 发布 clean-room | 与 Windows host 同机；固定镜像实测 |
| 其他团队成员设备 | UNKNOWN | UNKNOWN | — | 由维护者收集；未收集前不得虚构 |

## 6. Docker 发布环境

| 项 | 值 |
|---|---|
| Dockerfile | `Dockerfile.validation` |
| Compose | `docker-compose.validation.yml` |
| 基础镜像完整标签 | `python:3.12.10-slim-bookworm` |
| 不可变 digest（index） | `sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` |
| linux/amd64 manifest | `sha256:97983fa8cc88343512862c62307159a82261c3528dc025f79e5a3f7af43e50b4` |
| 镜像标签 | `dssc-c-validation:v0.4` |
| 运行用户 | 固定 uid/gid `10001:10001`（非 root）；宿主变量不能覆盖，原生 Linux evidence 目录须授予该 uid/gid 写权限 |
| Profile | `container`（`DSSC_VALIDATION_PROFILE=container`） |
| 根文件系统 / 网络 | 只读；`network_mode: none` |
| 唯一宿主挂载 | `./build/ci/docker:/workspace/build`，仅作为 Phase 08/CI 生成证据 sink |
| Docker socket / engine pipe | **禁止**挂载 |

镜像先复制两份 lock 并以 `--require-hashes` 安装，执行 `pip check`，再复制 `.dockerignore` 过滤后的仓库输入。镜像内预建 Phase 01–09 evidence current 目录；Compose 把隔离的宿主 `build/ci/docker` 映射到容器 `/workspace/build`，registry 继续决定其下实际 phase 路径。运行时使用镜像内源码，宿主 `.venv`、源码树、`.git`、secret 和 Docker daemon 均不进入容器。默认命令直接运行统一 dispatcher 的 `--suite all`。

## 7. 统一验证入口

| Suite | 当前状态 | 依赖 / 行为 |
|---|---|---|
| `frozen` | IMPLEMENTED | 受控 `check_frozen_files`；成功返回 0 |
| `environment` | IMPLEMENTED | 受控 `check_environment`；成功返回 0 |
| `baseline` | IMPLEMENTED | 依赖 `environment`；严格执行 manifest 绑定的 33 个 case |
| `traceability` | IMPLEMENTED | D 组契约、requirements、ADR、coverage 与 schema/hash 绑定 |
| `v0.4-model` | IMPLEMENTED | release manifest、模型、RDF/JSON-LD/SHACL/JSON Schema/OpenAPI |
| `v0.4` | IMPLEMENTED | 66 个四状态 cases 与 report graph oracle |
| `all` | IMPLEMENTED | 六个 constituent suites 加 composition、SPARQL、quality、governance、documentation，共 17 个 required components |

Registry：`C_Semantic_Treehouse/manifests/validation-suites.json`

Schema：`C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`
顶层合同版本字段：**仅** `contract_version`（当前 `1.6.0`）。当前 registry SHA-256 为 `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836`。

Dispatcher：`scripts/validate.py` — 只解析受控逻辑 entrypoint ID。schema 与跨记录语义校验先检查固定 suite 集合、状态、依赖、component、entrypoint allowlist、重复、悬空引用、依赖环和确定性展开。Phase 08–09 只读消费 1.6.0；任何 suite 状态、依赖或组成变化均返回 Phase 07 处理。

## 8. Profile 与证据合同

`host` profile 要求仓库 `.venv`、Git、Docker client/server/Compose 和 daemon 连通，主机 PowerShell/sh 包装固定选择它。`container` profile 要求镜像内 Python、lock、依赖、仓库输入和 evidence 写入能力；Git 与 Docker 相关 capability 在结果中固定为 `not_required`。固定镜像同时提供 `DSSC_VALIDATION_PROFILE=container` 和内置容器合同标记，并校验 Linux/amd64；CLI、环境变量或镜像合同不一致时返回非零。

独立 doctor 保持 `build/phase-01/current/` 兼容输出。suite dispatcher 使用固定 suite→owner Phase 映射和 registry 实现状态选择最高 active Phase，将证据写入 `build/phase-<NN>/current/`，并拆分为：

- `*.result.json`：可跨机器比较的规范化结果，不含绝对路径；
- `*.machine.json`：机器 inventory sidecar，包含 OS、architecture、解释器/工具路径和原始输出，并绑定 result 文件名与 SHA-256；
- `*.md`：suite result 的确定性摘要。

正式 suite result 记录 registry `contract_version`/SHA-256、runtime lock SHA-256，以及 `scripts/validate.py`、`scripts/doctor.py` 和所有实际加载 helper 的源文件 SHA-256。Phase 01 doctor/environment 结论引用 `build/phase-01/current/`；Phase 02 baseline 结论引用 `build/phase-02/current/`；suite envelope 随最高 `IMPLEMENTED` owner Phase 输出。

## 9. 网络与离线边界

**需要联网（首次）：**

- 下载官方 CPython 3.12.10 Windows 安装器（python.org）
- 从 PyPI 安装 bootstrap lock 与 runtime lock 中的包
- 拉取固定 digest 的 Docker 基础镜像并构建 validation 镜像

**核心验证可离线（在依赖与镜像已缓存后）：**

- 七个公开 suites（包括 `all`）以及 registry/schema 语义校验
- 冻结文件 SHA-256 校验
- doctor（host profile 仍需本机 Docker daemon 可达）

Compose 容器运行期为 `network_mode: none`。重建 `.venv` 时若本机 wheel cache 不完整，仍需访问 PyPI。

**不在核心验证路径：** Semantic Treehouse、Mermaid、ITB/SEMIC、GPU、数据库、在线 validator。

## 10. 常用命令

### Windows（PowerShell 5.1+）

```powershell
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe -I scripts\doctor.py --profile host
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite all
.\scripts\reproduce.ps1
```

### Linux

```bash
./scripts/bootstrap.sh
./.venv/bin/python -I scripts/doctor.py --profile host
./scripts/validate.sh --suite frozen
./scripts/validate.sh --suite environment
./scripts/validate.sh --suite baseline
./scripts/validate.sh --suite all
./scripts/reproduce.sh
```

### Docker

```powershell
$env:DSSC_SOURCE_COMMIT = (git rev-parse HEAD).Trim().ToLowerInvariant()
$env:DSSC_SOURCE_DIRTY = if (@(git status --porcelain).Count -gt 0) { 'true' } else { 'false' }
docker compose -f docker-compose.validation.yml build --no-cache --pull validation
docker compose -f docker-compose.validation.yml run --rm --entrypoint python validation -I scripts/doctor.py --profile container
docker compose -f docker-compose.validation.yml run --rm --entrypoint python validation -I scripts/check_ci.py --self-test
docker compose -f docker-compose.validation.yml run --rm validation
```

默认容器命令与显式 `--suite all` 均预期返回 0。构建参数会固化为镜像 ENV/OCI label，container provenance 对缺失、`unknown` 或格式错误的 source commit/dirty 失败关闭；源码改变后必须重建。WSL2 Linux host 已实际通过 host profile；独立 / bare-metal Linux 与 macOS 当前使用 Docker fallback。Linux 命令及代理、证书、执行策略和 daemon 诊断见 `docs/environment.md`。

## 11. `.venv` 安全重建边界

仅删除仓库根目录 `.venv/`，然后重新运行 bootstrap。不得删除：

- `requirements.lock` / `requirements-bootstrap.lock`
- 冻结输入、`archive/`、`prompts/`
- `C_Semantic_Treehouse/model/**`
- 任何不在 allowlist 的用户修改

执行删除前确认目标是当前仓库根目录下名为 `.venv` 的真实目录，父目录准确等于仓库根，且目标及其后代不存在 reparse point/symlink。随后使用 `Remove-Item -LiteralPath $Target -Recurse -Force` 或 Linux `rm -rf -- "${target}"` 删除这个精确目标并重新运行 bootstrap。发现内部链接时停止并逐项人工核对。可直接复制的完整边界检查命令见 `docs/environment.md` 第 8 节。

## 12. Phase 08 CI、clean-room 与可选证据

CI workflow 为 `.github/workflows/validate.yml`，只接受显式 `main` 的 `push`/`pull_request` 与无 shell input 的 `workflow_dispatch`。三个 required jobs 分别使用 `ubuntu-24.04`、`windows-2022` 和 `ubuntu-24.04` Docker clean-room；actions 使用完整 commit SHA，权限为 `contents: read`，checkout 不保留凭据，每个 job 30 分钟超时，核心步骤 fail closed，证据上传固定 `if: always()` 与 `if-no-files-found: error`。`scripts/check_ci.py` 的通用 policy API 与 validate workflow profile 分离，并通过临时目录 negative controls。Phase 08 截止时实际 GitHub run 尚未执行；后续已确认候选完成了候选绑定的 Ubuntu/Windows/Docker 三 job 与 remote clean clone。每个发生 tracked 内容变化的新候选均须独立重验，最新动态证据见 [`publication-record.md`](publication-record.md)。

`scripts/clean_room.py` 是本地 release-candidate rehearsal：它只写经过解析核验的 `build/clean-room/` 子树，导出 tracked 与必要 untracked 文件，排除 `.venv`、`build`、cache、secret、本机配置和 external upstream，记录源/排除/输出 hashes，并在隔离副本执行 bootstrap、明确 doctor profile、wrapper `all` 与单命令 reproduce。它不构成 Phase 09 的 remote `git clone` 证据。

WSL2 Linux host 证据固定为 Ubuntu 24.04.4 LTS / x86_64、CPython 3.12.10、Git 2.43.0、Docker client 29.3.0 / server 29.4.1 与 Compose 5.1.3。最终 harness 位于 `build/phase-08/linux-v8-final/harness-result.json`，对应 clean-room evidence 位于 `build/clean-room/路径 with space-linux-v8-final/evidence/`；该 host 轨没有创建 Docker socket bind，也没有执行 Treehouse workload。

历史时点（2026-08-11）的可选轨状态：Semantic Treehouse 总体为 `DEFERRED`，该次实际尝试为 `BLOCKED_AFTER_CONTROLLED_RETRY`，deployment 为 `NOT DEPLOYED`。固定 `v4.3.0` / commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf` 的 bounded checkout/materialization 已完成；canonical raw preflight 保持 33 `BLOCK`、46 `REVIEW`、`execution_authorized=false`，finding-specific human opt-in 已批准；`PrepareOnly` 的 production/loopback/internal-network/project-volume/zero-operation 边界已核验。实际 image build 的 final controlled retry 在 digest-pinned Docker Hub FrankenPHP layer 上发生 short read/unexpected EOF，随后确认零项目 container/network/volume/target image。workload/container、migration、UI、API、import、export、publication 均为 `NOT RUN`。Mermaid 完整 render/视觉 QA `DEFERRED`；外部 ITB/SEMIC `DEFERRED`（无数据外传授权，零上传）。这些轨不进入 `all` 或 required CI jobs。

### 12.1 Semantic Treehouse recovery addendum（2026-08-12）

用户批准从上述受控失败断点恢复；固定 checkout、runtime boundary、镜像、workload、数据库迁移和 loopback availability smoke 已形成成功证据。上述段落继续作为较早尝试的历史记录。

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`。

`SHACL validator manifest digest=sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`; `SHACL validator security boundary=non-root/internal-only/zero-host-port/read-only-rootfs/drop-all/no-new-privileges/resource-bounded`; `SHACL validation controls=positive-pass/negative-fail/idempotent-recheck-pass/EasyRDF-4-pattern-local-review-patch`; `PAUSED persistence=containers-networks-app-db-volumes-preserved`。

当前 `sth`、`shacl-validator` 与 `sth-db2` 在 exact project、Docker context 与 state-marker binding 下均已停止并保留为 exited containers。运行态应用入口固定为 `http://127.0.0.1:18014/`，数据库与 validator 未发布宿主端口。prod admin-only local-review 登录、cookie 非持久化与 `/app/var/user_data` 存储边界记录在 `build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json`。

canonical six-asset v0.4 API import 记录在 `build/evidence/treehouse/v0.4-import-2026-08-12.json`；重启后的 inventory、关系与 ontology TTL RDF-isomorphic export round-trip 记录在 `build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json`。真实浏览器登录及导入后 inventory/model view 记录在 `build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json`。

validator 固定 upstream manifest digest `sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`，派生 non-root 运行时采用 UID/GID `65532:65532`、internal-only network、零 host ports/bind mounts、read-only rootfs、drop-all capabilities、no-new-privileges 与 CPU/memory/PID 限额。canonical 正控通过；内存删除 `datasetId` 的负控失败并返回一个 violation。`build/evidence/treehouse/shacl-validator-execution-2026-08-12.json` 记录首次验证，`build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json` 记录 binding reused 且结果一致的幂等复验。

EasyRDF 转换使四个 `sh:pattern` literal lexical forms 发生变化；受限 local-review 派生 app 补丁仅在 generated schema disabled 时转发 raw canonical Turtle，canonical SHACL bytes 保持不变。完成验证后按 application→validator→database 顺序停止，containers、networks 与 app/DB named volumes 全部保留；`build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json` 固定该 `PAUSED` 状态。publication 仍为 `NOT RUN`；该可选轨不改变 frozen `all` composition 或 required CI jobs。
