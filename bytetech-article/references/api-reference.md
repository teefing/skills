# API 参考文档

## 基础配置

```
BASE_URL = https://bytetech.info
```

所有请求必须携带以下 Header:

- `x-jwt-token: <token>`（通过 skills CLI 获取，见下方说明）
- `Content-Type: application/json`

### 获取 JWT Token

```bash
# 首次登录
npm_config_registry=https://bnpm.byted.org/ npx -y skills@latest login

# 获取 JWT
TOKEN=$(npm_config_registry=https://bnpm.byted.org/ npx -y skills@latest get-jwt)
```

***

## 1. 文章列表 (article\_feed)

获取文章列表，支持按标签筛选、排序。

**路径**: `POST ${BASE_URL}/tech_api/v1/skill/article/feed`

| 参数        | 类型     | 必填 | 说明                 |
| --------- | ------ | -- | ------------------ |
| chanel    | int    | ✅  | `1`=全部文章，`4`=按标签筛选 |
| label\_id | int    | ❌  | 标签ID（见常用标签，仅 `chanel=4` 时需要） |
| sort      | int    | ❌  | `1`=最热(默认)，`2`=最新  |
| cursor    | string | ✅  | 分页游标，首页传 `"0"`     |
| limit     | int    | ❌  | 每页条数，最多10          |

**响应字段**:

| 字段    | jq路径                                 | 类型     | 说明                     |
| ----- | ------------------------------------ | ------ | ---------------------- |
| 文章ID  | `.data[].article_info.article_id`    | string | <br />                 |
| 标题    | `.data[].article_info.title`         | string | <br />                 |
| 简介    | `.data[].article_info.brief`         | string | <br />                 |
| 浏览量   | `.data[].article_info.view_cnt`      | int    | <br />                 |
| 点赞数   | `.data[].article_info.dig_cnt`       | int    | <br />                 |
| 收藏数   | `.data[].article_info.collect_cnt`   | int    | <br />                 |
| 评论数   | `.data[].article_info.comment_count` | int    | 站内评论数                  |
| 创建时间  | `.data[].article_info.ctime`         | int    | Unix时间戳                |
| 作者名   | `.data[].auther.name`                | string | 注意字段名为 auther（已知 typo） |
| 作者邮箱  | `.data[].auther.email`               | string | <br />                 |
| 标签    | `.data[].labels[].name`              | string | <br />                 |
| 分页游标  | `.cursor`                            | string | 用于下一页请求                |
| 是否有更多 | `.has_more`                          | bool   | <br />                 |

***

## 2. 搜索文章 (article\_search)

按关键词搜索文章。

**路径**: `GET ${BASE_URL}/tech_api/v1/skill/search/all`

| 参数       | 类型     | 必填 | 说明            |
| -------- | ------ | -- | ------------- |
| keyword  | string | ✅  | 搜索关键词（需URL编码） |
| id\_type | int    | ❌  | 传 `8` 搜文章（不传则搜全部类型） |

**响应结构**:

```json
{
  "err_no": 0,
  "err_msg": "success",
  "data": {
    "articles": [...],
    "article_count": 19,
    "users": [...],
    "labels": [...],
    "search_id": "xxx"
  },
  "cursor": "0",
  "has_more": false
}
```

**文章字段**:

| 字段   | jq路径                                          | 类型     | 说明                     |
| ---- | --------------------------------------------- | ------ | ---------------------- |
| 文章ID | `.data.articles[].article_info.article_id`    | string | <br />                 |
| 标题   | `.data.articles[].article_info.title`         | string | <br />                 |
| 简介   | `.data.articles[].article_info.brief`         | string | <br />                 |
| 摘要   | `.data.articles[].article_info.summary`       | string | AI生成摘要                 |
| 浏览量  | `.data.articles[].article_info.view_cnt`      | int    | <br />                 |
| 点赞数  | `.data.articles[].article_info.dig_cnt`       | int    | <br />                 |
| 收藏数  | `.data.articles[].article_info.collect_cnt`   | int    | <br />                 |
| 评论数  | `.data.articles[].article_info.comment_count` | int    | <br />                 |
| 创建时间 | `.data.articles[].article_info.ctime`         | int    | Unix时间戳                |
| 作者名  | `.data.articles[].auther.name`                | string | 注意字段名为 auther（已知 typo） |
| 作者邮箱 | `.data.articles[].auther.email`               | string | <br />                 |
| 作者部门 | `.data.articles[].auther.department_name`     | string | <br />                 |
| 标签列表 | `.data.articles[].labels[].name`              | string | <br />                 |

***

## 3. 文章详情 (article\_detail)

获取单篇文章详情。

**路径**: `POST ${BASE_URL}/tech_api/v1/skill/article/detail`

