# 迁移完整性说明

迁移采用“重新提取、再重排”的方式：核心基线直接来自核心 ZIP；原始任务材料来自独立暂存提取；后续材料从只读参考目录逐文件复制。

验收要求：

- 核心 ZIP 的 145 个文件在初始迁移时均有唯一目标，重排前后 SHA-256 相同；其中 6 个含个人绝对路径的副本随后按公开策略排除。
- `inputs/original-plan/` 仅含 11 个有效文件，不含包装目录或 macOS 元数据。
- 旧物理来源目录 `v1_docs/` 到 `archive/v0_docs/`、D 组两份输入和 `806.md` 的源/目标 SHA-256 相同。
- 冻结文件使用 `.gitattributes` 的 `-text` 规则，避免 Git 行尾转换破坏字节级哈希。
- 旧 `.git/` 和迁移暂存目录不会进入新仓库；两份原始 ZIP 则作为显式冻结输入保存在 `inputs/source-archives/received/`。
- 另有 1 个来自外部 `v1_docs/` 的含路径文件被排除；7 个公开排除项均保存原哈希与恢复来源。

机器生成的逐文件证据见 `manifests/*-migration-hash-map.tsv`；其中的 `Match=True` 记录复制完成时的源/目标一致性。随后执行的公开隐私排除以 `manifests/privacy-exclusions.tsv` 为准。当前公开树的冻结文件由 `scripts/verify_frozen_files.py` 校验。

Git 初始化前的 221 个文件路径快照见 `manifests/repository-files-at-migration.txt`；该快照已在版本命名修订后重新生成。
