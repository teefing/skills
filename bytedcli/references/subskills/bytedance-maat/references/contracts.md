# Maat CN / I18N 接口契约

来源：Maat 前端页面、发布和联调页面静态代码、已登录会话只读请求。写入契约经过静态追踪及离线测试；仅对用户逐次确认的管理员、普通构建及灰度操作做过真实执行，不能推广为所有写路径已验收。

所有接口同源，CN query 添加 `__siteEnv__=CN`，i18n 添加 `__siteEnv__=I18N`；站点路由集中在 API `site.ts`。成功 envelope 必须为数字 `code:0`，`success:false` 仍然算失败。下表 `region` 是项目发布区域，独立于站点；CN 默认 `CN`，i18n 必须显式指定项目支持的值。

项目版本摘要 `/api/project/center`、灰度详情和冻结查询不使用固定区域白名单，例如 CN 站点可查询 `region: "Volcengine"`。项目摘要和灰度发布检查区域属于项目声明的 `publishRegionList`；灰度发布仅为旧 CN 项目兼容未声明区域的情况。`project get` 不指定区域且项目不含 CN 时只返回元数据，不猜测区域。构建、管理员修改和联调写入保留各自的区域限制。

| 操作                      | 方法与路径                              | 业务参数                                                                                                                     |
| ------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 当前身份                  | GET `/api/user/currentUser`             | 无                                                                                                                           |
| 可见项目                  | POST `/api/project/list`                | `{ICanSee:true}`                                                                                                             |
| 我的收藏                  | POST `/api/project/list`                | `{pageSize,pageNo,keyword:"",onlyFavor:true}`；返回 `{total,rows}`                                                           |
| 项目详情                  | POST `/api/project/detail`              | `{name}`                                                                                                                     |
| 项目管理员修改            | POST `/api/project/update`              | 基本信息表单快照，仅改变 `adminUsers`，带 `_id`、`scmId`、`scmList` 和 `currentRegion`                                       |
| 当前版本摘要              | POST `/api/project/center`              | `{_id,region}`                                                                                                               |
| 成功版本搜索              | POST `/api/scm/searchVersion`           | `{status:"build_ok",repo_name,limit,offset,search}`                                                                          |
| 分支搜索                  | POST `/api/scm/getBranches`             | `{scmId,branch}`；返回字符串数组，搜索可能截断                                                                               |
| 分支最后提交              | POST `/api/scm/getBranchLastCommit`     | `{scmId,branch}`；返回 `{name,hash,message}`                                                                                 |
| 全状态构建历史            | POST `/api/scm/versionList`             | `{repos_id,pageSize,pageNo,version,branch}`；返回 `{total,rows}`                                                             |
| 仅构建                    | POST `/api/publish/v2/online/<project>` | `{onlineType:"onlyBuild",region,routerList:[{scmId,publishType:"branch",routers:[],checked:true,branch,description,envs?}]}` |
| 灰度详情                  | POST `/api/gray/detail`                 | `{projectName,parentProjectName:"",region}`                                                                                  |
| 冻结信息                  | GET `/api/freezeInfo/getFreezeInfo`     | query `{name,region}`                                                                                                        |
| 新 ID                     | POST `/api/open/newId`                  | 无，仅确认后调用                                                                                                             |
| 上线灰度                  | POST `/api/gray/update`                 | 完整当前配置加目标变更，必要时携带服务端返回的 `freezeInfo`                                                                  |
| 联调公共配置（只读）      | POST `/api/devConfig/get`               | `{projectId}`；空对象/null 为未初始化                                                                                        |
| 联调环境列表/精确查找     | POST `/api/devEnv/list`                 | `{projectId,region,name,exactMatchName,onlyWatch,onlyCreate,pageNo,pageSize}`；返回 `{total,rows}`                           |
| 修改单个联调环境          | POST `/api/devEnv/update`               | 当前环境对象合并指定表单字段；保留其他字段，不更新公共配置                                                                   |
| 联调触发构建              | POST `/api/devEnv/triggleBuild`         | `{_id}`；成功仅表示受理，不保证仅构建或本次构建成功                                                                          |
| 共享 API 代理目标（只读） | POST `/api/devApi/list`                 | `{projectId,keyword,pageNo,pageSize}`                                                                                        |
| 联调日志摘要（只读）      | POST `/api/devEnvLog/list`              | `{devEnvId,pageNo,pageSize}`；返回 `{total,rows}`                                                                            |

项目详情可能含 `token`、环境变量和 Webhook；SCM 响应可能含环境变量或产物链接。CLI 使用字段白名单，不输出 raw，不在 HTTP trace 中记录请求/响应体。

