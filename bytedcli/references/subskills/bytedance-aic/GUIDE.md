---
name: bytedance-aic
description: "Operate AIC 安卓云 via bytedcli: clusters, Android/Windows/Linux/Mac emulators, virtual phones, devboxes, cloud disks, images, Ceph bindings, permissions, stock, monitoring, logs, connection URLs, and QGA execution. Use for AIC or 安卓云 API tasks; Dora cloud-device reservations use bytedance-dora."
---

# AIC 安卓云

使用 `bytedcli aic` 管理安卓云资源；`--site cn|i18n|i18n-bd|boe` 选择控制面。所有命令使用显式 option；命令组不带子命令时显示帮助。

## Authentication

支持 CN、i18n、i18n-bd（SG）和 BOE；`--site` 选择 API origin 及匹配的 JWT 认证分区。i18n 使用 i18n-tt 认证，i18n-bd 使用 i18n-bd 认证；BOE 与前端一致复用 CN 认证。Swagger 未声明认证的集群列表、权限申请 URL、集群/全局健康检查、IDC、配置字典和 QGA 脚本列表直接匿名查询；其余接口支持以下认证方式：

显式全局 `--bytecloud-user-jwt-file` 优先使用本次调用的个人 JWT，按下表绑定认证分区；不读取其他身份的凭据。未传入时按以下顺序：

1. `aic --access-key <key> --secret-key <key>`；也支持 `BYTEDCLI_AIC_ACCESS_KEY` / `BYTEDCLI_AIC_SECRET_KEY`。两者必须配套，使用集群 AK/SK Basic Auth。
2. 对应认证分区的 `BYTEDCLI_SERVICE_ACCOUNT_JWT_CN` / `BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_TT` / `BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_BD`，或 `BYTEDCLI_SERVICE_ACCOUNT_JWT`，通过 `X-Jwt-Token` 发送服务账号 JWT。
3. bytedcli 共享 ByteCloud JWT 认证（包括显式 JWT override 与已登录身份）。按下表的 JWT 认证分区登录：CN / BOE 使用 `bytedcli --site cn auth login`，i18n 使用 `bytedcli --site i18n-tt auth login`，SG 使用 `bytedcli --site i18n-bd auth login`。查询时仍使用表中的 AIC `--site`。

不要把真实凭据写入 skill、示例或请求体文件。Basic Auth 与 JWT 不混用；401/403 时检查集群权限和服务账号绑定。

## Sites and capabilities

| 入口 | API base URL | JWT 认证分区 |
| --- | --- | --- |
| `--site cn` | `https://aic-api.byted.org` | CN |
| `--site i18n` | `https://aic-api-i18n.byted.org` | i18n-tt |
| `--site i18n-bd` | `https://aic-api-i18n-bd.byted.org` | i18n-bd（SG） |
| `--site boe` | `https://aic-api-boe.byted.org` | CN |

SG Swagger 未提供 QGA 执行、QGA 脚本列表、公共镜像列表和模拟器重置；SG 请求及预览会在认证前以 `AIC_CAPABILITY_UNSUPPORTED` 拒绝。这些路径在 CN 与 BOE 的 Swagger 中存在。

SG `emulator execute` 默认异步；需要同步返回时，在请求体中加入 `"sync": true`。异步返回请读取 `task_id` / `task_status`，不能把任务已受理等同于指令已成功。

## Quick start

```bash
bytedcli --site cn aic cluster list
bytedcli --site cn aic cluster list --followed
bytedcli --site i18n aic cluster list
bytedcli --site boe aic cluster list
# SG：--site 同时选择 AIC API 与 ByteCloud 认证站点
bytedcli --site i18n-bd aic cluster get --cluster demo-cluster --json
bytedcli --site i18n-bd aic emulator list --cluster demo-cluster --page 1 --page-size 20 --json
bytedcli --site cn aic cluster get --cluster demo-cluster --json
bytedcli --site cn aic emulator list --cluster demo-cluster --page 1 --page-size 20 --json
bytedcli --site cn aic emulator get --cluster demo-cluster --emulator demo-emulator --json
bytedcli --site cn aic emulator status get --cluster demo-cluster --emulator demo-emulator
bytedcli --site cn aic info get --name emulator_type
bytedcli --site cn aic idc list --cluster demo-cluster
bytedcli --site cn aic devbox spec list --mode android
bytedcli --site cn aic disk list --cluster demo-cluster
bytedcli --site cn aic image list --cluster demo-cluster
bytedcli --site cn aic public-image list --cluster demo-cluster --type android
bytedcli --site cn aic cluster stock get --cluster demo-cluster --body '{"mode":"android","cpu":2,"memory":4,"disk":20}'
bytedcli --site cn aic emulator error-log get --cluster demo-cluster --emulator demo-emulator
bytedcli --site cn aic emulator qga-script list
```

