# v0.4 四状态验收 fixtures

本目录由 `C_Semantic_Treehouse/manifests/v0.4-test-cases.json` 逐案绑定。每个 case 使用独立 fixture 文件和 SHA-256，运行时也各自构造提交 data graph；任何 fixture 字节漂移都会在验证前导致程序 `ERROR`。

- `pass/`：6 个预期 `PASS` case，包括仅含必填字段、合法可选字段以及相等时间边界。
- `fail/`：53 个预期 `FAIL` case，覆盖 D04-R001–D04-R016 的提交基数、字段、枚举、IRI、时间顺序及 Warning+Violation 优先级。
- `inapplicable/`：1 个仅命中 `ex:DatasetClosedShape` 契约内 Warning 的预期 `INAPPLICABLE` case。
- `untestable/`：6 个预期 `UNTESTABLE` case，覆盖 SUT 解析/离线加载失败以及预检后受控注入的 timeout、crash 和 service-runtime exception。

JSON-LD context 均内嵌或使用仓库相对路径；核心执行禁止 HTTP context fetch。D04-PC067–D04-PC070 是 authority、manifest、harness 与核心依赖预检的程序 `ERROR` 负控，不属于四状态 fixture manifest，由 Phase 05 self-test 单独执行。
