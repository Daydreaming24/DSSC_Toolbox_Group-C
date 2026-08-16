# DSSC C 组项目全流程实现导览：Phase 00 到 Phase 09

本文是一份面向初学者的项目实现导览。它的目标不是再复制一份最终报告，而是带着读者从任务要求开始，顺着 Phase 00 到 Phase 09，一步一步看懂这个 DSSC C 组 Semantic Treehouse / Semantic Model Governance 项目是怎样被搭起来、怎样被验证、怎样被治理、怎样交接给其他小组的。

如果只用一句话概括本项目：

> C 组把 Building Energy Consumption Data Product 这个最小能源数据产品，做成了一套可版本化、可验证、可复现、可交接的语义治理包。

这里的“语义治理包”不只是几个模型文件。它同时包含语义模型、JSON-LD 示例、SHACL 约束、JSON Schema、OpenAPI 片段、SPARQL 测试、质量指标、治理文档、Semantic Treehouse 部署证据、跨组 handoff、Docker/CI 验证入口和最终检查材料。

## 1. 先看懂项目要解决什么问题

DSSC Toolbox 研究任务把整个 data space 工具链拆成四个方向：

| 小组 | 方向 | 负责的问题 |
|---|---|---|
| A 组 | FIWARE FDF / TNO TSG | 数据如何发布、发现、协商和交换 |
| B 组 | Gaia-X Compliance Service + Registry | 参与方和服务如何表达 trust / compliance |
| C 组 | Semantic Treehouse | 共同语义模型如何定义、维护、发布和治理 |
| D 组 | ITB + SEMIC Validator | metadata 和规则如何做 conformance / validation |

C 组位于中间层。它不负责真实数据交换，也不负责 Gaia-X 合规服务本身，也不负责完整 ITB 平台实现。C 组的职责是定义大家共同使用的语义契约：

- A 组发布 data offering 时要知道 metadata 必须包含哪些字段。
- D 组做 SHACL validation 时要知道哪些字段必填、哪些值合法。
- B 组做 compliance 或 credential 说明时可以引用模型版本 URI 和 provenance。
- 最终集成故事需要一条清晰的链路：semantic model -> data offering -> compliance -> validation。

所以，本项目的核心不是“写一个能源 API”，而是回答：

1. 数据产品应该用哪些 metadata 字段描述？
2. 这些字段在语义上分别对应什么概念或标准？
3. 哪些字段必填，哪些值只能取固定值？
4. 模型如何从 v0.1 演进到 v0.3？
5. 如何证明 valid 示例真的通过、invalid 示例真的失败？
6. 如何让其他同学不用重新理解全部细节，也能使用 C 组成果？

## 2. 统一场景：Building Energy Consumption Data Product

项目的统一业务场景来自 `task_plan/` 下的场景包。场景很小，但足够覆盖 data space 的关键环节。

| 项目 | 内容 |
|---|---|
| Data Product | Building Energy Consumption Dataset API |
| Dataset ID | `building-energy-hourly-v1` |
| Provider | `Energy Data Provider Ltd.` |
| Consumer | `City Analytics Lab` |
| Data Space Authority | `City Energy Data Space Authority` |
| Format | JSON |
| Frequency | hourly |
| Unit | kWh |
| Endpoint | `https://api.example.org/energy/buildings/hourly` |
| Spatial Coverage | Shenzhen demo district |
| Temporal Coverage | 2026-05-01 to 2026-05-02 |

初学者可以把它理解成这样：

- Provider 有一份建筑每小时耗电量数据。
- Consumer 想在 data space 里发现并使用这份数据。
- Authority 要求这份数据产品先说清楚 metadata，并且 metadata 能被机器验证。
- C 组负责制定这份 metadata 的共同语义模型。

`task_plan/DSSC_Minimal_Energy_Scenario/` 是最原始的轻量样例包，里面的文件对应四个小组共同使用的素材：

| 文件 | 作用 |
|---|---|
| `README.md` | 解释最小能源场景，以及 A/B/C/D 组如何使用这些材料 |
| `VALIDATION_GUIDE.md` | 解释 valid / invalid metadata 为什么应通过或失败 |
| `data/building-energy-sample.json` | mock API 返回数据，给 A 组模拟 data exchange，也给 C 组理解 record 层 |
| `mock-api/openapi.yaml` | 原始 mock API 描述，说明 `/energy/buildings/hourly` 返回什么 |
| `metadata/data-product-valid.jsonld` | 原始合法 metadata 示例 |
| `metadata/data-product-invalid.jsonld` | 原始故意错误 metadata 示例 |
| `shapes/building-energy-shapes.ttl` | 原始最小 SHACL 约束 |
| `gaia-x/*.template.jsonld` | Gaia-X participant / service offering 学习模板 |

后续 `C_Semantic_Treehouse/` 里的成果，就是在这个最小场景基础上做了更工程化、更版本化、更可验证的扩展。

## 3. 整个仓库的角色分工

仓库可以按五层理解：

| 层次 | 主要路径 | 作用 |
|---|---|---|
| 任务输入层 | `task_plan/` | 保存课程任务、统一场景、早期字段整理任务 |
| 执行路线层 | `prompts/` | 保存 Phase 00-09 的实施 prompt，相当于项目施工图 |
| C 组成果层 | `C_Semantic_Treehouse/` | 保存语义模型、验证脚本、报告、治理、证据、交接材料 |
| 复现入口层 | `Makefile`、`make.cmd`、`Dockerfile.validation`、`docker-compose.validation.yml` | 让本地、Windows、Docker 都能运行验证 |
| CI 和外部工具层 | `.github/workflows/validate.yml`、`tools/semantic-treehouse/` | 提供 GitHub Actions 验证和 Semantic Treehouse 本地部署证据轨道 |

其中最重要的是 `C_Semantic_Treehouse/`：

| 目录或文件 | 初学者理解方式 |
|---|---|
| `README.md` | C 组成果包首页，说明目标、范围、快速运行方式 |
| `C_semantic_model_design.md` | 讲模型设计思路：两个模型、字段、标准对齐、验证策略 |
| `C_semantic_treehouse_usage.md` | 讲 Semantic Treehouse 如何作为支持性工具和证据轨道 |
| `C_model_versioning_demo.md` | 讲 v0.1、v0.2、v0.3 如何演进 |
| `C_export_for_validation.md` | 讲导出的 TTL、SHACL、JSON-LD、JSON Schema、OpenAPI 如何交给 validator |
| `model/` | 真正的版本化模型 artifact |
| `scripts/` | 自动验证和工具辅助脚本 |
| `validation/` | 自动生成或维护的验证报告 |
| `tests/sparql/` | SPARQL competency questions、查询和期望结果 |
| `mappings/` | SSSOM 标准映射表 |
| `governance/` | model card、changelog、release policy、provenance 等治理材料 |
| `quality/` | 模型质量评估 |
| `diagrams/` | Mermaid 关系图和治理流程图 |
| `handoff/` | 给 A、B、D 组的交接说明 |
| `evidence/` | Semantic Treehouse 本地部署和 smoke check 证据 |
| `FINAL_SUMMARY.md` | 最终提交级摘要 |

## 4. 贯穿全项目的一条主线

所有文件可以用下面这条线串起来：

```text
任务要求
  -> 最小能源场景
  -> metadata 字段整理
  -> C 组语义模型设计
  -> v0.1 / v0.2 / v0.3 版本化 artifact
  -> SHACL / JSON Schema / OpenAPI / SPARQL 验证
  -> SSSOM 标准映射和质量指标
  -> governance / provenance / release policy
  -> Semantic Treehouse 本地部署证据
  -> A/B/D 组 handoff
  -> CI、required files、path/link hardening
  -> FINAL_SUMMARY 和最终展示
```

这也是本文按 Phase 00-09 展开的原因：每个 Phase 都是在前一阶段成果上多加一层能力。

## Phase 00：仓库审计和项目脚手架

**阶段目标：先搭一个可持续生长的工程骨架。**

Phase 00 没有急着写完整模型，而是先回答几个工程问题：

