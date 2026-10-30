# ENV

```bash
# 站点与动态 standard_env 列表
bytedcli env site list

# 收藏/管理 ENV
bytedcli env list-starred --page 1 --page-size 10
bytedcli env list-managed --page 1 --page-size 10

# 按环境标识搜索
bytedcli env search --keyword "ppe_coze" --env-site cn,boe

# 按服务搜索
bytedcli env search-service --service "example.service.api" --env-site cn,boe

# 列出 ENV 下的服务列表（instance_meta API）
bytedcli env service list --env "ppe_qianchuan2" --standard-env online_cn
bytedcli env service list --env "ppe_qianchuan2" --standard-env online_cn --service-types tce --page 1 --page-size 20
bytedcli env service get --instance-id 123456 --standard-env online_cn

# 创建流程相关
bytedcli env site baseline-list
bytedcli env site baseline-zones --standard-env online_cn
bytedcli env check-name --name "ppe_demo" --standard-env online_cn
bytedcli env create --name "ppe_demo" --standard-env online_cn --idc LF --visibility private
# 若 baseline-zones 返回 China-North/LF，也可传 --idc China-North/LF；创建时 env.idc 保存为 LF。

# 部署与升级
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_i18nbd --psm "example.service.api" --flow-base prod
# 自定义资源租期：UI"添加服务"弹窗里的"租期"输入框对应 --lease-days，--lease-rule-id 透传系统策略 id
bytedcli env service deploy-tce --env "boe_demo" --standard-env boe --psm "demo.sample.svc" --flow-base prod --lease-days 2 --lease-rule-id 145
bytedcli env service deploy-tcc --env "ppe_demo" --standard-env online_i18nbd --psm "demo.sample.svc"
# upgrade-tce 是真实写操作：必须显式传 --dry-run（预览已解析的集群与 SCM 仓库）或 --yes（提交）二选一
bytedcli env service upgrade-tce --env "ppe_demo" --standard-env online_i18nbd --psm "example.service.api" --cluster-id 12345 --flow-base prod --scm-env-type prod --yes
# 预览从 Git 分支一次性升级现有 PPE TCE 集群；--dry-run 不触发编译或提交
bytedcli env service upgrade-tce --env "ppe_demo" --standard-env online_cn --psm "demo.sample.service" --cluster-id 12345 --branch "feat/demo" --dry-run
# --all 先预览当前全部 cluster_ids 和解析后的 scm_repos；不要自动紧接着执行 --yes
bytedcli env service upgrade-tce --env "ppe_demo" --standard-env online_cn --psm "demo.sample.service" --all --branch "feat/demo" --dry-run
# 用户确认预览后，把返回的 cluster_ids 原样带入 --expected-cluster-ids；成员变化时提交会被阻止
bytedcli env service upgrade-tce --env "ppe_demo" --standard-env online_cn --psm "demo.sample.service" --all --expected-cluster-ids 111,222 --branch "feat/demo" --yes

# 自动更新流水线：绑定 SCM 仓库分支，分支 push 后触发热更新（不同于一次性 deploy/upgrade）
bytedcli env service auto-update create --env "ppe_demo" --standard-env online_cn --env-type ppe --psm "demo.psm.tce" --repo "demo/service/api" --branch "debug/demo"
# 已存在同一 env+psm 的自动更新流水线时，命令返回已有流水线，不重复创建。
# 删除持久自动更新流水线需要 --yes；若已不存在，命令返回 deleted=false。
bytedcli env service auto-update delete --env "ppe_demo" --standard-env online_cn --env-type ppe --psm "demo.psm.tce" --yes

# 集群模板（cluster_param_template）：等价 UI"集群模板"下拉，一次部署多集群分集群配置
bytedcli env service list-cluster-templates --psm "demo.psm.tce" --standard-env online_cn
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --cluster-template-name "上次所选集群"
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --cluster-template-id 22708

# ENV 治理"服务部署模版"（deploy_template）：默认查询启用模版，与 cluster_param_template 独立
bytedcli env service deploy-template list --psm "demo.psm.tce" --standard-env online_cn
bytedcli env service deploy-template list --psm "demo.psm.tce" --standard-env online_cn --include-disabled --page 1 --page-size 20

# deploy-tce 是真实写操作：必须显式传 --dry-run（预览）或 --yes（提交）二选一
# --dry-run 与提交共用同一条解析链路（SCM 依赖 → 集群解析 → pre-check → DSL payload），只是不调部署接口
# 预览里的 clusters / deployment_slice 就是同参数提交会发送的内容；pre-check 也会执行
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --dry-run
# 输出 env/standard_env/env_type/psm/action/flow_base/branch/allow_debug/scm_repos/clusters/cluster_spec/pre_check/deployment_slice
# 固定落点（create_suggest 非确定性）：导出单集群后先按下文验证必填字段，再做一次固定 spec 的只读预检
bytedcli --jq '.data.cluster_spec' env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --dry-run > cluster.json
bytedcli --json env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --cluster-spec-file cluster.json --dry-run
# cluster_spec 仅在解析结果恰为一个完整集群时可复用；null / 多集群结果不能固定为单对象
# selector 是门禁不是筛选：只要求至少一个候选匹配，通过后提交整批 clusters，不要以为只部署匹配项

# 按 PSM 查该环境部署使用的 SCM 仓库与版本（只读）；数据与 deploy-tce 内部解析的是同一份
bytedcli env service list-scm-deps --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce"
# bytefaas 服务加 --psm-type bytefaas
# 输出依赖表（Env Type=基线 bundle 标签或 current × Repo × Version × Branch × Is Main）+ 主仓 Git 信息
# 部署默认 --flow-base prod 只选 prod bundle 行；--branch/--scm-repo-version 时以 override 为准
# 主仓 Git 信息为 best-effort：查不到时依赖表照常输出，main_repository=null 并给 main_repository_error
# 分支 -> 最新构建版本用既有命令：bytedcli scm repo version list <repo> --branch <branch>

# 允许远程调试：置 meta.debug=true（默认关闭）
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --allow-debug

# PPE bytefaas 部署 / 升级
bytedcli env service deploy-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas"
bytedcli env service deploy-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas" --scm-version "1.0.0.123"
bytedcli env service deploy-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas" --region cn-north --cluster faas-cn-north
bytedcli env service deploy-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas" --allow-debug
bytedcli env service upgrade-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas" --scm-version "1.0.0.124"

# ENV ByteCopy（CN/SG/EU/US：--site cn|i18n-tt|eu-ttp|us-ttp）
bytedcli env bytecopy service get --site i18n-tt --service-name "demo.service"
bytedcli env bytecopy instance get --site eu-ttp --service-name "demo.service" --instance-name "demo.instance"
bytedcli env bytecopy target-address list --site i18n-tt --instance-id 67890
bytedcli env bytecopy target-address add --site i18n-tt --instance-id 67890 --target-address 192.0.2.11:8080 --ttl 30

# 设备管理
bytedcli env device list --env "ppe_demo" --standard-env online_i18nbd
bytedcli env device add --env "ppe_demo" --standard-env online_i18nbd --device-id 4252524525 --expire-at "2026-02-19T01:19:40.471Z"
bytedcli env device update --env "ppe_demo" --standard-env online_i18nbd --device-id 4252524525 --expire-at "2026-02-19T09:19:58+08:00"
bytedcli env device unbind --standard-env online_i18nbd --device-id 4252524525

# 工单
bytedcli env ticket list --env "ppe_demo" --standard-env online_i18nbd --page 1 --page-size 10
bytedcli env ticket get --ticket-id 2021755505366867968 --standard-env online_i18nbd
```

