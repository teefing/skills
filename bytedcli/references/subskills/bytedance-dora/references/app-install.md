# Dora 应用安装

## Edge 任务与恢复

- `--transport edge --url-file <path-or-dash>` 使用 Dora REST 鉴权，支持 ByteCloud JWT 和 Dora AK/SK；不依赖 native WebSocket、ADB/BDC 连接或设备 shell 下载工具。设备与包格式支持由边缘服务决定，本文档不承诺所有设备系统均可安装。
- URL 仅从 owner-only 文件或非 TTY stdin 读取，必须为无 userinfo 的 HTTPS URL，最多 2048 字符；需能从边缘节点访问。请求/响应正文受敏感保护，输出移除 `package_url`，失败信息中的 URL 脱敏。
- 中心服务依据当前占用推导 `session_id`；创建和列表要求当前占用者，CLI 不自动占机或续租。
- 默认等待 `succeeded` 才返回 `delivery_status: confirmed`；`accepted/download/push/install` 是处理中，`failed/timeout/canceled` 使 deploy 失败并携带任务 ID、失败码和阶段。
- `--no-wait` 不轮询；进行中任务返回 `delivery_status: submitted`，复用已 `succeeded` 的任务返回 `confirmed`。两者都返回 `task_id` 和当前 `task.status`；用 `device app task get --id <task-id>` 跟踪。JSON 只输出一次结果，文本进度写入 stderr。
- `--timeout-ms` 是本地等待预算，默认 1800000，范围 1..14400000；`--timeout-seconds` 独立控制服务端任务超时，正 int32，未传使用服务端默认/上限。二者不能混用单位。本地等待超时或中断不自动取消远端任务；若创建响应未到，可用 `task list --serial` 找回任务。
- `--resign true|false` 显式控制重签名请求；edge 默认 false，native 默认 true。`--timeout-seconds`、`--no-wait` 仅 edge 可用。
- 同一 `serial + session_id + URL hash` 幂等，结果保留 `idempotent`；相同 URL 可能复用已完成或已失败任务，仅改 `resign` 或超时不保证重新安装。不要通过切换 transport 自动重试；先查任务并确认制品版本/URL。
- `device app task list --serial <serial> [--page 1 --page-size 20]` 查询当前会话；`task get --id` 仅要求任务 requester，可查历史任务；`task cancel --id` 要求 requester 且仍占用对应设备会话。查询成功不代表安装成功，必须看 `task.status`（get 返回对象的 `status`）。
- 设备释放可能导致任务进入 `canceled/DEVICE_RELEASED`；任务完成前保持租约，转移会话前关注 requester 与占用者变化对取消权限的影响。

## ADB 与 native

- 安装前必须确认用户已明确授权目标设备和指定 APK；仅收到包路径或 URL 不代表已经授权安装。用户已明确要求安装该 APK 时，PackageInstaller 的精确确认动作可视为同一授权范围。
- `--transport native --url-file <path-or-dash>` 直接连接 Dora `event.io` WebSocket 并发送 `app.install`。该路径不获取 ADB 地址，不需要本机 ADB 端口，且只支持当前用户已占用的 Android 设备。命令等待 Dora 返回成功或失败终态；文本模式显示进度，JSON 只输出终态结果。默认超时为 1800000 毫秒，可用 `--timeout-ms` 调整，最大 14400000 毫秒。原生安装默认发送 `resign:true`；可用 `--resign false` 明确请求不重签。
- 原生 URL 安装仅使用 Dora 官方直链契约；该契约没有 SHA-256 字段，因此 `--transport native` 不接受 `--sha256`。需要客户端校验制品摘要时显式使用 ADB URL 路径。
- `--transport adb --apk <path>` 接受本地普通 `.apk` 文件，通过参数数组执行 `adb install -r -d`。大文件仍会经过远程 ADB tunnel。
- `--transport adb --url-file <path-or-dash>` 由设备通过 `curl` 或 `wget` 直接下载，避免本机通过远程 ADB tunnel 传输整个文件。只接受最终 HTTPS 制品 URL，不跟随重定向，下载上限为 2 GiB。URL 文件在 POSIX 上必须是 owner-only（如 `0600`/`0400`）；`-` 只读取非 TTY stdin。
- 共享 MCP 调用不能使用 `--url-file -`，以免读取 MCP 协议 stdin；此时改用 owner-only URL 文件。直接运行 CLI 时仍可通过管道传入。
- ADB URL 下载必须同时提供可信的 `--sha256`。bytedcli 在安装前读取设备端 `sha256sum` 结果并精确比对，不一致时停止安装。
- URL 不进入进程 argv、普通日志、JSON 输出或错误摘要。不要把带签名 URL 直接写进命令行参数或文档。
- `--transport adb --url-file` 在设备侧优先使用禁用启动配置与 URL glob 的 `curl`；仅当 `wget` 支持禁用启动配置、netrc 和 cookies 时才使用其 fallback，否则需要先在设备上安装 `curl`。
- 每次 ADB URL 安装只创建一个 `/data/local/tmp/bytedcli-dora-*.apk`，所有终态都会尝试精确清理该文件，不扫描或删除设备上的其他临时文件。清理失败时返回 `DORA_APP_CLEANUP_FAILED` 和精确路径；释放设备前按该路径手动删除。
- ADB URL 安装要求设备具备 `stat`、`sha256sum`、`head` 和 `wc`。设备缺少必要工具，或 package manager 未返回独立的 `Success` 行时，命令结构化失败；不会静默改走远程 ADB 大文件传输。
- Native URL 安装只把受保护的 HTTPS URL 交给 Dora `app.install` 并等待终态，不创建 bytedcli ADB 临时文件，也不要求设备存在上述 shell 工具。
- 结果中的 `transport` 表示实际传输方式。为保持既有 JSON 契约，ADB URL 路径返回 `device-download`；本地 ADB 安装返回 `adb`，原生 URL 安装返回 `native`，边缘节点安装返回 `edge`。
