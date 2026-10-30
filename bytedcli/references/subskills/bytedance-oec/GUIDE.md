---
name: bytedance-oec
description: "OEC 研发能力入口。用户要求使用 bytedcli oec，或进行 StarTrail 流量、用例、回放、DIFF、Mock、降噪和执行实例分析时使用；具体子命令由 OEC 当前运行时提供。"
---

# OEC

首次配置时，安装或升级到包含 `oec` 入口的 bytedcli；已有该入口可跳过全局安装。StarTrail 由 OEC 入口自动准备运行环境，无需执行 `self plugin install`。

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli oec star-trail --help
```

看到 StarTrail 帮助即表示已启用，帮助不要求登录。若 `oec` 是未知命令，需要使用包含该入口的 bytedcli 版本。若已发布版本尚未包含该入口，在 bytedcli 对应功能分支根目录编译验证：

```bash
npm ci
npm run build
node dist/bytedcli.js oec star-trail --help
```

本地编译后通过 `node dist/bytedcli.js` 调用当前分支，终端中的 `bytedcli` 仍取决于已安装版本。`bytedcli oec +update` 用于更新或修复 OEC 运行环境。

先查看当前能力和参数，不在宿主 Skill 中固定维护子命令树：

```bash
bytedcli oec --help
bytedcli oec --help --all-help
bytedcli oec <子命令> --help
bytedcli oec +update
```

完整业务 Skill 由 [oec/oec-cli](https://code.byted.org/oec/oec-cli) 维护；StarTrail 的能力、接口和工作流见该库的 [StarTrail Skill](https://code.byted.org/oec/oec-cli/blob/main/skills/oec-star-trail/SKILL.md)。按用户目标读取所需资料。

bytedcli 提供运行环境、全局 JSON/jq/yes 及身份桥接。业务参数、地域、读写语义和结果以对应子命令帮助与业务 Skill 为准。MCP 默认使用共享 `run_command`，`--all-tools` 模式使用 `oec` 透传完整参数。