## 显式 ENV cluster spec

`env service deploy-tce --cluster-spec-file` 读取的是 **ENV 创建部署的单集群 spec**，不是
`tce cluster create` 使用的 `cluster_info`。两者字段与取值来源不同，不能互换。spec 的位置、
基线与机房值必须来自已确认的 ENV `--dry-run`、`create_suggest`、基线集群或
`cluster_param_template`；用户负责从候选中确认目标，Agent 不得猜测 zone、virtual cluster、
base cluster 或 IDC。

### 最小 JSON

```json
{
  "name": "demo-cluster",
  "zone": "sample-zone",
  "virtual_cluster": "sample-virtual-cluster",
  "base_cluster_id": 100,
  "dc_infos": [{ "idc": "sample-idc", "count": 1 }]
}
```

### 字段表

| 字段                    | 必填 | 类型 / 单位                 | 取值来源与行为                                                         |
| ----------------------- | ---- | --------------------------- | ---------------------------------------------------------------------- |
| `name`                  | 是   | string                      | ENV preview / create suggestion / baseline / cluster template 的集群名 |
| `zone`                  | 是   | string                      | 同一已确认 ENV 来源返回的 zone                                         |
| `virtual_cluster`       | 是   | string                      | 同一已确认 ENV 来源返回的 virtual cluster                              |
| `base_cluster_id`       | 是   | number                      | 同一已确认 ENV 来源返回的基线集群 ID                                   |
| `dc_infos`              | 是   | array，至少一项             | 已确认位置对应的 IDC 副本列表                                          |
| `dc_infos[].idc`        | 是   | string                      | ENV 来源返回的 IDC                                                     |
| `dc_infos[].count`      | 是   | number / 副本数             | 用户确认的该 IDC 副本数                                                |
| `cpu`                   | 否   | number / CPU cores          | 已确认 ENV 来源返回或用户明确选择的核数                                |
| `mem`                   | 否   | number / GiB                | 已确认 ENV 来源返回或用户明确选择的内存                                |
| `count`                 | 否   | number / 副本数             | 省略时沿用现有归一化：取 `dc_infos[].count` 的最大值                   |
| `host_type`             | 否   | string                      | 已确认 ENV 来源返回的 host type                                        |
| `network_mode`          | 否   | string                      | 已确认 ENV 来源返回的 network mode                                     |
| `ipv6only_enable`       | 否   | **string**                  | ENV wire 字段；即使表达开关也不是 boolean                              |
| `sidecar_egress_enable` | 否   | boolean                     | ENV sidecar egress 开关                                                |
| `advanced_parameters`   | 否   | object / open map           | 内容保持开放并原样保留，不臆造内部结构                                 |
| `new_env_vars`          | 否   | string 或 object / open map | 使用 ENV preview/template 已有形态或用户明确提供的值                   |

