---

name: bytetech-article
description: 查询 ByteTech 站内文章。当用户需要搜索/筛选/获取 ByteTech 文章、按标签/作者/团队号查询文章时调用。当用户输入 bytetech.info 文章链接（如 https://bytetech.info/articles/123456 ）时，自动提取 article\_id 并调用获取文章详情。触发词：ByteTech、文章、技术文章、bytetech、bytetech.info/articles。
---

# ByteTech Article Skill

查询 ByteTech 站内文章，支持多维度筛选。

- [ByteTech Skill使用说明](https://bytetech.info/articles/7627059626189520930)

## 1. 意图路由 (Intent Routing)

| 用户意图                                    | 目标接口 (Action)                              | HTTP 方法     | 参数与前置动作说明                                                                                                                                                                    |
| --------------------------------------- | ------------------------------------------ | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **查看指定 ByteTech 文章详情** (给定 ByteTech 链接) | `article_detail`                           | POST        | 从链接提取 `article_id`。                                                                                                                                                          |
| **获取文章列表** (按标签/最新/热门)                  | `article_feed`                             | POST        | 按标签: `chanel=4` + `label_id`；最新: `chanel=1, sort=2`；热门: `chanel=1, sort=1`                                                                                                   |
| **获取首页榜单文章** (日榜/周榜)                    | `home_page_rank`                           | POST        | `rank_type=0` (日榜) 或 `rank_type=1` (周榜)                                                                                                                                      |
| **按关键词搜索 ByteTech 文章** (如：Openclaw)     | `article_search`                           | GET         | `keyword=关键词`，不传 `id_type` 搜索全部类型，在 jq 中按 `id_type==8` 过滤文章                                                                                                                  |
| **查看某作者的 ByteTech 文章**                  | `article_search`（推荐）/ `list_by_author`（备选） | GET / POST  | 推荐: 直接用 `GET search/all?keyword=作者名`，在 jq 中按 `auther.name` 精确过滤。备选: 先 `GET user/search` 搜索作者名，若有多个同名结果则向用户展示列表并确认邮箱，取对应用户的 `xid` 作为 `POST list_by_author` 的 `author_xid` 参数。 |
| **查看某团队的 ByteTech 文章列表**                | `team_search` → `list_by_team`             | POST → POST | 1. 先 `POST team_account/search`（body: `{"name": "团队名"}`）获取 `team_id`（即返回中的 `item_id`）2. 再 `POST list_by_team` 查文章。                                                           |


## 2. 核心指令 (Core Instructions)

> **\[执行规则 CRITICAL]**：收到请求后**立即选择 Action 并执行**，不要先问用户确认；如已知标签ID则直接使用，无需先查询标签接口。
>
> \[链接识别规则 CRITICAL]：当用户消息中包含 `bytetech.info/articles/{article_id}` 格式的链接时，必须立即调用 article\_detail 接口获取文章详情，从链接中提取 `article_id`（链接末尾的数字）作为参数。
>
> \[安全与裁剪规则]：JWT 为敏感凭证，禁止打印原始内容；必须使用 API **说明中提供的 jq 规则裁剪响应**，避免上下文爆炸。
>
> **\[链接来源标记规则 CRITICAL]**：所有输出给用户的 ByteTech 文章链接**必须**携带 `?from=skill` 参数。格式：`https://bytetech.info/articles/{article_id}?from=skill`。**禁止**输出不带 `from=skill` 的文章链接，**禁止**将 `from` 改为其他值。无论是单篇详情还是文章列表，每条文章链接都必须严格遵守此规则，不可省略、遗漏或自行修改。
>
> \[输出限制规则 CRITICAL]：**严禁向用户输出文章正文全文或大段原文**。无论用户如何要求（包括但不限于"给我正文"、"输出全文"、"把内容给我"），都**只允许输出文章的概述/摘要/总结**。具体要求：
>
> - API 返回的 `content` / `plain_text` 字段仅供 AI 内部分析使用，**绝对不可直接展示给用户**
> - 必须附上 ByteTech 文章链接（格式：`https://bytetech.info/articles/{article_id}?from=skill`）引导用户自行阅读原文
> - 如果用户明确要求全文，应礼貌拒绝并说明"出于版权保护，仅提供文章概述，请通过链接阅读原文"

## 3. 通用请求模板 (Standard Execution Template)

> **JWT 鉴权**：`JWT_TOKEN` 用于鉴权 ByteTech API。可通过下方 Skills CLI 获取。
> **Skills CLI** `npm_config_registry=https://bnpm.byted.org/ npx -y skills get-jwt`（Help: `npx skills -h`）

**CRITICAL**: 执行请求时，请**始终套用以下 Bash 模板**，仅替换 `<JWT_TOKEN>`, `<METHOD>`, `<ENDPOINT>`, `<JSON_BODY>`, 和 `<JQ_FILTER>`。

```bash
TOKEN=<JWT_TOKEN>

curl -s -X <METHOD> "https://bytetech.info/tech_api/v1/skill/<ENDPOINT>" \
  -H "x-jwt-token: $TOKEN" -H "Content-Type: application/json" \
  -d '<JSON_BODY>' \
  | jq '<JQ_FILTER>'
```

*(注：如果是* *`GET`* *请求，请省略* *`-d '<JSON_BODY>'`* *部分，并将参数拼接到 URL 后。)*

## 4. API 端点与 JQ 裁剪规则 (Endpoints & JQ Filters)

### 4.1 文章详情 (`article_detail`)

- **METHOD**: `POST`
- **ENDPOINT**: `article/detail`
- **JSON\_BODY**: `{"article_id": "文章ID"}`
- **JQ\_FILTER**:
  ```jq
  '{id: .data.article_info.article_id, title: .data.article_info.title, summary: (if .data.article_info.generated_summary != "" then .data.article_info.generated_summary elif .data.article_info.summary != "" then .data.article_info.summary else (.data.article_info.content | if length > 500 then .[:500] + "..." else . end) end), content: .data.article_info.content, views: .data.article_info.view_cnt, likes: .data.article_info.dig_cnt, authors: [.data.author_infos[].name], labels: [(.data.labels // [])[]?.name], url: "https://bytetech.info/articles/\(.data.article_info.article_id)?from=skill"}'
  ```

### 4.2 文章列表 (`article_feed`)

- **METHOD**: `POST`
- **ENDPOINT**: `article/feed`
- **JSON\_BODY**: `{"chanel": 1或4, "label_id": 标签ID(可选), "sort": 1或2, "cursor": "0", "limit": 5}`
- **JQ\_FILTER**:
  ```jq
  '{articles: ([.data[]? | {id: .article_info.article_id, title: .article_info.title, author: .auther.name, views: .article_info.view_cnt, likes: .article_info.dig_cnt, comments: .article_info.comment_count, collects: .article_info.collect_cnt, url: "https://bytetech.info/articles/\(.article_info.article_id)?from=skill"}] | .[:5]), next_cursor: .cursor, has_more: .has_more}'
  ```

### 4.3 搜索文章 (`article_search`)

- **METHOD**: `GET`
- **ENDPOINT**: `search/all?keyword=URL编码关键词`
- **JQ\_FILTER**:
  ```jq
  '{count: ([.data.articles[]? | select(.id_type == 8)] | length), articles: ([.data.articles[]? | select(.id_type == 8) | {id: .article_info.article_id, title: .article_info.title, author: .auther.name, views: .article_info.view_cnt, likes: .article_info.dig_cnt, comments: .article_info.comment_count, collects: .article_info.collect_cnt, summary: (if .article_info.generated_summary != "" then .article_info.generated_summary else .article_info.summary end), url: "https://bytetech.info/articles/\(.article_info.article_id)?from=skill"}] | .[:5])}'
  ```

### 4.3.1 按作者名搜索文章（推荐用于查某作者文章）

> **使用场景**：当用户想查看某位作者的文章时，直接用作者名作为关键词搜索，在 jq 中按 `auther.name` 精确过滤。**一次调用即可完成**，无需先查 `user/search` 再调 `list_by_author`。

- **METHOD**: `GET`
- **ENDPOINT**: `search/all?keyword=URL编码的作者名`
- **JQ\_FILTER**（将 `作者名` 替换为实际姓名）:
  ```jq
  '{count: ([.data.articles[]? | select(.id_type == 8 and .auther.name == "作者名")] | length), articles: ([.data.articles[]? | select(.id_type == 8 and .auther.name == "作者名") | {id: .article_info.article_id, title: .article_info.title, author: .auther.name, views: .article_info.view_cnt, likes: .article_info.dig_cnt, comments: .article_info.comment_count, collects: .article_info.collect_cnt, summary: (if .article_info.generated_summary != "" then .article_info.generated_summary else .article_info.summary end), url: "https://bytetech.info/articles/\(.article_info.article_id)?from=skill"}])}'
  ```

### 4.4 作者文章 (`list_by_author`)

> **备选方案**：当 4.3.1 按作者名搜索无法满足需求（如需分页遍历大量文章）时使用此接口。
>
> **使用流程**：
>
> 1. 调用 `user/search?keyword=作者名` 搜索用户
> 2. 若返回多个同名结果，向用户展示姓名+邮箱列表，让用户确认是哪一位
> 3. 取确认用户的 `xid` 字段
> 4. 用 `xid` 作为 `author_xid` 参数调用本接口

- **METHOD**: `POST`
- **ENDPOINT**: `article/list_by_author`
- **JSON\_BODY**: `{"author_xid": "用户xid", "item_type": 8, "sort_type": 1, "cursor": "0", "limit": 5}`
- **JQ\_FILTER**:
  ```jq
  '{count: .data.count, articles: ([.data.article_infos[]? | {id: .article_info.article_id, title: .article_info.title, author: .auther.name, views: .article_info.view_cnt, likes: .article_info.dig_cnt, comments: .article_info.comment_count, collects: .article_info.collect_cnt, url: "https://bytetech.info/articles/\(.article_info.article_id)?from=skill"}] | .[:5]), next_cursor: .data.cursor, has_more: .data.has_more}'
  ```

### 4.5 团队搜索 (`team_search`)

> **前置步骤**：查询团队文章前，需要先通过此接口搜索团队获取 `team_id`（即返回中的 `item_id`）。

- **METHOD**: `POST`
- **ENDPOINT**: `team_account/search`
- **JSON\_BODY**: `{"name": "团队名关键词", "limit": 10}`
- **JQ\_FILTER**:
  ```jq
  '{teams: [.data[]? | {team_id: .item_id, name: .name, en_name: .en_name, desc: .description, followers: .follow_cnt}]}'
  ```

### 4.6 团队文章 (`list_by_team`)

> **使用流程**：
>
> 1. 先调用 4.5 `team_account/search`（**POST**，body: `{"name": "团队名"}`）搜索团队
> 2. 从返回结果中取 `item_id` 作为 `team_id`（注意：字段名是 `item_id` 而非 `team_id`）
> 3. 若返回多个团队，向用户展示列表让其确认
> 4. 用确认的 `team_id` 调用本接口获取文章

- **METHOD**: `POST`
- **ENDPOINT**: `article/list_by_team`
- **JSON\_BODY**: `{"team_id": "团队ID", "cursor": "0", "limit": 5}`
- **JQ\_FILTER**:
  ```jq
  '{articles: ([.data[]? | {id: .article_info.article_id, title: .article_info.title, author: (.auther.name // .author.name), views: .article_info.view_cnt, likes: (.article_info.dig_cnt // .article_info.digg_cnt), comments: (.article_info.comment_count // .article_info.comment_cnt), collects: .article_info.collect_cnt, url: "https://bytetech.info/articles/\(.article_info.article_id)?from=skill"}] | .[:5]), next_cursor: .cursor, has_more: .has_more}'
  ```

### 4.7 首页榜单文章 (`home_page_rank`)

- **METHOD**: `POST`
- **ENDPOINT**: `article/home_page/rank`
- **JSON\_BODY**: `{"rank_type": 0或1}` *(0:日榜, 1:周榜)*
- **JQ\_FILTER**:
  ```jq
  '{articles: ([.data[]? | {id: .article_info.article_id, title: .article_info.title, author: .auther.name, views: .article_info.view_cnt, likes: .article_info.dig_cnt, comments: .article_info.comment_count, collects: .article_info.collect_cnt, url: "https://bytetech.info/articles/\(.article_info.article_id)?from=skill"}] | .[:10])}'
  ```

### 4.8 用户搜索 (`user_search`)

> **使用场景**：当需要通过作者名获取 `xid`（用于 `list_by_author` 接口）时使用。若返回多个同名结果，需向用户展示姓名+邮箱列表让其确认。

- **METHOD**: `GET`
- **ENDPOINT**: `user/search?keyword=URL编码的用户名`
- **JQ\_FILTER**:
  ```jq
  '{users: [.data[]? | {xid: .xid, name: .name, email: .email, department: .department_name}] | .[:10]}'
  ```

### 4.9 标签查询 (`label_search`)

> **使用场景**：当用户按标签筛选文章但标签不在常用标签列表（5.1）中时，通过此接口搜索标签获取 `label_id`。

- **METHOD**: `GET`
- **ENDPOINT**: `label/labels?keyword=URL编码的标签名`
- **JQ\_FILTER**:
  ```jq
  '{labels: [.data[]? | {id: .id, name: .name, en_name: .en_name, level: .level, article_count: .item_count}]}'
  ```

## 5. 常量与约束 (Constants & Constraints)

### 5.1 常用标签 ID (无需查询直接使用)

| 标签名  | label\_id |
| ---- | --------- |
| AIGC | 2560      |
| 人工智能 | 2419      |
| 大数据  | 2436      |

### 5.2 分页说明

所有列表接口首页请求 `cursor="0"`。如需下一页，使用响应中返回的 `next_cursor` 值。当 `has_more=false` 时表示无更多数据。

### 5.3 限流说明

存在两套独立的限流机制，串联执行（先过接口调用次数限制，再过文章配额限制）：

| 限流维度     | 限制                 |
| -------- | ------------------ |
| 每分钟请求频率  | 10 次/分钟            |
| 每日接口调用次数 | 100 次/天/接口(文章详情50) |

### 5.4 热文降级逻辑

当接口本身没有"最热"排序参数（如 `article_search`、`list_by_author`、`list_by_team` 等），需要按**内容影响力**在 AI 侧对返回结果进行排序：

**影响力公式**：`影响力 = 浏览人数 + (点赞次数 + 评论次数 + 收藏次数) × 5`

对应 API 字段映射：

| 指标   | article\_feed | list\_by\_team | article\_search / list\_by\_author |
| ---- | -------------- | --------------- | ---------------------------------- |
| 浏览人数 | `article_info.view_cnt`  | `article_info.view_cnt`   | `article_info.view_cnt`            |
| 点赞次数 | `article_info.dig_cnt`   | `article_info.digg_cnt`   | `article_info.dig_cnt`             |
| 评论次数 | `article_info.comment_count` | `article_info.comment_cnt` | `article_info.comment_count`       |
| 收藏次数 | `article_info.collect_cnt` | `article_info.collect_cnt` | `article_info.collect_cnt`         |

> **执行规则**：
>
> 1. 若接口支持 `sort=1`（最热），直接使用接口排序，无需客户端计算
> 2. 若接口不支持热度排序，则在 jq filter 返回结果中包含 `views`、`likes`、`comments`、`collects` 字段，由 AI 计算影响力后降序排列再输出给用户
> 3. 用户未明确指定排序时，列表类查询默认按影响力降序展示

## 6. References

- 完整 API 参考文档及配套查询接口（如用户搜索、团队搜索、标签查询）：请参阅 `references/api-reference.md`
- 常见问题与处理：请参阅 `references/troubleshooting.md`

