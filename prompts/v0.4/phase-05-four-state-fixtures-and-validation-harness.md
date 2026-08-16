# Phase 05 Prompt — 四状态 Fixtures 与 Fail-Closed 验证 Harness

只实施 Phase 05。开始前完整读取 `prompts/v0.4/master-prompt.md`、`prompts/v0.4/human-intervention-policy.md` 和本文件；进入 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。

## 1. 目标

建立 v0.4 的可机读 test-case manifest、覆盖 D 组全部规范性规则的 fixtures，以及统一、fail-closed 的四状态验证 harness。验证器必须解析 SHACL report graph，稳定输出业务状态 `PASS`、`FAIL`、`INAPPLICABLE`、`UNTESTABLE`，并以程序状态 `SUCCESS` 或 `ERROR` 表达测试执行是否可信、实际结果是否符合 oracle。

本阶段完成后，`.\scripts\validate.ps1 -Suite v0.4` 必须成为 Windows host 的 v0.4 fixture 验收入口，并调用唯一 Python 编排核心；`all` 必须首次标记 `IMPLEMENTED`，确定性展开六个非 `all` 的公开 suite。

## 2. 非目标

- 不新增或修改 D 组规范性要求。
- 不修改 Phase 04 已批准的 v0.4 模型语义、namespace 或兼容性决定。
- 不实施 SPARQL、质量指标、governance、文档、CI 或 Treehouse 工作。
- 不把 v0.3 Energy Reading Record 无意义复制为 v0.4；其适用版本只按 release manifest 处理。
- 不推广临时报告为发布证据；本阶段输出保存在 `build/`。

## 3. 权威输入

按 Master 的权威顺序读取并核验：

1. `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`
2. `inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md`
3. `docs/v0.4/requirements-traceability.md` 及 Phase 03 已批准的兼容性/四状态决定
4. `C_Semantic_Treehouse/manifests/release-manifest.json`
5. `C_Semantic_Treehouse/manifests/v0.4-requirements.json`
6. `C_Semantic_Treehouse/manifests/schemas/*.schema.json`
7. `C_Semantic_Treehouse/manifests/validation-suites.json`
8. `docs/v0.4/STATUS.md` 中 Phase 04 小节
9. `C_Semantic_Treehouse/validation/expected-results.md` 和 v0 验证脚本，仅作历史行为与风险参考

D 组 TTL 当前登记 SHA-256 应为 `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`。任何不一致均阻塞本阶段。

## 4. 进入门槛

进入前必须同时满足：

- Phase 00–04 在 `docs/v0.4/STATUS.md` 中均记录为 `COMPLETE`。
- Phase 04 小节存在、非空并列明 release manifest、v0.4 artifacts、哈希和兼容性决定。
- 下列命令实际退出 0：

```text
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
```

- `release-manifest.json` 和 `v0.4-requirements.json` 通过各自 schema，引用路径存在且 hash 匹配。
- Phase 01–04 的 manifests 均通过各自 JSON Schema 和跨记录语义校验；`validation-suites.json` 的 `contract_version`/hash 与 `STATUS.md` 中 Phase 04 小节一致。
- `dct:conformsTo` 与 Closed Shape、D 原始 Shape 与 C 派生 Shape、v0.3 record 复用方式均已有明确 decision ID。
- `docs/v0.4/CHECKPOINT.md` 为空闲。
- 当前工作树中的既有修改已识别归属，本阶段可安全避开他人或用户改动。

任一进入门槛失败时，先完成安全诊断，把当前进度写入 `CHECKPOINT.md`。需要用户确认重叠修改归属或其他决定时标记 `AWAITING_HUMAN_DECISION`；确认没有安全选项时标记 `BLOCKED`，不实施文件变更。

## 5. 可写路径与保护路径

### 可写路径

