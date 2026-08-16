# Phase 00 baseline risk snapshot

审计日期：2026-08-09
快照边界：Phase 00 截止时的迁移、环境、语义、流程和发布风险

本文件是带日期的 **Phase 00 baseline risk snapshot**。Phase 00 标记 COMPLETE 后保持只读。后续处置、状态变化与人工决定追加到 `docs/v0.4/STATUS.md` 的对应 Phase 小节；Phase 09 汇总时引用原 risk ID。

表中的“阻塞 GitHub 发布”只表示发布前必须关闭或取得明确批准，不表示该风险阻塞 Phase 00 的迁移基线复核。相关角色缺失且进入实际决策点时，所属 Phase 按人工介入策略标记 `AWAITING_HUMAN_DECISION`。

| ID | 事实依据 | 影响 | 责任角色 | 计划处理 Phase | 阻塞 GitHub 发布 | Phase 00 截止状态 |
|---|---|---|---|---|---|---|
| P00-R01 | 当前 remote 数量为 0；最终 GitHub 仓库名称、可见性和组织/账户归属没有批准记录 | 无法确定发布目标、访问边界与所有权 | Repository Maintainer、Release Approver | 09 | 是 | OPEN |
| P00-R02 | tracked tree 中没有 LICENSE、LICENCE、COPYING 或 NOTICE；学校、第三方、来源 ZIP 与 D 组材料的再分发授权没有当前批准证据 | 公开分发可能缺少授权或准确归属 | Project Lead、Licensing Reviewer、材料权利人 | 09 前 | 是 | OPEN |
| P00-R03 | provenance 登记核心 ZIP 内 6 个含旧电脑绝对路径的历史条目；完整 ZIP 会让下载者取得这些字节 | 可追溯价值与历史路径披露需要发布批准 | Privacy Reviewer、Release Approver | 09 | 是 | DECISION_REQUIRED |
| P00-R04 | 当前 7 个提交及初始提交均携带 author email 元数据；初始提交和完整历史均未全部使用 noreply 域。证据只保存布尔分类，不复写原地址 | 推送会公开初始提交及后续历史中的身份元数据 | Commit Author、Release Approver | 09 | 是 | DECISION_REQUIRED |
| P00-R05 | `git remote -v` 无输出，当前没有远程 CI、run URL 或 release 证据 | 无法形成真实 GitHub/CI 发布链 | Repository Maintainer | 09 | 是 | OPEN |
| P00-R06 | 正式 CPython 3.12 完整补丁号尚未选择或固定；本机存在 ignored `.venv/`，`pyvenv.cfg` 写明 3.12.10；当前没有正式 `requirements.in`、hash lock、bootstrap、doctor 或 STATUS 证明 | 本地环境来源和可复现性未被接受；直接继承会污染 Phase 01 结论 | Environment Maintainer、Phase Executor | 01 | 是 | OPEN；现存环境未调用 |
| P00-R07 | 用户确认 `.venv/`、旧 `build/phase-00/` 与 2070-file `build/phase-01/` 来自一次已 Git 回档的 agent 尝试；另有 13 个 ignored `.pyc` 和一个空的本地 manifest schema 目录，时间与该回档过程相符；旧证据声称的 tracked 产物当前不存在 | 孤立 COMPLETE/PASS 草稿、cache 或空骨架可能误导状态或影响 bootstrap | Environment Maintainer、Phase Executor | 01 隔离重建；09 clean-room 复核 | 是 | OPEN；本次证据已隔离且所有旧残留保留 |
| P00-R08 | 旧脚本直接列出 v0.1–v0.3 文件和固定脚本集合，没有统一 release/suite manifest | 新版本容易漏检，验证组成缺少单一真源 | Validation Maintainer | 02、05 | 是 | OPEN |
| P00-R09 | 旧 SHACL 验证器只比较 `conforms`，没有断言实际目标命中，也没有对 report graph 的 source shape/path/severity/component/message 做 oracle 检查 | 空目标或错误约束命中可能形成虚假 PASS | Validation Maintainer、D Contract Reviewer | 05 | 是 | OPEN |
| P00-R10 | 旧 OpenAPI 验证器在缺少 `openapi-spec-validator` 时把结构解析记为 PASS | 缺失必需 validator 时可能 fail-open | Validation Maintainer | 02、05 | 是 | OPEN |
| P00-R11 | D 组 `DatasetClosedShape` allowlist 没有 `dct:conformsTo`；历史 v0.2/v0.3 metadata 使用该属性 | v0.4 conformance/version 声明可能被映射为 INAPPLICABLE；需兼容性决定 | C Semantic Reviewer、D Contract Reviewer | 03 | 是 | DECISION_REQUIRED |
| P00-R12 | Semantic Treehouse、Mermaid、ITB/SEMIC 和其他外部 validator 需要额外版本、网络或服务；Master 将它们定义为可选证据轨 | 外部轨不可用会限制附加证据，但不影响核心独立验证合同 | Evidence Maintainer | 08 | 否 | OPEN；仅可在 Phase 08 标记 DEFERRED |
| P00-R13 | 单个 Phase 内容较多，一次会话可能无法完整执行 | 无中断记录时会造成状态不明或重复工作 | Phase Executor | 全阶段 | 否 | CONTROLLED；使用 `CHECKPOINT.md` 记录中断点 |
| P00-R14 | C 组语义 reviewer、D 组契约 reviewer、领域 reviewer 和 Release Approver 的实际可用性尚未确认 | 兼容性、oracle、许可和发布决定可能无人批准 | Project Lead、Review Chair | 03、09；按实际需要 | 是 | OPEN；角色缺失时相关 Phase 进入 AWAITING_HUMAN_DECISION |
| P00-R15 | `archive/**` 有 61 个 tracked 文件，frozen manifest 覆盖 53 个；8 个迁移说明 wrapper 受永久只读和 `-text` 保护，却没有 frozen record 或 migration-map record | “104 项通过”不能扩张为“全部永久保护文件均 hash-bound”；发布说明可能夸大完整性 | Provenance Maintainer、Release Approver | 05 明确证据边界；09 发布复核 | 是 | OPEN；Phase 00 仅登记，不改 provenance/manifest |
| P00-R16 | 两份受保护说明存在现行描述漂移：`docs/v0.4/README.md` 仍称文档区“仅建立目录边界”；`docs/provenance/source-archives.md` 仍称两份 ZIP “计划与仓库一同纳入 Git”，而 Git 与 manifest 已证明它们自初始提交起 tracked。Phase 00 可写 allowlist 不包含这两份文件 | 导航和 provenance 说明可能让读者误判当前完成度或 ZIP tracking 状态 | Documentation Maintainer、Provenance Maintainer | 05 澄清 provenance；07 同步导航 | 是 | OPEN；Phase 00 保持保护边界，只登记风险 |

## 截止结论

上述风险均有事实依据、责任角色、计划处理 Phase 和发布阻塞性。Phase 00 的迁移复核可以在准确保留这些开放项的前提下完成；GitHub 发布仍需关闭所有标记“是”的风险，或取得符合人工介入策略的明确批准与证据。