- 成果放在哪里？
- 未来会有哪些模型版本？
- 验证脚本放在哪里？
- 报告、证据、治理、handoff 分别放在哪里？
- 后续所有验证能不能统一用一个命令运行？

### 00.1 输入来自哪里

Phase 00 主要读取和理解：

- `task_plan/DSSC_Toolbox_Research_Task_Plan.md`
- `task_plan/DSSC_Toolbox_Scenario.md`
- `task_plan/DSSC_Minimal_Energy_Scenario/README.md`
- `task_plan/DSSC_Minimal_Energy_Scenario/VALIDATION_GUIDE.md`
- `prompts/master-prompt.md`
- `prompts/phase-00-repository-audit-and-project-scaffold.md`

这些文件告诉我们：C 组要做的是 Semantic Treehouse / Semantic Model Governance，而且必须交付两层模型、版本化、导出可验证表示、和 A/D 组交接。

### 00.2 创建的核心结构

Phase 00 创建了 `C_Semantic_Treehouse/` 这个核心成果目录，并在其中预留了：

```text
C_Semantic_Treehouse/
  diagrams/
  docs/
  evidence/
  governance/
  handoff/
  mappings/
  model/
    v0.1/
    v0.2/
    v0.3/
  quality/
  scripts/
  tests/
  validation/
```

这里最值得注意的是 `model/v0.1`、`model/v0.2`、`model/v0.3`。这说明项目一开始就不是只做“最终版本”，而是要展示模型演进过程。

### 00.3 根目录执行入口

Phase 00 还创建了根目录的运行入口：

| 文件 | 作用 |
|---|---|
| `Makefile` | Unix / Docker / CI 环境下的统一命令入口 |
| `make.cmd` | Windows 兼容入口，让 `cmd /c make validate` 可运行 |
| `.gitignore` | 忽略缓存、虚拟环境、临时日志、外部 Treehouse clone，但保留最终验证报告 |
| `.github/workflows/.gitkeep` | 先占位，后续 Phase 08 放入真正 CI workflow |

常用命令从一开始就被设计出来：

```bat
cmd /c make help
cmd /c make validate
cmd /c make validate-shacl
cmd /c make test-sparql
cmd /c make quality
```

**Windows 演示方式：**

Phase 00 最适合现场先跑帮助命令：

```bat
cmd /c make help
```

这个命令只展示可用 target，不依赖 Semantic Treehouse 本地部署，也不要求先启动 Docker。它适合用来说明项目所有验证入口都已经被统一到了根目录。

如果要跑 `cmd /c make validate`，需要后续 Phase 02 之后的 Python 验证脚本和依赖已经准备好；它不是 Phase 00 的重点。

Phase 00 时很多 target 只是 stub，但这很重要：它先确定了“项目以后怎么跑”。

### 00.4 为什么 Phase 00 重要

对于初学者来说，Phase 00 的意义是：

- 不把所有文件堆在一个目录里。
- 不等最后才想怎么验证。
- 不把 Semantic Treehouse 当成唯一运行依赖。
- 从第一天就给模型、验证、治理、证据、交接分别留位置。

对应总结文件是 `C_Semantic_Treehouse/PHASE_0_SUMMARY.md`。

## Phase 01：核心词汇和版本化语义 artifact

**阶段目标：把业务场景变成机器可读、可验证的语义模型。**

Phase 01 是模型主体阶段。它把最小能源场景中的字段，正式做成 v0.1、v0.2、v0.3 三个版本。

### 01.1 先理解两个模型层次

本项目不是只有一个 JSON 文件，而是刻意分成两层：

| 模型 | 描述对象 | 用途 |
|---|---|---|
| Data Product Metadata | 数据产品本身 | catalogue、connector offering、SHACL metadata validation |
| Energy Reading Record | API 返回的一条能耗读数 | mock API、JSON Schema、OpenAPI、可选 SHACL payload validation |

这两个层次不要混淆：

- Metadata 回答“这份数据产品是谁提供、在哪里访问、是什么格式、什么单位、覆盖什么时间和空间”。
- Record 回答“API 返回的一条具体读数包含 buildingId、meterId、timestamp、energyKWh 等字段”。

### 01.2 命名空间和版本 URI

项目采用本地轻量命名空间：

```text
base namespace: https://w3id.org/dssc-demo/building-energy#
prefix: be
```

三个版本 URI 是：

```text
https://w3id.org/dssc-demo/building-energy/v0.1
https://w3id.org/dssc-demo/building-energy/v0.2
https://w3id.org/dssc-demo/building-energy/v0.3
```

metadata 示例通过 `dct:conformsTo` 指向具体版本。这样 D 组或 validator 不需要猜测“应该用哪版规则”，而是可以直接看到数据声明自己符合 v0.3。

### 01.3 v0.1：最小 metadata 基线

v0.1 文件在：

```text
C_Semantic_Treehouse/model/v0.1/
  building-energy-ontology.ttl
  data-product-metadata-shapes.ttl
  data-product-context.jsonld
  data-product-valid.jsonld
```

v0.1 定义 `be:DataProductMetadata`，要求最基础字段：

| 字段 | 作用 |
|---|---|
| `datasetId` | 数据产品编号 |
| `providerName` | 提供方名称 |
| `format` | 数据格式 |
| `frequency` | 更新频率 |
| `spatialCoverage` | 空间覆盖范围 |

v0.1 适合展示“最小 metadata 模型是什么样子”。

### 01.4 v0.2：加入 endpoint、unit 和时间范围

v0.2 文件在：

```text
C_Semantic_Treehouse/model/v0.2/
  building-energy-ontology.ttl
  data-product-metadata-shapes.ttl
  data-product-context.jsonld
  data-product-valid.jsonld
  data-product-invalid.jsonld
```

v0.2 在 v0.1 基础上增加：

| 字段 | 为什么重要 |
|---|---|
| `endpointUrl` | A 组发布 data offering 时需要 API 地址 |
| `unit` | D 组验证单位是否统一为 kWh |
| `temporalStart` | 数据时间范围起点 |
| `temporalEnd` | 数据时间范围终点 |

并且加入固定值约束：

| 字段 | 合法值 |
|---|---|
| `format` | `JSON` |
| `frequency` | `hourly` |
| `unit` | `kWh` |

v0.2 还故意放了一个 invalid 示例：`data-product-invalid.jsonld`。它缺少 `providerName`，把 `unit` 写成 `MWh`，还缺少 `temporalEnd`。这个文件不是错误提交，而是教学用负例，用来证明 validator 确实能抓住问题。

### 01.5 v0.3：加入 API record payload 模型

v0.3 文件在：

```text
C_Semantic_Treehouse/model/v0.3/
  building-energy-ontology.ttl
  data-product-metadata-shapes.ttl
  energy-reading-record-shapes.ttl
  data-product-context.jsonld
  energy-reading-record-context.jsonld
  data-product-valid.jsonld
  energy-reading-record-valid.jsonld
  energy-reading-record-invalid.jsonld
  energy-reading-record.schema.json
  openapi-fragment.yaml
```

v0.3 保留 v0.2 的 metadata 规则，并增加 `be:EnergyReadingRecord`。record 字段包括：

| 字段 | 示例 |
|---|---|
| `buildingId` | `BLD-001` |
| `meterId` | `MTR-001` |
| `timestamp` | `2026-05-01T00:00:00+08:00` |
| `energyKWh` | `12.4` |
| `unit` | `kWh` |
| `location` | city / district |

v0.3 体现了一个关键思想：同一个模型可以导出给不同工具使用。

| artifact | 给谁看 | 作用 |
|---|---|---|
| `.ttl` ontology | 语义建模 / RDF 工具 | 定义类、属性、标准继承关系 |
| `.jsonld` context | JSON-LD 数据生产者 | 把普通字段名映射到语义 IRI |
| `.ttl` SHACL shapes | D 组 / validator | 检查字段是否必填、类型和值是否合法 |
| `.schema.json` | API payload validator | 检查普通 JSON record |
| `openapi-fragment.yaml` | A 组 / API 文档 | 描述 endpoint 和 response schema |

