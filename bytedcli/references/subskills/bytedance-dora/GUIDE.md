---
name: bytedance-dora
description: "Use when tasks mention Dora, 云真机, 云手机, cloud device, device occupation/reservation/release/renewal, native Android screenshots/recordings/tap/swipe/text/key control or PNG/JPEG upload without ADB, Android/adb cloud devices, iOS/bdc cloud devices, Harmony/鸿蒙/HDC remote addresses, ADB/BDC/HDC connection addresses, semantic Android UI actions on occupied Dora cloud devices, or installing APK/IPA packages on occupied cloud devices."
---

# bytedcli Dora

Use this skill for Dora cloud-device work. The command domain is top-level `dora`; do not use `bits dora`.

## Invocation

Prefer globally installed `bytedcli`:

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

Use JSON mode for machine-readable output by placing `--json` before `dora`:

```bash
bytedcli --json dora device list
```

REST 命令支持 Dora AK/SK 或 ByteCloud JWT 鉴权。未配置 Dora AK/SK 时，先运行 `bytedcli auth login`。

### Dora AK/SK 鉴权

在 Dora 控制台的个人设置「AK/SK」页面获取 Access Key 和 Secret Key，通过环境变量或 CI Secret 注入：

```bash
export BYTEDCLI_DORA_ACCESS_KEY='demo-access-key'
export BYTEDCLI_DORA_SECRET_KEY='demo-secret-key'
bytedcli --json dora device list
bytedcli --json dora device list --scope group --group-id <group-id>
bytedcli --json dora device get --serial <device-serial>
```

- 两个环境变量必须成对设置；完整配置优先于 ByteCloud JWT，无需 `bytedcli auth login`。只配置一个或换票失败时明确报错，不自动切换身份。
- bytedcli 用 AK/SK 换取 Dora `auth_token`，REST 请求携带 `Authorization: Bearer <token>`。token 有效期 30 分钟，仅在当前进程内缓存，提前 1 分钟刷新；HTTP 401 时重新换票并重试一次，权限错误不重试。
- 查询、占用、预约、续期、释放及 ADB/BDC/HDC 取址使用此 REST 鉴权。私有分组仍要求 AK/SK 所属用户具有对应成员权限。
- AK/SK 模式下预约不从 ByteCloud 登录身份推断通知接收人；需要通知时显式传 `--callback-uri`。
- 原生 WebSocket 控制、截图/录屏、文件推送和 `app deploy --transport native` 仍需要 ByteCloud JWT；Dora REST token 不替代 WebSocket 的 JWT。ADB transport 的 UI 与安装可使用 AK/SK 完成 REST 前置查询。
- AK/SK 与 token 不落盘；换票请求与响应不会出现在 HTTP trace 中。取消两个环境变量后使用 ByteCloud JWT。

## When to use

- 查询 Dora 公有云真机 / 云手机列表。
- 按 Dora 分组 ID 查询真实分组设备列表。
- 查询当前用户已占用设备列表。
- 获取单台设备详情。
- 占用一台空闲设备用于远程调试。
- 申请预约设备。
- 按用户输入的 `安卓/adb`、`iOS/bdc` 或 `鸿蒙/harmony/hdc` 精确占用对应平台设备。
- 占用云真机后做二次验证、续期，并在长时间任务中启动到期前自动续期守护。
- 用户明确要求安装指定 APK/IPA 时，确认占用后优先由 Dora edge 节点下载安装；仅 ADB/BDC transport 需要客户端连接验证。
- 释放、续期当前占用的设备。
- 获取设备 ADB、BDC 或 Harmony HDC 远端调试地址。
- 不依赖 ADB，通过 Dora 原生 WebSocket 控制已占用的 Android 设备：点击、滑动、文本输入和按键。
- 不依赖 ADB，通过 Dora 原生 WebSocket 将已占用 Android 设备的当前画面截为 PNG，或录制为 MP4。
- 不依赖 ADB，将本地 PNG/JPEG 写入已占用 Android 设备的受限图片目录。

## Quick start

