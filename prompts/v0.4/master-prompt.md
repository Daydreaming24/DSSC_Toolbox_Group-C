# DSSC C 组 v0.4 Master Prompt

你正在 DSSC Toolbox C 组 Semantic Governance v0.4 仓库中工作。完整读取本 prompt、`prompts/v0.4/human-intervention-policy.md` 和当前 Phase prompt 后，只执行当前 Phase。

## 1. 总目标

在保留 v0 迁移基线和所有冻结输入可追溯性的前提下，交付 Building Energy Consumption Data Product 的 v0.4 语义治理可复现包。最终结果必须：

1. 忠实执行 D 组最终 SHACL TTL 契约。
2. 保留 v0.1–v0.3 历史模型并证明无回归。
3. 实现 `PASS`、`FAIL`、`INAPPLICABLE`、`UNTESTABLE` 四种业务结果。
4. 在 Windows、Linux、Docker 和 GitHub Actions 中使用同一个 Python 编排核心稳定复现。
5. 生成可审计的模型、fixtures、manifest、报告、治理、交接和发布证据。
6. 让新成员从干净 clone 按 README 完成环境建立和验证。

核心验证不得依赖 Semantic Treehouse、在线 validator、GPU、ML 模型、数据库或私有密钥。Semantic Treehouse 是独立、可延后的证据轨。

## 2. 权威信息顺序

发生冲突时，按以下顺序处理并记录：

1. 当前用户指令、仓库中的 `AGENTS.md` 和适用的安全规则。
2. `prompts/v0.4/human-intervention-policy.md`：所有 Phase 通用的暂停条件、人工确认清单和状态恢复步骤。
3. `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`：v0.4 规范性、可执行契约。
4. `inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md`：解释性材料。
5. `inputs/project/v0.4/806.md` 与 `inputs/original-plan/`：项目目标和场景边界。
6. `docs/v0.4/requirements-traceability.md`、已批准的兼容性决策和 manifests。
7. v0.1–v0.3 模型、v0 文档、旧报告和旧脚本：历史基线与重构参考。

规范性 TTL 与说明不一致时，保留两份原件，登记 issue/decision，禁止静默改写收到的文件。历史 PASS 只能证明历史执行，不能证明 v0.4 当前通过。

## 3. 永久保护范围

除非用户明确改变迁移策略，以下路径为只读：

- `inputs/source-archives/received/**`
- `inputs/original-plan/**`
- `inputs/project/v0.4/**`
- `inputs/d-group/v0.4/received/**`
- `archive/**`
- `prompts/v0/**`
- `C_Semantic_Treehouse/model/v0.1/**`
- `C_Semantic_Treehouse/model/v0.2/**`
- `C_Semantic_Treehouse/model/v0.3/**`
- `docs/provenance/manifests/frozen-files-SHA256SUMS`

每个 Phase 还必须声明更窄的可写路径和阶段特有保护路径。发现既有未提交修改时，先识别其归属并避开；不得覆盖、清理或回退用户修改。

已经在 `docs/v0.4/STATUS.md` 中记录为 `COMPLETE` 的 Phase 小节和已审核发布证据按只读处理。需要纠错时，先按 `human-intervention-policy.md` 的状态恢复步骤处理最早受影响 Phase，用新增小节记录修订依据，不覆盖原有记录；禁止静默改写历史证据。

执行 Phase 时不得修改本目录中的 prompt 来降低当前验收门槛。prompt 的修订应成为独立、显式的流程设计变更，并在提交说明中注明原因。

## 4. 版本和模型边界

- `v0` 表示原仓库整体基线。
- `v0.1`、`v0.2`、`v0.3` 表示历史语义模型版本。
- `v0.4` 表示根据 D 组新契约形成的目标版本。
- Dataset ID `building-energy-hourly-v1` 与仓库/模型版本无关，保持原值。

v0.4 metadata wire profile 使用 D 组 TTL 中的 `dcat:Dataset`、`ex:`、`dcat:`、`dct:` 路径和严格值约束。Energy Reading Record 若保持 v0.3 不变，应由 release manifest 明确引用 v0.3 合同，避免通过无意义复制制造新版本。

## 5. 阶段依赖

主线严格按顺序执行：

`00 → 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09`

