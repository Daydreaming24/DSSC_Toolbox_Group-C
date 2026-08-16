# 原始 ZIP 冻结区

本目录保存建立新仓库所依据的两个字节级原件。它们纳入 Git 是为了让全新 clone 不依赖额外的本机文件即可复核来源和重新执行迁移审计。

| 文件 | 角色 | SHA-256 |
|---|---|---|
| `received/DSSC_C_Semantic_Governance_Reproducible_Package_2026-06-25.zip` | v0 核心仓库来源 | `44f21783e57966c145c19e4c6edd74405bc1ace8ae2f31fae3f4bb92805d1135` |
| `received/DSSC_Tool_Learning.zip` | 原始任务计划来源 | `ce13a59d3d3834bdc67d74616421ee9b19d262bfda8c4de69bfc7b5193012241` |

治理规则：

- 文件名、内容和压缩结构均冻结，不得原地修改或重新压缩。
- 修订来源必须新增版本化文件，不得覆盖现有原件。
- ZIP 内含的 macOS 元数据可以在派生目录中排除，但 ZIP 原件本身保持不变。
- 仓库内的解压内容与 ZIP 原件之间通过 `docs/provenance/manifests/` 的条目和哈希证据关联。
- 核心 ZIP 内有 6 个历史条目包含旧电脑绝对路径。它们因“完整冻结原件”策略仍封装在 ZIP 中，但不作为解压副本发布；详情见 `docs/provenance/privacy-exclusions.md`。
- 公开推送前必须由维护者确认：保留完整来源 ZIP 的可追溯价值高于其中历史路径的披露风险。

从本目录运行以下命令可验证原件：

```bash
sha256sum -c SHA256SUMS
```

Windows 可使用 `Get-FileHash -Algorithm SHA256 received/*.zip` 并与 `SHA256SUMS` 对照。