### 01.6 Phase 01 和原始场景包的关系

`task_plan/DSSC_Minimal_Energy_Scenario/shapes/building-energy-shapes.ttl` 是最早的最小 SHACL 文件，使用 `ex:*` 和部分 DCAT/DCTERMS 术语。

C 组在 Phase 01 做了升级：

- 使用稳定的 `be:` 命名空间。
- 使用明确版本 URI。
- 把 metadata 和 record 分层。
- 增加 v0.1/v0.2/v0.3 演进。
- 增加 JSON-LD context、JSON Schema、OpenAPI fragment。

**Windows 演示命令：**

Phase 01 主要演示“模型 artifact 能否被基础工具解析”。这些命令不需要本地部署 Semantic Treehouse，但需要已经安装 Python 依赖：

```bat
cmd /c make validate-rdf
cmd /c make validate-jsonld
cmd /c make validate-jsonschema
cmd /c make validate-openapi
```

如果第一次运行时报缺少 Python 包，可以先在 Windows 终端运行一次：

```bat
python -m pip install -r C_Semantic_Treehouse\requirements.txt
```

讲解时可以这样对应：

| 命令 | 适合展示什么 |
|---|---|
| `cmd /c make validate-rdf` | `.ttl` ontology / SHACL 文件能否被 RDF parser 解析 |
| `cmd /c make validate-jsonld` | `.jsonld` context 和示例能否被 JSON-LD expansion |
| `cmd /c make validate-jsonschema` | v0.3 record schema 是否有效，valid/invalid record 是否按预期通过/失败 |
| `cmd /c make validate-openapi` | v0.3 OpenAPI fragment 是否结构合法 |

对应总结文件是 `C_Semantic_Treehouse/PHASE_1_SUMMARY.md`。

## Phase 02：验证 harness、脚本和 Docker 工具链

**阶段目标：让模型不是“看起来对”，而是可以被自动验证。**

Phase 02 开始把项目从文档型成果变成工程型成果。核心思想是：Semantic Treehouse 是语义治理工具，但本项目不能只依赖一个 UI 或外部服务；必须有独立本地验证路径。

### 02.1 Python 依赖

`C_Semantic_Treehouse/requirements.txt` 定义验证所需依赖：

| 依赖 | 用途 |
|---|---|
| `rdflib` | 解析 RDF/Turtle，运行 SPARQL |
| `pyshacl` | 执行 SHACL 验证 |
| `pyld` | JSON-LD expansion |
| `jsonschema` | 验证 Energy Reading Record JSON |
| `PyYAML` | 解析 OpenAPI YAML |
| `openapi-spec-validator` | 检查 OpenAPI 结构 |

### 02.2 脚本分工

`C_Semantic_Treehouse/scripts/` 中的脚本被拆得很清楚：

| 脚本 | 检查什么 | 输出报告 |
|---|---|---|
| `validation_common.py` | 公共路径、结果对象、报告写入函数 | 被其他脚本复用 |
| `validate_rdf.py` | 所有 `.ttl` 是否能被 RDF parser 解析 | `validation/rdf-validation-report.md` |
| `validate_jsonld.py` | 所有 `.jsonld` 是否能解析和 expansion | `validation/jsonld-validation-report.md` |
| `validate_shacl.py` | metadata / record 是否符合 SHACL，invalid 是否按预期失败 | `validation/pyshacl-validation-report.md` |
| `validate_jsonschema.py` | v0.3 record 是否符合 JSON Schema | `validation/jsonschema-validation-report.md` |
| `validate_openapi.py` | OpenAPI YAML 是否结构合法 | `validation/openapi-validation-report.md` |
| `run_all_validations.py` | 串起 RDF、SHACL、JSON-LD、JSON Schema、OpenAPI | `validation/all-validations-report.md` |

这套脚本有一个很好的教学点：每种验证只管一件事，最后统一汇总。

### 02.3 invalid 文件为什么能让总体验证 PASS

初学者最容易误解的是：为什么有 invalid 文件，报告却是 PASS？

原因是 `invalid` 示例的目标不是通过验证，而是“必须失败”。例如：

- `model/v0.2/data-product-invalid.jsonld` 应该被 SHACL 拒绝。
- `model/v0.3/energy-reading-record-invalid.jsonld` 应该被 JSON Schema 拒绝。

如果 invalid 文件反而通过了，那才说明规则太松。项目把“预期失败”也写进验证逻辑，因此整个 harness PASS 的含义是：

1. valid 示例通过；
2. invalid 示例确实失败；
3. 失败原因符合预期。

### 02.4 Docker 和根目录入口

根目录新增：

| 文件 | 作用 |
|---|---|
| `Dockerfile.validation` | 构建验证镜像，安装 Python 依赖 |
| `docker-compose.validation.yml` | 用 Docker Compose 挂载仓库并运行 `make validate` |

这保证了不只本机能跑，换一台机器也可以用 Docker 复现。

常用命令：

```bat
cmd /c make validate
cmd /c make validate-shacl
docker compose -f docker-compose.validation.yml run --rm validation
```

**Windows 演示方式：**

最推荐现场演示的是：

```bat
cmd /c make validate
```

它会运行核心本地验证链路，并生成或更新 `C_Semantic_Treehouse/validation/` 下的报告。这个命令不需要本地部署 Semantic Treehouse，只需要 Python 依赖已经安装。

如果只想重点展示 SHACL valid/invalid case，可以跑：

```bat
cmd /c make validate-shacl
```

然后打开：

```text
C_Semantic_Treehouse/validation/pyshacl-validation-report.md
```

这里可以重点讲：valid metadata 通过，invalid metadata 因为缺 `providerName`、`unit = MWh`、缺 `temporalEnd` 而按预期失败。

Docker 复现命令是：

```bat
docker compose -f docker-compose.validation.yml run --rm validation
```

这个命令需要 Windows 上安装并启动 Docker Desktop，但仍然不需要本地部署 Semantic Treehouse。它验证的是“独立本地 validation harness 是否能在容器里复现”。

对应总结文件是 `C_Semantic_Treehouse/PHASE_2_SUMMARY.md`。

## Phase 03：SPARQL competency questions 和语义测试

**阶段目标：证明模型不只是能通过语法检查，还能回答治理问题。**

RDF/SHACL 能证明文件格式和约束有效，但还需要回答一个更语义化的问题：这个模型能不能支持 data space governance 中的实际查询？

Phase 03 增加了 SPARQL competency questions。

### 03.1 什么是 SPARQL

SPARQL 是 RDF / 知识图谱世界里的查询语言。可以先用一个熟悉的类比来理解：

```text
SQL    -> 查询关系型数据库中的表
SPARQL -> 查询 RDF 语义图谱中的三元组
```

关系型数据库里常见的是“表、行、列”。RDF 语义图谱里常见的是“三元组”，也就是：

```text
主语 subject -> 谓语 predicate -> 宾语 object
```

例如本项目中的一条语义关系可以理解为：

```text
building-energy-hourly-v1 -> dct:identifier -> "building-energy-hourly-v1"
```

意思是：某个数据产品的 `dct:identifier` 是 `building-energy-hourly-v1`。

SPARQL 就是用来从这些语义关系里取答案的。一个极简查询可以写成：

```sparql
SELECT ?datasetId
WHERE {
  ?dataset dct:identifier ?datasetId .
}
```

它的意思是：在 RDF 图里找出某个 `?dataset` 的 `dct:identifier`，并把这个值命名为 `?datasetId` 返回。

在本项目里，SPARQL 不是用来查询普通业务数据库，也不是用来替代 SHACL。它的用途更像“语义模型问答测试”：

- SHACL 负责检查 metadata 是否符合规则，例如 `unit` 必须是 `kWh`。
- JSON Schema 负责检查 API record 的 JSON 结构是否正确。
- SPARQL 负责向语义模型提问，例如 provider 是谁、endpoint 是什么、metadata 符合哪个版本。

所以 Phase 03 的核心价值是：证明模型不只是被动接受验证，还能主动回答 data space governance 中的关键问题。