- `C_Semantic_Treehouse/fixtures/v0.4/**`
- `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
- `C_Semantic_Treehouse/manifests/schemas/v0.4-test-cases.schema.json`
- `C_Semantic_Treehouse/manifests/validation-suites.json`，仅更新 `v0.4`、组合 `all` 并 bump `contract_version`
- `C_Semantic_Treehouse/scripts/**`，仅限四状态分类、SHACL report 解析和当前 harness 重构
- `scripts/` 下由 Phase 01 受控 entrypoint catalog 发现的 v0.4 checker 模块；不含通用 dispatcher、doctor 或平台包装
- `C_Semantic_Treehouse/validation/expected-results.md`
- `build/phase-05/**`
- `build/validation/v0.4/**`
- `docs/v0.4/STATUS.md`
- `docs/v0.4/CHECKPOINT.md`

### 本阶段额外保护路径

- Master 永久保护范围全部只读。
- `C_Semantic_Treehouse/model/v0.4/**` 只读；发现模型缺陷时按 `human-intervention-policy.md` 记录问题并停下来找人确认，不在本 Phase 直接修改。
- `C_Semantic_Treehouse/manifests/release-manifest.json` 与 `v0.4-requirements.json` 只读；发现错误时同样停下来找人确认，并说明应回到哪个更早 Phase。
- `C_Semantic_Treehouse/manifests/schemas/validation-suites.schema.json` 只读。
- `scripts/validate.py`、`scripts/doctor.py` 和平台包装只读；发现 dispatcher 缺陷时按 `human-intervention-policy.md` 记录问题并停下来找人确认。
- Phase 06–09 的治理、报告、CI 和发布证据路径不写入。

## 6. 任务

### 6.1 定义 test-case manifest 和 schema

创建 `C_Semantic_Treehouse/manifests/v0.4-test-cases.json` 及 schema。每个 case 至少包含：

- 唯一、稳定的 `case_id`
- fixture 仓库相对路径、输入格式和预期 64 位十六进制 SHA-256
- release/profile ID
- Shape artifact ID、相对路径和预期 SHA-256
- 预期业务状态
- 覆盖的 requirement IDs
- manifest 顶层或每 case 引用的固定 pySHACL engine config：准确版本、`inference=none`、D SPARQL 所需 `advanced`、`abort_on_first=false`、Warning/Info 策略，以及 Meta-SHACL/Shape 结构证据引用；未批准的逐 case override 禁止

schema 必须使用 `if`/`then` 或 `oneOf` 按预期业务状态表达互斥 oracle：

- `PASS` 要求预期 target activation 数量大于 0、预期 `sh:ValidationResult` 数量为 0；禁止填写 `sourceShape`、`sourceConstraintComponent`、`resultPath`、severity、message 等结果专属断言。
- `FAIL` 和 `INAPPLICABLE` 要求预期 `sourceShape`、`sourceConstraintComponent`、severity、稳定 message 策略及精确结果数量或上下界；在规则存在 path 时要求 `resultPath`，并允许明确的 focus node/value 断言。`FAIL` 的 severity/结果组合必须能证明至少一个 Violation；`INAPPLICABLE` 只能声明已批准 Closed Shape Warning 映射。
- `UNTESTABLE` 要求预期 `failure_stage` 和受控 `reason_code`，并禁止 sourceShape/component/path/severity/message/result-count/focus/value 等 SHACL report 断言，防止未完成验证时伪造 report oracle。

schema 还必须拒绝未知业务状态、空 requirements、仓库外路径、绝对路径、缺失 fixture SHA-256、缺失 oracle、跨状态字段和互相矛盾的 result 数量。

JSON Schema 之外必须实现 test-case 跨记录语义校验器，至少检查 duplicate case/fixture/artifact assertion IDs、fixture path/hash 一致性、case 到 release/profile/Shape/requirement/decision 的 cross-reference、requirements 的反向覆盖、同一 fixture 路径多 hash 冲突和 failure-stage/reason-code 组合。使用临时 manifest 证明 duplicate IDs、悬空 requirement/artifact 引用、fixture hash 漂移、PASS 伪填 report 字段、FAIL/INAPPLICABLE 缺失结果 oracle、UNTESTABLE 伪填 report 断言均非零失败。manifest 中的 fixture SHA-256 必须在每次 suite 执行前与实际字节比较。

### 6.2 建立 canonical fixtures 与单一变异原则

在 `pass/` 建立一个 canonical valid fixture。其他业务规则 fixture 优先从该 fixture 做单一语义变异，使每个失败原因可定位。JSON-LD context 必须内嵌或通过仓库相对路径离线加载，核心测试禁止 HTTP context fetch。

最低 fixture 覆盖如下：

| 类别 | 必需覆盖 |
|---|---|
| PASS | 仅含全部必填字段；包含合法 description/license；`temporalStart == temporalEnd` |
| FAIL/提交级 | 0 个 Dataset；2 个 Dataset；blank-node Dataset |
| FAIL/字符串 | datasetId、title、providerName、spatial 的缺失、错误 datatype、空串、纯空白、多值 |
| FAIL/枚举 | frequency 缺失、`daily`、大小写错误、多值、错误 datatype；unit 错值与 `kWh + MWh`；format 错值与多值绕过 |
| FAIL/endpoint | 缺失、literal、HTTP IRI、多值 |
| FAIL/temporal | start/end 缺失、错误 datatype、多值、开始晚于结束 |
| FAIL/optional | description 错误 datatype/多值；license literal、HTTP IRI、多值 |
| FAIL/优先级 | 同时包含 Closed Shape Warning 和至少一个 Violation，实际结果必须为 FAIL |
| INAPPLICABLE | 其余内容完全有效，只增加一个 profile 外 Dataset property |
| UNTESTABLE | 确定性的 SUT malformed JSON-LD/RDF；全部权威合同与必需依赖预检通过后，测试替身模拟 validator timeout、crash 或验证服务 runtime exception |

一个 fixture 可以覆盖多个低层 constraint component，但每个 requirement ID 至少需要一个能够明确断言它的 case。若组合 fixture 使归因含糊，应拆为独立 case。

### 6.3 实现四状态分类器

按 Master 固定优先级实现：

1. 权威 Shape、manifest、harness 与必需依赖预检成功后，SUT 输入无法解析/离线加载，或 test-case manifest 具名且受控的 validator timeout、crash、验证服务 runtime exception 使可信判断无法形成 → `UNTESTABLE`。
2. report graph 中至少一个 `sh:Violation` → `FAIL`；同时存在 Warning 时仍为 FAIL。
3. 无 Violation，且存在来自 `ex:DatasetClosedShape` 的契约内 `sh:Warning` → `INAPPLICABLE`。
4. 输入和 Shape 成功解析、必需目标确实被评估、无 Violation/Warning → `PASS`。

未知 severity、未知 source shape、无法解析的 report graph、manifest/schema 错误、Shape/依赖缺失、报告写入失败或测试编排器异常必须形成程序状态 `ERROR` 和非零退出。它们不能被自动当作一个满足 oracle 的 UNTESTABLE case。

validator 调用必须显式固定并记录引擎配置，不能依赖库默认值：使用 lock 中的 pySHACL 版本，启用 D 契约所需的 SHACL-SPARQL/advanced 能力，固定 inference 策略（该 wire-profile 默认不引入额外推理），禁止首条结果后提前中止，并把 Warning/Info 策略写入机器证据。每个 fixture 单独构成提交 data graph；ontology、Shape、manifest、provenance 或其他 fixture 不得合并进该 graph。0/2 Dataset 和 temporal 倒序 fixtures 必须证明两个 SPARQL constraints 确实执行；任何一个未执行都使 suite 失败。

可以消费 Phase 03 的 D Meta-SHACL 通过证据，但每次 v0.4 suite 仍必须先核对发布 Shape 与 release manifest/D 原件的 SHA-256，并重新解析 Shape graph。hash 或 parse 失败时程序 ERROR；历史 Meta-SHACL 证据不能替代当前运行完整性检查。

### 6.4 解析并断言 SHACL report graph

每个结果至少规范化提取：focus node、result path、source shape、source constraint component、severity、message、value。排序不得依赖 RDF blank-node ID。所有 report result 必须映射到 manifest 中的 requirement ID；出现未映射结果时 suite 失败。

预期 FAIL case 只有在业务状态、requirement ID、source shape、path、severity、constraint component 和结果数量断言全部匹配时才为 `SUCCESS`。仅比较 `conforms=false` 不构成验收。

### 6.5 防止空目标假 PASS

实现目标激活/完整性检查，至少证明：

- 发布 Shape 图包含 release manifest 要求的全部命名 Shape。
- canonical PASS 数据中恰有一个 `dcat:Dataset`，Dataset NodeShapes 实际有 focus node。
- `ex:DatasetCardinalityShape` 的提交级 target 被实际执行。
- 0 Dataset case 稳定命中 cardinality violation。
- 发现 0 个测试、0 个执行测试或跳过必需测试时程序非零退出。

### 6.6 分离业务状态与程序状态

单 case JSON 记录 `expected_business_status`、`actual_business_status`、`assertions` 和 `program_status`。suite 退出码只表达 harness 是否完整执行及全部 oracle 是否匹配。预期 FAIL、INAPPLICABLE 或 UNTESTABLE 准确出现时，其 case 程序状态为 SUCCESS。

### 6.7 生成确定性结果

机器真源写入 `build/validation/v0.4/results.json`；Markdown 由该 JSON 确定性生成。环境和运行元数据单独写入 `run-environment.json`。结果必须包含 Master 证据合同要求的 discovered/executed/passed/failed/skipped、输入 hashes、fixture hashes、所有 consumed manifest hashes、validation-suites `contract_version`/registry hash，以及 `scripts/validate.py`、分类器、SHACL report parser、manifest semantic checker、报告器和全部实际加载 helper 的源 SHA-256，并能检测陈旧报告。

连续运行两次时，除独立环境清单外，规范化核心 JSON 应字节一致。

### 6.8 更新 suite 注册表并首次启用 all

只更新 `validation-suites.json` 中的 `v0.4` 和组合 `all`：

- `v0.4` 标记 `IMPLEMENTED`，组成包括 test-case schema、跨记录语义 checker、fixture hash、四状态分类、report assertions、target activation 和 fault-injection self-tests。
- `all` 首次标记 `IMPLEMENTED`，按确定性顺序展开六个非 `all` 公开 suite：`frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`。
- 本阶段的 `all` 尚不包含 Phase 06 SPARQL/quality/governance 内部 checks；Phase 06 将在不新增公开 suite 名的前提下加入并 bump `contract_version`。
- 状态或组成变化必须 bump 顶层 `contract_version`；新的 `contract_version`/registry SHA-256 进入 host/Docker 证据。
- 不新增公开 suite 名或其他合同版本字段。

重跑 suite registry 的 duplicate ID、悬空 dependency、dependency cycle、0 component、unknown entrypoint、重复 component、shell-command payload 和 `all` 展开不完整 negative controls。

## 7. 产物

- `C_Semantic_Treehouse/fixtures/v0.4/{pass,fail,inapplicable,untestable}/**`
- `C_Semantic_Treehouse/manifests/v0.4-test-cases.json`
- `C_Semantic_Treehouse/manifests/schemas/v0.4-test-cases.schema.json`
- 更新后的 `C_Semantic_Treehouse/manifests/validation-suites.json`
- 四状态分类与 report graph 断言实现
- classifier/negative-control 自测
- `build/validation/v0.4/results.json`
- `build/validation/v0.4/report.md`
- `build/validation/v0.4/run-environment.json`
- `build/phase-05/**`
- `docs/v0.4/STATUS.md` 中的 Phase 05 小节

## 8. 必需命令

以下命令均从仓库根目录运行并记录退出码：

```text
git status --short --branch
.\scripts\validate.ps1 -Suite frozen
.\scripts\validate.ps1 -Suite environment
.\scripts\validate.ps1 -Suite baseline
.\scripts\validate.ps1 -Suite traceability
.\scripts\validate.ps1 -Suite v0.4-model
.\scripts\validate.ps1 -Suite v0.4
.\scripts\validate.ps1 -Suite all
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
git status --short
```

还必须运行实现中定义的 deterministic rerun、故障注入自测、duplicate case/fixture ID、悬空 cross-reference、fixture hash mismatch，以及 suite registry duplicate/dependency/cycle/0-component/unknown-entrypoint/shell-payload/`all` 展开负控，并在 `STATUS.md` 中记录其完整规范化命令。Windows 包装必须证明其调用同一个 Python 编排器。

## 9. 验收矩阵

| 验收项 | 通过标准 | 证据 |
|---|---|---|
| Manifest schema | schema 有效，fixture SHA-256 必填且所有路径/hash/ID 可解析 | `build/phase-05/manifest-validation.json` |
| 状态条件化 oracle | PASS、FAIL/INAPPLICABLE、UNTESTABLE 的字段分支互斥，跨状态或缺失字段均被 schema 拒绝 | schema branch negative controls |
| Manifest 语义 | duplicate IDs、悬空 cross-references、同路径多 hash 和 fixture 漂移均被拒绝 | semantic negative controls |
| 规则覆盖 | 每个 v0.4 requirement 至少关联一个被执行 case | v0.4 results coverage 区 |
| 四状态 | 四种业务状态均由自动 case 实际产生 | `results.json` |
| FAIL 精确性 | 规则、Shape、path、severity、component、数量断言满足 | 每 case assertions |
| 优先级 | Warning + Violation 稳定得到 FAIL | 优先级 case |
| INAPPLICABLE | 仅 Closed Shape extra-property Warning 被映射 | INAPPLICABLE case |
| UNTESTABLE | SUT input parse 与预检通过后的受控 timeout/crash 各有确定性测试；意外 harness/authority error 非零 | negative controls |
| 目标命中 | PASS case 无空目标，0 Dataset 不假 PASS | target-activation checks |
| 零发现保护 | 0 tests/skip required 导致 ERROR | harness self-test |
| 确定性 | 两次核心 JSON 字节一致 | deterministic comparison |
| 无回归 | baseline、v0.4-model、v0.4、all 均退出 0 | suite reports |
| 完整性 | Phase 前后 frozen 均退出 0 | frozen reports |
| Suite 合同 | v0.4 与 all 首次 IMPLEMENTED；all 精确展开六个非all公开suite；`contract_version` 已 bump | registry/checker JSON |
| Runner 可追溯 | validate、分类器、report parser、semantic checker、报告器和 helper 源 hash 已记录 | results/environment JSON |
| 路径边界 | staged/unstaged check、stat、name-status 均审查，diff 仅位于可写路径 | diff 审查 |

## 10. AWAITING、BLOCKED 与 DEFERRED 规则

- 本阶段所有目标均为主线必需项，不允许使用 `DEFERRED`。
- 进入门槛失败时先完成安全诊断并把当前进度写入 `CHECKPOINT.md`。
- D hash 改变、compatibility decision 缺失、manifest schema/跨记录语义不一致、fixture hash 缺失或漂移、duplicate-ID/cross-reference 负控失败、suite `contract_version` 未 bump、证据缺少 runner/helper hash、规则无 fixture、任一必需 suite 非零、0 测试、未知 report result 或无法形成可信四状态时，按 `human-intervention-policy.md` 停止写入并完成至多一次只读复现。存在具名修复或需要用户选择时标记 `AWAITING_HUMAN_DECISION`；诊断确认当前没有安全路径时标记 `BLOCKED`。
- 若缺陷属于 Phase 03 traceability 或 Phase 04 model/release manifest，记录最早受影响 Phase 和证据，说明需要回到该 Phase 处理；禁止在本阶段就地绕过或静默修改上游产出。
- 可选外部 validator 不可用不影响本阶段，因为本阶段不得依赖它。

## 11. 阶段交接

全部验收通过后：

1. 在 `docs/v0.4/STATUS.md` 追加 Phase 05 小节，包含进入门槛、文件变更、命令/退出码、验收矩阵、证据路径、剩余风险和 Phase 06 进入条件。
   风险处置引用 Phase 00 baseline snapshot risk ID；不回写该 snapshot，新增风险登记供 Phase 09 汇总。
2. 把 `docs/v0.4/CHECKPOINT.md` 清空回占位符状态。
3. 明确交给 Phase 06 的真源：release manifest、v0.4 requirements、v0.4 test cases、validation-suites `contract_version`/registry hash、规范化 results JSON、runner/helper 源 hash，以及 v0.3 record 复用决定。
4. 报告工作树中所有剩余改动，不 commit、不 push。

## 12. Stop

Phase 05 标记 `COMPLETE`、`AWAITING_HUMAN_DECISION` 或 `BLOCKED` 后立即停止。不得开始 SPARQL、quality、governance、文档、CI、Treehouse 或发布工作。