## Writes

创建、更新、删除、执行指令、迁移、复制、重置、启停和权限修改默认仅生成请求预览，不请求认证或调用后端。加 `--yes` 提交；`--dry-run` 即使同时有 `--yes` 也只预览。库存查询是只读 POST，直接查询。

请求体使用 `--body` 或 `--body-file` 二选一；详细字段见 [JSON 请求体](references/bodies.md)。CLI 会校验 Swagger 声明的必填字段、类型与枚举。Windows/Linux/Mac 创建需要 `password` 和 `system_disk_size`；Android 创建需要 `amount`、`emulator_type`、`gpu` 和 `name`。

```bash
# 预览；emulator_type 与 gpu 请先用 info get 发现有效配置
bytedcli --site cn aic android create --cluster demo-cluster --body '{"amount":1,"name":"demo-emulator","emulator_type":"demo-type","gpu":"demo-gpu"}'
# 提交已检查的 JSON 文件
bytedcli --site cn aic android create --cluster demo-cluster --body-file ./demo-android.json --yes
bytedcli --site cn aic emulator power-on execute --cluster demo-cluster --emulator demo-emulator --yes
bytedcli --site cn aic emulator execute --cluster demo-cluster --emulator demo-emulator --body '{"command":"uname -a"}'
bytedcli --site cn aic emulator qga-script execute --cluster demo-cluster --emulator demo-emulator --body '{"script":"demo-script","params":{}}'
bytedcli --site cn aic disk delete --cluster demo-cluster --body '["demo-disk"]'
bytedcli --site cn aic image delete --cluster demo-cluster --body '["demo-image"]'
bytedcli --site cn aic permission member create --cluster demo-cluster --body '{"demo-role":["demo-user"]}'
```

`android create` 和 `emulator create` 分别对应 Android 专用与通用模拟器接口；`virtualphone create` 对应板卡模拟器。`image update` 接收完整镜像对象（包含 `spec` / `status`），`disk update` 接收云盘 spec；不要混用请求体。所有更新/详情路径中模拟器统一使用 `--emulator`，云盘/镜像使用 `--name`。

## Output and Agent Guidance

- 默认文本；`--json` 输出 bytedcli 标准 JSON envelope。后端 `code/msg/data` 信封已解包，成功码为 `200`。
- 列表数组规范为 `items`。分页接口返回 `page`、`page_size` 和真实后端 `total`（如果提供）；默认单页 20，无自动翻页。
- 文本与变更预览中的密码、密钥等字段脱敏；查询的 JSON 结果可含完整凭据，只在用户确实需要时消费，不复制到聊天或无关文件。
- 日志接口 `log get` 返回日志 URL，`error-log get` 返回 pod logs/events；不会自动下载 URL 内容。监控、webshell、VNC、RDP 返回连接信息，不启动浏览器或会话。
- `image task-log get` 支持查询任务日志和进度，不要求任务已成功；读取 `code` / `message` 判断任务状态。
- `AIC_INPUT_ERROR`：检查 selector 和 [请求体字段](references/bodies.md)。写入预览也会执行输入校验。
- `AIC_SITE_UNSUPPORTED`：使用 `--site cn|i18n|i18n-bd|boe`，不推测其他站点 host。
- `AIC_CAPABILITY_UNSUPPORTED`：所选控制面不支持该操作；SG 不支持 QGA、公共镜像列表与重置，保持 SG 资源使用 `--site i18n-bd`。
- `AIC_AUTH_INPUT_ERROR`：Basic Auth 两个 key 必须配套。
- `AIC_API_ERROR`：检查权限、资源名称和请求字段；写请求不会自动重试，失败后先查询资源状态。
- `AIC_RESPONSE_ERROR` / `AIC_NON_JSON_RESPONSE`：检查网络与登录状态，避免将 HTML 登录页面当作成功响应。
- 不接入已弃用 `batch_create`；Swagger 未描述更新参数的集群 `/update` 接口也未暴露。

## References

- [命令与接口映射](references/commands.md)
- [JSON 请求体](references/bodies.md)