### 03.2 什么是 competency question

Competency question 可以理解成“模型必须能回答的问题”。如果模型连这些基本问题都回答不了，就说明建模还不够有用。

本项目定义了 8 个问题：

| CQ | 问题 |
|---|---|
| CQ1 | 数据集 ID 是什么 |
| CQ2 | provider 是谁 |
| CQ3 | endpoint URL 是什么 |
| CQ4 | format 和 frequency 是什么 |
| CQ5 | unit 是什么 |
| CQ6 | spatial / temporal coverage 是什么 |
| CQ7 | metadata conform to 哪个模型版本 |
| CQ8 | Energy Reading Record 有哪些字段 |

### 03.3 文件组织

SPARQL 测试文件在：

```text
C_Semantic_Treehouse/tests/sparql/
  competency-questions.md
  queries/
    cq01-dataset-id.rq
    ...
    cq08-record-fields.rq
  expected/
    cq01-dataset-id.tsv
    ...
    cq08-record-fields.tsv
```

运行脚本是：

```text
C_Semantic_Treehouse/scripts/run_sparql_tests.py
```

它会加载 v0.3 ontology、v0.3 valid metadata、v0.3 valid record，然后运行每个 `.rq` 查询，把实际结果和 `expected/*.tsv` 精确比较。

### 03.4 这个阶段的价值

Phase 03 让模型从“字段列表”升级成“可查询知识图谱”。尤其 CQ7 检查 `dct:conformsTo`，说明数据产品 metadata 明确绑定到了 `https://w3id.org/dssc-demo/building-energy/v0.3`。

运行命令：

```bat
cmd /c make test-sparql
```

输出报告：

```text
C_Semantic_Treehouse/validation/sparql-competency-question-report.md
```

**Windows 演示方式：**

Phase 03 推荐直接运行：

```bat
cmd /c make test-sparql
```

这个命令不需要 Semantic Treehouse 本地部署。它只会读取仓库里的 v0.3 ontology、valid metadata、valid record、SPARQL queries 和 expected TSV 文件，然后生成 SPARQL 测试报告。

讲解时可以按这个顺序展示：

1. 打开 `C_Semantic_Treehouse/tests/sparql/competency-questions.md`，说明 8 个问题。
2. 打开任意一个 `C_Semantic_Treehouse/tests/sparql/queries/cq*.rq`，说明 SPARQL 查询长什么样。
3. 运行 `cmd /c make test-sparql`。
4. 打开 `C_Semantic_Treehouse/validation/sparql-competency-question-report.md`，说明每个 CQ 都和 expected result 精确匹配。

对应总结文件是 `C_Semantic_Treehouse/PHASE_3_SUMMARY.md`。

## Phase 04：SSSOM 映射和模型质量指标

**阶段目标：证明模型不是闭门造车，而是尽量复用外部标准。**

如果全部字段都用本地 `be:*` 自定义，短期很方便，但 data space 的互操作性会弱。Phase 04 的重点是把本地术语和外部标准联系起来。

### 04.1 什么是 SSSOM

SSSOM 全称可以理解为 **Simple Standard for Sharing Ontological Mappings**，也就是一种用来共享“本体/语义术语映射关系”的简单标准格式。

更直白地说，SSSOM 是一张结构化对照表，用来回答：

```text
我们自己定义的字段或概念
  -> 和哪个外部标准概念相似、等价、相关或可映射？
```

在本项目里，我们定义了很多本地术语，例如：

```text
be:DataProductMetadata
be:endpointUrl
be:EnergyReadingRecord
be:timestamp
be:unit
```

这些本地术语很适合教学和 demo，因为字段名短、含义清楚、容易和 JSON / SHACL / OpenAPI 对齐。但如果一个 data space 只使用自己发明的字段，就会有一个问题：别人怎么知道这些字段和已有标准是什么关系？

SSSOM 就是为了解决这个问题。它把本地术语和外部标准放在同一张表里。例如：

| 本地术语 | 可以对齐的外部标准概念 | 直观含义 |
|---|---|---|
| `be:DataProductMetadata` | `dcat:Dataset` pattern | 数据产品 metadata 可以看成 dataset metadata 的一种 profile |
| `be:endpointUrl` | `dcat:endpointURL` | API 访问地址 |
| `be:EnergyReadingRecord` | `sosa:Observation` | 一条能耗读数可以看成一次 observation |
| `be:timestamp` | `sosa:resultTime` / `xsd:dateTime` | 读数对应的时间 |
| `be:unit` | QUDT / UCUM unit concept | 能耗单位 |

这样做有三个好处：

- **可解释**：读者能看懂本地字段为什么这样设计。
- **可互操作**：其他系统可以根据映射关系，把本地字段理解成更通用的标准概念。
- **可评估**：项目可以计算 reuse ratio，量化本地模型有多少术语已经对齐外部标准。

所以，Phase 04 的 SSSOM 不是额外装饰，而是在回答一个很关键的问题：

> C 组模型到底是孤立的本地 schema，还是一个尽量和 DCAT、DCTERMS、SOSA/SSN、QUDT/UCUM、OWL-Time 等标准接轨的语义模型？

### 04.2 SSSOM 映射表

文件：

```text
C_Semantic_Treehouse/mappings/external-standard-alignment.sssom.tsv
```

SSSOM 可以理解成“语义映射表”。它记录：

- 本地字段是什么；
- 对应哪个外部标准概念；
- 用什么关系映射；
- 映射理由是什么；
- 置信度是多少。

涉及的外部标准包括：

| 标准 | 在项目中的用途 |
|---|---|
| DCAT / DCAT-AP | dataset 和 data service metadata |
| DCTERMS | identifier、format、spatial、conformsTo 等 |
| SOSA / SSN | observation、sensor、feature of interest |
| QUDT / UCUM | 能耗单位和数值 |
| OWL-Time / XSD | 时间覆盖和 timestamp |
| schema.org / FOAF | provider、location 等轻量映射 |

### 04.3 质量指标脚本

脚本：

```text
C_Semantic_Treehouse/scripts/quality_metrics.py
```

它计算：

| 指标 | 含义 |
|---|---|
| Field coverage | 任务要求字段是否都出现在 v0.3 shapes 中 |
| Constraint strength | 每个版本有多少必填约束和类型/枚举/节点约束 |
| Reuse ratio | v0.3 本地术语中有多少被映射到外部标准 |
| Breaking-change risk | v0.1 -> v0.2、v0.2 -> v0.3 的变更风险 |

输出：

```text
C_Semantic_Treehouse/quality/model-quality-assessment.md
C_Semantic_Treehouse/validation/quality-metrics-report.md
```

项目当前指标包括：

- required fields 覆盖率：15/15，100.00%。
- v0.3 ontology 本地术语：19 个。
- SSSOM 对齐的本地术语：15 个。
- reuse ratio：15/19，78.95%。
- SSSOM rows：23。

**Windows 演示方式：**

Phase 04 推荐运行：

```bat
cmd /c make quality
```

这个命令不需要 Semantic Treehouse 本地部署。它会读取 `mappings/external-standard-alignment.sssom.tsv` 和 v0.3 模型文件，重新生成质量指标报告。

演示时可以打开：

```text
C_Semantic_Treehouse/mappings/external-standard-alignment.sssom.tsv
C_Semantic_Treehouse/quality/model-quality-assessment.md
C_Semantic_Treehouse/validation/quality-metrics-report.md
```

讲解重点可以放在三点：

- SSSOM 表证明本地 `be:*` 术语和外部标准有映射关系。
- `model-quality-assessment.md` 给出 100% field coverage 和 78.95% reuse ratio。
- breaking-change risk 说明 v0.1 -> v0.2、v0.2 -> v0.3 对 A/D 组的影响。

### 04.4 对 A/D 组的影响

质量报告不是孤立的，它明确说明：

- v0.1 -> v0.2 是 stricter minor change，会影响 A 组 metadata 填写，也会让 D 组 validator 更严格。
- v0.2 -> v0.3 是 additive extension，增加 record payload 验证，但不破坏 v0.2 metadata contract。

