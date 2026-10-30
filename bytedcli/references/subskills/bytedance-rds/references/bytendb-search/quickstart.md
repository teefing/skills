# 首次接入

先读取[快速开始产品文档](https://cloud.bytedance.net/docs/rds/docs/6a1d2e22969ba90504ca0eb2/6a7f3863fc4c5a052788c528)，
架构和异步同步原理见[技术介绍](https://cloud.bytedance.net/docs/rds/docs/6a1d2e22969ba90504ca0eb2/6a7f3a73daf6e8052ef523c0)。
文档中的共享库是特定体验环境，不作为业务接入的默认目标。

确认用户选择的实例已开通 Search，取得所需数据库权限，再生成变更工单 SQL。
新建表、修改表、建索引与写入测试数据遵循目标库的 DDL/DML 工单流程。
未开通时按产品文档申请版本升级及功能开通，不通过本指南直接更改实例。

以下示例表名、维度、距离及过滤字段均为示例，按业务需求替换。
`tenant_id` 演示租户过滤，在每路召回中均需保留。

```sql
CREATE TABLE sample_documents (
  id BIGINT NOT NULL PRIMARY KEY,
  tenant_id BIGINT NOT NULL,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  category VARCHAR(64) NOT NULL,
  embedding VECTOR(4) NOT NULL,
  ANN INDEX idx_search (embedding, title, content)
    SECONDARY_ENGINE_ATTRIBUTE =
      '{"distance":"cosine","scalar_fields":"tenant_id,category"}'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO sample_documents
  (id, tenant_id, title, content, category, embedding)
VALUES
  (1, 1001, '混合检索入门', 'Hybrid search combines vector and full-text retrieval.',
   'search', TO_VECTOR('[1.0,0.0,0.0,0.0]')),
  (2, 1001, '向量检索', 'Vector retrieval finds semantically similar documents.',
   'search', TO_VECTOR('[0.95,0.05,0.0,0.0]'));
```

索引与 DML 异步同步。下列查询中的库名也须替换为实际库名；目标库 Owner 可用
`INDEX_ROWS` 观察同步进度，无需 `PROCESS` 权限。

```sql
SELECT DATABASE_NAME, TABLE_NAME, INDEX_NAME, INDEX_ROWS
FROM INFORMATION_SCHEMA.VECTOR_INDEXES
WHERE DATABASE_NAME = 'demo_db'
  AND TABLE_NAME = 'sample_documents'
  AND INDEX_NAME = 'idx_search';

SELECT id, title,
       COSINE_DISTANCE(embedding, TO_VECTOR('[1.0,0.0,0.0,0.0]')) AS distance
FROM sample_documents
WHERE tenant_id = 1001
ORDER BY distance ASC
LIMIT 5;
```

这里只检查查询形态、维度和排序方向，不承诺具体分数或写后立即可见。
使用现有 RDS/DB 命令检查实例和 schema；确认索引与字段配置后，再进行已授权的只读验证。

通过 CLI 查看执行计划时，使用门禁允许的 `EXPLAIN SELECT`：

```sql
EXPLAIN SELECT id, title
FROM sample_documents
WHERE tenant_id = 1001
ORDER BY COSINE_DISTANCE(embedding, TO_VECTOR('[1.0,0.0,0.0,0.0]')) ASC
LIMIT 5;
```

检查 `Extra` 中是否出现 `Using ANN Search`。树形的 `EXPLAIN FORMAT=TREE` 需要由用户
在自己已授权的 MySQL 客户端执行，不能提交给当前 CLI 的只读 SQL 入口。
