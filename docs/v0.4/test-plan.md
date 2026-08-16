# v0.4 D 组契约测试义务计划

> 本文是 `C_Semantic_Treehouse/manifests/v0.4-requirements.json` 的人类可读投影。JSON registry 是 requirement、test obligation、planned case、component coverage 与 expected status 的唯一机器真源；本文不得形成第二套 oracle。变更测试语义时先修改并校验 JSON，再同步本文。

## 范围与阶段边界

Phase 03 只冻结 planned case ID、变异轴、规则覆盖与预期状态。全部 case 的 `artifact_status` 均为 `PLANNED`，`fixture_ref` 均为 `null`。fixture 文件、`v0.4-test-cases.json` 和正式 harness 留给 Phase 05；本阶段不创建这些产物。

权威 Shape 为 `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`。测试以 `D04-PC001` 的一个 IRI Dataset、合法字段、无 profile 外属性为基线。除明确测试状态优先级的 `D04-PC060` 外，每个 planned case 只改变一个主要轴。一次变异可能同时触发同一 Shape 的多个 component，例如空串同时触发 `minLength` 与 `pattern`，这仍属于单一输入轴。

业务状态与程序状态分别断言：

- 可执行验证完成时程序状态为 `SUCCESS`，业务状态为 `PASS`、`FAIL` 或 `INAPPLICABLE`。
- SUT 解析/离线加载失败，或全部权威合同与依赖预检成功后的受控 runtime fault，由 harness 成功分类为 `UNTESTABLE`，程序状态仍为 `SUCCESS`。
- 权威 Shape、test manifest、harness 或核心依赖预检失败形成程序 `ERROR`，业务状态为 `null`，不得记录可信 PASS。
- pySHACL `conforms` 不是业务状态。至少一个 `sh:Violation` 决定 `FAIL`；无 Violation 且命中获准的 `ex:DatasetClosedShape` Warning 决定 `INAPPLICABLE`。
- 后续 harness 必须断言目标实际命中。目标节点数为 0 形成程序 `ERROR`；固定 `sh:targetNode ex:ValidationSubmission` 的 `ex:DatasetCardinalityShape` 必须显式证明已执行。

## Requirement 与义务覆盖

| Requirement | 正向义务 | 负向/边界义务 | 规范 component |
|---|---|---|---|
| `D04-R001` | `D04-PC001` | `D04-PC002`, `D04-PC003` | SPARQL |
| `D04-R002` | `D04-PC001` | `D04-PC004` | NodeKind、Property linkage |
| `D04-R003` | `D04-PC001` | `D04-PC005`, `D04-PC006`, `D04-PC007`, `D04-PC008`, `D04-PC009` | MinCount、MaxCount、Datatype、MinLength、Pattern |
| `D04-R004` | `D04-PC001` | `D04-PC010`, `D04-PC011`, `D04-PC012`, `D04-PC013`, `D04-PC014` | MinCount、MaxCount、Datatype、MinLength、Pattern |
| `D04-R005` | `D04-PC001` | `D04-PC015`, `D04-PC016`, `D04-PC017`, `D04-PC018`, `D04-PC019`, `D04-PC060` | MinCount、MaxCount、Datatype、MinLength、Pattern |
| `D04-R006` | `D04-PC001` | `D04-PC020`, `D04-PC021`, `D04-PC022`, `D04-PC023`, `D04-PC024` | MinCount、MaxCount、Datatype、MinLength、Pattern |
| `D04-R007` | `D04-PC001` | `D04-PC025`, `D04-PC026`, `D04-PC027`, `D04-PC028`, `D04-PC029` | MinCount、MaxCount、Datatype、In |
| `D04-R008` | `D04-PC001` | `D04-PC030`, `D04-PC031`, `D04-PC032`, `D04-PC033` | MinCount、MaxCount、Datatype、In |
| `D04-R009` | `D04-PC001` | `D04-PC034`, `D04-PC035`, `D04-PC036`, `D04-PC037` | MinCount、MaxCount、Datatype、In |
| `D04-R010` | `D04-PC001` | `D04-PC038`, `D04-PC039`, `D04-PC040`, `D04-PC041` | MinCount、MaxCount、NodeKind、Pattern |
| `D04-R011` | `D04-PC001` | `D04-PC042`, `D04-PC043`, `D04-PC044` | MinCount、MaxCount、Datatype |
| `D04-R012` | `D04-PC001` | `D04-PC045`, `D04-PC046`, `D04-PC047` | MinCount、MaxCount、Datatype |
| `D04-R013` | `D04-PC001`, `D04-PC048` | `D04-PC049` | SPARQL |
| `D04-R014` | `D04-PC001`, `D04-PC050`, `D04-PC051` | `D04-PC052`, `D04-PC053` | MaxCount、Datatype |
| `D04-R015` | `D04-PC001`, `D04-PC054`, `D04-PC055` | `D04-PC056`, `D04-PC057`, `D04-PC058` | MaxCount、NodeKind、Pattern |
| `D04-R016` | `D04-PC001` | `D04-PC059`, `D04-PC060` | Closed、Property allowlist |
| `D04-R017` | `D04-PC001` | `D04-PC061`, `D04-PC062`, `D04-PC063`, `D04-PC064`, `D04-PC065`, `D04-PC066`, `D04-PC067`, `D04-PC068`, `D04-PC069`, `D04-PC070` | operational header；无伪造 SHACL component |