```bash
# 查询公有空闲设备；默认筛选 public / idle / Android / physical / CN
bytedcli dora device list
bytedcli --json dora device list

# 常用筛选
bytedcli --json dora device list --os ios --device-type physical --usage idle --connect-state online
bytedcli --json dora device list --os android --device-type physical --usage idle --connect-state online
bytedcli --json dora device list --os harmony --device-type physical --usage idle --connect-state online
bytedcli dora device list --keyword "pixel"
bytedcli dora device list --connect-state online --country SG
bytedcli --json dora device list --os ios --is-intranet
bytedcli dora device list --level high --version "14" --manufacturer "Google"

# 查询当前用户已占用设备
bytedcli --json dora device list --scope occupied

# 查询指定 Dora 分组；group scope 必须显式提供 group ID
bytedcli dora device list --scope group --group-id <group-id>
bytedcli --json dora device list --scope group --group-id <group-id>
bytedcli --json dora device list --scope group --group-id <group-id> --os ios --device-type physical --keyword "demo"

# 获取设备详情
bytedcli --json dora device get --serial <device-serial>

# 占用设备用于远程调试；默认 1800 秒，最大 14400 秒
bytedcli --json dora device occupy --serial <device-serial> --time-sec 3600

# 申请预约设备
bytedcli --json dora device apply --serial <device-serial> --hours 2
bytedcli --json dora device apply --serial <model-key> --reservation-type model --hours 2

# 续期 / 释放
bytedcli --json dora device renew --serial <device-serial> --time-sec 14400
bytedcli --json dora device release --serial <device-serial>

# 获取连接地址
bytedcli --json dora device adb --serial <device-serial>
bytedcli --json dora device bdc --serial <device-serial>
bytedcli --json dora device hdc --serial <device-serial>

# Dora 原生 Android 控制，不依赖本机 ADB
bytedcli --json dora device control tap --serial <device-serial> --x 540 --y 1170
bytedcli --json dora device control swipe --serial <device-serial> --from-x 540 --from-y 1800 --to-x 540 --to-y 600 --duration-ms 300 --steps 8
bytedcli --json dora device control text --serial <device-serial> --text 'hello'
bytedcli --json dora device control key --serial <device-serial> --key back

# Dora 原生 Android 截图与录屏，不依赖本机 ADB；本机需安装 ffmpeg
bytedcli --json dora device screen export --serial <device-serial> --format png --output ./screen.png
bytedcli --json dora device screen export --serial <device-serial> --format mp4 --duration-sec 10 --output ./screen.mp4

# Dora 原生 Android 文件写入，不依赖本机 ADB；单文件必须小于 4 MiB
bytedcli --json dora device file upload --serial <device-serial> --file ./qr.png
bytedcli --json dora device file upload --serial <device-serial> --file ./qr.jpg --remote-path /sdcard/Pictures/bytedcli/codes/qr.jpg

# Android：按当前 UI hierarchy 精确查找、点击、长按
bytedcli --json dora device ui get --serial <device-serial> --resource-id example.app:id/action --package example.app
bytedcli --json dora device ui execute --action tap --serial <device-serial> --text "Open" --package example.app
bytedcli --json dora device ui execute --action long-press --serial <device-serial> --content-desc "Account" --duration-ms 5000 --package example.app

# Android：本地 APK 默认通过 ADB 安装
bytedcli --json dora device app deploy --serial <device-serial> --apk ./demo.apk

# 推荐：URL 装包默认 edge，由 Dora 边缘节点下载，不需要本机 ADB/BDC
printf '%s' "$APK_DOWNLOAD_URL" | \
  bytedcli --json dora device app deploy --serial <device-serial> --url-file -

# 仅提交边缘装包任务；需要重签名时显式增加 --resign true
bytedcli --json dora device app deploy --transport edge --serial <device-serial> --url-file ./package-url.txt --no-wait
bytedcli --json dora device app task list --serial <device-serial>
bytedcli --json dora device app task get --id <task-id>
bytedcli --json dora device app task cancel --id <task-id>

# Android：显式使用 Dora native WebSocket 远程安装
printf '%s' "$APK_DOWNLOAD_URL" | \
  bytedcli --json dora device app deploy \
    --transport native \
    --serial <device-serial> \
    --url-file -

# Android：保留原有 ADB 设备侧下载与 SHA-256 校验路径
printf '%s' "$APK_DOWNLOAD_URL" | \
  bytedcli --json dora device app deploy \
    --transport adb \
    --serial <device-serial> \
    --url-file - \
    --sha256 <expected-sha256>
```

## 远端调试地址（ADB / BDC / HDC）

三个命令都通过 `--serial` 获取当前用户已占用设备的远端调试地址，仅取址，不执行本机客户端、不验证连通性，也不自动占用或续期。已有占用可用 `device get` 和 `device list --scope occupied` 复核；需要新占用时，按下方通用占用流程选择对应平台。JSON 模式保留服务端返回的地址字段；Dora serial 与返回的调试地址是不同标识。

| 平台    | 取址命令                                            | 文本提示                |
| ------- | --------------------------------------------------- | ----------------------- |
| Android | `bytedcli dora device adb --serial <device-serial>` | `adb connect <address>` |
| iOS     | `bytedcli dora device bdc --serial <device-serial>` | `bdc connect <address>` |
| Harmony | `bytedcli dora device hdc --serial <device-serial>` | `hdc -s <address>`      |

ADB/HDC 文本模式分别展示存在的 `address` 和 `address_v6`；BDC 文本模式展示 `address`。HDC 返回远端 HDC Server 地址，文本提示是命令前缀，实际使用时追加所需命令，例如 `hdc -s <address> list targets`。HDC 接口若返回 `Device Occupied By Other`，先核实目标设备仍由当前用户占用。

