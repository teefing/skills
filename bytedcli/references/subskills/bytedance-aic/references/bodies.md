# AIC JSON 请求体

使用 `--body` 或 `--body-file` 二选一。字段名保持 Swagger 的 wire format，已声明的类型、枚举和必填字段会在请求前校验；Swagger 未描述的扩展字段透传。

## `cluster create`

必填字段：`cluster`、`psm_parent_id`。

字段：`business_list`、`cluster`、`description`、`level`、`owner`、`owner_list`、`psm`、`psm_id`、`psm_parent_id`、`psm_parent_path`、`service_account`。

## `devbox android create`

必填字段：`amount`、`spec_name`。

字段：`amount`、`spec_alias`、`spec_description`、`spec_id`、`spec_idc_region`、`spec_name`。

## `android create`

必填字段：`amount`、`emulator_type`、`gpu`、`name`。

字段：`abi`、`amount`、`annotations`、`api_level`、`cpu`、`creator`、`custom_meta_info`、`device`、`dpi`、`emulator_type`、`enable_cpu_render`、`enable_migration`、`enable_preload`、`enable_remote_gpu`、`fps`、`gpu`、`idc`、`image_tag`、`internal_storage_size`、`migration_cluster`、`migration_source`、`name`、`plan`、`ram_size`、`resolution_height`、`resolution_width`、`sd_size`、`userimage`、`vcpu`、`vm_heap_size`。

## `permission delete`

必填字段：Swagger 未声明字段级必填项。

角色成员请求体为 `{ "角色名": ["成员名"] }`。

## `permission member create`

必填字段：Swagger 未声明字段级必填项。

角色成员请求体为 `{ "角色名": ["成员名"] }`。

## `permission update`

必填字段：Swagger 未声明字段级必填项。

角色成员请求体为 `{ "角色名": ["成员名"] }`。

## `emulator batch delete`

必填字段：Swagger 未声明字段级必填项。

字段：`emulators`。

## `binding create`

必填字段：Swagger 未声明字段级必填项。

字段：`cluster`、`emulator`、`game_id`、`namespace`、`user_id`。

## `cluster stock get`

必填字段：Swagger 未声明字段级必填项。

字段：`cpu`、`disk`、`emulator_type`、`fps`、`gpu`、`idc`、`memory`、`mode`、`plan`、`resolution_height`、`resolution_width`。

## `disk delete`

请求体为字符串数组。



## `disk create`

必填字段：`alias`、`capacity`、`deploy_dc_id`、`type`。

字段：`alias`、`capacity`、`deploy_dc_id`、`description`、`type`。

## `disk update`

必填字段：`alias`、`capacity`、`deploy_dc_id`、`type`。

字段：`alias`、`capacity`、`deploy_dc_id`、`description`、`type`。

## `emulator create`

必填字段：`amount`、`emulator_type`、`gpu`、`name`。

字段：`abi`、`amount`、`annotations`、`api_level`、`cpu`、`creator`、`custom_meta_info`、`device`、`dpi`、`emulator_type`、`enable_cpu_render`、`enable_migration`、`enable_preload`、`enable_remote_gpu`、`fps`、`gpu`、`idc`、`image_tag`、`internal_storage_size`、`migration_cluster`、`migration_source`、`name`、`plan`、`ram_size`、`resolution_height`、`resolution_width`、`sd_size`、`userimage`、`vcpu`、`vm_heap_size`。

## `emulator replica create`

必填字段：`replicas_name`、`replicas_number`。

字段：`password`、`replicas_name`、`replicas_number`。

## `emulator execute`

必填字段：`command`。

字段：`command`、`container`、`env`、`sync`（boolean，可选）。SG 默认异步；`sync: true` 请求同步返回。异步响应的 `task_id` / `task_status` 表示任务状态，不代表命令已完成。

## `emulator migration execute`

必填字段：`migrate_mode`。

字段：`migrate_mode`、`schedule_idc`、`schedule_node`。

## `emulator qga execute`

必填字段：`command`。

字段：`command`、`container`、`domain`、`env`、`shell`。

## `emulator qga-script execute`

必填字段：`script`。

字段：`container`、`domain`、`env`、`params`、`script`、`shell`。

## `emulator reset execute`

必填字段：Swagger 未声明字段级必填项。

字段：`autostart`、`force`。

## `emulator update`

必填字段：Swagger 未声明字段级必填项。

字段：`annotations`、`custom_meta_info`、`image_tag`。

## `linux create`

必填字段：`amount`、`emulator_type`、`gpu`、`name`、`password`、`system_disk_size`。

字段：`amount`、`annotations`、`cloud_disk_list`、`cpu`、`creator`、`custom_meta_info`、`emulator_type`、`enable_migration`、`enable_vnc`、`gpu`、`idc`、`image_tag`、`migration_cluster`、`migration_source`、`name`、`num_of_gpu`、`password`、`plan`、`ram_size`、`system_disk_size`、`user_disk_list`、`user_disk_mode`、`user_disk_size`、`userimage`、`vcpu`。

## `mac create`

必填字段：`amount`、`emulator_type`、`gpu`、`name`、`password`、`system_disk_size`。

字段：`amount`、`annotations`、`cloud_disk_list`、`cpu`、`creator`、`custom_meta_info`、`emulator_type`、`enable_migration`、`enable_vnc`、`gpu`、`idc`、`image_tag`、`migration_cluster`、`migration_source`、`name`、`num_of_gpu`、`password`、`plan`、`ram_size`、`system_disk_size`、`user_disk_list`、`user_disk_mode`、`user_disk_size`、`userimage`、`vcpu`。

## `cluster secret update`

必填字段：`access_key`、`secret_key`。

字段：`access_key`、`secret_key`。

## `cluster service-account update`

必填字段：`service_account`。

字段：`service_account`。

## `image delete`

请求体为字符串数组。



## `image create`

必填字段：`emulator`。

字段：`alias`、`description`、`emulator`、`flatten`、`overlay`、`type`。

## `image update`

必填字段：Swagger 未声明字段级必填项。

字段：`clusterName`、`creationTimestamp`、`name`、`namespace`、`spec`、`status`。

## `virtualphone create`

必填字段：`amount`、`emulator_type`、`gpu`、`name`。

字段：`abi`、`amount`、`annotations`、`api_level`、`cpu`、`creator`、`custom_meta_info`、`device`、`dpi`、`emulator_type`、`enable_cpu_render`、`enable_migration`、`enable_preload`、`enable_remote_gpu`、`fps`、`gpu`、`idc`、`image_tag`、`internal_storage_size`、`migration_cluster`、`migration_source`、`name`、`plan`、`ram_size`、`resolution_height`、`resolution_width`、`sd_size`、`userimage`、`vcpu`、`vm_heap_size`。

## `windows create`

必填字段：`amount`、`emulator_type`、`gpu`、`name`、`password`、`system_disk_size`。

字段：`amount`、`annotations`、`cloud_disk_list`、`cpu`、`creator`、`custom_meta_info`、`emulator_type`、`enable_migration`、`enable_vnc`、`gpu`、`idc`、`image_tag`、`migration_cluster`、`migration_source`、`name`、`num_of_gpu`、`password`、`plan`、`ram_size`、`system_disk_size`、`user_disk_list`、`user_disk_mode`、`user_disk_size`、`userimage`、`vcpu`。
