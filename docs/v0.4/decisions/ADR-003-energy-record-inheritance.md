# ADR-003 — Energy Reading Record 继承 v0.3 子契约

- 状态：`ACCEPTED`
- 决定日期：2026-08-10
- 适用范围：Energy Reading Record 的版本继承、artifact identity 和与 v0.4 metadata 的边界
- 关联决定：`ADR-001-dct-conforms-to.md`、`ADR-002-wire-profile-and-version-identity.md`

## Context

D 组 v0.4 输入定义 Building Energy metadata profile。其 target 只有 `ex:ValidationSubmission` 和 `dcat:Dataset`，没有 `be:EnergyReadingRecord` target，也没有 `buildingId`、`meterId`、`timestamp`、`energyKWh`、record `be:unit` 或 `location` 等字段约束。

v0.3 Energy Reading Record 使用项目 `be:` namespace，target 为 `be:EnergyReadingRecord`。其 record-specific context、Shape、JSON Schema 和正负样例已经由 Phase 02 baseline manifest 绑定 SHA-256 并复验。D 组 metadata 的 `ex:unit` 与 record 的 `be:unit` 是不同 IRI。

v0.3 ontology 同时包含 metadata 与 record 术语。整个 ontology/metadata bundle 不能因此被描述成与 v0.4 wire profile 兼容。

## Decision

1. D 组 v0.4 变更只作用于 metadata wire profile。Energy Reading Record 精确继承 v0.3 record 子契约。
2. Phase 04 release manifest 必须显式引用以下五个 v0.3 record-specific artifacts 及其准确 SHA-256；不得复制到 `model/v0.4/` 制造一个内容相同的新 record 版本：

   | v0.3 artifact | SHA-256 |
   |---|---|
   | `C_Semantic_Treehouse/model/v0.3/energy-reading-record.schema.json` | `dd07414e3752bf582bf5e721009064e16d7be3e1e06d60daaad08000869ccfa9` |
   | `C_Semantic_Treehouse/model/v0.3/energy-reading-record-context.jsonld` | `9727da9b8650dc444d719113a6978a3a26a59bfd1fde011a98e4c1f4b476f748` |
   | `C_Semantic_Treehouse/model/v0.3/energy-reading-record-shapes.ttl` | `84d1eee9cfeecd1791117552611e83d36af7df4f3b4c783ddbd75d45bae66c9a` |
   | `C_Semantic_Treehouse/model/v0.3/energy-reading-record-valid.jsonld` | `8f7509ad08fb9a62cdff1d6c904801c9421c3ce768bdd9ecb651cd480aa158e1` |
   | `C_Semantic_Treehouse/model/v0.3/energy-reading-record-invalid.jsonld` | `e516f6a8e4ea811170c72e922b86ac7ea46594046704d01a55a2c8e13cd8f358` |

3. v0.3 ontology 中 record 术语的定义继续作为 v0.3 provenance/dependency 使用。不得据此宣称整个 v0.3 ontology、metadata context 或 metadata Shape 与 v0.4 wire-compatible。
4. record 样例中的 `dct:conformsTo` 不受 `ex:DatasetClosedShape` 约束，因为该 Closed Shape 只 target `dcat:Dataset`。ADR-001 对 v0.4 Dataset payload 的决定保持不变。
5. 后续若出现新的权威 record 要求，必须形成新的版本决定、artifact、requirements 和回归测试；不得静默改写本次继承边界。

## 依据

- D 组 TTL 的 target/path 集合和 metadata profile 说明。
- `C_Semantic_Treehouse/model/v0.3/energy-reading-record-*` 五个 record-specific artifacts。
- `C_Semantic_Treehouse/manifests/baseline-test-cases.json` 的 artifact hashes 与 record RDF/JSON-LD/SHACL/JSON Schema cases。
- `docs/v0.4/STATUS.md` 的 Phase 02 33-case host/container 等价结果。
- `docs/v0.4/STATUS.md` 的“Phase 03 — D 组契约审计、需求追踪与兼容性决策”授权边界、ADR-003 记录及风险处置，以及本次 Phase 03 用户指令。

## 后果

- v0.4 release 同时具有新的 metadata wire contract 和显式继承的 v0.3 record contract。
- record consumers 不需要因 metadata path 迁移而改变 payload。
- release manifest 必须表达跨版本继承及准确 hash，避免复制带来的虚假版本增量。
- v0.3 baseline 继续保护 record artifacts；v0.4 metadata 测试不得改写这些 oracle。

## 替代方案

### 把五个 record artifacts 复制到 `model/v0.4/`

拒绝。没有 record 语义变化时复制会制造无意义版本并增加漂移风险。

### 将 record namespace 从 `be:` 重写为 D 组 `ex:`

拒绝。D 组没有提出该要求，且两个 namespace 的 `unit` 等 IRI 含义与适用 target 不同。

### 宣称整个 v0.3 bundle 与 v0.4 兼容

拒绝。v0.3 metadata 到 v0.4 metadata 是 breaking wire-profile migration。

## 组级人工批准记录

当前用户于 2026-08-10 明确将本项目三类 ADR 审批身份改为组级可审计身份，并接受 ADR-001、ADR-002、ADR-003 的建议决定。该项目级用户决定覆盖 Phase 03 prompt 原有的自然人姓名粒度规则；三个角色仍分别记录。AI、agent 和 validator 均不是批准主体。

| 审批角色与可审计身份 | 日期 | 批准范围 | 结论 | 证据引用 |
|---|---|---|---|---|
| 项目维护方/当前用户 | 2026-08-10 | release manifest 的跨版本继承、artifact identity 和不复制策略 | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-003 记录 |
| DSSC Toolbox C 组 | 2026-08-10 | record 模型、namespace、兼容性、ontology 边界和 baseline 影响 | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-003 记录 |
| DSSC Toolbox D 组 | 2026-08-10 | D TTL 的 metadata-only 作用域及其不改变 record 子契约的解释 | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-003 记录 |