每条 requirement 在 registry 中至少有一个 `POSITIVE` test obligation，并至少有一个 `NEGATIVE`、`BOUNDARY` 或 `OPERATIONAL` obligation。checker 必须验证 obligation ID 和 planned case ID 全局唯一、双向引用闭合，以及 source component 全部被 obligation 覆盖。

## Planned case 目录

下表的 `SUCCESS/ERROR` 是程序状态。业务状态栏的 `—` 表示不存在可信业务判断。

| Case | Requirement | 单轴 | 主要变异 | 预期业务 / 程序状态 |
|---|---|---:|---|---|
| `D04-PC001` | `D04-R001`–`D04-R017` | 是 | 一个 IRI Dataset；全部声明字段合法；无额外属性；预检与 validator 正常 | PASS / SUCCESS |
| `D04-PC002` | `D04-R001` | 是 | 删除唯一 Dataset | FAIL / SUCCESS |
| `D04-PC003` | `D04-R001` | 是 | 增加第二个不同 Dataset | FAIL / SUCCESS |
| `D04-PC004` | `D04-R002` | 是 | Dataset IRI 改为 blank node | FAIL / SUCCESS |
| `D04-PC005` | `D04-R003` | 是 | datasetId 缺失 | FAIL / SUCCESS |
| `D04-PC006` | `D04-R003` | 是 | datasetId 多值 | FAIL / SUCCESS |
| `D04-PC007` | `D04-R003` | 是 | datasetId 改为 IRI | FAIL / SUCCESS |
| `D04-PC008` | `D04-R003` | 是 | datasetId 为空串 | FAIL / SUCCESS |
| `D04-PC009` | `D04-R003` | 是 | datasetId 为纯空白/Tab | FAIL / SUCCESS |
| `D04-PC010` | `D04-R004` | 是 | title 缺失 | FAIL / SUCCESS |
| `D04-PC011` | `D04-R004` | 是 | title 多值 | FAIL / SUCCESS |
| `D04-PC012` | `D04-R004` | 是 | title 改为 IRI | FAIL / SUCCESS |
| `D04-PC013` | `D04-R004` | 是 | title 为空串 | FAIL / SUCCESS |
| `D04-PC014` | `D04-R004` | 是 | title 为纯空白/Tab | FAIL / SUCCESS |
| `D04-PC015` | `D04-R005` | 是 | providerName 缺失 | FAIL / SUCCESS |
| `D04-PC016` | `D04-R005` | 是 | providerName 多值 | FAIL / SUCCESS |
| `D04-PC017` | `D04-R005` | 是 | providerName 改为 IRI | FAIL / SUCCESS |
| `D04-PC018` | `D04-R005` | 是 | providerName 为空串 | FAIL / SUCCESS |
| `D04-PC019` | `D04-R005` | 是 | providerName 为纯空白/Tab | FAIL / SUCCESS |
| `D04-PC020` | `D04-R006` | 是 | spatial 缺失 | FAIL / SUCCESS |
| `D04-PC021` | `D04-R006` | 是 | spatial 多值 | FAIL / SUCCESS |
| `D04-PC022` | `D04-R006` | 是 | spatial 改为 IRI | FAIL / SUCCESS |
| `D04-PC023` | `D04-R006` | 是 | spatial 为空串 | FAIL / SUCCESS |
| `D04-PC024` | `D04-R006` | 是 | spatial 为纯空白/Tab | FAIL / SUCCESS |
| `D04-PC025` | `D04-R007` | 是 | frequency 缺失 | FAIL / SUCCESS |
| `D04-PC026` | `D04-R007` | 是 | hourly 与 daily 多值绕过 | FAIL / SUCCESS |
| `D04-PC027` | `D04-R007` | 是 | frequency 改为 IRI | FAIL / SUCCESS |
| `D04-PC028` | `D04-R007` | 是 | frequency 为 daily | FAIL / SUCCESS |
| `D04-PC029` | `D04-R007` | 是 | frequency 为大小写错误的 Hourly | FAIL / SUCCESS |
| `D04-PC030` | `D04-R008` | 是 | unit 缺失 | FAIL / SUCCESS |
| `D04-PC031` | `D04-R008` | 是 | kWh 与 MWh 多值绕过 | FAIL / SUCCESS |
| `D04-PC032` | `D04-R008` | 是 | unit 改为 IRI | FAIL / SUCCESS |
| `D04-PC033` | `D04-R008` | 是 | unit 为 MWh | FAIL / SUCCESS |
| `D04-PC034` | `D04-R009` | 是 | format 缺失 | FAIL / SUCCESS |
| `D04-PC035` | `D04-R009` | 是 | application/json 与 text/csv 多值绕过 | FAIL / SUCCESS |
| `D04-PC036` | `D04-R009` | 是 | format 改为 IRI | FAIL / SUCCESS |
| `D04-PC037` | `D04-R009` | 是 | format 为 text/csv | FAIL / SUCCESS |
| `D04-PC038` | `D04-R010` | 是 | endpoint 缺失 | FAIL / SUCCESS |
| `D04-PC039` | `D04-R010` | 是 | 两个 HTTPS endpoint IRI | FAIL / SUCCESS |
| `D04-PC040` | `D04-R010` | 是 | HTTPS URL 编码为普通 string | FAIL / SUCCESS |
| `D04-PC041` | `D04-R010` | 是 | endpoint 为 HTTP IRI | FAIL / SUCCESS |
| `D04-PC042` | `D04-R011` | 是 | temporalStart 缺失 | FAIL / SUCCESS |
| `D04-PC043` | `D04-R011` | 是 | temporalStart 多值 | FAIL / SUCCESS |
| `D04-PC044` | `D04-R011` | 是 | temporalStart datatype 为 xsd:string | FAIL / SUCCESS |
| `D04-PC045` | `D04-R012` | 是 | temporalEnd 缺失 | FAIL / SUCCESS |
| `D04-PC046` | `D04-R012` | 是 | temporalEnd 多值 | FAIL / SUCCESS |
| `D04-PC047` | `D04-R012` | 是 | temporalEnd datatype 为 xsd:string | FAIL / SUCCESS |
| `D04-PC048` | `D04-R013` | 是 | temporalStart 等于 temporalEnd | PASS / SUCCESS |
| `D04-PC049` | `D04-R013` | 是 | temporalStart 晚于 temporalEnd | FAIL / SUCCESS |
| `D04-PC050` | `D04-R014` | 是 | description 缺省 | PASS / SUCCESS |
| `D04-PC051` | `D04-R014` | 是 | 提供一个合法 string description | PASS / SUCCESS |
| `D04-PC052` | `D04-R014` | 是 | description 多值 | FAIL / SUCCESS |
| `D04-PC053` | `D04-R014` | 是 | description 改为 IRI | FAIL / SUCCESS |
| `D04-PC054` | `D04-R015` | 是 | license 缺省 | PASS / SUCCESS |
| `D04-PC055` | `D04-R015` | 是 | 提供一个 HTTPS license IRI | PASS / SUCCESS |
| `D04-PC056` | `D04-R015` | 是 | license 多值 | FAIL / SUCCESS |
| `D04-PC057` | `D04-R015` | 是 | license 编码为普通 string | FAIL / SUCCESS |
| `D04-PC058` | `D04-R015` | 是 | license 为 HTTP IRI | FAIL / SUCCESS |
| `D04-PC059` | `D04-R016` | 是 | 增加一个 profile 外 Dataset 属性 | INAPPLICABLE / SUCCESS |
| `D04-PC060` | `D04-R005`, `D04-R016` | 否；优先级用例 | 同时增加额外属性并删除 providerName | FAIL / SUCCESS |
| `D04-PC061` | `D04-R017` | 是 | SUT 为 malformed JSON | UNTESTABLE / SUCCESS |
| `D04-PC062` | `D04-R017` | 是 | JSON 语法合法但 JSON-LD 无效 | UNTESTABLE / SUCCESS |
| `D04-PC063` | `D04-R017` | 是 | SUT 所需本地 context 缺失 | UNTESTABLE / SUCCESS |
| `D04-PC064` | `D04-R017` | 是 | 全部预检通过后注入具名 validator timeout | UNTESTABLE / SUCCESS |
| `D04-PC065` | `D04-R017` | 是 | 全部预检通过后注入具名 validator crash | UNTESTABLE / SUCCESS |
| `D04-PC066` | `D04-R017` | 是 | 全部预检通过后注入具名受控 service runtime/infrastructure fault | UNTESTABLE / SUCCESS |
| `D04-PC067` | `D04-R017` | 是 | 权威 Shape 不可用或预检失败 | — / ERROR |
| `D04-PC068` | `D04-R017` | 是 | test manifest 预检失败 | — / ERROR |
| `D04-PC069` | `D04-R017` | 是 | harness 预检失败 | — / ERROR |
| `D04-PC070` | `D04-R017` | 是 | 核心依赖预检失败 | — / ERROR |

