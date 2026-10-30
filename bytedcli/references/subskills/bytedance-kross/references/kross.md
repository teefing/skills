# Kross 命令说明

Kross 用于创建多平台（Linux、macOS、Windows）容器环境（workload）。

## 命令面

当前 Kross CLI 暴露这几组能力：

- `kross workspace list`
- `kross workspace create`
- `kross workspace delete`
- `kross workspace var list`
- `kross template list`
- `kross vm template list`
- `kross vm create`
- `kross vm execute`
- `kross workload access start`
- `kross workload access url`
- `kross workload access credentials`
- `kross workload list`
- `kross workload follow`
- `kross workload create`
- `kross workload update`
- `kross workload delete`
- `kross workload exec`
- `kross workload upload`
- `kross workload download`

`workspace create` 和 `workspace delete` 会提交 Kross work order。命令返回成功表示工单已提交，work order 状态为 `COMPLETED` 才表示创建或删除完成。

## Workspace 创建

```bash
bytedcli kross workspace create \
  --name demo-workspace \
  --cluster default-multi-platform \
  --service-tree-node-id 939026 \
  --access-level public
```

- `--cluster` 必须使用精确的 active cluster 名称
- `--service-tree-node-id` 必须是当前用户有管理权限的服务树目录节点 ID
- `--access-level` 支持 `private` 和 `public`，默认 `private`；public workspace 允许合法用户无需成为 member 即可创建 workload
- 默认配额为 1 CPU、1024 MB 内存、10 GB 存储
- 使用 `--cpu-cores`、`--memory-mb`、`--storage-gb` 覆盖默认配额
- 返回 workspace 和 `CREATE_WORKSPACE` work order；继续操作前应确认 work order 状态为 `COMPLETED`

## Workspace 查询

```bash
bytedcli kross workspace list
```

结果合并当前用户所属的 workspace 和所有 public workspace；其他用户的 private workspace 不会进入结果。后续通过 `--workspace <name>` 定位时使用相同的可见性规则。

- 返回当前用户有权限访问的 workspace
- CLI 会自动翻完分页，不需要手动指定 page 参数

## Workspace 删除

```bash
bytedcli kross workspace delete --name demo-workspace
bytedcli --json kross workspace delete --workspace-id 42
```

- `--name` 和 `--workspace-id` 二选一
- workspace 内仍有 workload 时服务端会拒绝删除
- 返回 `DELETE_WORKSPACE` work order；确认 work order 状态为 `COMPLETED` 后，workspace 才算删除完成

## Workspace 变量查询

```bash
bytedcli kross workspace var list --workspace demo-workspace
bytedcli --json kross workspace var list --workspace demo-workspace --type SECRET
```

- 入参使用 workspace 名称，不需要手动传 workspace id
- 支持通过 `--type PLAIN` 或 `--type SECRET` 过滤变量类型
- 返回变量的 `InjectionMode`。普通变量看 `EnvName`，secret 变量看 `UnixPath` / `WindowsPath`
- secret 变量只返回脱敏后的 `MaskedValue` 和文件注入路径，不返回明文值

## 模板查询

```bash
bytedcli kross template list --workspace demo-workspace
```

- 入参使用 workspace 名称，不需要手动传 workspace id
- CLI 会先解析 workspace，再由 Kross 服务端根据 workspace 可见性和生效中的 cluster binding 返回可用模板

## 查询 workload

```bash
bytedcli kross workload list --workspace demo-workspace
```

- 返回目标 workspace 下的 workload
- CLI 会自动翻完分页，不需要手动指定 page 参数
- 支持通过 `--name`、`--type`、`--status-cached` 做过滤

## 观察 workload 状态

```bash
bytedcli kross workload follow --workspace demo-workspace --name demo-job
bytedcli --json kross workload follow --workspace demo-workspace --workload-id 72
```

- `--name` 和 `--workload-id` 二选一
- 依次输出 Kross 提供的 `SNAPSHOT`、`MODIFIED` 和 `DELETED` 事件
- `--json` 输出 JSONL，每行是一个事件，不附加最终 envelope
- 这是无界流，只能在直接 CLI 会话中运行，不支持 MCP 或 captured execution
- 服务端关闭 SSE 流后命令结束；客户端不会自动重连