- 必需 Phase 的 `BLOCKED` 或 `AWAITING_HUMAN_DECISION` 会阻止当前及后续 Phase。
- `DEFERRED` 只适用于 Phase 08 中明确标记的 Semantic Treehouse、Mermaid 或外部 ITB/SEMIC 证据轨；Phase 09 只继承这些既有 DEFERRED 状态，不新增可延期项。
- 任何后续修改影响早期产物时，先按 `human-intervention-policy.md` 的状态恢复步骤处理最早受影响 Phase，重新验收通过后，再逐阶段确认恢复下游 Phase。
- 不允许用“已记录 blocker”跳过必需门槛继续主线。

## 6. 环境合同

最终环境必须分为三个档位：

1. 核心开发：Git、固定完整补丁号的 CPython 3.12、由该解释器建立的仓库 `.venv`、固定并校验的 pip/bootstrap toolchain、精确且含哈希的依赖锁。
2. 发布验证：固定 Python 基础镜像版本和 digest 的 Linux 容器，执行同一个 Python 入口。
3. 可选证据：Semantic Treehouse、Mermaid、ITB/SEMIC，分别固定外部版本和网络边界。

Phase 01 必须先登记团队实际 OS/architecture，再冻结支持矩阵。Windows host 和固定 Linux 容器是必需认证轨；macOS 或其他未实际认证的 host 使用同一固定 Docker 轨，直到对应原生 bootstrap 在该平台真实通过后才能宣称原生支持。

Windows 核心入口使用 Windows PowerShell 5.1+ 薄包装，不能依赖 GNU Make、POSIX shell 或 PowerShell 7。Linux shell、Make、Docker 和 CI 只调用统一 Python 编排器，不实现第二套验证逻辑。

依赖缺失、版本不符、lock hash 不匹配和 `pip check` 失败都必须 fail closed。普通 bootstrap 只消费 lock；锁生成工具及版本必须记录。首次安装、镜像拉取和可选外部工具的网络需求必须写入文档，并按 `human-intervention-policy.md` 取得人工确认。

## 7. 统一命令合同

完成对应 Phase 后，仓库应逐步提供并保持以下合同：

下列 `python` 是跨平台的规范化表示。Phase 01 完成后，host 实际执行必须显式使用 `.venv\Scripts\python.exe`（Windows）、`./.venv/bin/python`（Linux），或使用会选择该解释器的 `validate.ps1`/`validate.sh` 薄包装；不得让命令回落到全局 Python。Phase 00 以及 Phase 01 尚未建立 `.venv` 时，冻结校验使用 Phase 00 固定的 PowerShell `Get-FileHash` 或 Linux `sha256sum --check` 合同。

```text
python scripts/verify_frozen_files.py
python scripts/doctor.py
python scripts/validate.py --suite frozen
python scripts/validate.py --suite environment
python scripts/validate.py --suite baseline
python scripts/validate.py --suite traceability
python scripts/validate.py --suite v0.4-model
python scripts/validate.py --suite v0.4
python scripts/validate.py --suite all
```

Windows、Linux 和 Docker 包装命令必须调用仓库 `.venv` 或容器内的同一个 `scripts/validate.py`。尚未实现的必需 suite 必须返回非零并明确报告 `NOT_IMPLEMENTED`，不能用成功 stub 占位。

最终的一键复现合同固定为：

```text
.\scripts\reproduce.ps1     # Windows PowerShell 5.1+
./scripts/reproduce.sh       # Linux
docker compose -f docker-compose.validation.yml run --rm validation --suite all
```

`reproduce.ps1` 和 `reproduce.sh` 必须从零创建/校验 `.venv`、严格消费 lock、运行 doctor，再执行注册表固定的 `all` suite；任一步失败均返回非零。Phase 08 前若该合同尚未完整实现，入口必须明确返回 `NOT_IMPLEMENTED`，不能形成提前 PASS。

验证命令必须能从仓库根目录运行，并能正确处理包含空格或非 ASCII 字符的绝对仓库路径。实现时优先基于脚本自身位置解析仓库根，避免依赖调用者当前目录。

## 8. 四状态与程序状态

业务状态采用以下确定性优先级：

