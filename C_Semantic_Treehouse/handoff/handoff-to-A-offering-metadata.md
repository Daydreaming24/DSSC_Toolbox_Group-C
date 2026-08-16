# A 组交接：v0.4 Offering Metadata Contract

## 1. 交接范围与真源

A 组发布 Building Energy Consumption Data Product offering 时，metadata wire payload 使用 v0.4 `dcat:Dataset` profile。字段、约束与示例的机器真源为：

- [v0.4 requirements manifest](../manifests/v0.4-requirements.json)：`D04-R001`–`D04-R017`；
- [release manifest](../manifests/release-manifest.json)：当前 release、artifact 路径、版本关系和 SHA-256；
- [v0.4 JSON-LD context](../model/v0.4/data-product-context.jsonld)：JSON key 到 IRI 的展开；
- [canonical v0.4 JSON-LD example](../model/v0.4/data-product-valid.jsonld)：release artifact `v04-metadata-valid`；
- [ADR-001](../../docs/v0.4/decisions/ADR-001-dct-conforms-to.md) 与 [ADR-002](../../docs/v0.4/decisions/ADR-002-wire-profile-and-version-identity.md)：`dct:conformsTo`、Closed Shape 和 breaking wire migration 决策。

提交图必须恰好包含一个 `dcat:Dataset`（`D04-R001`），该 Dataset focus node 必须是 IRI（`D04-R002`）。Dataset ID `building-energy-hourly-v1` 是业务标识，与模型版本 `v0.4` 分属不同命名层。

## 2. v0.4 字段合同

下表逐行转录 requirements manifest 中的 12 个属性规则。`ex:` 精确表示 `https://example.org/dssc-energy#`。

| requirement_id | required | IRI | JSON key | datatype / node kind | cardinality | allowed value |
|---|---:|---|---|---|---|---|
| `D04-R003` | `true` | `ex:datasetId` | `datasetId` | `xsd:string` | `1..1` | 至少 1 个字符并匹配 `\S`，即至少含一个非空白字符 |
| `D04-R004` | `true` | `dct:title` | `title` | `xsd:string` | `1..1` | 至少 1 个字符并匹配 `\S`，即至少含一个非空白字符 |
| `D04-R005` | `true` | `ex:providerName` | `providerName` | `xsd:string` | `1..1` | 至少 1 个字符并匹配 `\S`，即至少含一个非空白字符 |
| `D04-R006` | `true` | `dct:spatial` | `spatial` | `xsd:string` | `1..1` | 至少 1 个字符并匹配 `\S`，即至少含一个非空白字符 |
| `D04-R007` | `true` | `dct:accrualPeriodicity` | `frequency` | `xsd:string` | `1..1` | `hourly`，精确且大小写敏感 |
| `D04-R008` | `true` | `ex:unit` | `unit` | `xsd:string` | `1..1` | `kWh`，精确且大小写敏感 |
| `D04-R009` | `true` | `dct:format` | `format` | `xsd:string` | `1..1` | `application/json`，精确值 |
| `D04-R010` | `true` | `dcat:endpointURL` | `endpointUrl` | `sh:IRI` | `1..1` | IRI 字符串匹配 `^https://` |
| `D04-R011` | `true` | `ex:temporalStart` | `temporalStart` | `xsd:date` | `1..1` | 合法的 `xsd:date` lexical form |
| `D04-R012` | `true` | `ex:temporalEnd` | `temporalEnd` | `xsd:date` | `1..1` | 合法的 `xsd:date` lexical form |
| `D04-R014` | `false` | `dct:description` | `description` | `xsd:string` | `0..1` | 出现时为一个字符串 |
| `D04-R015` | `false` | `dct:license` | `license` | `sh:IRI` | `0..1` | 出现时 IRI 字符串匹配 `^https://` |

跨字段规则：

| requirement_id | fields | rule |
|---|---|---|
| `D04-R013` | `temporalStart`, `temporalEnd` | 两值均为 `xsd:date` 时，`temporalStart` ≤ `temporalEnd`；相等日期有效。 |

## 3. Canonical JSON-LD 示例

Release manifest 将示例登记为：

| artifact ID | path | SHA-256 |
|---|---|---|
| `v04-metadata-context` | `C_Semantic_Treehouse/model/v0.4/data-product-context.jsonld` | `f46d3056239cc1cb7d678707e749b33e336564e5fce23ffcccd528eae6cbe391` |
| `v04-metadata-valid` | `C_Semantic_Treehouse/model/v0.4/data-product-valid.jsonld` | `9acc287ae274e549becd15852231b325c43e1dbddc14e9f2459f4c490420f239` |

Canonical payload 为：

```json
{
  "@context": "data-product-context.jsonld",
  "@id": "https://example.org/dssc-energy/datasets/building-energy-hourly-v1",
  "@type": "Dataset",
  "datasetId": "building-energy-hourly-v1",
  "title": "Building Energy Consumption Dataset API",
  "description": "Hourly electricity consumption readings for demo buildings in a city energy data space.",
  "providerName": "Energy Data Provider Ltd.",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "spatial": "Shenzhen demo district",
  "frequency": "hourly",
  "unit": "kWh",
  "temporalStart": "2026-05-01",
  "temporalEnd": "2026-05-02",
  "endpointUrl": "https://api.example.org/energy/buildings/hourly",
  "format": "application/json"
}
```

