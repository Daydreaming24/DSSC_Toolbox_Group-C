# AI-assisted, Human-governed Semantic Modeling

## 1. Purpose

本项目允许 AI 协助审计、fixture/代码/文档草拟和证据整理。语义权威、domain judgment、expected oracle、发布授权与对外承诺由明确的人类和机器 gate 控制。核心原则是：AI 生成候选变更，机器验证可执行合同，具名的人类/可审计组级身份承担语义与发布责任。

**AI 不得自主批准语义、修改权威合同或授权发布。** AI/agent/validator 均不作为 semantic reviewer、Domain Reviewer 或 Release Approver 的身份替代。

## 2. AI 可协助的工作

AI 可以在当前 Phase 的可写范围和人工授权内完成：

- 审计 manifests、schemas、Shape、fixtures、reports、provenance 和文档之间的一致性；
- 从已登记 requirement/test obligation 草拟正例、负例、四状态 fixture 和 negative control；
- 草拟 checker、reporter、deterministic serialization 与文档一致性代码；
- 草拟 README、模型说明、handoff、migration table 和 Mermaid source；
- 汇总 diff、hash、test count、business/program status 与 freshness evidence；
- 标出冲突、未知项、`PENDING`、`NOT RUN` 和需要人工决定的边界。

AI 生成内容始终是候选产物。Fixture expected status、SHACL oracle、namespace/path、compatibility conclusion 和 lifecycle decision 需回到对应 machine source 与 review gate 核验。

## 3. Authority 与 gate 分工

| gate | authority / executor | required evidence | decision boundary |
|---|---|---|---|
| D 契约 gate | D 组冻结 TTL；C/D 组审核解释 | D Shape path/hash、requirements trace、accepted ADR | Shape target/path/severity/component/message 和 Closed Shape 行为以冻结契约为准。AI 可审计 bytes 与引用，不改写或弱化合同。 |
| Manifest/oracle gate | 机器 checker + 人工评审 | JSON Schema、跨记录语义、unique IDs、references、hashes、coverage、negative controls | Expected oracle 与 actual result 分离保存；actual result 不自动改写 expected。 |
| Automated validator gate | 统一 validation dispatcher 与受控 checker | exit code、`SUCCESS/ERROR`、discovered/executed/passed/failed/skipped、完整 report assertions | 机器证明已登记合同被确定性执行。零发现、skip、陈旧 hash 与异常均 fail closed。 |
| C 组 semantic review | 具名人员或可审计 C 组身份 | term/path meaning、version identity、standard reuse、compatibility、migration、provenance | 形成语义接受、修改请求或拒绝结论。AI 提供证据和草案。 |
| Domain review | 具名 Domain Reviewer | Dataset/provider/spatial/temporal、`hourly`、`kWh`、`application/json`、HTTPS 和 metadata/record 边界 | 确认业务含义与领域适用性。 |
| D 组 final contract review | 可审计 D 组身份 | byte-identical Shape、four-state oracle、report graph 和 handoff | 确认 C artifact 对 D contract 的忠实执行。 |
| Release approval | 具名人类 Release Approver | 全量自动证据、semantic/domain/D review、risk、license/source、handoffs、platform/CI evidence | 明确批准或拒绝 v0.4 release；维护者已接受 P00-R14 最终责任，逐项审核记录继续保留 `PENDING`。 |
| Publication | 经明确授权的维护方 | commit、CI run URL/log、clean-room result、tag/release 与 publication record | 外部 Git/GitHub 操作只有获得明确授权后执行。 |

已接受的 Phase 03 ADR 只覆盖其声明的 migration decision 范围。它们为后续 release review 提供输入，不自动构成最终发布批准。

## 4. Human-governed lifecycle

1. **Capture authority**：保存冻结 D 组 Shape、说明、原始场景与 prompt；记录 repository-relative path 和 SHA-256。
2. **Trace requirements and decisions**：将 Shape semantics 登记为 requirement IDs，并通过具名 ADR 处理 `dct:conformsTo`、wire profile 和 record inheritance。
3. **Generate candidates**：人或 AI 在批准范围内草拟 model artifact、fixture、checker、reporter 或文档。
4. **Review diff and manifest binding**：逐文件阅读 unstaged/staged diff；核对 artifact ID、path、hash、origin、expected oracle 与允许写入范围。
5. **Run automated gates**：统一 dispatcher 提供七个公开 suite：`frozen`、`environment`、`baseline`、`traceability`、`v0.4-model`、`v0.4`、`all`。`all` 按 registry 的确定顺序聚合公开依赖，并在内部执行 composition、SPARQL、quality、governance 和 documentation components；required check 必须发现并执行，失败返回非零。
6. **Perform semantic and domain review**：具名 reviewer 评估机器无法决定的含义、适用性、compatibility、risk 和 downstream impact。
7. **Prepare A/B/D handoff**：把已核验的字段、URI/provenance、Shape/oracle/report 合同交给各组，并保留 `NOT RUN`/`PENDING` 边界。
8. **Authorize release and publication**：Release Approver 基于完整证据作出明确决定；维护方在单独授权后执行外部发布。
9. **Monitor and deprecate**：记录 issue/use evidence；breaking change 进入新的 requirement、decision、migration 与测试循环。

任何验证失败先保留失败证据并定位最早受影响 Phase。修改 Shape、fixture、manifest expected 值或 requirement trace 需要具名理由与人工确认。

## 5. 必须保留的审计轨

### Prompt 与授权