1. `UNTESTABLE`：harness、权威 Shape、manifest 和必需依赖预检均成功后，SUT 输入无法解析/加载，或 test-case manifest 明确声明并可控复现的 validator timeout、crash、验证服务/基础设施故障，使该提交无法形成可信判断。
2. `FAIL`：验证执行成功且 report graph 中至少存在一个 `sh:Violation`。同时出现 Warning 时仍为 FAIL。
3. `INAPPLICABLE`：验证执行成功、没有 Violation，并出现契约允许映射为不适用的 Warning；当前 D 组契约要求将 `ex:DatasetClosedShape` 的额外字段 Warning 映射到此状态。
4. `PASS`：输入和 Shape 成功解析，预期目标确实被评估，且没有 Violation 或 Warning。

业务状态与验证程序状态分开：

- `SUCCESS`：harness 完整执行并且实际业务状态与 test-case manifest 的预期完全匹配。
- `ERROR`：测试未发现、测试被跳过、预期断言不匹配、权威 Shape/manifest/report 结构异常、核心依赖缺失、编排器或证据写入异常。此时 suite 返回非零，不能用业务 `UNTESTABLE` 掩盖 harness 故障。

预期为 FAIL 的 fixture 只有在 manifest 规定的 requirement ID、source shape、path、severity、constraint component、message/结果数量断言满足时才算 `SUCCESS`。SUT 输入解析错误属于 `UNTESTABLE`，不能替代预期 FAIL；权威 Shape/manifest/report 解析错误属于程序 `ERROR`。发现 0 个必需测试必须返回非零。

## 9. Manifest 与 oracle 原则

统一数据源使用以下固定路径：

- `C_Semantic_Treehouse/manifests/release-manifest.json`：列出 v0.1–v0.4 的版本、artifact、hash、模型关系和适用验证。
- `C_Semantic_Treehouse/manifests/baseline-test-cases.json`：列出 v0.1–v0.3 的无回归 oracle。
- `C_Semantic_Treehouse/manifests/v0.4-requirements.json`：登记 D 组规则、Shape/path/severity/message 和 planned fixtures。
- `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`：列出 fixture、格式、预期四状态、覆盖的 requirement IDs 和 report 断言。
- `C_Semantic_Treehouse/manifests/validation-suites.json`：版本化登记七个公开 suite、实现状态、owner Phase、确定性有序组成和 `all` 的展开结果。
- `C_Semantic_Treehouse/manifests/deliverables.json`：由 Phase 09 形成的最终机器可读交付清单，登记路径、角色、SHA-256、许可证/来源和对应证据。
- `C_Semantic_Treehouse/manifests/schemas/*.schema.json`：分别约束上述 manifests，包括 `validation-suites.schema.json` 和 `deliverables.schema.json`。
- `docs/v0.4/requirements-traceability.md`：提供与机器可读 requirements manifest 一致的人类可读追踪表。

验证器读取 manifest，禁止分别硬编码 `v0.3` 或 `v0.4`。实际结果不能自动改写 expected oracle。修改 fixture、Shape、manifest 预期或要求追踪必须分别审查；非预期验证失败后需要此类修改时必须先按 `human-intervention-policy.md` 取得人工确认，禁止为了让测试通过同步弱化约束和预期。

七个公开 suite 名称固定为 `frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all`。任何组成变化都必须更新 `validation-suites.json` 的 contract version 和 hash；Phase 07 验收后冻结最终 `all` 组成，Phase 08–09 只读消费，并把平台、clean-room、发布检查作为独立门槛执行。

`scripts/validate.py` 必须先校验再确定性展开 suite registry，通过受控 Python module/entrypoint 调用内部 checks；禁止从 manifest 执行任意 shell 字符串。未知入口、空组成、重复项、循环依赖或声明与实际实现不一致均返回非零。

每份 manifest 都必须同时通过 JSON Schema 和跨记录语义校验。语义校验至少检查 ID 唯一性、仓库相对路径、引用完整性、hash 绑定、枚举组合和无循环依赖；不能仅依赖 JSON Schema 的 `uniqueItems` 判断对象内部某个 ID 是否重复。每类 checker 必须有重复 ID、断链引用或 hash 篡改 negative control，证明失败时返回非零。

## 10. 状态与证据合同

**两份文档分工，互不重叠：**

