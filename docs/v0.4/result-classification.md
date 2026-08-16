# v0.4 验证结果分类规范

## 1. 两层状态

每个 test case 同时具有业务状态与程序状态：

- 业务状态：`PASS`、`FAIL`、`INAPPLICABLE`、`UNTESTABLE`。
- 程序状态：`SUCCESS`、`ERROR`。

业务状态描述 SUT 相对 D 组契约的结果。程序状态描述 harness 是否完整、可信地执行并满足 test manifest 的 expected assertion。两者不得合并；pySHACL 的 `conforms` 布尔值也不得直接充当业务状态。

## 2. 分类前置条件

在考虑 `UNTESTABLE` 之前，harness 必须成功完成以下权威预检：

1. D 组 Shape 字节/hash、Turtle parse 和 Meta-SHACL 均有效。
2. requirements/test manifest、schema、cross-reference 和 source hash 均有效。
3. harness、runner、报告器和必需依赖存在且版本/源码符合合同。
4. 当前 case 已发现、enabled、required，并且 expected business status 合法。
5. authority-owned 本地 context、Shape、ontology 和其他核心依赖可离线加载。

上述任一项失败属于程序 `ERROR`。不得用业务 `UNTESTABLE` 掩盖权威 Shape、manifest、harness 或核心依赖故障。

## 3. 业务状态确定性优先级

前置条件成功后，严格按以下顺序选择且只选择一个业务状态：

| 优先级 | 条件 | 业务状态 |
|---:|---|---|
| 1 | SUT 输入无法解析或离线加载；SUT 所引用的允许范围内本地 context 缺失；或者 test manifest 具名声明且受控复现的 validator/service timeout、crash、service runtime/infrastructure fault 使验证无法完成 | `UNTESTABLE` |
| 2 | 验证和 report graph 生成成功，至少存在一个 `sh:Violation` | `FAIL` |
| 3 | 没有 Violation，且至少存在一个获准映射的 `ex:DatasetClosedShape` `sh:Warning` | `INAPPLICABLE` |
| 4 | 输入和 Shape 解析成功，预期 target 实际被评估，验证完成，且没有 Violation 或 Warning | `PASS` |

附加规则：

- Violation 与 Warning 同时出现时始终为 `FAIL`。
- 只有可追踪到 `ex:DatasetClosedShape`/`sh:ClosedConstraintComponent` 的 Warning 获准映射 `INAPPLICABLE`。
- 未识别 source shape、severity、constraint component，或出现未经批准的 Warning/Info severity 时形成程序 `ERROR`，不得推断业务 PASS/INAPPLICABLE。
- `UNTESTABLE` 只覆盖 SUT 侧 parse/load 故障和 manifest 明确、可控的 runtime fault。普通超时猜测、权威依赖缺失或 runner crash 不满足该条件。

## 4. 程序状态

### `SUCCESS`

以下条件必须全部成立：

1. harness 从 discovery 到 evidence 写入完整执行；
2. 权威预检和 report 结构校验全部通过；
3. 实际业务状态与 test manifest 的 expected business status 完全一致；
4. 对 FAIL/INAPPLICABLE case，requirement ID、source shape、path、severity、constraint component、message 和结果数量等规定断言全部满足；
5. 没有 case 被跳过，required case 数量非零。

预期为 `FAIL` 或 `UNTESTABLE` 的 case 在准确复现并满足 oracle 时，程序状态可以是 `SUCCESS`。

### `ERROR`

任一以下情况形成程序 `ERROR`，suite 必须非零退出：

- case 未发现、disabled、被跳过或 required case 数量为 0；
- actual business status 与 expected business status 不一致；
- authority Shape、manifest、schema、ontology、context 或核心依赖无效/缺失/hash 不匹配；
- target 节点数量为 0，或没有证据证明预期 target 被实际评估；
- report graph 缺失、无法解析、结构异常或缺少必需字段；
- source shape、path、severity、constraint component、message/数量断言无法可靠追踪；
- 出现未知 source shape、severity、component 或未经批准的结果映射；
- validator/harness/报告器异常，且该故障不是 manifest 具名声明并在全部权威预检后受控注入的 SUT runtime fault；
- evidence 写入、freshness、source hash 或 expected/actual 比较失败。

程序 `ERROR` 时不得记录可信业务 PASS。可以保留诊断观察值，但不能把它晋升为业务结论。

## 5. Target activation

业务 `PASS` 需要预期 target 命中数大于 0。任何预期 Shape 的 target 数为 0 都是程序 `ERROR`，即使 pySHACL 返回 `conforms=true` 且 report graph 为空。

`ex:DatasetCardinalityShape` 使用固定 `sh:targetNode ex:ValidationSubmission`。harness 必须显式断言该 Shape/target 已执行，不能仅依据数据图中是否显式出现该节点或 pySHACL 的 `conforms` 值推断执行。

## 6. Report graph 解释

1. 以 report graph 的结构化结果为业务分类输入；`conforms` 只作一致性诊断。
2. 先校验每个结果的 source shape、severity、constraint component、focus node、result path（适用时）和 message（TTL 显式提供时）。
3. NodeShape 级约束可以没有 result path。`D04-R002` 的 `ex:BuildingEnergyDatasetShape` NodeKind 约束没有规范 source path，也没有 TTL 显式 message；path 记为不适用，message 集合为空。pySHACL 默认文本不得充当规范 oracle。
4. 缺失本应存在的字段、错误 source locator 或异常 report 结构形成程序 `ERROR`。
5. 结构校验通过后，才按 `UNTESTABLE → FAIL → INAPPLICABLE → PASS` 的优先级确定业务状态。

## 7. SUT 与 authority 故障边界

| 故障 | 分类 |
|---|---|
| malformed JSON、无法解析的 JSON-LD SUT | 业务 `UNTESTABLE`；expected 匹配且 harness 完整时程序 `SUCCESS` |
| SUT 引用的、在受控离线加载范围内但缺失的本地 context | 业务 `UNTESTABLE` |
| D Shape、requirements/test manifest 或 authority-owned context 无法解析/缺失 | 程序 `ERROR` |
| manifest 具名且受控注入的 validator timeout/crash/service runtime fault；全部权威预检先成功 | 业务 `UNTESTABLE` |
| 非受控 runner crash、核心 validator import 缺失、evidence writer 失败 | 程序 `ERROR` |

## 8. 最小分类示例

| 观察 | 业务状态 | 程序状态条件 |
|---|---|---|
| 0 Violation，0 Warning，target 命中 | `PASS` | expected=PASS 且全部断言满足时 `SUCCESS` |
| 1+ Violation，可能同时有 Closed Warning | `FAIL` | expected=FAIL 且精确 report 断言满足时 `SUCCESS` |
| 0 Violation，仅有已追踪的 DatasetClosed Warning | `INAPPLICABLE` | expected=INAPPLICABLE 且精确 Warning 断言满足时 `SUCCESS` |
| SUT malformed，权威预检成功 | `UNTESTABLE` | expected=UNTESTABLE 且错误类别/阶段断言满足时 `SUCCESS` |
| 0 result，但 target=0 | 无可信业务结论 | `ERROR` |
| 未知 Warning 或 report 缺字段 | 无可信业务结论 | `ERROR` |
| actual=FAIL，expected=PASS | `FAIL` 观察值 | `ERROR` |

## 9. 机器真源

本文件冻结分类语义；case 级 expected business status、requirements 覆盖和 report assertion 由 manifests 提供。harness 必须验证二者一致，不能自动改写 expected 值来迎合实际结果。
