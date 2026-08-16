# Emergency Recovery Prompt for Codex

Use this only if a previous phase became messy or validation is failing.

You are in the C Group Semantic Governance repository. Do not add new scope. Stabilize the repository.

Tasks:

1. Inspect current files and git status.
2. Identify the smallest set of failures blocking make validate.
3. Fix only validation-breaking issues.
4. Preserve all semantic intent:

   * Data Product Metadata model
   * Energy Reading Record model
   * v0.1/v0.2/v0.3
   * SHACL valid/invalid behavior
   * JSON-LD, JSON Schema, OpenAPI
   * SPARQL competency questions
   * SSSOM mappings
   * governance/provenance metadata
   * handoff docs
5. Do not rewrite reports unless necessary.
6. Do not remove evidence files.
7. Do not make Semantic Treehouse deployment required for make validate.
8. If Semantic Treehouse scripts fail, document the failure in evidence and keep independent validation working.

Commands to run:

* make validate
* make check-required-files
* git status --short

Output:

* root cause summary
* files changed
* commands run
* pass/fail status
* remaining manual tasks

我建议执行顺序是：Phase 0–5 先完成核心 artifact 和 independent validation；Phase 6 再尝试 Semantic Treehouse 本地部署；Phase 7–9 负责报告、CI 和最终收口。这样即使 Semantic Treehouse Docker 部署卡住，你的 C 组仍然有完整、可验证、可交付的顶级工程包。