对应总结文件是 `C_Semantic_Treehouse/PHASE_4_SUMMARY.md`。

## Phase 05：provenance 和版本治理 metadata

**阶段目标：把模型当作可维护、可审查、可发布的治理资产。**

到 Phase 04 为止，模型已经可用、可验证、可评估。但 data space 中的语义模型通常不是一次性文件，而是长期维护的共同契约。Phase 05 于是加入治理层。

### 05.1 governance 目录

文件在：

```text
C_Semantic_Treehouse/governance/
  model-card.md
  changelog.md
  namespace-policy.md
  release-policy.md
  deprecation-policy.md
  review-workflow.md
  provenance.jsonld
```

每个文件解决一个治理问题：

| 文件 | 回答的问题 |
|---|---|
| `model-card.md` | 这个模型是什么、给谁用、能做什么、不能做什么、风险在哪里 |
| `changelog.md` | v0.1、v0.2、v0.3 分别改了什么 |
| `namespace-policy.md` | `be:` 命名空间和版本 IRI 怎么用 |
| `release-policy.md` | 一个版本发布前必须通过哪些 validation gates |
| `deprecation-policy.md` | 将来字段废弃时怎么通知、迁移和保持兼容 |
| `review-workflow.md` | 从 proposal 到 review、release、handoff 的流程 |
| `provenance.jsonld` | 用机器可读方式记录模型版本、生成活动、责任主体和验证报告 |

### 05.2 provenance.jsonld 的作用

`provenance.jsonld` 采用 PROV-O-inspired 表达方式。它记录：

- C Group 是负责 agent。
- v0.1、v0.2、v0.3 是三个 generated entities。
- v0.2 derived from v0.1。
- v0.3 derived from v0.2。
- validation reports 也是生成出的证据 artifact。

这让模型不只是“有文件”，而是“有来源、有版本、有生成活动、有责任人”。

### 05.3 governance 验证脚本

脚本：

```text
C_Semantic_Treehouse/scripts/validate_governance.py
```

它检查：

- governance 文件是否存在且非空；
- `model-card.md` 是否包含必须章节；
- `changelog.md` 是否显式包含 v0.1/v0.2/v0.3；
- `release-policy.md` 是否包含 validation gates；
- `namespace-policy.md` 是否包含 base namespace 和版本 IRI；
- `provenance.jsonld` 是否能 JSON-LD expansion，并包含必要 ID。

输出：

```text
C_Semantic_Treehouse/validation/governance-validation-report.md
```

**Windows 演示方式：**

Phase 05 推荐运行：

```bat
cmd /c make validate-governance
```

这个命令不需要 Semantic Treehouse 本地部署。它只检查 `governance/` 目录下的文档和 `provenance.jsonld` 是否完整、可解析、包含必要版本信息。

演示时可以按这个顺序打开：

```text
C_Semantic_Treehouse/governance/model-card.md
C_Semantic_Treehouse/governance/changelog.md
C_Semantic_Treehouse/governance/release-policy.md
C_Semantic_Treehouse/governance/provenance.jsonld
C_Semantic_Treehouse/validation/governance-validation-report.md
```

讲解重点是：Phase 05 不只写了治理文档，还把治理文档和 provenance 也纳入自动检查。

对应总结文件是 `C_Semantic_Treehouse/PHASE_5_SUMMARY.md`。

## Phase 06：Semantic Treehouse 本地部署证据轨道

**阶段目标：尝试本地启动 Semantic Treehouse，但不让它阻塞核心验证。**

任务要求 C 组研究 Semantic Treehouse，所以项目需要说明它的部署、使用和风险。但真实工具本地部署可能受 Docker、端口、上游变更影响。Phase 06 采取了很稳妥的策略：

> Semantic Treehouse 是 evidence track，不是 make validate 的硬依赖。

这意味着：

- 如果 Semantic Treehouse 可以启动，就记录证据。
- 如果启动失败，也记录失败日志和解释。
- 无论 Treehouse 是否完整可用，C 组模型仍可通过本地脚本独立验证。

### 06.1 tools 目录

文件：

```text
tools/semantic-treehouse/README.md
```

它解释：

- 本地部署目标；
- Docker 前提；
- expected ports 不做硬编码；
- 这条 evidence track 如何支持 C 组任务；
- fallback 是 `make validate`。

外部上游仓库会 clone 到：

```text
tools/semantic-treehouse/upstream/
```

但 `.gitignore` 明确忽略这个目录，因为它是外部工具副本，不是本项目源码。

### 06.2 脚本设计

Phase 06 加了两套脚本，分别支持 Unix 和 Windows：

```text
C_Semantic_Treehouse/scripts/treehouse_clone_or_update.sh
C_Semantic_Treehouse/scripts/treehouse_up.sh
C_Semantic_Treehouse/scripts/treehouse_down.sh
C_Semantic_Treehouse/scripts/treehouse_status.sh

C_Semantic_Treehouse/scripts/treehouse_clone_or_update.ps1
C_Semantic_Treehouse/scripts/treehouse_up.ps1
C_Semantic_Treehouse/scripts/treehouse_down.ps1
C_Semantic_Treehouse/scripts/treehouse_status.ps1
```

`Makefile` 使用 `.sh`，`make.cmd` 在 Windows 上调用 `.ps1`。

**Windows 演示命令和前提：**

Phase 06 的命令和前面不一样，它们属于 Semantic Treehouse 本地部署证据轨道，需要本机具备 Docker Desktop、网络或已存在的上游 clone、以及可用的本地部署环境：

```bat
cmd /c make treehouse-clone
cmd /c make treehouse-up
cmd /c make treehouse-status
cmd /c make treehouse-down
```

这些命令不是 `cmd /c make validate` 的必要条件，也不建议在没有提前部署和确认环境时现场直接运行。尤其是：

| 命令 | 是否能直接在普通 Windows 上演示 | 原因 |
|---|---|---|
| `cmd /c make treehouse-clone` | 需要网络或已缓存上游仓库 | 会 clone / fetch Semantic Treehouse upstream |
| `cmd /c make treehouse-up` | 需要 Docker Desktop 和可用端口 | 会尝试启动本地 Treehouse compose 服务 |
| `cmd /c make treehouse-status` | 需要之前已经启动过 Treehouse | 用于查看容器状态 |
| `cmd /c make treehouse-down` | 需要之前已经启动过 Treehouse | 用于停止本项目启动的 Treehouse compose project |

如果你的本机没有部署 Semantic Treehouse，讲解时建议不要现场跑这些命令，而是直接展示已有证据文件：

```text
C_Semantic_Treehouse/evidence/semantic-treehouse-local-deployment.md
C_Semantic_Treehouse/evidence/treehouse-smoke-check.txt
C_Semantic_Treehouse/evidence/treehouse-docker-ps.txt
C_Semantic_Treehouse/evidence/treehouse-docker-compose.log
```

同时强调：Semantic Treehouse 是 evidence track；真正可以直接在 Windows 上演示的核心验证仍然是：

```bat
cmd /c make validate
```

### 06.3 evidence 文件

证据文件在：

```text
C_Semantic_Treehouse/evidence/
  semantic-treehouse-local-deployment.md
  semantic-treehouse-upstream-version.txt
  treehouse-compose-candidates.txt
  treehouse-compose-file.txt
  treehouse-docker-compose.log
  treehouse-docker-ps.txt
  treehouse-smoke-check.txt
```

这些文件记录：

- 上游 commit；
- 使用哪个 compose 文件；
- Docker compose 日志；
- 容器状态；
- smoke check 结果。

当前证据显示：

- `http://localhost:4200/` UI smoke check 返回 `HTTP/1.1 200 OK`。
- `http://localhost:8014/` backend/root HEAD check 超时。
- 这个 caveat 被明确记录，没有夸大为完整 UI 工作流成功。

对应总结文件是 `C_Semantic_Treehouse/PHASE_6_SUMMARY.md`。

## Phase 07：报告、图和跨组 handoff

**阶段目标：把工程 artifact 变成可讲、可交接、可复用的材料。**

