---
name: bytedance-coral
description: "Use bytedcli Coral commands for Hive 字段敏感等级设置, Global Hive table creation/publication, regional expansion, ordinary-field replacement, metadata lookup and Hive permission workflows: safely preview or set field sensitivity levels, search Coral/Hive assets, inspect table metadata/DDL/partitions/lineage/quality, directly grant permissions, modify existing permission TTLs for database/table/column resources with dry-run/--yes guards, check your own grants on a database or table (我的权限 / permission list), apply for table- or whole-database permissions, answer drafts, submit or withdraw applications, and handle Coral-specific permission questionnaire edge cases."
---

# bytedcli Coral

Use this skill when the task mentions Coral 字段敏感等级、敏感字段、安全等级, Coral Global table creation/publication, Global field changes, Coral, Coral Hive metadata, table search, table/column/database permission, whether you already hold access to a database or table (我的权限), permission questionnaire, `existed_application_id`, or Coral approval withdrawal.

## Invocation

```bash
bytedcli --json coral <command> [options]
```

In this repo, local testing uses:

```bash
node dist/bytedcli.js --json coral <command> [options]
```

If options are unclear, run `coral --help`, `coral hive table --help`, or `coral permission --help` instead of guessing.

## Quick commands

```bash
# Search tables when only a keyword is known
bytedcli --json coral search --region sg --query "example_table" --type-name HiveTable --limit 10

# Prefer DB-scoped table search when DB is known
bytedcli --json coral hive table list --region sg --db-name example_db --query "example_table" --limit 10

# Inspect metadata
bytedcli --json coral hive table get --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table ddl --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table latest-partition --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table partitions --region sg --db-name example_db --table-name example_table --limit 20
bytedcli --json coral hive table preview --region sg --db-name example_db --table-name example_table --limit 10
bytedcli --json coral hive table replicas --region sg --db-name example_db --table-name example_table

# Mark a field sensitive: preview the full payload and diff, then explicitly submit
bytedcli --json coral field set-sensitive --table example_db/example_table --field sample_col --level 2
bytedcli --json coral field set-sensitive --table example_db/example_table --field sample_col --level 2 --yes

# Add a user-group member: preview first; --yes verifies cross-region access then creates the member
bytedcli --json coral user-group member create --group-id 12345 --user demo.user --region sg
bytedcli --json coral user-group member create --group-id 12345 --user demo.user --region sg --yes

# Delete a user-group member: preview first; --yes submits the deletion
bytedcli --json coral user-group member delete --group-id 12345 --user demo.user --region sg
bytedcli --json coral user-group member delete --group-id 12345 --user demo.user --region sg --yes

# Owner direct grant: preview first; no HTTP is sent without --yes
bytedcli --json coral permission grant --region sg --db-name example_db --table-name example_table \
  --auth-object demo-group --auth-type user_group --permission read --ttl 180
# Only after the user explicitly confirms the preview
bytedcli --json coral permission grant --region sg --db-name example_db --table-name example_table \
  --auth-object demo-group --auth-type user_group --permission read --ttl 180 --yes

# Owner direct column grant: repeat --column or comma-separate values; preview before --yes
bytedcli --json coral permission grant --region sg --db-name example_db --table-name example_table \
  --column sample_col --column sample_date --auth-object demo-user --auth-type person \
  --permission read --ttl 180

# Modify an existing permission TTL: preview first, then repeat with --yes
bytedcli --json coral permission modify-ttl --region cn --resource-type table \
  --name example_db/example_table --auth-type person --auth-object demo-user \
  --permission read --ttl 180 --reason "Extend table access"

# Check your own grants first (Coral 安全信息 → 我的权限); table results include covering database grants
bytedcli coral permission list --region cn --db-name example_db --table-name example_table
bytedcli coral permission list --region cn --cluster cn6 --db-name example_db

# Apply read permission; repeat --column for column access and --row-filter for row/partition scope
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --auth-object demo-user --permission read --ttl 365 \
  --reason "Need read access for analysis."
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --row-filter app=sample-app --auth-object demo-user --permission read --ttl 365

# Data production / dashboard construction: preview a 365-day personal read application
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --auth-type person --auth-object demo-user --permission read --ttl 365 \
  --requirement-type data-production --lang zh_CN \
  --reason '项目背景：示例项目；建设内容：示例数据链路与看板；使用方式：持续开发、验收与维护。' \
  --dry-run

# Whole-database write application; database scope is explicit and takes no --table-name
# --reason-detail passes the three data-production fields verbatim (项目背景, 建设内容, 使用方式)
# Database scope only previews; add --yes after the user confirms the preview
bytedcli --json coral permission apply --region cn --cluster cn6 --resource-type database \
  --db-name example_db --auth-object demo-user --permission write --ttl 365 \
  --requirement-type data-production --reason-detail '示例项目背景' \
  --reason-detail '示例建设内容' --reason-detail '示例使用方式'
bytedcli --json coral permission apply --region cn --cluster cn6 --resource-type database \
  --db-name example_db --auth-object demo-user --permission write --ttl 365 \
  --requirement-type data-production --reason-detail '示例项目背景' \
  --reason-detail '示例建设内容' --reason-detail '示例使用方式' --yes

# Interrupted or unknown apply result: check your recent applications before applying again
bytedcli triton approval list --type submitted --region cn --days 1
bytedcli triton approval get --region cn --id 1001

# Preserve notice confirmation in the submitted payload (ignore_notice=false)
bytedcli --json coral permission apply --region uspipo --db-name example_db \
  --table-name example_table \
  --auth-type psm --auth-object demo.psm \
  --permission read --ttl 0 --no-ignore-notice
```