- `docs/v0.4/STATUS.md`：**只保存已完成事项的历史记录**，追加写入，不改写既有内容。Phase 00 创建该文件；此后每个 Phase **完成**时才在文件末尾追加一个新小节，至少包含：进入门槛、文件变更、命令及退出码、验收矩阵、证据路径、剩余风险、下一阶段进入条件。`human-intervention-policy.md` 第 3.5 节的恢复记录同样以追加小节的形式写入这里。历史小节按只读处理，需要修订时新增小节说明修订依据，不得直接改写。
- `docs/v0.4/CHECKPOINT.md`：**只保存当前尚未完成的那一次中断/断点**，随时可被覆盖重写，不是历史记录。当前 Phase 因为非预期失败、需要人工决定、或者单次会话/上下文额度不足以跑完整个 Phase 而必须中途结束时，必须先把可恢复所需的信息写入这个文件再停止；Phase 顺利做完并把小节写入 `STATUS.md` 后，必须把这个文件清空回占位符状态。任何时候 `CHECKPOINT.md` 非空闲，都说明有一个 Phase 处于中断状态，新会话必须先处理它，不能跳过去执行别的 Phase。

空闲状态下，`CHECKPOINT.md` 的完整内容固定为：

```markdown
# 当前中断点

无。当前没有 Phase 处于中途中断状态。
```

非空闲时，替换成本次中断的实际内容，至少包含：所属 Phase、中断类型（单纯跑不完 / 失败 / 需要人工决定 / 状态不明）、已完成的子步骤和证据、下一步具体要做什么、如果是失败或状态不明还需包含 `human-intervention-policy.md` 第 3.5 节要求的根因、涉及的保护文件、复现命令与退出码。用户的答复、决定或手动修改也追加记录在这里，直到该 Phase 做完为止。

不再为每个 Phase 单独建 summary 文件，也不维护并行的机器可读状态副本（如 `execution-status.json`）。

临时输出统一写入 `build/`，审核后选定的发布证据才进入 `C_Semantic_Treehouse/evidence/releases/v0.4/`。机器可读 JSON（release manifest、test-case manifest 等）是验证结果真源，Markdown 报告由 JSON 生成或手动同步。

每次正式验证至少记录：

- suite 和 schema version
- Git commit（如存在）与 dirty flag
- OS、architecture、Python、pip 和关键 validator 版本
- lock 文件 SHA-256
- 输入、Shape 和 manifest SHA-256
- `validation-suites.json` 的 contract version 与 SHA-256
- 实际执行的 runner、validator、helper、生成器和 workflow 源文件仓库相对路径及 SHA-256
- 规范化命令参数，不写个人绝对路径
- 退出码
- discovered、executed、passed、failed、skipped 数量
- 每个 case 的 expected/actual business status
- report graph 断言结果

确定性结果与机器环境清单分开保存。实时 timestamp、绝对解释器路径、临时目录和随机顺序不能进入需要跨机器比较的核心结果。报告必须能检测输入 hash 改变造成的陈旧状态。

阶段总结（`STATUS.md` 中对应小节）不得写入个人绝对路径或未经验证的成功声明。

## 11. 每个 Phase 的固定执行协议

1. 先检查 `docs/v0.4/CHECKPOINT.md`。非空闲时说明存在一个未完成的中断点：先完整读取它，按其中记录的情况和用户此后给出的答复/修改恢复并接着做完那个 Phase，不得跳过去执行别的 Phase。空闲时才按正常流程开始新 Phase。
2. 完整读取 Master、`human-intervention-policy.md`、当前 Phase prompt、相关权威输入和 `STATUS.md` 中上一阶段记录。
3. 运行 `git status --short --branch` 和冻结文件校验。
4. 检查当前 Phase 的进入门槛。客观前置条件不满足时记录 `BLOCKED` 并停止；需要人工选择、纠正或授权时记录 `AWAITING_HUMAN_DECISION` 并停止——两种情况都要把当前进度写入 `CHECKPOINT.md`。
5. 向用户说明计划、预期改动和可写范围。
6. 实施当前 Phase 的最小完整变更，不扩展下一 Phase 的概念范围。Phase 内容较多、一次会话大概率跑不完时，在完成每个有意义的子步骤后更新 `CHECKPOINT.md`（已完成什么、下一步是什么、如何在新会话中原样接着做），不要等到整个 Phase 失败才第一次写。
7. 运行所有必需命令，保存实际退出码和机器可读证据。出现非预期失败时，按 `human-intervention-policy.md` 停止 tracked 写入、执行一次受控复现，把根因证据和可选方案写入 `CHECKPOINT.md`，然后向用户报告并停止。
8. 同时审查 unstaged 与 staged 改动：运行 `git diff --check`、`git diff --stat`、`git diff --name-status`、`git diff --cached --check`、`git diff --cached --stat`、`git diff --cached --name-status`、`git status --short`，并阅读实际 diff，确认修改未越界。
9. 再次运行冻结文件校验。
10. 在 `STATUS.md` 追加本 Phase 的记录小节，并把 `CHECKPOINT.md` 清空回占位符状态。
11. 只有全部必需验收项通过时标记 `COMPLETE`，随后停止并等待下一 Phase 指令。

