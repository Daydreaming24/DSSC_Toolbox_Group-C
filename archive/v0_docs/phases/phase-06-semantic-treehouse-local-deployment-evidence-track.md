# Phase 06：Semantic Treehouse 本地部署证据轨

## 1. 本阶段解决的问题

Phase 06 专门处理 Semantic Treehouse 本地部署和证据收集。和前面几个阶段不同，本阶段不是验证模型文件本身，而是尝试把 C 组研究对象 Semantic Treehouse 在本地通过 Docker 跑起来，并记录真实结果。

`prompts/phase-06-semantic-treehouse-local-deployment-evidence-track.md` 对本阶段定位非常明确：

```text
Create a non-blocking local Docker-based Semantic Treehouse deployment evidence track.
```

其中最重要的词是 non-blocking。也就是说，Semantic Treehouse 部署证据很重要，但不能成为 `make validate` 的硬依赖。如果部署失败，项目要诚实记录失败原因，同时保持独立验证链路可运行。

## 2. 为什么要把 Treehouse 设为 evidence track

C 组任务名称是 Semantic Treehouse / Semantic Model Governance，因此必须研究和记录 Semantic Treehouse。可是本项目从 Phase 00 起就确立原则：

> 独立本地验证是核心路径，Semantic Treehouse 是支持性证据轨。

`tools/semantic-treehouse/README.md` 中写：

```text
The semantic model package does not depend on Semantic Treehouse being available.
Independent validation through `make validate` remains the authoritative path for RDF,
JSON-LD, SHACL, JSON Schema, OpenAPI, SPARQL, quality, and governance checks.
```

这个设计降低了展示和评分风险。即使 Treehouse UI 或 backend 因本地环境、Docker、端口等原因异常，C 组仍然可以通过模型文件和验证报告证明交付物完整。

## 3. 新增产物

根据 `C_Semantic_Treehouse/PHASE_6_SUMMARY.md`，本阶段创建或修改：

| 文件 | 作用 |
|---|---|
| `tools/semantic-treehouse/README.md` | 说明 Treehouse 本地 evidence track 的目标、依赖、端口和 fallback。 |
| `scripts/treehouse_clone_or_update.sh` | POSIX 环境下 clone/fetch upstream。 |
| `scripts/treehouse_up.sh` | POSIX 环境下尝试启动 Treehouse compose。 |
| `scripts/treehouse_down.sh` | POSIX 环境下停止 Treehouse compose project。 |
| `scripts/treehouse_status.sh` | POSIX 环境下捕获状态。 |
| `scripts/treehouse_clone_or_update.ps1` | Windows PowerShell clone/fetch。 |
| `scripts/treehouse_up.ps1` | Windows PowerShell 启动。 |
| `scripts/treehouse_down.ps1` | Windows PowerShell 停止。 |
| `scripts/treehouse_status.ps1` | Windows PowerShell 状态捕获。 |
| `evidence/semantic-treehouse-local-deployment.md` | 汇总部署环境、命令、结果、错误解释。 |
| `evidence/semantic-treehouse-upstream-version.txt` | 记录 upstream commit。 |
| `evidence/treehouse-compose-candidates.txt` | 记录候选 compose 文件。 |
| `evidence/treehouse-compose-file.txt` | 记录实际选用 compose 文件。 |
| `evidence/treehouse-docker-compose.log` | 记录 compose 日志。 |
| `evidence/treehouse-docker-ps.txt` | 记录容器状态。 |
| `evidence/treehouse-smoke-check.txt` | 记录 UI/API smoke check。 |

同时更新：

- `Makefile`
- `make.cmd`
- `.gitignore`

## 4. Treehouse 工具说明

`tools/semantic-treehouse/README.md` 说明本目录目标：

```text
This directory is a non-blocking evidence track for trying a local Semantic Treehouse deployment.
It supports the C Group task by documenting whether a local UI/API instance can be cloned,
started, inspected, and used as supporting evidence.
```

它列出依赖：

```text
- Git
- Docker
- Docker Compose v2
- A POSIX shell for `Makefile` targets on Unix-like systems
- PowerShell for the Windows `make.cmd` wrapper
```

这和本仓库 Windows/Unix 双入口设计一致。

## 5. Clone 与 upstream commit 证据

`make treehouse-clone` 的任务是 clone 或 fetch upstream：

```text
https://gitlab.com/semantic-treehouse/semantic-treehouse.git
```

Phase 06 summary 记录：

```text
cmd /c make treehouse-clone — passed; upstream commit captured as
33cf285c187f58c773f4e0d8c2826eeb2f6b3778.
```

该 commit 也写入 `evidence/semantic-treehouse-upstream-version.txt`。

这一步的意义是：Treehouse 证据不只说“我试着跑过”，还记录了具体 upstream 版本，便于复现和解释。

## 6. 启动脚本做了什么

`PHASE_6_SUMMARY.md` 记录 `make treehouse-up`：

```text
selected upstream root `docker-compose.yml`, used `--profile dev`,
created required volumes, copied `.env.example` to `.env` when needed,
ran `composer install`, and ran Doctrine migrations.
```

`evidence/semantic-treehouse-local-deployment.md` 中的 Commands Run 更细：

```text
- docker volume create sth-app-data
- docker volume create sth-db2-data
- copy .env.example to .env if .env is missing
- docker compose -p dssc_treehouse_evidence ... --profile dev up -d --build
- composer install --no-interaction
- php bin/console doctrine:migrations:migrate --no-interaction
```

这说明脚本不是简单调用 docker compose，而是根据 upstream 项目需要补上 post-start setup。

## 7. Docker 环境证据

