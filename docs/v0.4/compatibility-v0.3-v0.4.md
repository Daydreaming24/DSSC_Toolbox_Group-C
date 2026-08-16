# v0.3 → v0.4 Compatibility

## 结论

v0.4 metadata 是 wire-profile breaking migration。项目版本 IRI `https://w3id.org/dssc-demo/building-energy/v0.4` 标识发布身份；payload 直接执行 D 组 `ex:/dcat:/dct:` wire paths。Energy Reading Record 精确继承 v0.3 子契约，`change: none`。

## Metadata payload 迁移

| 语义 | v0.3 wire | v0.4 wire / value | 升级动作 |
|---|---|---|---|
| type | `be:DataProductMetadata` | `dcat:Dataset`，且节点必须是 IRI | 改为直接声明 `dcat:Dataset`；不得依赖 subclass inference |
| Dataset ID | `dct:identifier` | `ex:datasetId` | 改 path；保持一个非空白 string |
| title | 旧 Shape 未要求 | `dct:title` | 增加一个非空白 string |
| provider | `be:providerName` | `ex:providerName` | 改 path；保持一个非空白 string |
| spatial | `be:spatialCoverage` | `dct:spatial` | 改 path；保持一个非空白 string |
| frequency | `be:frequency` | `dct:accrualPeriodicity = "hourly"` | 改 path；使用大小写敏感的精确值 |
| unit | `be:unit` | `ex:unit = "kWh"` | 改 namespace；不得把 record 的 `be:unit` 当作 metadata `ex:unit` |
| format | `be:format = "JSON"` | `dct:format = "application/json"` | 同时转换 path 与值 |
| endpoint | `be:endpointUrl` | `dcat:endpointURL` | 改 path；使用单一 HTTPS IRI |
| temporal start/end | `be:temporalStart` / `be:temporalEnd` | `ex:temporalStart` / `ex:temporalEnd` | 改 namespace；使用单一 `xsd:date`，并保证 start ≤ end |
| description | 旧 Shape 未声明 | 可选 `dct:description` | 若提供，使用最多一个 string |
| license | 旧 Shape 未声明 | 可选 `dct:license` | 若提供，使用最多一个 HTTPS IRI |
| version marker | Dataset 上的 `dct:conformsTo` | 不进入受 Closed Shape 约束的 Dataset | 将版本身份转移到 release manifest/provenance |
| graph/profile boundary | 无全图数量和 Closed Shape 合同 | 恰好一个 Dataset；只允许十二个声明 path | 每次提交隔离 data graph；移除 profile 外 Dataset 属性 |

旧 payload 未经上述转换不能声明符合 v0.4。v0.4 没有双路径 profile、兼容 alias 或隐式 namespace adapter。

## A 组与 D 组集成影响

A 组 offering metadata 应发送 v0.4 wire paths 和严格值，并在 offering/release provenance 层携带版本身份。只提供项目 version IRI 不能替代 payload path 清单。

D 组验证继续直接使用字节保持的 `data-product-metadata-shapes.ttl`。C 组 context 只提供 JSON-LD compact-term 映射，ontology 只提供语义说明；二者都不改写 Shape path、severity、message 或 allowlist。完整跨组 handoff 由 Phase 07 handoff 文档维护。

## Energy Reading Record 不变范围

以下五个 v0.3 artifact 以原 path、原 SHA-256 和 `change: none` 继承：

- `energy-reading-record.schema.json`
- `energy-reading-record-context.jsonld`
- `energy-reading-record-shapes.ttl`
- `energy-reading-record-valid.jsonld`
- `energy-reading-record-invalid.jsonld`

record type 仍为 `be:EnergyReadingRecord`，record properties 仍使用 `be:*`；record example 中的 `dct:conformsTo` 不受只 target `dcat:Dataset` 的 `ex:DatasetClosedShape` 约束。`C_Semantic_Treehouse/model/v0.3/openapi-fragment.yaml` 保持 v0.3 frozen release identity，不属于上述五项继承集合。整个 v0.3 ontology/metadata bundle不具有 v0.4 wire compatibility。

## Payload 版本标记策略

v0.4 Dataset payload 通过实际 `dcat:Dataset` type、D wire paths 和 release-manifest-bound artifact identity确定其 profile。项目 release manifest/provenance 记录 `currentRelease = v0.4`、version IRI、prior release、normative D source 和 artifact hashes。需要在协议层传递版本时，应使用 Dataset payload 外的 offering、HTTP 或 envelope metadata，并由后续 handoff 明确字段；不能向 Closed Dataset 添加未经声明属性。