交付 serialization 应通过同目录 context 展开为表中 IRI。`endpointUrl` 与 `license` 是 IRI-valued key；普通 JSON string 形式只有在 JSON-LD context 将其声明为 `@id` 时才形成所需 IRI node。

## 4. 运行行为

- endpoint：只接受一个 `dcat:endpointURL` IRI，scheme 必须为 HTTPS。
- format：只接受一个 `dct:format "application/json"`。
- frequency：只接受一个 `dct:accrualPeriodicity "hourly"`，值大小写敏感。
- unit：只接受一个 `ex:unit "kWh"`，值大小写敏感。
- temporal order：起止日期均为必填单值 `xsd:date`，起点可以等于终点，起点不能晚于终点。
- extra property：`ex:DatasetClosedShape` 以 `sh:Warning` 报告 allowlist 之外的 Dataset property。没有 Violation 且只有获准的 Closed Shape Warning 时，业务状态为 `INAPPLICABLE`；同时出现 Violation 时，业务状态为 `FAIL`。

## 5. v0.3 → v0.4 migration

该迁移是 release manifest 登记的 `wire-profile-breaking` 变更。A 组应对 metadata payload 做显式转换。

| v0.3 metadata | v0.4 metadata | A 组迁移动作 |
|---|---|---|
| `be:DataProductMetadata` / JSON `DataProductMetadata` | `dcat:Dataset` / JSON `Dataset` | 更换 RDF type，并保持 Dataset focus node 为 IRI。 |
| `dct:identifier` / `datasetId` | `ex:datasetId` / `datasetId` | 保留业务 ID 值，替换展开后的 IRI。 |
| 无 `title` | `dct:title` / `title` | 增加必填、单值、非空白标题。 |
| `be:providerName` / `providerName` | `ex:providerName` / `providerName` | 替换 namespace；值保持单值非空白字符串。 |
| `be:spatialCoverage` / `spatialCoverage` | `dct:spatial` / `spatial` | 同时迁移 IRI 和 JSON key。 |
| `be:frequency` / `frequency` | `dct:accrualPeriodicity` / `frequency` | 迁移 IRI，值固定为 `hourly`。 |
| `be:unit` / `unit` | `ex:unit` / `unit` | 迁移 IRI，值固定为 `kWh`。 |
| `be:format "JSON"` / `format` | `dct:format "application/json"` / `format` | 迁移 IRI，并把 lexical value 改为精确 MIME type。 |
| `be:endpointUrl` / `endpointUrl` | `dcat:endpointURL` / `endpointUrl` | 迁移 IRI，并确认它是单值 HTTPS IRI。 |
| `be:temporalStart`, `be:temporalEnd` | `ex:temporalStart`, `ex:temporalEnd` | 迁移 IRI，保留 `xsd:date`，再检查起点 ≤ 终点。 |
| 无规范字段 | 可选 `dct:description`, `dct:license` | 仅按 `0..1` datatype/node-kind 约束增加。 |
| payload `dct:conformsTo` 指向 v0.3 | v0.4 Dataset payload 省略该属性 | 在 release manifest 与 provenance 中引用 v0.4 release identity。 |

本合同不声明 v0.3/v0.4 双路径 alias。旧 payload 需要转换后才能进入 v0.4 validation。

## 6. `dct:conformsTo` 与 Closed Shape 决策

批准的处理方式固定如下：

1. 受 D 组 Shape 验证的 v0.4 Dataset payload 省略 `dct:conformsTo`。
2. 版本身份 `https://w3id.org/dssc-demo/building-energy/v0.4` 由 release manifest 和 [provenance](../governance/provenance.jsonld) 承载。
3. 若候选 payload 仍携带 `dct:conformsTo`，Closed Shape 会按 extra-property 规则产生 Warning；harness 保留该结果并按四状态优先级分类。

## 7. 发布前命令与 expected status

从仓库根目录按 host 选择一条现有受控入口：

```powershell
.\scripts\validate.ps1 -Suite v0.4
```

```bash
./scripts/validate.sh --suite v0.4
```

Expected program result：exit code `0`、`program_status: SUCCESS`、66 个 manifest case 全部 discovered/executed、0 failed、0 skipped；业务状态覆盖 `PASS: 6`、`FAIL: 53`、`INAPPLICABLE: 1`、`UNTESTABLE: 6`。当前本地机器证据见 [v0.4 results](../../build/validation/v0.4/results.json)。

该 suite 认证仓库中受 manifest/hash 绑定的 Shape、fixtures 和 oracle。A 组候选 offering 应先与本字段表及 canonical artifact 对照；需要把新候选纳入自动判定时，由 C/D 集成流程登记独立 fixture/test oracle 并复审，随后运行同一 suite。Phase 08/09 的 CI、Treehouse 和外部 SEMIC/ITB 执行当前均为 `NOT RUN`，不构成本地命令的附加成功声明。
