# Package 脚本索引

公开验证从仓库根目录的 [`scripts/validate.py`](../../scripts/validate.py) 进入。Windows [`validate.ps1`](../../scripts/validate.ps1)、Linux [`validate.sh`](../../scripts/validate.sh)、Make 和 Docker 都只转发到该 Python dispatcher；suite、依赖和 component 顺序由 [`validation-suites.json`](../manifests/validation-suites.json) 决定。package 目录中的脚本承担受控 helper、历史参考或可选外部 wrapper 角色，不形成第二个权威入口。

## 根受控验证层

| 文件 | 作用 |
|---|---|
| [`verify_frozen_files.py`](../../scripts/verify_frozen_files.py) | `frozen` 的标准库完整性核心 |
| [`doctor.py`](../../scripts/doctor.py) | `environment` 的 host/container profile 入口 |
| [`checks_baseline.py`](../../scripts/dssc_validation/checks_baseline.py) | manifest-bound v0.1–v0.3 baseline adapter |
| [`checks_traceability.py`](../../scripts/dssc_validation/checks_traceability.py) | D requirements/ADR/coverage adapter |
| [`checks_model.py`](../../scripts/dssc_validation/checks_model.py) | v0.4 release/model adapter |
| [`checks_v04.py`](../../scripts/dssc_validation/checks_v04.py) | 66-case 四状态与 report oracle adapter |
| [`checks_phase06.py`](../../scripts/dssc_validation/checks_phase06.py) | SPARQL、quality、governance 的 package helper adapter |
| [`checks_all.py`](../../scripts/dssc_validation/checks_all.py) | 固定 `all` composition 断言 |
| [`check_documentation.py`](../../scripts/check_documentation.py) | Phase 07 文档、链接、manifest 声明、Mermaid 结构与 negative controls |

Phase 07 规定的 checker 诊断使用显式 repo `.venv`：

```powershell
.\.venv\Scripts\python.exe scripts\check_documentation.py --self-test
.\.venv\Scripts\python.exe scripts\check_documentation.py
```

```bash
./.venv/bin/python scripts/check_documentation.py --self-test
./.venv/bin/python scripts/check_documentation.py
```

## 受控的当前 checker/helper

以下 Phase 06 模块由根 [`entrypoint_catalog.py`](../../scripts/dssc_validation/entrypoint_catalog.py) 通过固定 logical entrypoint 调用；registry 不执行任意 shell、module 或 path payload。

| 文件 | 当前职责 |
|---|---|
| [`run_sparql_tests.py`](run_sparql_tests.py) | 加载版本绑定 SPARQL manifest，执行 20 个 required CQ，并生成确定性结果和 self-test |
| [`sparql_manifest.py`](sparql_manifest.py) | 校验 SPARQL manifest/schema、authority 引用、路径与 hash |
| [`sparql_report.py`](sparql_report.py) | 生成规范化 JSON/Markdown 报告 |
| [`quality_metrics.py`](quality_metrics.py) | 从 manifests 与实际 RDF/SHACL 图计算八类质量指标，并校验 SSSOM |
| [`validate_governance.py`](validate_governance.py) | governance/provenance component 的受控入口 |
| [`governance_contract.py`](governance_contract.py) | 五-manifest preflight、governance/provenance 语义、负控和确定性实现 |

正式组合命令仍使用根 wrapper：

```powershell
.\scripts\validate.ps1 -Suite all
```

```bash
./scripts/validate.sh --suite all
```

单独调用 checker 只用于受控诊断或对应 Phase 规定的 self-test；它不会替代 registry 展开的 `all`。

## v0 历史参考脚本

下列文件保留 v0 实现和已知风险，当前 harness 不将它们视为公开 entrypoint：

- `phase1_validate.py`
- `run_all_validations.py`
- `validate_rdf.py`
- `validate_jsonld.py`
- `validate_shacl.py`
- `validate_jsonschema.py`
- `validate_openapi.py`
- `check_required_files.py`
- `check_links_and_paths.py`
- `validation_common.py`

历史风险和当前替代合同记录在 [`baseline-reproduction.md`](../../docs/v0.4/baseline-reproduction.md)。当前 baseline、v0.4 四状态和 documentation checks 分别由根 `scripts/dssc_validation/` 的 manifest-bound checks 与 Phase 07 checker 承担。

## Semantic Treehouse wrappers

[`treehouse_clone_or_update.ps1`](treehouse_clone_or_update.ps1) / [`treehouse_clone_or_update.sh`](treehouse_clone_or_update.sh)、[`treehouse_up.ps1`](treehouse_up.ps1) / [`treehouse_up.sh`](treehouse_up.sh)、[`treehouse_status.ps1`](treehouse_status.ps1) / [`treehouse_status.sh`](treehouse_status.sh) 和 [`treehouse_down.ps1`](treehouse_down.ps1) / [`treehouse_down.sh`](treehouse_down.sh) 来自可选外部证据轨。它们会涉及网络、上游仓库或 Docker 外部状态，须在 Phase 08 明确授权、固定上游版本并按证据门槛执行。

