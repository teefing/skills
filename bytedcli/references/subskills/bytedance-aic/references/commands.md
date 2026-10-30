# AIC 命令与接口映射

支持 `--site cn|i18n|i18n-bd|boe`。API 与认证按站点映射匹配；所有 selector 都使用 option。分页默认 `--page 1 --page-size 20`，`--page-size` 映射后端 `limit`。

分页结果返回 `page` / `page_size`；后端未返回总数时提供 `current_count`，不推算 `total`。`devbox spec list` 支持规格数组，空绑定列表规范为 `items: []`。

| 命令（前缀 `bytedcli aic`） | API | 行为 | 参数 |
| --- | --- | --- | --- |
| `idc get` | `GET /aicadb/idc/{idc}` | 只读 | `--idc`（必填） |
| `cluster list` | `GET /cluster` | 只读 | `--username`、`--followed`（boolean；仅订阅集群） |
| `cluster create` | `POST /cluster` | 预览/`--yes` | —；`--body` / `--body-file` |
| `devbox android list` | `GET /cluster/devbox/android` | 只读 | `--page`、`--page-size` |
| `devbox android create` | `POST /cluster/devbox/android` | 预览/`--yes` | —；`--body` / `--body-file` |
| `devbox spec list` | `GET /cluster/devbox/spec` | 只读 | `--mode`（必填，android/windows） |
| `devbox windows list` | `GET /cluster/devbox/windows` | 只读 | `--page`、`--page-size` |
| `cluster get` | `GET /cluster/{cluster}` | 只读 | `--cluster`（必填） |
| `cluster delete` | `DELETE /cluster/{cluster}/` | 预览/`--yes` | `--cluster`（必填） |
| `android create` | `POST /cluster/{cluster}/android` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `android get` | `GET /cluster/{cluster}/android/{emulator}/` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `permission apply-url get` | `GET /cluster/{cluster}/apply` | 只读 | `--cluster`（必填） |
| `permission delete` | `DELETE /cluster/{cluster}/authentication` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `permission get` | `GET /cluster/{cluster}/authentication` | 只读 | `--cluster`（必填） |
| `permission member create` | `POST /cluster/{cluster}/authentication` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `permission update` | `PUT /cluster/{cluster}/authentication` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `emulator batch delete` | `POST /cluster/{cluster}/batch_delete` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `binding list` | `GET /cluster/{cluster}/bindings` | 只读 | `--cluster`（必填） |
| `binding create` | `POST /cluster/{cluster}/bindings` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `binding delete` | `DELETE /cluster/{cluster}/bindings/` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填） |
| `binding get` | `GET /cluster/{cluster}/bindings/` | 只读 | `--cluster`（必填）、`--emulator`（必填）、`--user-id`、`--game-id` |
| `cluster stock get` | `POST /cluster/{cluster}/check_stock` | 只读 | `--cluster`（必填）；`--body` / `--body-file` |
| `disk delete` | `DELETE /cluster/{cluster}/clouddisk` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `disk list` | `GET /cluster/{cluster}/clouddisk` | 只读 | `--cluster`（必填）、`--page`、`--page-size` |
| `disk create` | `POST /cluster/{cluster}/clouddisk` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `disk get` | `GET /cluster/{cluster}/clouddisk/{name}` | 只读 | `--cluster`（必填）、`--name`（必填） |
| `disk update` | `PUT /cluster/{cluster}/clouddisk/{name}` | 预览/`--yes` | `--cluster`（必填）、`--name`（必填）；`--body` / `--body-file` |
| `emulator create` | `POST /cluster/{cluster}/emulator` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `emulator delete` | `DELETE /cluster/{cluster}/emulator/{emulator}/` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填） |
| `emulator get` | `GET /cluster/{cluster}/emulator/{emulator}/` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator webshell list` | `GET /cluster/{cluster}/emulator/{emulator}/all_webshell` | 只读 | `--cluster`（必填）、`--emulator`（必填）、`--username`（必填） |
| `emulator connection-check get` | `GET /cluster/{cluster}/emulator/{emulator}/connection_check` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator container list` | `GET /cluster/{cluster}/emulator/{emulator}/container` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator container-shell get` | `GET /cluster/{cluster}/emulator/{emulator}/container_shell/{container}` | 只读 | `--cluster`（必填）、`--emulator`（必填）、`--container`（必填） |
| `emulator replica create` | `PUT /cluster/{cluster}/emulator/{emulator}/duplicate` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填）；`--body` / `--body-file` |
| `emulator error-log get` | `GET /cluster/{cluster}/emulator/{emulator}/error_log` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator execute` | `POST /cluster/{cluster}/emulator/{emulator}/exec` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填）；`--body` / `--body-file` |
| `emulator host-monitor get` | `GET /cluster/{cluster}/emulator/{emulator}/host_monitor` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator account get` | `GET /cluster/{cluster}/emulator/{emulator}/init_account` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator log get` | `GET /cluster/{cluster}/emulator/{emulator}/log` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator migration execute` | `PUT /cluster/{cluster}/emulator/{emulator}/migrate` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填）；`--body` / `--body-file` |
| `emulator monitor get` | `GET /cluster/{cluster}/emulator/{emulator}/monitor` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator permission get` | `GET /cluster/{cluster}/emulator/{emulator}/permissions` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator qga execute` | `POST /cluster/{cluster}/emulator/{emulator}/qga_exec` | 预览/`--yes`，SG 不支持 | `--cluster`（必填）、`--emulator`（必填）；`--body` / `--body-file` |
| `emulator qga-script execute` | `POST /cluster/{cluster}/emulator/{emulator}/qga_script_exec` | 预览/`--yes`，SG 不支持 | `--cluster`（必填）、`--emulator`（必填）；`--body` / `--body-file` |
| `emulator rdp get` | `GET /cluster/{cluster}/emulator/{emulator}/rdp` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator reboot execute` | `PUT /cluster/{cluster}/emulator/{emulator}/reboot` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填） |
| `emulator reset execute` | `PUT /cluster/{cluster}/emulator/{emulator}/reset` | 预览/`--yes`，SG 不支持 | `--cluster`（必填）、`--emulator`（必填）；`--body` / `--body-file` |
| `emulator power-on execute` | `PUT /cluster/{cluster}/emulator/{emulator}/start` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填） |
| `emulator status get` | `GET /cluster/{cluster}/emulator/{emulator}/status` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `emulator power-off execute` | `PUT /cluster/{cluster}/emulator/{emulator}/stop` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填） |
| `emulator update` | `PUT /cluster/{cluster}/emulator/{emulator}/update` | 预览/`--yes` | `--cluster`（必填）、`--emulator`（必填）；`--body` / `--body-file` |
| `emulator vnc get` | `GET /cluster/{cluster}/emulator/{emulator}/vnc` | 只读 | `--cluster`（必填）、`--emulator`（必填）、`--username` |
| `emulator webshell get` | `GET /cluster/{cluster}/emulator/{emulator}/webshell` | 只读 | `--cluster`（必填）、`--emulator`（必填）、`--username`（必填） |
| `emulator list` | `GET /cluster/{cluster}/emulators` | 只读 | `--cluster`（必填）、`--page`、`--page-size` |
| `cluster subscription create` | `PUT /cluster/{cluster}/follow` | 预览/`--yes` | `--cluster`（必填） |
| `binding status get` | `GET /cluster/{cluster}/has_binding/` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `cluster health get` | `GET /cluster/{cluster}/health_check` | 只读 | `--cluster`（必填） |
| `linux create` | `POST /cluster/{cluster}/linux` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `mac create` | `POST /cluster/{cluster}/mac` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `cluster monitor get` | `GET /cluster/{cluster}/monitor` | 只读 | `--cluster`（必填） |
| `public-image list` | `GET /cluster/{cluster}/publicimage` | 只读，SG 不支持 | `--cluster`（必填）、`--type`（windows/android/linux/mac） |
| `cluster secret get` | `GET /cluster/{cluster}/secret` | 只读 | `--cluster`（必填） |
| `cluster secret update` | `PUT /cluster/{cluster}/secret` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `cluster service-account update` | `PUT /cluster/{cluster}/service_account` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `cluster subscription delete` | `PUT /cluster/{cluster}/unfollow` | 预览/`--yes` | `--cluster`（必填） |
| `image delete` | `DELETE /cluster/{cluster}/userimage` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `image list` | `GET /cluster/{cluster}/userimage` | 只读 | `--cluster`（必填）、`--page`、`--page-size` |
| `image create` | `POST /cluster/{cluster}/userimage` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `image get` | `GET /cluster/{cluster}/userimage/{name}` | 只读 | `--cluster`（必填）、`--name`（必填） |
| `image update` | `PUT /cluster/{cluster}/userimage/{name}` | 预览/`--yes` | `--cluster`（必填）、`--name`（必填）；`--body` / `--body-file` |
| `image task-log get` | `GET /cluster/{cluster}/userimage_task_log/{taskid}` | 只读 | `--cluster`（必填）、`--task-id`（必填） |
| `virtualphone create` | `POST /cluster/{cluster}/virtualphone` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `windows create` | `POST /cluster/{cluster}/windows` | 预览/`--yes` | `--cluster`（必填）；`--body` / `--body-file` |
| `windows get` | `GET /cluster/{cluster}/windows/{emulator}/` | 只读 | `--cluster`（必填）、`--emulator`（必填） |
| `health get` | `GET /health_check` | 只读 | `--group`（必填，cluster/psm/idc/emulator_type）、`--keyword` |
| `idc list` | `GET /info/idc_list` | 只读 | `--cluster`（必填）、`--data-struct` |
| `info get` | `GET /info/{name}` | 只读 | `--name`（必填） |
| `emulator qga-script list` | `GET /qga_scripts` | 只读，SG 不支持 | — |