## 虚拟机

查询当前 workspace 可用的 VM 镜像模板：

```bash
bytedcli kross vm template list --workspace demo-workspace
```

创建 VM workload：

```bash
bytedcli kross vm create \
  --workspace demo-workspace \
  --name demo-vm \
  --image-template-id ubuntu-2204 \
  --vcpu 2 \
  --memory-mb 4096 \
  --architecture x86_64 \
  --timeout-seconds 300
```

- `--architecture` 支持 `x86_64`、`arm64`
- `--firmware` 支持 `bios`、`uefi`、`uefi-secure-boot`；省略时使用镜像模板值
- `--cloud-init-user-data-secret-name` 引用 workspace namespace 中已有的 Secret
- `--cloud-init-network-data-file` 从本地文件读取 network-data
- `--retain-disk-on-delete` 请求在删除 workload 时保留平台管理的持久盘；默认不启用
- `--timeout-seconds` 设置 VM 的存活时间，必须为正整数且没有固定上限；超时后 Kross 自动回收 VM
- VM 不支持 `autoDeleteOnCompletion`，`vm create` 不会发送该字段

启动、停止或重启 VM：

```bash
bytedcli kross vm execute \
  --workspace demo-workspace \
  --name demo-vm \
  --action restart
```

通过本地端口访问 SSH 或 RDP：

```bash
bytedcli kross workload access start \
  --workspace demo-workspace \
  --name demo-vm \
  --protocol ssh

ssh -p 2222 user@127.0.0.1
```

- SSH 默认本地端口为 `2222`，RDP 默认本地端口为 `13389`
- `--address` 仅允许 `127.0.0.1` 或 `::1`，不会监听外部网卡
- 可用 `--local-port` 覆盖默认端口，用 `--ttl-seconds` 指定 1 到 900 秒的 access session 生命周期
- 每个本地 TCP 连接都会创建独立的 Kross access session

## 创建 job workload

### Quick create

```bash
bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --image demo/image:latest \
  --template-id linux-basic \
  --command 'sleep 300'
```

Quick create 默认行为：

- workload 类型固定为 `JOB`
- `container-name` 默认是 `main-container`
- CPU request/limit 默认 `1000m`
- memory request/limit 默认 `2048 MB`
- `timeoutSeconds` 默认 `300`
- `autoDeleteOnCompletion` 默认 `true`

常用覆盖参数：

```bash
bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --image demo/image:latest \
  --template-id linux-basic \
  --cpu-request-milli 2000 \
  --cpu-limit-milli 2000 \
  --memory-request-mb 4096 \
  --memory-limit-mb 4096 \
  --timeout-seconds 900 \
  --command 'sleep 300'
```

### Advanced create

如果需要完整控制 `CreateWorkload` 请求体，使用：

```bash
bytedcli kross workload create \
  --workspace demo-workspace \
  --body-file ./demo-kross-job.json
```

注意：

- `--body-file` 不能和 quick create 参数混用
- 请求体里仍然必须包含 `TemplateID`
- 如果模板提供默认镜像，quick create 可以省略 `--image`
- 如果模板锁定 `image` 字段，quick create 不接受 `--image`

## 更新 workload

```bash
# 调整副本数；0 表示缩容到零，具体类型限制由服务端校验
bytedcli kross workload update --workspace demo-workspace --name demo-workload --desired-replicas 2

# 更新容器、模板、ByteNAS 卷或 VM 配置
bytedcli --json kross workload update --workspace demo-workspace --workload-id 72 --body-file update.json
```

`--name` 和 `--workload-id` 二选一；`--desired-replicas` 和 `--body-file` 二选一。JSON 文件使用 `UpdateWorkload` 字段，不包含 `WorkspaceID`、`WorkloadID`、`Name`、`Type` 等定位或创建字段。

支持的请求字段：

