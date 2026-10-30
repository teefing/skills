---
name: merlin-eval-data-upload
description: 使用 v4 DataCard 上传任务导入 HDFS 数据和 LarkSheet；用户需要注册评估集、导入数据表、查看上传任务状态或配置 tag 列时使用。HDFS 与 LarkSheet 来源分别填写对应 upload_config 子对象，先查看当前 schema。
---

# 上传评估数据

使用 DataCard v4 上传任务导入 HDFS 数据或飞书表格。先检查当前 schema；`datacard_name` 是完整的 `catalog.database.table`，不是单独的表名。

```bash
bytedcli merlin data datacard-upload-jobs create --schema
# 预览注册一组已有 Parquet 文件
bytedcli merlin data datacard-upload-jobs create --datacard-name seed.demo_database.demo_table --mode register --write-mode create --register-config '{"file_format":"parquet","hdfs_paths":["hdfs://example-cluster/demo/data"]}' --dry-run
# 使用实际资源参数并获得提交授权后，去掉 --dry-run 执行同一请求
# 用创建结果中的任务 SID 查状态
bytedcli merlin data datacard-upload-jobs get --sid demo-upload-job
bytedcli merlin data datacard-upload-jobs list --datacard-name seed.demo_database.demo_table --page-size 20
```

`mode=register` 的业务参数放在 `register_config`；`mode=upload` 的来源配置放在 `upload_config`。HDFS、DataCard 和 LarkSheet 的结构不同，按 schema 的 `source_type` 和对应子对象填写，不沿用旧的顶层 `file_config`。`write_mode=create` 创建数据；`append`、`overwrite` 会修改已有数据，执行前核对目标和写入语义。

任务创建成功不等于导入完成。读取任务状态和失败信息，完成后再读取 DataCard 的 schema、snapshot 和预览。网络超时后先查询已有任务，避免重复提交。

```bash
bytedcli merlin data get-detail --schema
bytedcli merlin data get-data-preview --schema
```

旧的 `data upload/get-job/list-jobs` 是独立工具的本地包装流程，不是远端 MCP 工具；使用上述 v4 上传任务入口。
