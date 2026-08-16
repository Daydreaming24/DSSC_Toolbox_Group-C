# Semantic Treehouse 用户指南

本文说明本仓库 Semantic Treehouse 本地实例的日常使用、SHACL 验证、安全暂停与恢复、完整收尾和故障检查。命令应从仓库根目录执行。当前实例已经部署可选 SHACL validator，完成 canonical v0.4 正控与负控验证后处于 `PAUSED` 状态。

当前运行合同由 tracked 权威锁 `tools/semantic-treehouse/upstream.lock.json`、仓库提供的跨平台 wrappers，以及本次受控部署生成的本地 runtime overlays 共同约束。upstream 检出目录 `tools/semantic-treehouse/upstream/` 本身是可选外部材料且默认不进入 clean-room 镜像；runtime overlays 和 synthetic environment 位于 Git 忽略目录，其中可能含本地敏感配置，不要提交、复制、截图或发布其内容。

## 1. 当前实例边界

| 项目 | 当前值 |
|---|---|
| 当前服务状态 | `PAUSED`；三个容器均保留且已正常停止 |
| Web 入口 | 恢复后使用 `http://127.0.0.1:18014/` |
| 登录入口 | 恢复后使用 `http://127.0.0.1:18014/login` |
| Compose project | `dssc-semantic-treehouse-v04` |
| 应用容器 | `dssc-semantic-treehouse-v04-sth` |
| SHACL validator 容器 | `dssc-semantic-treehouse-v04-shacl-validator` |
| 数据库容器 | `dssc-semantic-treehouse-v04-sth-db2` |
| 应用数据卷 | `dssc-semantic-treehouse-v04-sth-app-data` |
| 数据库卷 | `dssc-semantic-treehouse-v04-sth-db2-data` |
| validator 内部网络 | `dssc-semantic-treehouse-v04-validator-internal` |
| validator 宿主端口 | 无；应用通过内部网络访问 validator |
| 数据库宿主端口 | 无 |
| 容器自动重启 | 关闭；Docker daemon 重启后按本文流程手动恢复 |

恢复运行后，应用只监听本机 loopback 的 18014 端口。validator 只连接独立 internal 网络并在容器内提供服务，宿主机和局域网均没有 validator 端口入口。数据库也没有宿主端口。应用同时连接 ingress、数据库 internal 网络和 validator internal 网络。

当前 local-review 登录门只允许固定 `admin` 账户，运行模式保持 `APP_ENV=prod` 和 `APP_DEBUG=0`。保持 18014 的 loopback 绑定，并保持 validator 与数据库零宿主端口。

## 2. 开始使用

当前服务已暂停。先按第 6 节恢复三个容器，再执行本节操作。

### 2.1 登录

1. 打开 `http://127.0.0.1:18014/login`。
2. 点击 `Admin`。
3. 登录成功后进入 `Specifications`。
4. 打开项目 `DSSC C Semantic Governance v0.4`。

浏览器会话失效时，重新进入登录页并点击 `Admin`。浏览器 cookie、session ID 和 synthetic environment 内容都应留在本机内存或受保护的本地运行目录中。

### 2.2 查看已经导入的 v0.4 内容

项目中包含以下主要对象：

- `DSSC C Building Energy Ontology`：选择 `0.4` 版本，可使用 `Graph`、`Tree` 和 `Export` 查看或导出 ontology。
- `DSSC C Data Product Metadata`：选择 `0.4` 版本，可查看根元素、ontology 关联以及 RDF/JSON-LD syntax binding。
- `DSSC C v0.4 RDF / JSON-LD + SHACL`：已经启用 validator 与 schema validation，并关联 canonical SHACL 文件和 JSON-LD example。
- Documentation attachments：包含 JSON-LD context、release README 和 checksum 清单。

当前导入对象是 v0.4 审阅基线。实验性编辑宜放入新项目或新版本，以便保留 canonical import、验证结果与已有证据之间的对应关系。当前流程没有执行 publication。

## 3. 使用 SHACL Validator

### 3.1 在 UI 中执行验证

