# v0.1–v0.3 基线复现说明

## 1. 文档状态与证据边界

本文件定义 Phase 02 对冻结 v0.1–v0.3 的历史对照、语义一致性标准和新的 baseline 执行合同。历史报告位于 `archive/v0_validation_reports/`，生成时间为 2026-06-25，承担预期行为与诊断文本的对照作用。

当前环境的正式结论以锁定 Windows `.venv` 和固定 digest Docker 容器产生的机器证据为准。Host/Docker 的最终结果、镜像身份、运行计数和一致性结论应在两条轨道均完成后写入发布证据与 `docs/v0.4/STATUS.md`。本文件当前不作这些运行结果声明。

冻结 artifact、既有 SPARQL expected TSV 和经 `C_Semantic_Treehouse/manifests/schemas/baseline-test-cases.schema.json` 校验的 `C_Semantic_Treehouse/manifests/baseline-test-cases.json` 共同构成机器 oracle。Runner 只读取 expected，不根据 actual 自动改写 expected。

## 2. 历史预期与当前 33 case 对照矩阵

Phase 02 baseline 固定覆盖六类 33 个 case：7 RDF + 10 JSON-LD + 5 SHACL + 2 JSON Schema + 1 OpenAPI + 8 SPARQL。

| 类别 | Case 数 | 历史报告所证明的预期 | Phase 02 必须验证的当前合同 | 稳定比较键 |
|---|---:|---|---|---|
| RDF/Turtle | 7 | 7 个 TTL 全部可解析。历史三元组数依次为 30、32、54、62、101、62、40。 | 精确发现 manifest 中的 7 个 artifact；逐个校验路径、SHA-256、Turtle parse 和 manifest 声明的精确三元组数；全部执行且无 skip。 | case ID、artifact path/hash、program status、parse outcome、精确 triple count。 |
| JSON-LD | 10 | 4 个 context 与 6 个 example 全部可解析并展开；历史 context 顶层节点数为 0，example 为 1。 | 精确执行 10 个 manifest case；context 只从仓库本地加载；逐例断言 manifest 声明的精确顶层节点数；任何网络访问、缺失 context、解析或展开异常均为 `ERROR`。 | case ID、artifact/context hash、program status、离线展开 outcome、精确 top-level node count。 |
| SHACL | 5 | v0.1 metadata valid、v0.2 metadata valid、v0.3 metadata valid、v0.3 Energy Reading Record valid 均 conforms；v0.2 metadata invalid 不 conforms。历史 invalid report 含 3 个 Violation。 | 每例显式配置引擎并隔离 data/shapes/ontology graph；证明 target activation 大于 0；解析 report graph；正例结果数为 0；负例精确命中 3 个已声明结果且无未声明关键差异。 | case ID、graph hashes、engine config、target count、result count、规范化 source shape、path、component、severity、message。 |
| JSON Schema | 2 | Draft 7 schema 有效；valid record 通过；invalid record 失败，旧报告只展示首个 `meterId` required 错误。 | 使用 `Draft7Validator` 与 `FormatChecker`；valid record 通过；invalid record 同时命中 required、date-time、number、unit 四类结构化错误。 | case ID、schema/data hashes、validator keyword、instance path、expected business/program status。 |
| OpenAPI | 1 | YAML 基本结构通过，历史报告记录 `openapi-spec-validator` 完整检查通过。 | `openapi-spec-validator` 必须成功导入并执行完整规范验证；缺失、导入失败和验证异常均为 `ERROR`。 | case ID、artifact hash、validator 名称/版本、program status、validation outcome。 |
| SPARQL | 8 | `cq01`–`cq08` 的变量名、行和值与对应 expected TSV 一致。 | 精确发现 8 个 query；逐个校验 query/expected hash；使用确定性排序和序列化比较变量名、行数和值；无缺失、额外或 skipped case。 | case ID、query/expected hashes、变量序列、规范化行和值、row count。 |
| **合计** | **33** | 六类历史报告均为 PASS。 | 通过条件为 discovered=33、executed=33、case-level oracle matched=33、failed=0、skipped=0；预期业务负例仍要求程序 `SUCCESS`。 | 完整 case 集、全部 artifact/oracle hash、expected/actual、suite 退出码。 |

### 2.1 SHACL v0.2 invalid 的稳定 oracle

历史 raw report 显示三个结果。Phase 02 使用以下稳定组合断言：

| Path | Constraint component | Severity | 稳定 message 断言 |
|---|---|---|---|
| `be:unit` | `sh:InConstraintComponent` | `sh:Violation` | `unit must be kWh in v0.2.` |
| `be:temporalEnd` | `sh:MinCountConstraintComponent` | `sh:Violation` | `temporalEnd is required and must be an xsd:date.` |
| `be:providerName` | `sh:MinCountConstraintComponent` | `sh:Violation` | `providerName is required and must be a string.` |

