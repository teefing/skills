# 混合检索

先读取[混合检索产品文档](https://cloud.bytedance.net/docs/rds/docs/6a1d2e22969ba90504ca0eb2/6a7f3afcf4918e053e42b40e)。
以下使用[快速开始](quickstart.md)的示例 schema。

## 全文过滤向量召回

```sql
SELECT id, title,
       COSINE_DISTANCE(embedding, TO_VECTOR('[1.0,0.0,0.0,0.0]')) AS distance
FROM sample_documents
WHERE tenant_id = 1001 AND category = 'search'
  AND MATCH(title, content) AGAINST('vector')
ORDER BY distance ASC
LIMIT 10;
```

这是过滤式混合：MATCH 是硬过滤条件，最终只按向量距离排序，不融合全文分数。

## 两路召回后做 RRF

需要同时保留关键词和语义候选时，独立执行有限的全文、向量召回，再由 SQL 融合。
当前 CLI 的只读门禁拒绝以 `WITH` 开头的 CTE。以下完整 SQL 模板供用户在自己已授权的
MySQL 客户端执行；不要直接提交给 `rds db query` / `db sql execute`，也不要由 Agent
自动切换执行入口。若需通过 CLI 验证，可分别执行两路有限的 SELECT 观察候选结果。

```sql
WITH text_recall AS (
  SELECT id, MATCH(title, content) AGAINST('vector') AS score
  FROM sample_documents
  WHERE tenant_id = 1001 AND category = 'search'
    AND MATCH(title, content) AGAINST('vector')
  ORDER BY score DESC, id ASC
  LIMIT 100
), vector_recall AS (
  SELECT id,
         COSINE_DISTANCE(embedding, TO_VECTOR('[1.0,0.0,0.0,0.0]')) AS distance
  FROM sample_documents
  WHERE tenant_id = 1001 AND category = 'search'
  ORDER BY distance ASC, id ASC
  LIMIT 100
), text_ranked AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY score DESC, id ASC) AS recall_rank
  FROM text_recall
), vector_ranked AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY distance ASC, id ASC) AS recall_rank
  FROM vector_recall
), candidates AS (
  SELECT id, 1.0 / (60 + recall_rank) AS contribution FROM text_ranked
  UNION ALL
  SELECT id, 1.0 / (60 + recall_rank) AS contribution FROM vector_ranked
)
SELECT id, SUM(contribution) AS fusion_score
FROM candidates
GROUP BY id
ORDER BY fusion_score DESC, id ASC
LIMIT 10;
```

`100`、`60`、`10` 是两路 Top-K、RRF 常量和最终返回量的示例，应按业务调整。
两路必须重复租户、ACL、状态及时间等全部约束，不能只在最终结果中补过滤。
`UNION ALL` 保留单路候选，按主键聚合后再稳定排序。

需要加权融合时，先统一分数方向：全文分数做归一化，向量距离按文档支持的
`SIMILARITY(distance)` 转为相似度，再按明确权重计算。Min-Max 归一化须处理
最大值等于最小值的情况。不要直接相加原始全文分数与向量距离。
