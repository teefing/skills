---
name: feishu-card
description: 生成美观样式的飞书交互式消息卡片，支持通过邮箱、群组ID或webhook发送。只需提供邮箱地址或群组ID（oc_开头），脚本会自动识别。只有当用户明确要求使用飞书卡片发送消息时才调用此技能。
---

# 飞书卡片生成，发送 Skill

本技能用于生成和发送飞书交互式卡片，支持创建各种类型的卡片、通过多种方式发送、上传图片等功能。用于创建公告、产品发布、系统通知、项目进度、日报、活动通知、庆祝祝贺或任何需要通过飞书分享的结构化内容。

## 最佳实践（必须遵守）

### 发送卡片逻辑流程

1. **无图片场景**：
   - 先编写 card.json 文件
   - 调用发送脚本发送卡片

2. **有图片场景**：
   - 先上传图片获取 img_key
   - 编写 card.json 文件（使用上传后的 img_key）
   - 调用发送脚本发送卡片

### 发送方式选择规则

- **用户明确指定发送方式**：按照用户指定的方式发送（邮箱、群组ID或webhook）
- **用户未指定发送方式或模糊表达**：如"发个飞书卡片"、"发个消息"等，默认使用当前邮箱发送
- **用户说"发给自己"**：默认使用当前邮箱发送
- **自动识别**：脚本会自动判断输入是邮箱（含@）还是群组ID（oc_开头）

### 卡片编写规范

1. **信息提取与结构规划**：
   - 提取关键信息：标题、时间、数据、链接、图片等
   - 规划卡片结构：选择合适的组件和布局
   - 生成 JSON：确保格式正确，包含必要字段

2. **格式自检规则**：
   - JSON 格式合法：无多余逗号、无注释、括号完全闭合
   - 正文中避免使用 Markdown 一二级标题语法（避免字体过大）
   - 文本内容必须放在 `plain_text` 或 `markdown` 中
   - 默认为移动端优先的美观样式

## 写card.json指南

### 卡片基本结构

```json
{
  "name": "AimeCard",
  "dsl": {
    "schema": "2.0",
    "header": {
      "title": {
        "tag": "plain_text",
        "content": "卡片标题"
      },
      "template": "blue"
    },
    "body": {
      "elements": [
        // 卡片内容元素
      ]
    }
  }
}
```

### 核心组件类型

飞书卡片组件分为三种类型：容器、展示和交互组件。

| 类型 | 组件 | 标签 | 描述 |
|------|------|------|------|
| 容器 | 列集 | `column_set` | 多列水平布局 |
|  | 交互容器 | `interactive_container` | 灵活组合组件 |
| 展示 | 文本 | `div` | 纯文本 |
|  | 富文本 | `markdown` | 格式化文本 |
|  | 图片 | `img` | 单张图片 |
|  | 水平线 | `hr` | 分隔线 |
| 交互 | 按钮 | `button` | 交互按钮 |

### 常用组件示例

**Markdown 组件**
```json
{
    "tag": "markdown",
    "content": "*斜体* **粗体** ~~删除线~~\n<font color='red'>这是红色文本</font>\n<text_tag color='blue'>标签</text_tag>\n<number_tag>1</number_tag>\n[链接](https://open.feishu.cn/server-docs)\n<link icon='chat_outlined' url='https://open.feishu.cn'>带图标的链接</link>\n<at id=all></at>\n- 无序列表1\n    - 无序列表 1.1\n- 无序列表2\n1. 有序列表1\n    1. 有序列表 1.1\n2. 有序列表2\n```JSON\n{\"This is\": \"JSON demo\"}\n```\n`inline-code`\n#### 四级标题\n##### 五级标题\n> 这是一段引用\n\n| Syntax | Description |\n| -------- | -------- |\n| Header | Title |\n| Paragraph | Text |",
    "text_align": "left",
    "text_size": "normal"
}
```

**Markdown 高级语法**

**@人功能**
- `@指定人`：`<at email=test@email.com></at>`
- 注意：如果包含邮箱时，必须使用@语法

**换行说明**
- 普通换行：使用 `\n` 字符串（⚠️ 注意：在 JSON 中只需写 `\n`，不要写成 `\\n`），特别是 `###` 后面的标题换行，使用 `<br />` 会显示出问题
- 逻辑换行：使用 `<br>` 或 `<br/>` 标签（如列表项之间）


