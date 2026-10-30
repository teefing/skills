# 完整灰度条件编辑

`maat gray deploy --conditions-file <path>` 支持新增或修改目标灰度的完整条件树。仍为预览优先，确认后才上线；不增加原始请求透传或绕过权限的入口。先用 `bytedcli maat gray deploy --help` 核对安装版本是否包含该参数，不能仅凭 skill 文档推断已发布。

## 读取、编辑、确认

1. 用 `gray get` 读取配置，在 `versions` 中按 `name` 精确定位目标，取它的 `rootCondition` 到 JSON 文件。文件只包含该对象，不包含 `versions`、`flow`、项目、版本或整个响应。不要把未检查的查询输出直接提交。
2. 在本地编辑树：支持增加、删除、修改表达式或分组，以及切换 AND/OR。输入是**整树替换**，不是自动合并。仅增加用户名时，找到准确的 `source: inner`、`key: username` 节点，保留已有成员及其他节点后再增加；多个匹配节点或账号不确定时先澄清。不能用 `--header` 替代用户名条件。
3. 用 `--conditions-file` 生成预览，展示 before/after 完整树、版本、流量与影响范围；同一目标的版本、流量、条件和排序修改放入同一命令，等待一次上线确认，不分字段重复询问。省略 `--version`、`--flow` 则保持原值；未指定 `--before/--after` 时保留原位置，其他灰度的内容及相对顺序保留。`no_op` 无需上线确认。
4. 使用同一文件、相同参数加 `--yes --confirm-plan <fingerprint>`。每次调用重新读取文件，内容变化会改变预览指纹；远端配置、身份或冻结信息变化也会拒绝旧确认。发生 `MAAT_PLAN_STALE` 时重新预览并确认，不自动重试写入。
5. `verified` 仅代表整份配置回读一致，不代表访问流量已命中。结果未知时停止，不重复提交。

```bash
bytedcli --site cn --json maat gray get --project demo-web
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode update --conditions-file ./conditions.json
# 用户已审阅并二次确认相同预览后
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode update --conditions-file ./conditions.json --yes --confirm-plan <fingerprint>
# 新增仍要求准确版本和流量；新根 UUID 留空由系统分配
bytedcli --site i18n --json maat gray deploy --project demo-web --region Singapore-Central --name demo-new --mode create --version 1.0.0.42 --flow 0 --conditions-file ./conditions.json
```

## 灰度顺序

`--before <name>` 表示紧邻指定灰度之前，`--after <name>` 表示紧邻其之后，均按 `gray get` 的准确名称匹配，不接受版本号、环境条件值或模糊前缀。适用于 create 和 update，可与条件、版本和流量修改组合，也可只移动已有灰度。

- 不传位置参数：新建追加末尾，修改保持原位置，不改变旧行为。
- 同时提供两者：先从列表移除目标，再验证 `after` 参照项紧邻 `before` 参照项且在它之前，在二者之间插入。若反向、不相邻、同名、缺失或参照自身，报错且不写入；不猜测一个区间里的位置。只有一个参照时可直接选定准确位置。
- 只移动目标，其他条目的完整配置及相对顺序不变，不修改 `flowMode`。Priority 模式下顺序可能改变路由优先级，不能承诺业务流量不受影响。
- 预览展示完整的 `order.before` / `order.after` 名称列表。位置参数、远端顺序及完整配置均绑定确认指纹；任何变化须重新预览和确认。位置已经满足且配置未改变时为 `no_op`，不发送写请求。
- 新建条目的真实 ID 仍在确认后分配，按目标名称定位并同时绑定根条件 UUID，与插入位置无关。回读校验包括完整列表顺序，不把接口受理当成实际流量命中。

例如已有 `demo-first`、`demo-last` 两个相邻灰度，新建用户名条件灰度并放在二者之间：

