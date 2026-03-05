# 编写飞书卡片

## 🎨 高级组件

### 组件分类

飞书卡片组件分为三种类型：**容器**、**展示**和**交互**组件。

| 类型 | 组件 | 标签 | 描述 |
|------|------|------|------|
| **容器** | 列集 | `column_set` | 多列水平布局 |
|  | 可折叠面板 | `collapsible_panel` | 隐藏次要信息 |
|  | 表单容器 | `form` | 批量提交表单数据 |
|  | 交互容器 | `interactive_container` | 灵活组合组件 |
| **展示** | 标题 | `header` | 卡片标题 |
|  | 文本 | `div` | 纯文本 |
|  | 富文本 | `markdown` | 格式化文本 |
|  | 图片 | `img` | 单张图片 |
|  | 多图片 | `img_combination` | 多张图片网格/轮播 |
|  | 人员 | `person` | 用户头像和姓名 |
|  | 人员列表 | `person_list` | 多个用户 |
|  | 图表 | `chart` | 数据可视化 |
|  | 表格 | `table` | 数据表格 |
|  | 水平线 | `hr` | 分隔线 |
|  | 音频 | `audio` | 音频播放器 |
| **交互** | 按钮 | `button` | 交互按钮 |
|  | 溢出 | `overflow` | 可折叠按钮组 |

### 高级文本组件

#### Markdown 组件高级用法
支持格式化的富文本：

**支持的 markdown：**
- `**粗体**`, `*斜体*`
- `[链接文本](url)`
- `` `内联代码` ``
- `- 项目符号列表`
- `\n` 用于换行（在 JSON 中转义为 `\\n`）

**Markdown 中的颜色：**
```
<font color='grey'>灰色文本</font>
<text_tag color='blue'>蓝色标签</text_tag>
```

#### Div 组件高级用法
带颜色和大小控制的纯文本：

### 高级布局组件

#### 列集组件高级用法
多列布局（并排内容）：

#### 交互容器高级用法
灵活组合组件：

### 高级交互组件

#### 按钮组件高级用法
⚠️ **重要**: Schema 2.0 已弃用 `action` 标签。现在直接使用按钮：

### 其他高级组件

#### 分隔线
```json
{
    "tag": "hr"
}
```

#### 图片组件高级用法
```json
{
    "tag": "img",
    "img_key": "img_v2_...",           // 图片标识符
    "alt": {
        "tag": "plain_text",
        "content": "替代文本"
    },
    "scale_type": "fit_horizontal",    // fit_horizontal, crop_center
    "size": "medium",                  // small, medium, large, stretch_without_padding
    "corner_radius": "10px",           // 可选: 4px, 8px, 10px 等
    "preview": true                     // 启用图片预览
}
```

#### 多图片组件
```json
{
    "tag": "img_combination",
    "layout": "grid",                  // grid, carousel
    "card_id": "img_combination_1",
    "img_list": [
        {
            "img_key": "img_v2_...",
            "alt": {
                "tag": "plain_text",
                "content": "图片描述"
            },
            "preview": true
        }
    ]
}
```

#### 人员组件
```json
{
    "tag": "person",
    "avatar_url": "https://...",
    "name": {
        "tag": "plain_text",
        "content": "张三"
    },
    "extra": {
        "tag": "plain_text",
        "content": "产品经理"
    }
}
```

#### 人员列表组件
```json
{
    "tag": "person_list",
    "persons": [
        {
            "avatar_url": "https://...",
            "name": {
                "tag": "plain_text",
                "content": "张三"
            },
            "extra": {
                "tag": "plain_text",
                "content": "产品经理"
            }
        }
    ],
    "max_show_count": 3,
    "show_more": {
        "tag": "plain_text",
        "content": "查看更多"
    }
}
```

#### 表格组件
```json
{
    "tag": "table",
    "columns": [
        {
            "name": "姓名",
            "width": "weighted",
            "weight": 1
        },
        {
            "name": "部门",
            "width": "weighted",
            "weight": 1
        }
    ],
    "rows": [
        {
            "cells": [
                {
                    "tag": "plain_text",
                    "content": "张三"
                },
                {
                    "tag": "plain_text",
                    "content": "产品部"
                }
            ]
        }
    ]
}
```

#### 图表组件
```json
{
    "tag": "chart",
    "title": {
        "tag": "plain_text",
        "content": "销售趋势"
    },
    "config": {
        "type": "line",
        "x_axis": {
            "title": "月份",
            "data": ["1月", "2月", "3月"]
        },
        "y_axis": {
            "title": "销售额",
            "data": [100, 200, 300]
        }
    }
}
```

#### 音频组件
```json
{
    "tag": "audio",
    "title": {
        "tag": "plain_text",
        "content": "音频标题"
    },
    "audio_url": "https://...",
    "cover_url": "https://...",
    "duration": 120
}
```

#### 可折叠面板组件
```json
{
    "tag": "collapsible_panel",
    "header": {
        "tag": "plain_text",
        "content": "详细信息"
    },
    "body": {
        "elements": [
            // 面板内容
        ]
    }
}
```

#### 表单容器组件
```json
{
    "tag": "form",
    "name": "feedback_form",
    "elements": [
        // 表单元素
    ],
    "submit_button": {
        "tag": "button",
        "text": {
            "tag": "plain_text",
            "content": "提交"
        },
        "type": "primary"
    }
}
```

#### 溢出组件
```json
{
    "tag": "overflow",
    "options": [
        {
            "text": {
                "tag": "plain_text",
                "content": "选项1"
            },
            "value": "option1"
        },
        {
            "text": {
                "tag": "plain_text",
                "content": "选项2"
            },
            "value": "option2"
        }
    ]
}
```

## 🎯 高级卡片示例

