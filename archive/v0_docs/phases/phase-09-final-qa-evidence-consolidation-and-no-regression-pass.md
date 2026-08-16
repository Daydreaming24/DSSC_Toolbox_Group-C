# Phase 09：最终 QA、证据汇总与无回归检查

## 1. 本阶段解决的问题

Phase 09 是整个项目的收尾阶段。它的任务不是大规模新增功能，而是做最终无回归检查，并把证据汇总成可以提交和展示的最终包。

`prompts/phase-09-final-qa-evidence-consolidation-and-no-regression-pass.md` 的目标是：

```text
Perform a final no-regression pass and consolidate evidence into a grading-ready package.
```

这里的重点是：

- no-regression：前面阶段已经通过的验证不能在最后被破坏。
- evidence consolidation：把分散在 validation、quality、governance、evidence、handoff、docs 中的证据汇总成最终说明。
- no false claims：不能把 partial 项写成 done，不能隐藏 Treehouse caveat。

## 2. Phase 09 要运行的命令

Prompt 要求运行：

```text
make clean
make validate
make quality
make test-sparql
make check-required-files
```

在本 Windows 项目中，对应常用入口是：

```bat
cmd /c make clean
cmd /c make validate
cmd /c make quality
cmd /c make test-sparql
cmd /c make check-required-files
```

这些命令覆盖：

- 清理缓存。
- 全量验证。
- 质量指标。
- SPARQL 能力问题。
- 必需文件检查。

## 3. 最终需要检查的验证报告

Prompt 明确要求检查：

```text
validation/pyshacl-validation-report.md
validation/jsonschema-validation-report.md
validation/openapi-validation-report.md
validation/sparql-competency-question-report.md
validation/governance-validation-report.md
validation/required-files-report.md
validation/path-link-report.md
```

这些报告分别来自：

| 报告 | 对应阶段 | 证明什么 |
|---|---|---|
| `pyshacl-validation-report.md` | Phase 02 | metadata 和 record SHACL valid/invalid 行为正确。 |
| `jsonschema-validation-report.md` | Phase 02 | Energy Reading Record JSON Schema 正负例正确。 |
| `openapi-validation-report.md` | Phase 02 | OpenAPI fragment 可解析并通过 validator。 |
| `sparql-competency-question-report.md` | Phase 03 | 模型能回答八个语义治理问题。 |
| `governance-validation-report.md` | Phase 05 | governance 文件和 provenance 完整可解析。 |
| `required-files-report.md` | Phase 08 | minimum/excellent/top-tier 文件齐全。 |
| `path-link-report.md` | Phase 08 | 本地链接和脚本路径没有明显问题。 |

Phase 09 的作用就是把这些 evidence 串起来，形成最终叙述。

## 4. 全量验证结果

`validation/all-validations-report.md` 中写：

```text
Overall status: PASS
```

报告列出基础检查：

```text
validate_rdf.py | Status: PASS
validate_shacl.py | Status: PASS
validate_jsonld.py | Status: PASS
validate_jsonschema.py | Status: PASS
validate_openapi.py | Status: PASS
```

后续 `make validate` 还会继续运行：

- `test-sparql`
- `quality`
- `validate-governance`
- `check-links-and-paths`
- `check-required-files`
- `evidence`

因此最终 PASS 表示核心模型、验证脚本、语义测试、质量、治理和硬化检查都没有回归。

## 5. invalid examples 的处理

Phase 09 特别要求：

```text
Ensure invalid examples are reported as expected failures, not pipeline failures.
```

最终 `FINAL_SUMMARY.md` 中专门写：

```text
The pipeline passes because invalid examples fail for intended reasons:

- v0.2 invalid metadata fails SHACL because `providerName` is missing,
  `unit` is `MWh`, and `temporalEnd` is missing.
- v0.3 invalid Energy Reading Record fails JSON Schema,
  with `meterId` reported as the first required-property error.
```

这段很适合放进展示。它解释了为什么 report 中会看到 invalid 数据失败，但 overall pipeline 仍然 PASS。

## 6. Treehouse claims 的最终核对

Phase 09 要求检查 `C_semantic_treehouse_usage.md` 是否诚实区分：

- Semantic Treehouse local deployment evidence。
- independent local validation evidence。
- unavailable/failed functions if any。

最终 `FINAL_SUMMARY.md` 的 Known Limitations 写：