HDC 的 `address` 格式为 `IPv4:端口`；`address_v6` 格式为不带方括号的 `IPv6:端口`，例如 `2001:db8:0:1:0:0:0:1:8710`，末尾的 `8710` 是端口。将返回值完整传给 `hdc -s`，保留服务端地址格式。设备可能只有 IPv4、只有 IPv6 或同时提供两者；某个字段缺省或为空字符串时，使用另一个非空地址。JSON 保留服务端字段，文本模式只输出非空地址。可用 `hdc -s <address> list targets` 验证连接，并用返回的 connect key 作为 `-t` 参数选择设备。

## Dora 原生 Android 控制（无需 ADB）

`device control` 直接连接 Dora 的控制 WebSocket，不会启动、调用或依赖本机 `adb`。控制前设备必须由当前用户占用，且设备详情必须包含有效 Session 与屏幕分辨率。

**授权边界**：执行 `dora device control`（tap、swipe、text、key）前，必须确认用户已明确授权目标设备（serial）和具体动作序列；不要在用户仅描述高层业务目标时静默执行破坏性点击、表单提交、支付或后退/Home 导航。

**控制与 UI 方式选择规则**：

- **原生 Dora 控制 (`dora device control tap|swipe|text|key`)**：已知目标像素坐标、滑动轨迹、整段文本输入或标准硬件按键（home、back、enter 等）时优先使用。直接走 Dora 原生 WebSocket，低延迟，不依赖本机 ADB 环境。
- **ADB 语义 UI (`dora device ui get|execute`)**：需要按 `text`、`resource-id`、`content-desc` 查找定位元素，需要断言页面唯一匹配或检查 UI hierarchy，或需要校验 package/readback 状态时使用（底层依赖 ADB 与 UIAutomator）。

```bash
# 点击：x / y 是设备屏幕内的零基像素坐标
bytedcli --json dora device control tap --serial <device-serial> --x 540 --y 1170

# 滑动：起点、终点是像素坐标；默认 300 ms、8 个中间移动帧；--duration-ms 最大 10000 ms，--steps 最大 120
bytedcli --json dora device control swipe --serial <device-serial> --from-x 540 --from-y 1800 --to-x 540 --to-y 600
bytedcli --json dora device control swipe --serial <device-serial> --from-x 100 --from-y 100 --to-x 900 --to-y 1800 --duration-ms 500 --steps 12

# 文本：通过 Dora 原生整段文本粘贴事件输入，支持 Unicode 和换行
bytedcli --json dora device control text --serial <device-serial> --text 'hello 世界'
bytedcli --json dora device control text --serial <device-serial> --text $'第一行\n第二行'

# 按键：支持别名或非负 Android 数字 keycode
bytedcli --json dora device control key --serial <device-serial> --key home
bytedcli --json dora device control key --serial <device-serial> --key back
bytedcli --json dora device control key --serial <device-serial> --key 66
```

按键别名：`home`、`back`、`enter`、`menu`、`recent` / `app-switch`、`volume-up`、`volume-down`、`power`。

控制结果中的 `delivery_status: "sent"` 表示 WebSocket 已连接且控制帧已提交给连接。Dora 协议没有逐操作 ACK，因此不能把该字段解释为设备端已确认执行。需要确认界面结果时，可通过 Dora Web 控制台（`https://dora.bytedance.net` 或 `https://bits.bytedance.net/quality/dora/`）观察实时画面，或使用 `dora device screen export --format png` 获取当前画面。

## Dora 原生 Android 截图与录屏（无需 ADB）

`device screen export` 复用 Dora 原生 `screen.io` WebSocket 下行画面流，不会获取 ADB 地址，也不会启动或调用本机 `adb`。命令仅支持当前用户已占用的 Android 设备，并要求本机 `PATH` 中存在 `ffmpeg`。

```bash
# 截取当前画面为 PNG；默认最多等待关键帧 15000 ms
bytedcli --json dora device screen export \
  --serial <device-serial> \
  --format png \
  --output ./screen.png

# 录制无音频 MP4；默认 10 秒，范围 1-300 秒
bytedcli --json dora device screen export \
  --serial <device-serial> \
  --format mp4 \
  --duration-sec 10 \
  --output ./screen.mp4

# 设备休眠或首个关键帧较慢时，可调大等待时间，最大 60000 ms
bytedcli --json dora device screen export \
  --serial <device-serial> \
  --format png \
  --output ./screen.png \
  --timeout-ms 30000
```

