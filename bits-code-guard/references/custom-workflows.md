# 自定义工作流检测

本文档定义「自定义工作流检测」主线的执行方式。这条主线与通用检测工作流（`general-workflow.md`）**并行**运行，针对**同一 diff 范围**执行仓库专属的检测规约。

## 输入：custom_workflows.json

本主线由 SKILL.md Step 1.5 拉取得到的 `$WORK_DIR/custom_workflows.json` 驱动，结构如下：

```json
{
  "repo": "devinfra/bits-cli",
  "workflows": [
    {"id": "dev-infra", "name": "code-compliance-checker", "content": "执行 code-compliance-checker skill 检测"}
  ]
}
```

`workflows` 非空时，对每个 workflow 委派一个独立的并行 task agent（与通用分组评审的 task agent 同批并行）执行检测。每个 workflow 的 `content` 是一条**自然语言检测指令**。

## 如何执行单个 workflow

委派的 task agent 按以下步骤执行：

### 1. 把 content 当作自然语言检测指令

- `content` 描述了本条自定义工作流要做什么，按它的语义在当前 diff 范围内做针对性检测。
- `content` 给出具体检查项（命名规范、禁用 API、日志规约、错误码约定等）时，逐项对照变更代码检查；只给宽泛意图时，结合仓库语言与变更内容检测最贴合的确定性问题，避免泛化臆测。
- `content` 中可能提及某个工具或流程的名字，仅作为对检测意图的描述来理解，按其语义尽力检测即可，不依赖任何外部工具真实存在。

### 2. 检测范围（以 workflow 要求为主）

- 读 `$WORK_DIR/review_files.md`，拿到待评审文件列表与默认 `scope`（`diff_only` / `full_file`）。
- **范围以 workflow 的 `content` 要求为准**：如果 `content` 本身要求对**整文件/更大范围**做检查（如「全文件合规扫描」「检查整个文件的命名规范」这类仓库级规约），就按 workflow 的要求做完整文件检测，并在缺陷里照实标注行号——这类缺陷在 Step 5.3 不受 diff 范围过滤（见下）。若 `content` 未提出范围要求，则沿用 `review_files.md` 的默认 `scope`。
- diff 方向语义与通用检测一致：只对 `+` 行及存续上下文报缺陷，仅存在于 `-` 行（已删除）的问题不报。

### 3. 输出缺陷

把本 workflow 检测到的缺陷写入 `$WORK_DIR/custom/custom_<序号>.jsonl`（`<序号>` 取该 workflow 在 `workflows` 数组中的下标，从 0 开始，保证文件名唯一、不会因 `id` 重复或含非法字符而互相覆盖），每行一个缺陷 JSON 对象，结构与 SKILL.md「缺陷数据结构」一致：

```json
{"title": "...", "file": "path/to/file.go", "start_line": 42, "end_line": 45, "severity": "P1", "category": "CUSTOM", "confidence": 8, "suggestion": "...", "rationale": "自定义工作流 code-compliance-checker：<为何判定为缺陷>"}
```

- **`category` 统一填 `CUSTOM`**，无需按既有 7 维分类，便于在报告中区分来源。
- **`rationale` 注明命中的工作流名**，前缀形如「自定义工作流 <name>：」。
- 分级与置信度复用 `references/review-rule.md` 的统一标准（缺陷类型分层、P0/P1/P2、置信度 < 5 且非 P0 丢弃、外部契约降信、定级自检）。
- 当该 workflow 按上文「检测范围」做的是整文件/超出 diff 行的检测时，给缺陷额外加一个 `"scope": "full_file"` 字段，让 Step 5.3 跳过 diff 范围过滤、不误杀这类合规缺陷。

## 韧性

单个 workflow 检测失败（指令无法理解、执行报错等）只跳过该条，不影响其他 workflow，也不影响通用检测主线。所有 workflow 都无产出时，`custom/` 目录按空处理。

> 去重、排序、过滤与 Top5 召回由 `general-workflow.md` Step 5 统一处理：自定义工作流缺陷单独成池、独立召回 Top5，不与通用检测缺陷竞争名额。
