# 原始来源归档

两份 ZIP 的字节级冻结副本保存在 `inputs/source-archives/received/`，计划与仓库一同纳入 Git。复制后的 SHA-256 与仓库外原件一致。下列时间均为原件的 UTC 修改时间。

| 来源 | 仓库内冻结路径 | 大小（bytes） | UTC 修改时间 | 条目数 | SHA-256 |
|---|---|---:|---|---:|---|
| v0 核心基线：`DSSC_C_Semantic_Governance_Reproducible_Package_2026-06-25.zip` | `inputs/source-archives/received/` | 130092 | 2026-06-25 11:44:33 | 146 | `44f21783e57966c145c19e4c6edd74405bc1ace8ae2f31fae3f4bb92805d1135` |
| `DSSC_Tool_Learning.zip` | `inputs/source-archives/received/` | 30411 | 2026-06-09 13:35:21 | 38 | `ce13a59d3d3834bdc67d74616421ee9b19d262bfda8c4de69bfc7b5193012241` |

## 导入事实

- 核心 ZIP 不含 `.git/`，解压后有 145 个文件和 1 个显式目录条目。
- 核心 ZIP 的 141 个嵌套条目使用反斜杠分隔。此次在 Windows 上使用 `Expand-Archive` 安全提取；跨平台重建工具必须先规范化 `\` 与 `/`，并拒绝绝对路径和 `..` 路径。
- 任务 ZIP 含 20 个被排除的 macOS 元数据条目：19 个 `__MACOSX/` 下的 AppleDouble `._*` 和 1 个 `.DS_Store`。
- 去掉包装目录与元数据后得到 11 个有效文件；它们与旧工作区 `original_plan/` 中的 11 个有效文件逐文件 SHA-256 一致。
- 仓库内两份 ZIP 是规范性的冻结来源；解压目录是可审计派生结果，不取代 ZIP 原件。
- 核心 ZIP 内封装了 6 个含旧电脑绝对路径的历史条目；完整冻结策略保留这些原始字节，但对应解压副本已排除，风险见 `privacy-exclusions.md`。
- 用于追溯但未导入的新旧分界仓库 HEAD 为 `8c0c7542a6175064b925bcf827765659d5054883`。

完整条目和迁移哈希清单位于 [`manifests/`](manifests/)。
