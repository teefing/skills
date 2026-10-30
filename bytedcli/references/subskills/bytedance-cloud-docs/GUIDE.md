---
name: bytedance-cloud-docs
description: "公司级文档检索与知识问答入口。帮助用户查找、阅读和理解公司内部产品、平台、技术与研发文档，依据官方资料回答问题、梳理操作步骤、比较方案和解释故障。用户询问某个内部系统是什么、如何使用、为什么这样设计，寻找接入指南、配置说明、API、最佳实践或相关资料时使用；也适用于只给关键词、简称、问题现象，或尚不知道该查哪个产品的探索性问题。无需用户明确提到字节云、Cloud Docs、文档中心或搜索；跨产品、跨组件的问题同样适用。支持自然语言查文档、按文档 ID 读取，以及业务域和 API 文档发现。"
---

# bytedcli Cloud Docs

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

- 根据用户的自然语言询问召回 ByteCloud 产品或组件相关文档
- 搜索/获取 Cloud Docs
- 查询业务域与 API 文档

## Routing

- 用户以自然语言询问 ByteCloud 产品或组件文档时，读取 [文档搜索与召回](references/recall-docs.md)。
- 用户已经给出明确 `doc_id`、只要求读取指定文档时，使用 `cloud-docs get`，并读取 [Cloud Docs CLI 命令](references/cloud-docs.md)。
- 用户明确要求执行 `search`、`list-business` 或 `list-docs` 命令时，读取 [Cloud Docs CLI 命令](references/cloud-docs.md)。

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
bytedcli cloud-docs search "keyword"
bytedcli cloud-docs get "doc_id"
bytedcli cloud-docs list-business
bytedcli cloud-docs list-docs "business_id" --api-doc "tce:v1"
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json cloud-docs search ...`）

## References

- [Cloud Docs CLI 命令](references/cloud-docs.md)
- [文档搜索与召回](references/recall-docs.md)
