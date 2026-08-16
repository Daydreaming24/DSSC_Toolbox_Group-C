# Codex Phase Prompts

下面给你一套 **Codex 分 phase 执行 prompt**。它按“工程 harness 先行、artifact 可验证、Semantic Treehouse 本地部署不阻塞主线”的原则设计。你的 C 组任务要求包括两个层次模型、版本化、导出可验证表示、与 A/D 组交接，以及四份报告和关系图；你前面确定的顶级路线还要求 SSSOM、CI、SPARQL、provenance、质量评估和双路径证据。 
使用方法：在 Codex 里先贴 **Master Prompt**，然后按 Phase 0 到 Phase 9 逐个贴。不要一次性让 Codex 做完全部；每 phase 结束后要求它运行验收命令并提交 evidence。

## Files

- [master-prompt.md](master-prompt.md)
- [phase-00-repository-audit-and-project-scaffold.md](phase-00-repository-audit-and-project-scaffold.md)
- [phase-01-core-vocabulary-and-versioned-semantic-artifacts.md](phase-01-core-vocabulary-and-versioned-semantic-artifacts.md)
- [phase-02-validation-harness-scripts-and-dockerized-tooling.md](phase-02-validation-harness-scripts-and-dockerized-tooling.md)
- [phase-03-sparql-competency-questions-and-semantic-tests.md](phase-03-sparql-competency-questions-and-semantic-tests.md)
- [phase-04-sssom-mapping-and-reuse-metrics.md](phase-04-sssom-mapping-and-reuse-metrics.md)
- [phase-05-provenance-and-version-governance-metadata.md](phase-05-provenance-and-version-governance-metadata.md)
- [phase-06-semantic-treehouse-local-deployment-evidence-track.md](phase-06-semantic-treehouse-local-deployment-evidence-track.md)
- [phase-07-reports-diagrams-and-handoff-contracts.md](phase-07-reports-diagrams-and-handoff-contracts.md)
- [phase-08-ci-pipeline-and-final-repository-hardening.md](phase-08-ci-pipeline-and-final-repository-hardening.md)
- [phase-09-final-qa-evidence-consolidation-and-no-regression-pass.md](phase-09-final-qa-evidence-consolidation-and-no-regression-pass.md)
- [emergency-recovery-prompt.md](emergency-recovery-prompt.md)