- `--format` 支持 `png|mp4`，默认 `png`；PNG 的 `--output` 必须以 `.png` 结尾，MP4 必须以 `.mp4` 结尾。
- `--output` 的父目录必须已经存在且不能是符号链接；命令拒绝覆盖已有文件。
- MP4 的 `--duration-sec` 默认 10 秒，范围为 1-300 秒；PNG 不接受该参数。当前只录视频，不包含设备音频。
- `--timeout-ms` 是等待首个 H.264 配置帧与关键帧的时间，默认 15000 ms，范围为 1-60000 ms；录屏开始后还会额外等待指定录制时长。
- 两条命令都会先校验当前用户占用关系和 Android 平台，再连接 Dora 原生画面流。原始 H.264 与未完成产物使用 owner-only 临时文件；只有 `ffmpeg` 成功后才原子写入目标路径，失败时清理临时文件。
- 成功 JSON 返回 `serial`、绝对 `output_path`、`format`、`codec`、`frame_count` 和 `bytes`；录屏额外返回 `duration_ms` 与 `frame_rate`。
- `DORA_SCREEN_FFMPEG_NOT_FOUND` 表示本机没有可执行的 `ffmpeg`；安装 FFmpeg 并确保其位于 `PATH` 后重试。
- `DORA_SCREEN_KEYFRAME_TIMEOUT` 通常表示设备休眠、画面流尚未就绪或关键帧等待时间不足；唤醒设备或调大 `--timeout-ms` 后重试。
- 单次捕获最多接收 256 MiB 原始 H.264 数据与 36001 个视频帧；`DORA_SCREEN_CAPTURE_TOO_LARGE` 或 `DORA_SCREEN_CAPTURE_TOO_MANY_FRAMES` 时缩短 `--duration-sec` 后重试。

## Dora 原生 Android 文件写入（无需 ADB）

`dora device file upload` 将一个本地 PNG/JPEG 先上传到 Dora 用户文件库，再通过官方 `file.push` 事件写入当前用户已占用的 Android 设备。该命令不获取 ADB 地址，也不调用本机 `adb`。

**授权边界**：仅当用户明确要求把指定本地 PNG/JPEG 写入指定 Dora 设备时执行。执行前确认目标 serial、源文件和设备目标路径；使用默认路径时也要明确告知 `/sdcard/Pictures/bytedcli/<本地文件名>`。用户只提供图片、询问能力或描述后续验收目标时，先确认这些写入参数，不执行上传。

```bash
bytedcli --json dora device file upload \
  --serial <device-serial> \
  --file ./qr.png

bytedcli --json dora device file upload \
  --serial <device-serial> \
  --file ./qr.jpg \
  --remote-path /sdcard/Pictures/bytedcli/codes/qr.jpg \
  --timeout-ms 120000
```

- 当前只接受字节签名与扩展名一致的 `.png`、`.jpg`、`.jpeg` 普通文件；拒绝符号链接、空文件和大于等于 4 MiB 的文件。4 MiB 起需要的分片上传尚未接入。
- 默认设备路径是 `/sdcard/Pictures/bytedcli/<本地文件名>`。显式 `--remote-path` 必须位于 `/sdcard/Pictures/bytedcli/` 下，路径穿越与反斜杠会被拒绝；以 `/` 结尾时自动追加本地文件名。
- 命令计算本地 SHA-256 用于结果校验，并按 Dora 官方协议计算 MD5 `file_hash`；随后用 `check_file` 复用已上传文件，或通过 `upload/file` 上传，再发送 `file.push {file_path,file_hash}` 并等待成功/失败终态。
- 成功结果中的 `status: "device file written"`、`confirmed: true` 只确认 Dora `file.push` 成功终态。该命令不会声称 MediaStore 已索引，也不保证相册应用立即可见；需要确认界面时另行导出屏幕或打开目标应用检查。
- JSON 返回 `serial`、`session_id`、`device_path`、`source_sha256`、`file_size`、`mime_type`、`transport`、`confirmed` 与 `status`。文件内容不会写入 argv、日志或错误。

### Markdown 多行换行（必读）

Shell 中需要输入真实换行时使用 `$'...'`，例如 `--text $'第一行\n第二行'`。不要写成 `--text "第一行\n第二行"`，bash / zsh 双引号不会把 `\n` 转换为换行，设备会收到字面量反斜杠和字母 `n`。

## Android 语义 UI 操作

`dora device ui get` 与 `dora device ui execute --action tap|long-press` 只支持当前用户已占用且在线的 Android 设备。调用方传 Dora serial；bytedcli 每次重新获取 Dora ADB 地址，按有效 IPv4、IPv6 target 的顺序执行完整在线校验，并为所有后续 ADB 命令显式传 `-s <resolved-target>`。