## Rules that matter

- `field set-sensitive` only supports CN Hive tables in `db/table` form and levels `1`–`4`. It reads the column search response plus the real table-detail projection, validates every required UI-contract field, and constructs the captured second-stage whitelist payload rather than forwarding the full response. Dry-run previews both PUT payloads and writes nothing. With `--yes`, the CLI rechecks both baselines, performs the two-stage update, and verifies sensitive columns through search plus stable table-detail business fields while allowing server-added metadata. Only explicit Coral business rejection permits compensation; unknown transport commit state is reported without another write.
- `permission modify-ttl` modifies existing grants by resource identity, never by application id. It is dry-run by default and requires `--yes` to POST. Single-object CLI resource types are `table` (`db/table`), `database` (`db`), and `column` (`db/table/column`); `data_source` is fixed to `hive`. Batch `--object`/`--objects-file` JSON uses API numeric `resource_type` values `1`, `2`, and `3` and must include `data_source`.
- Direct grant / 添加获权方 is an immediate owner write. Run `permission grant` without `--yes` first, show the endpoint and full payload, and use `--yes` only after explicit user confirmation. `--dry-run` wins if both flags are present.
- Direct grant supports table-level and column-level permissions. Pass repeatable or comma-separated `--column` values for column grants; each column is submitted as a separate resource object.
- Use `/tmp` for drafts and debug payloads; do not write scratch files into the repo.
- Do not reuse cookies from browser curl examples; use bytedcli auth/session.
- Permission questions, legal option ids, and cross-region option ids must come from Coral draft/API output. Do not invent schemas or answer ids.
- Omit `--cluster` unless Coral troubleshooting or product context explicitly requires a group override; CN permission apply defaults to Coral group `default`. Use `--cluster cn6` for 华北6 (China-North6) databases.
- `permission list` shows the logged-in user's own grants (权限层级 / 获权方 / 权限来源 / 权限类型 / 行限制), including grants through user groups and departments. Pass `--table-name` for a table; omit it for the whole database. It cannot answer for other users or PSMs.
- `permission apply --resource-type database` applies for the whole Hive database (Triton resource type 0). Database scope must be selected explicitly; `--table-name`, `--column` and `--row-filter` are rejected with it. The default `--resource-type table` still requires `--table-name`. Database scope only previews by default and submits with `--yes` (`--dry-run` wins); table scope keeps submitting unless `--dry-run` is given. Show the preview (resource, permission, ttl, `existingPermissions`) to the user and add `--yes` only after they confirm.
- For a personal application to yourself, `permission apply` first reads 我的权限 and reports `existingPermissions.coveredBy` when an unrestricted database or table grant already covers the request (write covers read). This is a warning, not a block: check expiry with `triton obtained list` and do not reapply just to renew. 我的权限 only describes the logged-in user, so coverage is evaluated (`checked: true`) only when 我的权限 shows a personal grant for the applicant. Otherwise the result is `checked: false` with a `reason`: a PSM receiver, another user, only group or department grants, or no grants at all. Check those with `permission list`.
- `--reason-detail` must be given exactly three times, in the requirement type's field order (data-production: 项目背景, 建设内容, 使用方式), together with `--requirement-type`. The values are submitted verbatim and Coral copilot is not asked to rewrite them.
- `CORAL_PERMISSION_SUBMIT_UNKNOWN` means the create request was sent but no reliable response came back (network error or 5xx). Do not resubmit; run `triton approval list --type submitted --region <region> --days 1` and look for the application first.
- `permission apply` sends `ignore_notice=true` by default; use `--no-ignore-notice` only when the captured product flow explicitly needs `ignore_notice=false`.
- `--requirement-type` accepts `data-analysis`, `index-calculation`, and `data-production` (数据生产/看板建设). An explicit type overrides the AI result. Production reasons use 项目背景、建设内容、使用方式; missing/empty AI fields and AI failures fall back to the supplied `--reason`.
- Request 365 days with `--ttl 365`; the CLI returns the error without shortening the TTL or switching the requirement type when the resource policy rejects the request. `permission apply --dry-run` only previews; without it, apply may directly create a ticket when no questionnaire requires answers. A `draft` result continues through the existing answer/create commands.
- Row/partition-scoped access uses repeatable `--row-filter column=value`. Repeat the option for multiple exact values. `--column` selects readable columns and does not constrain rows.
- In real workflows, ask the user before answering permission questions. Only random-answer in explicitly authorized tests.
- Cross-region questions are returned under `crossRegionQuestions`; answer them with `permission answer --question-id <id> --answer <option id or option text>`. Repeat `--answer` for multi-select questions.
- `status: existing` / `existed_application_id` is an existing ticket, not a new submission.
- `status: unknown` or no `groupId`/URL means do not claim a new ticket was created.
- If a test creates a ticket id, withdraw it before finishing.

