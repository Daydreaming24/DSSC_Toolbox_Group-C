# DSSC C 组 v0.4 Emergency Recovery Prompt（已合并）

状态恢复相关内容已合并进 [`human-intervention-policy.md`](human-intervention-policy.md) 第 3 节“状态恢复（原 Emergency Recovery）”，与"什么时候要停下来找人确认"合并成一份文档，避免两份文件各自维护一套规则、互相漂移。

遇到上下文丢失、当前 Phase 状态不明、验证从已知通过变为失败、工作树出现意外修改、环境或 CI 与本机结果不一致等情况时，直接阅读 `human-intervention-policy.md` 第 3 节，按其中的读取顺序、保护范围、恢复步骤和必须产出执行。

本文件保留为重定向说明，暂不删除，避免仓库中其余引用本文件名的 Phase prompt 出现死链；这些引用会在后续精简 Phase 00–09 prompt 时一并更新为指向 `human-intervention-policy.md`。
