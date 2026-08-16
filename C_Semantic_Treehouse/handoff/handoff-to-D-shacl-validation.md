# D 组交接：v0.4 SHACL Validation Contract

## 1. Authority 与 byte binding

[Release manifest](../manifests/release-manifest.json) 将 D 组冻结输入和 C 组发布 Shape 绑定到相同 bytes：

| role | manifest ref / artifact ID | repository path | SHA-256 |
|---|---|---|---|
| D 组规范性冻结 TTL | `d-shape-v04` | `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` |
| C 组 byte-copy metadata Shape | `v04-metadata-shapes` | `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` |

可直接查看 [D 组冻结 TTL](../../inputs/d-group/v0.4/received/building-energy-shapes_D.ttl) 与 [C 组 Shape artifact](../model/v0.4/data-product-metadata-shapes.ttl)。相同 SHA-256 是本交接的首要完整性断言；任何一侧 bytes 改变都应使 validation fail closed。

## 2. Requirements、test oracle 与 fixtures

| authority | path | SHA-256 / scope |
|---|---|---|
| Requirements registry | `C_Semantic_Treehouse/manifests/v0.4-requirements.json` | `53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e`；`D04-R001`–`D04-R017` |
| Test-case manifest | `C_Semantic_Treehouse/manifests/v0.4-test-cases.json` | `87e367ea285ddc7feb5fa7f3f4b6c0035be0b768de5e56398ac422abaf494e5a`；66 cases |
| Fixture root | `C_Semantic_Treehouse/fixtures/v0.4/` | manifest 逐 case 绑定 fixture path、format 与 SHA-256 |

入口文件为 [requirements manifest](../manifests/v0.4-requirements.json)、[test-case manifest](../manifests/v0.4-test-cases.json) 和 [fixture index](../fixtures/v0.4/README.md)。Fixture 按 `pass/`、`fail/`、`inapplicable/`、`untestable/` 分类；目录名用于导航，expected oracle 始终读取 test-case manifest。

Test manifest 还固定 Shape artifact assertion、profile ID `dssc-building-energy-metadata-v0.4`、pySHACL engine configuration、每个 case 的 requirement IDs、expected business status 和 report graph 断言。实际结果不会自动回写 expected oracle。

## 3. 单命令验证与程序退出语义

从仓库根目录按 host 选择对应受控入口：

```powershell
.\scripts\validate.ps1 -Suite v0.4
```

```bash
./scripts/validate.sh --suite v0.4
```

成功合同：exit code `0`、suite `v0.4` 的 `program_status` 为 `SUCCESS`、66 discovered、66 executed、66 passed、0 failed、0 skipped，并且全部 17 个 requirement IDs 被实际执行覆盖。当前本地结果见 [machine result](../../build/validation/v0.4/results.json) 与 [human-readable report](../../build/validation/v0.4/report.md)。

程序语义独立于业务状态：

- `SUCCESS`：harness 完整运行，authority/hash/preflight 成功，每个 case 的 actual business status 与 manifest expected status 相同，全部 report assertions 成立。
- `ERROR`：测试零发现、required test 跳过、hash/freshness/schema 错误、Shape/manifest/report authority 异常、oracle mismatch、未控异常或证据写入失败；suite 返回非零。

`FAIL` 和 `UNTESTABLE` 都是 manifest 可期望的业务状态。它们只有在所有对应断言成立时才计入程序 `SUCCESS`。

## 4. 四状态确定性优先级

在 authority Shape、manifest、依赖与 harness preflight 全部成功之后，业务状态依次判定：

1. `UNTESTABLE`：SUT 无法解析/加载，或 test manifest 明确声明并可控复现 validator timeout、crash、validation service/runtime fault，无法形成可信业务判断。
2. `FAIL`：validation 执行成功，report graph 至少含一个 `sh:Violation`；同时出现 Warning 仍为 `FAIL`。
3. `INAPPLICABLE`：validation 执行成功、没有 Violation，并出现获准映射的 `ex:DatasetClosedShape` extra-property `sh:Warning`。
4. `PASS`：输入与 Shape 成功解析，预期 targets 确实激活，report graph 没有 Violation 或 Warning。

