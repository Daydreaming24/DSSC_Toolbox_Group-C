# v0.4 Model Derivation

## 派生边界

v0.4 metadata 的规范性可执行真源是 `inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`，SHA-256 `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`。说明文件 `inputs/d-group/v0.4/received/初始TTL到最终TTL修改说明.md` 的 SHA-256 是 `d95a98be50641dbf4c131818547756183bf795edc426668c7c43c00f934bc7b4`，只用于解释。

版本与兼容边界由三份已接受决定固定：

| 决定 | SHA-256 | 派生影响 |
|---|---|---|
| `docs/v0.4/decisions/ADR-001-dct-conforms-to.md` | `1f32a23a955cedc4c4b06a10a3ea82efd4ad2be3890562193838ac706b18988a` | Dataset payload 移除 `dct:conformsTo` |
| `docs/v0.4/decisions/ADR-002-wire-profile-and-version-identity.md` | `fcefb0a0aa615cc194d7077b2a20f0dcd62a19d446c163abe8adb8b8d39aa759` | D wire IRI 与项目 version IRI 分层；metadata breaking migration |
| `docs/v0.4/decisions/ADR-003-energy-record-inheritance.md` | `d1bdfe0a533261bcff6bad0306c0436de7c6a415db19decf159dc34993729286` | 五项 v0.3 record-specific artifacts 原样继承 |

项目版本 IRI 是 `https://w3id.org/dssc-demo/building-energy/v0.4`，prior version 是 `https://w3id.org/dssc-demo/building-energy/v0.3`。D wire namespace 是 `https://example.org/dssc-energy#`；二者承担不同身份，不互相替换。

## 发布工件派生记录

| target | 来源 | transformation | source SHA-256 | target SHA-256 |
|---|---|---|---|---|
| `C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl` | D 组规范 TTL | `byte-copy` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` | `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda` |
| `C_Semantic_Treehouse/model/v0.4/building-energy-ontology.ttl` | D TTL、ADR-002/003、v0.3 ontology、版本命名政策 | `manual-semantic-derivation` | D `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`; ADR-002 `fcefb0a0aa615cc194d7077b2a20f0dcd62a19d446c163abe8adb8b8d39aa759`; ADR-003 `d1bdfe0a533261bcff6bad0306c0436de7c6a415db19decf159dc34993729286`; v0.3 ontology `b3081a4ea960e7b90f4a2e836e99dfa092f29346106cd1e2b9f7c58b0d598e7d`; version policy `4fc4d5d656e7519cbb065d232a9d68f16469cedec69a732d7c787af74c21d26a` | `c2139583d8b2c92fbd805db49f9a30e883c1aea27cb704063c3ea9d0456df5d9` |
| `C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld` | D TTL 与原始 valid inline context | `manual-context-derivation` | D `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`; original valid `fd64b653877fbf7df3bd9f66d482dafb576df7ce096cdb54c2f36079aa521013` | `f46d3056239cc1cb7d678707e749b33e336564e5fce23ffcccd528eae6cbe391` |
| `C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld` | 原始 valid metadata、v0.4 local context、ADR-001/002 | `manual-example-derivation` | original valid `fd64b653877fbf7df3bd9f66d482dafb576df7ce096cdb54c2f36079aa521013`; local context `f46d3056239cc1cb7d678707e749b33e336564e5fce23ffcccd528eae6cbe391`; ADR-001 `1f32a23a955cedc4c4b06a10a3ea82efd4ad2be3890562193838ac706b18988a`; ADR-002 `fcefb0a0aa615cc194d7077b2a20f0dcd62a19d446c163abe8adb8b8d39aa759` | `9acc287ae274e549becd15852231b325c43e1dbddc14e9f2459f4c490420f239` |
| `C_Semantic_Treehouse/model/v0.4/README.md` | D 输入、三份 ADR、release/fixture 边界 | `manual-documentation` | D `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`; explanation `d95a98be50641dbf4c131818547756183bf795edc426668c7c43c00f934bc7b4`; ADR hashes见上文 | `388e4dd823c60b55772946eb7fa37e90c2e5cf52e8300b784bba29ae4364873c` |
| `C_Semantic_Treehouse/model/v0.4/SHA256SUMS` | 上述五个发布工件的最终字节 | `sha256-posix-path-list` | `388e4dd823c60b55772946eb7fa37e90c2e5cf52e8300b784bba29ae4364873c`; `c2139583d8b2c92fbd805db49f9a30e883c1aea27cb704063c3ea9d0456df5d9`; `f46d3056239cc1cb7d678707e749b33e336564e5fce23ffcccd528eae6cbe391`; `a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`; `9acc287ae274e549becd15852231b325c43e1dbddc14e9f2459f4c490420f239` | `66cd79dd5cd05299c6a07010b087b4da87b138045223aa39449548ea7c46484a` |

release manifest 对所有实际引用使用完整 64 位 SHA-256。

## D Shape byte-copy 证明

- source：`inputs/d-group/v0.4/received/building-energy-shapes_D.ttl`
- target：`C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl`
- source/target size：`10375` bytes
- source/target SHA-256：`a556039c0ec3030a9c4273c62a787e448b8869f7648e948663e10d3fe007cbda`
- byte comparison：完全相同
- serialization：UTF-8、无 BOM、LF、文件末尾含 LF
- Git attribute：`C_Semantic_Treehouse/model/v0.4/data-product-metadata-shapes.ttl: text: unset`

目标文件没有加入 provenance 注释、version triple、格式化或换行转换。`.gitattributes` 只对该精确 target 设置 `-text`。

## Context 字段映射

| compact term | expanded IRI | coercion |
|---|---|---|
| `Dataset` | `dcat:Dataset` | type IRI |
| `datasetId` | `ex:datasetId` | string |
| `title` | `dct:title` | string |
| `description` | `dct:description` | string |
| `providerName` | `ex:providerName` | string |
| `license` | `dct:license` | `@id` |
| `spatial` | `dct:spatial` | string |
| `frequency` | `dct:accrualPeriodicity` | string |
| `unit` | `ex:unit` | string |
| `temporalStart` | `ex:temporalStart` | `xsd:date` |
| `temporalEnd` | `ex:temporalEnd` | `xsd:date` |
| `endpointUrl` | `dcat:endpointURL` | `@id` |
| `format` | `dct:format` | string |

context 不定义 `be:` alias 或 `conformsTo` compact term。IRI/date coercion 与 D Shape 的 `sh:nodeKind`、`sh:datatype` 和 HTTPS constraints 对齐。

## Ontology 人工派生审查点

1. ontology subject 与 `owl:versionIRI` 都是 `https://w3id.org/dssc-demo/building-energy/v0.4`，并以 `owl:priorVersion` 指向 v0.3。
2. `dct:description` 明确 metadata wire-profile breaking migration，同时限定 v0.3 record 子契约不变。
3. 直接复用 `dcat:Dataset`；只声明 D wire 使用的五个本地属性：`ex:datasetId`、`ex:providerName`、`ex:unit`、`ex:temporalStart`、`ex:temporalEnd`。
4. 每个本地属性都有最小 label、comment、`rdfs:domain dcat:Dataset` 和准确 range；没有 `be:` path、双路径 alias、`owl:imports` 或会产生额外 payload path 的 subproperty adapter。
5. ontology 不复述 cardinality、enumeration、HTTPS、顺序或 Closed Shape constraints；规范约束始终由 byte-copy Shape提供。

