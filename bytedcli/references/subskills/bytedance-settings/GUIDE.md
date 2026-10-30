---
name: bytedance-settings
description: Operate ByteDance Settings with bytedcli across item, draft, review, deploy, whitelist, UT, var, and biz workflows. Use for Settings configuration management, space discovery, or keyword-to-space-ID lookup.
---

# Settings (bytedcli)

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- 需要执行 Settings 全流程能力（配置、草稿、审核、发布、白名单、UT、变量、biz）
- 需要通过 `--from` / `--query-json` / `--body-json` 透传请求体或筛选条件
- 需要批量维护 `app_settings` 客户端配置流程

## 前置条件

- 按通用调用方式执行命令（含内网 registry）：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`

## 功能分组命令

> 说明：请求体/查询参数可通过 `--from`、`--query-json`、`--body-json` 原样透传；请按命令参数与 payload 字段约定构造 JSON。

```bash
# item / draft
bytedcli settings item get --item-id "123456"
bytedcli settings item list --id "<space-id>" --page 1 --page-size 50
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{\"type\":\"integer\"}" --reviewers-json "[]"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "1"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "abc"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{}"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{\"s\":\"abc\"}"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --scheme "{}"
bytedcli settings draft save --item-id "123456" --code "return true" --draft-type 1 --next-step 1

# review / deploy
bytedcli settings review list --item-id "123456"
bytedcli settings deploy list --item-id 123456 --page 1 --page-size 10

# whitelist
bytedcli settings whitelist add --item-id "123" --title "demo" --whitelist "u1" --whitelist "u2"
bytedcli settings whitelist save --whitelist-id 1001 --code-file "./sample-whitelist.py"
bytedcli settings whitelist save --whitelist-id 1001 --ignore-ab false
bytedcli settings whitelist save --whitelist-id 1001 --item-vars '[{"var_id":1,"name":"SAMPLE_VAR","value":"[\"sample\"]","var_type":3}]'
bytedcli settings whitelist list --item-id "123" --page-size 10 --page 1 --status 0 --type 0 --keyword ""
bytedcli settings whitelist biz-get --whitelist-id 1001

# ut / var / biz
bytedcli settings ut list --item-id 123456 --ut-status 0
bytedcli settings var list-item --item-id 123456
bytedcli --site cn --json settings biz search --keyword "sample-sdk-settings" --type sdk
bytedcli --site cn --json settings item search --id "<space-id>" --query "sample-config"
bytedcli settings biz search-id --appid "1001"
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json settings review list --item-id "123"`）
- `settings biz search` 返回候选集合；从 `.data.spaces` 读取结果，确认空间后再把 ID 传给 `settings item search`
- `settings biz search` 当前仅支持 CN；示例显式使用全局选项 `--site cn` 以锁定站点
- `--type` 只过滤上游本次返回的候选；空间名称不保证唯一，候选集合也不保证完整
- SDK 搜索无结果时不会回退到 AppID
- `settings item list` 的 `pagination.total` 可能包含已逻辑删除配置；按 `total` 翻完所有页，实际可见数以各页 `data` 按 `item_id` 聚合去重后为准
- 大多数 `settings` 子命令支持 `--from <path>` / `--query-json` / `--body-json` 组合透传
- `settings item create --schema/--scheme` 支持 schema JSON 或示例值自动推断类型（`1 -> integer`，`abc -> string`，`{} -> 宽松 object`，`{"s":"abc"} -> 严格 object schema`）
- `settings item apply` 作为兼容别名保留，推荐使用 `settings item create`
- 分页命令优先使用 `--page`（1-based）；`--page-no` 仅兼容旧用法

- `settings whitelist save` 先读取当前详情，将显式参数合并后再全量保存。除 `status` 按下述规则转换外，所有可选字段不传就保留现值，包括名称、白名单 ID、类型、AB 开关、过期时间、生效条件、变量、鸿蒙开关和 `extra`。`--code-file` 可选，不传就沿用当前代码。详情读取失败或结构不完整时停止保存，不会发送部分字段。
- save 的 `--status` 仅接受 `0`（启用）或 `1`（失效）。详情中的 `2` 是根据过期时间计算的状态，不可直接写入。省略 `--status` 时，详情 `0/1` 保持原值，详情 `2` 转为可写状态 `0`。未指定 `--expired-time` 时保留原过期时间，因此过期白名单仍会过期。将过期时间延长到未来可能恢复生效；若需保持失效，请显式指定 `--status 1`。
- `--whitelist` 指定本次完整名单，不传则保留；当前 CLI 暂不提供清空名单参数。
- `settings whitelist add/save --ignore-ab` 支持 `true`、`false`，兼容不带值的写法（表示 `true`）；save 不传时保留当前值。`--item-vars` 接收与 `whitelist_info.item_vars` 相同的 JSON 数组字符串，例如 `'[{"var_id":1,"name":"SAMPLE_VAR","value":"[\"sample\"]","var_type":3}]'`；传入 `'[]'` 表示清空变量。
- save 读取的 `whitelist_info.item_vars` 若为字符串 `"null"`（可含 JSON 空白），会先归一化为 `'[]'`，再合并并校验本次参数，因此省略 `--item-vars` 也能保存旧记录。回读摘要与差异比较将该字符串与 `[]` 视为同一个空变量表；未要求修改的非空变量表变为空表仍会警告。该兼容仅适用于详情中的字符串，空串、缺字段、实际 `null` 和无效 JSON 仍会报错；显式 `--item-vars` 仍须是 JSON 数组字符串，清空用 `'[]'`。
- 通过 MCP 命名参数调用 whitelist add/save 时，`ignoreAb` 使用字符串 `"true"` / `"false"`；原来传布尔值的调用方需要更新参数。
- save 成功后回读一次并对比保存前的 ID 数量、状态、过期时间和变量名。JSON 输出的 `verification.before/after` 包含这些摘要，`verification.diff` 记录所有实际字段变化及 `requested` 标记。显式修改，或修改过期时间引起且持久状态不变的 `0/2` 展示状态变化，标记为 `requested: true` 且不警告；意外变为失效态 `1` 仍会警告。其他未要求修改的字段发生变化时，文本输出 warning，JSON 的 `verification.warnings` 同时给出警告。回读失败返回 `SETTINGS_WHITELIST_VERIFY_FAILED`，表示已经执行保存；先用 `settings whitelist get --whitelist-id <id>` 核对结果。
- `settings review create`、`settings whitelist add` 未指定 `--support-harmony-os` 时读取配置 `latest_info.extra` 并保留鸿蒙开关。读取失败或缺少布尔值时停止提交，可用 `--support-harmony-os true|false` 显式指定。
- review 的 JSON 输入和 whitelist add 的 `--from` 支持 `support_harmony_os` 或 `extra.support_harmony_os`；显式 CLI 参数优先，顶层字段优先于 extra，最终请求中的两处值保持一致。
- whitelist add 会检查创建结果的鸿蒙开关；值不一致时，按新记录的内容和状态补充保存，再回读确认，成功输出最终详情。后续保存或回读失败会返回 `SETTINGS_WHITELIST_PARTIAL_WRITE` 和已创建的 `whitelist_id`；先用 whitelist get 核对，再保存该记录，避免重复执行 add。补充保存沿用后端代码校验，代码需要有有效返回值。

## References

- `references/settings.md`
- `../../invocation.md`
- `references/review-create.sample.json`
- `references/review-create-open.sample.json`