1. 按第 6 节恢复全部服务并登录。
2. 打开 UI 的 `Validator` 页面。
3. 选择 binding `DSSC C v0.4 RDF / JSON-LD + SHACL`。
4. 在输入区粘贴待验证的 JSON-LD 临时副本并执行验证。
5. 查看 syntax 与 schema 两组结果；当前 binding 没有启用 business-rules validation，因此该项可以显示为空或不适用。

validator 没有宿主端口。浏览器请求先到 loopback-only Treehouse 应用，再由应用通过 `dssc-semantic-treehouse-v04-validator-internal` 调用 validator。

### 3.2 canonical example 的相对 context

[`data-product-valid.jsonld`](model/v0.4/data-product-valid.jsonld) 的顶层 `@context` 使用相对引用 `data-product-context.jsonld`。文件系统验证可以从同目录解析该引用；UI 或 API 的单条消息请求没有同目录文件解析上下文。

在 Validator 中验证 canonical example 时，使用 validation-only 临时副本：

1. 读取 [`data-product-context.jsonld`](model/v0.4/data-product-context.jsonld) 中 `@context` 的对象值。
2. 在内存或粘贴区临时把 example 的 `"@context": "data-product-context.jsonld"` 替换为该对象值。
3. 验证结束后丢弃临时副本。

该操作只解决请求边界中的 context 定位。canonical example 与 context 文件应保持原样，临时内联后的 RDF 图应与从同目录解析 canonical 文件得到的 RDF 图等价。

### 3.3 正控与负控

建议每次 validator 配置发生变化后运行一对诊断：

- 正控：使用完成 context 内联的 canonical valid example。预期 `syntax_valid=true`、`schema_valid=true`，且没有 schema violation。
- 负控：从同一个临时 payload 中仅删除 `datasetId` 后再次验证。预期语法仍然有效，schema validation 失败并返回相应 violation。

正控证明合法 canonical 数据可以通过；负控证明 validator 和当前 SHACL 约束确实参与了判定。负控只在内存或粘贴区构造，不要回写 canonical 文件，也不要保存到 Treehouse 的 canonical binding。验证证据应只记录状态、计数和脱敏摘要，避免记录请求正文、cookie 或 session。

## 4. 只读查看运行状态

以下命令只读取三个容器、三个网络和两个数据卷的状态，不读取容器环境变量。

### 4.1 Windows PowerShell

```powershell
$treehouseContainers = @(
    "dssc-semantic-treehouse-v04-sth",
    "dssc-semantic-treehouse-v04-shacl-validator",
    "dssc-semantic-treehouse-v04-sth-db2"
)

docker inspect `
  --format '{{.Name}} state={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}} restart={{.HostConfig.RestartPolicy.Name}}' `
  $treehouseContainers

docker inspect `
  --format '{{.Name}} port-bindings={{json .HostConfig.PortBindings}} networks={{json .NetworkSettings.Networks}}' `
  $treehouseContainers

docker network inspect `
  --format '{{.Name}} internal={{.Internal}}' `
  dssc-semantic-treehouse-v04-internal `
  dssc-semantic-treehouse-v04-ingress `
  dssc-semantic-treehouse-v04-validator-internal

docker volume inspect `
  --format '{{.Name}} driver={{.Driver}}' `
  dssc-semantic-treehouse-v04-sth-app-data `
  dssc-semantic-treehouse-v04-sth-db2-data
```

### 4.2 POSIX shell

```bash
treehouse_app_container='dssc-semantic-treehouse-v04-sth'
treehouse_validator_container='dssc-semantic-treehouse-v04-shacl-validator'
treehouse_db_container='dssc-semantic-treehouse-v04-sth-db2'

docker inspect \
  --format '{{.Name}} state={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}} restart={{.HostConfig.RestartPolicy.Name}}' \
  "$treehouse_app_container" \
  "$treehouse_validator_container" \
  "$treehouse_db_container"

docker inspect \
  --format '{{.Name}} port-bindings={{json .HostConfig.PortBindings}} networks={{json .NetworkSettings.Networks}}' \
  "$treehouse_app_container" \
  "$treehouse_validator_container" \
  "$treehouse_db_container"