## Fixture 实现义务

Phase 05 materialize fixture 时必须保持 planned case ID，不得复用同一个 ID 表示不同变异。优先让每个 fixture 只引入表中的一个主要变异；`D04-PC060` 是经过明确登记的双变异优先级用例。

JSON-LD fixture 必须使用受控的本地 context loader，禁止网络解析。`D04-PC063` 只删除 SUT 需要的本地 context；权威 Shape、manifest 与 harness 仍需通过预检。`D04-PC064`–`D04-PC066` 必须通过具名、确定性 fault-injection hook 触发，记录 hook ID、触发点和 preflight 成功证据；随机超时、机器负载或真实服务波动不能充当测试 oracle。

`D04-PC067`–`D04-PC070` 是 harness 负控。它们证明合同或基础设施前置条件失败时会 fail closed 为程序 `ERROR`，不属于 SUT 的 `UNTESTABLE` fixture。

## 后续验收

Phase 05 的正式 test-case manifest 和 runner 至少需要机械断言：

- 每个 planned case ID 恰好 materialize 一次，全部 70 个 ID 均有 fixture 或具名 fault-control 实现。
- 每条 requirement 的正向与负向/边界 obligation 均有执行结果；source shape、path、severity、message 与 constraint component 按 registry 核对。
- `D04-PC001` 实际命中全部预期 target；`DatasetCardinalityShape` 的固定 targetNode 被单独记录。
- Warning 与 Violation 混合时 `D04-PC060` 为 FAIL；单独 Closed Warning 时 `D04-PC059` 为 INAPPLICABLE。
- SUT/runtime `UNTESTABLE` 与程序 `ERROR` 使用不同字段和证据，不以 pySHACL `conforms` 直接替代业务状态。
- fixture、test-case manifest、runner 与报告的 repo-relative 路径和 SHA-256 进入后续证据；本计划中的 `PLANNED` 引用届时由受控阶段更新为实际 artifact。
