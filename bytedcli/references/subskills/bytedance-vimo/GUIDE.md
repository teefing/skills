---
name: bytedance-vimo
description: "Use for Vimo Web operations. Always route the request by deployment with the global `--site cn|i18n` option: CN covers JianYing creator task instructions, submissions and rewards, account evidence, homepage configuration, template RID lookup/download, and commerce reads; i18n covers CapCut overseas Creator, User, Template, incentive, and controlled writes. Keep CN and overseas contracts, authentication, and references separate. Use vimocli only for Material OpenAPI workflows."
---

# ByteDance Vimo

Use one stable command shape and select the deployment globally:

```bash
bytedcli --site cn vimo <resource> <action> [options]
bytedcli --site i18n vimo <resource> <action> [options]
```

Put global options such as `--site`, `--json`, and HTTP routing headers before `vimo`.

## Route by site before loading details

Determine the business deployment from the user's object and intent, then read only the matching
site reference:

| User intent                                                           | Site   | Command family               | Read next                                                                                     |
| --------------------------------------------------------------------- | ------ | ---------------------------- | --------------------------------------------------------------------------------------------- |
| JianYing account evidence by UID                                      | `cn`   | `vimo user get`              | [`references/cn.md`](references/cn.md)                                                        |
| JianYing creator tasks, activity rules, submissions, or award evidence | `cn` | `vimo creator task/task-submission/task-reward` | [`references/cn.md`](references/cn.md) |
| JianYing template RID, Vimo resource/share URL, signed ZIP            | `cn`   | `vimo template get/download` | [`references/cn.md`](references/cn.md)                                                        |
| JianYing share-topic query, create, or template binding               | `cn`   | `vimo topic ...`             | [`references/cn.md`](references/cn.md)                                                        |
| JianYing commerce feature, benefit, or history                        | `cn`   | `vimo commerce ...`          | [`references/cn.md`](references/cn.md)                                                        |
| JianYing homepage tool, floor, priority, or relationship              | `cn`   | `vimo homepage ...`          | [`references/cn.md`](references/cn.md)                                                        |
| CapCut 创作者资料、权限/标签、线索、征稿/成长任务 | `i18n` | Select the exact `vimo creator` leaf | [`references/i18n.md`](references/i18n.md) |
| CapCut 征稿任务审批、规则、预览、置顶、奖励排序及线索补充接口 | `i18n` | `vimo creator task/clue ...` | [`references/creator-task-clue-extra.md`](references/creator-task-clue-extra.md) |
| CapCut 基础用户资料、用户查询页的签约状态 | `i18n` | `vimo user list` | [`references/i18n.md`](references/i18n.md), then [`references/users.md`](references/users.md) |
| 有哪些模板分发场景、场景支持哪些模板类型/子类型 | `i18n` | `vimo template distribution-scene list` | [`references/templates.md`](references/templates.md) |
| 指定场景的导航 Tab、草稿或线上导航配置 | `i18n` | `vimo template tab list` | [`references/templates.md`](references/templates.md) |
| 模板列表、按 TemplateID 查详情、受控模板修改 | `i18n` | `vimo template list` or an explicit mutation leaf | [`references/templates.md`](references/templates.md) |
| 用户激励的运营活动、活动玩法、推荐模板强插配置 | `i18n` | Select the exact `vimo incentive` leaf | [`references/incentive.md`](references/incentive.md) |

Use the site, page and object already established in the conversation. Ask only when a missing
distinction changes the endpoint: a bare “template ID” does not identify a template resource, task
template or CN RID. Keep a known overseas request overseas; an unsupported operation does not
justify switching to CN or treating these IDs as interchangeable. Overseas authentication and the
complete intent-to-command table are in [i18n.md](references/i18n.md).