docker network inspect \
  --format '{{.Name}} internal={{.Internal}}' \
  dssc-semantic-treehouse-v04-internal \
  dssc-semantic-treehouse-v04-ingress \
  dssc-semantic-treehouse-v04-validator-internal

docker volume inspect \
  --format '{{.Name}} driver={{.Driver}}' \
  dssc-semantic-treehouse-v04-sth-app-data \
  dssc-semantic-treehouse-v04-sth-db2-data
```

当前 `PAUSED` 状态的预期结果为：三个容器均为 `exited`，三个网络和两个数据卷仍然存在，18014 无法连接。恢复后，三个容器都应为 `running` 且 `healthy`；应用端口绑定为 `127.0.0.1:18014`，validator 和数据库的 `port-bindings` 为空。

仓库现有 `treehouse_status.ps1` / `treehouse_status.sh` 仍采用 core 两服务与原始网络的精确投影。可选 validator 增加了第三个容器和 `validator-internal` 网络，因此三服务正常运行时该 wrapper 也会报告 `REVIEW_REQUIRED`；日常暂停保留容器和网络，同样会报告 `REVIEW_REQUIRED`。使用上面的三容器只读检查判断当前实例，保留 wrapper 输出供维护者审阅。

## 5. 日常安全暂停

日常暂停保留三个容器、三个网络、两个数据卷和运行配置。顺序固定为：应用 → SHACL validator → 数据库。先停止应用可以结束新请求，再停止无状态 validator，最后给数据库正常结束和刷写数据的时间。

当前实例已经处于本节描述的 `PAUSED` 状态。以后从运行状态暂停时使用以下命令。执行前先保存 UI 中正在编辑的内容并结束当前验证。

### 5.1 Windows PowerShell

```powershell
$treehouseAppContainer = "dssc-semantic-treehouse-v04-sth"
$treehouseValidatorContainer = "dssc-semantic-treehouse-v04-shacl-validator"
$treehouseDbContainer = "dssc-semantic-treehouse-v04-sth-db2"

docker stop --time 30 $treehouseAppContainer
if ($LASTEXITCODE -ne 0) { throw "Failed to stop the Treehouse application container." }

docker stop --time 30 $treehouseValidatorContainer
if ($LASTEXITCODE -ne 0) { throw "Failed to stop the SHACL validator container." }

docker stop --time 60 $treehouseDbContainer
if ($LASTEXITCODE -ne 0) { throw "Failed to stop the Treehouse database container." }

docker inspect `
  --format '{{.Name}} {{.State.Status}}' `
  $treehouseAppContainer `
  $treehouseValidatorContainer `
  $treehouseDbContainer
```

最后三行期望均为 `exited`。

### 5.2 POSIX shell

```bash
treehouse_app_container='dssc-semantic-treehouse-v04-sth'
treehouse_validator_container='dssc-semantic-treehouse-v04-shacl-validator'
treehouse_db_container='dssc-semantic-treehouse-v04-sth-db2'

docker stop --time 30 "$treehouse_app_container"
docker stop --time 30 "$treehouse_validator_container"
docker stop --time 60 "$treehouse_db_container"

docker inspect \
  --format '{{.Name}} {{.State.Status}}' \
  "$treehouse_app_container" \
  "$treehouse_validator_container" \
  "$treehouse_db_container"
```

暂停后的正常现象包括：Web 页面不可访问，三个容器保留且为 `exited`，三个网络和两个数据卷继续存在。健康检查在容器退出后可能显示 `unhealthy`；暂停状态以 `.State.Status=exited` 为准。

使用 `docker stop` 完成日常暂停。`docker pause` 会冻结进程，不适合作为数据库和当前三服务闭包的日常停机方式。

## 6. 重新启用

恢复顺序固定为：数据库 → 等待数据库 healthy → SHACL validator → 等待 validator healthy → 应用 → 等待应用 healthy → 检查 loopback HTTP。应用依赖数据库和 validator，这个顺序可使依赖项先完成就绪。

### 6.1 Windows PowerShell

```powershell
$treehouseAppContainer = "dssc-semantic-treehouse-v04-sth"
$treehouseValidatorContainer = "dssc-semantic-treehouse-v04-shacl-validator"
$treehouseDbContainer = "dssc-semantic-treehouse-v04-sth-db2"

