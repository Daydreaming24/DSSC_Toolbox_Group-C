# 当前质量评估区

`model-quality-assessment.md` 由
`C_Semantic_Treehouse/scripts/quality_metrics.py` 确定性生成。计算先校验五份统一
manifest 的 JSON Schema、hash 与跨记录语义，再从 release manifest 选择实际
RDF/SHACL 图和继承的 Energy Reading Record 合同。

规范输出：

- `build/validation/quality/results.json`：八类指标的机器真源；
- `build/validation/quality/report.md`：由机器真源生成的验证摘要；
- `build/validation/quality/run-environment.json`：独立环境侧车；
- `build/phase-06/quality/negative-controls.json`：五份 manifest 的重复 ID/悬空引用、SSSOM、指标合同与 freshness 负控；
- `build/phase-06/quality/determinism.json`：双次计算及输出 hash 证据。

所有 SSSOM 行当前保持 `PENDING_DOMAIN_REVIEW`，机器 PASS 表示结构、引用、
覆盖率和确定性门槛通过。领域批准继续等待具名人工审阅。