## 基本信息管理员

控制台从项目详情选取 `name,logo,desc,_id,msgcenter,token,duty,lock,bypass,businessDomains`，将 `scmList` 转换为主 `scmId` 加其余仓库 ID 的数组，附加 `adminUsers` 和 `currentRegion` 后提交。CLI 遵循同一表单序列化，不假定后端支持只发送管理员字段的 PATCH。敏感表单读取及写 transport 不导出公共 API barrel，只由受确认保护的服务使用。

管理员变更预览仅输出名单及差异；指纹覆盖站点、区域上下文、身份和完整保留字段。提交前重新检查；提交后回读表单业务字段。当前身份必须为项目管理员或 Maat 管理员，最终权限仍由服务端决定。实际执行需针对本次变更获得确认；离线测试不能证明实际权限变更。

联调配置与构建的字段、影响和恢复边界见 [联调环境](dev.md)。联调仓库与生产 SCM 不可混用；环境配置/日志查询不提供本次触发与产物的可靠关联。

## 灰度条目

普通 `byte` 和 `volcengine` 项目的 Maat 渲染链共用 `/api/gray/update`，发送完整灰度快照加表单变化，不另行合并火山项目设置。项目详情仅投影 `volcengineConfig.renderChain` 用于能力检查和确认指纹；未设置、空值及 `maat` 使用该路线，`volcengine` 与未知非空值拒绝提交。火山路线已静态追踪并覆盖离线测试，实际发布仍需逐次确认和回读，不能将预览等同于写入验收。

`versionList` 顺序有业务含义。每条含 `_id`、`name`、`flow`、`scmVersion`、`scmVersionDesc`、`scmVersionList`、`rootCondition`。新增时由服务端生成 `_id`，同步赋给 `rootCondition.uuid`；`createUser` / `updateUser` 来自当前身份。

删除使用相同完整配置更新：控制台先按目标 `_id` 从 `versionList` 移除一条，再上线灰度。CLI 的 `gray delete` 按唯一准确名称锁定该条目，预览展示目标 ID；确认指纹包含完整基线、删除后的 payload、身份、区域和操作类型。保留所有其他条目及配置，不申请 ID，不删除构建记录。详细操作见 [删除流程](gray-delete.md)。

控制台的 up/down 操作交换 `versionList` 中的相邻条目后提交完整配置，无独立优先级字段。CLI 的 `--before/--after` 仅插入或移动目标；双参照须在移除目标后相邻。预览展示前后顺序，位置参数及有序 payload 纳入指纹；新建分配 ID 时按名称定位目标而非假设目标在末尾。

完整条件树通过 `gray deploy --conditions-file` 输入，只替换目标条目的 `rootCondition`，复用相同预览、指纹、提交前重查和回读链路。来源、字段、操作符和值类型见 [条件编辑](conditions.md)。文件不是完整 gray/update payload，不能修改其他条目或项目级字段。

`scmVersionList` 的单 SCM 项为 `{scmId,scmName,scmVersion,desc}`，更新版本必须同时更新顶层版本及描述。未改动的条目和未知字段原样保留在内部写入快照中，不将项目详情合并进灰度 payload。

请求头条件示例：

```json
{
  "type": "sub-conditions",
  "join": "AND",
  "uuid": "sample-gray-id",
  "conditions": [
    {
      "type": "expression",
      "dataType": "string",
      "source": "header",
      "key": "x-demo-env",
      "name": "header.x-demo-env",
      "option": "Equals",
      "value": "demo-gray",
      "uuid": "sample-condition-id"
    }
  ]
}
```

`flowMode` 支持 `Priority` 和 `Parallel`，保持当前值。并行模式下小于 1 的 flow 项之和不能超过 1；flow=1 的条件分流项不纳入该随机流量和。这与网页当前校验语义一致，不应自行改成全部项相加。

## 一致性与恢复

确认指纹覆盖站点、发布区域、当前配置、项目路由、身份、冻结信息和目标 payload。新 ID 是确认后生成的非业务字段，以预览占位符表示；其余配置不得变化。

发布成功响应后仍需读取灰度详情；断网、超时、非成功响应均不得触发写重试。回读比较完整业务配置及顺序，忽略顶层服务端时间/版本计数与 Kura 空默认值。失败或差异返回结果未知，交由人工检查。

未验证的边界：服务端 CAS / 幂等键、线上灰度路由命中、未初始化灰度的创建协议、父子/多 SCM/KuraCloud 等发布路线。不能将离线 mock 当成线上发布验收。
