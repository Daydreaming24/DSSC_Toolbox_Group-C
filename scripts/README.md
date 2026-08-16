# 仓库环境与验证入口

Phase 01 固定 CPython 3.12.10，并让 Windows、Linux、Make 和 Docker 进入同一个 Python 编排核心。入口从自身位置解析仓库根，支持包含空格和非 ASCII 的路径；普通使用无需 activation，也不调用全局 `pip`。

## Bootstrap

Windows PowerShell 5.1+：

```powershell
.\scripts\bootstrap.ps1
# 显式选择已核验的解释器：
.\scripts\bootstrap.ps1 -PythonPath 'C:\path\to\python.exe'
```

Linux：

```bash
./scripts/bootstrap.sh
PYTHON_PATH=/absolute/path/to/python3.12 ./scripts/bootstrap.sh
```

两份 bootstrap 都要求准确 CPython 3.12.10 和 `ensurepip` 25.0.1，创建或复用仓库 `.venv`，从 `requirements-bootstrap.lock` 固定 pip 25.0.1、pip-tools 7.4.1、setuptools 75.8.2 与 wheel 0.45.1，再以 `--require-hashes` 安装根 `requirements.lock`。首次成功会写入绑定 base interpreter、bootstrap/contract、两份 lock 和 venv 全树 fingerprint 的 trust marker；复用时先由 base Python `-I -S` 静态验证 marker 与全树，再启动 venv Python。未知残留、`.pth` 漂移及非允许 symlink/junction 均失败关闭。pip 命令同时使用 `--isolated` 和系统空配置文件，阻断 `target/prefix/root/user` 重定向。最后执行 `pip check` 和 `doctor --profile host`。重复运行消费相同 lock；Windows `-SkipDoctor` 和 Linux `SKIP_DOCTOR=1` 只用于受控诊断。

## Doctor

doctor 需要明确 profile：

```powershell
.\.venv\Scripts\python.exe -I scripts\doctor.py --profile host
.\.venv\Scripts\python.exe -I scripts\doctor.py --profile host --json
```

```bash
./.venv/bin/python -I scripts/doctor.py --profile host
```

`host` profile 将仓库 `.venv`、Git、Docker client/server/Compose 和 daemon 连通性作为门槛。固定镜像使用 `container` profile，仅门控镜像内 Python、lock、依赖、仓库输入和 evidence 写入；Git/Docker capability 记录为 `not_required`。profile 不从“Docker CLI 缺失”等现象推断。

每次运行产生 `build/phase-01/current/doctor-<profile>.result.json` 与 `.machine.json`。result 是不含机器绝对路径的规范化结果；machine sidecar 保存机器事实，并记录对应 result 的 SHA-256。

## Validate

Windows 与 Linux 薄包装只选择仓库 `.venv` 解释器并透传参数：

```powershell
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
```

```bash
./scripts/validate.sh --suite frozen
./scripts/validate.sh --suite environment
```

Make 入口同样只转发：

```text
make bootstrap
make doctor
make validate-frozen
make validate-environment
make validate SUITE=frozen
```

七个公开 suite 的当前合同如下：

| Suite | 状态 | 退出合同 |
|---|---|---|
| `frozen` | IMPLEMENTED | 完整核验 frozen manifest；成功为 0，0 条记录会失败 |
| `environment` | IMPLEMENTED | 运行 doctor 环境门槛；成功为 0 |
| `baseline` | IMPLEMENTED | 依赖 environment，严格执行 manifest 绑定的 33 个 case；成功为 0 |
| `traceability` | IMPLEMENTED | 运行需求追踪、决策与 manifest 绑定检查；成功为 0 |
| `v0.4-model` | IMPLEMENTED | 运行 v0.4 派生模型、release manifest 与契约检查；成功为 0 |
| `v0.4` | IMPLEMENTED | 运行 v0.4 四状态 fixtures 与 report assertions；成功为 0 |
| `all` | IMPLEMENTED | 按冻结 registry 展开全部 required components；成功为 0 |

`scripts/validate.py` 先以固定 schema 和跨记录语义规则校验 `C_Semantic_Treehouse/manifests/validation-suites.json`，再按 registry 依赖确定性展开 component。dispatcher 只接受 `scripts/dssc_validation/entrypoint_catalog.py` 中受控的逻辑 entrypoint ID。重复 ID/component/entrypoint、悬空引用、依赖环、0 component、unknown entrypoint、suite/entrypoint 错配和 shell-command payload 均失败关闭。

Host suite 证据写为 `build/phase-<NN>/current/suite-<suite>-host.result.json`、`.machine.json` 和由 result 确定性生成的 `.md`；`<NN>` 是 registry 中已实现 suite 的最高受控 owner Phase。Compose 将 container 对应文件写入同 Phase 的专用 `current/docker/`。result 记录 evidence phase、registry `contract_version`/SHA-256、runtime lock SHA-256、runner 与实际加载 helper 的 SHA-256。