```bash
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-new --mode create --version 1.0.0.42 --flow 100 --conditions-file ./conditions.json --after demo-first --before demo-last
# 只移动已有灰度；版本、流量和条件保留
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode update --before demo-last
```

上述命令只预览；单独获得该次完整预览的上线确认后，直接以相同参数加 `--yes --confirm-plan <fingerprint>` 提交，不再追加条件或排序的确认。不使用位置参数绕过冻结、账号或项目发布限制。

## JSON 结构

根必须为 `sub-conditions` 分组，`join` 为 `AND` 或 `OR`，`conditions` 为有序节点数组。子节点可以是表达式或分组。根以外的分组不能是空数组；空根数组表示清空条件，100% 流量时可能影响全部用户。

表达式字段：

| 字段 | 契约 |
| --- | --- |
| `type` | `expression` |
| `source` | `header`、`cookie`、`query`、`inner` |
| `key` | header/cookie/query 的准确参数名；inner 仅支持 `username`、`larkchat`、`pathname`、`volUserid` |
| `option` | `Equals`、`NotEquals`、`Includes`、`NotIncludes`、`StartsWith`、`EndsWith`、`In`、`NotIn`、`RegExp` |
| `value` | In/NotIn 为非空字符串数组，其他操作符为非空字符串；不自动转换数字、布尔或逗号分隔文本 |
| `dataType` | 可省略，默认为 `string`；控制台当前编辑器只创建 string 类型 |
| `name` | 可省略，自动生成 `source.key`；提供时必须一致 |
| `uuid` | 可省略，自动生成稳定节点标识；从查询结果编辑时建议保留，整棵树内必须唯一 |

`inner.larkchat` 只支持 `In`，值是准确群 ID 列表；不猜测或自动创建群。`inner.username` 使用准确账号而非中文姓名，不自动去掉账号后缀。`RegExp` 按字符串原样交给 Maat，不在 CLI 中执行，也不承诺不同正则引擎的语义。

根 UUID 在修改时若提供，必须等于目标灰度 ID；新增时必须省略，确认后由服务端分配并绑定。UUID 只是节点标识，不是权限或版本字段。请求头、Cookie、Query 键大小写和值原样保留，不自动排序或去重列表。

如下示例表示“指定用户，或同时匹配环境头与路径”。它不是可直接覆盖任意现有树的模板；实际修改须以目标当前树为基础。

```json
{
  "type": "sub-conditions",
  "join": "OR",
  "conditions": [
    {
      "type": "expression",
      "source": "inner",
      "key": "username",
      "option": "In",
      "value": ["demo-alice", "demo-bob", "demo-carol"]
    },
    {
      "type": "sub-conditions",
      "join": "AND",
      "conditions": [
        {
          "type": "expression",
          "source": "header",
          "key": "x-demo-env",
          "option": "Equals",
          "value": "demo-ppe"
        },
        {
          "type": "expression",
          "source": "inner",
          "key": "pathname",
          "option": "StartsWith",
          "value": "/demo/"
        }
      ]
    }
  ]
}
```

## 校验与边界

- 只接受普通 JSON 文件，最大 256 KiB；最多 1000 个节点（含根），根以下最多三层，与控制台编辑器一致。单值最大 16384 字符，列表最多 1000 项。
- 文件与 `--header`、`--clear-conditions` 互斥。省略三者会原样保留已有树，不限制历史配置中的未知字段。
- 新输入严格校验字段，不允许整份灰度对象、拼错字段或未知操作符被静默丢弃。只覆盖上表所列控制台契约，不提供任意服务器字段透传。
- 不允许凭据类条件键（如 authorization、cookie、password、secret、token）或 `[REDACTED]` 占位值。Cookie 来源可用于普通业务 Cookie，但不是导入登录 Cookie 的入口。查询中的敏感值会脱敏，不能把脱敏输出当作真实值重新提交。
- 仍受项目、区域、Maat 渲染链、冻结和账号权限限制。不支持的渲染链不会因为提供条件 JSON 而变为可发布。