## Canonical example 人工派生审查点

canonical example 将原始 valid metadata 的 inline context 换成本地 sibling context，保留 Dataset IRI、场景 Dataset ID、标题、描述、provider、endpoint、空间、日期和 license。`format` 为 `application/json`、`frequency` 为 `hourly`、`unit` 为 `kWh`，日期顺序合法。展开图恰好包含一个 IRI `dcat:Dataset` 和十三个 triples；没有 `dct:conformsTo` 或 Closed Shape allowlist 外的 Dataset property。

## Requirements implementation 引用

`D04-R001`–`D04-R017` 的 Phase 03 source semantics、path、severity、message、expected statuses 和 test obligations 保持不变。Phase 03 registry SHA-256 是 `67391a561c61aa540535463df371e2aa5a0c4f8fff93b45c52a18b0067258ae1`；补充 implementation refs 后的 SHA-256 是 `53953e915d6da6159b342a04f1dc6d0ff6a8f53bd5892eb7933551710ebe014e`。

机器比较先从每条 requirement 删除 `implementation`，再使用 `sort_keys=true`、`separators=(',', ':')`、`ensure_ascii=false` 的 UTF-8 canonical JSON 和末尾 LF。Phase 03 与 Phase 04 投影均为 79,254 bytes，SHA-256 均为 `8a6d4bee6c06623915e4fa2664d465b666e087db9caf0b315ef2f5831bd0e3fe`，语义字段零变化。

R001–R016 的 Phase 04 refs 指向 byte-copy Shape，并按规则需要引用 ontology/context；R017 同时引用 Shape 与 `scripts/dssc_validation/model_contract.py`（SHA-256 `75e975db21b07fd2efe7210ddee4feb95682ab0821fbaaeaf4e765feda50686c`）。受保护 requirements schema 的 implementation reference 使用 path 和 description，description 内含实际 SHA-256；统一 release manifest（SHA-256 `7d75676b898fdbc00c9b1da78900054aec5f426690822e07970200b5fd88076a`）再对发布 artifacts 建立结构化 path/hash 绑定。Phase 05 fixture/evidence references 与完整四状态 harness 保持 `PLANNED`，由 test-case manifest 独立管理。

## Record inheritance 边界

继承集合严格采用 ADR-003 的五项 record-specific artifacts：JSON Schema、context、Shape、valid example、invalid example。`C_Semantic_Treehouse/model/v0.3/openapi-fragment.yaml` 继续作为 v0.3 frozen artifact 审计，不加入五项继承集合。所有继承 target 都使用原 v0.3 path/hash，`change: none`，不复制到 `model/v0.4/`。
