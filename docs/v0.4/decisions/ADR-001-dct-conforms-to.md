# ADR-001 — v0.4 Dataset payload 中的 `dct:conformsTo`

- 状态：`ACCEPTED`
- 决定日期：2026-08-10
- 适用范围：D 组 Shape 验证的 v0.4 metadata Dataset payload、版本声明位置、Closed Shape 结果映射和相关需求追踪
- 关联风险：`P00-R11`

## Context

v0.2/v0.3 metadata 使用 `dct:conformsTo` 携带版本声明。规范性 D 组 Shape `ex:DatasetClosedShape` 对 `dcat:Dataset` 使用 `sh:closed true`，其 allowlist 没有 `dct:conformsTo`。因此 v0.4 Dataset payload 携带该属性时会产生 `sh:Warning`。按照已冻结的四状态优先级，在没有 Violation 时，该 Warning 映射为 `INAPPLICABLE`；同时存在 Violation 时映射为 `FAIL`。

D 组 TTL 是规范性可执行契约。收到的 TTL、说明和历史 v0.1–v0.3 artifact 均保持不变。

契约审计还发现 `D04-R002` 的来源 `ex:BuildingEnergyDatasetShape` 是 NodeShape 级 `sh:nodeKind sh:IRI` 约束。该 Shape 没有 `sh:path`，也没有显式 `sh:message`。pySHACL 可能生成默认诊断文本，该文本不属于 D 组 TTL 的规范消息。

## Decision

1. 由 D 组 Shape 验证的 v0.4 `dcat:Dataset` payload 不携带 `dct:conformsTo`。
2. v0.4 版本身份和 conformance 信息进入 Phase 04 的 release manifest 与 provenance，不进入受 `ex:DatasetClosedShape` 约束的 Dataset payload。
3. 如果 SUT 的 Dataset payload 携带 `dct:conformsTo`，不得修改或适配 D 组 Shape 来隐藏结果：
   - 只有获准映射的 `ex:DatasetClosedShape` Warning、没有 Violation时，业务状态为 `INAPPLICABLE`；
   - 同时存在任何 `sh:Violation` 时，业务状态为 `FAIL`。
4. `D04-R002` 的机器追踪必须忠实表示 TTL：source path 为不适用，显式 source message 集合为空。引擎默认消息只可作为非规范诊断，不得进入规范 oracle 或伪装成 TTL 来源消息。
5. 四状态及程序 `ERROR` 的完整优先级以 `docs/v0.4/result-classification.md` 为准。

## 依据

- `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl` 中 `ex:DatasetClosedShape` 的 target、closed 声明、allowlist、severity 和 message。
- `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl` 中 `ex:BuildingEnergyDatasetShape` 的 NodeKind 约束及其缺失的显式 path/message。
- `docs/v0.4/risk-register.md` 的 `P00-R11`。
- `docs/v0.4/STATUS.md` 的“Phase 03 — D 组契约审计、需求追踪与兼容性决策”授权边界、ADR-001 记录及风险处置，以及本次 Phase 03 用户指令。

## 后果

- v0.3 metadata payload 不能原样作为 v0.4 wire payload；迁移必须移除 payload 中的 `dct:conformsTo`，并采用 v0.4 paths/value constraints。
- 版本治理仍可审计，版本身份由 release manifest/provenance 承载。
- Closed Shape 的实际 Warning 被保留，harness 可以确定性地区分 `INAPPLICABLE` 与 `FAIL`。
- requirements registry 和报告断言不会把 pySHACL 的默认文本误写成 D 组规范消息。

## 替代方案

### 将 `dct:conformsTo` 加入 D 组 allowlist

拒绝。该方案会修改或弱化冻结的规范性 D 组契约。

### 保留 payload 中的 `dct:conformsTo` 并把 Warning 忽略为 PASS

拒绝。该方案与 D 组明确的 Closed Shape 和四状态映射冲突。

### 复制 v0.3 metadata 并继续使用旧版本声明方式

拒绝。v0.3→v0.4 已确认为 wire-profile breaking migration。

## 组级人工批准记录

当前用户于 2026-08-10 明确将本项目三类 ADR 审批身份改为组级可审计身份，并接受 ADR-001、ADR-002、ADR-003 的建议决定。该项目级用户决定覆盖 Phase 03 prompt 原有的自然人姓名粒度规则；三个角色仍分别记录。AI、agent 和 validator 均不是批准主体。

| 审批角色与可审计身份 | 日期 | 批准范围 | 结论 | 证据引用 |
|---|---|---|---|---|
| 项目维护方/当前用户 | 2026-08-10 | 仓库与发布决策；Dataset payload 移除 `dct:conformsTo`，版本信息转入 release manifest/provenance | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-001 记录 |
| DSSC Toolbox C 组 | 2026-08-10 | metadata 模型兼容性、版本声明位置，以及 `D04-R002` source path/message 的忠实表示 | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-001 记录 |
| DSSC Toolbox D 组 | 2026-08-10 | D TTL、Closed Shape、四状态映射，以及 NodeShape 级 NodeKind 结果的解释 | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-001 记录 |