若某次会话在 Phase 尚未做完、也没有遇到明确失败的情况下就要结束（比如上下文/时间不够），同样必须先把当前进度和下一步指引写入 `CHECKPOINT.md` 再停止，不能让 Phase 处于"半途而废又没留痕迹"的状态。

## 12. Git、网络与安全规则

- 不删除或覆盖用户文件、冻结输入、历史证据或其他人的未提交修改。
- 不使用 `git reset --hard`、`git checkout --` 等破坏性恢复命令。
- 未经明确授权，不 commit、不 push、不创建/修改 remote、不打 tag、不改写历史、不创建 GitHub release。
- 外部下载必须属于当前 Phase，固定来源和版本，并记录 checksum/commit/digest。
- 首次 `.venv`/依赖安装、系统软件安装、镜像 pull/build、第三方 workload 和新增外部网络访问必须先按 `human-intervention-policy.md` 取得人工确认。
- 可能长时间阻塞的本地、网络、Docker 和 CI 命令应设置合理超时；超时后保存已有证据并向用户报告，不得无界等待或无限重试。
- 不提交 `.env`、token、证书、私钥、缓存、虚拟环境或未清理的外部日志。
- 生成或采集的日志先扫描 secrets、个人绝对路径和敏感环境值，再进入发布证据。
- clean 命令只能删除明确列入 allowlist 的 `build/` 或缓存目标，执行前解析并核对绝对路径。

## 13. 禁止形成虚假 PASS

- 工具缺失或命令未运行时不得标记 COMPLETE。
- 不得把 `if available`、`optional validator` 或浅层语法检查用于替代必需验证。
- 不得把空目标、零测试、零查询结果、跳过测试或过期报告视为通过。
- 不得通过删除负例、减少断言、降低 severity、放宽 Shape、修改 expected output 或隐藏错误来通过门槛。
- 不得伪造截图、CI URL、Treehouse 状态、命令输出或人工审批。
- 文件存在性检查必须同时检查非空、格式、引用、schema/hash 和 freshness（按适用范围）。
- Semantic Treehouse 失败可记录为 `DEFERRED` 或 `BLOCKED`，不得记录为 PASS；核心 suite 必须继续独立通过。
- Phase 09 的最终发布验证（GitHub Actions 运行结果、clean-room clone 结果）必须附可核查的真实证据（run URL、关键日志摘要、退出码），不得凭空声称通过；正常的 push → CI 跑绿 → 人工确认即可，不需要额外的 payload/completion 双 commit 或发布沿革归档系统。

## 14. 最终质量门槛

Phase 09 完成时必须有证据证明：

- 冻结输入完整且 v0.1–v0.3 无回归。
- v0.4 覆盖 D 组全部已登记规则。
- 四种业务状态均有自动化 fixture，并有 harness 自测/negative control。
- RDF、JSON-LD、SHACL、JSON Schema、OpenAPI、SPARQL、质量、governance、provenance、链接和 required-files 检查均 fail closed。
- 本机 Windows `.venv`、Linux、Docker 和实际 GitHub Actions 使用 lock 运行成功。
- clean clone 分别运行 `scripts/reproduce.ps1` 或 `scripts/reproduce.sh` 单命令复现，结束时无非预期 Git diff。
- A/B/D 组 handoff 与实际 v0.4 artifact 一致。
- 发布证据能够追溯到输入 hash、lock hash、commit 和验证结果。
- 许可证、第三方材料再分发、ZIP 隐私例外、提交身份和仓库可见性均有明确人工决定。
- README、final checklist 和 `STATUS.md` 没有超出证据的完成声明。
- `deliverables.json` 完整覆盖最终交付物且每个 hash、引用、角色和许可证信息通过 schema、语义检查和 required-files 检查。

严格执行当前 Phase。进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后停止；不得自动开始下一 Phase。
