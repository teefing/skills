# Mock 配置管理

## Use Cases

查询、创建、更新或删除 FTF Mock 配置时使用。命令入口为 `bytedcli ftf mock-config`，通过 TeslaX v1 OpenAPI 调用现有 Manager CRUD。

Mock 未命中或回放异常先按 [diag-mock.md](diag-mock.md) 收集证据；诊断请求本身不授权修改配置。本流程不提供 apply、版本管理、发布状态或回放执行。

## Inputs

- 明确目标 site，沿用入口 Skill 的全局参数规则；ID 不能用于推断区域。
- 列表必须提供 `space_id`，可按配置 ID、PSM、名称子串和泳道筛选，分页逐页读取。详情以配置 ID 定位。
- 创建 JSON 包含正整数 `space_id`、非空 `psm`、`name` 和对象 `mock_items`；可提供字符串 `lane` 和 `create_user`。
- 更新 JSON 包含正整数 `mock_id`、非空 `psm`、`name`、字符串 `lane` 和对象 `mock_items`；可提供 `update_user`。
- 缺省审计用户来自 bytedcli 登录身份；文件中的显式用户优先。删除可用 `--update-user` 指定。

`mock_items` 按现有后端协议填写，CLI 原样传递其嵌套内容。不要依据名称猜测协议字段，也不要把查询列表当作完整更新请求；列表不含完整 Mock 规则。

## Workflow

1. 用明确区域和已有筛选条件查询，再按 ID 获取详情：

   ```bash
   bytedcli --site cn --json ftf mock-config list --space-id 123 --psm example.psm --page 1 --page-size 20
   bytedcli --site cn --json ftf mock-config get --id 456
   ```

   列表记录位于 `.data.mock_configs`，保留后端 `total`、`page`、`page_size`。详情位于 `.data`，原始 Nova 响应保留在 `.context.backend`。

2. 创建或更新前，准备完整请求 JSON，核对目标、泳道和每条 Mock 规则。更新先读详情，保留所需旧值；从 `.data.id` 显式填写 `mock_id`，审计字段按本次操作填写。创建的最小空规则示例：

   ```json
   {
     "space_id": 123,
     "psm": "example.psm",
     "name": "demo mock",
     "lane": "demo_lane",
     "mock_items": {}
   }
   ```

   空对象代表空规则配置；只有明确要清空规则时才提交。JSON 文件可原样包含后端支持的嵌套规则字段。

3. 用户已明确授权本次目标和内容后，执行对应写命令：

   ```bash
   bytedcli --site cn --json ftf mock-config create --request-json /tmp/mock-create.json --yes
   bytedcli --site cn --json ftf mock-config update --request-json /tmp/mock-update.json --yes
   bytedcli --site cn --json ftf mock-config delete --id 456 --yes
   ```

4. 创建成功回执 `.data` 是配置 ID，用该 ID 获取详情；更新后回读同一 ID，核对名称、PSM、泳道和规则；删除后用原筛选查询，确认配置从列表消失。更新/删除成功回执可能是 `null`，不能单凭该回执认定目标记录确实发生变化。
5. 写入超时或结果不明确时，停止后续写入，按原区域和选择条件回读。更新或删除报错也要先回读：现有后端可能已完成数据库写入，随后在清理缓存时失败。创建不能盲目重试；仅在确认未创建且仍获授权后决定下一步。

## Write Constraints

- 创建、更新、删除均要求 `--yes`；CLI 不自动重试写请求，也没有 dry-run、CAS、回滚或额外 apply 操作。
- 更新覆盖名称、PSM、泳道和整份规则，不是局部 patch。CLI 要求完整更新字段，以避免遗漏规则或泳道。
- 空或缺省泳道在现有后端会生成内部随机泳道，查询时显示为空；若要保留已绑定泳道，必须提交原值。
- 泳道关联配置会影响该 PSM/泳道的 Mock 使用；不能承诺此次写入只影响一个指定回放任务，也不能从保存成功推断正在运行的实例已刷新。
- `enable` 虽出现在现有更新 DTO 中，当前服务不使用该字段；不要把它当作启停能力。
- 删除采用现有软删除行为；不存在的 ID 也可能返回成功。确认效果必须依赖回读。
- 不额外调用未封装的配置生效、调试或回放接口，不绕过平台权限。

## Results

成功时报告区域、操作、配置 ID、PSM/泳道及回读结论。查询结果保留完整后端业务数据；文本只展示必要字段，完整规则使用 JSON 获取。

权限失败或输入不完整时停止依赖该条件的操作，给出具体缺项或后端错误。写入结果不明确或回读未确认时，报告“结果待确认”和实际回读证据，不能声称保存、删除或运行时生效已完成。