Shape/manifest 解析失败、required dependency 缺失和 harness 自身崩溃直接产生程序 `ERROR`，不进入业务 `UNTESTABLE`。

## 5. SHACL report graph 解读

Harness 在每个 `sh:ValidationResult` 上规范化并核对下列字段：

| normalized field | SHACL meaning | D 组核对要点 |
|---|---|---|
| `focus_node` | `sh:focusNode` | 实际被约束评估的 RDF node；保留 term type 与 value。 |
| `result_path` | `sh:resultPath` | property constraint 的实际 path；NodeShape/SPARQL graph-level result 可为 `null`。 |
| `source_shape` | `sh:sourceShape` | 产生结果的 named Shape，例如 `ex:DatasetCardinalityShape` 或 `ex:DatasetClosedShape`。 |
| `source_constraint_component` | `sh:sourceConstraintComponent` | 约束组件，例如 `sh:SPARQLConstraintComponent`、`sh:MinCountConstraintComponent`、`sh:ClosedConstraintComponent`。 |
| `severity` / `severity_name` | `sh:resultSeverity` | IRI 与本地名；`Violation` 优先于 `Warning`。 |
| `message` | `sh:resultMessage` | 与 requirements/test manifest 的 message policy 比较；引擎默认文本不能伪装成 D TTL 的显式规范 message。 |
| `value` | `sh:value` | 触发结果的 RDF term；保留 IRI/literal 类型与 lexical form。 |
| `requirement_id` | harness trace binding | 由 source Shape/path/component/severity/message 绑定回 `D04-Rxxx`，必须位于 case 声明范围。 |

Test manifest 的 `expected_results` 还会断言 source shape、path、constraint component、severity、message policy 和 exact/minimum count。Harness 通过 `all-report-results-asserted` 确认 report graph 中没有未被 oracle 解释的额外结果。

## 6. Expected `FAIL` 与 harness `ERROR`

Expected `FAIL` 表示 validator 已成功执行，并产生 manifest 预期的一个或多个 `sh:Violation`。只有 requirement ID、source shape、path、constraint component、severity、message/value 与结果数量全部符合 oracle，该 case 才得到 `program_status: SUCCESS`。

Harness `ERROR` 表示验证流程或断言合同无法可信完成，例如：

- expected `FAIL` case 没有产生预期 Violation；
- 产生了错误的 Shape/path/component/message 或额外未声明结果；
- SUT parse fault 被错误用来代替 expected `FAIL`；
- authority Shape、manifest、hash、required dependency 或 report structure 无效；
- 测试零发现、跳过或执行异常。

因此，外部系统映射时应保留两个维度：`business_status` 与 `program_status`/exit code。

## 7. ITB 映射建议

| ITB concept | 本仓库映射 | 保留的 assertion |
|---|---|---|
| Test suite | v0.4 profile、byte-bound Shape、requirements registry 与 test manifest 的固定组合 | profile/release ID、authority hashes、engine config、全部 required case IDs |
| Test case | 一个 `D04-PCxxx` manifest record | fixture hash、requirement IDs、expected business status、report oracle |
| SUT | 该 case 的一个 JSON-LD submission graph；集成时可替换为经审查登记的 A 组候选 offering | 输入 format/hash、load stage、target activation 与 network boundary |
| Validation service | 固定配置的 pySHACL harness，或保持相同 oracle 的 ITB/SEMIC adapter | program exit、business status、完整 `sh:ValidationReport` 字段与 evidence reference |

Adapter 应保留原 Shape bytes和 expected oracle，并把 packaging/service failure 映射为 program `ERROR` 或 manifest 明确的受控 `UNTESTABLE`。外部服务产生的报告需能够追溯到 suite、test case、SUT hash、Shape hash 和 validator version。

## 8. 当前证据边界

- 当前本地 pySHACL v0.4 harness：已运行，machine result 为 `SUCCESS`。
- 外部 SEMIC validator：`NOT RUN`。
- 外部 ITB test suite/service：`NOT RUN`。
- Semantic Treehouse：`NOT RUN`。
- CI、Docker clean-room 与 GitHub publication：Phase 08/09 尚待执行，当前无成功证据。

本 handoff 提供 ITB mapping 建议和可复现的本地 oracle，不声称任何外部 validator、service 或 publication 已通过。
