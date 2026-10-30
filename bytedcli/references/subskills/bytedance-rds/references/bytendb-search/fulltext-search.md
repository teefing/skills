# 全文检索

先读取[全文检索产品文档](https://cloud.bytedance.net/docs/rds/docs/6a1d2e22969ba90504ca0eb2/6a7f3ada10b733054d83f7ff)。
以下使用[快速开始](quickstart.md)的示例 schema，其 ANN 索引同时覆盖 `title` 和 `content`。

```sql
SELECT id, title,
       MATCH(title, content) AGAINST('vector') AS text_score
FROM sample_documents
WHERE tenant_id = 1001
  AND MATCH(title, content) AGAINST('vector')
ORDER BY text_score DESC, id ASC
LIMIT 10;
```

`SELECT` 中的 MATCH 返回全文相关性分数，`WHERE` 中的 MATCH 排除未命中的记录。
两处同字段、同词的表达式是同一个逻辑召回；相同查询词检索多个字段时使用一个
`MATCH(col1, col2)`。每个 ANN 全文召回查询块都需有限 `LIMIT`，MATCH 不放在 HAVING 中。

匹配结果取决于分词和检索模式，不承诺文本逐字包含整段查询词，也不预设具体分数。
普通 ANN 全文检索不生成复杂 Boolean Mode；分词、Ngram 或高级语法先核对产品文档。
