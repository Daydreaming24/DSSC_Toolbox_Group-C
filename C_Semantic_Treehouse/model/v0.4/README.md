# Building Energy Metadata Model v0.4

本目录是 Building Energy metadata wire profile 的 v0.4 稳定发布接口。规范性约束来自 D 组冻结 Shape；ontology 和 JSON-LD 文件描述并使用该 wire profile，不能替代或弱化 SHACL 约束。

## 发布工件

| 文件 | 角色 |
|---|---|
| `building-energy-ontology.ttl` | v0.4 版本身份、breaking 边界和 D wire 本地属性的语义说明 |
| `data-product-metadata-shapes.ttl` | D 组规范性 SHACL 契约的字节级派生副本 |
| `data-product-context.jsonld` | 将稳定 JSON 字段映射到 D 组 `ex:/dcat:/dct:` paths 的本地 context |
| `data-product-valid.jsonld` | 使用 sibling context、可离线展开的 canonical valid Dataset |
| `SHA256SUMS` | 本目录发布工件的仓库相对 POSIX 路径与 SHA-256 清单；不递归列出自身 |

## 权威来源与派生

规范性来源是 `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`，SHA-256 为 `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`。解释性来源是 `inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md`，SHA-256 为 `d95a98be50641dbf4c131818547756183bf795edc426668c7c43c00f934bc7b4`。

`data-product-metadata-shapes.ttl` 采用 `byte-copy` 转换，源文件与发布文件的字节及 SHA-256 完全相同。该文件没有附加 provenance 注释、格式化或换行转换；派生证据位于 release manifest 和 `docs/v0.4/model-derivation.md`。

canonical example 的场景来源是 `inputs/original-plan/DSSC_Minimal_Energy_Scenario/metadata/data-product-valid.jsonld`，SHA-256 为 `fd64b653877fbf7df3bd9f66d482dafb576df7ce096cdb54c2f36079aa521013`。发布 example 保留场景身份和值，并通过本地 context 明确表达 v0.4 wire paths。

## 版本身份与 wire namespace

- 项目版本 IRI：`https://w3id.org/dssc-demo/building-energy/v0.4`
- prior version：`https://w3id.org/dssc-demo/building-energy/v0.3`
- D wire namespace：`ex:` = `https://example.org/dssc-energy#`
- 标准 paths：`dcat:` = `http://www.w3.org/ns/dcat#`，`dct:` = `http://purl.org/dc/terms/`

项目版本 IRI 标识发布版本；它不重写 payload 中的 wire IRI。v0.4 metadata 是从 v0.3 `be:` metadata profile 到 D 组 `dcat:Dataset` profile 的 breaking migration。历史 `be:` namespace 继续用于冻结版本和继承的 Energy Reading Record 子契约。

## `dct:conformsTo`

根据 `docs/v0.4/decisions/ADR-001-dct-conforms-to.md`，受 `ex:DatasetClosedShape` 约束的 v0.4 Dataset payload 不携带 `dct:conformsTo`。版本身份和 conformance 信息由 `C_Semantic_Treehouse/manifests/release-manifest.json` 与 provenance 承载。Dataset 若额外携带该属性，D Shape 会保留 Closed Shape Warning，并按批准的结果分类处理。

## Energy Reading Record 继承

根据 `docs/v0.4/decisions/ADR-003-energy-record-inheritance.md`，v0.4 精确继承以下五个 v0.3 record-specific artifacts，`change: none`：

| v0.3 artifact | SHA-256 |
|---|---|
| `C_Semantic_Treehouse/model/v0.3/energy-reading-record.schema.json` | `dd07414e3752bf582bf5e721009064e16d7be3e1e06d60daaad08000869ccfa9` |
| `C_Semantic_Treehouse/model/v0.3/energy-reading-record-context.jsonld` | `9727da9b8650dc444d719113a6978a3a26a59bfd1fde011a98e4c1f4b476f748` |
| `C_Semantic_Treehouse/model/v0.3/energy-reading-record-shapes.ttl` | `84d1eee9cfeecd1791117552611e83d36af7df4f3b4c783ddbd75d45bae66c9a` |
| `C_Semantic_Treehouse/model/v0.3/energy-reading-record-valid.jsonld` | `8f7509ad08fb9a62cdff1d6c904801c9421c3ce768bdd9ecb651cd480aa158e1` |
| `C_Semantic_Treehouse/model/v0.3/energy-reading-record-invalid.jsonld` | `e516f6a8e4ea811170c72e922b86ac7ea46594046704d01a55a2c8e13cd8f358` |

`C_Semantic_Treehouse/model/v0.3/openapi-fragment.yaml` 仍是 v0.3 frozen release artifact；它不扩张上述五项 record inheritance set。v0.4 不复制或改写 record 文件。

## Fixtures、harness 与 manifests

正式 fixtures 位于 `C_Semantic_Treehouse/fixtures/v0.4/**`，case 级引用和预期状态由 `C_Semantic_Treehouse/manifests/v0.4-test-cases.json` 管理，阶段完成历史由 `docs/v0.4/STATUS.md` 管理。稳定版本、artifact、hash、派生与继承关系由 `C_Semantic_Treehouse/manifests/release-manifest.json` 管理；D04 requirements 由 `C_Semantic_Treehouse/manifests/v0.4-requirements.json` 管理。