- `get` 是只读查询。执行 `execute --action tap|long-press` 前，必须确认用户已明确授权目标设备与具体动作；不要把仅提供 selector 视为点击授权。
- `--resource-id`、`--text`、`--content-desc` 必须三选一，均为精确匹配。
- 建议自动化流程显式传 `--package`。传入后会在动作前校验 resumed package，并将节点限定到同一 package；点击或长按后再次读取 resumed package。
- 每次查询或动作都重新执行 UIAutomator dump，只接受 `enabled=true` 且 bounds 有效的节点，不缓存旧 hierarchy 或旧坐标。
- 匹配结果必须恰好一个。零匹配返回 `DORA_UI_NODE_NOT_FOUND`，多匹配返回 `DORA_UI_NODE_AMBIGUOUS`；命令不会降级到 OCR、截图识别或 Computer Use。
- Lynx、WebView、Canvas 和系统 IME 可能不暴露 UIAutomator 节点。遇到结构化未找到错误时，检查页面节点可见性或改用 App 提供的稳定 resource-id。
- 成功 JSON 返回 `serial`、`adb_target`、selector 类型与脱敏指纹、`package`、`bounds`、动作、`duration_ms` 和 readback 状态；不输出 selector 原文或完整 hierarchy。
- `execute --action long-press` 的 `--duration-ms` 接受 500–10000 毫秒，默认 1200 毫秒。

## 应用安装（优先 edge）

`dora device app deploy` 要求 `--apk` 与 `--url-file` 二选一。URL 默认使用 edge，由 Dora 边缘节点下载安装；本地 APK 和带 `--sha256` 的 URL 默认使用 ADB。需要原生 WebSocket 安装时显式传 `--transport native`。安装前确认目标设备与安装包已获用户授权。

edge 默认等待任务 `succeeded` 才返回 `confirmed`；`--no-wait` 对进行中任务返回 `submitted`，对复用的已成功任务返回 `confirmed`，均需检查 `task.status`。超时或中断不会自动取消远端任务，先查询任务，不要自动切换 transport 重试。

安装参数、任务恢复、ADB/native 限制及输出契约见 [应用安装说明](references/app-install.md)；执行安装或处理失败时读取。

## 驱动服务地址、动态代理与会话转移

以下命令复用前述 REST 鉴权，支持完整 Dora AK/SK 或 ByteCloud JWT。

```bash
bytedcli --json dora driver local-addr --serial <device-serial>
bytedcli --json dora driver remote-addr --serial <device-serial>
bytedcli --json dora device cert-info --serial <device-serial>
bytedcli --json dora device open-proxy --serial <device-serial> --port 8080 --name demo-proxy --country CN --confirm
bytedcli --json dora device session-transfer --serial <device-serial> --to-user-id demo-user --session-id <active-session-id>
```

- `driver local-addr` 返回设备接入侧 ADB/BDC/HDC server 地址，`driver remote-addr` 返回云端 server 地址；它们只取地址，不连接、占机或续期。两者要求设备由当前调用身份占用。server 地址不能一律当作 `device adb` 返回的 adbd 地址使用。
- `device cert-info` 查询 iOS 证书名称 `cert_name` 和扩展内存支持 `increased_memory_support`，不获取证书文件；平台适用性由服务端判断。
- 执行 `device open-proxy` 前确认目标设备已由当前身份占用，并已在设备 Host 上将监听端口 forward 到设备应用；`--port` 是该 Host 端口，取值 1..65535。iOS 模拟器直接使用 Host 端口。命令不自动占机、续期或执行 forward。
- `--name` 可省略，最多 128 个字符，不允许控制字符；`--country` 默认 CN，必须使用服务端已配置的区域。确认设备、端口与操作意图后提供 `--confirm`。
- 同一设备会话、区域、端口重复创建会复用代理；每个会话最多 5 个不同代理。保留返回的 `proxy_id` 与 `endpoints`，优先使用 `address` / `address_v6`，仅在网络要求时使用 VIP 地址。代理创建成功不代表设备应用连通。
- 会话释放后代理失效；设备接入端重启后 endpoint 可能变化，不应长期缓存。当前 CLI 只提供打开代理，尚无代理列表刷新或单独关闭命令；需要这些操作时使用平台提供的对应能力，不能猜测 CLI 命令。
- 执行 `device session-transfer` 前确认转出设备和接收用户，并停止旧身份的自动续期守护。`--to-user-id` 必填且不能是当前占用者；`--session-id` 可选，用于服务端校验当前活跃会话；`--description` 是可选预留字段，实际审计描述由服务端生成。
- 转移保留 active `session_id`、已有连接资源和租约截止时间，不会释放或重新占机，也不会延长租约。公有远程调试设备检查接收方配额；私有设备要求发起方同时是当前占用人及分组 Admin/Owner，接收方可不在分组中。转移成功后使用接收方身份操作、续期和释放。

## 稳定占用云真机

以下设备占用与维护流程适用于 Android、iOS 和 Harmony。核心原则：**先明确平台，再只筛对应平台；占用后必须二次验证并续期；长时间占用要启动自动续期守护**。已占用的目标设备直接复核并取址，不重复选机和占用。仅需地址时使用前文取址命令；Android/iOS 的连接与可选安装见下一节。