以下是一个完整的飞书卡片示例，展示了一个活动通知卡片：

## 🎨 详细颜色与图标参考

### 颜色枚举值详细表
| **颜色枚举值** | **浅色主题** | **深色主题** | **色系** |
|---|---|---|---|
| blue | #1456F0 | #75A4FF | 蓝 |
| green | #1A7526 | #51BA43 | 绿 |
| red | #C02A26 | #F6827E | 红 |
| orange | #A44904 | #F3871B | 橙 |
| yellow | #865B03 | #FBCB46 | 黄 |
| purple | #7A35F0 | #B88FFE | 紫 |
| grey | #646a73 | #a6a6a6 | 中性色 |
| turquoise | #067062 | #1AB7A1 | 青 |
| wathet | #076A94 | #25B2E5 | 天蓝 |

### 有效颜色详细参考

**所有有效颜色：**
- 基础：`grey`, `red`, `orange`, `yellow`, `green`, `blue`, `purple`
- 色阶：`grey-50`, `grey-100`, `grey-200`, `grey-300`, `grey-400`, `grey-500`, `grey-600`, `grey-700`, `grey-800`, `grey-900`
- 蓝色：`blue-50`, `blue-100`, ..., `blue-900`
- 其他：`lime-50`, `turquoise-50`, `carmine-50`, `violet-50` 等

**无效颜色（请勿使用）：**
- ❌ `emerald-50`（使用 `green-50` 或 `turquoise-50`）
- ❌ 自定义十六进制颜色
- ❌ RGB 值

### 间距与边距详细说明

在元素之间添加间距：

```json
{
    "tag": "div",
    "margin": "16px 0px 0px 0px",  // 上 右 下 左
    "text": { /* ... */ }
}
```

所有边距值：`4px`, `8px`, `12px`, `16px`, `20px`, `24px`

### 图标详细列表

#### 系统图标
- `calendar_colorful`、`todo_colorful`、`vote_colorful`

#### 线性图标 (outlined)
- `add_outlined`、`delete_outlined`、`search_outlined`、`edit_outlined`、`download_outlined`、`upload_outlined`、`refresh_outlined`、`check_outlined`、`close_outlined`、`warning_outlined`

#### 面性图标 (filled)
- `add_filled`、`delete_filled`、`search_filled`、`edit_filled`、`check_filled`、`close_filled`

#### 图标高级用法
图标不仅可以在卡片头部使用，还可以在多个场景中应用：

**1. 卡片头部**
```json
{
  "header": {
    "title": {"tag": "plain_text", "content": "卡片标题"},
    "template": "blue",
    "icon": {
      "tag": "standard_icon",
      "token": "calendar_colorful"
    }
  }
}
```

**2. Markdown 文本中**
```json
{
  "tag": "markdown",
  "content": "审批已完成",
  "icon": {
    "tag": "standard_icon",
    "token": "succeed_filled",
    "color": "green"
  }
}
```

#### 获取更多图标
```bash
# 查看所有图标
python3 scripts/list_icons.py
```

## 🎯 高级设计模式

### 带图标的文本（列布局）
```json
{
    "tag": "column_set",
    "columns": [
        {
            "tag": "column",
            "width": "auto",
            "elements": [
                {"tag": "img", "img_key": "...", "size": "small"}
            ]
        },
        {
            "tag": "column",
            "width": "weighted",
            "weight": 1,
            "elements": [
                {"tag": "markdown", "content": "**主要内容**"}
            ]
        }
    ]
}
```

### 带背景的指标卡片
```json
{
    "tag": "column",
    "background_style": "grey-50",
    "padding": "12px 12px 12px 12px",
    "elements": [
        {"tag": "div", "text": {"content": "标签", "text_color": "grey"}},
        {"tag": "div", "text": {"content": "29 单", "text_size": "heading"}},
        {"tag": "markdown", "content": "<text_tag color='blue'>+86%</text_tag>"}
    ]
}
```

## 🎨 详细设计规范

### 标题与层级详细说明
- 卡片主标题：使用 `header.title` 的 `plain_text`
- 正文小标题：使用 `markdown` 的加粗形式 `**标题**` 或 4-5 级标题 `#### 标题`
- **避免**：`# 标题`、`## 标题` 等 Markdown 一二级标题语法（字体过大）
- 文本字号：默认使用 `"text_size": "normal"` 或 `"normal_v2"`

### 内容布局详细说明
- 采用「信息分块」形式，每块承担清晰角色
- 高亮条目：使用 `interactive_container` + `column_set`
  - 左列：emoji 图标（如 ✨ / ⚡ / 🔒）
  - 右列：标题（加粗）+ 描述（灰色小字）
  - 容器使用浅色背景（如 `background_style: "green-50"`）
- 段落之间使用 `hr` 分隔线或 `margin` 调整间距
- 移动端优先：控制列数（多数场景使用 1-2 列），避免宽表格，使用要点列举代替超长段落

### 颜色与图标详细说明
- 头部 `template`：
  - 信息通知：`blue`
  - 成功/发布/庆祝：`green`
  - 告警/错误：`red`
  - 中性：`turquoise` 或 `purple`

## ⛔ 详细禁用用法

1. **避免使用 Markdown 一二级标题语法**
   - 不建议：`# 标题`、`## 标题` 出现在 `markdown` 内容中
   - 可使用：`#### 标题`、`##### 标题` 或加粗 `**标题**` 作为替代

2. **禁止输出不完整的卡片**
   - 必须包含外层：`msg_type: "interactive"`、`card.schema: "2.0"`、`header`、`body`

3. **禁止在 JSON 外混入说明文字**
   - 当用户要求「直接发送卡片」时，输出纯 JSON，不包含额外解释