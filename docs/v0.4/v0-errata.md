# v0 基线已知问题与迁移勘误

本文件只记录已确认的问题，不回写冻结的 v0 基线材料。

1. `inputs/original-plan/DSSC_Toolbox_Research_Task_Plan.md` 保留了来源文件中的 `D:\...` 场景路径。它们是原任务的历史位置表达，不是本仓库当前路径；当前文件均位于 `inputs/original-plan/`。
2. v0 基线模型使用 `be:DataProductMetadata`、`dct:identifier`、`be:*` 路径和 `format = "JSON"`；D 组 v0.4 契约要求显式 `dcat:Dataset`、`ex:/dcat:/dct:` 扁平路径和 `application/json`。因此 v0.4 是不兼容的 wire-profile 迁移，不能描述成对 v0.3 Shape 的简单增强。
3. 旧 SHACL 验证器只比较 `conforms` 布尔值，没有解析 report graph 或断言目标节点实际命中，存在空目标假 PASS 风险。
4. 旧 OpenAPI 验证器在缺少 `openapi-spec-validator` 时可降级为 PASS，不符合当前 fail-closed 要求。
5. 旧 SHACL、JSON Schema、OpenAPI、SPARQL、quality、governance 和 required-files 流程多处硬编码 v0.3；不能直接用于 v0.4。
6. 旧依赖、基础镜像和 CI runner 使用浮动版本；旧 GitHub Actions 未形成可核验的真实远程运行证据。
7. v0 Treehouse 证据只代表旧机器的非阻塞证据轨，且上游 clone/compose 选择未形成稳定锁定。
8. 7 个含个人绝对路径的历史文件未进入公开工作树；原哈希和恢复来源见 `docs/provenance/privacy-exclusions.md`。

以上问题必须在 v0.4 prompts、release manifest、验证器和复现文档中显式解决。
