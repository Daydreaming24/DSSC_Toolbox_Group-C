# DSSC C组项目报告

## 项目总览

这个项目是通过大语言模型（codex）搭建出来的。分为10个步骤（phase00-phase09），对应给codex的10个阶段指令。

本次DSSC的总场景为：“一个能源数据提供方 `Energy Data Provider Ltd.` 在 data space 中发布建筑小时级用电量数据；数据消费者 `City Analytics Lab` 发现并申请访问；data space authority 要求该数据产品具备共同语义模型、基础 trust/compliance 描述，并通过 metadata validation。”我们C组的主要学习任务是理解 data space 中共同语义模型如何被定义、维护、发布和治理。

具体来说，就是要建立 `Building Energy Consumption` semantic model。先建模 data product metadata 字段：`datasetId`、`providerName`、`endpointUrl`、`format`、`frequency`、`unit`、`spatialCoverage`、`temporalStart`、`temporalEnd`，然后为了后续进行版本模型化，又可以再建模 API record 字段：`buildingId`、`meterId`、`timestamp`、`energyKWh`、`unit`、`location`。一共分成3个版本：v0.1包含metadata基础字段，v0.2增加unit和temporal coverage约束，v0.3拓展API record schema。然后导出或对照SHACL，最后把模型交给D组做validation。不过，实际上在仓库中C组已经建立了几个验证的模型，并已经对各个版本进行了验证。

下面按照项目的搭建顺序，依次讲解phase00-phase09所做的工作。

## Phase00

第0阶段主要是为之后的所有阶段“铺路”。创建了项目目录，以及写入了项目目标和统一场景。这样之后的codex窗口就可以进行“接力”完成，不会因为上下文窗口限制而出现目标漂移等问题。同时，做了"plan B"的操作：因为当时并不清楚semantic treehouse能否在本地部署，因此额外设计了“本地验证”轨道，这样即使之后本地部署出了问题，之后也可以通过自己的python脚本来检验各个版本是否可行/不可行。第0阶段还写了makefile，便于之后阶段进行统一运行和调试。

## Phase01

Phase 01实际上几乎已经完成了C组的全部工作。v0.1, v0.2, v0.3三个版本的模型都在这个阶段进行创建。下面分别对这3个版本进行讲解。

### Phase01 - v0.1

v0.1版本添加了metadata的几个核心字段。由于本项目的数据产品是”Building Energy Consumption Data Product“，v0.1只添加了最核心的5个字段：

| 字段 | 含义 |
|---|---|
| `datasetId` | 数据产品的标识符。 |
| `providerName` | 数据提供方名称。 |
| `format` | 数据格式，例如 `JSON`。 |
| `frequency` | 数据更新或采样频率，例如 `hourly`。 |
| `spatialCoverage` | 数据覆盖的地理范围。 |

v0.1内共有4个文件：

```
C_Semantic_Treehouse/model/v0.1/
  building-energy-ontology.ttl
  data-product-context.jsonld
  data-product-metadata-shapes.ttl
  data-product-valid.jsonld
```

其中`building-energy-ontology.ttl`是语义词汇表。它说明模型中有哪些概念和属性，以及这些词汇的含义。在 v0.1 中，它定义了 `DataProductMetadata` 这个核心类，以及 `providerName`、`format`、`frequency` 和 `spatialCoverage` 四个项目属性。它还声明了模型版本，并把 `DataProductMetadata` 与标准的 `dcat:Dataset` 概念关联起来。

`data-product-context.jsonld` 是 JSON 字段与 RDF 语义词汇之间的翻译表。它让我们可以继续使用简短、易读的 JSON 字段名，同时让机器知道每个字段对应的完整语义标识。例如，`datasetId` 对应标准属性 `dct:identifier`，`providerName` 对应本项目定义的 `be:providerName`。

`data-product-metadata-shapes.ttl` 是 v0.1 的数据检查清单，使用 SHACL 编写。它规定一份合格的 `DataProductMetadata` 必须包含 `datasetId`、`providerName`、`format`、`frequency` 和 `spatialCoverage`。这五个字段都必须出现一次，并且值必须是字符串。如果数据缺少字段、字段重复或类型不正确，验证工具就会报告错误。

