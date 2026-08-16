# Phase 02：验证工具链、脚本与 Docker 化复现

## 1. 本阶段解决的问题

Phase 02 的核心目标是把 Phase 01 产出的语义文件变成“可自动验证”的工程产物。也就是说，项目不再只拥有一组模型文件，而是拥有一条能反复运行的验证流水线。

`prompts/phase-02-validation-harness-scripts-and-dockerized-tooling.md` 对本阶段的目标写得很清楚：

```text
Create a robust independent local validation harness that can run without Semantic Treehouse.
```

这句话是整个项目的核心工程原则之一。Semantic Treehouse 是 C 组研究的工具对象，但最终交付不能只依赖 Treehouse UI。Phase 02 因此建立了一个独立 validation harness，使模型文件本身可以被本地 Python 工具和 Docker 环境验证。

## 2. 为什么 Phase 02 很关键

在 Phase 01 中，项目已经有了 ontology、JSON-LD、SHACL、JSON Schema 和 OpenAPI，但这些文件如果只靠人工阅读，很难证明它们真的有效。Phase 02 解决了以下问题：

| 问题 | Phase 02 的解决方式 |
|---|---|
| Turtle 是否语法正确？ | 用 `rdflib` 解析 RDF/Turtle。 |
| JSON-LD 是否可以展开？ | 用 `pyld` 做 JSON-LD expansion。 |
| valid metadata 是否真的符合 SHACL？ | 用 `pyshacl` 验证 valid case。 |
| invalid metadata 是否按预期失败？ | 用 `pyshacl` 验证 negative case，并把预期失败视为 harness success。 |
| record payload 是否符合 schema？ | 用 `jsonschema` 验证 valid/invalid record。 |
| OpenAPI fragment 是否结构合法？ | 用 YAML parser 和 `openapi-spec-validator` 检查。 |
| 别人机器上能否复现？ | 增加 `Dockerfile.validation` 和 `docker-compose.validation.yml`。 |

这一步把项目从“语义建模草稿”推进到“可复现实验包”。

## 3. 新增依赖

Phase 02 创建了 `C_Semantic_Treehouse/requirements.txt`，其中包含：

```text
rdflib>=7.0.0
pyshacl>=0.26.0
pyld>=2.0.4
jsonschema>=4.22.0
PyYAML>=6.0.1
openapi-spec-validator>=0.7.1
```

这些库分别对应验证链路中的不同层：

- `rdflib`：RDF/Turtle parsing。
- `pyshacl`：SHACL validation。
- `pyld`：JSON-LD expansion。
- `jsonschema`：JSON Schema validation。
- `PyYAML`：OpenAPI YAML parsing。
- `openapi-spec-validator`：OpenAPI 结构检查。

这也说明项目没有把 validation 写成纯文本 checklist，而是尽量交给已有标准工具执行。

## 4. 新增脚本

根据 `C_Semantic_Treehouse/PHASE_2_SUMMARY.md`，本阶段创建了：

| 脚本 | 作用 |
|---|---|
| `scripts/validation_common.py` | 提供路径、报告写入、状态记录等公共逻辑。 |
| `scripts/validate_rdf.py` | 验证 Turtle/RDF 文件可解析。 |
| `scripts/validate_jsonld.py` | 验证 JSON-LD 文件可解析和展开。 |
| `scripts/validate_shacl.py` | 运行 SHACL valid/invalid cases。 |
| `scripts/validate_jsonschema.py` | 运行 record JSON Schema valid/invalid cases。 |
| `scripts/validate_openapi.py` | 检查 OpenAPI fragment。 |
| `scripts/run_all_validations.py` | 统一调用 RDF、SHACL、JSON-LD、JSON Schema、OpenAPI 检查。 |

这些脚本生成的报告包括：

```text
validation/rdf-validation-report.md
validation/jsonld-validation-report.md
validation/pyshacl-validation-report.md
validation/jsonschema-validation-report.md
validation/openapi-validation-report.md
validation/all-validations-report.md
```