JSON 新文件应使用表中的 canonical 类型。为兼容历史输入，现有归一化仍会把数值字符串转换为
number；可选字段类型无效时继续按既有规则忽略。未知顶层字段和 `dc_infos[]` 内未知字段会被过滤，
`advanced_parameters` map 内部内容会保留；不要依赖未知顶层扩展字段透传。

### 只读固定与复验

部分 fallback 预览可能只返回不完整候选，因此不能只看到 `cluster_spec` 非 null 就复用；必须检查
全部必填字段。多集群解析返回 `cluster_spec=null`，不能把它固定成一个 spec 对象。

```bash
# 导出本次只读解析得到的单集群对象
bytedcli --jq '.data.cluster_spec' env service deploy-tce \
  --env ppe_demo --standard-env online_cn --psm demo.psm.tce --dry-run > cluster.json

# 验证非 null、必填字符串、base_cluster_id 与非空 dc_infos
jq -e '
  type == "object" and
  (.name | type == "string" and length > 0) and
  (.zone | type == "string" and length > 0) and
  (.virtual_cluster | type == "string" and length > 0) and
  (.base_cluster_id | type == "number") and
  (.dc_infos | type == "array" and length > 0 and
    all(.[]; (.idc | type == "string" and length > 0) and (.count | type == "number")))
' cluster.json

# 去掉原 selector，用同一 ENV 入口再次只读验证固定 spec 与 pre_check
bytedcli --json env service deploy-tce \
  --env ppe_demo --standard-env online_cn --psm demo.psm.tce \
  --cluster-spec-file cluster.json --dry-run
```

第二次输出中应再次核对 `data.cluster_spec` 与 `data.pre_check`。`--cluster-spec-file` 与
`--specify-dcs` / `--zone` / `--virtual-cluster` 互斥；`--cluster-template-id` /
`--cluster-template-name` 彼此互斥，并且不能与 spec 文件或这些 selector 同传。只有用户确认后，
才能在同一 ENV 命令上把 `--dry-run` 改为 `--yes`。

## PPE bytefaas deployment

`env service deploy-bytefaas` 把一个 bytefaas（ByteCloud FaaS）服务挂载到 PPE 泳道，
`env service upgrade-bytefaas` 把已挂载实例切换到新的 SCM 版本。两者都走 **ENV 平台**，
是测试/泳道部署链路，**不**是生产发布。

生产 cluster 的正式发布使用 `bytedcli faas release create`（见 `bytedance-faas` skill），
两条链路互不替代。

### 必填与默认值

| 参数              | 说明                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------ |
| `--env`           | 目标 PPE/泳道 ENV 名称（必填）                                                       |
| `--standard-env`  | 基线 standard env，如 `online_cn` / `boe` / `online_i18nbd`（必填）                  |
| `--psm`           | bytefaas 服务的 PSM（必填）                                                          |
| `--env-type`      | env type 覆盖：`ppe`、`boe`、`boe_feature`、`boe_base`；默认按 `--standard-env` 推断 |
| `--region`        | bytefaas region，默认 `cn-north`                                                     |
| `--cluster`       | bytefaas cluster，默认 `faas-cn-north`                                               |
| `--scm-version`   | SCM 主仓版本号，省略时自动取 prod 基线最新版                                         |
| `--code-revision` | 指定 code revision id，省略时使用最新 revision                                       |
| `--allow-debug`   | 允许远程调试：置 meta.debug=true（默认关闭）                                         |

### 示例

