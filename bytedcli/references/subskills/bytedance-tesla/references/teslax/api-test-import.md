# 保存 API Test 用例到 TeslaX

将用户明确选择的 Flux API Test 或 Repo 归档 YAML 保存为 TeslaX Case。
转换与创建由原生 `bytedcli tesla case import-api-test` 完成；不执行测试、
不持续同步、不承诺跨次去重。保存认证使用 ByteCloud JWT。

## 绑定本批来源

1. 从用户指向的生成产物或归档路径确定本批文件，不从当前目录猜测。
2. 不按 PASS/FAIL 筛选，运行失败的负向用例也可保存。
3. 分散文件重复 `--input`；专用目录输入不递归，不扫描整个 Repo。
4. 零文件时说明原因，不展示目标表单、不调用创建。
5. 记录本批文件集合与保存站点，等待期间保持同次调用关联；
   换批后重新绑定。历史或分享展示不能发起新保存。

## 目标选择

优先直接向用户询问目标 Space、Folder 与 Case 分支：ID 为正 int64，
`folderId` 不能是 0 虚拟根；Case 分支独立于 IDL 分支。

若宿主确实提供已核实的 TeslaX 目标选择组件，可以只用它收集同一组字段。
组件回传只是目标输入，不构成保存授权，也不代表 Case 已创建。
组件版本、字段映射或宿主调用方式未核实、工具不存在、加载失败、
取消或超时时，回到直接询问用户；不猜版本，不编造组件或映射字段。
保存前仍需用户对本批文件与目标作出明确确认；`--yes` 只能在用户
已明确同意本批保存后使用。

## CLI 保存

先检查安装版本的 `bytedcli tesla case import-api-test --help`。
支持 API Test 3.8.12 运行态 `defaults/api_list/scenario_ref/call_chain`
和归档 `description/api/test_target/request/expected`。
每文件一个 Case、一个请求 Step。

```bash
bytedcli --site cn --json tesla case import-api-test \
  --input ./confirmed-batch/a_case.yaml --input ./confirmed-batch/b_case.yaml \
  --space-id 123 --folder-id 789 --branch master --dry-run
```

`--dry-run` 仅本地预检，与 `--yes` 互斥；不验证远端目录、权限或
IDL 可用，不称“已保存”。全批先预检，再确认，最后顺序创建。
普通 CLI 需要交互确认，或在用户明确同意本批保存后使用 `--yes`。
保存站点为全局 `--site cn|boe`，放在 `tesla` 前，与源请求的
env/vregion 分离。BOE 验证使用 BOE 目标，不能复用当前 CN 表单 ID。
bytedcli 自动获取同站点 JWT；缺少认证使用 `bytedcli --site cn auth login`。
不回显 JWT，不把 CLI JWT 写入 Case。

Thrift `defaults.idl_version` 必须是真实 Git 分支；缺失或数字 BAM
版本时使用经核实的 `--idl-branch example.service.api=feature/idl`。
目标 Case 分支不是 IDL 分支，不默认 master。方法元数据由后端事务前校验。

## 支持边界

- 原文 `req_body`、JSON 大整数与负向内容保留，不按业务 IDL 修补。
- Path 编码、query 重复键和顺序保留；header 冲突报错，
  Cookie 按源规则合并，不额外添加 Content-Type。
- HTTP 相对 Host 的路径保留。真实执行需要 EnvTag 的 PSM→Host
  与业务接口鉴权；保存成功不证明二者就绪，不猜域名。
- 结构断言确定性生成一个 `pyv3` 后置脚本，保存时不求值。
  覆盖比较、类型、严格成员、存在、长度、集合量词、JSON 解码、
  可选字段与嵌套 current/parent 引用。
- 原始 expected、scenario/assertion_plan 保留在 Step 描述；
  描述不是执行断言，不能用 `metadata.source_refs` 证明持久化。
- 自然语言/script-null、外部观察、Mock、链路、变量、既有脚本和
  RPC context 无完整映射时整批失败，不以 warning 丢弃后保存。
- `defaults.timeout`、节点 `timeout`、`request.request_timeout`
  无 Case 持久化映射，明确拒绝；不能删字段后冒称完整迁移。
- 正则限 Go/Python 共享子集；wildcard/filter 报错。
- 新建 Case 为 `enabled=false` 草稿。显式 Debug 仍可执行；
  启用与调试另行授权。

## 回执与恢复

stdout 解析一份 bytedcli 标准 JSON。全成功读 `data`；失败时
`data=null` 且非零退出，按错误类型读 `error.details`：输入/参数
错误读 `error.details.issues`，批量创建结果读 `error.details.summary`。
`total = created + failed + unknown + not_attempted`；预检
`validated` 不计 created。结果为 validated、success、partial、
failed 或 indeterminate；任何 unknown 都使结果为 indeterminate。

当前项无法确认创建时停止后续，不重试，不把 unknown 当 failed。
先按 `client_id`、`log_id` 核对平台资产/日志，再明确选定确认未创建项。
认证、权限或共享目标失效也停止剩余项。Idempotency-Key 仅用于当前
请求关联，不能据此承诺跨次提交只创建一次。

返回实际数量、目录 Web 链接和未完成项，不回显 body/header/Token。
组件提交成功不等于保存成功；CLI 不回写原件或 mapping。
真实核对包括创建后读回/Web 资产、断言、HTTP/Thrift 执行及宿主
同 PPE 联调/JWT/CORS。本地单测不能代替真实核对。CLI/Skill 提供
版本材料；正式宿主预置与质量看板验收由对应负责人完成。

## 来源

- [组件 MR !298](https://code.byted.org/pdi-qa/teslaApp/merge_requests/298)
- [宿主 MR !826](https://code.byted.org/devinfra/swarm/merge_requests/826)
- [迁移源 TeslaX MR !71](https://code.byted.org/pdi-qa/teslax-cli/merge_requests/71)
- [技术方案](https://bytedance.larkoffice.com/docx/JaOidkMEboSN9wxD8MucI0zjnTc)
