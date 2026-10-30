# Settings

```bash
bytedcli settings item get --item-id "123456"
bytedcli settings item list --id "<space-id>" --page 1 --page-size 50
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{\"type\":\"integer\"}" --reviewers-json "[]"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "1"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "abc"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{}"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{\"s\":\"abc\"}"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --scheme "{}"
bytedcli settings draft save --item-id "123456" --code "return true" --draft-type 1 --next-step 1
bytedcli settings review list --item-id "123456"
bytedcli settings deploy list --item-id 123456 --page 1 --page-size 10
bytedcli settings whitelist add --item-id "123" --title "demo" --whitelist "u1"
bytedcli settings whitelist save --whitelist-id 1001 --code-file "./sample-whitelist.py"
bytedcli settings whitelist save --whitelist-id 1001 --ignore-ab false
bytedcli settings whitelist save --whitelist-id 1001 --item-vars '[{"var_id":1,"name":"SAMPLE_VAR","value":"[\"sample\"]","var_type":3}]'
bytedcli settings whitelist list --item-id "123" --page-size 10 --page 1 --status 0 --type 0 --keyword ""
bytedcli settings whitelist biz-get --whitelist-id 1001
bytedcli settings ut list --item-id 123456 --ut-status 0
bytedcli settings var list-item --item-id 123456
bytedcli --site cn --json settings biz search --keyword "sample-sdk-settings" --type sdk
bytedcli --site cn --json settings item search --id "<space-id>" --query "sample-config"
bytedcli settings biz search-id --appid "1001"
```

`settings biz search` 返回候选集合。通过 `.data.spaces` 读取结果，确认空间后再把 ID 传给
`settings item search`。该命令当前仅支持 CN；示例显式使用全局选项 `--site cn` 以锁定站点。
`--type` 只过滤上游本次返回的候选；空间名称不保证唯一，结果也不保证完整。SDK 搜索无结果时
不会回退到 AppID。

`settings item list` 的 `pagination.total` 可能包含已逻辑删除的历史配置，`data` 只返回当前
可见配置。枚举时仍按 `total / page_size` 翻完所有页，不能因某页少于 `page_size` 提前停止；
实际可见数量以各页 `data` 按 `item_id` 聚合去重后的结果为准。

`settings whitelist save` 采用读取、合并、全量保存的流程。除 `status` 按下述规则转换外，所有可选字段不传就保留当前值，
`--code-file` 也可以省略。详情读取失败或结构不完整时停止保存。`--ignore-ab true|false`
支持显式开关；旧写法 `--ignore-ab` 等同于 `true`，add 命令同样支持。
MCP 命名参数 `ignoreAb` 使用字符串 `"true"` / `"false"`，原布尔值参数需要迁移。
`--item-vars` 是与 `whitelist_info.item_vars` 相同的 JSON 数组字符串，传入 `'[]'` 会清空变量。
save 读取到字符串 `"null"`（可含 JSON 空白）时，先归一化为 `'[]'`，再合并并校验本次参数；省略 `--item-vars` 也能保存旧记录。
回读摘要与差异比较将该字符串与 `[]` 视为同一个空变量表；未要求修改的非空变量表变为空表仍会警告。
此兼容仅适用于详情中的字符串，空串、缺字段、实际 `null` 和无效 JSON 仍会报错；显式 `--item-vars` 仍须是 JSON 数组字符串。

save 的 `--status` 仅接受 `0`（启用）或 `1`（失效）。详情中的 `2` 是根据过期时间计算的状态，不可直接写入。
省略 `--status` 时，详情 `0/1` 保持原值，详情 `2` 转为可写状态 `0`。
未指定 `--expired-time` 时保留原过期时间，因此过期白名单仍会过期。
将过期时间延长到未来可能恢复生效；若需保持失效，请显式指定 `--status 1`。
`--whitelist` 指定本次完整名单，不传则保留；当前 CLI 暂不提供清空名单参数。

保存后回读并核对 ID 数量、状态、过期时间和变量名。`verification.before/after` 返回摘要，
`verification.diff` 返回字段变化及 `requested` 标记。显式修改，或修改过期时间引起且持久状态不变的 `0/2` 展示状态变化，标记为 `requested: true` 且不警告；意外变为失效态 `1` 仍会警告。
其他未要求修改的字段发生变化时输出 warning，
JSON 同时带有 `verification.warnings`。回读失败的 `SETTINGS_WHITELIST_VERIFY_FAILED`
表示保存已经执行，应先用 `settings whitelist get` 核对结果。
