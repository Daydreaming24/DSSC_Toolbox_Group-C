# Phase 00：仓库审计与项目脚手架

## 0. 这一阶段一句话概括

Phase 00 是 C 组项目的“地基阶段”。它不急着写 ontology、SHACL、JSON-LD 或 SPARQL，而是先把整个语义治理包的目录、命令入口、证据规则、验证规则和项目边界确定下来。

更直白地说，Phase 00 解决的是：

> 后面所有语义模型、验证脚本、治理文档、Treehouse 证据和跨组交接材料，应该放在哪里、怎么运行、怎么证明它们是真的可复现。

所以 Phase 00 的成果不是一个最终模型，而是一个可以继续建设的工作台。

## 1. 为什么 Phase 00 很重要

C 组任务看起来是 “Semantic Treehouse / Semantic model governance”，但真正要交付的不是一张截图，也不是单独一份报告，而是一个可复现的 semantic governance package。这个包需要同时满足几个要求：

1. 有清晰的项目范围：C 组负责共享语义模型层，不直接实现 connector、trust service 或 conformance test bed。
2. 有统一业务场景：所有模型围绕 Building Energy Consumption Data Product 展开。
3. 有版本演进：后续要支持 `v0.1`、`v0.2`、`v0.3`。
4. 有本地验证能力：即使 Semantic Treehouse 本地部署失败，也能验证 RDF、SHACL、JSON-LD 等核心产物。
5. 有证据归档：成功和失败都要留下日志、说明和复现记录。

因此 Phase 00 的核心判断是：**先搭工程骨架，再逐步填入语义内容**。这也是 prompt 中明确写的要求：

```text
Do not create full semantic artifacts yet.
```

这句话非常关键。它说明 Phase 00 有意避免过早开始建模，而是先让项目具备稳定的组织结构和复现路径。

## 2. 阶段输入：它根据哪些材料做设计

Phase 00 主要响应三类输入文件。

| 输入文件 | 读到的关键信息 | 对 Phase 00 的影响 |
|---|---|---|
| `task_plan/DSSC_Toolbox_Research_Task_Plan.md` | C 组负责 Semantic model governance，工具是 Semantic Treehouse | 决定建立 `C_Semantic_Treehouse/` 作为 C 组核心交付目录。 |
| `task_plan/DSSC_Toolbox_Scenario.md` | 统一场景是 Building Energy Consumption Data Product | README 中固定 dataset、provider、consumer、endpoint、coverage 等场景信息。 |
| `prompts/phase-00-repository-audit-and-project-scaffold.md` | 要创建目录、Makefile target、占位报告、evidence 规则和 validation 规则 | 形成后续所有阶段可以接着使用的项目脚手架。 |

从任务计划看，C 组的定位可以简化成：

```text
C 组 = Semantic model governance + Semantic Treehouse + data product metadata semantic model
```

从场景文件看，C 组不是随便找一个抽象数据集建模，而是围绕建筑小时级能耗数据产品建模。这个场景后来贯穿了模型、示例数据、SHACL 约束、JSON Schema、OpenAPI fragment 和 SPARQL competency questions。

## 3. Phase 00 具体做了什么

### 3.1 先做仓库审计

Phase 00 的第一步是检查当前仓库，而不是直接创建文件。它运行或等价运行了这些命令：

```text
pwd
find . -maxdepth 3 -type f | sort
Get-ChildItem -Force C_Semantic_Treehouse -Recurse
make help
```

这一步的作用是确认当前工作目录、已有文件、是否已经存在 C 组目录，以及 `make` 命令在本机环境中能否运行。

这里有一个很真实的工程细节：在 Windows PowerShell 中，直接运行 `make help` 一开始并不顺利，因为本机没有 GNU Make，而且 PowerShell 默认不会从当前目录搜索 `make.cmd`。因此后面增加了 Windows 兼容入口 `make.cmd`，并推荐使用：

```bat
cmd /c make help
cmd /c make validate
```

这说明 Phase 00 不只是“理论上可运行”，而是考虑了团队成员真实的 Windows 开发环境。

### 3.2 创建 C 组核心工作区

Phase 00 创建的核心目录是：

```text
C_Semantic_Treehouse/
```

这个目录就是 C 组语义治理包的主体。后续所有模型、报告、脚本、验证结果、证据和交接材料，都围绕这个目录组织。

它还创建了几个顶层报告文件：

