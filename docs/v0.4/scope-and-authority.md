# v0.4 范围与权威矩阵

审计日期：2026-08-09
状态：Phase 00 冻结的工作边界

语义和流程发生冲突时，依次采用当前用户指令/适用安全规则、人工介入策略、D 组规范性 TTL、D 组解释说明、项目与场景输入、已批准的追踪/决定/manifests、v0 历史材料。来源字节、状态记录和发布证据各自还有独立的域内权威关系，详见下表。

## 1. 权威关系

| 路径或信息类别 | 角色 | 权威优先级 | 可直接修改 | 修订方法 | 完整性检查方法 |
|---|---|---|---|---|---|
| 当前用户指令、适用安全规则和仓库约束 | 规范性输入 | 全局 P0 | 不适用 | 由有权限的人显式修订 | 会话指令与仓库约束审阅 |
| `prompts/v0.4/human-intervention-policy.md`、Master 与当前 Phase prompt | 规范性输入 / 可编辑流程源 | 全局 P1 | 当前 Phase 禁止 | 独立流程设计变更；不得在执行中降低门槛 | Git diff、review 与 prompt 一致性审计 |
| `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl` | **规范性输入；v0.4 规范性可执行契约** | 语义 P2 | 否，冻结 | D 组修订时新增版本目录；C 组适配写入派生文件 | D 组 `SHA256SUMS`、supplemental map、frozen manifest、SHA-256 |
| `inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md` | **解释性输入** | 语义 P3 | 否，冻结 | D 组修订时新增版本目录；解释变化另行记录 | D 组 `SHA256SUMS`、supplemental map、frozen manifest、SHA-256 |
| `inputs/project/v0.4/806.md` | 规范性项目范围输入 | 语义 P4 | 否，冻结 | 新增版本化项目要求 | supplemental map、frozen manifest、SHA-256 |
| `inputs/original-plan/**` | 解释性场景输入 / 冻结历史 | 语义 P4；来源域高优先级 | 否，冻结 | 从新来源形成新版本或派生文件 | 11-file migration map、frozen manifest、SHA-256 |
| `docs/v0.4/requirements-traceability.md`、批准的兼容性决定与 v0.4 manifests | 可编辑源；批准后为派生执行合同 | 语义 P5 | 仅在所属 Phase | issue/decision review 后修改派生源；同步 schema、引用和 hash | JSON Schema、语义引用、hash、negative controls；当前尚未建立 |
| 两份 `inputs/source-archives/received/*.zip` | 冻结历史；来源字节真源 | 来源域 P0 | 否，冻结 | 新来源使用新文件名/版本目录 | source `SHA256SUMS`、frozen manifest、中央目录只读审计 |
| `docs/provenance/manifests/**` | 冻结历史 / 迁移证据 | 来源域 P1 | frozen manifest 永久只读；其他文件依适用流程 | 通过明确迁移策略与新增证据修订；Phase 00 不改写 | 格式、路径、hash、映射基数与 Git tracking 审计 |
| `C_Semantic_Treehouse/model/v0.1/**`–`v0.3/**` | 冻结历史 | 语义 P6 | 否，永久保护 | 新模型版本或勘误文档 | frozen manifest、Git tracking、`text: unset` |
| `prompts/v0/**`、`archive/**`、旧报告与旧工具入口 | 冻结历史 | 语义 P6 | 否，永久保护 | 新现行文档或派生文件 | 登记文件使用 frozen manifest；历史 migration map 只证明复制时一致；8 个 archive wrapper 的未绑定范围见 `P00-R15` |
| `C_Semantic_Treehouse/model/v0.4/**`、fixtures、manifests、现行 governance/mapping/handoff/quality 源 | 可编辑源 | 派生 P1 | 仅在所属后续 Phase | 从权威输入派生，经 review、traceability 与测试修订 | suite、schema、语义引用、hash 与 negative controls；当前尚未实现 |
| 根 `scripts/**`、环境锁、Docker/Make/CI 入口 | 可编辑源 | 执行 P1 | Phase 00 禁止；仅在所属后续 Phase | 固定工具版本后按环境/验证 Phase 修订 | doctor、hash lock、统一 suite、跨平台与 clean-room 检查 |
| 根 README、`docs/environment.md`、`迁移清单.md` 与现行说明 | 解释性输入 / 可编辑源 | 文档 P2 | 仅在允许的 Phase | 只同步已证明事实；历史记录保留原样 | 当前命令、STATUS、diff 与链接审计 |
| `docs/v0.4/STATUS.md` 已完成小节 | 冻结历史 / 状态真源 | 状态域 P0 | 只追加，不回写 | 受影响 Phase 恢复后追加修订小节 | Phase 验收矩阵、命令退出码、证据路径 |
| `docs/v0.4/CHECKPOINT.md` | 可编辑源；当前中断状态 | 状态域 P1 | 可由当前 Phase 覆盖 | 中断时记录；Phase 完成后恢复固定空闲占位符 | 固定结构与恢复流程人工审阅 |
| `build/**`、`.venv/**`、本机缓存 | 临时生成物 | 无发布权威 | 可由所属流程生成；清理需 allowlist 与授权 | 从当前受控源重新生成 | Git ignore、路径/secret 扫描、freshness；旧回档残留明确隔离 |
| `C_Semantic_Treehouse/evidence/releases/v0.4/**` | 发布证据 | 发布域 P0（审核后） | 仅在所属发布 Phase | 从已通过的当前机器结果审核晋升 | commit、lock、输入/runner/manifest hash、freshness、CI/clean clone |

