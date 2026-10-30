# PPE Debug / Watchpoint

## 适用范围与输入

使用 `bytedcli --site cn env watchpoint` 调试 CN PPE 环境。创建会话和断点会修改远端调试状态；所有写命令默认校验参数并预览实际 HTTP method/path/body/query，不鉴权或访问后端；明确授权后加 `--yes` 才执行，`--dry-run` 与 `--yes` 互斥。先确认用户已授权本次调试及目标服务、环境、Pod、代码位置。其他站点尚不支持。

准备目标 PSM、PPE 环境、集群、准确 Pod 名，以及 `file:line` 断点或 capture expression。环境标识必须是 `ppe` 或以 `ppe_` 开头。表达式使用调试平台支持的语法；动作固定为 CAPTURE。

## 调试流程

1. 用 ENV 查询目标环境中的服务与实例。多实例时明确目标 Pod，不能任取第一个。
2. 创建会话，保存返回的 `sessionId`。CLI 校验返回会话的 `created_at`（10 分钟内，允许服务端时钟领先本机不超过 60 秒）与 Pod；过期、缺少校验信息或不匹配时，关闭旧会话再重建一次。仍无效则关闭并报错；删除失败则直接报错，避免继续创建。
3. 批量创建断点，保存 `result` 中每个断点 ID。每个位置用一个 `--breakpoint` 值，或在同一个参数后连续提供多个值。
4. 让用户在目标 PPE 环境触发请求，约 3 秒后逐个查询断点。
5. 查询结果保留原始快照、变量、堆栈和状态字段。空记录或 pending 只表示当前查询没有快照，不能据此判断目标代码从未执行。可再次触发并手动重查。
6. 无论命中、无记录、查询报错或用户取消，结束本次调试时都要关闭会话。清理失败时保留 sessionId，明确告知并给出重试命令，不能宣称已清理。

```bash
# 发现实例；get 返回集群与 Pod 信息
bytedcli --site cn env service list --env ppe_demo --standard-env online_cn --service-types tce
bytedcli --site cn env service get --instance-id 123456 --standard-env online_cn

# 创建或复用有效会话；可选 --commit-id，--expired-at（未来 Unix 秒，上限 9999999999，拒绝毫秒值）
bytedcli --json --site cn env watchpoint session start \
  --psm example.service.api --env ppe_demo --cluster default --instance-name demo-pod --yes

# 使用新返回的 sessionId，多断点和表达式可同时提供
bytedcli --site cn --json env watchpoint create --session-id demo-session \
  --psm example.service.api --env ppe_demo --cluster default --instance-name demo-pod \
  --breakpoint handler.go:42 service.go:88 --expression request.id --yes

# 用户触发请求后，查询所有断点及每个断点快照
bytedcli --site cn --json env watchpoint list --session-id demo-session
bytedcli --site cn --json env watchpoint get --session-id demo-session --id demo-point-1
bytedcli --site cn --json env watchpoint get --session-id demo-session --id demo-point-2

# 可删除单个断点；调试结束后必须关闭会话
bytedcli --site cn env watchpoint delete --session-id demo-session --id demo-point-1 --yes
bytedcli --site cn env watchpoint session delete --session-id demo-session --yes
```

## 参数和结果

- `session start` 必填 `--psm --env --cluster --instance-name`，可选 `--commit-id --expired-at`（未来 Unix 秒，不超过 9999999999）。执行加 `--yes`，否则只预览。返回 `sessionId`、毫秒时间 `createdAt`、`instanceName` 与完整 `raw`。
- `create` 必填目标参数和 `--session-id`，至少提供 `--breakpoint` 或 `--expression`。返回 sessionId 与完整批量结果，不截断断点 ID。
- `list/get/delete` 必填 `--session-id`，`get/delete` 还必填 `--id`；可用 `--psm --env --cluster --instance-name` 增加筛选，Pod 在请求中映射为 `pod`。
- `session delete` 执行需 `--session-id --yes`，用它清理会话及其断点。
- `list` 额外返回 `items`、当前可识别集合的 `count`、后端 `total`、`page`、`page_size` 与 `has_more`；未知的集合/总数/分页/是否还有更多均为 `null`，不拿当前页条数冒充全量。
- 查询不轮询、不在客户端截断、不伪造分页总数；后端返回什么状态、分页或快照字段，均保留在 `result`。文本模式同样展示完整结果；全局 `--json` 输出一个标准 JSON envelope。
- ByteCloud CN JWT 由统一认证解析，不回显 token。Watchpoint 不接受 ENV 的 `--standard-env`；该参数仅用于前置 ENV 查询。