这些 PropertyShape 使用匿名节点。跨运行比较采用 manifest 和 runner 共同定义的规范化 `source_shape` 描述：`kind=anonymous-property-shape` 与稳定的 `owner_node_shape` IRI，再结合 path/component/severity/message/count；运行时 blank-node ID 不进入 oracle。

### 2.2 JSON Schema invalid 的四类 oracle

| Instance path | Validator keyword | 预期含义 |
|---|---|---|
| 根对象 | `required` | 缺少 `meterId`。 |
| `timestamp` | `format` | 值不符合 `date-time`。 |
| `energyKWh` | `type` | 值应为 number。 |
| `unit` | `enum` | 值应为 `kWh`。 |

当前 manifest 把英文错误 message 与 instance pointer、schema pointer、keyword 和 count 一同固定为结构化 oracle；runner 对规范化错误对象进行精确比较。锁定的 jsonschema 4.26.0 使这些 message 成为当前 baseline 的稳定断言。

## 3. 依赖版本与历史可追溯性

当前 `requirements.lock` 固定以下直接验证依赖：

| 依赖 | 当前锁定版本 |
|---|---:|
| RDFLib | 7.6.0 |
| pySHACL | 0.40.1 |
| PyLD | 2.0.4 |
| jsonschema | 4.26.0 |
| PyYAML | 6.0.3 |
| openapi-spec-validator | 0.9.0 |

旧安装入口使用浮动下限约束，archive 报告没有记录当次解析出的准确发行版、lock hash、Python 补丁版本或完整 package inventory。因此旧环境的精确依赖版本未知。涉及依赖升级的文字变化应标注为“由依赖漂移引起的合理推断”，不写成已证明的精确版本迁移。

当前证据必须记录 lock SHA-256、六个 validator 版本、Python/pip 版本以及 runner/helper 源文件 SHA-256。这样可以把今后的诊断文本变化定位到明确环境。

## 4. 文本漂移与语义漂移

### 4.1 可接受的报告文本漂移

以下字段可随报告生成器、平台或依赖版本变化，并应从规范化语义比较中剔除或单独记录：

- 生成时间、绝对工作路径、OS、architecture 和 Markdown 排版。
- pySHACL raw report 中 ValidationResult 的展示顺序、匿名 Shape 的 blank-node 标签、前缀/完整 IRI 表达、Literal/datatype 排版和缩进。
- archive 中 jsonschema 首错的外围叙述、标题和展示顺序；当前 manifest 所列四条精确 message 仍属于稳定 oracle。
- OpenAPI、PyYAML、RDFLib、PyLD 的异常类展示、堆栈、行列格式和诊断措辞。
- 当前 runner 新增的 engine config、target activation、hash、expected/actual、程序状态和环境元数据段落的标题、布局与呈现顺序；这些字段的规范化值继续参与语义比较。

这些差异应保留在 raw 诊断或 `environment.json` 中，确定性 `result.json` 使用规范化字段完成比较。

### 4.2 必须拒绝的语义漂移

以下差异构成 baseline 不一致，suite 必须非零退出：

- 33 个 case 的 ID、类别、数量、启用状态或执行状态发生变化。
- 冻结 artifact、Shape/schema/query/expected TSV 的路径或 SHA-256 不一致。
- 任一 expected business status、expected program status 或 actual oracle match 不一致。
- SHACL target activation 为 0、正例出现 ValidationResult、负例缺少任一预期结果或出现未声明关键结果。
- SHACL 的规范化 path、constraint component、severity、稳定 message 或结果数量不一致。
- JSON Schema invalid 未同时命中四类预期结构化错误、精确 message 不一致，或命中了未批准的关键差异。
- OpenAPI 只完成 YAML 浅层解析、完整 validator 未执行或完整验证失败。
- SPARQL 的变量名、行数、值或 expected TSV 精确比较不一致。
- Host 与 Docker 的规范化 case 集、oracle、artifact hash 或结果不一致。

SPARQL expected TSV 和 SHACL/JSON Schema 的结构化断言属于冻结语义。依赖升级不能把这些差异归类为文本漂移。

## 5. 旧脚本 fail-open 风险与 Phase 02 修复合同

旧脚本保留用于历史审计。Phase 02 runner 必须通过正向结果和 negative controls 证明下列风险已经关闭。