- [Master prompt](../../prompts/v0.4/master-prompt.md)、[human-intervention policy](../../prompts/v0.4/human-intervention-policy.md) 与 [Phase 07 prompt](../../prompts/v0.4/phase-07-documentation-diagrams-and-handoffs.md)；
- 用户针对保护文件、网络、安装、外部写入、Git 操作和发布动作的明确决定；
- [STATUS](../../docs/v0.4/STATUS.md) 中只追加的完成记录，以及 [CHECKPOINT](../../docs/v0.4/CHECKPOINT.md) 中当前中断/恢复记录。

### Machine authorities

- [release manifest](../manifests/release-manifest.json)：version、artifact、hash、origin 与 record inheritance；
- [requirements manifest](../manifests/v0.4-requirements.json)：D04 rule、source locator、boundary 与 test obligation；
- [test-case manifest](../manifests/v0.4-test-cases.json)：fixture hash、expected business status 和 report oracle；
- [validation-suite registry](../manifests/validation-suites.json)：fixed suite、entrypoint、ordered `all` composition、contract version/hash；
- [provenance JSON-LD](../governance/provenance.jsonld)：Entity/Activity/Agent、source/artifact path/hash、derivation、inheritance 与 pending activities。

### Diff 与 source trace

每次 review 至少保留下列命令的实际结果与退出码：

```text
git status --short --branch
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
```

Evidence 同时登记 dispatcher、checker、reporter 和实际加载 helper 的 repository-relative path 与 SHA-256。个人绝对路径、token、secret、临时目录和 machine-local interpreter path 不进入可发布的 normalized result。

### Reports 与 negative controls

- [v0.4 four-state result](../../build/validation/v0.4/results.json)；
- [SPARQL result](../../build/validation/sparql/results.json)、[quality result](../../build/validation/quality/results.json) 与 [governance result](../../build/validation/governance/results.json)；
- 文档 checker 的正常结果、deterministic rerun 和 self-test/negative-control evidence；
- broken link、absolute path、unknown artifact/suite、manifest mismatch、zero discovery、missing Mermaid structure 和 false `DONE` 输入各自应返回非零。

失败日志与原始 machine result 应保留用于诊断。生成新版 evidence 采用新路径或明确的历史/当前边界，避免覆盖失败来形成虚假成功叙述。

## 6. 状态语言与自动化边界

业务状态与程序状态分开记录：

- `PASS`、`FAIL`、`INAPPLICABLE`、`UNTESTABLE` 描述已登记 case 的业务判断；
- `SUCCESS` 表示 harness 完整执行且 actual 与 expected 完全匹配；
- `ERROR` 表示 authority、harness、oracle、dependency、freshness、coverage 或 evidence 失败，程序退出非零。

`PENDING` 表示尚需实际 review/approval/activity。`NOT RUN` 表示该执行轨尚未运行。文档汇总器不得把 `PENDING`、`NOT RUN`、`PARTIAL` 或历史 evidence 自动升级为 `DONE`。

当前外部/可选轨边界：

- Semantic Treehouse：deployment/workload/import/export/SHACL execution=`PASS`，runtime=`PAUSED`，仅 publication=`NOT RUN`；
- 外部 SEMIC/ITB：`NOT RUN`；
- Mermaid parser、renderer 与 visual QA：`NOT RUN`；Phase 07 只做 deterministic structure lint，该 lint 不证明 syntax/render 成功；
- CI、Docker clean-room 和 GitHub repository publication：已有候选绑定证据；每个发生 tracked 内容变化的新候选均须独立重验，最新动态 SHA/run/clone 见 [`publication-record.md`](../../docs/v0.4/publication-record.md)；
- v0.4 human governance：维护者已接受 P00-R14 最终责任；逐项 semantic/domain/D/release sign-off 记录保持 `PENDING`。

## 7. Demo 导航

演示应沿机器真源与 review gate 展开：

1. [版本演进与 breaking migration](../C_model_versioning_demo.md)；
2. [metadata/record/四状态关系图 source](../diagrams/metadata-record-model.mmd)；
3. [semantic governance flow source](../diagrams/semantic-governance-flow.mmd)；
4. [A 组 offering metadata handoff](../handoff/handoff-to-A-offering-metadata.md)；
5. [B 组 model URI/provenance handoff](../handoff/handoff-to-B-model-uri-provenance.md)；
6. [D 组 SHACL validation handoff](../handoff/handoff-to-D-shacl-validation.md)；
7. 上述 machine results 与 provenance audit trail。

演示者应把历史 v0 evidence、当前 v0.4 本地 machine evidence、最新已确认候选的 Phase 08/09 技术发布链、P00-R14 已接受责任与尚待形成的逐项签字、可选 external evidence 分开讲解。当前状态以 [`STATUS.md`](../../docs/v0.4/STATUS.md) 的最新追加记录为准，动态候选绑定以 [`publication-record.md`](../../docs/v0.4/publication-record.md) 为准。Demo 只展示已存在的证据状态，不把责任接受扩张为逐项审核完成。

## 8. 责任与合规边界

AI 输出可提升审计覆盖、生成速度与文档一致性。人类 reviewer 对采用哪些候选变更、语义是否正确、业务是否适用和是否发布承担明确责任。Validator 对其固定可执行断言提供机器结果；它不承担法律、伦理、商业或组织授权判断。

本审计轨支持可追溯性和复现。它不自动构成 Gaia-X conformity、法律合规、安全认证、数据权利确认或对外发布批准；这些结论需要对应权威规则、实际检查和具名授权。