`data-product-valid.jsonld` 是一份符合 v0.1 要求的示例数据。它描述了一个按小时更新的建筑能耗数据产品，并填写了提供方、格式和覆盖区域等信息。文件通过 `@context` 使用前面的字段映射，并通过 `conformsTo` 表明自己遵循 v0.1 模型。它也可以作为 SHACL 验证的测试输入。

### Phase01 - v0.2

`model/v0.2` 是在 v0.1 基础上发展出来的第二个模型版本。它的核心目标是把 v0.1 的“基础 data product metadata 描述”推进成一个更适合 onboarding validation 的语义合同。v0.2相比v0.1又新增了4个字段：

| v0.2 新增字段 | 含义 |
|---|---|
| `endpointUrl` | 数据产品 API endpoint |
| `unit` | 能耗单位 |
| `temporalStart` | 数据时间覆盖起点 |
| `temporalEnd` | 数据时间覆盖终点 |

因此，v0.2 开始让 metadata 具备更强的工程可用性，因为它加入了 API endpoint、单位、时间覆盖范围和更严格的枚举约束。但v0.2 的模型仍然只关注 data product metadata，还没有进入 API record payload。此外，v0.2相比v0.1，有5个文件，新增了一个失败案例`data-product-invalid.jsonld`：
```
C_Semantic_Treehouse/model/v0.2/
  building-energy-ontology.ttl
  data-product-context.jsonld
  data-product-metadata-shapes.ttl
  data-product-valid.jsonld
  data-product-invalid.jsonld
```

`data-product-invalid.jsonld`缺少 `providerName` 和 `temporalEnd`，并把只能为 `kWh` 的 `unit` 写成了 `MWh`。

### Phase01 - v0.3

v0.3 是三个版本中最完整的一版。它保留了 v0.2 的数据产品元数据合同，同时新增了 API 返回的单条建筑能耗记录模型。因此，它既说明“数据产品怎样被描述”，也说明“数据产品实际返回的数据应该是什么样”。v0.3共有10个文件：

```
C_Semantic_Treehouse/model/v0.3/
  building-energy-ontology.ttl
  data-product-context.jsonld
  data-product-metadata-shapes.ttl
  data-product-valid.jsonld
  energy-reading-record-context.jsonld
  energy-reading-record-shapes.ttl
  energy-reading-record-valid.jsonld
  energy-reading-record-invalid.jsonld
  energy-reading-record.schema.json
  openapi-fragment.yaml
```

这10个文件可以分成共同语义层、元数据层和能耗记录层。

1. 共同语义层：`building-energy-ontology.ttl`

   这是整个 v0.3 的语义词汇表。除了原有的 `DataProductMetadata`，它还定义了 `EnergyReadingRecord`、`Building` 和 `Meter`，以及建筑编号、仪表编号、时间、能耗值和地点等属性。文件还把这些概念与 DCAT、SOSA、QUDT 和 Schema.org 等标准词汇关联起来。例如，能耗记录被视为一种 SOSA observation，仪表被视为一种 sensor。它负责统一解释元数据和能耗记录中的概念。

2. 元数据层：
   `data-product-context.jsonld`是元数据字段的 JSON-LD 翻译表。它把 `datasetId`、`endpointUrl`、`temporalStart` 等易读的 JSON 字段映射到完整的语义标识，并说明 URL 和日期等字段的类型。
   `data-product-metadata-shapes.ttl`是元数据的 SHACL 检查清单，基本延续 v0.2 的规则。它要求九个元数据字段完整且单值，并检查 URL、日期、格式、频率和单位是否符合要求。
   `data-product-valid.jsonld`是一份能够通过元数据验证的正例。它描述数据产品的提供方、API 地址、格式、频率、单位、空间范围和时间范围，并声明自己遵循 v0.3。

