# ByteDog Authentication

ByteDog commands use ByteCloud authentication for the target `--site`.

Use the site specified by the user. If none was specified, select it from a ByteDog URL, host IP, or PSM as described below. Resolve failed, empty, or ambiguous lookups before continuing; do not assume `cn`.

## Host IP to auth site

Check [authentication](#authentication-sequence) for `cn`, then look up the host IP's site. `--ip` accepts IPv4 or IPv6.

```bash
bytedcli --json bytedog tool ip-site get --ip 192.0.2.10
```

Use `data.site` as `--site` for subsequent ByteDog commands and check that site's authentication.

## PSM to auth site

If only a PSM is available, check [authentication](#authentication-sequence) for the current `--site` (`cn` by default), then query its available partitions:

```bash
bytedcli --json tce env-cascader --psm example.service.api
```

Map `data.data[].partition` (the text-mode `Partition` column) to `--site` values and deduplicate them. Omit `--partition` and `--excluded-partitions` to include all candidates.

| Partition label (case-insensitive) | `bytedcli --site` |
| --------------------------------- | ---------------- |
| `CN`                              | `cn`             |
| `BOE`                             | `boe`            |
| `I18N`, `i18n-tt`                  | `i18n-tt`        |
| `I18NBD`, `i18n-bd`                | `i18n-bd`        |
| `USTTP`, `us-ttp`                  | `us-ttp`         |
| `EUTTP`, `eu-ttp`                  | `eu-ttp`         |

Use the site if there is one candidate. If there are several, narrow them using deployment context; ask the user if still ambiguous. For unrecognized partition labels, confirm the site before continuing. After selecting the target site, check its [authentication](#authentication-sequence).

## URL host to auth site

When the user provides a ByteDog page or console URL, choose the `bytedcli --site` value from the URL host.

| ByteDog URL host                | `bytedcli --site` | SSO/auth area            | Auth check                                   | Login command                        |
| ------------------------------- | ----------------- | ------------------------ | -------------------------------------------- | ------------------------------------ |
| `bytedog.bytedance.net`         | `cn`              | ByteDance SSO / CN       | `bytedcli --site cn --json auth status`      | `bytedcli --site cn auth login`      |
| `bytedog-sinf.bytedance.net`    | `sinf-cn`         | ByteDance SSO / CN       | `bytedcli --site sinf-cn --json auth status` | `bytedcli --site sinf-cn auth login` |
| `bytedog-boe.bytedance.net`     | `boe`             | BOE test SSO             | `bytedcli --site boe --json auth status`     | `bytedcli --site boe auth login`     |
| `bytedog.byteintl.net`          | `i18n-bd`         | ByteDance SSO / ByteIntl | `bytedcli --site i18n-bd --json auth status` | `bytedcli --site i18n-bd auth login` |
| `bytedog-i18n.bytedance.net`    | `i18n-tt`         | TikTok SSO / ROW         | `bytedcli --site i18n-tt --json auth status` | `bytedcli --site i18n-tt auth login` |
| `bytedog-ttp-us.tiktok-row.net` | `us-ttp`          | TikTok SSO / US TTP      | `bytedcli --site us-ttp --json auth status`  | `bytedcli --site us-ttp auth login`  |
| `bytedog-ttp-eu.tiktok-row.net` | `eu-ttp`          | TikTok SSO / EU TTP      | `bytedcli --site eu-ttp --json auth status`  | `bytedcli --site eu-ttp auth login`  |

## Authentication sequence

For the selected `--site`, check authentication before logging in:

```bash
bytedcli --site <site> --json auth status
```

Use `data.authenticated` to decide whether the ByteCloud JWT path is available for ByteDog:

- `data.authenticated=true`: run the requested ByteDog command. Do not log in again merely because `data.bytecloud_auth.status` is `need_login`; ENV JWT, JWT override, or session JWT may be the active source.
- `data.authenticated=false`: start ByteCloud Auth login for that same site, complete it, then run the requested ByteDog command.

```bash
# Human / blocking
bytedcli --site <site> auth login

# Agent / non-blocking, only after data.authenticated=false
bytedcli --site <site> --json auth login --begin
bytedcli --site <site> --json auth login --complete <token>
```

Keep the selected target site even if another site is already authenticated.

## Network profile

ByteDance 生产网络设置 `BYTEDCLI_NETWORK_PROFILE=prod`，办公网络保持该变量未设置。该值区分大小写，不使用 `PROD`；出现连接错误时先确认网络配置，避免反复切换环境。
