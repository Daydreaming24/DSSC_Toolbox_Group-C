# Phase 09 Prompt — 最终 QA、Clean Clone、发布证据与 GitHub Readiness

只实施 Phase 09。开始前完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md` 和本文件；进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。

## 1. 目标

对完整 v0.4 release candidate 做从零、无回归、fail-closed 的最终审查；建立机器可读的最终交付清单，复核一键复现入口并建立发布安全检查；完成许可证、第三方再分发、隐私、提交身份与 GitHub 目标的人工决定；在逐项取得外部写授权后，从已提交候选完成本地 clean clone、push、GitHub 上已有的 `validate.yml` 实际运行确认和真正的远程 clean clone。

Phase 09 不新建独立的发布 workflow 或自定义"attestation"文件格式。判断发布是否成功的证据是三件可直接核查的事实，记录在 `build/` 并向用户报告：

1. 已提交的最终候选 commit 通过本地一键复现和全部最终 QA checker。
2. push 后，Phase 08 已有的 `.github/workflows/validate.yml` 针对这个精确 commit SHA 自动触发，且 Ubuntu/Windows/Docker 三个 job 全部成功（通过 `gh run view` 或 GitHub Actions 页面确认，记录 run URL、run ID 和结论）。
3. 从 GitHub 仓库的 canonical URL 做一次真正的 `git clone`（不是本地目录复制），在其中运行对应平台的一键复现命令并确认结果 clean。

这三件事都确认后，可以在**新的一次提交**里把候选 commit 的 SHA、CI run URL/结论、远程 clone 结果写进 `docs/v0.4/STATUS.md`——这不构成自引用，因为这次提交描述的是它之前那个已经存在、不会再变的候选 commit，不是描述它自己。

仅本地通过、尚未 push 或尚未完成远程确认时，只能记录 `RELEASE_CANDIDATE READY`；它不等于 Phase 09 `COMPLETE`。

## 2. 非目标

- 不新增模型概念、字段、规则、fixture 类别、质量指标或治理范围。
- 不改变 D 组契约、Shape、oracle、四状态分类或既有 suite 语义。
- 不修改 validation-suites 合同、四个上游 manifests、早期 Phase 记录或已批准 decisions。
- 不通过放宽检查、删除负例、降低文档状态、改写 expected output 或绕过 CI 修复问题。
- 不把旧 workflow run、其他 branch/commit 的 run、仅成功的部分 job 或本地 copy 当作对当前候选的确认。
- 不自动猜测许可证、GitHub 身份、owner、repository、visibility、default branch、remote、tag 或 release policy。
- 不在对应动作未获单独授权时创建 repository、commit、配置 remote、push、设置默认分支/保护规则、tag 或 release。
- 不要求 Phase 08 的 Treehouse、Mermaid renderer 或外部 ITB/SEMIC 可选轨成功。
- 不新建独立的发布专用 GitHub Actions workflow；发布验证复用 Phase 08 已经跑绿的 `validate.yml`。

## 3. 权威输入

完整读取并核验：

1. Master、`human-intervention-policy.md`、Phase 00–08 prompts 和 `docs/v0.4/STATUS.md` 中 Phase 00–08 的小节。
2. 四个上游 manifests 及 schemas：
   - `C_Semantic_Treehouse/manifests/release-manifest.json`
   - `C_Semantic_Treehouse/manifests/baseline-test-cases.json`
   - `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
   - `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
3. `C_Semantic_Treehouse/manifests/validation-suites.json` 及 `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json`。它们是 Phase 07 已冻结、Phase 08 已跨平台复核的 suite composition 与 `contract_version` 真源，本阶段只读。
4. `docs/v0.4/requirements-traceability.md` 和已批准 decisions。
5. Phase 02 baseline、Phase 05 四状态、Phase 06 semantic/quality/governance、Phase 07 documentation、Phase 08 cross-platform/workflow-static/clean-room 机器证据。
6. `docs/provenance/**`、`inputs/source-archives/README.md`、`docs/provenance/privacy-exclusions.md`。
7. `迁移清单.md` 的完成标准和 GitHub 发布前检查。
8. 当前 Git worktree、index、history、remotes、tags，以及维护者已经明确给出的人工决定。
9. `docs/v0.4/risk-register.md`（Phase 00 baseline risk snapshot）及 `docs/v0.4/STATUS.md` 中 Phase 00–08 各小节记录的对应风险处置。risk-register 本身保持只读，只作为本阶段第 6.7 节收口的输入。

Phase 09 新建的 `C_Semantic_Treehouse/manifests/deliverables.json` 在通过 schema 和跨记录语义检查后，成为最终 required-files 的唯一机器可读清单。验证器不得另行维护第二套硬编码 required-files 列表。

## 4. 进入门槛

进入实施前必须同时满足：

1. Phase 00–08 主线状态均在 `docs/v0.4/STATUS.md` 中记录为 `COMPLETE`；Phase 08 可选轨可逐项 `DEFERRED`。
2. Phase 08 小节明确记录 Windows、Linux validation container、Docker、workflow static policy、validation-suites 合同和 clean-room rehearsal 的成功证据。
3. 四个上游 manifests、schemas、paths、hashes 和 freshness 全部有效。
4. validation-suites 合同：
   - schema 和 `contract_version` 明确；
   - validation-suites manifest hash 与 Phase 08 小节一致；
   - 列出 `frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all`；
   - `all` 的 composition 包含 Phase 06/07 已批准的全部核心检查；
   - 每个 suite 有实现入口、依赖、预期报告和非零失败语义。
5. 当前 Windows 仓库 `.venv` 存在，以下命令实际退出 0：

```powershell
.\.venv\Scripts\python.exe scripts\verify_frozen_files.py
.\.venv\Scripts\python.exe scripts\doctor.py --profile host
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
.\scripts\validate.ps1 -Suite v0.4
.\scripts\validate.ps1 -Suite all
```

6. 当前 staged 与 unstaged 修改均已识别归属，并完成以下只读审计：

```text
git status --short --branch
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
git diff HEAD --check
git diff HEAD --stat
git diff HEAD --name-status
```

7. `docs/v0.4/CHECKPOINT.md` 为空闲。
8. 本阶段具名可写文件不存在无法安全保留的用户或其他成员修改。

进入门槛失败时，先完成安全诊断，把当前进度写入 `CHECKPOINT.md`。需要用户确认或补齐上游产物时标记 `AWAITING_HUMAN_DECISION`；确认没有安全路径时标记 `BLOCKED`，并说明需要回到哪个最早受影响 Phase。Phase 09 不在本地修补上游语义、suite composition 或历史证据。

## 5. 可写路径与保护路径

### 5.1 可写路径

仅允许创建或修改以下 tracked 文件：

- `README.md`
- `迁移清单.md`
- `LICENSE`
- `NOTICE`
- `THIRD_PARTY_MATERIALS.md`
- `C_Semantic_Treehouse/README.md`
- `C_Semantic_Treehouse/FINAL_SUMMARY.md`
- `C_Semantic_Treehouse/docs/demo-script.md`
- `C_Semantic_Treehouse/docs/final-checklist.md`
- `C_Semantic_Treehouse/manifests/deliverables.json`
- `C_Semantic_Treehouse/manifests/schemas/deliverables.schema.json`
- `C_Semantic_Treehouse/evidence/releases/v0.4/README.md`
- `C_Semantic_Treehouse/evidence/releases/v0.4/evidence-index.json`
- `C_Semantic_Treehouse/evidence/releases/v0.4/core-results.json`
- `C_Semantic_Treehouse/evidence/releases/v0.4/core-report.md`
- `scripts/check_deliverables.py`
- `scripts/check_publication_safety.py`
- `scripts/check_evidence_freshness.py`
- `scripts/README.md`
- `docs/v0.4/README.md`
- `docs/v0.4/release-readiness.md`
- `docs/v0.4/human-decisions.md`
- `docs/v0.4/publication-record.md`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`

仅允许写入以下 ignored 临时目录：

- `build/phase-09/**`
- `build/final-qa/**`
- `build/clean-clone/**`
- `build/remote-clean-clone/**`
- `build/ci-verification/**`

`LICENSE`、`NOTICE` 和 `THIRD_PARTY_MATERIALS.md` 只在维护者完成对应许可证/再分发决定后按批准内容创建或更新。

### 5.2 保护路径

除 Master 永久保护范围外，以下路径在本阶段全部只读：

- Phase 00–08 的所有 `STATUS.md` 历史小节、恢复记录、机器结果和批准 decisions。
- `C_Semantic_Treehouse/model/**`
- `C_Semantic_Treehouse/fixtures/**`
- `C_Semantic_Treehouse/tests/**`
- `C_Semantic_Treehouse/mappings/**`
- `C_Semantic_Treehouse/quality/**`
- `C_Semantic_Treehouse/governance/**`
- `C_Semantic_Treehouse/handoff/**`
- 四个上游 manifests 及其 schemas。
- `C_Semantic_Treehouse/manifests/validation-suites.json` 及其 schema。
- `scripts/validate.py`、`scripts/reproduce.ps1`、`scripts/reproduce.sh`、Phase 01–08 的 validator/harness 模块、bootstrap、doctor 和 wrappers。
- `.github/**`（含 Phase 08 的 `.github/workflows/validate.yml`）；Phase 09 不新增或修改任何 workflow 文件。
- `Dockerfile.validation`、`docker-compose.validation.yml`、`Makefile`、`.gitignore` 和 `.gitattributes`。
- 已审核的 Phase 02/04 release evidence；Phase 09 只创建本节列出的四个最终 evidence 文件。

发现保护路径缺陷时，记录最早受影响 Phase，停止 Phase 09，按该 Phase prompt 修复并从那里重新验收到 Phase 09。维护者"知情"不构成越界修改授权；需要重新执行对应 Phase。

已有 Git remote、repository、history、branch、tag、release 和保护设置始终只读，直到第 6.8 节取得对应动作的独立人工授权。

## 6. 任务

### 6.1 冻结并验证 Validation-Suites 合同

在任何最终 QA 生成前：

1. 读取 validation-suites schema、`contract_version` 和 manifest SHA-256。
2. 双向核对 validation-suites 合同与 `scripts/validate.py` 的合法公开 suite、`all` composition、报告路径和失败语义。
3. 核对 Phase 08 小节记录的 validation-suites hash。
4. 证明 0 suite、重复 suite ID、未知 suite、缺实现、缺报告或从 `all` 删除必需 component 均会失败。
5. 把 validation-suites `contract_version`/manifest hash 写入最终确定性 QA 结果和 deliverables manifest；schema 作为普通 tracked deliverable 单独记录 hash。

本阶段不得修改 validation-suites 合同或 `scripts/validate.py`。发现差异时说明需要回到创建或最后修改该合同的最早 Phase。

### 6.2 建立最终 Deliverables Manifest

创建：

- `C_Semantic_Treehouse/manifests/schemas/deliverables.schema.json`
- `C_Semantic_Treehouse/manifests/deliverables.json`
- `scripts/check_deliverables.py`

schema 使用明确 JSON Schema draft，至少要求：

- `schema_version`、release/profile ID。
- validation-suites manifest/schema path、`contract_version` 和 manifest SHA-256；schema 自身 hash 由普通 deliverable 记录承载。
- 唯一、非空的 deliverable ID。
- 仓库相对 POSIX path；禁止绝对路径、`..` 逃逸、glob 和大小写碰撞。
- SHA-256、media type、role、required/publish 状态。
- origin：project-authored、derived、inherited、third-party 或 generated-reviewed。
- license/redistribution classification、适用 license identifier 或 `NOASSERTION`、人工 decision ID。
- 对 derived/inherited/third-party 文件的来源 path/hash 或 manifest 引用。

`deliverables.json` 明确列出最终 GitHub candidate 中的 tracked publication files，包括模型、inputs、prompts、manifests、schemas、fixtures、tests、治理、SSSOM、quality、reports、handoffs、`.github/workflows/validate.yml`、环境入口、Phase 08 reproduce scripts、administrative files 和 release evidence index。清单唯一排除自身，并且不嵌入自身 hash；它必须列出并校验 `deliverables.schema.json`、`check_deliverables.py`、`evidence-index.json` 以及其余全部候选 tracked 文件的实际 SHA-256。这些文件不反向嵌入 `deliverables.json` 的 hash，因此这一依赖关系无环。`deliverables.json` 自身的 SHA-256 只进入 ignored runtime evidence。任何 checker 都不得硬编码 `deliverables.json` 的预期 hash。

`check_deliverables.py` 先做 schema validation，再做跨记录语义检查：

- ID、规范化路径和 case-folded path 唯一。
- 所有 required 文件存在、非空、格式可解析且 hash 匹配。
- 所有 release-manifest artifacts、四个 manifests/schemas、validation-suites 合同、最终报告/handoffs/CI/reproduce/evidence 文件，以及 `迁移清单.md`、`docs/v0.4/README.md` 和 `scripts/README.md` 均被覆盖。
- 除 `deliverables.json` 自身这一具名例外外，`git ls-files` 中每个将随 candidate push 的 tracked 文件均有一条带实际 hash 的 manifest 记录；manifest 中 `publish: false` 的文件不得仍留在将被 push 的 tracked tree。
- publish 文件均有明确 license/redistribution decision；`NOASSERTION` 必须引用维护者明确决定。
- manifest 不列自己，不把 ignored build/cache/secret/upstream 当作 deliverable。
- required-files 检查只消费 `deliverables.json`，不得在代码中维护第二套文件名清单。

至少在 `build/phase-09/negative-controls/deliverables/` 的临时副本证明：重复 ID、大小写路径碰撞、`../`、绝对路径、缺失文件、空文件、陈旧 hash、未知 role、缺 license decision 和空 entries 均非零失败。

### 6.3 建立最终安全、隐私和 Freshness 检查

实现具名 checker：

- `scripts/check_publication_safety.py`
- `scripts/check_evidence_freshness.py`

Phase 09 的全部 Python checker 只使用标准库或 Phase 01 lock 已声明并带 hash 的依赖，统一由仓库 `.venv` 运行；不得临时 `pip install`、调用全局 Python 或引入未登记工具。确需新增运行时依赖时说明需要回到 Phase 01 更新环境合同和 lock，并从那里重新验收。

安全检查至少覆盖：

- ZIP 外个人绝对路径、用户名、临时目录和解释器路径。
- secrets、token、private key、`.env`、credential 和未清理日志。
- Git worktree、index 和 history 中作者姓名/邮箱及历史敏感内容。
- 两份来源 ZIP 的文件名、大小、hash 和批准的内部路径例外。
- D 组文件、第三方内容、许可证和再分发 decision。
- repository size、大文件、cache、Treehouse upstream 和 macOS metadata。
- `.gitattributes`、脚本 executable/line-ending 和 workflow 权限。

freshness 检查至少绑定：

- 四个上游 manifests hashes。
- validation-suites `contract_version`/manifest hash。
- deliverables manifest hash。
- lock hash。
- validator/harness 源文件 hashes 或已提交 clean candidate commit。
- 每个选定 evidence 的 inputs/reports hashes。

在 `build/phase-09/negative-controls/scanners/` 使用生成的无害 canary 和临时副本证明：

- secret canary 被拒绝。
- Windows 用户目录和 POSIX home 绝对路径 canary 被拒绝。
- `.env`/private-key header canary 被拒绝。
- stale input hash、stale report hash 和错误 validation-suites hash 被拒绝。
- 已过期或引用旧 manifest 的 evidence 被拒绝。
- 允许的 ZIP 内历史路径例外只能通过具名、已批准 allowlist，不能通过全局忽略规则放行。

每个 negative control 必须返回非零并有 reason code。发现 0 个扫描目标、scanner 异常、未知 allowlist 或 negative control 未触发时，checker 本身返回非零。

场景数据的 CC-BY-4.0 只约束该场景数据。仓库代码、D 组材料和来源 ZIP 分别使用维护者批准的许可/再分发决定。

### 6.4 只读复核 Phase 08 一键复现入口

把 Phase 08 已创建的 `scripts/reproduce.ps1` 和 `scripts/reproduce.sh` 作为只读上游产物复核。本阶段先核对它们已被 tracked、非空、hash 与 Phase 08 evidence 一致，并分别满足 Windows PowerShell 5.1+ 与文档规定的 Linux shell 合同；随后静态检查并实际证明两个脚本：

1. 从脚本自身位置解析仓库根，支持空格和非 ASCII 路径。
2. 运行对应 Phase 01 bootstrap，严格消费含 hashes 的 lock，并核对已有或新建 `.venv`。
3. 显式使用仓库 `.venv` 运行 `doctor.py --profile host` 和 frozen 校验。
4. 通过 Windows `validate.ps1 -Suite all` 或 Linux `validate.sh --suite all` 运行 validation-suites 合同 `contract_version` 固定的 `all` composition。
5. 原样返回第一个非零退出码；不接受改变 composition 的参数，不 skip、不回落到全局 Python，也不自动重写 expected files。

Phase 09 的 deliverables、安全与 freshness 检查在一键复现命令成功后由本阶段命令分开执行，不修改 Phase 08 脚本。任一脚本缺失、hash 不符、接口不完整或行为失败时，记录诊断，说明需要回到 Phase 08 修复；修复后从 Phase 08 重新验收到本阶段。

README 的最终单命令固定为：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
```

```bash
./scripts/reproduce.sh
```

需要联网的首次 bootstrap 与后续离线边界必须明确记录。重复运行应幂等，确定性核心结果应稳定。Phase 09 只把上述两条已存在命令写入 README，不创建或编辑对应脚本。

### 6.5 从零运行全部本地核心验证

在当前 Windows 工作区运行 `scripts/reproduce.ps1`，随后以 `.venv` 运行第 8.1 节的 Phase 09 checker、只读 documentation/CI checker及其 negative controls；并运行 Phase 08 的 Linux validation container、Docker 无缓存 build/default `all`。所有 required test 的 discovered/executed/passed/failed/skipped 均明确，required skipped 为 0。

逐份审查机器 JSON 和生成 Markdown，确认 expected FAIL/INAPPLICABLE/UNTESTABLE 精确命中 oracle，harness `ERROR` 没有被业务状态掩盖。validation-suites `contract_version`/manifest hash、validator source hashes、manifests、lock 和结果 freshness 必须一致。

### 6.6 固化无自引用的 Tracked 发布证据

仅创建或更新第 5.1 节列出的四个 release evidence 文件。规则如下：

- `core-results.json` 是当前确定性上游核心 suite 结果聚合，记录 validation-suites manifest/schema path、`contract_version`/manifest hash、四个上游 manifests、lock、deliverables 的稳定 path、validator source hashes 和上游 gate 结果，不记录 deliverables/安全/freshness 自检结果、deliverables hash、实时 timestamp、当前 commit SHA 或 CI run ID。deliverables、安全和 evidence-freshness checker 的结果只进入 ignored runtime evidence。
- `core-report.md` 由 `core-results.json` 确定性生成。
- `evidence-index.json` 记录稳定路径和 role，不写当前 HEAD/run/remote-clone 动态绑定。
- release evidence README 解释稳定 tracked 内容和 push 后需要另外核查的动态事实（CI run、远程 clone）。
- raw environment/logs 留在 `build/`；任何准备发布的内容先通过 safety/freshness 检查。

### 6.7 完成稳定最终文档

更新第 5.1 节列出的 README、迁移清单、checklist、demo、FINAL_SUMMARY、release-readiness、human-decisions、publication-record 和 `STATUS.md`。

- `release-readiness.md` 逐条列出 `docs/v0.4/risk-register.md` 登记的每个风险 ID，标注最终处置：`RESOLVED`（注明由哪个 Phase 的 `STATUS.md` 小节解决及证据路径）、`ACCEPTED_LIMITATION`（注明理由，并同步写入 final checklist 的已知限制）或 `OPEN_BLOCKING`（该风险被 Phase 00 登记为阻塞发布且尚未解决）。本步骤只读取 `risk-register.md`，不回写该文件。
- Phase 01–08 各自在 `STATUS.md` 小节里可能记录了不在 Phase 00 原始快照里的"新增风险"（每个 Phase 的产物/交接章节都要求"新增风险登记供 Phase 09 汇总"）。逐个通读 Phase 01–08 的 `STATUS.md` 小节，把这些新增风险单独列进 `release-readiness.md` 的"新增风险"一节，同样标注 `RESOLVED`/`ACCEPTED_LIMITATION`/`OPEN_BLOCKING` 终态；不能只处理 Phase 00 快照里的原始风险 ID 而遗漏这些。
- 根 `迁移清单.md` 继续作为持续更新的人读工作清单摘要（机器可读真源始终是 `docs/v0.4/STATUS.md`，冲突时以 `STATUS.md` 为准）。只依据 Phase 00–08 已通过证据更新对应 checkbox、状态和稳定 evidence 路径；Phase 09 的 push、CI 确认与远程 clean clone 门槛在完成前保持未完成，不写当前 commit SHA、run ID/URL 或临时 `build/` 路径。
- `docs/v0.4/README.md` 从"截至 Phase 07"导航更新为最终稳定导航，至少链接 Phase 08/09 记录、release-readiness、human decisions、publication record、最终 evidence index 和 deliverables。
- `scripts/README.md` 保留 Phase 08 已登记的 reproduce/CI/clean-room 说明，只增加 Phase 09 三个具名 checker 的调用方式、输入输出和 fail-closed 语义。
- `check_deliverables.py` 验证这三个文件存在且 hash/role/license 记录匹配；只读 `scripts/check_documentation.py` 对它们执行正常检查、deterministic rerun 和既有 negative controls。文档 checker 缺陷说明需要回到 Phase 07，Phase 09 不修改它。

Tracked 文档只记录：

- 稳定 repository URL、visibility、default branch 和 workflow path。
- validation-suites 合同、deliverables 的路径。
- 可选轨真实状态、已知限制和长期责任。
- risk-register 原始风险与 Phase 01–08 新增风险的最终处置（`RESOLVED`/`ACCEPTED_LIMITATION`/`OPEN_BLOCKING`）。

Tracked 文档在候选 commit 形成前不得写当前 HEAD SHA、run ID、run URL、job ID 或"当前 CI 已成功"声明。这些事实只在推送、CI 确认、远程 clone 全部完成之后，作为对已经存在、不会再变的候选 commit 的描述，写进随后的一次记录性提交（见第 6.11 节）。文档不得超出证据宣称 Treehouse、Mermaid visual QA 或 ITB/SEMIC 成功。

### 6.8 完成人工发布决定和远程预检

任何外部写入前，向维护者展示并分别记录以下决定。每项使用 `APPROVED`、`DENIED` 或 `NOT_REQUESTED`，附批准主体和范围：

#### 内容与身份

- repository license 或"不授予通用 license"的明确选择。
- D 组文件再分发授权。
- 两份来源 ZIP 再分发授权。
- ZIP 内历史绝对路径公开风险接受决定。
- commit author name/email 和 GitHub 登录身份。

#### Repository 模式二选一

1. **创建新 repository**：单独授权创建操作，并确认 owner/organization、repository name、public/private visibility、default branch、初始化策略和目标 canonical URL。
2. **使用既有 repository**：单独授权使用该精确 repository，并核对 immutable repository ID、owner、name、canonical URL、visibility、default branch、现有内容、现有 branches/tags/remotes 和是否允许写入目标 branch。

不得把"提供 owner/name"解释为"授权创建 repository"，也不得把"允许 push"解释为"允许使用任意同名 repository"。目标已存在但用户选择"新建"时停止并重新确认，禁止覆盖或接管。

#### 外部写动作逐项授权

- 创建 GitHub repository。
- 创建本地候选 commit。
- 新增 Git remote；若已有 remote，授权使用该精确 URL。覆盖/改写 remote 需要另一项明确授权。
- push 精确 branch（push 会按 Phase 08 已配置的触发条件自动运行 `validate.yml`，不需要另外手工触发）。
- 手工重新运行 `validate.yml` 中对应候选 SHA 的 run（仅在自动触发失败或需要重跑时使用，需单独授权）。
- 设置或更改 default branch。
- 设置 branch protection/required checks。
- 创建 tag。
- 创建 GitHub Release。

未获授权的动作保持 `NOT_REQUESTED`，不能顺带执行。普通 push 授权不包含 force push；本流程始终禁止 force push、history rewrite、squash/rebase 和删除远程引用。

执行写操作前完成只读身份/权限预检：

- 当前 GitHub account/organization membership 与批准主体一致。
- 认证机制可用，最小 scopes 足够；证据不显示 token/credential。
- 新建目标不存在，或既有目标的 immutable ID/URL 与批准记录一致。
- visibility、default branch、branch protection 能力和 required jobs 计划明确。
- local branch、remote name/URL 和预期 push refspec 精确展示给维护者。

任一必需决定或预检缺失时，输出 `RELEASE_CANDIDATE READY — PUBLICATION AWAITING HUMAN DECISION`，Phase 09 标记 `AWAITING_HUMAN_DECISION` 并把当前进度写入 `CHECKPOINT.md`。不得用 `DEFERRED` 规避。

决定形成后，按批准范围创建或更新 `LICENSE`、`NOTICE` 和 `THIRD_PARTY_MATERIALS.md`，随后重新生成 deliverables manifest、tracked evidence、最终 QA 与本地一键复现结果。

### 6.9 创建最终候选 Commit 并验证本地 Clean Clone

仅在维护者审核 tracked candidate 并授权 commit 后继续：

1. 保存本轮变更基线 commit 和 `git diff HEAD --name-status`；确认 staged/unstaged diff 均在第 5.1 节 allowlist。
2. 创建一个最终候选 commit；禁止 amend、squash、rebase 或历史改写。
3. 记录候选 SHA到 `build/phase-09/`，不回写 tracked 文件。
4. 在经过绝对路径核验的 `build/clean-clone/` 下，从该本地 commit 执行真正 `git clone`；工作树复制不算。
5. 在 clone 中运行相应平台的单命令 `scripts/reproduce.ps1` 或 `scripts/reproduce.sh`；成功后用该 clone 的 `.venv` 运行 Phase 09 三个最终 QA checker、documentation/CI 静态检查。
6. 确认 clone resolved SHA 等于候选 SHA，运行后无 tracked diff、无意外 untracked 文件。
7. 把环境、命令、退出码、结果 hashes 写入 ignored `build/clean-clone/`。

本地 clean clone 失败时，候选不能发布。任何修复形成新 commit 时都产生新的候选 SHA，之前的本地/远程验证全部失效，必须重新做一遍。

### 6.10 按授权 Push 并确认远程 CI 与远程 Clean Clone

执行每个外部写动作前，再次展示目标和该动作的批准记录。

1. 新 repository 模式：只在"创建 repository"获批后创建精确 owner/name/visibility/default-branch 目标；创建后只读核对 immutable repository ID 和 canonical URL。
2. 既有 repository 模式：只读核对 ID/URL/visibility/default branch/现有 refs，确认与批准记录一致。
3. 仅在"新增/使用 remote"获批后配置或使用精确 remote。已有 remote URL 不一致时停止，禁止静默覆盖。
4. 仅在"push branch"获批后执行普通 push，禁止 force。push 会按 `validate.yml` 已有的触发条件自动运行。
5. 等待该 push 触发的 run 完成。用 `gh run view <run-id>`（有 `gh` CLI 时）或直接查看 GitHub Actions 页面确认：run 的 `head_sha` 精确等于候选 SHA，Ubuntu、Windows、Docker 三个 job 全部成功。把 run URL、run ID、结论和三个 job 的结果写入 `build/ci-verification/`。旧 run、其他 commit 的 run 或部分成功的 job 都不能作为确认依据；确认失败或需要重跑时，重新触发前先取得单独授权，且只针对同一候选 SHA 重跑，不允许悄悄换成新 commit 再冒充同一次确认。
6. 在经过绝对路径核验的 `build/remote-clean-clone/` 下，从 GitHub 仓库的 canonical URL 执行真正 `git clone`（public repository 使用匿名 clone；private repository 只使用运行本次操作所需的最小、只读、不持久化的凭据，不把凭据写入任何日志或证据）。核对 clone 得到的 HEAD 等于候选 SHA，运行相应平台的一键复现命令，确认结果 clean、无意外 diff。把命令、退出码和结果 hashes 写入 `build/remote-clean-clone/`。
7. tag 只在独立 tag 授权后创建，并指向已经完成上述确认的精确 commit。
8. GitHub Release 只在独立 release 授权后创建；release notes 可以链接第 5 步记录的 CI run URL 作为验证依据。
9. default branch 或 branch protection 只按各自批准项修改。无权限时记录 `PENDING OWNER ACTION`；若其被定义为必需发布 gate，则 Phase 保持 `AWAITING_HUMAN_DECISION`。

### 6.11 记录发布确认，完成最终一致性审查

第 6.10 节的 CI 确认和远程 clean clone 都成功后：

1. 只读核对：远程 default branch 的候选 SHA、Actions run 的 `head_sha`、远程 clone resolved SHA 三者完全相同；三个必需 job 都成功；本地仓库 HEAD 与已批准候选一致，工作树没有未预期的 tracked 修改。
2. 在一次新的记录性提交里，把候选 commit SHA、CI run URL/run ID/结论、远程 clone 结果写进 `docs/v0.4/STATUS.md` 的 Phase 09 小节，并按需要更新 `publication-record.md`。这次提交描述的是它之前那个已经确认完成的候选 commit，不是描述自己，因此不构成自引用；这次提交本身不需要再被 push 后重新做一轮 CI/clone 确认（它不改变已发布的模型、验证逻辑或发布证据的实质内容）。
3. Phase 09 的有效状态在这次记录完成后成为 `COMPLETE`。

若发现候选 commit 本身需要修改，必须创建新的候选 commit，并从本地 clean clone、push、CI 确认、远程 clean clone 全部重新做一遍；旧的确认结果不能延用到新 commit。

## 7. 必需产物

### Tracked 稳定产物

- `C_Semantic_Treehouse/manifests/deliverables.json` 及 schema。
- 三个最终 QA checker：`check_deliverables.py`、`check_publication_safety.py`、`check_evidence_freshness.py`。
- 经本阶段只读复核的 Phase 08 `scripts/reproduce.ps1`、`scripts/reproduce.sh`。
- 最终根/package README、`迁移清单.md`、`docs/v0.4/README.md`、`scripts/README.md`、final checklist、demo script、FINAL_SUMMARY。
- `release-readiness.md`（含 Phase 00 risk-register 逐项处置结论）、`human-decisions.md`、`publication-record.md`。
- 四个具名 release evidence 文件。
- `docs/v0.4/STATUS.md` 中的 Phase 09 小节（记录性提交，写在候选 commit 之后）。

### Ignored 本地运行产物

- `build/final-qa/**`。
- `build/clean-clone/**`。
- `build/remote-clean-clone/**`。
- `build/ci-verification/**`。

### 外部动态事实（不进入 tracked 文件，只作为第 6.11 节记录的依据）

- CI run 的 head SHA、run ID/URL、三个 job 的结论。
- 远程 clone 的 resolved SHA 和一键复现结果。

## 8. 必需命令

### 8.1 当前 Windows 工作区

```powershell
git status --short --branch
.\.venv\Scripts\python.exe scripts\verify_frozen_files.py
.\.venv\Scripts\python.exe scripts\doctor.py --profile host
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
.\scripts\validate.ps1 -Suite v0.4
.\scripts\validate.ps1 -Suite all
.\.venv\Scripts\python.exe scripts\check_deliverables.py
.\.venv\Scripts\python.exe scripts\check_publication_safety.py
.\.venv\Scripts\python.exe scripts\check_evidence_freshness.py
.\.venv\Scripts\python.exe scripts\check_documentation.py
.\.venv\Scripts\python.exe scripts\check_documentation.py --self-test
.\.venv\Scripts\python.exe scripts\check_ci.py
.\.venv\Scripts\python.exe scripts\check_ci.py --self-test
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
git diff HEAD --check
git diff HEAD --stat
git diff HEAD --name-status
git status --short
```

### 8.2 Linux、Docker 与 clones

Linux clean environment 使用：

```bash
./scripts/reproduce.sh
./.venv/bin/python scripts/check_deliverables.py
./.venv/bin/python scripts/check_publication_safety.py
./.venv/bin/python scripts/check_evidence_freshness.py
./.venv/bin/python scripts/check_documentation.py
./.venv/bin/python scripts/check_documentation.py --self-test
./.venv/bin/python scripts/check_ci.py
./.venv/bin/python scripts/check_ci.py --self-test
```

- Windows 本地 clean clone：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\reproduce.ps1`。
- Linux validation container：执行同一 `scripts/validate.py --suite all`，随后运行三个最终 QA checker。
- Docker：无缓存 build 和默认 `--suite all`，并核对 validation-suites `contract_version`/manifest hash。
- 远程确认：`gh run view <run-id>`（或 Actions 页面）+ 真正 `git clone <github-url>` 到 `build/remote-clean-clone/`，运行相应平台一键复现命令。

### 8.3 Negative controls

运行并记录 deliverables、privacy、secret、path、freshness、validation-suites 合同的全部临时破坏测试。它们只能写 `build/phase-09/negative-controls/`，不得修改 tracked oracle。

## 9. 验收矩阵

| ID | 验收项 | 通过标准 | 证据 |
|---|---|---|---|
| P09-A01 | Validation-suites 合同 | schema 有效，`contract_version`/manifest hash 与 Phase 08 一致，`all` composition 完整且本阶段零修改 | contract audit |
| P09-A02 | Deliverables schema | schema 有效；跨记录 checker 拒绝重复/碰撞/逃逸/空项/未知 role | negative controls |
| P09-A03 | Required files | required deliverables 全部非空、可解析、hash/role/license/decision 匹配 | deliverables results |
| P09-A04 | Frozen/baseline/v0.4 | frozen、历史 baseline、D requirements、四状态和 negative controls 全通过 | core results |
| P09-A05 | 语义/治理/文档 | SPARQL、SSSOM、quality、governance、provenance、links、handoffs 与三个最终导航文件全通过 | `all`/documentation results |
| P09-A06 | Scanner fail-closed | privacy/secret/path/freshness canaries 均被拒绝；0 扫描目标失败 | scanner controls |
| P09-A07 | 一键复现 | Windows 和 Linux 单命令从 lock 成功，路径/退出码合同一致 | reproduce evidence |
| P09-A08 | 跨平台 | Windows、Linux container、Docker 消费同一 validation-suites `contract_version`/manifest hash 并全部成功 | platform evidence |
| P09-A09 | 修改边界 | staged/unstaged/HEAD diff 均在具名 allowlist，早期记录/manifests 零修改 | Git audit |
| P09-A10 | 人工决定 | 内容、身份、repository 模式和每项外部写动作分别有明确决定 | human decisions |
| P09-A11 | Repository 预检 | 新建或既有路径唯一，ID/owner/name/visibility/default branch/identity 精确 | remote preflight |
| P09-A12 | 本地 clean clone | 已提交候选一键复现与 Phase 09 checker 成功，resolved SHA 正确且运行后 clean | local clone evidence |
| P09-A13 | CI 确认 | push 触发的 run 的 `head_sha` 精确等于候选 SHA，Ubuntu/Windows/Docker 三个 job 全部成功；旧 run/其他 commit 不能作为依据 | run URL/结论记录 |
| P09-A14 | 远程 clean clone | 真正从 GitHub URL clone、resolved SHA 等于候选、一键复现成功且 clean | remote clone evidence |
| P09-A15 | 无自引用 | 候选 commit 本身不含当前 commit/run/clone 的动态值；这些事实只出现在候选之后的记录性提交里 | commit content audit |
| P09-A16 | 最终有效状态 | 第 6.11 节的记录性提交完成，三项外部事实与候选 SHA 一致 | STATUS.md Phase 09 小节 |
| P09-A17 | 可选轨 | PASS/DEFERRED 状态真实且不影响核心 | optional evidence index |
| P09-A18 | 风险台账收口 | risk-register 原始风险 ID 与 Phase 01–08 `STATUS.md` 小节中记录的新增风险，都有 `RESOLVED`/`ACCEPTED_LIMITATION`/`OPEN_BLOCKING` 之一的终态；标记阻塞发布的风险均非 `OPEN_BLOCKING` | release-readiness.md |

P09-A01 至 P09-A12、P09-A15 以及 P09-A18 在最终候选 commit 内静态或本地验证。P09-A13、P09-A14 由候选 commit push 后的实际 CI run 和远程 clone 验证，P09-A16 由第 6.11 节的记录性提交满足，P09-A17 保留可选轨真实状态。全部 P09-A01 至 P09-A18 满足后，Phase 09 的有效状态才是 `COMPLETE`。

## 10. AWAITING、BLOCKED 与 DEFERRED 规则

### 必须暂停

- 任一主线 suite、final checker、negative control 或必需平台失败。
- validation-suites 合同缺失、变化、composition 不完整，或 `contract_version`/manifest hash 与 Phase 08 不一致。
- deliverables 清单缺失、陈旧、路径逃逸、hash/license/decision 不一致。
- candidate tracked tree 含未登记文件，或含 `publish: false`、无再分发授权却仍会被 push 的文件。
- release evidence 陈旧、不完整或包含敏感信息。
- risk-register 原始风险或 Phase 01–08 新增风险中，标记为阻塞发布的仍为 `OPEN_BLOCKING`。
- 候选未提交或本地 clean clone 失败。
- GitHub repository 身份/可见性/default branch 与批准目标不一致。
- push 触发的 run 未运行/失败/head_sha 不匹配候选 SHA。
- 远程 clone 未完成，或未按一键入口复现，或 resolved SHA 不匹配。
- tracked 文件在候选 commit 本身里写入了当前动态 SHA/run ID，形成自引用。
- final checklist/summary 含不实声明。

以上情况先按 `human-intervention-policy.md` 完成安全诊断并把进度写入 `CHECKPOINT.md`。许可证、身份、repository 模式或任一外部写动作尚未获得明确决定，或 CI/远程 clone 确认尚未完成时，标记 `AWAITING_HUMAN_DECISION` 并记录 `RELEASE_CANDIDATE READY — PUBLICATION AWAITING HUMAN DECISION`；确认当前没有可批准的安全路径时标记 `BLOCKED`。不得用 `DEFERRED` 绕过发布门槛。

### 允许 DEFERRED

只允许继承 Phase 08 已登记的可选轨：Semantic Treehouse、Mermaid 完整渲染/视觉 QA、外部 ITB/SEMIC。它们在 final checklist 保留真实状态和恢复步骤。

GitHub CI 确认、远程 clone、repository/许可决定属于最终必需门槛，不能 DEFERRED。

## 11. 阶段交接

### CI 确认/远程 clean clone 尚未完成

1. 记录 `RELEASE_CANDIDATE READY`，标记 `AWAITING_HUMAN_DECISION` 或 `BLOCKED`，把当前进度写入 `CHECKPOINT.md`。
2. 报告已完成的本地/静态门槛、未满足的 P09-A13/P09-A14/P09-A16 外部门槛、批准记录和下一项精确动作。
3. 停止，不把 release candidate ready 称为发布完成。

### CI 确认与远程 clean clone 均已完成

1. 按第 6.11 节创建记录性提交，把候选 commit SHA、CI run URL/结论、远程 clone 结果写入 `docs/v0.4/STATUS.md` 的 Phase 09 小节。
2. 把 `docs/v0.4/CHECKPOINT.md` 清空回占位符状态。
3. 向用户交付 repository URL、最终候选 commit SHA、CI run URL、release evidence index、final checklist、FINAL_SUMMARY 和 demo script。
4. tag、Release、default branch 或 branch protection 中任何 `NOT_REQUESTED` 项保持不变，不补做未授权操作。
5. 报告最终 Git 状态和长期维护事项。

## 12. Stop

Phase 09 有效状态成为 `COMPLETE`，或形成真实 `BLOCKED` 后立即停止。不得继续新增功能、修改模型/验证范围，或执行未获授权的 GitHub 操作。