function Wait-TreehouseHealthy {
    param(
        [string]$Name,
        [int]$TimeoutSeconds = 180
    )

    $treehouseDeadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $treehouseDeadline) {
        $treehouseHealth = docker inspect `
          --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' `
          $Name 2>$null

        if (($LASTEXITCODE -eq 0) -and ($treehouseHealth.Trim() -eq "healthy")) {
            Write-Host "$Name is healthy"
            return
        }

        Start-Sleep -Seconds 2
    }

    throw "Container did not become healthy: $Name"
}

docker start $treehouseDbContainer
if ($LASTEXITCODE -ne 0) { throw "Failed to start the Treehouse database container." }
Wait-TreehouseHealthy $treehouseDbContainer

docker start $treehouseValidatorContainer
if ($LASTEXITCODE -ne 0) { throw "Failed to start the SHACL validator container." }
Wait-TreehouseHealthy $treehouseValidatorContainer

docker start $treehouseAppContainer
if ($LASTEXITCODE -ne 0) { throw "Failed to start the Treehouse application container." }
Wait-TreehouseHealthy $treehouseAppContainer

$treehouseResponse = Invoke-WebRequest `
  -UseBasicParsing `
  -TimeoutSec 15 `
  http://127.0.0.1:18014/api/environment/info

if ($treehouseResponse.StatusCode -ne 200) {
    throw "Treehouse loopback API did not return HTTP 200."
}
```

### 6.2 POSIX shell

```bash
treehouse_app_container='dssc-semantic-treehouse-v04-sth'
treehouse_validator_container='dssc-semantic-treehouse-v04-shacl-validator'
treehouse_db_container='dssc-semantic-treehouse-v04-sth-db2'

wait_treehouse_healthy() {
  treehouse_container_name=$1
  treehouse_attempt=0

  while [ "$treehouse_attempt" -lt 90 ]; do
    treehouse_health=$(docker inspect \
      --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
      "$treehouse_container_name" 2>/dev/null || true)

    if [ "$treehouse_health" = healthy ]; then
      printf '%s\n' "$treehouse_container_name is healthy"
      return 0
    fi

    treehouse_attempt=$((treehouse_attempt + 1))
    sleep 2
  done

  printf '%s\n' "Container did not become healthy: $treehouse_container_name" >&2
  return 1
}

docker start "$treehouse_db_container"
wait_treehouse_healthy "$treehouse_db_container"

docker start "$treehouse_validator_container"
wait_treehouse_healthy "$treehouse_validator_container"

docker start "$treehouse_app_container"
wait_treehouse_healthy "$treehouse_app_container"

curl --fail --silent --show-error \
  --max-time 15 \
  http://127.0.0.1:18014/api/environment/info \
  >/dev/null
```

恢复后使用第 4 节的只读检查确认三容器健康、validator 和数据库零宿主端口、应用仍为 loopback-only。浏览器旧会话可能继续有效，也可能要求重新登录。core `treehouse_status` 在当前可选 validator 投影下预期报告 `REVIEW_REQUIRED`。

## 7. 完整收尾与全新部署

日常使用优先采用第 5、6 节的 `docker stop/start`，这条路径保留当前导入数据和三服务配置。

仓库公开的 `treehouse_down.ps1` / `treehouse_down.sh` 目前验证 core 两服务精确闭包。当前可选 validator 容器和网络会触发 `REVIEW_REQUIRED`，因此不要绕过其保护检查，也不要把 core wrapper 单独当作三服务完整收尾命令。

需要完整移除三个容器和三个网络时，应使用本次受控部署对应的完整 runtime overlay 集合执行经过审阅的三服务 teardown，并在操作前后执行第 4 节的只读检查。完整收尾必须保留以下两个数据卷：

