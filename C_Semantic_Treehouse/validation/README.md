# 当前验证区

`expected-results.md` 是从 v0 基线保留并补充当前执行合同的规范输入。机器可读 oracle 位于 `manifests/baseline-test-cases.json`，runner 不会根据实际输出回写 expected。

统一入口：

```text
.\scripts\validate.ps1 -Suite baseline
.\.venv\Scripts\python.exe -I scripts\validate.py --suite baseline
docker compose -f docker-compose.validation.yml run --rm validation --suite baseline
```

Host 和 Docker 各自产生确定性 result JSON、machine environment JSON 和由 JSON 渲染的 Markdown。suite dispatcher 写入 `build/phase-02/current/`，container 文件通过专用窄挂载进入 `build/phase-02/current/docker/`。比较忽略 OS/architecture 等机器差异，要求 case IDs、oracle、artifact hashes 和语义结果一致。

所有 JSON-LD context 只从 manifest 绑定的仓库文件加载，网络请求失败关闭。旧报告位于 `archive/v0_validation_reports/`，只用于历史差异对照，不代表当前 lock、代码或机器环境。经过 secrets、绝对路径、hash freshness 和稳定顺序审核的选定证据才会进入 `evidence/releases/v0.4/baseline/`。
