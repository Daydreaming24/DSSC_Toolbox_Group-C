# B 组交接：v0.4 Model URI 与 Provenance

## 1. 可引用身份

B 组在 connector、policy、catalogue 或 lineage 记录中可引用下列已登记身份：

| role | value | machine source |
|---|---|---|
| Model/release IRI | `https://w3id.org/dssc-demo/building-energy/v0.4` | release manifest 的 `releases[id=v0.4].versionIri`；provenance Entity 同一 `@id` |
| Release ID / status | `v0.4` / `current` | release manifest；`current` 表示仓库当前模型 release；P00-R14 最终责任已由维护者接受，逐项审核记录仍为 `PENDING` |
| Machine profile ID | `dssc-building-energy-metadata-v0.4` | requirements 与 test-case manifest 的 `profile.id` |
| Wire-profile vocabulary URI | `https://example.org/dssc-energy#`（`ex:`） | D 组规范性 Shape 与 v0.4 context |
| Dataset class IRI | `http://www.w3.org/ns/dcat#Dataset`（`dcat:Dataset`） | D 组规范性 Shape |
| Historical record vocabulary | `https://w3id.org/dssc-demo/building-energy#`（`be:`） | 显式继承的 v0.3 Energy Reading Record 子合同 |

当前 manifests 没有声明另一个可替代 `profile.id` 的 standalone profile-document IRI。B 组应引用上表现有 model/release IRI、profile ID 与 wire namespace，避免生成未经治理的新 profile URI。

机器真源为 [release manifest](../manifests/release-manifest.json)、[requirements manifest](../manifests/v0.4-requirements.json)、[test-case manifest](../manifests/v0.4-test-cases.json) 和 [provenance JSON-LD](../governance/provenance.jsonld)。

## 2. 版本、artifact 与来源 hash

Release manifest 当前把 `v0.4` 分类为 `wire-profile-breaking`，其 prior release 为 `v0.3`。可核验引用如下：

| item | manifest ID / ref | repository path | SHA-256 |
|---|---|---|---|
| D 组规范性 Shape | `d-shape-v04` | `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` |
| D 组说明 | `d-change-note` | `inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md` | `d95a98be50641dbf4c131818547756183bf795edc426668c7c43c00f934bc7b4` |
| v0.4 ontology | `v04-ontology` | `C_Semantic_Treehouse/model/v0.4/building-energy-ontology.ttl` | `c2139583d8b2c92fbd805db49f9a30e883c1aea27cb704063c3ea9d0456df5d9` |
| v0.4 JSON-LD context | `v04-metadata-context` | `C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld` | `f46d3056239cc1cb7d678707e749b33e336564e5fce23ffcccd528eae6cbe391` |
| C 组 byte-copy Shape | `v04-metadata-shapes` | `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` |
| Canonical metadata example | `v04-metadata-valid` | `C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld` | `9acc287ae274e549becd15852231b325c43e1dbddc14e9f2459f4c490420f239` |
| Release manifest | provenance Entity role `release` | `C_Semantic_Treehouse/manifests/release-manifest.json` | `35b194fe0c280c9a01067d2c9eac205c9e178da235ba06596719144b975111d8` |
| Validation-suite registry | provenance Entity role `validation-suites` | `C_Semantic_Treehouse/manifests/validation-suites.json` | `09c74417a9b674206070ea2d25cea45ed7704f9485269eb264446f0472d51836` |

Source 与 artifact 的 hash 来自 release manifest/provenance 绑定。B 组引用时应同时保存 identifier、repository-relative path、SHA-256 和 release IRI，避免只保存易漂移的文件名。

## 3. PROV entity / activity / agent

[provenance JSON-LD](../governance/provenance.jsonld) 提供下列核心图：