| 文件 | Phase 00 中的作用 | 后续阶段的作用 |
|---|---|---|
| `C_semantic_model_design.md` | 占位模型设计报告 | 后续写入语义模型设计、类、属性、标准复用说明。 |
| `C_semantic_treehouse_usage.md` | 占位 Treehouse 使用报告 | 后续记录 Semantic Treehouse 部署和使用情况。 |
| `C_model_versioning_demo.md` | 占位版本演进说明 | 后续说明 `v0.1`、`v0.2`、`v0.3` 如何演进。 |
| `C_export_for_validation.md` | 占位导出和验证说明 | 后续说明如何导出 RDF/JSON-LD/SHACL 并进行验证。 |

这些文件在 Phase 00 里还不是完整报告，但它们提前把最终交付物的位置固定下来了。

### 3.3 创建后续阶段需要的目录

Phase 00 创建了以下目录结构：

```text
C_Semantic_Treehouse/
  diagrams/
  model/v0.1/
  model/v0.2/
  model/v0.3/
  mappings/
  governance/
  validation/
  handoff/
  quality/
  evidence/
  docs/
  scripts/
  tests/
  sparql/
  fixtures/
```

这些目录可以按功能理解：

| 目录 | 放什么 | 为什么 Phase 00 就要创建 |
|---|---|---|
| `model/` | RDF/Turtle、JSON-LD context、SHACL shapes、examples、JSON Schema、OpenAPI fragment | C 组最核心的语义产物需要按版本保存。 |
| `model/v0.1/` | 最小 data product metadata 模型 | 对应后续版本演进的起点。 |
| `model/v0.2/` | 加强 metadata 字段和约束 | 对应 endpoint、unit、temporal coverage 等增强。 |
| `model/v0.3/` | 加入 energy reading record payload 模型 | 把语义模型从 metadata 扩展到 API record。 |
| `validation/` | 验证报告和预期结果说明 | 让 RDF、SHACL、JSON-LD 等验证结果有固定位置。 |
| `scripts/` | 自动化验证脚本 | 支撑 `make validate` 和 CI。 |
| `sparql/` | SPARQL competency questions | 用查询证明模型能回答关键业务问题。 |
| `fixtures/` | 测试数据、样例输入 | 给脚本和验证用。 |
| `mappings/` | 与 DCAT、SOSA、QUDT、OWL-Time 等标准的映射 | 证明模型不是孤立自造词汇。 |
| `governance/` | namespace、release、provenance、review 等治理文件 | 体现 semantic governance，而不只是建模。 |
| `handoff/` | 给 A、B、D 组的交接材料 | 支持跨组协作。 |
| `quality/` | 覆盖率、约束强度、复用比例等质量指标 | 支持 top-tier 要求。 |
| `evidence/` | Treehouse 部署日志、截图、smoke check、本地验证证据 | 给展示和评分提供可追溯证据。 |
| `docs/` | 工程说明和方法论文档 | 解释设计选择。 |
| `diagrams/` | 架构图、关系图 | 支持汇报展示。 |

这套目录体现了 Phase 00 的核心价值：它不是“建了一堆文件夹”，而是提前把整个项目拆成了模型、验证、治理、证据、质量和交接几个层次。

## 4. README 如何确定项目边界

Phase 00 创建并填写了主入口文件：

```text
C_Semantic_Treehouse/README.md
```

这个 README 做了四件重要的事。

### 4.1 说明项目目标

README 开头定义了项目目标：

```text
The goal is to build a reproducible semantic governance package
for the Building Energy Consumption Data Product.
```

这里的关键词是 `reproducible`。C 组不是只产出一份说明，而是要产出一个别人能重新运行验证的包。

### 4.2 明确 C 组范围

README 的 Scope 部分写道：

```text
C Group owns the shared semantic model layer. It does not implement the connector,
trust service, or conformance test bed directly.
```

这句话适合研讨时重点讲。它把 C 组和其他组的边界讲得很清楚：

- A 组可能更关注 connector 和 data offering。
- B 组可能更关注 trust service。
- D 组可能更关注 conformance test bed。
- C 组提供共享语义模型，让其他组能理解和验证同一个 data product。

也就是说，C 组的成果是基础设施型成果：它不一定直接面向最终用户，但会影响其他模块如何描述、交换和验证数据。

### 4.3 固定统一业务场景

README 的 Scenario 部分写入了统一场景：

```text
Data Product: Building Energy Consumption Dataset API
Dataset ID: building-energy-hourly-v1
Provider: Energy Data Provider Ltd.
Consumer: City Analytics Lab
Format: JSON
Frequency: hourly
Unit: kWh
Endpoint: https://api.example.org/energy/buildings/hourly
Spatial Coverage: Shenzhen demo district
Temporal Coverage: 2026-05-01 to 2026-05-02
```