- `DesiredReplicas`：非负整数。
- `Containers`：完整替换容器列表；每个容器需包含要保留的完整配置，镜像、资源、环境变量等不会按字段自动合并。
- `TemplateID`：模板 ID；空字符串表示移除 workload 模板。
- `ApplyMode`：模板应用模式，`1` 为 MERGE，`2` 为 STRICT。
- `ByteNASVolumes`：完整替换卷列表；空数组表示清空。
- `VirtualMachine`：完整 VM 配置，VM 更新时必填。

例如，`update.json` 同时修改副本数和完整容器列表：

```json
{
  "DesiredReplicas": 2,
  "Containers": [
    {
      "Name": "main-container",
      "Image": "example.registry/demo/app:v2",
      "Resources": {
        "CPURequestM": 1000,
        "CPULimitM": 2000,
        "MemRequestBytes": 1073741824,
        "MemLimitBytes": 2147483648
      }
    }
  ]
}
```

未提供的顶层字段保持不变。命令拒绝空对象、未知顶层字段及 `null` 更新值。Sandbox 不支持更新；VM 不能更新容器、模板或 ByteNAS 卷，副本数只能为 1，其他运行状态和配置限制由服务端校验。

命令成功表示更新请求已处理，不代表新实例已经就绪。使用 `bytedcli kross workload follow --workspace demo-workspace --workload-id 72` 观察运行状态。

## 删除 workload

```bash
bytedcli kross workload delete --workspace demo-workspace --name demo-job
bytedcli --json kross workload delete --workspace demo-workspace --workload-id 72
```

- `--name` 和 `--workload-id` 二选一
- 推荐脚本场景使用 `--json`

## 远程执行命令

```bash
bytedcli kross workload exec --workspace demo-workspace --name demo-workload --command 'pwd'
```

可选能力：

- `--container-name`：多容器 workload 时显式指定目标容器
- `--shell`：请求特定 shell
- `--pod-name`：指定 pod
- `--tty`：请求 TTY，会更接近交互终端语义
- `--output-file`：把命令输出落到本地文件

默认行为：

- 使用非 TTY webshell
- 自动剥离 ANSI 控制序列，得到更干净的 stdout
- 默认超时 `30000 ms`

## 上传/下载容器文件

```bash
bytedcli kross workload upload \
  --workspace demo-workspace \
  --name demo-workload \
  --container-name main-container \
  --local-path ./config.yaml \
  --remote-path /tmp/config.yaml

bytedcli kross workload download \
  --workspace demo-workspace \
  --workload-id 72 \
  --container-name main-container \
  --remote-path /tmp/config.yaml \
  --output ./config.yaml
```

- `upload` 和 `download` 都支持 `--name` 或 `--workload-id` 二选一
- `upload` 必须传 `--local-path` 和容器内目标 `--remote-path`
- `download` 必须传容器内来源 `--remote-path` 和本地 `--output`
- 如果 workload 有多个容器，显式传 `--container-name`
- 如需指定 pod，可传 `--pod-name`
- `upload` 会先向 Kross 申请临时 capability URL，再通过 webshell 把文件拉到目标 workload
- `download` 会让 workload 先把远端文件推送到临时 capability URL，再由 CLI 下载到本地
- 这条临时文件链路同时适用于 Linux、macOS、Windows workload；Linux/macOS 目标容器需要提供 `curl`，Windows 目标容器需要提供 `curl.exe`

## 推荐闭环