`evidence/semantic-treehouse-local-deployment.md` 记录环境：

```text
Docker version 29.5.2, build 79eb04c
Docker Compose version v5.1.4
```

记录 upstream commit：

```text
33cf285c187f58c773f4e0d8c2826eeb2f6b3778
```

这些信息适合放入展示中的 “deployment evidence” 页。

## 8. Smoke check 结果

`evidence/treehouse-smoke-check.txt` 记录：

```text
Smoke check: http://localhost:4200/
curl exit code: 0
HTTP/1.1 200 OK
```

这说明 Semantic Treehouse development UI 在 `http://localhost:4200/` 有响应。

同一文件也记录了 backend/root 的 caveat：

```text
Smoke check: http://localhost:8014/
curl exit code: 28
curl: (28) Operation timed out after 5011 milliseconds with 0 bytes received
```

项目没有隐藏这个问题，而是在 `C_semantic_treehouse_usage.md` 中解释：

```text
The smoke check shows `http://localhost:4200/` returning `HTTP/1.1 200 OK`.
The backend/root port `http://localhost:8014/` is mapped by Compose,
but the root HEAD check timed out after 5 seconds.
This is recorded as a partial smoke caveat, not hidden.
```

这种写法体现了证据诚实原则。

## 9. Treehouse 使用报告如何定位

`C_semantic_treehouse_usage.md` 的开头写：

```text
Semantic Treehouse is treated as a semantic model governance and publication tool.
In this package it is an evidence track, not the only source of truth.
The authoritative validation path is the independent local harness under `scripts/` and `validation/`.
```

这段可以直接作为研讨展示的核心解释：我们既做了 Treehouse 本地部署证据，也没有让 Treehouse 成为项目唯一验证来源。

## 10. UI/API 仍需人工补充的证据

Phase 06 证据确认 UI 端口可访问，但并没有完成完整手动 UI 工作流截图。`C_semantic_treehouse_usage.md` 中列出建议人工确认：

```text
- the Semantic Treehouse home or login page
- specification or vocabulary listing
- message model or ontology workflow
- export controls if available
- validator or API routes if accessible in the local instance
```

这后来被 final checklist 标为 partial：

```text
Semantic Treehouse full manual UI workflow screenshots | partial
```

这同样说明项目没有虚构截图或声称完成未完成的 UI workflow。

## 11. 与独立验证路径的关系

Phase 06 最重要的验收条件之一是：

```text
make validate remains independent and still passes.
```

`PHASE_6_SUMMARY.md` 记录：

```text
cmd /c make validate — passed; independent validation remains separate from
the Semantic Treehouse deployment evidence track.
```

这证明 Treehouse 部署脚本不会污染核心 validation harness。Treehouse evidence 和 semantic artifact validation 是两条轨。

## 12. 本阶段遇到的问题和处理

`C_semantic_treehouse_usage.md` 中记录 issues：

```text
- Windows did not provide a working POSIX shell path, so PowerShell wrappers were added.
- The upstream repository contains a CI image compose file under `.gitlab`;
  the harness was adjusted to prefer the root `docker-compose.yml`.
- The upstream README requires `composer install` and Doctrine migrations after compose startup;
  these were added to the harness.
- The UI smoke check succeeds on port `4200`, while the backend/root HEAD check on `8014` times out.
```

这部分很适合在展示时说明“实际工程中遇到了什么”。它比只说“部署成功”更真实，也更能体现可复现研究的严谨性。

## 13. 本阶段验收情况

`PHASE_6_SUMMARY.md` 给出：

```text
treehouse-clone: pass.
treehouse-up: pass with partial smoke caveat on backend root path.
treehouse-status: pass.
validate: pass.
```

同时说明：

```text
Semantic Treehouse development UI smoke check: `http://localhost:4200/`
returned `HTTP/1.1 200 OK`.
```

## 14. 本阶段限制

Phase 06 的 remaining risks 是：

```text
The local Treehouse instance was verified through a smoke check,
not through a full UI workflow or screenshot capture.
```

以及：

```text
Backend root path behavior needs manual follow-up if the final report requires API-level Treehouse screenshots.
```

这些限制后来也写入 `FINAL_SUMMARY.md` 的 Known Limitations。

## 15. 对后续阶段的影响

Phase 06 直接支撑：

- `C_semantic_treehouse_usage.md` 中的 Docker evidence 和 issues。
- `docs/demo-script.md` 中 3:00 到 3:40 的 Treehouse evidence 展示段。
- `docs/final-checklist.md` 中 Semantic Treehouse usage record 的 done/partial 说明。
- `FINAL_SUMMARY.md` 中 Known Limitations。

## 16. 研讨展示建议

介绍 Phase 06 时，不建议只说“部署成功”。更好的讲法是：

> 我们把 Semantic Treehouse 当作支持性证据轨来跑。本地 UI smoke check 在 4200 端口返回 200 OK，但 backend/root HEAD check 在 8014 端口 timeout。这个 caveat 被保留在 evidence 中，同时核心语义验证仍然通过 `make validate` 独立完成。

建议现场打开：

- `tools/semantic-treehouse/README.md`
- `C_Semantic_Treehouse/evidence/semantic-treehouse-local-deployment.md`
- `C_Semantic_Treehouse/evidence/treehouse-smoke-check.txt`
- `C_Semantic_Treehouse/C_semantic_treehouse_usage.md`

可以引用：

```text
HTTP/1.1 200 OK
```

同时也引用：

```text
curl: (28) Operation timed out after 5011 milliseconds with 0 bytes received
```

这样可以展示项目既有成果，也诚实记录限制。