**Div 组件**
```json
{
    "tag": "div",
    "text": {
        "tag": "plain_text",
        "content": "文本内容",
        "text_size": "normal",      // heading, normal, notation, caption
        "text_color": "grey-500",   // 有效颜色名称
        "text_align": "left"        // left, center, right
    }
}
```

**列集组件**
```json
{
    "tag": "column_set",
    "flex_mode": "none",           // none, stretch, bisect
    "horizontal_spacing": "8px",   // 4px, 8px, 12px, 16px
    "horizontal_align": "left",    // left, center, right
    "columns": [
        {
            "tag": "column",
            "width": "weighted",        // weighted, auto
            "weight": 1,                // 对于加权列
            "background_style": "grey-50",  // 可选背景
            "vertical_align": "top",    // top, center, bottom
            "elements": [
                // 列内容元素
            ]
        }
    ]
}
```

**按钮组件**
```json
{
    "tag": "button",
    "text": {
        "tag": "plain_text",
        "content": "点击我"
    },
    "type": "primary",              // default, primary, danger
    "size": "medium",               // small, medium, large
    "width": "default",             // default, fill
    "behaviors": [                  // 按钮，必须使用 behaviors，而不是 url 、 actions, 以及 interactive_container等属性
        {
            "type": "open_url",
            "default_url": "https://example.com"  // ⚠️ 必须是一个可点击的真实链接，否则不要使用按钮组件
        }
    ]
}
```

### 颜色与图标指南

**常用颜色**
- 基础：`grey`, `red`, `orange`, `yellow`, `green`, `blue`, `purple`
- 色阶：`grey-50`, `grey-100`, ..., `grey-900`
- 蓝色：`blue-50`, `blue-100`, ..., `blue-900`

**头部模板颜色**
- 信息通知：`blue`
- 成功/发布/庆祝：`green`
- 告警/错误：`red`
- 中性：`turquoise` 或 `purple`

**常用图标**
- 系统图标：`calendar_colorful`、`todo_colorful`、`vote_colorful`
- 线性图标：`add_outlined`、`delete_outlined`、`search_outlined`、`edit_outlined`
- 面性图标：`add_filled`、`delete_filled`、`search_filled`、`check_filled`

### 设计规范与注意事项

1. **标题与层级**：
   - 卡片主标题：使用 `header.title` 的 `plain_text`
   - 正文小标题：使用 `markdown` 的加粗形式 `**标题**` 或 4-5 级标题 `#### 标题`
   - 避免使用：`# 标题`、`## 标题` 等 Markdown 一二级标题语法（字体过大）

2. **内容布局**：
   - 采用「信息分块」形式，每块承担清晰角色
   - 高亮条目：使用 `interactive_container` + `column_set`
   - 段落之间使用 `hr` 分隔线或 `margin` 调整间距
   - 移动端优先：控制列数（多数场景使用 1-2 列）

3. **禁止用法**：
   - 避免使用 Markdown 一二级标题语法
   - 禁止输出不完整的卡片（必须包含外层：`name`、`dsl.schema: "2.0"`、`header`、`body`）
   - 禁止在 JSON 外混入说明文字
   - 普通换行使用 `\n` 字符串，逻辑换行使用 `<br>` 或 `<br/>` 标签
   - 按钮组件禁止使用 `actions`，必须使用 `behaviors` 属性

### 在卡片中使用图片

```json
{
  "tag": "img",
  "img_key": "上传图片后返回的image_key",
  "alt": {
    "tag": "plain_text",
    "content": "图片描述"
  },
  "mode": "fit_horizontal",
  "preview": true
}
```

