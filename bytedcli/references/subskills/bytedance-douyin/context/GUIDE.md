---
name: bytedance-douyin-context
description: "抖音私域上下文的统一入口与能力路由。涉及字节/抖音内部需求、Meego、MR、当前代码、PSM、团队文档、群聊、会议、Oncall 工单、团队记忆、数据资产、compiled-wiki 或 ContextPack 时使用；任何明确要求使用 douyin-cli context 或 bytedcli douyin context 的任务也使用本 skill。普通本地代码开发、Git、提交推送或 MR 创建不触发。"
metadata:
  requires:
    bins: ["bytedcli"]
  cliHelp: "bytedcli douyin context --help; bytedcli douyin context workspace --help; bytedcli douyin context requirements --help; bytedcli douyin context status --help; bytedcli douyin context change --help; bytedcli douyin context doc --help; bytedcli douyin context meeting --help; bytedcli douyin context chat --help; bytedcli douyin context oncall --help; bytedcli douyin context memory --help; bytedcli douyin context data --help; bytedcli douyin context compiled-wiki --help;"
---

# 抖音私域上下文

使用 `bytedcli douyin context` 访问抖音私域上下文能力。该命令透明代理 `douyin-cli context`，参数和输出语义以上游当前命令帮助为准。

## 使用边界

- 只有回答当前问题需要新增的上下文证据时才调用本 skill。
- 普通本地代码开发、工作区检查、测试、Git 提交/推送和 MR 操作不属于上下文取证。
- 用户明确提到 `douyin-cli context`、`bytedcli douyin context` 或其命令结果时，使用本 skill 并保持用户提供的 ID、URL、repo、PSM、MR、路径和时间范围不变。
- 涉及具体需求且要继续开发、排查或评审时，优先恢复该需求的 ContextPack，再用需求、状态、变更或代码证据核对当前事实。泛泛的开发请求没有具体需求线索时不主动解析需求。

## 命令发现与运行时

不要猜测子命令、参数或返回字段，先查看当前受管运行时的帮助：

```bash
bytedcli douyin context --help
bytedcli douyin context <group> --help
```

bytedcli 优先复用 PATH 中的 `douyin-cli`，缺失时按需准备受管运行时。需要更新受管版本时使用：

```bash
bytedcli douyin context +update
bytedcli douyin context +update <version>
```

全局 `--jq` 不适用于该透明代理；需要过滤 JSON 时，将命令输出通过管道交给 `jq`。

## 能力路由

先把问题拆成独立待回答项，再按所需证据选择命令组。只查询足以闭合当前问题的证据，不默认读取全部上下文。

| 目标                                                | 优先命令组                          |
| --------------------------------------------------- | ----------------------------------- |
| 发现或确认 workspace、查看可用上下文范围            | `workspace`                         |
| 查需求身份、PRD/TRD、Meego 字段、关联任务与历史需求 | `requirements`                      |
| 查需求或任务的当前流程状态、负责人、节点和排期      | `status`                            |
| 查关联 MR、历史代码变更和交付事实                   | `change`                            |
| 查当前代码、接口、字段、调用链和静态实现            | 根据 `--help` 选择代码取证入口      |
| 查团队文档、单份文档或执行深度文档调研              | `doc` / `investigate`               |
| 查会议、群聊、Oncall 工单或团队知识                 | `meeting` / `chat` / `oncall`       |
| 查个人或团队记忆                                    | `memory`                            |
| 发现数据资产或执行明确的只读数据查询                | `data`                              |
| 管理或检索 compiled-wiki                            | `compiled-wiki`                     |
| 读取或沉淀需求上下文包、任务回执和持久产物          | 根据 `--help` 选择 ContextPack 入口 |

多类证据互不替代：需求归档不能证明当前代码行为，历史 MR 不能证明当前 revision，静态代码也不能单独证明负责人、排期或最终决策原因。按依赖顺序组合取证，并在证据足够后继续完成用户原任务。

## 执行约束

- 默认使用只读查询。创建、更新、覆盖、删除、上传、挂载或其他写入操作必须来自用户明确请求，并遵守对应命令帮助中的预览、确认和读回要求。
- 需要结构化结果时使用上游命令支持的 JSON 选项；透明代理不会额外包装业务输出。
- 命令失败时保留原始错误码和 hint，先按提示恢复认证、权限或运行时，再重试原命令；写入结果不确定时先读回状态，不自动重复提交。
- 获取到足够证据后继续回答、开发或排查，不要只转述 CLI 输出。