```text
Semantic Treehouse local UI smoke check succeeded on `http://localhost:4200/`,
but full manual UI workflow screenshots are still a documented partial item.
```

还写：

```text
Semantic Treehouse backend/root HEAD check on `http://localhost:8014/`
timed out in the local evidence run.
```

这说明 Phase 09 没有把 Phase 06 的 partial caveat 抹掉，而是继续放在最终限制中。

## 7. Cross-group handoff 的最终核对

Phase 09 要求确保：

```text
A group can use metadata fields and JSON-LD.
D group can run SHACL validation.
B group can optionally reference model URI/provenance.
```

最终仓库有三份 handoff：

| 文件 | 对象 | 说明 |
|---|---|---|
| `handoff/handoff-to-A-offering-metadata.md` | A 组 | 提供 nine required metadata fields、JSON-LD example、v0.3 model URI、endpoint/DataService recommendation。 |
| `handoff/handoff-to-D-shacl-validation.md` | D 组 | 提供 shapes、valid/invalid examples、validation commands、invalid case 解释。 |
| `handoff/handoff-to-B-model-uri-provenance.md` | B 组 | 提供 v0.3 model URI、namespace、validation report、provenance metadata reference。 |

B 组 handoff 中写：

```text
B Group can optionally reference the C Group semantic model URI and provenance metadata
when describing connector behavior, policy references, provenance, or integration evidence.
```

这说明 B 组不是 C 组模型的主要消费者，但可以在 compliance / credential / policy narrative 中引用模型 URI 和 provenance。

## 8. FINAL_SUMMARY 的创建

Phase 09 最重要的新文件是：

```text
C_Semantic_Treehouse/FINAL_SUMMARY.md
```

它包含：

1. What Was Built。
2. How To Run Validation。
3. Evidence For Minimum Requirements。
4. Evidence For Excellent And Top-Tier Requirements。
5. Invalid Examples Are Expected Failures。
6. Known Limitations。
7. Suggested Next Steps。

这个文件就是最终交付包的“入口级总结”。

## 9. Final Summary：项目建成了什么

`FINAL_SUMMARY.md` 开头写：

```text
This package builds a reproducible Semantic Governance Package for the Building Energy Consumption Data Product.
```

它列出 core model：

```text
- Data Product Metadata semantic model for catalogue/offering/SHACL validation.
- Energy Reading Record semantic model for API payload validation.
- Versioned releases v0.1, v0.2, and v0.3 under `model/`.
```

然后列出 engineering and governance assets：

```text
- RDF/Turtle ontology artifacts.
- JSON-LD contexts and valid/invalid examples.
- SHACL shapes.
- JSON Schema and OpenAPI fragment.
- SSSOM semantic mapping table.
- SPARQL competency questions.
- Governance docs, changelog, provenance JSON-LD, namespace/release/deprecation policies.
- Semantic Treehouse local deployment evidence.
- Independent local validation harness.
- A, B, and D group handoff notes.
- CI workflow and hardening checks.
```

这就是项目最终形态的完整概括。

## 10. Final Summary：如何运行验证

`FINAL_SUMMARY.md` 给出主命令：

```bat
cmd /c make validate
```

并给出 focused commands：

```bat
cmd /c make validate-shacl
cmd /c make validate-jsonschema
cmd /c make validate-openapi
cmd /c make test-sparql
cmd /c make quality
cmd /c make check-required-files
cmd /c make check-links-and-paths
```

这适合放在最终展示的“复现方式”页。

## 11. Minimum requirements evidence

`FINAL_SUMMARY.md` 将最低要求映射到证据：

```text
Two models | `C_semantic_model_design.md`; `model/v0.3/building-energy-ontology.ttl`
v0.1/v0.2/v0.3 | `C_model_versioning_demo.md`; `model/v0.1/`; `model/v0.2/`; `model/v0.3/`
SHACL or equivalent validation artifact | `model/v0.3/data-product-metadata-shapes.ttl`; `model/v0.3/energy-reading-record-shapes.ttl`
Semantic Treehouse usage record | `C_semantic_treehouse_usage.md`; `evidence/semantic-treehouse-local-deployment.md`
Relationship diagram | `diagrams/metadata-record-model.mmd`
Validation pass | `validation/all-validations-report.md`
```

这张表非常适合直接作为答辩中的 evidence slide。

## 12. Excellent 和 Top-tier requirements evidence

`FINAL_SUMMARY.md` 还列出：

```text
Standards alignment | `mappings/external-standard-alignment.sssom.tsv`; `C_semantic_model_design.md`
JSON-LD context | `model/v0.3/data-product-context.jsonld`; `model/v0.3/energy-reading-record-context.jsonld`
JSON Schema and OpenAPI | `model/v0.3/energy-reading-record.schema.json`; `model/v0.3/openapi-fragment.yaml`
SPARQL competency questions | `tests/sparql/competency-questions.md`; `validation/sparql-competency-question-report.md`
Quality metrics | `quality/model-quality-assessment.md`; `validation/quality-metrics-report.md`
CI pipeline | `.github/workflows/validate.yml`
AI-assisted human governance | `docs/ai-assisted-human-governed-semantic-modeling.md`
```

这说明项目不仅满足 minimum，还覆盖了 top-tier 的多个扩展项。

## 13. Known Limitations 的意义

Final Summary 中列出的限制包括：

```text
- Semantic Treehouse local UI smoke check succeeded on `http://localhost:4200/`,
  but full manual UI workflow screenshots are still a documented partial item.
