---
name: bytedance-dyt
description: "Use bytedcli dyt to discover and run the engineering commands a repository ships through its dyt entry (the Douyin unified engineering CLI): list the command catalog, read a command's usage and side effects, then run it and get a structured result. Trigger when the user asks for dyt, or asks for a repository engineering task such as workspace status, checks, builds or environment diagnostics while working inside a checkout that ships dyt. Do not trigger outside such a checkout or for build and release flows of other platforms."
---

# bytedcli dyt

`bytedcli dyt` 在当前目录所在的仓库里查找 dyt 入口，并把 `dyt` 之后的命令和参数原样交给它执行。可用命令由仓库自身提供，随代码版本变化；以 `bytedcli dyt help` 的输出为准，不要猜测命令名或参数。

## 使用前提

- 在提供 dyt 的仓库目录（根目录或任意子目录）内执行；bytedcli 从当前目录向上查找仓库根目录的 dyt 入口。
- 找不到入口时返回 `DYT_ENTRY_NOT_FOUND`，进入仓库目录后重试。

## 发现命令

```bash
# 命令目录
bytedcli dyt help
# 某个命名空间或命令的用法、参数与副作用
bytedcli dyt help hello
bytedcli dyt help hello world
bytedcli dyt hello world --help
# 结构化命令目录：命令名、usage、options、side_effect、cost、stability、是否支持 JSON
bytedcli --json dyt help
```

- 命令形态为 `bytedcli dyt <NAMESPACE> <COMMAND> [SUBCOMMAND] [OPTIONS]`，最多三级。
- 执行前先读目标命令的帮助：`side_effect` 为 `none`（只读）、`local`（修改本地状态）或 `remote`（修改远端状态）；`cost` 为 `build` 表示包含编译等高耗时操作；`json` 表示是否支持结构化输出。
- 帮助和提示里出现的 `dyt <命令>` 对应 `bytedcli dyt <命令>`。

## 执行命令

```bash
bytedcli dyt hello world --name demo-name
bytedcli --json dyt hello world --name demo-name
```

- 文本模式原样输出命令结果；日志、进度和警告在 stderr。
- `--json` 写在 `dyt` 前后均可。成功时命令结果在 `data`，命令名和警告在 `context.command`、`context.warnings`；失败时 `error.code` 为 `DYT_<错误码>`，并带 `message` 与 `hint`。
- 命令不支持结构化输出时返回 `DYT_JSON_NOT_SUPPORTED`，去掉 `--json` 重新执行。
- 退出码：`0` 成功，`1` 执行完成但结果不通过（例如检查失败），`2` 用法错误，`3` 环境未就绪，`4` 需要确认或权限不足，`5` 远端或网络失败，`130` 被中断。

## 写操作

```bash
# 预览将要执行的写操作
bytedcli --json dyt <NAMESPACE> <COMMAND> --dry-run
# 用户确认后执行远端写操作
bytedcli --json dyt <NAMESPACE> <COMMAND> --yes
```

- `side_effect` 为 `local` 或 `remote` 的命令先用 `--dry-run` 预览。
- 远端写操作在 JSON 模式或非终端环境下不会交互询问：缺少 `--yes` 时返回 `DYT_CONFIRMATION_REQUIRED`（退出码 4），命令不会执行。先展示 `--dry-run` 结果并取得用户明确同意，再加 `--yes` 重试；`--yes` 不代替用户授权。
- 终端里以文本模式执行远端写操作时，会在终端询问确认。
- 远端写入失败不代表操作未生效；结果不确定时先查询状态，不要直接重试。

## 常见问题

| 现象                     | 处理                                                          |
| ------------------------ | ------------------------------------------------------------- |
| `DYT_ENTRY_NOT_FOUND`    | 当前目录不在提供 dyt 的仓库内；进入仓库目录后重试             |
| `DYT_UNKNOWN_COMMAND`    | 命令不存在；按 `hint` 中的相近命令或 `bytedcli dyt help` 修正 |
| `DYT_USAGE`              | 参数错误；用 `bytedcli dyt <命令> --help` 核对用法            |
| `DYT_ENV_NOT_READY`      | 环境缺少依赖；按 `hint` 准备环境后重试                        |
| `DYT_RESULT_UNPARSEABLE` | 未得到结构化结果；去掉 `--json` 查看原始输出                  |