Compose 仅挂载 Phase 01–09 九个预声明的 `current/docker` evidence 目录；active Phase 由 registry 中最高 `IMPLEMENTED` owner Phase 自动选择。源码、`.git`、`.venv` 与 Docker socket 均不挂载。container baseline 从镜像构建参数 `DSSC_SOURCE_COMMIT` / `DSSC_SOURCE_DIRTY` 读取 source state，缺失、`unknown` 或格式错误时失败关闭；源码改变后必须重建镜像。

## Phase 08 复现、CI 与 clean-room 入口

Phase 08 的现行 Compose 以 `./build/ci/docker:/workspace/build` 单一 evidence bind 取代上方 Phase 01 的九目录布局；镜像默认命令运行 `all`。源码、`.git`、`.venv`、secret 与任何 daemon/control socket 均不挂载。

单命令入口只编排既有 bootstrap 与统一 validator，并固定运行 registry 的 `all`：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

```bash
./scripts/reproduce.sh
```

两者均拒绝参数。Windows 包装使用 Windows PowerShell 5.1 子进程隔离既有 bootstrap 的显式退出；Linux 包装以 `exec` 传播最终 validator 退出码。它们不包含 suite composition 或 checker 规则。

CI workflow 的静态检查与隔离负控：

```powershell
.\.venv\Scripts\python.exe -I scripts\check_ci.py
.\.venv\Scripts\python.exe -I scripts\check_ci.py --self-test
```

默认机器结果位于 `build/ci/`。通用 permissions/action pin/checkout/runner/timeout/shell/artifact predicates 与 `.github/workflows/validate.yml` 的三-trigger、三-job profile 分开，供 Phase 09 的发布验证只读复用。本地静态 PASS 本身只证明 workflow 合同；最近已确认候选完成了候选绑定的实际 GitHub Actions Ubuntu/Windows/Docker 三个必需 job。最新 run URL 与结论见 [`publication-record.md`](../docs/v0.4/publication-record.md)。

Release-candidate clean-room 支持只清单、导出与实际 rehearsal：

```powershell
.\.venv\Scripts\python.exe -I scripts\clean_room.py --mode manifest-only
.\.venv\Scripts\python.exe -I scripts\clean_room.py --mode export
.\.venv\Scripts\python.exe -I scripts\clean_room.py --mode rehearsal --profile host
```

输出严格位于 `build/clean-room/` 的新 run 目录，记录 source/exclusion/export/command/output hashes；`.venv`、既有 `build`、cache、secret、本机配置和 external upstream 不进入导出。rehearsal 是未提交 release candidate 的本地隔离复演，与发布后的 remote clean clone 证据分开。最近已确认候选已从 canonical GitHub URL 完成真实 remote clean clone、一键复现和三个最终 QA checker；最新绑定见 [`publication-record.md`](../docs/v0.4/publication-record.md)。

Semantic Treehouse 静态预检入口：

```powershell
.\.venv\Scripts\python.exe -I scripts\check_treehouse_compose.py --self-test
```

实际 preflight 必须提供 upstream root、compose path、40 位固定 commit 与唯一 Compose project name。checker 只读分析 digest、build boundary、权限、挂载、socket、网络、端口、`.env`/secret/config、container/project name 和 cleanup 风险，不执行 clone、pull、build 或 `up`。Phase 08 已对固定 commit 的实际 upstream compose 执行该 checker；canonical raw 结果为 `BLOCKED`（33 `BLOCK`、46 `REVIEW`、`execution_authorized=false`）。

本段冻结 2026-08-11 的受控尝试。用户在阅读风险后批准部署前修复与更窄 runtime attempt。bounded checkout/materialization 和 `treehouse_up.ps1 -HttpPort 18014 -PrepareOnly` 已完成；PrepareOnly 的 pull/build/up/container/volume/migration/smoke counters 均为 0。实际 image build 最终因 digest-pinned Docker Hub FrankenPHP layer short read/unexpected EOF 停止，清理后零项目资源。deployment 为 `NOT DEPLOYED`；workload/container、migration、UI、API、import/export/publication 均为 `NOT RUN`。此 optional track 不进入核心 `all`。

## Phase 09 最终 QA checkers

Phase 09 新增三个标准库/锁内依赖的具名 checker，由仓库 `.venv` 以 `-I` 运行；**不**并入 `reproduce.ps1` / `reproduce.sh`。一键复现成功后再分开执行。任一项 `ok=false`、非零退出、0 扫描目标或 scanner 异常均失败关闭。