| 参数          | 类型     | 必填 | 说明   |
| ----------- | ------ | -- | ---- |
| article\_id | string | ✅  | 文章ID |

**响应结构**:

```json
{
  "err_no": 0,
  "err_msg": "success",
  "data": {
    "article_info": { ... },
    "auther": { ... },
    "author": { ... },
    "author_infos": [ ... ],
    "labels": [ ... ]
  }
}
```

**文章基础信息** (`.data.article_info`):

| 字段   | 路径                   | 类型     | 说明       |
| ---- | -------------------- | ------ | -------- |
| 文章ID | `.article_id`        | string | <br />   |
| 标题   | `.title`             | string | <br />   |
| 简介   | `.brief`             | string | <br />   |
| 摘要   | `.summary`           | string | 用户填写的摘要  |
| AI摘要 | `.generated_summary` | string | AI自动生成摘要 |
| 浏览量  | `.view_cnt`          | int    | <br />   |
| 点赞数  | `.dig_cnt`           | int    | <br />   |
| 收藏数  | `.collect_cnt`       | int    | <br />   |
| 评论数  | `.comment_count`     | int    | 站内评论数    |
| 创建时间 | `.ctime`             | int64  | Unix时间戳  |

**作者信息** (`.data.author_infos[]`):

| 字段 | 路径                 | 类型     |
| -- | ------------------ | ------ |
| 姓名 | `.name`            | string |
| 邮箱 | `.email`           | string |
| 部门 | `.department_name` | string |

**标签信息** (`.data.labels[]`):

| 字段   | 路径      | 类型     |
| ---- | ------- | ------ |
| 标签ID | `.id`   | int    |
| 标签名  | `.name` | string |

***

## 4. 作者文章 (list\_by\_author)

获取指定作者的文章列表。

> **使用流程**：先通过 `user/search` 搜索作者名，若返回多个同名结果则向用户展示姓名+邮箱列表让用户确认，取确认用户的 `xid` 作为 `author_xid` 参数。推荐优先使用 `search/all` 按作者名搜索。

**路径**: `POST ${BASE_URL}/tech_api/v1/skill/article/list_by_author`

| 参数          | 类型     | 必填 | 说明                                            |
| ----------- | ------ | -- | --------------------------------------------- |
| author\_xid | string | ✅  | 作者的 `xid`（通过 `user/search` 查询，取响应中的 `xid` 字段） |
| item\_type  | number | ✅  | 文章类型传 `8`                                     |
| cursor      | string | ❌  | 分页游标，默认 `"0"`                                 |
| limit       | int    | ✅  | 每页条数，最多10                                     |
| sort\_type  | int    | ✅  | 热门传 `1`（默认），最新传 `6`                           |

**响应结构**:

```json
{
  "err_no": 0,
  "err_msg": "success",
  "data": {
    "BaseResp": { ... },
    "article_infos": [
      {
        "article_info": { ... },
        "auther": { ... },
        "author": { ... },
        "labels": [ ... ]
      }
    ],
    "count": 0,
    "cursor": "1",
    "has_more": false
  }
}
```

**响应字段**:

| 字段    | jq路径                                               | 类型     | 说明                               |
| ----- | -------------------------------------------------- | ------ | -------------------------------- |
| 文章ID  | `.data.article_infos[].article_info.article_id`    | string | <br />                           |
| 标题    | `.data.article_infos[].article_info.title`         | string | <br />                           |
| 浏览量   | `.data.article_infos[].article_info.view_cnt`      | int    | <br />                           |
| 点赞数   | `.data.article_infos[].article_info.dig_cnt`       | int    | <br />                           |
| 评论数   | `.data.article_infos[].article_info.comment_count` | int    | <br />                           |
| 收藏数   | `.data.article_infos[].article_info.collect_cnt`   | int    | <br />                           |
| 作者名   | `.data.article_infos[].auther.name`                | string | 注意：API 字段名为 `auther`（非 `author`） |
| 总数    | `.data.count`                                      | int    | <br />                           |
| 分页游标  | `.data.cursor`                                     | string | 用于下一页请求                          |
| 是否有更多 | `.data.has_more`                                   | bool   | <br />                           |

***

## 5. 团队文章 (list\_by\_team)

获取指定团队的文章列表。

**路径**: `POST ${BASE_URL}/tech_api/v1/skill/article/list_by_team`

| 参数       | 类型     | 必填 | 说明              |
| -------- | ------ | -- | --------------- |
| team\_id | string | ✅  | 团队ID（需先查询，传字符串） |
| cursor   | string | ❌  | 分页游标            |
| limit    | int    | ✅  | 每页条数，最多10       |

**响应字段**（与 article\_feed 结构类似，但字段名有差异）：