| 旧实现位置 | 历史风险 | Phase 02 remediation |
|---|---|---|
| `C_Semantic_Treehouse/scripts/validation_common.py:37`–`46` | `all([])` 会使空结果集得到 PASS；报告含运行时 timestamp。 | 在执行前拒绝空 manifest/空 case 集；确定性结果与环境时间字段分离。 |
| `C_Semantic_Treehouse/scripts/validate_openapi.py:29`–`36` | `openapi-spec-validator` 缺失时仍记录 PASS。 | validator 为强制锁定依赖；缺失、导入异常和验证异常统一形成程序 `ERROR`。 |
| `C_Semantic_Treehouse/scripts/validate_shacl.py:27`–`47` | 只比较 `conforms`；未证明 target 命中，也未断言 report graph。 | 显式计算 target activation；解析并规范化每个 `sh:ValidationResult`；按结构化 oracle 比较。 |
| `C_Semantic_Treehouse/scripts/validate_shacl.py:30`–`34` | 硬编码 `inference=rdfs`、`meta_shacl=false`，其余关键行为依赖默认值。 | manifest 显式固定全部 engine config，并把 expected 与 actual config 同时写入证据。 |
| `C_Semantic_Treehouse/scripts/validate_jsonschema.py:35`–`46` | 任意首个 `ValidationError` 即可使 invalid case 判为 harness PASS。 | 枚举全部错误并精确匹配 required/date-time/number/unit 四类结构化 oracle。 |
| `C_Semantic_Treehouse/scripts/phase1_validate.py:57`–`78` | 任一 exemplar 缺失时整个正负例块可静默跳过。 | manifest 明确列出必需 case；缺失、disabled、skipped 和 hash mismatch 均非零退出。 |
| `C_Semantic_Treehouse/scripts/phase1_validate.py:33`–`43`、`80`–`91` | JSON-LD 只检查 JSON syntax；OpenAPI 只检查 YAML 和顶层键。 | JSON-LD 执行离线 expansion；OpenAPI 执行强制完整 validator。 |
| `C_Semantic_Treehouse/scripts/validate_rdf.py:10`–`17`、`validate_jsonld.py:48`–`61` | 宽 glob 只拒绝 0 文件，遗漏单个必需 artifact 时仍可能 PASS。 | 不使用 glob 充当 oracle；按 manifest 的精确 case/artifact 列表执行并核对 hash。 |
| `C_Semantic_Treehouse/scripts/validate_jsonld.py:26`–`38`、`55` | 缺失本地 context 时可能落入默认 document loader；网络策略未受控。 | 自定义只读本地 loader；拒绝 URL scheme、路径逃逸和所有网络请求。 |
| `C_Semantic_Treehouse/scripts/run_sparql_tests.py:73`–`78` | 只要发现至少一个 `cq*.rq` 即可继续，遗漏必需 CQ 可能静默少跑。 | 跨记录语义校验器强制精确 8 个必需 CQ，并拒绝缺失或悬空 query/expected 引用。 |
| `C_Semantic_Treehouse/scripts/run_sparql_tests.py:23`–`40` | Literal 被降为普通字符串，datatype/lang 信息未进入比较，也没有声明稳定的字节级 TSV 合同。 | 当前冻结 oracle 明确采用 lexical UTF-8 TSV 单元格；runner 拒绝 BNode 与 tab/newline，精确比较变量、行数、TSV bytes/hash，稳定排序并保留重复行。Datatype/lang 不属于这组历史 TSV 的表达面。 |
| `C_Semantic_Treehouse/scripts/run_all_validations.py:33`–`44` | 聚合列表没有运行 SPARQL，五个脚本通过即可返回 0。 | 统一 dispatcher 只调度已校验 registry；baseline 的六类 33 case 全部由单一 manifest 驱动。 |
| `C_Semantic_Treehouse/scripts/check_required_files.py:106`–`115` | `exists()` 只证明路径存在，不能证明内容、hash、时效或生成环境。 | artifact/report 均绑定 SHA-256、producer/helper hashes、lock hash 和环境证据；旧报告存在性不构成当前 PASS。 |

## 6. 新 baseline 执行合同

### 6.1 通用状态与退出语义

- Schema 校验先于任何 case 执行；跨记录校验覆盖 duplicate ID、悬空引用、同路径 hash 冲突和必需 case 集。
- 每个 case 分别记录 expected business status、expected program status、actual business status、actual program status 和 oracle assertions。
- 预期负例的业务状态为 `FAIL`，其程序状态为 `SUCCESS`；只有预期违规全部命中且无关键额外差异时，该 case 才属于 harness PASS。
- 文件缺失、hash mismatch、解析异常、依赖异常、未知配置、网络访问和 runner 内部异常均为程序 `ERROR`。
- Suite 只有在 33 个 case 全部执行、程序成功且 oracle 匹配时返回 0。零 case、disabled 必需 case、skip 或未实现分支均返回非零。

### 6.2 Offline JSON-LD