日常登录、模型浏览、安全暂停/恢复和完整收尾的操作步骤见 [`C_semantic_treehouse_user_guide.md`](../C_semantic_treehouse_user_guide.md)。

下述内容冻结 2026-08-11 的受控尝试。Phase 08 已固定 upstream `v4.3.0` / commit `e6d7315a09afdfaadbe3ad1a09cf5305f8d13faf`。clone/materialization wrapper 已核验 detached clean worktree、lock hashes、`core.autocrlf=false` 与敏感/生成目录缺失。根 [`check_treehouse_compose.py`](../../scripts/check_treehouse_compose.py) 的 self-test 已通过，实际 raw preflight 保持 `BLOCKED`（33 `BLOCK`、46 `REVIEW`、`execution_authorized=false`）。用户批准已呈现风险及更窄 runtime attempt 后，PowerShell `PrepareOnly` 通过 production、loopback、internal-network、project-volume 和零 operation counters 边界。

实际 image build 最终在 digest-pinned Docker Hub FrankenPHP layer 下载时 short read/unexpected EOF。清理后项目 container/network/volume/target image 均为 0；deployment 为 `NOT DEPLOYED`，workload/container、migration、UI/API/import/export/publication 为 `NOT RUN`。decision、preflight、runtime boundary 与失败证据位于 `build/evidence/treehouse/`；完整边界见 [`C_semantic_treehouse_usage.md`](../C_semantic_treehouse_usage.md)。这些 wrappers 与结果不进入核心 `all`。

### Recovery addendum（2026-08-12）

用户随后批准从既有断点恢复；固定 checkout、部署前边界、镜像、workload、数据库迁移和两个 loopback availability smoke 已完成。上段内容继续保留为较早受控失败的历史记录。

`checkout=PASS`; `raw preflight=BLOCKED`; `opt-in=APPROVED`; `PrepareOnly=PASS`; `image build=PASS`; `deployment=PASS`; `workload=PASS`; `database migration=PASS`; `current runtime=PAUSED`; `root loopback smoke=PASS`; `API loopback availability smoke=PASS`; `UI workflow=PASS`; `model import=PASS`; `export=PASS`; `publication=NOT RUN`; `SHACL validator execution=PASS`。

`SHACL validator manifest digest=sha256:208dc8b9be042d96164ef85d2f9a904c8a0da8f7df366057d5ba5f43dffc2b0b`; `SHACL validator security boundary=non-root/internal-only/zero-host-port/read-only-rootfs/drop-all/no-new-privileges/resource-bounded`; `SHACL validation controls=positive-pass/negative-fail/idempotent-recheck-pass/EasyRDF-4-pattern-local-review-patch`; `PAUSED persistence=containers-networks-app-db-volumes-preserved`。

当前 `sth`、`shacl-validator` 与 `sth-db2` 均已停止并保留为 exited containers；运行时应用仅监听 `http://127.0.0.1:18014/`，数据库与 validator 不发布宿主端口。prod admin-only local-review 登录和 `/app/var/user_data` 持久化边界见 `build/evidence/treehouse/runtime-auth-storage-recovery-admin-only-2026-08-12.json`。

经认证 loopback API 已导入 canonical six-asset v0.4 set，证据为 `build/evidence/treehouse/v0.4-import-2026-08-12.json`；重启后的 inventory、关系与 ontology TTL RDF-isomorphic round-trip 见 `build/evidence/treehouse/v0.4-import-post-restart-2026-08-12.json`。真实浏览器登录、导入后 inventory 与 model view 见 `build/evidence/treehouse/browser-ui-import-verification-2026-08-12.json`。

SHACL validator 固定 upstream manifest digest `sha256:208dc8b9…2b0b`，exact digest 记录在执行证据中；派生镜像以 `65532:65532` 运行，并采用 internal-only network、零宿主端口/绑定挂载、只读 rootfs、`cap_drop=ALL`、no-new-privileges 与资源限制。canonical 正控 `schema_valid=true`；内存删除 `datasetId` 的负控 `schema_valid=false` 且有一个 violation。首次与幂等复验证据为 `build/evidence/treehouse/shacl-validator-execution-2026-08-12.json`、`build/evidence/treehouse/shacl-validator-execution-idempotent-recheck-2026-08-12.json`。

EasyRDF 的 Turtle→RDF/XML 转换改变了四个 `sh:pattern` literal 的 lexical form；local-review 派生 app 补丁只在 generated schema disabled 时转发 raw canonical Turtle，canonical SHACL bytes 保持不变。验证后按 application→validator→database 顺序停止，containers、networks 与 app/DB 两个 named volumes 均保留；`build/evidence/treehouse/runtime-pause-after-shacl-validation-2026-08-12.json` 记录 `PAUSED`。publication 仍未执行。
