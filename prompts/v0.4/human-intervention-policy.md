# DSSC C 组 v0.4 人工介入与状态恢复指南

本文件适用于 `prompts/v0.4/` 下的全部 Phase。它回答两个问题：**什么时候要停下来找人确认**，以及**仓库状态不明、验证从通过变成失败、或者一次会话/上下文额度跑不完整个 Phase 时该怎么记录和恢复**。目标是防止 AI agent 单方面做出不可逆动作、悄悄放宽验收标准、在没有真实证据的情况下宣称完成，或者中途中断却不留下可恢复的痕迹——但不要求为此维护锁文件、hash 链或不可变状态记录；两份文档就够：

- `docs/v0.4/STATUS.md`：只追加已完成 Phase 的历史记录，不改写。
- `docs/v0.4/CHECKPOINT.md`：只保存当前这一次尚未完成的中断点，空闲时是占位符，随时可被覆盖重写。任何时候它非空闲，都说明有一个 Phase 中途停下了，新会话必须先处理它。

## 1. 必须停下来找人确认的情况

出现以下任一情况时，停止对 tracked 文件的写入，把当前进度、情况、证据和你建议的下一步写入 `docs/v0.4/CHECKPOINT.md`（见第 3 节的字段要求），再向用户说明并等待明确答复后继续。**沉默、"继续"、"看着办"不构成批准**——用户必须针对具体动作给出可执行的答复。

**动作类（做之前问）：**
- 首次安装或更新系统软件、系统级配置。
- 首次创建/重建 `.venv` 并从 lock 安装依赖；升级或更换依赖版本。
- 拉取或构建新的 Docker 镜像；运行未运行过的第三方容器 workload。
- 任何超出当前 Phase 已声明可写范围的新增下载、网络访问或外部写入。
- `git commit`、`push`、创建/修改 remote、打 tag、创建 GitHub release，或任何其他会被他人看到的 Git 写操作。
- 删除、覆盖或清理冻结输入、历史证据，或看起来不属于当前任务的既有未提交修改。
- 破坏性恢复命令（`git reset --hard`、`git checkout --`、`git clean -f` 等）。

**结果类（发现之后问）：**
- 第一次出现非预期失败（测试失败、validator 崩溃、hash 不匹配、CI 与本机结果不一致等）：只允许做**一次**不改变 tracked 文件或外部状态的受控复现去确认问题是否稳定重现，然后停下来报告根因证据和可选方案，不要反复重试或自行“修到能过”。第二次失败或发现新根因时重新停下来。
- 需要修改 fixture、Shape、manifest 的 expected 值或需求追踪表才能让测试通过：这类改动必须先说明理由、经用户确认后才能改，不能为了通过测试静默弱化约束。
- 权威输入（D 组 TTL 及说明）与已有理解不一致，或与 Phase 需求文档冲突。

## 2. 证据要求

任何 “已完成” 或 `COMPLETE` 的声明都必须附带真实证据：实际跑过的命令、退出码、结果文件路径/hash。不能用“工具不可用时跳过”“看起来应该没问题”“浅层语法检查”替代必需验证；发现 0 个测试、测试被跳过、结果过期都不算通过。`master-prompt.md` 第 13 节列出了更完整的“禁止形成虚假 PASS”清单，同样适用于这里。

每个 Phase 收尾前，运行 `git status --short`、`git diff --stat`、`git diff --name-status`（以及对应的 `--cached` 版本）并阅读实际 diff，确认改动没有超出这次声明的可写范围、没有触碰保护路径。确认后：若本 Phase 到此已全部做完，把结果记入 `docs/v0.4/STATUS.md` 对应小节并把 `docs/v0.4/CHECKPOINT.md` 清空回占位符；若还没做完，把当前进度更新进 `CHECKPOINT.md`。不需要额外生成 hash 链或不可变记录文件。

## 3. 中断记录与状态恢复

`docs/v0.4/CHECKPOINT.md` 对应两类不同的中断，处理方式不同：

- **情况 A：单纯跑不完**——没有出现异常，只是这次会话的时间/上下文额度不足以做完整个 Phase。直接把"已经做到哪一步、有哪些命令跑过且结果如何、下一步具体做什么"写进 `CHECKPOINT.md` 即可，不需要走 3.3 的诊断步骤；新会话读取后从记录的下一步继续做完这个 Phase。
- **情况 B：状态不明或出了问题**——上下文丢失、当前 Phase 状态不明、验证从已知通过变为失败、工作树出现意外修改、环境或 CI 与本机结果不一致（即原 Emergency Recovery 覆盖的场景）。按 3.1–3.5 的完整流程处理，目标是恢复到可解释、可验证的状态，不要顺便扩大范围或“顺手”添加新功能。