```bash
# 首次挂载到 PPE 泳道(自动取 prod 基线最新 SCM 版本)
bytedcli env service deploy-bytefaas \
  --env ppe_demo_swimlane --standard-env online_cn \
  --psm demo.psm.faas

# 显式指定 SCM 版本
bytedcli env service deploy-bytefaas \
  --env ppe_demo_swimlane --standard-env online_cn \
  --psm demo.psm.faas --scm-version 1.0.0.123

# 显式覆盖 region / cluster
bytedcli env service deploy-bytefaas \
  --env ppe_demo_swimlane --standard-env online_cn \
  --psm demo.psm.faas --region cn-north --cluster faas-cn-north

# 升级已挂载实例到新的 SCM 版本
bytedcli env service upgrade-bytefaas \
  --env ppe_demo_swimlane --standard-env online_cn \
  --psm demo.psm.faas --scm-version 1.0.0.124
```

### 常见误用

- 把 `--standard-env` 当成"泳道类型"：`online_cn` / `boe` 是基线，`ppe` 才是 env type；
  PPE 类型由命令名定位，需要覆盖时用 `--env-type`，不要把这两个参数互换。
- 试图传 git 分支或 ICM 镜像：目前 CLI 只支持 SCM 制品，
  不存在 `--branch` 或镜像标签参数。
- 试图自定义资源租期：PPE bytefaas 默认 14 天短回收，CLI 不暴露 `--lease-days`。
- 想做生产 cluster 正式发布却调用 `deploy-bytefaas`：这条命令只挂到 PPE 泳道；
  生产发布请改走 `bytedance-faas` skill 的 `faas release create`。

## ENV ByteCopy

ENV ByteCopy 命令用于查看 ByteCopy service / instance、创建/启动/停止 instance，以及给 instance 添加目标地址。
ByteCopy 站点使用 `--site`，不是 `--env-site`。
在 ByteDance 生产网络环境中调用 `env bytecopy --site i18n-tt` 时，设置 `BYTEDCLI_NETWORK_PROFILE=prod`；bytedcli 会自动把 i18n-tt 路由到生产网可达域名。

### 站点

| 控制台区域 | 参数             |
| ---------- | ---------------- |
| SG         | `--site i18n-tt` |
| EU TTP     | `--site eu-ttp`  |
| US TTP     | `--site us-ttp`  |

### 示例

```bash
# 查 ByteCopy service
bytedcli env bytecopy service get --site i18n-tt --service-name demo.service

# 查看 service 下的 instance
bytedcli env bytecopy instance get --site eu-ttp \
  --service-name demo.service --instance-name demo.instance
bytedcli env bytecopy instance create --site i18n-tt \
  --service-name example.service.api --instance-name demo.instance \
  --source-env MESH --source-type PSM --protocol THRIFT --dc sg1 \
  --required-function forward --env prod --cluster default \
  --sd-name dev.example.sg1.demo --online-data-percent 100 \
  --force-mode false --context-json '{}' --yes
bytedcli env bytecopy instance create --site i18n-tt   --service-name example.service.api   --request-json '{"InstanceName":"demo.instance","SourceEnv":"MESH"}' --yes
bytedcli env bytecopy instance start --site i18n-tt \
  --instance-id 67890 --start-storage false --yes
bytedcli env bytecopy instance stop --site i18n-tt --instance-id 67890 --yes

# 查看 / 添加 instance 目标地址
bytedcli env bytecopy target-address list --site i18n-tt --instance-id 67890
bytedcli env bytecopy target-address add --site i18n-tt \
  --instance-id 67890 --target-address 192.0.2.11:8080 --ttl 30
```

### 参数要点

| 参数               | 说明                                                            |
| ------------------ | --------------------------------------------------------------- |
| `--service-name`   | ByteCopy service 名称                                           |
| `--instance-name`  | ByteCopy instance 名称                                          |
| `--instance-id`    | ByteCopy instance id，来自 `instance get` 或控制台 instance URL |
| `--target-address` | 目标地址，格式 `ip:port`；IPv6 用 `[2001:db8::1]:8080`          |
| `--ttl`            | `target-address add` 目标地址 TTL，单位分钟，默认 `30`          |

`instance create` 不提供业务默认值且不会隐式启动；`--request-json` 可原样提交完整后端 `InstanceReq`，并与其他创建字段参数互斥。create 不传 `--yes` 时只预览完整请求；field-flag 模式必须显式传 `--force-mode true|false`；`--thrift-transport` 仅用于 NON-MESH THRIFT。`instance start` 必须显式传 `--start-storage true|false`；start/stop 都必须传 `--yes`，且 create、start、stop 各自只执行对应的一个后端操作。
