# D 组 v0.4 输入

- 来源：DSSC Toolbox D 组
- 接收/登记日期：2026-08-07
- 维护责任：DSSC Toolbox C 组
- 用途：定义 C 组 v0.4 元数据模型的验证契约与验收要求

## 权威性

`received/building-energy-shapes_D.ttl` 是规范性、可执行的权威契约。`received/初始TTL到最终TTL修改说明.md` 是解释性材料。若二者存在不一致，以 TTL 的实际约束为待核验事实，同时在需求追踪中记录问题；不得静默修改任一收到的原件。

任何 C 组适配都必须写入新的派生文件，并记录源文件路径与 SHA-256。D 组若发送修订版，应新增版本目录，不覆盖本目录。

## 完整性

从本目录运行：

```bash
sha256sum -c SHA256SUMS
```

Windows 可使用 `Get-FileHash -Algorithm SHA256 received/*` 并与 `SHA256SUMS` 对照。