前面几个 Phase 已经生成了模型和验证链路。Phase 07 负责把它们整理成报告、图和 handoff 文档。

### 07.1 Mermaid 图

```text
C_Semantic_Treehouse/diagrams/metadata-record-model.mmd
C_Semantic_Treehouse/diagrams/semantic-governance-flow.mmd
```

`metadata-record-model.mmd` 讲数据关系：

- Provider 发布 Data Product Metadata。
- Metadata 用 `dct:conformsTo` 指向 v0.3。
- Metadata 被 SHACL 验证。
- Metadata 指向 DataService endpoint。
- API 返回 Energy Reading Record。
- A 组使用 metadata 字段。
- D 组接收 shapes 和 examples。

`semantic-governance-flow.mmd` 讲治理流程：

```text
proposal -> review -> version release -> export artifacts -> validate -> publish/handoff -> monitor/deprecate
```

### 07.2 四份核心 C 组报告

```text
C_Semantic_Treehouse/C_semantic_model_design.md
C_Semantic_Treehouse/C_semantic_treehouse_usage.md
C_Semantic_Treehouse/C_model_versioning_demo.md
C_Semantic_Treehouse/C_export_for_validation.md
```

它们分别回答：

| 文件 | 重点 |
|---|---|
| `C_semantic_model_design.md` | 模型设计、两个层次、标准对齐、SHACL、JSON-LD、OpenAPI/JSON Schema、SPARQL、质量和限制 |
| `C_semantic_treehouse_usage.md` | Semantic Treehouse 的定位、部署证据、UI/API 待确认点、独立验证 fallback |
| `C_model_versioning_demo.md` | v0.1/v0.2/v0.3 的版本演进、兼容性、对 A/D 组影响 |
| `C_export_for_validation.md` | 导出 artifact、valid/invalid 示例、验证结果、与原始 shapes 对比、D 组 checklist |

### 07.3 handoff 文档

```text
C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md
C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md
C_Semantic_Treehouse/handoff/handoff-to-B-model-uri-provenance.md
```

交接逻辑是：

| 接收方 | C 组给什么 |
|---|---|
| A 组 | 九个 metadata 必填字段、JSON-LD 示例、v0.3 model URI、OpenAPI/record schema 建议 |
| D 组 | SHACL shapes、valid/invalid examples、验证命令、预期结果、ITB/SEMIC story |
| B 组 | 可选引用的 model URI、namespace、provenance metadata 和 validation report |

这一步很关键，因为它证明 C 组成果不是自说自话，而是能嵌入全组 data space 工具链。

### 07.4 AI-assisted human-governed modeling

Phase 07 还加入：

```text
C_Semantic_Treehouse/docs/ai-assisted-human-governed-semantic-modeling.md
```

这份材料说明 AI 可以辅助整理字段、草拟映射、生成检查脚本，但最终权威必须来自：

- human review；
- validation gates；
- audit trail；
- downstream handoff review。

**Windows 演示方式：**

Phase 07 主要是展示文档和图，不要求本地部署 Semantic Treehouse，也没有必须单独运行的 Treehouse 命令。建议按这个顺序打开文件讲：

```text
C_Semantic_Treehouse/diagrams/metadata-record-model.mmd
C_Semantic_Treehouse/diagrams/semantic-governance-flow.mmd
C_Semantic_Treehouse/C_semantic_model_design.md
C_Semantic_Treehouse/C_model_versioning_demo.md
C_Semantic_Treehouse/C_export_for_validation.md
C_Semantic_Treehouse/handoff/handoff-to-A-offering-metadata.md
C_Semantic_Treehouse/handoff/handoff-to-D-shacl-validation.md
C_Semantic_Treehouse/handoff/handoff-to-B-model-uri-provenance.md
```

如果 IDE 支持 Mermaid preview，可以直接预览 `.mmd` 图；如果不支持，也可以把 Mermaid 源码当作文本流程图讲。Phase 07 的总结里也说明：项目做了 Mermaid 静态语法检查，但没有依赖 Mermaid CLI 做 render-level validation。

为了证明报告整理后没有引入回归，可以在 Windows 上跑：

```bat
cmd /c make validate
```

这个命令不需要 Semantic Treehouse 本地部署。

对应总结文件是 `C_Semantic_Treehouse/PHASE_7_SUMMARY.md`。

## Phase 08：CI pipeline 和最终仓库加固

**阶段目标：让仓库适合提交、评分和现场演示。**

Phase 08 是工程硬化阶段。它不再主要增加新模型，而是检查：

- 必需文件是否都存在；
- Markdown 链接是否断裂；
- 脚本是否写死 Windows 绝对路径；
- CI 是否能在 GitHub Actions 中运行验证；
- 演示时该按什么顺序讲。

### 08.1 什么是 CI 化

CI 是 **Continuous Integration**，通常翻译为“持续集成”。所谓“CI 化”，可以先理解成：

> 把原来需要人手动运行的检查，放到自动化平台里，让它在每次提交代码或发起合并请求时自动运行。

在没有 CI 的情况下，项目验证往往依赖某个人记得运行：

```bat
cmd /c make validate
```

这会带来几个风险：

- 有人改了模型文件，但忘记跑验证；
- 有人只在自己电脑上跑通，换一台机器就失败；
- 提交前不知道 Markdown 链接、required files、SHACL、SPARQL 是否仍然正常；
- 最终展示时才发现某个报告或 artifact 漏了。

CI 化就是把这些检查变成自动流程。例如项目一旦推送到 GitHub，GitHub Actions 就自动执行：

```text
安装依赖 -> 运行 make validate -> 生成/上传验证报告
```

这样，模型、脚本、报告和 handoff 文档每次改动后，都可以被同一套规则重新检查。

在本项目里，CI 化的重点不是部署一个真实服务，而是复用本地验证入口 `make validate`。也就是说：

- 本地开发时可以运行 `cmd /c make validate`。
- Docker 中可以运行 `make validate`。
- GitHub Actions 中也运行同一个 `make validate`。

这让项目有一个很清楚的质量门槛：只要 CI 运行通过，就说明 RDF、JSON-LD、SHACL、JSON Schema、OpenAPI、SPARQL、quality、governance、required files 和 path/link hardening 这些检查仍然没有回归。

所以 Phase 08 里的 CI 化，本质上是在把 C 组语义治理包从“某台电脑上能跑”提升到“仓库级别可自动复现、可自动检查”的状态。

### 08.2 GitHub Actions workflow

文件：

```text
.github/workflows/validate.yml
```

它在 `push` 和 `pull_request` 时：

1. checkout repository；
2. 设置 Python 3.12；
3. 安装 `C_Semantic_Treehouse/requirements.txt`；
4. 运行 `make validate`；
5. 上传 validation、quality、evidence Markdown 报告。

这说明本地验证链路已经具备 CI 化条件。

### 08.3 required files 检查

脚本：

```text
C_Semantic_Treehouse/scripts/check_required_files.py
```

输出：

```text
C_Semantic_Treehouse/validation/required-files-report.md
```

它检查 minimum、excellent、top-tier 三类交付物是否存在。例如：

- 两个模型；
- v0.1/v0.2/v0.3 artifact；
- SHACL shapes；
- SSSOM；
- SPARQL 报告；
- provenance；
- handoff；
- FINAL_SUMMARY。

### 08.4 path/link hardening

脚本：

```text
C_Semantic_Treehouse/scripts/check_links_and_paths.py
```

输出：

```text
C_Semantic_Treehouse/validation/path-link-report.md
```

它检查：

- Markdown 本地链接是否断裂；
- scripts 中是否出现 Windows-only 绝对路径。

这对可复现性很重要，因为项目不能只在组长电脑上跑。

### 08.5 展示脚本和最终 checklist

```text
C_Semantic_Treehouse/docs/demo-script.md
C_Semantic_Treehouse/docs/final-checklist.md
```

`demo-script.md` 给出五分钟展示顺序：

1. 看 repository structure。
2. 看 v0.1/v0.2/v0.3。
3. 跑 SHACL validation。
4. 解释 invalid metadata。
5. 跑 SPARQL competency questions。
6. 看 Semantic Treehouse evidence。
7. 看 A/D handoff。
8. 看 quality metrics 和 final checklist。