### 3.1 先读

1. `docs/v0.4/CHECKPOINT.md`——若非空闲，这就是要恢复的中断点，优先按其记录的情况处理。
2. `prompts/v0.4/master-prompt.md`
3. `docs/v0.4/STATUS.md`（若存在）——重点看最近几个小节
4. 当前失败涉及的 Phase prompt

Master 中的冻结、Git、安全、四状态和证据规则继续生效。

### 3.2 恢复期间额外保护

除 Master 第 3 节的永久保护范围外，在找到根因前不得修改：

- D 组收到的 TTL 和说明
- v0.4 Shape、fixtures、test-case manifest 和 expected oracle
- release manifest、validation suite registry
- 已审核的发布证据
- `docs/v0.4/STATUS.md` 中已有的历史小节（只能追加新小节，不能改写）

只有证据明确显示这些文件本身存在缺陷，并单独向用户说明后，才能将其列入修复范围。不得通过弱化 Shape、删除 fixture、改变预期状态或减少断言来消除失败。

### 3.3 恢复步骤

1. 运行只读状态检查：

   ```text
   git status --short --branch
   git diff --check
   git diff --stat
   git diff --name-status
   git diff --cached --check
   git diff --cached --stat
   git diff --cached --name-status
   # Phase 01 已完成时，使用仓库 .venv 运行 scripts/verify_frozen_files.py；
   # Phase 01 尚未完成时，使用 Phase 00 固定的 Get-FileHash/sha256sum 合同。
   ```

2. 识别：最后一个有完整证据的 `COMPLETE` Phase；当前 Phase 和最近一次实际成功命令；失败是否可在当前工作树稳定复现；既有用户修改与本轮修改的边界。

3. 将根因归为一类：environment/lock、parser/serialization、model/Shape、fixture/oracle、validator/harness、report/freshness、cross-platform/CI、optional external evidence、repository state/provenance。

4. Phase 01 已完成且 `.venv` 通过 doctor 后，使用统一 Python 入口复现（包装脚本损坏时直接调用 `.venv\Scripts\python.exe scripts\validate.py --suite <suite>` 或 Linux 等价命令）。

5. 找到能解释失败的最小根因和最小修复集合。修复前向用户说明：根因证据、拟修改文件、涉及的保护文件、回归范围，等待确认。

6. 只实施恢复所需的修改。保留失败日志和原始机器可读结果，不覆盖证据来隐藏失败。

7. 从最早受影响 Phase 开始，按顺序重新运行必需验收直到当前 Phase。

8. 再次运行冻结校验、diff 审计和 Git 状态检查。

### 3.4 状态处理

- 环境或必需依赖无法恢复：当前 Phase 标记 `BLOCKED`。
- Semantic Treehouse 等明确的非阻塞外部轨失败：记录证据，可标记 `DEFERRED`；核心验证仍须通过。
- 实际结果与 oracle 冲突且尚未确认哪一方错误：标记 `AWAITING_HUMAN_DECISION`，保留双方证据，禁止自行改变预期。
- 工作树包含来源不明或重叠修改：停止写入并请求用户确认。

### 3.5 必须产出

在 `docs/v0.4/CHECKPOINT.md` 写入/更新记录，包含：触发原因和首次观察到的失败、最后已知良好的 Phase/commit/lock hash、根因分类与直接证据、修改文件及理由、保护文件确认结果、复现命令与退出码、当前状态和剩余人工任务、明确的下一步。用户给出决定或自己动手做了修改后，把这些也追加进同一份记录，再继续恢复。

问题解决、且从最早受影响 Phase 开始的回归重新验收通过后，把这份记录浓缩进 `docs/v0.4/STATUS.md` 对应 Phase 的完成小节，并把 `CHECKPOINT.md` 清空回占位符状态。恢复完成不自动授权进入下一 Phase；等待用户明确指示后再继续。

## 4. 禁止事项（汇总）

- 不使用破坏性 Git 命令，不覆盖用户改动。
- 不删除失败证据、历史报告或未知文件。
- 不重新生成 expected oracle 来迎合实际输出。
- 不把解析错误、超时、缺依赖或零测试写成 expected FAIL。
- 不扩大概念模型或发布范围。
- 未经用户明确授权不执行 commit、push、tag、remote 或 GitHub release 操作。

本文件的修改本身应作为独立、显式的流程设计变更记录在 `docs/v0.4/STATUS.md` 或提交说明中，不得为了规避已发现的问题而放宽这里的标准。