## 普通 Hive 列说明

修改已有普通 Hive 表的列说明时，使用 `coral hive table update --column-comments '{"sample_col":"字段说明"}' --db-name example_db --table-name example_table --region cn`。默认只读取完整 schema 并预览差异；获得写入授权后加 `--yes` 提交，`--dry-run` 始终优先。无需手工回传完整列数组。分区列、Global 表、其他引擎以及截断或折叠 schema 会被拒绝。

读取元数据、安全标签 CID 归一化、单次提交和回读核验的边界见 `references/search-and-metadata.md` 的「更新普通 Hive 列说明」。`verified` 仅表示 Coral 元数据一致，不表示下游 Hive 引擎已同步；失败或超时后先读取状态，不能自动重放写请求。

## Global tables

For Global table creation, field changes, region expansion or publication recovery, read `references/global-table.md` first. Use `coral global-table create / modify field / add-region / get / wait` with `--site i18n-tt`. Writes preview by default; `--yes` submits once. Creation and modifications accept Hive-style `--fields` or `--ddl`/`--file`; create also accepts `--partition-keys`. Ordinary fields support nested `array`, `map`, `struct` and `uniontype` in JSON and SQL; map keys and partition keys must be primitive types. Server schema validation still runs before create submission. Field updates accept `--region` as publication targets; omit it for all intended regions. Selected regions must have a successful prior publication. A new version cancels earlier unfinished publications, including unselected pending targets; the command blocks unless `--supersede-pending` explicitly acknowledges that effect. Deferred existing tables can be brought up to the same schema later; canceled targets that never materialized require add-region. Global `gcp` means US-EastRed/cid=5; `eu-compliance2` is the separate EU-Compliance2/cid=31 target. Pending publication is not proof of an approval ticket, and a timeout must not trigger resubmission.

For incremental field additions, use `coral global-table modify field --add-fields <json>` or `--add-fields-file <json-file>`; these are mutually exclusive with the complete-replacement inputs `--fields` / `--ddl` / `--file`. Existing primary keys and parquet zstd/gzip storage are preserved; primary-key tables allow additions only, retaining every existing field. Inspect aggregated preflight failures through `error.details.checks`; an already satisfied incremental request returns `changed=false` without submitting. See `references/global-table.md` for input rules, preservation checks and recovery.

To explicitly remove primary keys, use `modify field --clear-primary-key` while retaining all existing columns. To switch regional expiry to partition-name TTL, add `--ttl-column <existing STRING partition>` (format `yyyyMMdd`); each region keeps its current retention days. Supply the complete unchanged field list for an attribute-only update. Inspect `attributeChanges` in the preview, then submit with `--yes` under the existing authorization and verify the same operation with `wait --verify-ddl`. See the Global table guide for legacy key properties, expiry exclusions and recovery.

## References

- `references/global-table.md` — Global table lifecycle, schema inputs and recovery.
- `references/search-and-metadata.md` — compact metadata command guide.
- `references/permission-workflow.md` — permission draft/create/withdraw flow and gotchas.
- `references/commands.md` — command cheat sheet.
