# 流程指令

- `v0/`：原 Phase 0–9 流程，按字节冻结。
- `v0.4/`：已经完成设计、等待从 Phase 00 开始逐阶段执行的 v0.4 流程；其中 [`human-intervention-policy.md`](v0.4/human-intervention-policy.md) 规定异常暂停、人工批准、有限修复、per-phase closure activation和发布终态仲裁，[`emergency-recovery-prompt.md`](v0.4/emergency-recovery-prompt.md) 持久化 recovery frontier、保护 downstream overlay并逐阶段恢复，Phase 09使用唯一 plan namespace、`ABANDONED|SUPERSEDED_COMPLETE|PRELOCK_INVALIDATED`递归lineage和不可覆盖的 payload/completion evidence refs。

两套流程必须分开维护，避免把历史完成声明带入新的验证周期。