这一步很重要，因为它让后续所有模型都围绕同一个具体数据产品展开。没有这个场景，后续 ontology 和 SHACL 可能会变得很空泛。

### 4.4 写入验收路线图

README 还把最终目标分成了三档：

- Minimum
- Excellent
- Top-tier

Minimum 包括两类模型、三个版本、SHACL 验证、Treehouse 使用记录和关系图。Excellent 进一步要求对齐 DCAT/DCAT-AP、SOSA/SSN、QUDT/UCUM、OWL-Time，并提供 JSON-LD、JSON Schema、OpenAPI、valid/invalid validation reports 和跨组交接。Top-tier 则加入 SSSOM mapping、CI、SPARQL、provenance、质量评估和 AI-assisted but human-governed semantic modeling。

所以 README 不只是介绍文件，它也是后续阶段的路线图。

## 5. 本地验证与 Semantic Treehouse 的“双轨制”

Phase 00 最重要的工程判断之一，是把项目验证分成两条轨道：

| 轨道 | 作用 | 是否阻塞项目 |
|---|---|---|
| 本地独立验证 | 验证 RDF、JSON-LD、SHACL、JSON Schema、OpenAPI、SPARQL、quality、governance 等核心产物 | 是核心主线。 |
| Semantic Treehouse 证据轨 | 记录 Treehouse 部署、UI/API、日志、截图、失败说明和 smoke check | 是重要证据，但不应让项目完全依赖它。 |

这个思想写在 `C_Semantic_Treehouse/docs/engineering-harness.md`：

```text
The package uses local and Docker-based validation so the core semantic artifacts
can be checked reproducibly without relying on a hosted Semantic Treehouse instance.
```

它解决的是一个非常现实的问题：Semantic Treehouse 本地部署可能会受 Docker、网络、端口、依赖版本影响。如果项目所有证据都依赖 UI 部署，一旦部署失败，展示和评分风险就很高。

因此 Phase 00 规定：

- 本地验证是权威复现路径。
- Semantic Treehouse 是重要证据路径。
- Treehouse 失败也要记录，但不能让核心模型验证失效。

这就是后续 Phase 06 中 Treehouse 部署证据可以带有 caveat，但最终 `make validate` 仍然可以作为主验证路径的原因。

## 6. Makefile：统一命令入口

Phase 00 在仓库根目录创建了：

```text
Makefile
make.cmd
```

`Makefile` 是 Unix、Docker、CI 环境下的统一命令入口。Phase 00 要求即使暂时没有真实实现，也要先创建 target：

```text
help
validate
validate-rdf
validate-shacl
validate-jsonld
validate-jsonschema
validate-openapi
test-sparql
quality
treehouse-up
treehouse-down
evidence
clean
```

这些 target 的意义不是 Phase 00 立刻完成所有验证，而是先把“怎么运行项目”这件事固定下来。后续阶段只需要把 stub 替换成真实脚本。

例如后续阶段可以逐步把：

```text
validate-rdf
```

从占位命令变成真正调用 RDF parser 的脚本；把：

```text
validate-shacl
```

变成真正运行 SHACL valid/invalid cases 的脚本。

`make.cmd` 则是给 Windows 环境准备的兼容入口。因为本项目实际在 Windows 上开发，直接假设所有成员都有 GNU Make 并不稳妥。Phase 00 通过 `cmd /c make help` 和 `cmd /c make validate` 提供了更可靠的本地运行方式。

## 7. validation/README.md：先定义验证类别

Phase 00 创建了：

```text
C_Semantic_Treehouse/validation/README.md
```

它列出了后续项目应该覆盖的验证类别：

```text
RDF parse checks
JSON-LD expansion checks
SHACL valid case
SHACL invalid case
JSON Schema record validation
OpenAPI lint
SPARQL competency questions
```

这份 README 的作用是提前定义“什么叫验证充分”。注意这里不仅有 valid case，还有 invalid case。也就是说，项目不仅要证明正确样例能通过，还要证明错误样例会被发现。

这对 semantic governance 很重要，因为治理不是只描述数据长什么样，还要规定什么数据不合格。

## 8. evidence/README.md：先定义证据规则

Phase 00 创建了：

```text
C_Semantic_Treehouse/evidence/README.md
```

它要求后续 evidence 至少包含：

```text
Docker compose logs for Semantic Treehouse attempts
Container status output
Screenshots captured manually when UI access is available
Semantic Treehouse UI/API notes
Failed deployment logs and interpretation if deployment fails
Independent local validation logs and reports
```

最值得强调的是这句话：

```text
Do not invent screenshots.
```

这体现了项目的证据原则：不伪造截图，不假装工具一定成功。如果 Treehouse 部署失败，就把失败日志、原因解释和替代验证路径写清楚。

