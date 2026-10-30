# Goofy URL Structure

Goofy Web 控制台 URL 支持两种域名前缀：

- `cloud.*` 系列（如 `cloud.bytedance.net`）：路径带 `/goofy/` 前缀，例如 `https://cloud.bytedance.net/goofy/app/123`
- `deploy.bytedance.net`：路径不带 `/goofy/` 前缀，例如 `https://deploy.bytedance.net/app/123`

## URL → ID 映射

从 URL 提取 ID 的规则如下：

| URL 路径模式 | 提取的 ID | 对应 CLI 参数 |
| --- | --- | --- |
| `/app/<appId>` | `appId`（query `deployUnitId` → `regionId`） | `--app-id` / `--region-id` |
| `/channel/<channelId>` | `channelId` | `--channel-id` |
| `/channel/<channelId>/deploy?deploymentId=<id>` | `channelId` + `deployId` | `--channel-id` / `--deploy-id` |
| `/team/<teamId>` | `teamId` | `--team-id` |
| `/web/quick-preview/redeploy/<id>` | `previewId` | `--preview-id` |

## Host → site 映射

| Host                              | Site      |
| --------------------------------- | --------- |
| `cloud.bytedance.net`             | `cn`      |
| `deploy.bytedance.net`            | `cn`      |
| `cloud-boe.bytedance.net`         | `boe`     |
| `cloud.byteintl.net`              | `i18n-bd` |
| `cloud-boei18n.bytedance.net`     | `boe`     |
| `cloud.tiktok-row.net`            | `i18n-tt` |
| `cloud.tiktok-us.net`             | `us-ttp`  |
| `cloud-ttp-us.bytedance.net`      | `us-ttp`  |
| `cloud-eu.tiktok-row.net`         | `eu-ttp`  |

## 哪些命令接受 URL

`get-deployment`、`diagnose`、`cancel`、和 `retry` 接受直接粘贴部署页 URL，CLI 会从 URL 中解析出 `deployId` 并根据 host 推断 `site`，无需额外网络请求。

其余命令目前仍需传纯数字 ID，可按上表从 URL 中手动提取。

A bare numeric or alphanumeric string (no `/` or protocol) passed to deployment commands is treated directly as the deployment ID.
