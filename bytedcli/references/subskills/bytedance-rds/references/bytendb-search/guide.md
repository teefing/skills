# ByteNDB Search

ByteNDB Search 在支持该能力的 ByteNDB 实例上，通过 SQL 提供向量相似度、全文和混合检索，
可用于语义搜索及 RAG 知识库。FusionSearch / hybrid_search 是相关实现名称。

本指南提供接入指导、生成和校验 SQL；实例发现、schema 和已授权的只读查询使用现有
`bytedcli rds` 或 `bytedcli db` 命令。`rds db search` 和 `db search` 搜索数据库实例，
表内语义检索通过 SQL 表达。

## 按意图加载

根据当前任务只读取必要参考：

| 意图 | 参考 |
| --- | --- |
| 能力发现、实例条件、首次建表与写入 | [快速开始](quickstart.md) |
| 向量距离、Embedding、标量过滤、Post Filter、JSON | [向量检索](vector-search.md) |
| MATCH AGAINST、分词、全文评分 | [全文检索](fulltext-search.md) |
| 全文过滤向量、双路召回、RRF、加权融合 | [混合检索](hybrid-search.md) |

本指南及参考均随 RDS、DB Skill 分发；已安装时直接读取相对路径，
也可按所属领域 Skill 中的 `bytedcli self skill get` 示例按需读取。

## 先确认实例条件

区分产品支持与目标实例已开通：确认实例、站点/地域、ByteNDB 版本、功能配置及表索引。
不能仅因 SQL 兼容 MySQL、命令能执行 SQL 或已经读取本指南，就判断目标实例支持 Search。
可用区域与开通流程以[快速开始产品文档](https://cloud.bytedance.net/docs/rds/docs/6a1d2e22969ba90504ca0eb2/6a7f3863fc4c5a052788c528)为准；
无法取得部署信息时，明确标记“目标实例能力未确认”。不默认选择生产库或共享体验库。

收集新表/存量表、主键、向量来源与维度、距离类型、全文字段、过滤字段、每路 Top-K，
以及租户、ACL、状态、时间等必要条件。复用用户已提供的信息；缺失且影响结果时再询问，
可以合理假设时标明假设并给出模板。

## 选择查询形态

| 需求 | 查询形态 | 排序 |
| --- | --- | --- |
| 语义相似数据 | 向量 Top-K | 距离升序或相似度降序 |
| 关键词相关数据 | 全文 Top-K | MATCH 分数降序 |
| 必须命中关键词，再比较语义 | 同一查询块中的 MATCH 硬过滤 + 向量 Top-K | 向量距离/相似度 |
| 同时保留关键词与语义候选 | 两个独立且有限的召回分支，再做 SQL 融合 | RRF 或归一化加权 |

## SQL 约束

生成 SQL 前，按所选参考读取对应产品文档。不要根据原生 MySQL、ByteES 或其他向量
数据库类推未确认的语法。生成后检查：

1. 使用 InnoDB 表和主键；一张表只创建一个 Vector/ANN 索引，覆盖向量及所需全文字段。
2. `VECTOR(N)`、写入/查询向量、Embedding 输出维度一致；可执行向量中不用 `...`。
3. 距离与索引一致：`cosine` / `COSINE_DISTANCE`、`l2` / `L2_DISTANCE`、`ip` / `INNER_PRODUCT`。
   原始距离升序；受支持的 `SIMILARITY(distance)` 降序。
4. 每个 ANN 向量或全文召回查询块都带有限 `LIMIT`；每块只有一个逻辑 ANN `MATCH`，
   相同查询词检索多个字段用 `MATCH(col1, col2)`。ANN `MATCH` 放在 `WHERE` 中。
5. 全文检索字段必须被 ANN 索引覆盖；下推过滤字段配置在 `scalar_fields` 中，不重复配置主键。
   不能下推的表达式仅在明确启用 Post Filter 后生成，并说明结果可能不足 `LIMIT`。
6. 同块 `MATCH` + 向量排序是过滤式混合，不贡献第二路全文分数。分数融合使用独立召回分支，
   各自设置 `LIMIT`、重复全部安全和业务过滤条件，以 `UNION ALL` 保留单路候选，再按主键聚合。
7. 不直接相加原始全文分数和向量距离；先统一分数方向并归一化，或用 RRF。
8. 普通 ANN 全文检索不生成复杂 Boolean Mode 语法；JSON 标量数组 `$[*]` 是单独的受限能力。
   JSON 全文优先生成文本列；嵌套对象数组仅使用产品文档确认的 `json_nested_columns` 结构。
9. `TO_EMBEDDING` 优先使用目标实例已注册的模型 alias，示例使用占位 alias，不输出真实 Key。
   `EMBEDDING_PIPELINE` 必须配套 ANN 索引的 `emb_pipeline`，不作为普通独立函数生成。
10. 索引与 DML 异步同步，写后不保证立即可检索。可查询
    `INFORMATION_SCHEMA.VECTOR_INDEXES.INDEX_ROWS` 观察进度；结果不完整时先检查同步状态。

## 返回与排查

按用户请求给出必要的 DDL、DML、查询或执行计划 SQL，说明召回、过滤和排序语义。
不直接执行生产 DDL/DML，也不代办权限、升级实例、注册模型或管理 ByteES 集群。
需要实际只读验证时，沿用当前 RDS/DB 命令的鉴权、参数与 SQL 校验规则；先查看对应 `--help`。
当前 CLI 的只读门禁允许单条 SELECT、SHOW TABLES、SHOW CREATE TABLE 和 `EXPLAIN SELECT`，
不接受 `EXPLAIN FORMAT=TREE`、`SET SESSION` 或以 `WITH` 开头的 CTE。
通过 CLI 排查时使用 `EXPLAIN SELECT ...`。需要树形计划、Post Filter 会话开关或完整 CTE
融合模板时，提供 SQL 供用户在自己已授权的 MySQL 客户端执行；会话设置和依赖它的查询须
在同一客户端会话中完成，不由 Agent 自动切换执行入口，也不假设跨 CLI 调用保留会话。

查询未下推时，先在 CLI 的 `EXPLAIN SELECT` 结果中检查 `Using ANN Search`；需要查看
`VECTOR_ENGINE` 等树形节点时，由用户在自己的 MySQL 客户端运行 `EXPLAIN FORMAT=TREE`。
同时检查索引字段、距离、过滤字段和 `LIMIT`。错误码与错误原文以实际返回为准。
