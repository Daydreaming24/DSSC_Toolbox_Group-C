# ADR-002 — v0.4 wire profile 与版本身份

- 状态：`ACCEPTED`
- 决定日期：2026-08-10
- 适用范围：v0.4 metadata wire paths、namespace、版本 IRI 和 v0.3→v0.4 迁移边界
- 关联决定：`ADR-001-dct-conforms-to.md`、`ADR-003-energy-record-inheritance.md`

## Context

v0.3 metadata 使用项目 `be:` vocabulary、`be:DataProductMetadata`、`dct:identifier` 和多个 `be:*` path。D 组 v0.4 TTL 直接约束 `dcat:Dataset`，并使用 `https://example.org/dssc-energy#` 下的 `ex:*` path、DCAT 和 DCTERMS path。D 组说明将这些字段描述为 C 组扁平结构；仓库实际 v0.3 wire contract 与该结构不同，因此本仓库必须把迁移登记为 breaking wire-profile migration。

项目版本 IRI 用于标识发布版本。版本身份与 payload 字段 IRI 是两个独立层次；用项目 namespace 重写 D 组 wire paths 会改变规范性契约的实际行为。

## Decision

1. D 组 TTL 中下列 IRI 是 v0.4 metadata 的规范 wire contract：

   | 语义角色 | v0.4 wire IRI |
   |---|---|
   | Dataset 类型 | `dcat:Dataset` |
   | Dataset ID | `ex:datasetId` |
   | 标题 | `dct:title` |
   | 提供方 | `ex:providerName` |
   | 空间范围 | `dct:spatial` |
   | 更新频率 | `dct:accrualPeriodicity` |
   | 单位 | `ex:unit` |
   | 时间起点/终点 | `ex:temporalStart` / `ex:temporalEnd` |
   | endpoint | `dcat:endpointURL` |
   | 格式 | `dct:format` |
   | 可选描述/许可 | `dct:description` / `dct:license` |

2. `ex:` 精确表示 `https://example.org/dssc-energy#`。不得把这些 IRI 重写成 v0.3 `https://w3id.org/dssc-demo/building-energy#` 下的 `be:*` IRI。
3. v0.4 继续沿项目既定版本序列命名；Phase 04 的 release manifest/provenance 使用项目稳定版本身份 `https://w3id.org/dssc-demo/building-energy/v0.4`，该版本 IRI不改变任何 D 组 wire path。
4. v0.3 metadata 到 v0.4 metadata 是 breaking migration。v0.3 与 v0.4 artifact 必须保持版本分离，禁止声明旧 payload 可无转换通过 D 组契约。
5. 本决定不创建双路径 profile、兼容 alias 或隐式 namespace adapter。任何后续 adapter 需要新的明确需求、独立追踪和测试。

## 依据

- `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl` 的 prefix、target、path、value 和 Closed Shape allowlist。
- `C_Semantic_Treehouse/model/v0.3/data-product-context.jsonld` 与 `data-product-metadata-shapes.ttl` 的 v0.3 type/path。
- `docs/v0.4/v0-errata.md` 第 2 项记录的 breaking wire-profile 事实。
- `docs/v0.4/STATUS.md` 的“Phase 03 — D 组契约审计、需求追踪与兼容性决策”授权边界、ADR-002 记录及风险处置，以及本次 Phase 03 用户指令。

## 后果

- Phase 04 派生的 v0.4 model/context/examples 必须精确执行 D 组 IRI 和约束。
- v0.3 artifacts 继续冻结，可用于 baseline 和显式迁移输入。
- release manifest 可以使用稳定的项目版本序列，同时明确区分版本身份与 wire vocabulary。
- A/B/D 组后续 handoff 必须把 v0.4 paths 作为 wire contract，不能仅给出项目版本 IRI。

## 替代方案

### 把 D 组 `ex:*` 全部重写为项目 `be:*`

拒绝。该方案改变规范性 Shape 的 path 和 Closed Shape allowlist。

### 同时接受 v0.3 与 v0.4 两套 paths

拒绝。当前 D 组 TTL没有双 profile 语义；静默接受两套 paths 会削弱约束并使 oracle 不确定。

### 将 v0.4 描述为 v0.3 的向后兼容增强

拒绝。type、path、必填字段、严格值和 Closed Shape 均发生破坏性变化。

## 组级人工批准记录

当前用户于 2026-08-10 明确将本项目三类 ADR 审批身份改为组级可审计身份，并接受 ADR-001、ADR-002、ADR-003 的建议决定。该项目级用户决定覆盖 Phase 03 prompt 原有的自然人姓名粒度规则；三个角色仍分别记录。AI、agent 和 validator 均不是批准主体。

| 审批角色与可审计身份 | 日期 | 批准范围 | 结论 | 证据引用 |
|---|---|---|---|---|
| 项目维护方/当前用户 | 2026-08-10 | 仓库版本序列、v0.4 发布身份和 breaking migration 决策 | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-002 记录 |
| DSSC Toolbox C 组 | 2026-08-10 | 模型 namespace、版本 IRI、v0.3/v0.4 兼容边界和派生模型义务 | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-002 记录 |
| DSSC Toolbox D 组 | 2026-08-10 | D TTL 中 `ex:/dcat:/dct:` wire paths 的规范解释及禁止重写 | 批准 | 本次 Phase 03 用户指令；`docs/v0.4/STATUS.md` Phase 03 授权边界与 ADR-002 记录 |