`final-checklist.md` 则把 minimum、excellent、top-tier 要求逐项对应到 evidence path。

**Windows 演示命令：**

Phase 08 推荐按“先专项、再总体验证”的顺序演示：

```bat
cmd /c make check-required-files
cmd /c make check-links-and-paths
cmd /c make validate
```

这三个命令都不需要本地部署 Semantic Treehouse。

| 命令 | 输出 | 讲解重点 |
|---|---|---|
| `cmd /c make check-required-files` | `C_Semantic_Treehouse/validation/required-files-report.md` | minimum / excellent / top-tier 交付文件是否齐全 |
| `cmd /c make check-links-and-paths` | `C_Semantic_Treehouse/validation/path-link-report.md` | Markdown 链接和脚本路径是否适合复现 |
| `cmd /c make validate` | 多个 `validation/*.md` 报告 | 把 Phase 02-08 的检查统一跑一遍 |

GitHub Actions 的 `.github/workflows/validate.yml` 不是在本地 Windows 里手动运行的脚本，而是项目上传到 GitHub 后由平台自动执行。讲解时只需要打开这个文件，说明它在 CI 中运行同一个 `make validate`。

对应总结文件是 `C_Semantic_Treehouse/PHASE_8_SUMMARY.md`。

## Phase 09：最终 QA、证据汇总和 no-regression pass

**阶段目标：不再扩范围，只做最终确认、证据汇总和提交级说明。**

当前仓库没有单独的 `C_Semantic_Treehouse/PHASE_9_SUMMARY.md`，Phase 09 的成果集中体现在：

```text
C_Semantic_Treehouse/FINAL_SUMMARY.md
C_Semantic_Treehouse/validation/*.md
C_Semantic_Treehouse/quality/model-quality-assessment.md
C_Semantic_Treehouse/docs/final-checklist.md
```

### 09.1 最终应运行的检查

Phase 09 prompt 要求最终运行：

```bat
cmd /c make clean
cmd /c make validate
cmd /c make quality
cmd /c make test-sparql
cmd /c make check-required-files
```

以及在支持环境中运行 clean / git status 等检查。当前仓库的总结中也明确提到：工作区不是 git repository，因此 `git status --short` 不能提供有效结果。这是已记录限制，不是隐藏问题。

**Windows 演示方式：**

如果只是课堂讲解或研讨展示，建议优先运行：

```bat
cmd /c make validate
cmd /c make quality
cmd /c make test-sparql
cmd /c make check-required-files
```

这些命令都不需要本地部署 Semantic Treehouse。

`cmd /c make clean` 会清理缓存和临时文件，适合做正式 no-regression pass 前运行；普通现场演示可以不跑，以免浪费时间重新生成中间缓存。

最终讲解时建议打开：

```text
C_Semantic_Treehouse/FINAL_SUMMARY.md
C_Semantic_Treehouse/docs/final-checklist.md
C_Semantic_Treehouse/validation/all-validations-report.md
C_Semantic_Treehouse/validation/required-files-report.md
C_Semantic_Treehouse/validation/path-link-report.md
```

如果被问到 Semantic Treehouse，则打开 Phase 06 的 evidence 文件，而不是现场运行 `treehouse-up`。

### 09.2 FINAL_SUMMARY 做了什么

`C_Semantic_Treehouse/FINAL_SUMMARY.md` 是最终提交级摘要，包含：

- What was built；
- How to run validation；
- minimum requirements 的 evidence；
- excellent / top-tier requirements 的 evidence；
- invalid examples 为什么是 expected failures；
- known limitations；
- suggested next steps。

它把前面所有阶段的成果压缩成评分和展示时最容易引用的一页索引。

### 09.3 最终 validation reports 如何读

`C_Semantic_Treehouse/validation/` 下的报告可以这样理解：

| 报告 | 证明什么 |
|---|---|
| `rdf-validation-report.md` | Turtle ontology 和 SHACL 文件能被 RDF parser 解析 |
| `jsonld-validation-report.md` | JSON-LD examples 能解析并 expansion |
| `pyshacl-validation-report.md` | SHACL valid/invalid case 按预期工作 |
| `jsonschema-validation-report.md` | Energy Reading Record 的 valid/invalid JSON 按预期工作 |
| `openapi-validation-report.md` | OpenAPI fragment 结构合法 |
| `sparql-competency-question-report.md` | 模型能回答 8 个治理问题 |
| `quality-metrics-report.md` | SSSOM 和质量指标脚本正常运行 |
| `governance-validation-report.md` | governance 文件完整，provenance 可解析 |
| `required-files-report.md` | 必需交付文件存在 |
| `path-link-report.md` | Markdown 链接和脚本路径没有明显复现风险 |
| `all-validations-report.md` | 汇总核心验证脚本的总结果 |

所有关键报告的 overall status 都是 PASS。注意，这里的 PASS 包含“invalid 示例按预期失败”。

### 09.4 最终限制也被写清楚

项目没有假装所有东西都完美完成，而是在 FINAL_SUMMARY 和 checklist 中明确列出限制：

- Semantic Treehouse UI smoke check 成功，但完整手动 UI 工作流截图仍是 partial。
- backend/root HEAD check 在本地 evidence run 中 timeout。
- Mermaid 图做了静态语法检查，但没有用 Mermaid CLI 做 render-level validation。
- provider、location、unit 建模仍是 demo 级轻量表达，生产环境应进一步使用 organization/place nodes 和 QUDT/UCUM unit IRIs。
- 当前目录不是 git repository，不能给出 git working-tree summary。

这很适合在研讨中强调：好项目不是没有限制，而是限制被诚实记录、并且核心验证路径不依赖这些 partial 项。

## 5. 文件之间的整体串联关系

下面按目录重新串一次，帮助读者把“很多文件”看成“一个流程”。

### 5.1 `task_plan/`：任务和原始场景

`DSSC_Toolbox_Research_Task_Plan.md` 给出总任务：A/B/C/D 四组分别研究 connector、compliance、semantic governance、validation。

`DSSC_Toolbox_Scenario.md` 和 `DSSC_Minimal_Energy_Scenario/` 给出统一能源数据产品场景。

`tasks/task1/` 和 `tasks/task2/` 是早期字段整理任务：

- `metadata_fields_table.md` 从原始 valid metadata 和 SHACL shapes 中整理字段。
- `Metadata_Semantic_Model_Table_v0.1.md` 进一步补充字段分类、数据类型、语义 IRI、SHACL 规则、valid/invalid 对比。

这些早期任务相当于 C 组模型设计的预备工作：先把字段看懂，再进入正式版本化建模。

### 5.2 `prompts/`：Phase 00-09 的施工说明

`prompts/master-prompt.md` 定义总目标和质量标准。

`prompts/phase-00-...md` 到 `prompts/phase-09-...md` 定义每个阶段做什么、验收标准是什么、需要运行哪些命令。

可以把 `prompts/` 理解成“项目路线图”，而 `C_Semantic_Treehouse/PHASE_*_SUMMARY.md` 和最终 artifact 是“按路线图施工后的结果”。

### 5.3 `C_Semantic_Treehouse/model/`：语义模型的实体文件

`model/v0.1/` 是 baseline metadata。

`model/v0.2/` 是 stricter metadata，加 endpoint/unit/temporal coverage 和 invalid case。

`model/v0.3/` 是最终 demo 版本，加 Energy Reading Record、JSON Schema 和 OpenAPI。

最适合初学者的阅读顺序：

1. 先打开 `model/v0.3/data-product-valid.jsonld`，看普通 metadata 长什么样。
2. 再打开 `model/v0.3/data-product-context.jsonld`，看字段如何映射成语义 IRI。
3. 再打开 `model/v0.3/data-product-metadata-shapes.ttl`，看 validator 要求哪些字段。
4. 再打开 `model/v0.3/building-energy-ontology.ttl`，看类和属性如何被正式定义。
5. 最后看 `energy-reading-record.schema.json` 和 `openapi-fragment.yaml`，理解 API payload 层如何接上。

