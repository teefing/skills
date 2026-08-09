# 02 · Chart Taxonomy

当前支持 17 种图表类型。大部分图型一一对应 `assets/previews/<id>.png` 与 `assets/style-tokens/<id>.json`；但少数图型为**代码原生图**（仅 Mermaid / PlantUML），不依赖 style-tokens。表中 **signals** 用于选图型（Select 阶段），**structure** 用于 Plan 阶段约束拓扑，**route** 指定优先渲染路径，**fallback** 指定该类型不适用时最可能的替代。

> 对 DSL 图型：`id` 与 `assets/` 下文件名一一对齐。对代码原生图：不要求补 preview/raw/style-tokens，但必须补 examples 与飞书回读验证证据。
>
> 当前验证状态：17 种图型均已有可运行样例并完成飞书端验证；其中 `sequence` / `state-machine` / `flowchart` 已在 2026-04-28 重新按 Mermaid 路由复核，`funnel` 已在同日按彩色 DSL 路由复核。图型能力是否可对外发布，以 `COVERAGE_REPORT.md` 为准，而不是只看本表。

| # | id | 中文名 | signals（触发语义） | structure（拓扑约束） | route（优先渲染路径） | fallback |
|---|---|---|---|---|---|---|
| 1  | `business-architecture`     | 业务架构图          | "能力分层""平台组成""业务域" | N 行 × 多列，带左侧侧栏或顶部标题 | `dsl` | system-architecture |
| 2  | `system-architecture`       | 系统架构图          | "技术组件""服务拓扑""外部依赖" | 垂直 N 层 + 右侧外部依赖侧栏 | 强视觉验收优先 `svg-openapi`；低复杂度可 `dsl` | link-architecture |
| 3  | `flowchart`                 | 流程图              | "先做 A 再做 B""如果 X 则 Y" | 主流程走中轴，异常分支走侧线 | 标准审批/判断流优先 `mermaid(flowchart)`；复杂复合卡片流走 `dsl` | state-machine |
| 4  | `swimlane`                  | 泳道图              | "用户""运营""平台"等**多角色**协作 | 横向泳道 + 角色列头 | `dsl` | flowchart |
| 5  | `complex-swimlane`          | 复杂业务泳道图      | 多系统多节点端到端履约 | 多泳道 + 跨泳道跳转 + 分支 | `dsl` | swimlane |
| 6  | `sequence`                  | 时序图              | "A 调用 B""返回""回调" | 顶部角色头 + 垂直生命线 + 水平消息 | 优先 `mermaid(sequenceDiagram)`；必要时 `plantuml` | flowchart |
| 7  | `org-chart`                 | 组织架构图          | "团队""汇报""职责" | 自顶向下树 | `dsl` | business-architecture |
| 8  | `state-machine`             | 状态机图            | "状态""流转""失败重试" | 有向图 + 自环 | 优先 `mermaid(stateDiagram-v2)`；仅样式增强需求明显时回 `dsl` | flowchart |
| 9  | `funnel`                    | 漏斗图              | "阶段转化""流失" | 从上到下宽度递减 | `dsl`，且必须彩色分层、禁止无意义外框 | — |
| 10 | `gantt`                     | 甘特图              | "排期""周期""进度" | 时间轴 + 任务条 | `mermaid(gantt)` | milestone |
| 11 | `milestone`                 | 里程碑图            | "版本路线""阶段目标""关键节点" | 水平时间线 + 节点 | `dsl` | gantt |
| 12 | `matrix-quadrant`           | 矩阵象限图          | "优先级""价值 vs 成本" | 2×2 或 3×3 象限 | 强视觉验收优先 `svg-openapi`；低复杂度可 `dsl` | — |
| 13 | `link-architecture`         | 链路架构图          | "端到端链路""数据流转""系统依赖" | 从左到右串联组件，带分支 | `dsl` | system-architecture |
| 14 | `lark-style-architecture`   | 飞书画板风格架构图  | "策略到模块""承接关系""产品运营汇报""高级飞书风格架构图" | 顶部核心逻辑横幅 + 4-6 个彩色模块列 + 模块内二级卡片/要点 + 跨模块右角连接 | `dsl` | business-architecture |
| 15 | `sketch-architecture`       | 手绘风格架构图      | "草图""早期方案""低保真" | 任意拓扑，视觉带手绘笔触 | 强视觉验收优先 `svg-openapi`；低复杂度可 `dsl` | — |
| 16 | `mindmap`                   | 思维导图            | "思维导图""脑图""要点整理""发散" | 单根节点 + 多层分支 | 优先 `mermaid(mindmap)`；必要时 `plantuml` | — |
| 17 | `er-diagram`                | ER 图               | "ER 图""实体关系""表结构""主键""外键" | 实体 + 字段 + 基数关系 | 优先 `mermaid(erDiagram)`；必要时 `plantuml` | — |

## 选型原则

1. **语义优先，形状其次**：用户说"多个角色协作"就选 swimlane，哪怕结构可以用 flowchart 表达。
2. **代码原生优先**：只要目标图型已被飞书代码图原生支持，且用户要的是标准图法，优先 Mermaid / PlantUML，不要先用 DSL 硬拼。
3. **不确定时问一次**：如果 `business-architecture` 和 `system-architecture` 两种候选都合理，一次性给出 2-3 个选项让用户选，**不连环问**。
4. **不"兜底到 flowchart"**：如果没有清晰匹配项，告知用户当前 17 种覆盖不到这种需求，而不是硬塞。

## 参考素材的正确用法

- ✅ **允许**：把 `assets/style-tokens/<id>.json` 作为 style 软约束，把 `assets/previews/<id>.png` 描述给多模态 LLM 当视觉锚。
- ✅ **必须**：当用户评价"不够高级 / 太简单 / 和示例差距大"，对 `system-architecture` / `matrix-quadrant` / `sketch-architecture` 读取 `07-premium-style-contracts.md`，并优先用 SVG 高保真路径还原 preview 的版式气质。
- ❌ **禁止**：把 `assets/raw/<id>.json`（节点级坐标）作为 few-shot 喂给 LLM，会诱导它抄坐标和抄文案。
- ❌ **禁止**：按"这张图上写了'用户入口/核心能力/数据底座'，那我也这么分层"——这是参考素材里的**业务内容**，不是"样式"。

## 三类强视觉图型的选型下限

- `system-architecture`：输入必须能形成主架构区和外部依赖/运行时/基础设施等侧栏或底座。只给 3-5 个服务名时，不要强行画成参考图级复杂系统架构；应先降级为 `link-architecture` 或一次性要求补模块分层。
- `matrix-quadrant`：必须有两个明确评价轴，默认 2×2。禁止把四个象限渲染成横向四列卡片；没有坐标轴标签和象限边界时视为选型失败。
- `sketch-architecture`：必须表达阶段/泳道/模块组与少量关键连线。禁止只画普通圆角卡片；没有虚线分区、手绘双线/下划线或草图式弱网格时视为风格失败。

## lark-style-architecture 选型下限

只有当输入本身包含**核心逻辑/策略**、**至少 4 个承接模块**，且大多数模块有可归纳的二级能力或要点时，才选 `lark-style-architecture`。如果用户只给出 2-3 层线性分层，应该选 `business-architecture` 或 `system-architecture`，不要把 `lark-style-architecture` 画成"三排白色盒子 + 少量箭头"。
