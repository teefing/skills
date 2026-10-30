# 向量、Embedding 与过滤

先读取[向量相似度检索产品文档](https://cloud.bytedance.net/docs/rds/docs/6a1d2e22969ba90504ca0eb2/6a7f3aa110b733054d83f69a)。
以下使用[快速开始](quickstart.md)的示例 schema。

```sql
SELECT id, title,
       COSINE_DISTANCE(embedding, TO_VECTOR('[1.0,0.0,0.0,0.0]')) AS distance
FROM sample_documents
WHERE tenant_id = 1001 AND category = 'search'
ORDER BY distance ASC
LIMIT 10;
```

检查 `VECTOR(N)`、查询向量与模型输出维度一致，以及查询距离与索引配置一致。
`tenant_id`、`category` 在 `scalar_fields` 中才能作为高频条件下推。

## Embedding

`TO_EMBEDDING(model_alias, input, input_type)` 使用目标实例已注册的模型 alias。
先确认 alias、输入类型、模型输出维度和目标索引距离，不假设某个内置模型在所有实例可用。
例如已确认 `sample_embedding` 接受 `unimodal_text` 时，可生成：

```sql
SELECT TO_EMBEDDING('sample_embedding', '数据库索引', 'unimodal_text');
```

本例 alias 为占位值。将 Embedding 用于写入或查询前，向量列维度必须与实际模型一致；
快速开始的四维样例不能直接用于任意模型输出。使用预先生成的向量同样可做语义检索。
注册模型由目标库的接入流程处理，SQL、工单、日志和对话中不要输出真实 API Key。
`EMBEDDING_PIPELINE` 仅在相应索引已配置 `emb_pipeline` 时按产品文档生成。

## Post Filter 与 JSON

`LIKE` 等不能下推的条件需要明确启用 Post Filter。当前 CLI 的只读门禁拒绝 `SET SESSION`，
且多次 CLI 调用不保证共享会话。以下 SQL 供用户在自己已授权的 MySQL 客户端同一会话中
依次执行；不要把设置语句提交给 `rds db query` / `db sql execute`，也不要由 Agent 自动
切换其他执行入口。

```sql
SET SESSION vedb_fusion_search_post_filter_enabled = ON;

SELECT id, title
FROM sample_documents
WHERE tenant_id = 1001 AND content LIKE '%vector%'
ORDER BY COSINE_DISTANCE(embedding, TO_VECTOR('[1.0,0.0,0.0,0.0]')) ASC
LIMIT 10;
```

Post Filter 在 ANN 候选召回后执行，返回数量可能小于 `LIMIT`。高频过滤优先配置为标量下推。
JSON 全文优先使用生成文本列；`$[*]` 标量数组过滤和 `json_nested_columns` 嵌套检索
使用产品文档各自定义的配置，不把它们当作任意 JSON 路径能力。