## 5. Makefile 如何串起验证链路

后续 `Makefile` 中的 `validate` target 最终变成：

```makefile
validate:
	@python $(PACKAGE_DIR)/scripts/run_all_validations.py
	@$(MAKE) test-sparql
	@$(MAKE) quality
	@$(MAKE) validate-governance
	@$(MAKE) check-links-and-paths
	@$(MAKE) check-required-files
	@$(MAKE) evidence
	@echo "Local validation harness completed."
```

Phase 02 主要负责其中第一段，也就是 `run_all_validations.py` 调用的基础验证。后续 Phase 03、04、05、08 再把 SPARQL、quality、governance 和 hardening check 接进去。

Windows wrapper `make.cmd` 也同步支持：

```bat
cmd /c make validate-rdf
cmd /c make validate-shacl
cmd /c make validate-jsonld
cmd /c make validate-jsonschema
cmd /c make validate-openapi
cmd /c make validate
```

这让 Windows 成员无需安装 GNU Make 也能运行。

## 6. SHACL 验证：valid 与 invalid 都是证据

`C_Semantic_Treehouse/validation/expected-results.md` 明确规定：

```text
Expected failing case:

- `model/v0.2/data-product-invalid.jsonld` must fail because:
  - `providerName` is missing.
  - `unit` is `MWh` instead of `kWh`.
  - `temporalEnd` is missing.

This expected failure is a successful harness outcome.
```

这句话非常重要。验证流水线的目的不是让所有输入都通过，而是让 valid case 通过、invalid case 按预期失败。只有这样，才能证明约束真的生效。

`validation/pyshacl-validation-report.md` 中记录：

```text
### v0.2 invalid metadata fails as expected

Status: PASS
Expected: does not conform
Actual conforms: False
```

它还列出了 3 个违反点：

```text
Message: unit must be kWh in v0.2.
Message: temporalEnd is required and must be an xsd:date.
Message: providerName is required and must be a string.
```

这刚好对应任务场景中要求 D 组解释的三个 validation failure。

## 7. JSON Schema 验证

除了 metadata 的 SHACL 验证，Phase 02 也验证 v0.3 的 record payload。

`validation/jsonschema-validation-report.md` 中写明：

```text
### Energy Reading Record schema is valid

Status: PASS

`model/v0.3/energy-reading-record.schema.json` is a valid Draft 7 schema.
```

valid record 通过：

```text
### Valid Energy Reading Record passes

Status: PASS

`model/v0.3/energy-reading-record-valid.jsonld` conforms.
```

invalid record 按预期失败：

```text
### Invalid Energy Reading Record fails as expected

Status: PASS

First error: 'meterId' is a required property
```

`model/v0.3/energy-reading-record-invalid.jsonld` 里确实没有 `meterId`，同时还包含 `timestamp: "not-a-date-time"`、`energyKWh: "12.4"` 和 `unit: "MWh"`。因此这个 negative case 同时覆盖 required field、format/type 和 enum 约束。

## 8. OpenAPI 验证

`validation/openapi-validation-report.md` 记录：

```text
Overall status: PASS

`model/v0.3/openapi-fragment.yaml` parsed successfully.
Spec passed `openapi-spec-validator`.
```

这说明 v0.3 中的 API 描述不仅是 YAML 文本，而且符合 OpenAPI validator 的结构要求。

OpenAPI fragment 的核心路径是：

```yaml
/energy/buildings/hourly:
  get:
    summary: Return hourly building energy readings.
```

它返回的是 `EnergyReadingRecord` 数组，和 JSON Schema 的 record 结构保持一致。

## 9. JSON-LD 验证

Phase 02 开始使用 `pyld` 做 JSON-LD expansion。`validation/expected-results.md` 说明：

```text
Local sibling context files are inlined by the validation harness so validation
does not depend on network access.
```