> **注意**：此接口的 `auther` 字段为 `null`，作者信息在 `author` 字段中；点赞字段为 `digg_cnt`（非 `dig_cnt`）；评论字段为 `comment_cnt`（非 `comment_count`）。

| 字段    | jq路径                                 | 类型     | 说明                                  |
| ----- | ------------------------------------ | ------ | ----------------------------------- |
| 文章ID  | `.data[].article_info.article_id`    | string |                                     |
| 标题    | `.data[].article_info.title`         | string |                                     |
| 浏览量   | `.data[].article_info.view_cnt`      | int    |                                     |
| 点赞数   | `.data[].article_info.digg_cnt`      | int    | 注意：是 `digg_cnt` 非 `dig_cnt`        |
| 评论数   | `.data[].article_info.comment_cnt`   | int    | 注意：是 `comment_cnt` 非 `comment_count` |
| 收藏数   | `.data[].article_info.collect_cnt`   | int    |                                     |
| 作者名   | `.data[].author.name`                | string | 注意：是 `author` 非 `auther`           |
| 分页游标  | `.cursor`                            | string | 用于下一页请求                             |
| 是否有更多 | `.has_more`                          | bool   |                                     |

***

## 6. 首页榜单文章 (home\_page\_rank)

获取首页的榜单文章（小时榜、周榜）。

**路径**: `POST ${BASE_URL}/tech_api/v1/skill/article/home_page/rank`

| 参数         | 类型  | 必填 | 说明                     |
| ---------- | --- | -- | ---------------------- |
| rank\_type | int | ❌  | 榜单类型，`0`=日榜(默认)，`1`=周榜 |

**响应结构**:

```json
{
  "err_no": 0,
  "err_msg": "success",
  "data": [
    {
      "article_info": { ... },
      "auther": { ... },
      "author": { ... },
      "labels": [ ... ]
    }
  ]
}
```

**文章字段**: 同 `article_feed` 接口的字段（返回一个包含文章对象的数组，没有分页字段）。

***

## 配套查询接口

### 标签查询

**路径**: `GET ${BASE_URL}/tech_api/v1/skill/label/labels?keyword=xxx`

| 字段    | jq路径                 | 类型     | 说明              |
| ----- | -------------------- | ------ | --------------- |
| 标签ID  | `.data[].id`         | int    | 用于 label\_id 参数 |
| 标签名   | `.data[].name`       | string | <br />          |
| 英文名   | `.data[].en_name`    | string | <br />          |
| 父标签ID | `.data[].parent_id`  | int    | 0表示一级标签         |
| 层级    | `.data[].level`      | int    | 1=一级, 2=二级      |
| 文章数   | `.data[].item_count` | int    | <br />          |

### 用户搜索

**路径**: `GET ${BASE_URL}/tech_api/v1/skill/user/search?keyword=xxx`

> **注意**：同名用户可能有多个，需向用户展示姓名+邮箱列表让其确认。确认后取对应用户的 `xid` 字段，用作 `list_by_author` 的 `author_xid` 参数。`user_item_info.article_cnt` 字段不准确（写过文章的作者可能显示为 0），不可作为判断依据。

| 字段  | jq路径                      | 类型     | 说明                                    |
| --- | ------------------------- | ------ | ------------------------------------- |
| xid | `.data[].xid`             | string | 用于 `list_by_author` 的 `author_xid` 参数 |
| 姓名  | `.data[].name`            | string | <br />                                |
| 邮箱  | `.data[].email`           | string | 同名时需向用户确认                             |
| 部门  | `.data[].department_name` | string | <br />                                |
| 头像  | `.data[].avatar`          | string | <br />                                |
| 积分  | `.data[].score`           | int    | 积分/贡献值                                |

### 团队号搜索

**路径**: `POST ${BASE_URL}/tech_api/v1/skill/team_account/search`

| 参数       | 类型     | 必填 | 说明            |
| -------- | ------ | -- | ------------- |
| name     | string | ✅  | 团队名关键词        |
| original | int    | ❌  | `0`=中文，`1`=英文 |
| cursor   | string | ❌  | 分页游标          |
| limit    | int    | ❌  | 每页条数，最多10     |

| 字段   | jq路径                    | 类型     | 说明                               |
| ---- | ----------------------- | ------ | -------------------------------- |
| 团队ID | `.data[].item_id`       | string | 用于 team\_id 参数（注意：字段名是 item\_id） |
| 团队名  | `.data[].name`          | string | <br />                           |
| 英文名  | `.data[].en_name`       | string | <br />                           |
| 简介   | `.data[].description`   | string | <br />                           |
| 关注数  | `.data[].follow_cnt`    | int    | <br />                           |
| 部门ID | `.data[].department_id` | string | <br />                           |