### 5.4 `C_Semantic_Treehouse/scripts/`：自动化的执行者

`scripts/` 的脚本可以分成四类：

| 类别 | 文件 |
|---|---|
| 核心验证 | `validate_rdf.py`、`validate_jsonld.py`、`validate_shacl.py`、`validate_jsonschema.py`、`validate_openapi.py`、`run_all_validations.py` |
| 语义测试和质量 | `run_sparql_tests.py`、`quality_metrics.py` |
| 治理和加固 | `validate_governance.py`、`check_required_files.py`、`check_links_and_paths.py` |
| Semantic Treehouse 证据 | `treehouse_*.sh`、`treehouse_*.ps1` |

它们都通过 `Makefile` 或 `make.cmd` 暴露成简单命令，所以展示时不需要逐个记 Python 脚本路径。

### 5.5 `C_Semantic_Treehouse/validation/`：验证结果的证据层

这里的报告不是附属品，而是项目可信度的核心证据。

如果老师或同学问“你们怎么证明模型真的有效”，不要只说“我们写了 SHACL”，而是打开：

```text
C_Semantic_Treehouse/validation/pyshacl-validation-report.md
C_Semantic_Treehouse/validation/jsonschema-validation-report.md
C_Semantic_Treehouse/validation/sparql-competency-question-report.md
C_Semantic_Treehouse/validation/all-validations-report.md
```

然后说明 valid 通过、invalid 按预期失败、SPARQL 能回答关键问题。

### 5.6 `C_Semantic_Treehouse/governance/`：让模型可维护

这部分适合在研讨中提升项目高度：

- `model-card.md` 说明模型边界。
- `changelog.md` 说明版本变化。
- `namespace-policy.md` 说明命名空间如何稳定使用。
- `release-policy.md` 说明发布前必须过哪些 gate。
- `deprecation-policy.md` 说明未来字段变更如何不伤害下游。
- `review-workflow.md` 说明人工审查和自动验证如何配合。
- `provenance.jsonld` 说明模型来源和生成关系。

这说明 C 组交付的不是一次性 schema，而是有治理意识的 semantic asset。

### 5.7 `C_Semantic_Treehouse/handoff/`：让其他小组能用

这部分最适合串联全组项目：

- A 组看 `handoff-to-A-offering-metadata.md`，就知道 data offering metadata 要包含哪些字段。
- D 组看 `handoff-to-D-shacl-validation.md`，就知道拿哪些 shapes 和 examples 跑 validation。
- B 组看 `handoff-to-B-model-uri-provenance.md`，就知道如何引用模型 URI 和 provenance。

所以，C 组成果的出口不是最终报告，而是这些可操作的 handoff contract。

### 5.8 根目录和 CI：让项目可复现

| 文件 | 说明 |
|---|---|
| `Makefile` | 标准命令入口，适合 Linux/Docker/CI |
| `make.cmd` | Windows 下的兼容入口 |
| `Dockerfile.validation` | 构建验证环境 |
| `docker-compose.validation.yml` | 用 Docker Compose 运行验证 |
| `.github/workflows/validate.yml` | GitHub Actions 中运行 `make validate` |
| `.gitignore` | 忽略临时文件和外部 upstream，但保留验证报告 |

这些文件说明项目不是只能“看文档”，而是能被机器重复执行。

## 6. 初学者需要掌握的几个概念

### 6.1 JSON 和 JSON-LD

普通 JSON 适合程序读写，但不一定知道字段的语义。例如 `unit` 只是一个字符串。

JSON-LD 在 JSON 基础上加 `@context`，把 `unit` 映射到某个 IRI，让机器知道它是语义模型中的单位字段。

项目中的例子：

```text
model/v0.3/data-product-valid.jsonld
model/v0.3/data-product-context.jsonld
```

### 6.2 RDF/Turtle ontology

`.ttl` 文件用 RDF/Turtle 表达类、属性和外部标准关系。例如：

- `be:DataProductMetadata` 是一个 class。
- 它可以被看作 `dcat:Dataset` 的一种 profile。
- `be:endpointUrl` 和 `dcat:endpointURL` 对齐。

项目中的例子：

```text
model/v0.3/building-energy-ontology.ttl
```

### 6.3 SHACL

SHACL 是 RDF 数据的约束语言。它回答：

- 哪些字段必须有？
- 最多出现几次？
- 数据类型是什么？
- 值只能是什么？

项目中的例子：

```text
model/v0.3/data-product-metadata-shapes.ttl
model/v0.3/energy-reading-record-shapes.ttl
```

### 6.4 JSON Schema

JSON Schema 验证普通 JSON payload。它很适合 API response record。

项目中的例子：

```text
model/v0.3/energy-reading-record.schema.json
```

### 6.5 OpenAPI

OpenAPI 描述 API endpoint、参数、返回结构。A 组做 connector/offering 时可以引用它说明数据服务接口。

项目中的例子：

```text
model/v0.3/openapi-fragment.yaml
```

### 6.6 SPARQL

SPARQL 是 RDF 图查询语言。项目用它证明模型能回答治理问题，例如 provider、endpoint、unit、conformsTo version。

项目中的例子：

```text
tests/sparql/queries/*.rq
```

### 6.7 SSSOM

SSSOM 是语义映射表格式。它说明本地术语如何映射到外部标准。

项目中的例子：

```text
mappings/external-standard-alignment.sssom.tsv
```

### 6.8 Provenance

Provenance 表示来源、生成过程、责任主体和版本衍生关系。

项目中的例子：

```text
governance/provenance.jsonld
```

## 7. 推荐研讨介绍路线

如果要给同学做研讨介绍，可以按下面顺序讲：

1. 先用 `task_plan/DSSC_Toolbox_Research_Task_Plan.md` 说明四个小组分工。
2. 用 `task_plan/DSSC_Minimal_Energy_Scenario/README.md` 讲统一能源场景。
3. 打开 `C_Semantic_Treehouse/README.md`，说明 C 组范围：只做 semantic model governance，不做 connector/compliance/ITB 本体。
4. 打开 `model/v0.3/data-product-valid.jsonld`，从最直观的 metadata JSON 开始讲。
5. 打开 `model/v0.3/data-product-metadata-shapes.ttl`，说明哪些规则会被 SHACL 检查。
6. 打开 `model/v0.2/data-product-invalid.jsonld`，解释三个预期错误：缺 providerName、unit=MWh、缺 temporalEnd。
7. 运行或展示 `validation/pyshacl-validation-report.md`，说明 invalid 失败是好事。
8. 打开 `C_model_versioning_demo.md`，讲 v0.1 -> v0.2 -> v0.3。
9. 打开 `quality/model-quality-assessment.md`，讲 100% field coverage 和 78.95% reuse ratio。
10. 打开 `handoff/` 三份文件，讲 C 组如何交给 A/B/D 组。
11. 最后打开 `FINAL_SUMMARY.md` 和 `docs/final-checklist.md`，说明项目达到哪些要求、还有哪些 partial 限制。

## 8. 最后用一句话串起 Phase 00-09

Phase 00 先搭项目骨架；Phase 01 把能源数据场景变成版本化语义模型；Phase 02 给模型建立本地验证 harness；Phase 03 用 SPARQL 证明模型能回答治理问题；Phase 04 用 SSSOM 和质量指标证明模型有标准复用和可评估性；Phase 05 加入治理、发布、审查和 provenance；Phase 06 尝试 Semantic Treehouse 本地部署并留下证据，同时保持独立验证不受影响；Phase 07 把模型成果写成报告、图和跨组 handoff；Phase 08 加 CI、required-file 和 path/link hardening，让仓库适合展示和提交；Phase 09 做最终 QA 和证据汇总，用 `FINAL_SUMMARY.md` 把整个可复现语义治理包收束起来。

这就是本项目的完整实现过程：从一个轻量能源数据产品场景出发，逐步构建出一个面向 data space 的、可版本化、可验证、可治理、可交接的 C 组 Semantic Governance Package。