| PROV role | stable `@id` | meaning and relation |
|---|---|---|
| Agent | `https://w3id.org/dssc-demo/agents/d-group` | D 组；规范性 Shape 与说明 Entity 的 `wasAttributedTo`。 |
| Agent | `https://w3id.org/dssc-demo/agents/c-group` | C 组；derivation Activity 的 `wasAssociatedWith`，v0.4 Entity 的 `wasAttributedTo`。 |
| Source Entity | `https://w3id.org/dssc-demo/building-energy/source/d-shape-v0.4` | 保存 `sourceRef`, `path`, `sha256`，绑定冻结 D Shape。 |
| Source Entity | `https://w3id.org/dssc-demo/building-energy/source/d-change-note-v0.4` | 保存 D 组解释性说明的 `sourceRef`, `path`, `sha256`。 |
| Activity | `https://w3id.org/dssc-demo/building-energy/activity/c-group-v0.4-derivation` | `activityKind: semantic-model-derivation`，`status: completed`；`used` v0.3 与两个 D source Entities，`generated` v0.4 Entity。 |
| Model Entity | `https://w3id.org/dssc-demo/building-energy/v0.4` | `compatibility: wire-profile-breaking`；`priorVersion` v0.3；`inherits` v0.3 Energy Reading Record contract。 |
| Record-contract Entity | `https://w3id.org/dssc-demo/building-energy/contract/v0.3-energy-reading-record` | 集合化表达五个 inherited record artifact；其内容与 v0.3 精确一致。 |
| Release-governance Activity | `https://w3id.org/dssc-demo/building-energy/activity/v0.4-release-approval` | `status: responsibility-accepted`；维护者已接受 P00-R14 最终责任，逐项语义、领域、D 组与发布签字仍待形成。 |

B 组构造 lineage 时可使用：

```text
D Shape Entity --used by--> C derivation Activity --generated--> v0.4 Model Entity
D Shape Entity --wasAttributedTo--> D Group
C derivation Activity --wasAssociatedWith--> C Group
v0.4 Model Entity --inherits--> v0.3 Energy Reading Record contract
```

## 4. 推荐的可引用字段

从 release manifest 引用：

- `releases[].id`, `status`, `versionIri`, `priorRelease`, `compatibilityClassification`；
- `artifacts[].id`, `role`, `path`, `mediaType`, `sha256`；
- `artifacts[].origin.type`, `sources`, `inheritedFrom`, `sourceArtifact`, `change`；
- `sourceCatalog[].id`, `kind`, `path`, `sha256`；
- `validationSuiteRegistry.path`, `contractVersion`, `sha256`。

从 provenance 引用：

- `@id`, `@type`, `title`, `description`, `status`, `compatibility`；
- `path`, `sha256`, `sourceRef`, `releaseArtifactRef`, `manifestRole`, `artifactKind`；
- `used`, `generated`, `wasGeneratedBy`, `wasDerivedFrom`, `wasAssociatedWith`, `wasAttributedTo`, `priorVersion`, `inherits`。

建议 B 组引用原字段及值，并附证据文件 path/hash。重新命名字段会降低跨组机器核验能力。

## 5. 兼容性与使用限制

- v0.3 → v0.4 metadata 是 `wire-profile-breaking` migration。v0.3 的 `be:DataProductMetadata`、paths 与 lexical values 需要显式转换后才能满足 D 组 v0.4 Shape。
- Model/release IRI `https://w3id.org/dssc-demo/building-energy/v0.4` 标识发布版本；它不改写 v0.4 payload 中的 `ex:/dcat:/dct:` wire IRIs。
- v0.4 Dataset payload 依据 [ADR-001](../../docs/v0.4/decisions/ADR-001-dct-conforms-to.md) 省略 `dct:conformsTo`；版本信息由 release manifest/provenance 承载。
- v0.3 Energy Reading Record 子合同由 [ADR-003](../../docs/v0.4/decisions/ADR-003-energy-record-inheritance.md) 精确继承，五个 record artifacts 保留 v0.3 path/hash；metadata breaking change不意味着 record payload 变更。
- 现有合同不提供 namespace alias、双路径 acceptance 或隐式 adapter。新 adapter/profile URI 需要独立 requirement、decision 与测试。
- Release manifest 的 `status: current` 表示仓库中的当前模型版本。Provenance 将人工责任记为 `responsibility-accepted`，将已有候选绑定 CI 与 GitHub repository publication 记为 `confirmed`，将 Treehouse 可选本地运行记为 `completed-local-optional`；逐项人工审核仍为 `PENDING`，Treehouse publication 与外部 SEMIC/ITB 执行仍为 `NOT RUN`。动态候选绑定统一见 `docs/v0.4/publication-record.md`。

## 6. 适用边界

这些 model URI、profile identifier、artifact hash 和 provenance relations 支持仓库内的版本识别、来源追踪、connector 引用与 validation evidence 关联。

**该信息不构成 Gaia-X 或法律合规证明。** 它也不替代数据权利、许可、隐私、安全、身份、policy enforcement、contractual obligation 或最终发布授权的专项审查。Gaia-X conformity、法律合规与外部 certification 需要各自权威规则、实际验证和具名批准证据。