```bash
# 1. 创建 workspace，并等待返回的 work order 完成
bytedcli kross workspace create \
  --name demo-workspace \
  --cluster default-multi-platform

# 2. 查 workspace、变量和模板
bytedcli kross workspace list
bytedcli kross workspace var list --workspace demo-workspace
bytedcli kross template list --workspace demo-workspace

# 3. 创建 workload
bytedcli kross workload create \
  --workspace demo-workspace \
  --name demo-job \
  --image demo/image:latest \
  --template-id linux-basic \
  --command 'sleep 300'

# 4. 远程执行命令
bytedcli kross workload exec \
  --workspace demo-workspace \
  --name demo-job \
  --command 'hostname; pwd'

# 5. 上传或下载容器文件
bytedcli kross workload upload \
  --workspace demo-workspace \
  --name demo-job \
  --container-name main-container \
  --local-path ./config.yaml \
  --remote-path /tmp/config.yaml

bytedcli kross workload download \
  --workspace demo-workspace \
  --name demo-job \
  --container-name main-container \
  --remote-path /tmp/config.yaml \
  --output ./config.yaml

# 6. 删除 workload
bytedcli kross workload delete --workspace demo-workspace --name demo-job

# 7. workspace 内没有 workload 后提交删除，并等待返回的 work order 完成
bytedcli kross workspace delete --name demo-workspace
```

## 本地端口转发 SSH/RDP/VNC

SSH、RDP、VNC 均使用 `kross workload access start`。旧入口 `kross vm access start` 继续兼容相同参数，但不再显示在 VM 命令列表中。

SSH 默认监听 `127.0.0.1:2222`，RDP 默认监听 `127.0.0.1:13389`，VNC 默认监听 `127.0.0.1:15900`。使用 `--local-port 0` 自动分配空闲端口，或 `--address ::1` 监听 IPv6 回环地址。每个本地 TCP 连接独立申请短期 Kross access session。命令保持前台运行，Ctrl-C 关闭监听和全部连接。

服务端返回实例 ID 时，同一转发命令的连接固定到首次选中的实例；实例替换或 Sandbox 暂停、恢复后，需重新运行 `access start`。非 VM SSH 要求服务端支持实例绑定；VM SSH/RDP 和 VNC 兼容不返回实例 ID 的旧服务端，此时不提供实例固定保证。

### SSH 与 IDE

SSH 支持运行中的 VM、Deployment、Job 和 Linux Sandbox（Kross 管理的 Linux 沙箱 workload）。服务端负责定位并校验运行实例，客户端无需指定 Pod。非 VM SSH 仅允许恰好一个符合条件的运行中副本，不支持使用 hostNetwork 的 Pod；零个或多个运行中副本均拒绝连接。

目标环境须启动监听 TCP 22 的 SSH 服务并配置账号与密钥等登录凭据。Kross 只转发 SSH 数据，不安装服务或管理 SSH 密码。

```bash
bytedcli kross workload access start --workspace demo-workspace --name demo-linux --protocol ssh --local-port 2222
ssh -p 2222 demo-user@127.0.0.1
```

IDE 需与 bytedcli 在同一台机器运行，SSH 目标填写本次 `access start` 输出的监听地址和端口，并使用目标环境的账号与密钥。镜像需满足 IDE 后端的系统依赖，SSH 服务需允许 IDE 所需的端口转发；使用 SFTP 的 IDE 还需启用 SFTP。

### RDP

RDP 仅支持 VM，目标系统需要运行 TCP 3389 上的 RDP 服务：

```bash
bytedcli kross workload access start --workspace demo-workspace --name demo-windows-vm --protocol rdp
```

### VNC 与托管密码

```bash
bytedcli kross workload access start --workspace demo-workspace --name demo-desktop --protocol vnc
bytedcli kross workload access start --workspace demo-workspace --name demo-windows-vm --protocol vnc
bytedcli --json kross workload access start --workspace demo-workspace --name demo-mac --protocol vnc --local-port 0
```

VNC 转发到目标 TCP 5900。目标可以是镜像内已启动 VNC Server 的 VM，或启用了 VNC 的 Linux/macOS Deployment/Job；后者在恰好一个实例运行时允许连接，零个或多个时拒绝连接。Windows Pod 不在支持范围。

Windows VM VNC 连接 guest 内的 TCP 5900，不使用 KubeVirt/QEMU console。Kross Windows VNC 镜像不要求额外的 VNC 密码，身份校验由短期 Kross access session 完成；`workload access credentials` 只适用于托管 Linux/macOS workload。

托管 Linux/macOS workload 的密码由实例管理通道单独获取。连接命令不读取或修改密码。Ctrl-C 清理连接；JSON 输出中的 `listening` 表示本地端口就绪，`connected` 表示远端转发建立，`connection_error` 表示本次连接失败。