这个原则对研讨展示很有价值，因为它说明 C 组不是只追求“看起来成功”，而是在做可复现、可审计的工程记录。

## 9. docs/engineering-harness.md：解释为什么要这么设计

Phase 00 还创建了：

```text
C_Semantic_Treehouse/docs/engineering-harness.md
```

这个文件解释了为什么要使用本地和 Docker-based validation：

- 本地验证能让核心语义产物脱离外部 UI 独立检查。
- Docker 验证让依赖环境更接近可复现。
- CI 后续可以运行同样的命令，保证本地开发和评分检查使用同一套路径。
- Semantic Treehouse 仍然重要，但它是 evidence track，不是唯一 blocker。

这份文件实际上说明了 Phase 00 的工程哲学：**展示可以依赖工具，验证不能完全依赖工具。**

## 10. 本阶段验收结果

`C_Semantic_Treehouse/PHASE_0_SUMMARY.md` 记录了 Phase 00 的实际完成情况。

通过项包括：

- 脚手架目录已经创建。
- 占位报告文件已经创建。
- README 说明了 purpose、scope、quality checklist、quickstart、final structure 和 independent validation rule。
- `docs/engineering-harness.md` 解释了本地 / Docker 验证，以及为什么 Semantic Treehouse 不应成为 blocker。
- `evidence/README.md` 解释了 evidence 收集规则。
- `validation/README.md` 列出了后续验证类别。
- `cmd /c make help` 能在 Windows 环境运行。
- `cmd /c make validate` 能运行 Phase 00 的 validation stubs。
- 将仓库根目录加入 `PATH` 后，`make help` 可以通过 `make.cmd` wrapper 运行。

没有完全按原始预期通过的是：

```text
Plain PowerShell make help
```

原因不是项目逻辑错误，而是环境问题：本机没有 GNU Make，PowerShell 也不会默认搜索当前目录下的 `make.cmd`。Phase 00 用 Windows wrapper 解决了这个问题。

## 11. Phase 00 对后续阶段的影响

Phase 00 虽然不写最终语义模型，但它决定了后面所有阶段的工作方式。

| 后续内容 | Phase 00 提前做的铺垫 |
|---|---|
| Phase 01 的 RDF、JSON-LD、SHACL、examples | 已经有 `model/v0.1/`、`model/v0.2/`、`model/v0.3/` 目录。 |
| Phase 02 的验证脚本 | 已经有 `scripts/` 目录和 `make validate-*` target。 |
| Phase 03 的 SPARQL competency questions | 已经有 `sparql/` 目录和 `test-sparql` target。 |
| Phase 04 的标准映射和质量指标 | 已经有 `mappings/` 和 `quality/` 目录。 |
| Phase 05 的 provenance 与版本治理 | 已经有 `governance/` 目录。 |
| Phase 06 的 Treehouse evidence | 已经有 `evidence/` 规则和 `treehouse-up/down` target。 |
| Phase 07 的报告与交接 | 已经有报告占位文件、`handoff/` 和 `diagrams/`。 |
| Phase 08/09 的最终 QA 和 no-regression | 已经有统一 `make validate` 入口。 |

因此，Phase 00 的真正贡献是把“后面要做什么”提前组织成了可执行结构。

## 12. 研讨时可以怎么讲

介绍 Phase 00 时，不建议说成：

```text
我们创建了一些文件夹和 README。
```

更好的讲法是：

```text
Phase 00 是 C 组语义治理包的工程地基。我们先没有急着建 ontology，
而是先确定项目范围、统一业务场景、目录结构、验证入口和证据规则。
这样后续每一个语义产物都能被管理、被验证、被复现，也能和其他组交接。
```

如果现场要手把手展示，可以按这个顺序打开文件：

1. `prompts/phase-00-repository-audit-and-project-scaffold.md`
2. `C_Semantic_Treehouse/README.md`
3. `C_Semantic_Treehouse/docs/engineering-harness.md`
4. `C_Semantic_Treehouse/validation/README.md`
5. `C_Semantic_Treehouse/evidence/README.md`
6. `Makefile`
7. `make.cmd`
8. `C_Semantic_Treehouse/PHASE_0_SUMMARY.md`

可以配合运行：

```bat
cmd /c make help
```

如果要用一段话收尾，可以说：

> Phase 00 的重点不是产出最终模型，而是让项目从第一天起就具备可复现、可验证、可审计和可交接的工程结构。它把 Semantic Treehouse 放在证据轨，把本地独立验证放在主轨，从而降低了外部工具部署失败对最终交付的影响。