### 输入到设备类型映射

| 用户输入 / 物料                               | 目标平台 | 连接方式                     | 安装方式                                                     |
| --------------------------------------------- | -------- | ---------------------------- | ------------------------------------------------------------ |
| `安卓` / `android` / `adb` / `.apk` / `.apks` | Android  | Edge HTTP、ADB 或 native WebSocket | `dora device app deploy`（`.apks` 需 bundletool 或平台支持） |
| `iOS` / `ios` / `iphone` / `bdc` / `.ipa` | iOS | Edge HTTP 或 BDC | URL 优先 edge；本地 IPA 使用 `bdc install --resign` |
| `鸿蒙` / `harmony` / `hdc`                    | Harmony  | HDC                          | 专用安装未接入；edge 支持需向服务端核实                       |

- 用户显式说 `adb` 就按 Android；显式说 `bdc` 就按 iOS；显式说 `鸿蒙`、`harmony` 或 `hdc` 就按 Harmony。
- 用户只给安装包时，从后缀推断：`.apk`/`.apks` => Android，`.ipa` => iOS。
- 显式平台与安装包后缀冲突时先停下说明冲突，不要跨平台安装或随机占设备。
- 没有平台线索且没有安装包时，先询问 Android、iOS 还是 Harmony；不要默认占 Android。

### 通用占用流程

1. **确认平台**：按上表确定 Android、iOS 或 Harmony，以及对应的 ADB、BDC 或 HDC 取址命令。
2. **只查对应平台候选设备**：

   ```bash
   # iOS / BDC
   bytedcli --json dora device list --os ios --device-type physical --usage idle --connect-state online

   # Android / ADB
   bytedcli --json dora device list --os android --device-type physical --usage idle --connect-state online

   # Harmony / HDC
   bytedcli --json dora device list --os harmony --device-type physical --usage idle --connect-state online
   ```

3. **占用候选设备**：

   ```bash
   bytedcli --json dora device occupy --serial <device-serial> --time-sec 3600
   ```

4. **占用后必须验证**：

   ```bash
   bytedcli --json dora device get --serial <device-serial>
   bytedcli --json dora device list --scope occupied
   ```

   验证点：目标 serial 出现在“我已占用”列表；平台与预期的 `android`、`ios` 或 `harmony` 一致；连接状态为 online；用途变为远程调试/已占用。任一不满足，不要继续取址、连接或安装，换一台重试。

5. **占用确认后立即续期，并再次确认**：

   ```bash
   bytedcli --json dora device renew --serial <device-serial> --time-sec 14400
   bytedcli --json dora device get --serial <device-serial>
   bytedcli --json dora device list --scope occupied
   ```

   续期策略：未指定时续到 Dora 允许的最大远程调试时长（当前最大 14400 秒）；如果用户指定占用时长，按用户时长续期但不能超过平台上限。续期失败时不要继续后续设备操作，先说明设备可能很快过期并重新占用或重试续期。

6. **长时间任务启动自动续期守护**：

   如果任务可能超过当前占用时长，或用户明确要求“别让设备过期 / 快到期自动续期”，占用验证和首次续期成功后立即启动后台续期守护。默认策略：到期前 10 分钟触发续期；如果当前 Dora JSON 字段不好稳定解析到期时间，则使用保守轮询，每 50 分钟续到 14400 秒，并把每次 `get / renew / occupied` 结果写日志。

   ```bash
   DORA_SERIAL=<device-serial>
   DORA_RENEW_SEC=14400
   DORA_RENEW_INTERVAL_SEC=3000   # 50 分钟；必须短于当前租约剩余时长
   DORA_RENEW_LOG="/tmp/dora-renew-${DORA_SERIAL}.log"
   DORA_RENEW_PID="/tmp/dora-renew-${DORA_SERIAL}.pid"

   (
     while true; do
       date '+%Y-%m-%d %H:%M:%S %z'
       bytedcli --json dora device get --serial "$DORA_SERIAL"
       bytedcli --json dora device renew --serial "$DORA_SERIAL" --time-sec "$DORA_RENEW_SEC"
       bytedcli --json dora device list --scope occupied
       sleep "$DORA_RENEW_INTERVAL_SEC"
     done
   ) >> "$DORA_RENEW_LOG" 2>&1 &
   echo $! > "$DORA_RENEW_PID"
   ```

   启动后要说明 PID 和日志路径。任务结束或释放设备前必须停止守护，避免无人使用时继续续期：

   ```bash
   kill "$(cat /tmp/dora-renew-<device-serial>.pid)"
   rm -f "/tmp/dora-renew-<device-serial>.pid"
   bytedcli --json dora device release --serial <device-serial>
   ```

   自动续期守护失败时，优先看日志里的 `renew` 返回和续期后的 `device get` / `--scope occupied`；连续失败不要继续声称设备安全，重新占用或提醒用户。

