# 公开仓库隐私排除项

迁移审计发现 7 个历史文件含旧电脑用户名、桌面路径、解释器路径或临时目录。这些解压副本不进入可浏览的公开工作树；其中 6 个来自核心 ZIP 的原始字节按用户要求仍封装在 `inputs/source-archives/received/` 的冻结 ZIP 中，另一个来自旧物理目录 `v1_docs/` 的 v0 基线文档可从只读参考来源恢复。

因此，“公开树不含个人绝对路径”只适用于 ZIP 外的解压文件。完整 ZIP 原件是显式例外：发布 ZIP 也会使其内部历史路径可被下载者解压查看，推送 GitHub 前必须人工确认。

| 新仓库中原拟路径 | 恢复来源 | 原文件 SHA-256 |
|---|---|---|
| `archive/v0_validation_reports/all-validations-report.md` | 核心 ZIP：`C_Semantic_Treehouse/validation/all-validations-report.md` | `ee1477c4de0d74a62c44aea064ac2009c29f4ac8d32f4e742b455c3d7d55e728` |
| `archive/v0_docs/phases/phase-08-ci-pipeline-and-final-repository-hardening.md` | 外部只读参考目录：`v1_docs/phases/phase-08-ci-pipeline-and-final-repository-hardening.md` | `e3a4aa4b20e7143ac1e9b5c7426416533b68679ce648e7cf343241b4d69ef75e` |
| `archive/v0_evidence/C_Semantic_Treehouse/evidence/semantic-treehouse-local-deployment.md` | 核心 ZIP：同相对路径 | `981e1c841e17ac06d934a0f73ff8ae5e5c18ecdb327603871e313e6600a6f433` |
| `archive/v0_evidence/C_Semantic_Treehouse/evidence/treehouse-compose-candidates.txt` | 核心 ZIP：同相对路径 | `272e08b1e4cc0e6f6f067e0e487979678de5dd55ac9f5cbb1214fc5d216f01d3` |
| `archive/v0_evidence/C_Semantic_Treehouse/evidence/treehouse-compose-file.txt` | 核心 ZIP：同相对路径 | `eac48402e77908c5ee8d8c50a0f80cef41b2c6801faf9c041847621eedf96f6c` |
| `archive/v0_evidence/C_Semantic_Treehouse/evidence/treehouse-docker-compose.log` | 核心 ZIP：同相对路径 | `0a5d79a0b72a9ae57beccdd749355709ecca056b1c82c6183daf978f88d3e62a` |
| `archive/v0_phase_summaries/PHASE_8_SUMMARY.md` | 核心 ZIP：`C_Semantic_Treehouse/PHASE_8_SUMMARY.md` | `4ab56c1aac032a51f7581db74cc90a8cd74687c37b29a05cd50036db45971579` |

逐条机器可读记录见 `manifests/privacy-exclusions.tsv`。这里记录的是明确、透明的发布排除，不是验证或迁移遗漏。