- Context 解析限制在仓库根目录内的 manifest 声明路径。
- Loader 拒绝 HTTP(S)、非本地 `file:` authority、其他 URL scheme、绝对路径逃逸、符号链接逃逸和未声明文件。PyLD 为已声明仓库本地 context 生成的本地 `file:` URI 可以加载；解析后的文件必须仍位于受控仓库边界并命中 allowlist。
- Context 文件也必须校验 SHA-256；缓存只能按已校验的 path/hash 键使用。
- 任何网络访问尝试立即形成可诊断 `ERROR`。

### 6.3 SHACL engine 与图隔离

每个历史 SHACL case 显式固定并记录：

- `inference=none`
- `advanced=false`
- `abort_on_first=false`
- `meta_shacl=true`
- Warning/Info 处理策略：所有未在 oracle 中声明的 severity 均视为差异；历史正例要求 0 个 `sh:ValidationResult`

Data graph 只包含当前 case 数据。Shapes graph、可选 ontology graph、manifest、provenance 和其他 fixtures 保持分图。实际传给 pySHACL 的配置必须与 manifest 完全一致。Shape graph 结构验证失败、target activation 为 0 或配置未知时，case 进入程序 `ERROR`。

### 6.4 JSON Schema、OpenAPI 与 SPARQL

- JSON Schema 使用 schema 声明的 Draft 7 validator 和 `FormatChecker`。Invalid JSON 解析失败属于程序 `ERROR`；schema validation 的四个预期错误及其精确 message 全部命中才构成成功负例。
- OpenAPI 使用锁定的 `openapi-spec-validator` 完整验证 `openapi-fragment.yaml`。YAML parse 和顶层键检查只作为前置诊断。
- SPARQL 固定 `cq01`–`cq08` 与各自 expected TSV 的一对一映射。比较包含变量顺序、行数、冻结 TSV 的 lexical UTF-8 单元格值、精确 bytes/hash、确定性排序和重复行保留；结果中的 BNode、tab 或换行使 case 进入程序 `ERROR`。0 行只在 expected 明确为 0 行时允许。

### 6.5 确定性证据与跨环境比较

每条环境轨输出确定性 `result.json`、独立 `environment.json` 和从 JSON 生成的 Markdown。Host baseline 文件为 `build/phase-02/current/baseline-host.result.json`、`baseline-host.environment.json` 和 `baseline-host.md`；Docker 文件通过窄挂载落在宿主 `build/phase-02/current/docker/baseline-container.result.json`、`baseline-container.environment.json` 和 `baseline-container.md`。统一 dispatcher 另写 host envelope `build/phase-02/current/suite-baseline-host.result.json`、`.machine.json` 与 `.md`，以及 Docker envelope `build/phase-02/current/docker/suite-baseline-container.result.json`、`.machine.json` 与 `.md`。`result.json` 至少绑定：

- suite/schema 版本、baseline manifest/schema hash；
- validation-suites `contract_version` 与 registry hash；
- requirements lock hash；
- 全部 artifact/query/expected hashes；
- discovered/executed/passed/failed/skipped counts；
- 每个 case 的 expected、actual 和 assertion 明细；
- dispatcher、baseline runner、报告生成器和本次实际加载 helper 的路径与 SHA-256。

`environment.json` 记录 commit/dirty、OS、architecture、Python、pip 和 validator 版本。Host 轨从 Git 读取 commit 与 `git status --porcelain` dirty 状态。Container 轨读取镜像构建时传入的 `DSSC_SOURCE_COMMIT` 与 `DSSC_SOURCE_DIRTY`：前者必须是 40 位小写 Git commit，后者必须是 `true` 或 `false`；Compose 将二者作为 Docker build args 传给 `Dockerfile.validation`，镜像再把它们固化为环境变量和 OCI labels。缺失、`unknown` 或格式错误会使 baseline evidence provenance 进入程序 `ERROR`，源码变化后必须重建镜像。

Host/Docker 规范化比较允许 OS、architecture、平台路径和环境时间字段不同；case 集、oracle、artifact hashes、engine config 和语义结果必须完全一致。证据审计还要确认 container source commit 对应本次 host commit，dirty 值准确描述镜像构建时的源码状态。

## 7. Archive caveat

`archive/v0_validation_reports/README.md` 已明确这些报告来自旧环境。历史报告缺少当前 lock、manifest、runner/helper hashes、完整环境 inventory、target activation 和跨环境一致性证据；其中含个人解释器路径的旧 `all-validations-report.md` 已按公开策略排除。

因此 archive PASS 只用于回答“冻结模型过去预期表现为何”。当前 PASS 必须由 Phase 02 锁定环境重新执行产生，历史 Markdown 不复制为当前 evidence。若当前结构化结果与冻结 oracle 不一致，应保留失败 JSON、环境信息和差异，并按 Phase 02 人工介入规则处置。