托管 Linux/macOS VNC 模板通过 `kross.byted.org/vnc-enabled: "true"` 和 `kubernetes.io/os: linux` 或 `darwin` 启用密码下发。Kross 创建每个 workload 独立的 Secret，并将密码只读挂载到 `/opt/kross/vnc/password`；配套镜像内置的启动脚本读取密码，启动桌面和 TCP 5900 上的 VNC 服务。Linux 未设置 fsGroup 时默认使用 1000，该设置也影响 Pod 内其他支持 fsGroup 的卷。镜像必须支持这一启动约定，连接命令不安装或配置服务。

使用 `bytedcli kross workload access credentials --workspace demo-workspace --name demo-desktop --password-file ./demo-desktop.vnc-password` 将托管密码写入新的 `0600` 文件；不会覆盖已有文件或符号链接，输出中不包含密码。需要明文时显式传入 `--show-password`，两种输出方式不能同时使用。读取需要 workspace 操作权限；workspace token 还需 `workload:credentials:read` scope，单独的 `workload_exec` 不足以取密。

凭据读取直接访问 Secret，不需要运行中的 Pod、Exec 或节点登录。同一 workload 的副本共用密码，实例重建不改变密码；删除 workload 时清理 Secret。使用后应删除本地密码文件。自备镜像的密码由镜像约定，未启用托管 Secret 时不能使用此取密命令。

## 浏览器远程桌面

`kross workload access url` 返回浏览器桌面链接，`--protocol` 默认 `vnc`，目前仅支持 `vnc`。默认 `--auth login` 需要浏览器 Kross 登录态；`--auth ticket` 通过 CLI 当前身份签发一次性短期链接，可在无登录态浏览器中使用。链接当前仅支持 CN。

```bash
bytedcli kross workload access url --workspace demo-workspace --name demo-mac
bytedcli --json kross workload access url --workspace demo-workspace --workload-id 72 --protocol vnc --auth ticket --ttl-seconds 300
```

`--ttl-seconds` 只控制票据兑换期限（1–900 秒，默认 300 秒），不改变浏览器会话时长。票据仅可兑换一次，页面初始化时清除 fragment；刷新需重新获取链接。票据链接是访问凭据，不应写入日志或文档。`--open` 仅用于 login 模式，禁止与 ticket 模式组合，避免票据进入进程参数及系统审计日志。

Linux/macOS Deployment/Job 需要单个运行中的 VNC 实例及托管 VNC Secret；KubeVirt VM 需要运行中且无需额外密码的 guest VNC 服务。workspace token 需同时具备 `workload_exec` 和 `workload:credentials:read`。浏览器授权最多持续 15 分钟，且不超过原授权有效期，只能访问目标实例。JSON 始终返回 `workspace_id`、`workload_id`、`protocol`、`auth`、`url`、`expires_at` 和 `opened`；login 模式的 `expires_at` 为 `null`，未指定 `--open` 时的 `opened` 为 `null`，否则表示浏览器启动进程是否成功创建，不代表页面加载或桌面连接成功。

## Computer-use：截图、键鼠和文本剪贴板

`bytedcli kross computer-use` 通过 Kross 的 HTTP + WebSocket API 操作远端桌面，无需安装 VNC/RDP 客户端。创建会话复用 Kross 的站点认证和 API 代理，WebSocket 连接服务端返回的会话地址。macOS/Linux 使用 `--protocol vnc`（默认），Windows 使用 `--protocol rdp`。

