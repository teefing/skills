# 内嵌 HTML 块操作（Embed Operations）

> 本文档覆盖在飞书文档中**插入、更新、读取、删除** HTML 块（AddOns Block, block_type=40）的完整流程。

## 前提

| 场景 | 身份 | 说明 |
|------|------|------|
| Bot 自建的文档 | `--as bot` | 无需用户登录 |
| 用户手建/他人文档 | `--as user` | 需要 `lark-cli auth login` |

⚠ **同一文档读写必须用同一身份**，Bot 建的文档用 User 去操作会返回 `1770032 forBidden`。

所需权限 scope: `docx:document:write_only`、`docx:document:readonly`

---

## 1. 插入 HTML 块（Create）

```bash
# 步骤一：准备自包含 HTML 文件（CSS/JS 内联或引用 CDN，容器有明确 height）

# 步骤二：用 build_payload.py 生成 API payload
python3 scripts/build_payload.py create <html_file> [--index N] > payload.json

# 步骤三：调用 API 插入
lark-cli api POST "/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children" \
  --as user --data @payload.json

# 返回的 block_id 用于后续更新/删除
```

`index` 控制插入位置：`0` = 文档开头，`-1` = 末尾（默认），正整数 = 指定子块索引。

---

## 2. 更新 HTML 块（Update）

飞书不支持原地 PATCH AddOns 块。策略是「查位置 → 删旧块 → 同位置新建」：

```bash
# 步骤一：查询旧块在父块中的位置
lark-cli api GET "/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}" --as user
# 从 children 数组中找到目标 block_id 的 index

# 步骤二：删除旧块
lark-cli api DELETE "/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete" \
  --as user --data '{"start_index": <index>, "end_index": <index+1>}'

# 步骤三：在原位置插入新块
python3 scripts/build_payload.py create <new_html_file> --index <原index> > payload.json
lark-cli api POST "/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children" \
  --as user --data @payload.json
```

⚠ 新块 `block_id` 与旧块不同，后续操作需使用返回的新 ID。  
⚠ **先建后删更安全**：新建成功才删旧块，中途失败最多多一块不丢数据。

---

## 3. 读取 HTML 块（Get）

```bash
lark-cli api GET "/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}" --as user \
  --jq '.data.block.add_ons.record'
# 返回 JSON 字符串，再 parse 得到 html 字段
```

提取纯 HTML 到文件：

```bash
lark-cli api GET "/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}" --as user \
  --jq '.data.block.add_ons.record' | python3 -c "
import json, sys
print(json.loads(json.loads(sys.stdin.read()))['html'])
" > output.html
```

---

## 4. 删除 HTML 块（Delete）

```bash
# 先查 index
lark-cli api GET "/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}" --as user \
  --jq '[.data.block.children | to_entries[] | select(.value == "<block_id>") | .key][0]'

# 按 index 批量删除
lark-cli api DELETE "/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete" \
  --as user --data '{"start_index": <index>, "end_index": <index+1>}'
```

---

## 5. 查找文档中所有 HTML 块

```bash
lark-cli api GET "/open-apis/docx/v1/documents/{doc_id}/blocks" \
  --as user --params '{"page_size":500}' \
  --jq '[.data.items[] | select(.block_type==40) | {block_id, record: .add_ons.record}]'
```

---

## 批量操作注意

- 连续多次 create 间加 `sleep 0.5`，否则触发 `99991400` 限流错误
- `lark-cli api --data @file` 只接受**相对路径**，不能用绝对路径
- 单次 payload 建议不超过 500KB（过大可能超时）