只释放本轮创建且已不再使用的占用；用户原有占用保持不变。Harmony 的应用安装支持需向边缘服务核实，当前没有专用 HDC 安装、控制或截图命令。

## Android/iOS 连接与可选安装

以下步骤用于用户明确要求连接设备或安装指定 APK/IPA 的任务；仅查询远端调试地址不需要执行这些步骤。

1. **按 transport 验证安装前置条件**：
   - Edge（推荐）：URL 可从边缘节点访问，设备由当前用户占用且在线；不获取 ADB/BDC 地址、不执行客户端连接。包格式与重签支持以服务端为准。
   - Android native：不获取 ADB 地址，也不执行 `adb connect`。保持设备由当前用户占用且在线；`dora device app deploy --transport native` 会再次校验 Android 平台、占用关系和有效 Dora session。
   - Android ADB：

     ```bash
     bytedcli --json dora device adb --serial <device-serial>
     adb connect <host:port>
     adb -s <host:port-or-serial> get-state
     ```

   - iOS BDC（本地 IPA 或显式 BDC 工作流）：

     ```bash
     bytedcli --json dora device bdc --serial <device-serial>
     bdc connect <bdc-address-or-command-from-dora>
     bdc devices
     ```

   ADB / BDC 连接验证不通过时不要走对应 transport 安装；edge/native 不以本机 ADB/BDC 连接作为前置条件。

2. **可选安装包**：仅当用户明确要求在目标设备安装指定包路径，或明确要求查找并安装指定安装包时执行；仅提供包路径、URL 或安装包物料时，先确认目标设备与安装动作。未授权安装时只占用、续期、按需启动自动续期守护并连接验证。
   - Android APK：

     ```bash
     bytedcli --json dora device app deploy --serial <device-serial> --apk <package.apk>
     ```

     原生安装默认向 Dora 发送 `resign:true`；如需明确请求不重签，传 `--resign false`，需要重签则传 `--resign true`。edge 默认请求不重签，可用 `--resign true` 显式请求重签。SDK 的 `installDoraNativeAndroidApp` 与 `installDoraAndroidApp` 使用同名 boolean 字段 `resign`；这是发往平台的请求开关，不代表已经独立验证包签名。

     用户已明确授权安装且有受保护 HTTPS APK URL 时，优先使用 `--transport edge --url-file -`，由 Dora 边缘节点下载。需要 native WebSocket 时显式传 `--transport native`。需要客户端 SHA-256 校验时使用 `--transport adb --url-file - --sha256 <digest>`。edge/native 只发起安装并等待终态，不执行任何 UI 点击。若云真机弹出 PackageInstaller 二次确认，无 ADB 流程先用 `dora device screen export --format png` 观察画面，再在用户已授权且坐标精确时使用 `dora device control tap`；不要点击未知 OEM 弹窗。只有必须按 resource-id / text 做语义定位时才使用 `dora device ui get|execute`，该分支会重新引入 ADB。

   - iOS IPA URL：优先 `app deploy --transport edge --url-file <path> --resign true`，设备和证书支持以边缘服务结果为准。
   - iOS 本地 IPA（BDC）：

     ```bash
     bdc install --resign -u <ios-udid-or-bdc-id> <package.ipa>
     ```

     iOS 真机常见证书不匹配；默认加 `--resign`，不要先尝试无重签安装再失败。

3. **安装后验证**：Edge 以任务 `succeeded` 终态作为安装结果；`submitted` 不足以证明安装成功。Android native 以 `app.install` 成功终态作为安装结果；完全无 ADB 的验收可用 `device screen export` 观察画面，并在坐标明确时用 `device control key|tap|swipe|text` 完成启动与交互。需要按包名执行 `pm list packages`、启动 activity 或语义 UI 定位时才切到 ADB。Android ADB 使用 `pm list packages` 或启动 activity；iOS 使用 `bdc` 的 app list/info/launch 能力验证 bundle 存在并可启动。没有包名 / bundle id 时，先从安装包元信息解析，不凭文件名猜。

## Notes