| Checker | 输入 | 输出 / fail-closed 语义 |
|---|---|---|
| `scripts/check_deliverables.py` | `C_Semantic_Treehouse/manifests/deliverables.json` + schema；`git ls-files` | schema + 跨记录语义；required path/hash；coverage anchors；tracked 双向覆盖（`deliverables.json` 自身例外）；缺 license decision / `NOASSERTION` 无 decision / publish:false 仍 tracked → 非零 |
| `scripts/check_publication_safety.py` | tracked 文本、ZIP 合同、privacy allowlist、Git 作者/message、`.gitattributes`、workflow permissions | 拒绝 secret/私钥/`.env` 风格、ZIP 外个人绝对路径、未 allowlist 的 ZIP 内历史路径；0 扫描目标失败 |
| `scripts/check_evidence_freshness.py` | 四个上游 manifests、validation-suites contract/hash、deliverables 绑定、lock、core sources、evidence-index 中 result 输入 | 拒绝 stale input/report hash、错误 validation-suites hash、过期/旧 manifest evidence |

Windows：

```powershell
.\.venv\Scripts\python.exe -I scripts\check_deliverables.py
.\.venv\Scripts\python.exe -I scripts\check_publication_safety.py
.\.venv\Scripts\python.exe -I scripts\check_evidence_freshness.py
```

Linux：

```bash
./.venv/bin/python -I scripts/check_deliverables.py
./.venv/bin/python -I scripts/check_publication_safety.py
./.venv/bin/python -I scripts/check_evidence_freshness.py
```

机器结果默认打印 JSON 到 stdout；Phase 09 运行时可将副本保存在 ignored `build/phase-09/**` 或 `build/final-qa/**`。这些 runtime 结果 **不得** 写回 tracked `core-results.json`。

相关只读文档：[`docs/v0.4/release-readiness.md`](../docs/v0.4/release-readiness.md)、[`docs/v0.4/human-decisions.md`](../docs/v0.4/human-decisions.md)、[`docs/v0.4/publication-record.md`](../docs/v0.4/publication-record.md)。

v0.4 已公开托管；已确认候选的 Windows/Linux local clean clone、普通 push、三-job CI 与远程 clean clone 均有 `PASS` 记录。维护者（GitHub 身份 `Daydreaming24`）已明确接受 P00-R14 的最终人工治理责任，该风险终态为 `ACCEPTED_LIMITATION`，当前无 `OPEN_BLOCKING` 风险。每个发生 tracked 内容变化的新候选均须独立完成 Phase 09 §6.9–§6.11；有效状态以 [`STATUS.md`](../docs/v0.4/STATUS.md) 最新追加记录为准。公开托管且无通用 license grant 为已接受限制；tag、GitHub Release、branch protection 和 default-branch 更改均为 `NOT_REQUESTED`。Semantic Treehouse publication、Mermaid render 与外部 ITB/SEMIC 保持既有 `NOT RUN` / `DEFERRED` 状态。

## 冻结校验器边界

`verify_frozen_files.py` 只依赖 Python 标准库，用于检查迁移后的冻结输入和历史归档。它是受保护入口，Phase 01 的 `frozen` checker 复用其加载和 SHA-256 逻辑，未修改该文件。package-level 旧验证脚本仍保留历史边界，后续 Phase 通过新增受控 checker 接入统一 registry。

## Semantic Treehouse recovery addendum（2026-08-12）

获批准的断点恢复已完成；前文的 registry short-read/EOF 仍是较早尝试的历史证据。

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`。

`SHACL validator manifest digest=sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`; `SHACL validator security boundary=non-root/internal-only/zero-host-port/read-only-rootfs/drop-all/no-new-privileges/resource-bounded`; `SHACL validation controls=positive-pass/negative-fail/idempotent-recheck-pass/EasyRDF-4-pattern-local-review-patch`; `PAUSED persistence=containers-networks-app-db-volumes-preserved`。

`sth`、`shacl-validator` 与 `sth-db2` 当前均为保留的 exited containers。运行态应用边界为 `http://127.0.0.1:18014/`，数据库和 validator 无宿主端口。prod admin-only local-review 登录及 `/app/var/user_data` 持久化证据位于 `build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json`。

canonical six-asset v0.4 API import 记录在 `build/evidence/treehouse/v0.4-import-2026-08-12.json`；重启后 inventory、关系及 ontology TTL RDF-isomorphic export round-trip 记录在 `build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json`。真实浏览器登录、导入后 inventory 与 model view 记录在 `build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json`。

validator 固定至 upstream manifest digest `sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`；派生 non-root 运行时使用 internal-only network、零宿主端口/绑定挂载、只读 rootfs、drop-all capabilities、no-new-privileges 与资源上限。canonical 正控通过，内存删除 `datasetId` 的负控产生一个 violation；`build/evidence/treehouse/shacl-validator-execution-2026-08-12.json` 和 `build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json` 分别记录首次执行与 binding reused 的幂等复验。

EasyRDF 转换对四个 `sh:pattern` literal 造成 lexical-form drift；受限 local-review 派生 app 补丁只在 generated schema disabled 时直接传递 raw canonical Turtle，源 SHACL 未变。验证后按 application、validator、database 顺序停止，containers/networks 和 app/DB named volumes 保留，证据为 `build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json`。publication 仍为 `NOT RUN`；该可选轨仍不进入核心 `all`。
