# 03 · Style System

所有样式都来自 `assets/style-tokens/`，由 `scripts/extract_style_tokens.py` 从官方参考画板中抽取。**不允许在代码里硬编码颜色 / 字号 / 圆角**，所有这些值必须从 token 文件里读。

## Table of Contents

- 文件布局
- 每张 `<id>.json` 里有什么
- `_catalog.json` 的 `house_style`
- Planner / Renderer 的使用协议
- Preview 版式指纹
- 高保真路径的风格预算补充
- 语义分配规则
- 禁止事项

## 文件布局

```
assets/
├── previews/<id>.png         # 视觉锚：描述给多模态 LLM 用
├── raw/<id>.json             # 原始节点结构（仅作为审查时查阅，不喂 LLM）
└── style-tokens/
    ├── <id>.json             # 该图型的风格指纹
    └── _catalog.json         # 跨图聚合出的 house_style（全局默认）
```

## 每张 `<id>.json` 里有什么

```jsonc
{
  "id": "flowchart",
  "cn": "流程图",
  "use_case": "单角色流程、审批/判断步骤",
  "source_token": "...",
  "node_count": 29,
  "style": {
    "palette": {
      "fill_colors":   [{"value": "#ffffff", "count": 4}, ...],
      "border_colors": [{"value": "#98a2b3", "count": 8}, ...],
      "text_colors":   [{"value": "#1f2329", "count": 17}, ...]
    },
    "typography": {
      "font_sizes":       [{"value": 14, "count": 16}, ...],
      "font_weights":     [{"value": "regular", "count": 11}, ...],
      "horizontal_align": [{"value": "center", "count": 20}]
    },
    "shape": {
      "composite_types": [{"value": "round_rect", "count": 5}, ...],
      "border_widths":   [{"value": "narrow", "count": 7}],
      "border_styles":   [{"value": "solid", "count": 7}, ...]
    },
    "connector": {
      "shapes":       [{"value": "straight", "count": 6}, ...],
      "arrow_styles": [{"value": "line_arrow", "count": 8}],
      "line_widths":  [{"value": "narrow", "count": 8}]
    },
    "uses_inline_svg_decoration": true
  }
}
```

**读法约定**：`count` 越高，越接近该图型的"house default"；Render 阶段选色/字号时，**从 count 最高的开始往下取**。但 `lark-style-architecture` 这类飞书高级架构图会把浅蓝/浅红/浅黄/浅绿作为低频模块底色，不能只取 top3；需要从完整 palette 里挑出语义分区色。要强调色（如"异常/阻塞"），优先取和主色差异大的（见下文"语义分配"）。

## `_catalog.json` 的 `house_style`

跨 15 张图聚合出来的全局规律。两条用途：

1. **跨图一致性**：一篇文档里同时有流程图和系统架构图时，两张图的背景色/字号共享 `house_style` 的默认值，避免视觉打架。
2. **冷启动**：当新的图型还没有专属 token 时，用 `house_style` 做 fallback。

## Planner / Renderer 的使用协议

Plan 阶段（04-planner-contract.md）里，必须读 `<id>.json` 的 `style` 段，并把选定的 token 值写进 plan：

```jsonc
{
  "style_budget": {
    "primary_fill":   "#ffffff",      // 取自 fill_colors[0]
    "primary_border": "#98a2b3",      // 取自 border_colors[0]
    "accent_border":  "#5b8ff9",      // 取自 border_colors[1]，用于主流程强调
    "danger_border":  "#e86868",      // 取自 border_colors[3]，用于异常
    "body_font_size": 14,             // 取自 font_sizes[0]
    "title_font_size": 24,            // 取自 font_sizes 里较大的那个
    "connector_shape": "straight",
    "arrow_style":    "line_arrow"
  }
}
```

Render 阶段**只能**使用 `style_budget` 里声明的值，不得现引入新的颜色/字号。

## Preview 版式指纹

`style-tokens` 只记录颜色、字号、形状和连线频次；它本身不足以还原 `assets/previews/` 里的高级感。Planner 还必须从 preview 视觉锚提炼一份**版式指纹**，写入 `plan.style_profile` 或等价的自检说明：

| 图型 | 必须捕捉的版式指纹 |
|---|---|
| `system-architecture` | 大画布弱点阵背景、左侧主架构堆叠、右侧外部依赖栏、顶部图例、小号层标签、浅色大容器 + 白色服务卡 |
| `matrix-quadrant` | 2×2 坐标矩阵、横纵轴标签、四块低饱和浅色象限、象限内用 bullet 文本而不是满屏卡片 |
| `sketch-architecture` | 低保真草图语义、虚线阶段分区、方形手绘卡片、双线/下划线笔触、少量跨阶段斜线或折线连接 |

这些特征不属于业务内容，不会违反"禁止抄文案"；它们是风格结构。Render 阶段如果只使用 token top1/top2 而没有版式指纹，会退化成普通盒子图，应在 Gate B 前打回。

## 高保真路径的风格预算补充

当 `route = "svg-openapi"` 时，`style_budget` 还要显式结算以下值，且全部来自 `<id>.json` 或 `_catalog.json`：

```jsonc
{
  "canvas_fill": "#fbfcfd",
  "grid_dot_color": "#b7bdc6",
  "soft_panel_fill": "#f7f8fa",
  "soft_panel_border": "#dadde3",
  "section_label_fills": ["#eee7ff", "#e7eeff", "#eaf7ee", "#fff4d9"],
  "semantic_fills": ["#eef3ff", "#fdebec", "#eaf7ee", "#fff4d9", "#f2ecff"],
  "semantic_borders": ["#5b7fcb", "#c94c4c", "#4e9d6d", "#c8a33e", "#7b67c9"]
}
```

缺哪个值就从同图型 token 的完整 palette 往后取；仍缺再从 `_catalog.json.house_style` 取。不要在 SVG 里写 token 之外的新色。

## 语义分配规则

token 文件给的是"这张图里用了哪些色"，但没有告诉你"哪种色代表异常"。由 Planner 负责做语义映射，参考原则：

- **中性主色**（高频灰/蓝）→ 常规节点
- **暖色**（红/橙）→ 异常、阻塞、风险
- **绿色** → 成功、完成、校验通过
- **紫色** → 外部依赖或策略层
- **金色/黄色** → 需要关注、人工介入

语义映射结果要写入 `plan.style_budget`，Render 阶段按 plan 照做，不二次发挥。

## 禁止事项

- ❌ 硬编码十六进制色值在脚本里（必须从 token 读）
- ❌ 把 `assets/raw/<id>.json` 的坐标或文案传给 LLM
- ❌ 跨图型借用 token（e.g. flowchart 用 funnel 的色板）——要借用必须显式在 plan 里注明 `style_source: "funnel"`