这解决了一个常见复现问题：JSON-LD 中如果引用本地 context 或网络 context，验证时可能因为路径或网络不可用而失败。Phase 02 的 harness 通过处理本地 sibling context，使验证尽量不依赖外部网络。

## 10. Docker 化复现

Phase 02 新增两个根目录文件：

| 文件 | 作用 |
|---|---|
| `Dockerfile.validation` | 构建 Python 3.12 验证环境，安装 `make` 和 Python dependencies。 |
| `docker-compose.validation.yml` | 用 compose 启动 validation service，挂载仓库并运行 `make validate`。 |

`Dockerfile.validation` 的核心逻辑是：

```dockerfile
FROM python:3.12-slim
WORKDIR /workspace
RUN apt-get update \
    && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/*
COPY C_Semantic_Treehouse/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
CMD ["make", "validate"]
```

`docker-compose.validation.yml` 则把仓库挂到 `/workspace`：

```yaml
services:
  validation:
    build:
      context: .
      dockerfile: Dockerfile.validation
    working_dir: /workspace
    volumes:
      - .:/workspace
    command: ["make", "validate"]
```

这样即使本机 Python 环境不同，也可以通过 Docker 复现验证。

## 11. 本阶段运行结果

`PHASE_2_SUMMARY.md` 记录了本阶段运行：

```text
python -m pip install -r C_Semantic_Treehouse\requirements.txt
cmd /c make validate-shacl
cmd /c make validate
docker compose -f docker-compose.validation.yml run --rm validation
```

通过项包括：

- `cmd /c make validate` 本地端到端通过。
- Docker Compose validation 端到端通过。
- 所有 validation reports 被创建。
- v0.2 invalid metadata 因三项预期错误失败。
- v0.3 invalid record 按 JSON Schema 预期失败。

报告也诚实记录了一个 Docker 本地问题：

```text
The first direct Docker Compose build failed because the local Docker credential helper
`docker-credential-desktop` was not available in `%PATH%`.
```

这个问题后来通过临时空 `DOCKER_CONFIG` 解决。它不是仓库配置错误，而是本地 Docker Desktop credential 配置问题。

## 12. 对模型本身的小调整

Phase 02 修改了 `model/v0.3/energy-reading-record-shapes.ttl`：

```text
now checks `energyKWh` as a non-negative numeric literal instead of requiring strict `xsd:decimal`.
```

原因是 JSON-LD 数字展开时的 datatype 可能和严格 `xsd:decimal` 不完全一致。这个调整体现了验证工程中的现实取舍：

- SHACL 检查能源值非负，保证语义约束。
- JSON Schema 继续要求 JSON number，保证 API payload 类型。

这比死守一种 RDF datatype 更适合跨 JSON-LD 和 API payload 的 demo。

## 13. 对后续阶段的影响

Phase 02 之后，项目拥有了权威验证路径：

```bat
cmd /c make validate
```

这条路径后来被：

- Phase 03 的 SPARQL tests 扩展。
- Phase 04 的 quality metrics 扩展。
- Phase 05 的 governance validation 扩展。
- Phase 08 的 required-files 和 path-link check 扩展。
- Phase 09 的 final no-regression pass 使用。

也就是说，Phase 02 使所有后续工作都可以接入统一 validation harness。

## 14. 研讨展示建议

讲 Phase 02 时，建议重点展示“invalid case 是成功证据”：

1. 打开 `model/v0.2/data-product-invalid.jsonld`，指出缺 `providerName`、`unit = MWh`、缺 `temporalEnd`。
2. 打开 `validation/pyshacl-validation-report.md`，展示三条 violation message。
3. 解释：pipeline overall PASS，不是因为 invalid 数据通过了，而是因为 invalid 数据按预期失败了。

可以现场运行：

```bat
cmd /c make validate-shacl
cmd /c make validate-jsonschema
cmd /c make validate
```

最后总结：

> Phase 02 把 C 组模型从“写出来”推进到“可证明”。它让模型文件、正例、反例、验证报告和 Docker 复现环境形成了一条完整证据链。

