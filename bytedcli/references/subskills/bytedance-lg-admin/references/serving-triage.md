# 线上 Merlin 部署分层排查 Runbook（snapshot / pilot）

本文是按链路顺序组织的**线上部署排障手册**：从一个 Merlin 部署链接 / PSM 出发，逐层走到控制面、数据面、容器内部，再追到镜像与源码。命令级 FAQ（登录、站点、JSON 写法等通用问题）看 [`troubleshooting.md`](troubleshooting.md)，本文不重复；本文专注"serving 不健康时按什么顺序查"。

适用对象：Forge 训练任务部署到 Merlin 在线 serving 的 snapshot / pilot_gpu 两类机器（CUDA / MLU 机型流程一致）。所有操作只读，不要在生产容器里做写操作。

章节索引：

- [§0 三个先记住的结论](#0-三个先记住的结论)
- [§1 从链接 / PSM 解析坐标](#1-从链接--psm-解析坐标)
- [§2 控制面全景：lg-admin torch serving get](#2-控制面全景lg-admin-torch-serving-get)
- [§3 数据面进容器：lg-admin torch serving inspect](#3-数据面进容器lg-admin-torch-serving-inspect)
- [§4 非 CN / RoW：链接 → GPCP SDP → 只读排查](#4-非-cn--row链接--gpcp-sdp--只读排查i18n-ttsg--va)
- [§5 inspect 不够用时：手搓进容器（CN / 同构 orthrus 站点）](#5-inspect-不够用时手搓进容器cn--同构-orthrus-站点)
- [§6 往镜像与源码侧追：icm → SCM → 本地仓](#6-往镜像与源码侧追icm--scm--本地仓)
- [§7 分层排查顺序（checklist）](#7-分层排查顺序checklist)
- [§8 健康判据速查](#8-健康判据速查)

## 0. 三个先记住的结论

1. **Forge job id 是跨系统主键。** snapshot / pilot / prifly / Forge / Merlin deploy 全靠它关联；拿到链接后第一件事就是解出 job id，后续命令只认它。
2. **k8s ready ≠ 健康。** `readyReplicas` 齐了只代表框架探针通过、容器进程在，不代表模型加载完成。真 ready 的判据是：snapshot 侧产物已生成并上传，pilot 侧日志出现 `warmup model success`、预编译产物就位且无 recompile、endpoints 拉起。
3. **先定性"慢"还是"crash-loop"，再动手。** 看 worker 进程是否反复换 PID、每次错误是否停在同一处：确定性 crash-loop 不要当性能问题等，慢 / 正常重试不要当崩溃反复重启干预。

## 1. 从链接 / PSM 解析坐标

### 1.1 认平台

- Merlin 部署平台的 Web origin 形如 `https://ml.<merlin-domain>`（CN 生产为 `https://ml.bytedance.net`，ByteIntl / TTP 等站点各自有独立 origin，见 [`invocation.md`](invocation.md) 的站点表）。这是**部署平台**，不是 Forge。
- Forge / Reckon 在另一个域（`https://reckon.bytedance.net` 的 `/forge2/...`），管训练 job 与 serving service；prifly 监控页也挂在 Forge 侧。
- 链接只用来取坐标，排查本身不靠浏览器点页面，走下面的 CLI。

### 1.2 从部署 URL / PSM 解字段

Merlin 部署详情 URL 形态：

```text
https://ml.<merlin-domain>/deployment/serviceList/service/detail/<psm>/deploy/<deploy-id>
```

其中 PSM 是点分的坐标串。snapshot 与 pilot_gpu 两族 PSM 的规范后缀分别是：

```text
snapshot.<biz>.model_<job-id>[_runtime_<runtime-id>_<tag>.<pool>.<machine-spec>]
pilot_gpu.<biz>.model_<job-id>
```

示例（值均为占位）：

```text
snapshot.sample_biz.model_12345678_runtime_87654_demo.sample-pool.cambriconmlu580x6.16g.1x/deploy/87654321
```

| 片段                       | 含义                                                                              |
| -------------------------- | --------------------------------------------------------------------------------- |
| `snapshot` / `pilot_gpu`   | 机器类型：snapshot 负责模型转换 / 编译 / 产产物，pilot 负责在线推理               |
| `sample_biz`               | biz（业务线标识）                                                                 |
| `model_12345678`           | **Forge job id，跨系统主键**                                                      |
| `runtime_87654`            | runtime id（snapshot 这一轮转换 / 编译运行的标识）                                |
| `demo`                     | 部署 / 机房标签（如 AZ 标记，随站点不同）                                         |
| `sample-pool`              | 资源池                                                                            |
| `cambriconmlu580x6.16g.1x` | 机型规格（例：MLU580 6 卡；CUDA 机型是对应的 GPU 规格串），用于判断资源类型与卡型 |
| `deploy/87654321`          | 本次发布单 id（一次发布动作一个）                                                 |

解析动作：肉眼或 `cut -d. -f...` / `sed` 拆出 job-id、biz、机型、deploy-id。job-id 同时可以在 Forge 页面 `https://reckon.bytedance.net/forge2/jobs/<job-id>` 反查训练侧信息。

## 2. 控制面全景：`lg-admin torch serving get`

拿到 job-id 后先拉控制面全景（Forge 页、prifly 页、snapshot / pilot 两个 PSM、每个 deploy 的 ready 状态与实例 host）：

```bash
# CN 站点
bytedcli --json lg-admin torch serving get --job-id 12345678

# 非 CN 站点：--origin 换成本次 deployment 链接里的 Merlin origin。JWT 站点随
# origin 自动推导（Merlin 与 Reckon 两侧都是），不需要全局 --site；但首次使用
# 某站点前先登录该站点，例如 ByteIntl：bytedcli --site i18n-bd auth login
bytedcli --json lg-admin torch serving get --job-id 12345678 \
  --origin https://ml-i18nbd.byteintl.net

# tiktok-row RoW 站点：先登录 TikTok SSO 站点，再用 --origin 指向 row Merlin。
# Reckon 区域 host 与 JWT 均由 origin 自动推导（i18n-tt -> reckon-us.tiktok-row.net），
# 不用再手填 --reckon-base-url
bytedcli --site i18n-tt auth login
bytedcli --json lg-admin torch serving get --job-id 12345678 \
  --origin https://ml.tiktok-row.net
```

返回里关键字段：

- `forge_job_url`：Forge job 页；
- `reckon_base_url`：本次实际使用的 Reckon host（CN 为 `reckon.bytedance.net`；row origin 自动推导为区域 host，可据此核对）；
- `prifly[]`：prifly 监控页（serving service 级），含 `state`；prifly 查询失败时其他字段照常返回并带 `prifly_error`；`prifly_hint` 字段始终存在（无提示为 `null`），仅 row 站点查到空列表时为非空字符串（自动推导 host 时提示如何用 `--reckon-base-url` 覆盖；已显式传 `--reckon-base-url` 时为中性提示“该 job 可能没有 prifly 页”）；
- `services[].psm` / `psm_detail_url` / `kind`（`snapshot` | `pilot_gpu`）；
- `services[].deployments[]`：`deployment_id`、`region`、状态摘要（形如 `ready 3/3 (1 unavailable)`，直接对应 k8s `readyReplicas` / `replicas` / `unavailableReplicas`）、`instances[]`（`region`、`idc`、`host`、`state`，以及始终存在的 `pod_name`（k8s pod 名，RoW SDP 的 `--pod-name` 目标；NotReady / 未调度行为 `null`）与 `container_id`（CRI 容器 id；无值时为 `null`））。文本模式实例表额外展示 `POD NAME` 列（`null` 显示为 `-`）；`container_id` 仅在 `--json` 输出中提供。实例 host 可能是裸 IPv6，可以直接给 inspect 用。

用法要点：

- 默认 `--include-instances` 开启；只要页面链接时用 `--no-include-instances` 省掉逐 deploy 的实例查询。
- `--origin` 接受完整 URL，也接受裸 host（如 `ml.tiktok-row.net`，自动补 `https://`）。
- Reckon host 推导表来自 Merlin / Forge 站点表：`i18n-tt -> reckon-us.tiktok-row.net`、`eu-ttp -> reckon-eu.tiktok-row.net`、`us-ttp -> reckon-ttp.tiktok-row.net`；CN 与 ByteIntl（`i18n-bd`，与 CN 同 Reckon 平面）保持 `reckon.bytedance.net` 不变。Merlin 与 Reckon 两侧请求的 JWT 都按 `--origin` 推导出的站点分别获取（i18n-tt / eu-ttp / us-ttp），全局 `--site cn` 不会再导致 row 控制面 401；首次使用某站点前先 `bytedcli --site <site> auth login`。推导不符合预期时用 `--reckon-base-url <url>` 显式覆盖（自定义 host 回退全局站点 JWT）。该参数只接受裸 https origin：传裸 host 会自动补 `https://`，但带 userinfo/port/path/query/fragment（如 `/`、`https://h/sub`）会直接报 INPUT_ERROR，不会生成不可用的 job 页 URL，也不会静默落到别的默认平面。
- eu-ttp / us-ttp 的 Reckon prifly 查询路径（JSON API 走各站点独立 API host：`reckon-bdee.tiktok-eu.org` / `reckon-bdee.tiktok-us.net`）**尚未在真实环境验证**；空列表时 `prifly_hint` 会明确标注该路由未验证（此时 `--reckon-base-url` 无法把内置表内 host 改到别的 API host，不要把 flag 当这两站的修复手段）；只有站点表之外的自定义 host 才会同时覆盖页面与 API 请求。失败时以 `prifly_error` 为准，不要默认这两站 prifly 已可用。
- `ready x/y` 是 k8s 视角，**只能当入口线索**，健康与否以第 3、7 节的产物 / 日志判据为准。
- 某个 target 没有任何 live instance（发布单停了 / 缩容到 0）时，实例列表为空——这本身就是结论（服务没在跑），不是 job 不存在。

## 3. 数据面进容器：`lg-admin torch serving inspect`

`inspect` 把"授 host root → ssh 上宿主机 → 按进程定位容器 → 进容器 namespace 跑只读命令"整条链路自动化。

```bash
# 交互式定位 + 打印进入命令（默认 grant 开启，TTY 下直接授权）
bytedcli lg-admin torch serving inspect --job-id 12345678 --target snapshot

# 自动化 / JSON：一条只读命令直接在容器里执行
# 非 CN 实例必须显式 --site 与 --account；host 已在自己名下时用 --no-grant
bytedcli --json lg-admin torch serving inspect --job-id 12345678 \
  --target pilot --instance <ipv6> \
  --site i18n --account <your-account> --no-grant \
  --exec '<read-only cmd>' \
  --yes
```

常用参数：

- `--target pilot|snapshot|both`（默认 `both`）；`--idc <name>` 按机房过滤；`--instance <ip>` 锁定单机；`--all-instances` 对全部实例 fan-out。
- `--grant` / `--no-grant`：进机前先通过 orthrus 授 host root（默认开）；已持有机器时用 `--no-grant` 只 ssh。
- `--yes`：JSON / 非 TTY 下真正提交授权（否则只 dry-run 打印将授予的内容）。
- `--site cn|i18n|ttp` + `--account <user>`：非 CN 实例必填（CN 对当前登录用户自助授权）。`cn` 可从实例 `idc`/`region` 推断，i18n / ttp 从不猜测——授权错控制面比不授权更糟。
- `--exec '<cmd>'`（约定只读：`cat` / `ls` / `grep` / `tail`）、`--exec-max-bytes`、`--exec-timeout-ms`；`--locate-timeout-ms` 放宽慢主机的定位超时（默认 60s，慢 socket-hybrid 主机光建连就可能 >30s）。

inspect 内部机制（手搓时也是同一套，见第 5 节）：

1. 复用 `serving get` 的解析器拿到 pilot / snapshot 实例（带 `idc`）；
2. orthrus 授 host root（CN 自助；i18n / ttp 走 cookie 授权，需要 `--account`）；
3. 轮询等待 sshd 生效后 `bgo ssh root@<host>` 登上**宿主机**（不是容器）；
4. 按**进程签名**在宿主机上定位容器 PID，并从 `/proc/<pid>/cgroup` 解出 CRI 容器 id；
5. 给出 PID、`/proc/<pid>/root`、CRI id 与可粘贴的 `nsenter` 进入命令；带 `--exec` 时直接在容器 namespace 里跑完并回收输出。

进程签名与消歧（一台宿主机经常混部多个模型，必须按 job 收窄）：

| target   | 签名（按尝试顺序）                                                                                                                  | 收窄方式                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| pilot    | `manhattan_worker`（实际计算进程，cmdline 带 `--model_name=...r<job-id>_0`），其次 `pilot_main` / `lgt_pilot_main`（只是 launcher） | 先要求 cmdline 命中 `model_<job-id>` 或 `r<job-id>`，再退回纯签名匹配     |
| snapshot | `snapshot_model_optimizer`                                                                                                          | 定位到共享的 snapshot 容器即可，按模型的编译日志在容器内 workspace 下再分 |

JSON 模式下某 target 有多实例又没 pin `--instance` 时返回 `selection_required` + 候选列表，不会挂住等交互；部署已停时返回空实例但仍带 `serving_pages`（Forge prifly 页与状态），用来区分"停服"与"job 不存在"。

### 3.1 pilot 健康一键配方

```bash
bytedcli --json lg-admin torch serving inspect --job-id 12345678 \
  --target pilot --instance <ipv6> --no-grant \
  --exec 'ls /opt/tiger/inductor/write_done; grep -c "warmup model success" /var/log/tiger/data.manhattan.log; grep -ciE "recompil|guard fail" /var/log/tiger/worker_*.stderr'
```

健康 = `write_done` 存在（预编译包已解出）+ `warmup model success` 出现 + recompile 计数为 0。缺 `write_done` 或 recompile 非 0，说明 pod 在冷编译 / 按请求 batch size 重编译。

## 4. 非 CN / RoW：链接 → GPCP SDP → 只读排查（i18n-tt；sg / va）

tiktok-row RoW 集群（`ml.tiktok-row.net` 等）上，第 3 节的 orthrus 授权 + bgo/ssh 通道不可用；进容器的**唯一合规通道是 GPCP SDP**（白屏 WebShell：服务端命令白名单 + 审计留痕）。Forge/Primus 训练 pod 另有 Forge 侧 SDP 入口，但与本 runbook 的 Merlin 在线 serving 无关；Bernard serving pod（snapshot / pilot）统一走 `bytedcli gpcp sdp`。ByteIntl（`i18n-bd`，与 CN 同 Reckon / SSO 平面）不适用本节，沿用第 3 节。

适用范围（与 `bytedance-gpcp` skill 对齐）：

- **本节 SDP 路径只对 i18n-tt（`ml.tiktok-row.net`，区域 sg / va）验证过。**
- **eu-ttp 机器 GPCP SDP 暂不支持**（网络问题）；eu-ttp serving 只能先用第 2 节 `serving get --origin https://ml-eu.byteintl.net` 做控制面只读排查，进容器走合规通道的人工审批，不要在 runbook 里给 SDP 命令。
- **us-ttp（`ml-ttp-us.byteintl.net` / `ml.tiktok-usts.org`）的 SDP attach 未验证**：GPCP SDP 只有 `--region sg|va` 两个入口，不覆盖 TTP US 合规区域；控制面查询可用，进容器前先与合规 / owner 确认通道，不要假设 sg/va 能 attach 到 us-ttp pod。

### 4.1 站点、区域与凭据

| 用途                  | 选择                                                                                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Merlin/Bernard 控制面 | 命令级 `--origin https://ml.tiktok-row.net` 即可；JWT 站点随 origin 自动推导，首次使用先 `bytedcli --site i18n-tt auth login`（eu-ttp / us-ttp 换各自 origin 与登录站点，仅做控制面查询，SDP 见上）              |
| RoW Reckon / prifly   | host 与 JWT 均由 `--origin` 自动推导：i18n-tt → `https://reckon-us.tiktok-row.net`（eu-ttp / us-ttp 的 prifly JSON API 路径未在真实环境验证）；返回的 `reckon_base_url` 可核对，异常时用 `--reckon-base-url` 覆盖，CN 行为不变 |
| SDP 区域              | 仅 `--region sg`（默认；覆盖新加坡 / maliva / 马来机房）或 `--region va`（美东独立入口）；没有其他区域                                                                                                        |
| SDP 凭据              | 固定 i18n-tt / TikTok SSO 登录态（`bytedcli --site i18n-tt auth login`，不是 CN 浏览器 SSO）+ i18n ByteCloud **用户** JWT；AK/SK 会被拒绝                                                                     |

### 4.2 SDP 目标：alive pod 的 pod 名

- pod 名直接取 `serving get` 输出里的 `instances[].pod_name`（= Bernard `detail.tasks[].id` = k8s `metadata.name`）；无值时字段为 `null`（NotReady / 未调度行），这样的 pod 本来也 attach 不了。`--json` 输出的同一 instance 对象还带 `container_id`（CRI 容器 id；无值为 `null`）。常规排查不用再单独跑 `merlin deploy get`。
- 需要 `healthCheckResults.alive` / `startedAt` 等存活细节时再补：`bytedcli --site i18n-tt -j merlin deploy get --deployment-id <deploy-id> --origin https://ml.tiktok-row.net`。
- **只有 `alive: true` 的主容器能 attach**。NotReady / alive=false 的 pod：作业能创建，但 `command execute` 永远停在 `init_conn_resp code=1`，最终 `SDP_WEBSHELL_INIT_TIMEOUT`；调大 `--init-timeout-ms` 无用（不是慢，是容器没有活着的主进程），不要反复重试。
- 滚动发布中 pod 可能换 host / 换名；attach 失败先重跑第 2 节全景与 deploy 详情，确认目标仍 alive。
- 偶发 HTTP 500 `IAM API error code: 10100001` 是后端瞬时错误，等 15s 重试即可。

### 4.3 建 SDP 作业并执行只读命令

> 本文其余步骤均为只读；`gpcp sdp job create` 是本节唯一会创建服务端对象的动作（创建诊断用 WebShell 作业）。它默认 dry-run，**先预览、向用户确认目标 pod 与区域后再加 `--yes` 提交**，不要把带 `--yes` 的命令当只读命令直接跑。

```bash
# 1) 预览建作业（不带 --yes 即 dry-run：submitted=false，不创建任何对象）
bytedcli --site i18n-tt -j gpcp sdp job create \
  --target bernard --pod-name <pod-name> --user root \
  --region sg

# 2) 与用户确认预览里的 pod / region 无误后，再加 --yes 真正创建，返回 jobId / detailUrl
bytedcli --site i18n-tt -j gpcp sdp job create \
  --target bernard --pod-name <pod-name> --user root \
  --region sg --yes

# 3) 同一 jobId 可多次复用，每次执行一条只读命令
bytedcli --site i18n-tt -j gpcp sdp command execute \
  --region sg --job-id <sdp-job-id> \
  --init-timeout-ms 60000 --timeout-ms 60000 \
  --command '<单条只读命令>'

# 4) 查服务端白名单（数百条：ps / cat / tail / grep / find / ls / ldd / nvidia-smi / dmesg 等）
bytedcli --site i18n-tt gpcp sdp whitelist list --region sg --page-size 100
```

协议约束（实测）：

- 只接受**单行**命令：管道 `|` 可以；换行、`;`、`&&`、`||`、后台 `&` 会被拒绝或不结束。CN runbook 里的多段配方要拆成多次 execute。
- 白名单服务端强制，被拒命令直接报错、不会被改写。
- 返回的 `completed` 是权威完成状态；`exitCode` **恒为 null**（SDP 协议不回传退出码），成败只能看输出内容。
- 冷启动首次连接偶发 init 慢，`--init-timeout-ms 90000~120000` 即可；长时间 code=1 不转 code=0 基本是目标容器不 alive。

### 4.4 RoW 容器日志布局与日志网关限制

- torch2.7 起的 `snapshot_torch_gpu` 基底（RoW 实测）**没有** CN 基底的 `workspace/dump_log_backup/<n>/{load_distcp_serving,torch_dense_convert,aot_compile_part_0,aot_warmup}.log` 四段布局：每轮任务在 `workspace/tmp_ws_<n>/...` 建临时目录，阶段输出并入 `/var/log/tiger/snapshot_model_optimizer.python.log.*`；Python import 阶段就失败时临时目录秒建秒删、没有任何阶段日志。任务 / 结果文件是 `workspace/<model-r-name>/<task-dir>/model_optimize_task.json` 与 `model_optimize_result.json`——失败时 result 为 `{}`、`TosPath`/`ResultPath` 恒空，即无产物。
- pilot 的健康判据与 CN 相同（见第 8 节速查表：`write_done` + `warmup model success` + recompile 计数 0），但 NotReady pilot 同样 attach 不了；拿不到容器内证据时如实说明，不要用日志网关的空输出冒充"无异常"。
- 容器日志网关（`merlin deploy logs` / Bernard `instanceLog`）对"活着但不 ready"的 pod 返回空内容、对已销毁 pod 返回 400/404。snapshot / pilot 的文件日志**只在存活容器内、经 SDP 读取**，不要等日志网关补数据。
- 镜像 / SCM 只读溯源仍走第 6 节：镜像 tag 与构建元数据用 `bytedcli --site i18n-tt -j merlin deploy service get --service-id <service-id> --origin https://ml.tiktok-row.net` 获取，JSON 路径为 `detail.config.icm_url_list` 与 `detail.config.custom_build_meta`（`base_image` + 全部 SCM 包版本），RoW 同样可用；换波对比时 diff 两者，SCM overlay 相同而 base 镜像切换是典型基底回归信号。`<service-id>` 取第 2 节 `serving get` 输出的 `services[].service_id`。

## 5. inspect 不够用时：手搓进容器（CN / 同构 orthrus 站点）

需要交互排查、跑较长的只读脚本，或 inspect 定位失败时，按固定手法自己走一遍。tiktok-row RoW 不适用本节（没有 orthrus / bgo 通道），走第 4 节 SDP。

### 5.1 bgo 的三个硬约束

1. **必须有 pty**：`bgo` 启动时把终端切 raw mode，无 tty（脚本 / 管道直连）会直接 `SIGSEGV`。统一用 `script` 包一层：

   ```bash
   script -q /dev/null bgo ssh root@<ipv6>
   ```

2. **复杂命令单行 base64 传输，单行控制在约 820 字符以内**：要在远端跑多行脚本时，本地先 base64 成单行、登上去再 `echo '<b64>' | base64 -d | bash`；超长就拆段。
3. **跳板会限流**：短时间高频连 `bgo ssh` 会触发 sshd `MaxAuthTries`（表现为 `too many authentication failures`）。被限流后**停止重试，等几分钟**让 sshd 计数重置；必要时用 `ssh-add -D` 或 `-o IdentitiesOnly=yes -o PreferredAuthentications=gssapi-with-mic` 减少每次尝试的 key 数。

### 5.2 宿主机上定位并进入容器

```bash
# 1) 带 pty 登宿主机
script -q /dev/null bgo ssh root@<ipv6>

# 2) 找容器：按模型名 / job id 过滤 crictl 列表，拿到 <container-id>
crictl ps | grep -F 'model_12345678'

# 3) 取容器 init 进程在宿主机 namespace 的 PID
crictl inspect -o go-template --template '{{.info.pid}}' <container-id>

# 4) nsenter 进容器的 mount/pid namespace（交互 shell）
nsenter -t <pid> -m -p -- bash -l

# 或一条命令执行后返回（自动化用，引号按 shell 规则转义）
nsenter -t <pid> -m -p -- bash -lc '<read-only cmd>'
```

### 5.3 日志 / 产物固定路径

pilot 容器：

- `/var/log/tiger/data.manhattan.log*`：serving 主日志，**`warmup model success` 才算真 ready**；
- `/var/log/tiger/lgtorch_launch.log`：启动日志；
- `/var/log/tiger/worker_<rank>_<n>.stderr`：各 worker stderr，recompile / guard fail 原因在这里；
- `/opt/tiger/inductor/`：预编译产物目录，`write_done` 是解包完成哨兵，`inductor.lock` 是解包锁。

snapshot 容器：

- Go 侧日志 + 容器内 workspace：每模型编译产物日志在 `tmp_ws_*` 一类目录下，按 job 对应模型目录再找；
- `workspace/dump_log_backup/<n>/` 下四个关键阶段日志：
  - `load_distcp_serving.log`：拉取分布式产物（snapshot 输入侧）；
  - `torch_dense_convert.log`：dense 部分转换；
  - `aot_compile_part_0.log`：AOT 编译；
  - `aot_warmup.log`：编译后 warmup。

原生进程崩溃（segfault 等）看**宿主机 `dmesg`**：容器与宿主共享内核，nsenter 进容器后 `dmesg` 常被禁用，宿主上才能看到内核级崩溃记录。

## 6. 往镜像与源码侧追：icm → SCM → 本地仓

容器内现象指向"镜像缺包 / 装错版本 / 代码不是预期 commit"时，沿构建链反向追。鉴权统一用 bytedcli 的 ByteCloud JWT（`bytedcli auth get-bytecloud-jwt-token`；JWT 站点随 Merlin origin 推断，`i18n-tt` 等 TikTok SSO 站点需先单独 `auth login`，见 [`invocation.md`](invocation.md)）。

1. **查镜像构建历史**：确认线上镜像每次构建装了哪些 SCM 包、哪个包缺失或版本不对（缺 optimizer、错算子版本通常在这一层暴露）。

   ```bash
   bytedcli --json icm version list --namespace <image-namespace> --name <image-name> \
     --page 1 --page-size 20
   # 可按版本 / 状态过滤：--version <v>、--status ok|fail|building|dropped|timeout
   bytedcli icm version get --image-name hub.<registry>/<ns>/<name>:<tag>
   ```

   镜像名 / namespace 从部署配置或容器信息里取；`icm version get` 的合并详情带构建 commit 等字段。

2. **SCM 版本 → 源码 commit**：拿到镜像里 SCM 包的确切版本号后，解析它 pin 的 40 位 commit（以 build manifest 为准，不受 force-push / 合并时间漂移影响）：

   ```bash
   bytedcli --json scm repo version get "<scm-repo-path>" --version <scm-version>
   bytedcli scm repo version compare --repo-id <repo-id> --base <v1> --target <v2>
   bytedcli scm repo diagnose --repo "<scm-repo-path>" --version <scm-version>
   ```

   `version get` 返回 `commit_hash`（该 SCM 构建对应的精确源码提交）；`version compare` 给两个版本间的精确 commit 区间；构建本身有问题用 `diagnose` / `build-log`。无论从哪个入口拿到 SCM 版本记录，关键是落到 build manifest pin 的 commit SHA，而不是只看版本号。

3. **本地仓比对**：在对应源码本地仓内，用 commit SHA 做精确比对，不要凭版本号猜：

   ```bash
   git cat-file -t <commit-hash>          # 确认本地仓有这个对象
   git merge-base --is-ancestor <commit-hash> <branch> && echo in-branch
   git show <commit-hash>:<path/to/file>  # 看该提交里的文件内容
   git diff <commit-hash>..<another> -- <path>
   ```

   常见结论：线上 SCM 版本对应的 commit 不含某个修复 / 仍带某个 bug → 结论是"需要发新版镜像"，而不是运行时调参能解决。

## 7. 分层排查顺序（checklist）

按数据链路从上游往下游逐层剥，每一层有明确的"看哪里 / 什么算过"，确认一层再进下一层：

> tiktok-row RoW 集群没有下面第 3~8 步使用的 orthrus / bgo 通道，进容器改走第 4 节的 GPCP SDP（命令约束、日志布局差异见该节）；健康判据与本 checklist 相同。

1. **坐标**：链接 / PSM → job id、biz、机型、runtime、deploy 发布单（第 1 节）。
2. **控制面状态**：`serving get` 拿两个 PSM、各 deploy 的 ready 与实例 host / idc；区分"没实例（停服）"与"实例在但不健康"。
3. **snapshot 是否产出**：进 snapshot 容器看 `load_distcp_serving`（拉产物）→ `torch_dense_convert`（转换）→ `aot_compile_part_0`（编译）→ `aot_warmup`（warmup）四段日志，定位卡在哪一阶段。
4. **产物是否上传**：snapshot 产物应落到远端对象存储（TOS）；snapshot 容器内"成功"但产物没上传，pilot 侧一定拉不到——这是最容易被 k8s ready 掩盖的断链。
5. **coordinator 是否派任务**：snapshot 产物在，但下游没被调度 / 没收到任务，去 prifly / serving service 状态侧看调度。
6. **pilot 是否被调度拉起**：有实例 host 才谈得上 inspect；没实例回到第 2 步看发布单。
7. **pilot 加载 / warmup**：`data.manhattan.log` 的 `warmup model success`、`worker_*.stderr` 有无报错或 recompile、`/opt/tiger/inductor/write_done` 是否在。
8. **endpoints / 端到端前向**：warmup 过后确认 endpoints 注册并对实例发一次真实前向；prifly 监控页看流量与错误。
9. **镜像 / 源码根因**：链路都通但行为不对（缺包、错版本、修复不在）→ 第 6 节 icm / SCM / 本地仓。

### slow vs crash-loop 定性

在第 3、7 步观察期先做这个判断：

- **慢 / 正常重试**：worker PID 稳定不换，日志在推进（阶段在往前走），错误是瞬时且每次位置不同 → 等 + 看资源 / 排队，不要反复重启或重复授权连机。
- **确定性 crash-loop**：worker 进程反复换 PID（被 archon 反复拉起），每次堆栈停在**同一处**、同一错误 → 代码 / 镜像 / 数据确定性问题，直接进对应层日志（snapshot 四阶段或 pilot worker stderr）定位，必要时宿主 `dmesg` 看原生崩溃，再走第 6 节追构建侧，不要当性能问题等。

## 8. 健康判据速查

| 层面         | 表面信号（不可信）                         | 真判据                                                                              |
| ------------ | ------------------------------------------ | ----------------------------------------------------------------------------------- |
| k8s / deploy | `readyReplicas = replicas`，无 unavailable | 仅代表探针通过、进程在                                                              |
| snapshot     | deploy 状态正常、容器 running              | 四阶段日志全过且产物已生成并上传到 TOS                                              |
| pilot        | 容器 running、endpoints 已注册             | `write_done` 在 + `data.manhattan.log` 有 `warmup model success` + recompile 计数 0 |
| 端到端       | 监控页有实例                               | endpoints 真实前向成功，prifly 无持续错误                                           |
| 镜像 / 代码  | 镜像 tag 是"最新"                          | icm 构建记录含预期 SCM 版本，SCM `commit_hash` 含预期修复                           |