For “查询分发场景”, return `scenes` and the relevant `itemTypeMap` semantics, then stop. Query Tab
configuration only when requested. A configured scene or Tab does not prove actual Feed delivery.
For “近七天表现” or another specified period, use Vimo to identify the object, then obtain metrics
with the requested window; template creation-time filters and creator 30-day fields do not answer
an arbitrary reporting period. See [analytics boundaries](references/i18n.md#期间表现与能力缺口).

## Domain boundaries

- Task details (任务说明、投稿、获奖名单) use `creator task get`. For submissions and rewards,
  i18n uses `creator task submission list` and `creator task reward list`; CN uses
  `creator task-submission list` and `creator task-reward list`. CN uses [cn.md](references/cn.md); i18n uses
  [creator-tasks.md](references/creator-tasks.md). CN rewards use page numbers and require no rule ID;
  i18n rewards use cursors and require `--rule-id`. Shared reads without explicit site retain i18n behavior.
- `vimo creator` under `--site i18n` is the overseas 创作者管理 view. It owns creator lists, permissions, labels,
  clues, tasks, rewards, contracts, and punishments.
- `vimo user` is the overseas 用户查询/基础用户 view. It queries ordinary CapCut users by UID,
  CapCut ID, or contract status. Do not call this object a creator user or route it through
  `vimo creator`.
- `vimo template` under `--site cn` is RID lookup/download. Under `--site i18n`, it is overseas
  template management. Site selection is therefore part of the command contract.
- `vimo topic` is CN-only. `list` is read-only; `create` and `update` are L2 writes that default to
  dry-run and require explicit confirmation before adding `--yes`. `update` appends template IDs and
  preserves the existing topic name, type, and start time.
- `vimo user` under `--site cn` is read-only JianYing account evidence by UID. Under `--site i18n`,
  it is the CapCut overseas basic-user query view.
- `vimo homepage` is the read-only JianYing homepage configuration graph. Tool IDs connect atomic
  definitions to primary/secondary orders; `relatedCategoryId` connects a primary list to one
  secondary collection. The priority view is a filtered online primary-list view, not a fourth entity.
  Runtime primary-list matching checks smaller priority values first and keeps only the first matched
  list per category type; confirm conflicts against the CN reference before treating a later row as
  effective.
  When `homepage graph get` returns `experiment_vids`, follow the mandatory VID-to-Libra procedure in
  the CN reference for every VID. This JianYing homepage workflow always queries Libra app `147`;
  Vimo's `appId=1775` is a separate namespace. A VID is a version ID and must never be used as a
  Flight ID.
- Homepage floors are a separate entity from the tool ordering graph. `homepage floor list` reads
  the configuration library, `homepage floor-priority list` is its published/online ordering view,
  and `homepage floor get` resolves item `toolId` references plus experiment VIDs. The runtime client
  consumes a server-resolved feed rather than the Vimo admin payload directly, and may insert a local
  album-to-video floor, so configured priority is not guaranteed to be the absolute on-screen order.
- Overseas `creator list`, `user list`, and `template list` accept optional `--biz capcut`.
  Omitting it defaults to CapCut. Historical `--biz 106` remains accepted for existing scripts;
  both forms resolve to numeric bid `106` in Vimo requests. New calls should use `capcut`.
  Regional selectors such as `--biz-ids` and `--region-biz-id` are separate concepts.

Use `vimocli` instead for Material CRUD, upload/publish, custom fields, service-account OpenAPI,
and cross-business material administration.

## Site policy

The CLI accepts flat commands without an explicit site for older callers and infers the deployment
from the selected capability. New commands, documentation, and automation must generate
`--site cn|i18n` with the flat `vimo` tree. `--site i18n-tt` is accepted as an overseas site alias,
but canonical Vimo commands use `--site i18n`.

An explicit site must agree with the selected capability. Do not retry a site mismatch by dropping
`--site`; correct the routing decision instead.

## Execution and safety

Overseas `/template/*` and `/user/*` accept a personal ByteCloud JWT for `i18n-tt`
through `BYTEDCLI_USER_CLOUD_JWT`, without local `auth login` or a Vimo Cookie.
Keep `--site i18n` on Vimo commands; the client selects the JWT issuer internally.
Use a JWT belonging to the intended operator; Vimo validates identity and permissions.
See [overseas authentication](references/i18n.md) for credential priority and Cookie fallback.

1. Verify the selected leaf and requested flags with `--help` when the installed version is
   uncertain. Do not substitute a nearby command when a flag is absent.
2. Keep every UID, template ID, task ID, benefit ID, and other 64-bit identifier as a decimal
   string. Never coerce it to a JavaScript number.
3. For reads, check top-level `status` before consuming `data`, and follow only the pagination
   fields documented by the matching reference.
4. Never print, persist, or put Cookie/JWT values in command arguments. Treat injected credentials
   as process-scoped secrets.
5. When a CN read fails with `VIMO_PERMISSION_DENIED`, read the CN permission guidance, show the
   returned Kani permission and dry-run command, then ask whether the user wants to request it. Do
   not submit an approval unless the user explicitly requested automatic application in the original
   prompt or confirms after seeing the denial.
6. For writes, read the matching mutation reference first. Preview without `--yes`, show the exact
   action/target/payload and effects, obtain confirmation for that operation, then submit once.
   Follow the selected leaf's current help and risk-policy output: L3 submissions require audit
   `--reasons`, distinct from a business `--reason` such as an offline or punishment reason.
   Never automatically retry an unknown mutation outcome or replace an unsupported action with a
   different write. Vimo performs the final permission check for every read and write.

## Kani permission recovery for agents

When JSON output contains `next_action` and `approval_context`, the calling Agent must pass the
complete `approval_context` to the executor named by `next_action.executor`. For `a2ui`, ask A2UI to
run `next_action.operation` and generate the Kani application link.

The calling Agent must not construct a Kani URL, invent missing fields, submit the permission
application, or retry the Vimo mutation automatically. It should show the generated link to the user
and retry only after the user confirms that permission was granted.

## Progressive references

Read the site reference first, then load only the leaf reference required by the request:

- CN routing, authentication, template inputs, and commerce tuple model:
  [`references/cn.md`](references/cn.md)
- Overseas routing, authentication, network profile, and domain selection:
  [`references/i18n.md`](references/i18n.md)
- Creator list: [`references/creator-list.md`](references/creator-list.md)
- User query: [`references/users.md`](references/users.md)
- Creator clues and clue plans: [`references/creator-clues.md`](references/creator-clues.md),
  [`references/creator-clue-plans.md`](references/creator-clue-plans.md)
- Creator tasks and task templates: [`references/creator-tasks.md`](references/creator-tasks.md),
  [`references/creator-task-templates.md`](references/creator-task-templates.md)
- Creator task and clue supplemental commands: [`references/creator-task-clue-extra.md`](references/creator-task-clue-extra.md)
- Creator growth tasks: [`references/creator-growth-tasks.md`](references/creator-growth-tasks.md)
- Overseas distribution scenes/types, templates and navigation Tab: [`references/templates.md`](references/templates.md)
- User-incentive operation activities, activity rules and force-insert templates: [`references/incentive.md`](references/incentive.md)
- Creator mutations: [`references/creator-mutations.md`](references/creator-mutations.md)
- Clue/task mutations: [`references/creator-task-mutations.md`](references/creator-task-mutations.md)
- Overseas template mutations: [`references/template-mutations.md`](references/template-mutations.md)
- Shared invocation and troubleshooting: [`../../invocation.md`](../../invocation.md),
  [`../../troubleshooting.md`](../../troubleshooting.md)