```text
dssc-semantic-treehouse-v04-sth-app-data
dssc-semantic-treehouse-v04-sth-db2-data
```

validator 是无状态服务，没有项目数据卷。完整 teardown 的 Compose 命令只能使用普通 `down`，禁止附加 `-v` 或 `--volumes`。当前本地 runtime overlay 与 synthetic environment 属于部署恢复材料；确认后续恢复方案前应继续保留。

公开 `treehouse_up` 使用 fresh-only 合同，仅负责 core Treehouse 新部署，并会拒绝复用已有项目卷。它不会独立恢复当前 retained-volume 三服务实例，也不会自动重建可选 validator。需要全新部署或完整 down 后恢复时，应重新走批准后的 Phase 08 预检、固定镜像、core 部署、validator add-on 和验证流程。

## 8. 数据保护和禁止操作

两个受管卷共同保存当前 Treehouse 状态。应用卷保存上传的 SHACL 和文档附件；数据库卷保存项目、specification、版本、binding、example、账户及关系数据。完整恢复需要两个卷同时存在。

禁止对当前项目执行以下操作：

```text
docker compose down -v
docker compose down --volumes
docker volume rm dssc-semantic-treehouse-v04-sth-app-data
docker volume rm dssc-semantic-treehouse-v04-sth-db2-data
docker system prune --volumes
```

也不要直接运行上游原始 Compose 文件。当前受控 runtime 才包含 loopback-only 应用端口、validator 与数据库零宿主端口、admin-only local-review 登录、持久化目标和三网络边界。

不要把完整 `docker inspect`、容器环境、synthetic environment、cookie、session 或未经脱敏的日志写入证据。第 4 节给出的格式化只读命令避开了环境值。

## 9. 故障检查

### 9.1 容器未变为 healthy

先确认依赖启动顺序，再查看有限日志：

```powershell
docker logs --tail 100 dssc-semantic-treehouse-v04-sth-db2
docker logs --tail 100 dssc-semantic-treehouse-v04-shacl-validator
docker logs --tail 100 dssc-semantic-treehouse-v04-sth
```

日志可能含运行细节，仅在本机查看；共享前先脱敏。数据库 healthy 后再启动 validator，validator healthy 后再启动应用。

### 9.2 Validator 报 context 解析错误

确认输入是否仍保留相对 `@context`。对 canonical example 使用第 3.2 节的 validation-only 内存内联方式，再运行正控与负控。保持 canonical 文件不变。

### 9.3 端口 18014 被占用

Windows：

```powershell
Get-NetTCPConnection -LocalPort 18014 -ErrorAction SilentlyContinue
```

POSIX：

```bash
ss -ltn 'sport = :18014'
```

确认占用者后再恢复应用。保持服务只发布到 loopback 地址。validator 和数据库不需要宿主端口。

### 9.4 状态为 REVIEW_REQUIRED

当前三服务运行态和日常暂停态都会超出 core `treehouse_status` 的两服务投影。使用第 4 节检查：

- 三个固定容器是否都存在，状态是否与期望的 `PAUSED` 或运行态一致；
- 运行时数据库、validator、应用是否都为 healthy；
- 应用是否仍只绑定 `127.0.0.1:18014`；
- validator 和数据库是否保持零宿主端口；
- 三个固定网络和两个固定数据卷是否存在；
- validator 网络是否保持 `internal=true`。

发现容器、网络、label 或卷缺失时，停止进一步写操作，保留现场并查阅脱敏证据。

## 10. 相关文档

- [`C_semantic_treehouse_usage.md`](C_semantic_treehouse_usage.md)：证据门槛、历史执行状态和 import/export 证明边界。
- [`tools/semantic-treehouse/README.md`](../tools/semantic-treehouse/README.md)：固定 upstream、runtime overlay 和 evidence track。
- [`scripts/README.md`](scripts/README.md)：跨平台 Treehouse wrappers 的来源与状态。
- [`docs/v0.4/STATUS.md`](../docs/v0.4/STATUS.md)：Phase 08 恢复、登录、导入、SHACL validator 与安全暂停记录。