3. 能耗记录层：

   `energy-reading-record-context.jsonld`是能耗记录字段的 JSON-LD 翻译表。它解释 `buildingId`、`meterId`、`timestamp`、`energyKWh`、`unit` 和 `location` 等字段的语义，并把时间标记为日期时间、能耗值标记为十进制数。
   `energy-reading-record-shapes.ttl`是能耗记录的 SHACL 检查清单。每条记录必须包含建筑编号、仪表编号、时间、能耗值、单位和地点；能耗值不能小于零，单位必须是 `kWh`，时间必须是正确的日期时间。
   `energy-reading-record-valid.jsonld`是一条合格的能耗记录正例。它表示某栋建筑的某个仪表在指定时间记录了 `12.4 kWh`，并给出了城市和行政区。
   `energy-reading-record-invalid.jsonld`是一条故意写错的反例。它缺少 `meterId`，时间格式错误，把能耗值写成字符串，并使用了不允许的 `MWh` 单位。它用来确认验证工具能够识别错误记录。
   `energy-reading-record.schema.json`是面向普通 JSON API 数据的结构检查规则。它同样要求六个核心字段，检查时间、非负数值和固定单位，并进一步要求 `location` 中包含 `city` 和 `district`。它还禁止未定义的额外字段。SHACL 主要检查转换成 RDF 后的语义数据，而 JSON Schema 可以直接检查普通 JSON 请求或响应。
   `openapi-fragment.yaml`是 API 合同片段。它描述了 `GET /energy/buildings/hourly` 接口、可使用的查询参数，以及成功响应中的能耗记录数组。它让前面的能耗记录结构进入 API 文档，使接口实现方和数据使用方能够按照同一套字段约定工作。

其中，ontology 统一定义概念，两个 context 分别翻译元数据和能耗记录，两个 SHACL shapes 检查 RDF 语义数据，JSON Schema 检查普通 JSON 结构，OpenAPI 描述实际接口，正例和反例则用于验证这些规则是否按预期工作。

## Phase02

Phase02是一个本地验证的阶段。虽然，我们可以进行人工比对之前编写的示例，例如v0.3中的`data-product-valid.jsonld`是否符合我们设计的模型规范，但是光靠人工比对可能会出现纰漏。并且，在具体的生产过程中，这些实例可能有几百条甚至上千条，因此直接进行手动比对实属下策。因此，Phase02写了一套python脚本来进行自动化验证这些内容，其中总脚本是`run_all_validations.py`，运行这个脚本可以验证全套的测试数据是否符合规范。

具体来说，这里的脚本验证有两类。首先是SHACL规则，这用来比对元数据，即`data-product-valid.jsonld`是否符合`data-product-metadata-shapes.ttl`给的规则；然后是JSON Schema，它用来比对更底层的API返回数据。比如对于具体的用电量记录实例（比如 `energy-reading-record-valid.json`），脚本会把它拿去和对应的JSON Schema文件（比如`energy-reading-record.schema.json`）做比对。

此外，phase02还使用了docker让这套验证脚本在其他环境中可复现。

## Phase03

Phase03同样也是一个验证阶段，不过和Phase02主要关注的语法层面不同，Phase03更多关注的是模型的解释力。 在这个阶段，引入了一个在语义建模领域非常经典的方法，叫做“能力问题”（Competency Questions，简称CQ）。具体来说，是从使用者的角度列出一系列业务问题。比如，假设Data Space的管理者拿到我们设计的数据包，他可能会问：“这个数据集的唯一编号是什么？”、“提供方是哪家公司？”、“API的调用地址在哪里？”、“计量的单位是不是度（kWh）？”等等的问题。Phase03就是如此，我们设计了8个类似的问题，来考察我们设计的模型能否回答这些问题。特别地，我们使用了SPARQL将这些问题进行了转化，同时，我们为每个问题都自行设计了一个标准回答，这样我们的脚本就可以自动进行检查。如果8个问题都能精准回答，那就证明我们的语义模型不仅合法合规，而且具有极高的业务解释力。

## Phase04

Phase04主要做的是证明本次项目的建模大体上靠近国际通用的标准和规范。