- `device list` 的主要筛选值使用语义化输入：`--usage idle|remote-debug|automation|ops|reserve|all`，`--connect-state online|offline|all`，`--os android|ios|windows|macos|linux|harmony`，`--device-type physical|vm|emulator|baymax`，`--level low|medium|high|all`。
- `--is-intranet` 仅用于公有设备池；传入时向 Dora 设备列表接口追加 `is_intranet=true`，未传时不按该字段筛选。
- 查询分组设备必须同时传 `--scope group --group-id <id>`。分组查询支持可选的 `--keyword`、`--os` 和 `--device-type`；使用任一筛选时，查询最近 7 个完整自然日（北京时间）的分组设备统计结果，无匹配设备时返回空列表。其他 public 专用筛选和分页参数仍会被拒绝。未使用筛选时一次返回完整分组；分组不存在、无权限、空列表、归属不一致或接口失败都会明确报错，绝不降级查询公有池。
- `--version` 按 Dora 页面设备系统版本过滤，`--manufacturer` 按品牌过滤。
- 文本输出会渲染关键字段；JSON 输出保留结构化结果，适合脚本继续解析。
- `adb` / `bdc` / `hdc` 文本模式输出连接提示；需要原始地址字段时使用 JSON 模式。`hdc` 使用 `-s` 指定远端 HDC Server，实际使用时需追加具体命令。
- 设备操作按 Dora 页面接口执行，`occupy` 固定用于远程调试占用，`apply` 用于预约申请。
- `device ui`、`app deploy --transport adb|native` 为 Android-only；edge 由边缘服务判断设备与安装包支持。安装只操作当前占用设备，不自动占机或续租。URL 优先 edge，本地 APK 或带 SHA-256 的兼容调用使用 ADB。
- `device control tap|swipe|text|key` 仅支持当前用户已占用的 Android 设备，直接走 Dora 原生 WebSocket，不需要本机 ADB；iOS 设备继续使用 BDC 能力。
- `device screen export --format png|mp4` 仅支持当前用户已占用的 Android 设备，直接读取 Dora 原生 H.264 画面流，不需要本机 ADB；需要本机 `ffmpeg` 生成 PNG / MP4。
- `device file upload` 仅支持当前用户已占用的 Android 设备，通过 Dora 用户文件库与原生 `file.push` 写入受限图片目录，不需要本机 ADB。
- 控制坐标使用零基像素值，必须落在 Dora 返回的屏幕宽高范围内。不要传 `0..1` 比例，bytedcli 会在发送前自动归一化。
- 文本控制不会在结果中回显输入内容，只返回字符数和发送帧数。

## 常见错误

- 不要使用 `bits dora ...` 或猜测 `dora device connect`；Dora 是顶层 `dora` 域，连接地址分别通过 `device adb` / `device bdc` / `device hdc` 获取。
- 不要把 `--group-id` 传给默认的 public 查询来判断分组归属；bytedcli 会拒绝这种组合，因为公有池接口不接受分组归属语义。必须使用 `--scope group --group-id <id>`。
- `DORA_GROUP_EMPTY` 表示分组接口请求成功、但该分组当前没有设备；它不同于 `DORA_GROUP_NOT_FOUND`。应停止依赖设备的后续步骤，等待分组补充设备或改为显式查询另一个已知分组，不要降级到公有池。
- 不要把 `adb` 当成 iOS 连接方式，也不要把 `bdc` 当成 Android 连接方式。
- 不要为了点击、滑动、文本输入或 Android 按键先获取 ADB 地址；优先使用 `dora device control ...` 原生控制命令。
- 不要把 `delivery_status: "sent"` 当成设备端 ACK；需要确认操作效果时使用 `dora device screen export --format png` 或 Dora Web 控制台实时画面核对。
- 不要猜测 `dora device screenshot` / `record` / `stream` / `screenrecord`；标准命令是 `dora device screen export --format png|mp4`。
- 不要把 `dora device file upload` 的成功解释为图片已进入 MediaStore 或相册；它只确认指定设备文件路径写入成功。
- 不要只看 `occupy` 命令返回成功；必须用 `device get` + `--scope occupied` 验证确实占到当前用户名下，然后执行 `device renew` 续期并再次确认。
- 不要为长时间占用只续期一次；用户要求保持占用或任务可能超过租约时，要启动自动续期守护，并记录 PID 与日志路径。
- 不要在释放设备后留下自动续期守护；释放前先 kill 对应 PID，否则可能无人使用时继续续期占住设备。
- 不要在多设备连接时省略 `adb -s` / `bdc -u`；安装必须指向刚才验证过的目标设备。
- 不要在用户未提供安装包、也未指定包来源时主动找包或猜包；这种场景不进入安装流程，仅查询地址时不执行客户端连接验证。
- 不要猜测 `dora device ui find` / `search`；标准查询命令是 `dora device ui get`。
- 不要把 Dora serial 直接传给 `adb -s`；`device ui` 和 ADB transport 的 `device app deploy` 会在每次调用时解析并验证当前 ADB target。边缘安装使用 `--transport edge`，WebSocket 安装使用 `--transport native`。
- 不要把签名 URL 放进 `--url-file` 的参数值；该参数接收文件路径或 `-`，URL 内容通过 owner-only 文件或非 TTY stdin 读取。
- 不要给 `--transport native` 传 `--apk`、`--sha256` 或 ADB 地址；该路径只接收 `--url-file` 并等待 Dora 原生安装终态。