- Semantic Treehouse backend/root HEAD check on `http://localhost:8014/`
  timed out in the local evidence run.
- Mermaid diagrams passed static syntax checks, but render-level validation was not run
  because Mermaid CLI was not installed.
- Provider, location, and unit modeling remain lightweight for the demo;
  production profiles should use organization/place nodes and QUDT/UCUM unit IRIs.
- The current directory is not a git repository, so `git status --short`
  cannot produce a working-tree summary.
```

这些限制让最终报告更可信。项目不是声称“什么都完成到生产级”，而是清楚区分 demo 成果和生产级后续工作。

## 14. Final Checklist 与 Final Summary 的关系

`docs/final-checklist.md` 是按验收项逐条勾选，`FINAL_SUMMARY.md` 是按项目叙事汇总证据。二者互补：

- checklist 适合审查“有没有缺项”。
- final summary 适合展示“项目整体做成了什么”。

Phase 09 要求：

```text
Ensure docs/final-checklist.md has no unjustified “done” status.
```

最终 checklist 保留了 Known Partials：

```text
Semantic Treehouse full manual UI workflow screenshots | partial
Mermaid render-level validation | partial
```

这说明 done 状态有证据支撑，partial 项没有被强行改成 done。

## 15. 本阶段没有新增概念范围

Prompt 明确要求：

```text
Do not add new conceptual scope in this phase unless needed to fix a gap.
```

这很重要。Phase 09 的工作不是突然增加新模型、新标准或新字段，而是确保既有成果一致、可运行、可解释。

如果在最后阶段临时增加概念范围，容易导致：

- validation 没有覆盖。
- handoff 文档不一致。
- final checklist 无法映射证据。
- demo script 讲不清楚。

因此 Phase 09 主要做 QA 和 consolidation。

## 16. 项目最终状态

从最终文件看，项目已经形成完整结构：

```text
C_Semantic_Treehouse/
  model/v0.1/
  model/v0.2/
  model/v0.3/
  validation/
  tests/sparql/
  mappings/
  quality/
  governance/
  evidence/
  handoff/
  diagrams/
  docs/
  scripts/
  FINAL_SUMMARY.md
```

根目录还有：

```text
Makefile
make.cmd
Dockerfile.validation
docker-compose.validation.yml
.github/workflows/validate.yml
```

这说明项目既有研究文档，也有可执行验证入口。

## 17. 研讨展示建议

Phase 09 可以作为最后一页总结：

> 最后阶段没有再扩展模型，而是做 no-regression pass，把所有证据汇总成 final summary。最终包可以通过 `cmd /c make validate` 复现验证，invalid examples 按预期失败，Treehouse 证据和 caveat 都被如实记录，minimum/excellent/top-tier 要求都能在 checklist 和 final summary 中找到对应证据。

建议现场打开：

- `C_Semantic_Treehouse/FINAL_SUMMARY.md`
- `C_Semantic_Treehouse/docs/final-checklist.md`
- `C_Semantic_Treehouse/validation/all-validations-report.md`
- `C_Semantic_Treehouse/validation/required-files-report.md`

如果时间足够，可以运行：

```bat
cmd /c make validate
```

然后以 `FINAL_SUMMARY.md` 的 Known Limitations 结尾，说明项目已经可复现，但也清楚知道哪些部分仍是 demo 级或 partial evidence。