首先，我们编写了一份SSSOM语义规范表。在这份表格中，我们把我们自己给数据起的本地名字，和国际权威标准（比如DCAT、SOSA）中的官方名字，一行一行地做了一一对应。不仅如此，我们还在这本词典中标注了“匹配度”。具体来说如果我们的意思和国际标准分毫不差，就标上“完全匹配”；如果是类似但有细微差别（比如我们用的是简单的文字名字，而标准要求是一个复杂的组织机构），我们就标上“近似匹配”。

然后，在这一阶段我们又开发了一个自动化脚本进行评估。这是一个Python程序（quality_metrics.py），它会自动去扫描我们的整个模型，并计算出三个分数：“覆盖率”，查验任务要求的所有字段是不是都做了进去；“约束强度”，看看规则是不是足够严格，能把错误数据挡在门外；三是“标准复用比例”，查看一下到底有百分之多少的字段是成功对接了国际标准的。

## Phase05

Phase05让项目在工程上变得更加可控。由于我们目前已经设计了3个版本的模型（v0.1, v0.2, v0.3），之后也可能继续更新模型，因此我们有必要设计一套更新的规则，例如，严禁直接删除字段这种会直接导致下游系统崩溃的操作。Phase05做的正是这些工作。具体来说，phase05的工作分成3部分：

首先划定了模型的使用范围和责任边界（`model-card.md`），明确规定了这套模型是做给谁用的、能用来做什么。此外，还明文规定了模型禁止用来做什么，例如明确禁止用于真实的电费财务结算。这些可以有效防止下游业务因为误解或滥用模型而导致严重的生产事故。

然后，记录语义模型迭代的更新日志（`changelog.md`）。它清晰地记录了模型从v0.1到v0.3的演进，例如加了什么新字段、改了什么老规则。同时，它也附带了兼容性通知用于告诉下游的A组和D组本次更新是否会导致兼容性问题，如果出现问题可以如何修改。

此外，为了防止未来出现私自删改字段导致下游系统全线崩溃这类的事情发生，phase05还指定了后续版本的更新规则，包括审批流程（任何人改字段之前都需要经过提前的提案和审批）、废弃缓冲机制（绝不允许直接删除旧字段，而是必须设立几个月的缓冲期，让下游进行配套更新之后才能删除），以及机器溯源（生成一份机器可读的电子档案`provenance.jsonld`，让服务器也能自动查出当前模型是哪个版本、遵循什么规则）。

最后，就跟前面的阶段一样，我们也利用脚本设计了一套自动化验证的流水线进行验证。

## Phase06

Phase06的主要内容，就是使用docker在本地部署了Semantic treehouse, 并进行了冒烟测试；并把测试日志写入了本地仓库。其中，冒烟测试的前端结果一切正常，但是后端因为超时没有反应。不过，在这个项目中，本地部署semantic treehouse并不是必须；在phase02-phase05，我们已经做了大量的验证工作，并且可以通过本地的脚本进行自动化验证。

## Phase07

Phase07基本上做的是一些演示内容。例如，准备了两张图`etadata-record-model.mmd`（用来表示数据空间里各个角色和文件的连线）和`semantic-governance-flow.mmd`（项目流程图）。然后也写了一份Phase01-06的项目报告`C_semantic_model_design.md`，包含项目目标与架构定位、设计原则与标准对齐（其中包含复用优先原则）、模型质量得分、局限性与未来展望等内容。同时，也为A组和D组各写了一份跨组交接报告。

## Phase08

Phase08在项目中引入了CI(Continuous Integration)，用来证明代码不仅在本地能跑，在云端（github上的ubuntu）也能够跑通。同时，又写了两个“警察脚本”用来验证仓库内容是否已经完全符合了项目要求，以及是否有工程上的任何不规范的地方（如写死路径这类的问题）。同时，也写了个展示文档`demo-script.md`，以及为B组写了一份交接报告。

## Phase09

Phase09做了最后的验证收尾工作。运行了之前所有阶段的测试脚本（包括语法检查、规则拦截、SPARQL测试、文件查漏脚本等等），同时，在文档中特别注明了那些故意设计的错误示例。最后，输出了最终报告FINAL_SUMMARY.md。
