# 删除单条灰度

`maat gray delete` 删除一个准确命名的灰度条目并发布配置；不是删除项目、构建产物、联调环境或回滚版本。先用 `bytedcli maat gray delete --help` 确认安装版本具备此命令，不能仅凭 Skill 文档推断已发布。

## 操作流程

1. 读取 `gray get`，确认准确项目、站点、发布区域和目标 `name`。CN 默认 CN；i18n 必须显式传准确 `--region`。用户只给请求头值、模糊前缀或描述时先定位并澄清，不把它当作名称直接删除。
2. 运行 `gray delete --project <project> --name <name>`，不带 `--yes`。预览包括 `operation: delete`、目标的 `before`（ID、名称、版本、流量、条件）、`after: null`、完整 `order.before/order.after`、剩余配置和冻结信息，不申请 ID、不发送写请求。
3. 向用户说明将移除哪个条目，匹配流量可能转向其他灰度或项目默认版本；删除最后一条时列表将为空。将目标和风险合并在同一次提示中，展示预览后单独等待一次明确上线确认，最初的“删除它”不代替二次确认。
4. 用户确认当前唯一删除预览后，直接使用相同站点、区域、项目、名称及预览指纹，加 `--yes --confirm-plan <fingerprint>` 提交，不再问“是否确认删除”。旧 deploy 指纹不能用于 delete；目标、身份、项目、冻结或远端配置变化时说明差异、重新预览并确认，不自动接受新指纹。
5. 回读验证整个配置：目标已不存在，剩余条目的完整字段及顺序仍匹配。`verified` 只证明配置一致，不证明在线流量去向；`verified_after_error` 表示写响应报错但回读匹配，不能归因于本次写入。`MAAT_DEPLOY_UNKNOWN` 时停止并只读核查，不能再次提交来试探结果。

```bash
bytedcli --site cn --json maat gray get --project demo-web
bytedcli --site cn --json maat gray delete --project demo-web --name demo-gray
# 单独确认该次预览后
bytedcli --site cn --json maat gray delete --project demo-web --name demo-gray --yes --confirm-plan <fingerprint>
```

## 边界

- 目标必须唯一存在；不存在或重复时报错，不猜测，也不将未知结果伪装为删除成功。已删除后重放旧确认不会再写入。
- 保留所有非目标条目的字段、相对顺序及项目级配置。底层仍是整份灰度配置替换；提交前快照重查不是服务端原子 CAS，避免与其他人并发编辑。
- 复用已有发布的项目类型、单 SCM、区域、渲染链、账号、锁定和冻结检查。删除不查询旧构建是否仍在版本列表，也不分配新 ID。
- 不支持 `--all`、通配符匹配、批量删除，也不接收版本、流量、条件或排序修改参数；`gray deploy --mode delete` 不是删除入口。
- 不支持删除构建、项目或联调环境。不绕过权限、封禁或未知渲染链限制，不改用手写 API 兜底。