```bash
# 截图；坐标按截图原始像素计算
bytedcli kross computer-use screenshot get --workspace demo-workspace --name demo-desktop --output screen.png

# 把 UTF-8 文件写入远端剪贴板，并粘贴到当前焦点（Mac）
bytedcli kross computer-use clipboard update --workspace demo-workspace --name demo-mac --text-file prompt.txt --paste-keys meta,v

# Linux/Windows 的粘贴通常使用 ctrl,v；Windows 选择 RDP
bytedcli kross computer-use clipboard update --workspace demo-workspace --name demo-windows --protocol rdp --text '你好 😀' --paste-keys ctrl,v

# 复制当前选区，然后读取远端剪贴板（Linux）
bytedcli --json kross computer-use clipboard get --workspace demo-workspace --name demo-linux --copy-keys ctrl,c

# 同一会话内执行多步操作
bytedcli --json kross computer-use execute --workspace demo-workspace --name demo-desktop --data @operations.json --output after.png
```

所有命令使用 `--workspace`，并且在 `--name` 与 `--workload-id` 中二选一。会话默认 300 秒；`--ttl-seconds` 的 VNC 范围为 30–900、RDP 为 60–900。`--timeout-ms` 默认为 100000，约束 HTTP 创建与每次 WebSocket 响应等待。RDP 分辨率可用 `--width`（320–4096）、`--height`（200–4096）设置，默认 1280 × 720；VNC 使用远端分辨率。

`operations.json` 是按顺序执行的操作数组（最多 256 项），例如：

```json
[
  {"operation":"actions","actions":[{"type":"click","x":300,"y":200}]},
  {"operation":"clipboard_write","text":"你好，世界 😀\n/tmp/中文 目录/demo.txt"},
  {"operation":"actions","actions":[{"type":"key","keys":["ctrl","v"]}]},
  {"operation":"screenshot"}
]
```

支持 `screenshot`、`clipboard_read`、`clipboard_write` 和 `actions`。`actions` 每批 1–32 项，可选 `capture_after: true` 获取执行后的截图、`frame_id` 防止使用过期截图操作。鼠标动作包括 `click`/`move`（`x`,`y`）、`scroll`（加 `delta_x`,`delta_y`，每轴 -100..100）、`drag`（`start_x`,`start_y`,`end_x`,`end_y`,`duration_ms`，最长 2000 毫秒）。`click` 可传 `button: left|middle|right`、`click_count`。键盘动作为 `key`（`keys` 数组）和 `type_text`（`text`，每批总计最多 512 个字符）。Mac 的 Command 对应 `meta`，普通应用粘贴为 `meta,v`；终端等应用可能使用不同快捷键。

`--data` 接受 JSON 字符串或 `@文件路径`。`clipboard update` 的 `--text` 为原样文本（`@` 不作为文件引用），与 `--text-file` 二选一；`--text ''` 清空文本。文本必须为合法 Unicode、不含 NUL、UTF-8 不超过 16 KiB，不会静默截断。换行读取时规范化为 LF。

每条命令打开一个会话，按顺序执行后关闭。写剪贴板不会自动粘贴；Linux/Windows 在断开后可能失去剪贴板所有权，使用 `--paste-keys` 或同一个 `execute` 计划完成写入和粘贴。新连接可能读不到先前内容；先在目标应用选中文本，再通过 `--copy-keys` 在当前会话复制。此 API 不操作调用方的本地剪贴板。

结果包含 `results` 数组，读取文本在对应结果的 `text` 字段。截图包含尺寸、`frame_id`、`mime_type` 和 Base64 `data`。`--output` 将最后一个返回的截图保存为图片，并从输出中省略全部截图 Base64；`execute --output` 的计划必须包含截图或 `capture_after: true`。图片格式以 `mime_type` 为准（PNG/JPEG）。会话地址和凭据不会出现在命令结果中。

失败会停止计划，已执行动作不会回滚。`CLIPBOARD_UNSUPPORTED` 表示远端不支持剪贴板通道，`CLIPBOARD_UNAVAILABLE` 表示当前没有可读文本。`CLIPBOARD_OUTCOME_UNKNOWN` 或连接超时/中断表示输入可能已生效；先观察桌面状态，再决定后续操作，不能直接重试整个计划。

会话地址必须使用 `wss://`，明文 `ws://` 会在连接前拒绝。文本模式显示会话、操作数、剪贴板文本和截图元信息，不打印图片 Base64；Base64 只在 `--json` 模式返回，或通过 `--output` 保存图片。