## 2. D 组输入冲突处理

D 组 TTL 是 v0.4 的规范性可执行契约；D 组说明提供解释背景。发现二者不一致时执行以下流程：

1. 保留两份 received 原件及其 SHA-256。
2. 创建明确的 issue/decision 记录，列出冲突、影响、C/D 组 reviewer 与批准结论。
3. 在新的派生文件中落实批准决定，并建立 source hash 和 requirement ID 追踪。
4. 更新适用 manifests、fixtures 和测试；保持收到的原件不变。

`dct:conformsTo` 未进入 D 组 `DatasetClosedShape` allowlist，属于已登记的兼容性决定 `P00-R11`，留给 Phase 03 的 C/D 组 review。

## 3. Phase 00 可写边界

本阶段仅允许创建或修改：

- `README.md`
- `迁移清单.md`
- `docs/environment.md`
- `docs/v0.4/current-state.md`
- `docs/v0.4/scope-and-authority.md`
- `docs/v0.4/risk-register.md`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`
- `build/phase-00/**`

本阶段保护 Master 永久保护范围，并额外保护 `prompts/v0.4/**`、`.github/**`、`scripts/**`、`tools/**`、`C_Semantic_Treehouse/**`、根 Docker/Compose/Make、所有 requirements/lock/环境配置和生成报告。`.gitignore` 与 `.gitattributes` 保持不变。

本次机器证据使用 `build/phase-00/reconciliation-2026-08-09/`，从而保留并隔离用户确认的已回档 Phase 00/01 旧残留。

## 4. Phase 00 完成后的只读边界

- 本文件记录的 Phase 00 范围是后续 Phase 的进入依据；需要改变时按人工介入策略形成明确决定。
- `risk-register.md` 是带日期的 baseline snapshot，Phase 00 COMPLETE 后保持只读。
- `STATUS.md` 的 Phase 00 小节保持只读；后续只在文件末尾追加。
- `CHECKPOINT.md` 继续只保存当前未完成中断点，空闲时使用固定占位符。
- `build/**` 仍是临时本机证据区；只有经过审核并与当前 commit、lock 和 manifests 对齐的文件才可晋升为发布证据。