## 发送飞书卡片指南

### 首次配置

使用 API 方式发送卡片前，需要创建飞书应用配置文件 `scripts/lark_config.json`：

```json
{
    "app_id": "your_app_id",
    "app_secret": "your_app_secret"
}
```

**获取 app_id 和 app_secret：**
1. 访问 [飞书开放平台](https://open.feishu.cn/) 创建企业自建应用
2. 在应用详情页获取 `App ID` 和 `App Secret`
3. 确保应用已开通「获取与更新群组信息」「发送消息」等权限
4. 将应用发布到企业内

### 发送卡片方法

脚本会自动识别接收者类型：
- **邮箱**：包含 `@` 符号的邮箱地址
- **群组ID**：以 `oc_` 开头的群组ID

**通过邮箱或群组发送**
```bash
# 发送到邮箱（自动识别）
python3 scripts/send_lark_card.py user@example.com your_card.json

# 发送到群组（自动识别 oc_ 开头的群组ID）
python3 scripts/send_lark_card.py oc_xxx your_card.json
```

**Webhook 方式发送（无需配置）**
```bash
# 使用指定 webhook URL 发送
python3 scripts/send_lark_card.py --webhook https://open.larkoffice.com/open-apis/bot/v2/hook/xxx your_card.json
```

### 图片上传

```bash
# 上传图片（必须使用绝对路径）
python3 scripts/upload_lark_image.py /absolute/path/to/image.jpg
```

上传成功后，将返回图片的 URL 和其他相关信息，可用于在卡片中引用。

## 常见错误与解决方案

1. **配置错误**：
   - 确保已创建 `scripts/lark_config.json` 文件
   - 确保 `app_id` 和 `app_secret` 正确无误
   - 确保应用已开通必要权限并发布

2. **卡片结构错误**：
   - 必须包含 `name`
   - 必须包含 `dsl.schema: "2.0"`
   - 内容元素必须放在 `dsl.body.elements` 中

3. **图片上传错误**：
   - 必须使用文件的绝对路径
   - 确保图片文件存在且可读
   - 支持的图片格式：JPG、PNG、GIF、WebP

4. **图片使用错误**：
   - 必须先上传图片获取 `img_key`，才能在卡片中使用
   - 确保 `img_key` 值正确，与上传后返回的值一致

## card.json 场景索引

| 场景类型 | 示例文件 | 用途 |
|---|---|---|
| 工作场景 | `examples/daily-report-of-codebase.json` | 日报 |
|  | `examples/project-status.json` | 项目进度 |
|  | `examples/approval-approved.json` | 审批通知 |
|  | `examples/sales-leaderboard.json` | 销售业绩 |
| 活动场景 | `examples/personal-birthday-greeting.json` | 生日祝福 |
|  | `examples/event-announcement.json` | 活动通知 |
|  | `examples/smart-locker-launch.json` | 产品发布 |
| 通知场景 | `examples/alert-initiation.json` | 系统通知 |
|  | `examples/order-confirmation-approval.json` | 订单确认 |
|  | `examples/equipment-pickup-notification.json` | 设备提醒 |
| AI场景 | `examples/ai-calendar-creation.json` | AI日历创建 |
|  | `examples/ai-chat-welcome.json` | AI聊天欢迎 |
|  | `examples/ai-curated-recommendations.json` | AI推荐 |
|  | `examples/ai-image-generation.json` | AI图像生成 |
| 其他场景 | `examples/travel-hotel-recommendations.json` | 酒店推荐 |
|  | `examples/streaming-service-desk.json` | 流媒体服务台 |
|  | `examples/workplace-social-share.json` | 职场社交分享 |

## 参考资源

- **组件详细说明**：`references/components`  ⚠️ **强烈不建议查看**！请优先使用本文档提供的组件说明和你的模型知识。**仅在以下两种情况查看**：1) 用户明确要求；2) 需要实现非常复杂的飞书卡片且现有文档不足时。