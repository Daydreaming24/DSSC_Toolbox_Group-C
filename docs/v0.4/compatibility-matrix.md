# v0.3→v0.4 兼容性矩阵

## 结论

v0.4 metadata 是 wire-profile breaking migration。v0.4 继续沿项目既定版本序列命名；项目版本 IRI 只标识版本，不重写 D 组 `ex:/dcat:/dct:` wire paths。规范决定见 `decisions/ADR-001-dct-conforms-to.md` 和 `decisions/ADR-002-wire-profile-and-version-identity.md`。

Energy Reading Record 位于独立边界：它精确继承 v0.3 record 子契约，不随 metadata wire profile 改版，见 `decisions/ADR-003-energy-record-inheritance.md`。

## Metadata wire profile

| 规则 | v0.3 | v0.4 wire profile | 影响 | 迁移义务 |
|---|---|---|---|---|
| `D04-R001` | 无提交图 Dataset 数量约束 | 图中必须恰好一个 `dcat:Dataset` | 新的图级约束 | harness 必须显式执行固定 `ex:ValidationSubmission` target，并覆盖 0/1/2+ Dataset |
| `D04-R002` | metadata 样例为有 IRI 的 `be:DataProductMetadata`，旧 Shape 未显式约束节点种类 | Dataset 必须是 IRI | 约束增强 | blank Dataset 必须 FAIL；该 NodeShape 约束无 source path、无显式 source message |
| type | `be:DataProductMetadata`（ontology 中为 `dcat:Dataset` 子类） | 显式 `dcat:Dataset` | wire type 改变 | payload 直接使用 `dcat:Dataset`；不得依赖推理获得 target |
| `D04-R003` | `dct:identifier` | `ex:datasetId` | path 改变 | 改用 D 组 `ex:` IRI，并满足单值、string、非空白约束 |
| `D04-R004` | 旧 metadata Shape 无显式 title 要求 | `dct:title` 必填 | 新必填字段 | 增加单值、非空白 `xsd:string` title |
| `D04-R005` | `be:providerName` | `ex:providerName` | path 与严格度改变 | 改 path，并满足单值、string、非空白约束 |
| `D04-R006` | `be:spatialCoverage` | `dct:spatial` | path 与严格度改变 | 改 path，并满足单值、string、非空白约束 |
| `D04-R007` | `be:frequency = "hourly"` | `dct:accrualPeriodicity = "hourly"` | path 改变，类型/单值约束增强 | 精确、区分大小写地使用 `hourly` |
| `D04-R008` | `be:unit = "kWh"` | `ex:unit = "kWh"` | path 改变，类型/单值约束增强 | 不得把 v0.3 `be:unit` 当作 D `ex:unit` |
| `D04-R009` | `be:format = "JSON"` | `dct:format = "application/json"` | path和值改变 | 使用准确 media type 字符串 |
| `D04-R010` | `be:endpointUrl`，IRI | `dcat:endpointURL`，HTTPS IRI | path 与 scheme 强度改变 | 使用单一 `https://` IRI |
| `D04-R011` | `be:temporalStart`，`xsd:date` | `ex:temporalStart`，`xsd:date` | path 改变 | 改用 D `ex:` path，保持单值准确 datatype |
| `D04-R012` | `be:temporalEnd`，`xsd:date` | `ex:temporalEnd`，`xsd:date` | path 改变 | 改用 D `ex:` path，保持单值准确 datatype |
| `D04-R013` | 无 start/end 顺序约束 | `temporalStart <= temporalEnd` | 新跨字段约束 | 相等允许，倒序 FAIL |
| `D04-R014` | 旧 Shape 未声明 `dct:description` | 可省略；出现时最多一个 `xsd:string` | 显式可选 profile 补充 | 缺省可通过；多值或错误 datatype FAIL |
| `D04-R015` | 旧 Shape 未声明 `dct:license` | 可省略；出现时最多一个 HTTPS IRI | 显式可选 profile 补充 | 缺省可通过；多值、非 IRI 或非 HTTPS FAIL |
| `D04-R016` | 未使用 Closed Shape；样例含 `dct:conformsTo` | Dataset Closed Shape allowlist 不含 `dct:conformsTo` | profile 外字段产生 Warning | v0.4 Dataset payload 移除 `dct:conformsTo`；额外字段单独出现映射 `INAPPLICABLE`，与 Violation 共存映射 `FAIL` |
| `D04-R017` | 旧流程未形成四状态受控故障合同 | SUT parse/load 或受控 runtime fault 可映射 `UNTESTABLE` | harness 合同改变 | 仅在权威合同、manifest、harness 和依赖预检成功后应用；权威输入或 harness 故障为程序 `ERROR` |

## Namespace 与版本身份

| 层次 | 固定身份 | 兼容性规则 |
|---|---|---|
| D wire vocabulary | `ex:` = `https://example.org/dssc-energy#`，以及标准 `dcat:`/`dct:` | 直接执行 D TTL；不得重写成项目 `be:` paths |
| 历史项目 vocabulary | `be:` = `https://w3id.org/dssc-demo/building-energy#` | 保留给 v0.1–v0.3 baseline 和继承的 record 子契约 |
| v0.4 版本身份 | `https://w3id.org/dssc-demo/building-energy/v0.4` | 由 release manifest/provenance 表达；不进入受 Closed Shape 约束的 Dataset payload，不改变 wire paths |

## Energy Reading Record 继承边界

D 组输入中没有 Energy Reading Record target 或字段约束。下列 artifact 继续以 v0.3 identity 使用：

| artifact | v0.3 合同与 v0.4 D metadata 的关系 |
|---|---|
| `energy-reading-record-context.jsonld` | 保持 `be:EnergyReadingRecord` 与 record `be:*` paths；不映射到 D `ex:*` |
| `energy-reading-record-shapes.ttl` | target 仍为 `be:EnergyReadingRecord`；与 D 的 `dcat:Dataset` target 分离 |
| `energy-reading-record.schema.json` | 继续验证 record JSON payload；不承担 v0.4 metadata wire validation |
| `energy-reading-record-valid.jsonld` | 保持 v0.3 正例和 `dct:conformsTo`；Dataset Closed Shape 不以该 record 为 target |
| `energy-reading-record-invalid.jsonld` | 保持 v0.3 负例 oracle；不因 metadata 迁移改写 expected |

Phase 04 release manifest 必须显式引用上述 v0.3 artifacts 及其 SHA-256。整个 v0.3 metadata/ontology bundle不具有 v0.4 wire compatibility；继承声明只覆盖准确的 record 子契约和其 v0.3 provenance/dependency。

## 验证与追踪真源

本矩阵是人类可读的兼容性审计。D 组 TTL 是 v0.4 规范约束真源；`C_Semantic_Treehouse/manifests/v0.4-requirements.json` 是 Phase 03 requirement/test-obligation 的机器真源。两者不一致时 traceability suite 必须非零失败，不能由本文件形成第二套 oracle。
