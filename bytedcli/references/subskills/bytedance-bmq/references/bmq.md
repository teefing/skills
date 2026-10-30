# BMQ

```bash
# Topic 列表
bytedcli bmq topic list --vregion "US-BOE" --page 1 --page-size 20
bytedcli bmq topic list --vregion "Singapore-Central" --search "demo" --all

# Topic 详情
bytedcli bmq topic get --topic-id 12345 --vregion "US-BOE"

# Topic 官方流量监控链接（BMQ 平台同款 Grafana 监控 URL）
bytedcli --site us-ttp bmq topic metrics get --search "demo-topic"
bytedcli --site us-ttp bmq topic metrics get --topic-id 12345 --type iframe

# Cluster 列表
bytedcli bmq cluster list --vregion "US-BOE" --all
bytedcli bmq cluster list --vregion "Singapore-Central" --search "public"

# Consumer Group 列表
bytedcli bmq consumer list --vregion "US-BOE" --page 1 --page-size 20
bytedcli bmq consumer list --vregion "Singapore-Central" --search "demo-consumer" --all

# Mirror 列表
bytedcli bmq mirror list --vregion "Singapore-Central" --status RUNNING --all
bytedcli bmq mirror list --vregion "Singapore-Central" --search "topic_name" --page-size 10

# 多站点（TikTok ROW）
bytedcli --site i18n-tt bmq topic list --vregion "Singapore-Central" --all

# TTP 站点
bytedcli --site us-ttp bmq topic list
bytedcli --site eu-ttp bmq topic list --vregion eu-ttp2
```

## Mirror search and hash strategy

`bmq mirror list --search <topic>` filters by **target topic** in the selected
`--vregion` (the mirror's target region). `--all` includes mirrors not owned by you;
`--page` and `--page-size` select one page, not an automatic full scan.

JSON mirror records include `partitionAlign` and `kafkaHashPolicy`. Text output
shows `Partition Align` and `Kafka Hash Policy`. These are separate upstream
fields: `false` is preserved, missing/null values are JSON `null` (text `-`), and
policy strings such as `PARTITION_ALIGN` or `KAFKA_DEFAULT` are returned unchanged.
Do not infer a policy from partition counts or substitute one field for the other.


## Topic creation orders

`bmq topic create` submits a ByteCloud resource order that creates the BMQ approval workflow. Select the control plane with global `--site` and an explicit virtual region with `--vregion`; the CLI maintains the CreateTopic mapping. The command does not accept `--workflow-config-id`. Supported sites are `cn`, `boe`, `i18n-bd` (alias `i18n`), `i18n-tt`, `us-ttp` and `eu-ttp`. Unsupported sites or unmapped site/region pairs fail before submission instead of falling back to another control plane.

```bash
bytedcli --site cn bmq topic create \
  --vregion China-North --cluster-name demo-cluster --topic-name demo-topic \
  --owner demo-owner --service-tree '|Demo|Messaging' \
  --message-qps 100 --message-size-kb 64 --partition-num 3 --replica-num 2 \
  --priority P2 --read-psm example.app.reader --write-psm example.app.writer --dry-run
```

Use the full region name, such as `China-North`, `China-BOE`, `US-BOE`, `Singapore-SaaS` (ByteIntl), `Singapore-Central` (TikTok ROW), `US-TTP` or `EU-TTP2`. Ambiguous region aliases such as `CN` and `SG` are not creation selectors. Ordinary BMQ creation does not reuse SINF message-preview routing.

Required inputs: virtual region, cluster name, topic name, owner, service-tree node ID or exact path, message QPS, message size in KB, partition count and `--priority`. The console form requires a Topic priority and the creation workflow rejects orders without one (`priority should be S/P0/P1/P2/P3`), so the CLI rejects a missing or unknown priority before any network call. Service-tree paths are resolved to one exact node through a read-only lookup; incomplete or ambiguous results stop the command. All numeric options accept only positive safe integers. A 64 MiB message is `--message-size-kb 65536`. Retention accepts either `--retention-hours` or `--retention-days`, not both.

Topic names follow the native creation form: at least three lowercase letters, digits, underscores or hyphens; the `__lane` suffix is reserved. Cluster names are matched exactly against the selected region's cluster list. A full result page without pagination metadata cannot confirm a complete lookup and stops creation.

Defaults: replicas 2, security level L3, topic usage `others`, retention size 256 GB, maximum consumers 20, partition production quota 5120 KB/s, lane topic false and user personal information false. Use `--partition-max-flow-kb` to change that quota; the CLI retrieves the matching partition QPS and computes total Topic production flow. The selected cluster's `multiDc` field determines `disaster` versus `non-disaster`; an unavailable or unconfirmed cluster stops creation. Like the console's creation form, the CLI accepts only clusters reported with `applied: true`; choose one from `bytedcli --site <site> bmq cluster list --vregion <vregion> --all --page-size 100 --json` on the same site and region (`--all` includes clusters you do not own).

Use `--member` for an additional owner, `--psm` for a primary service, and repeatable/comma-separated `--read-psm` / `--write-psm` for service permissions. A PSM present in both permission lists receives one `read-write` grant. The resource form's `psm` is derived from the new Topic name. Security level accepts L1-L4 or P0-P3; data sensitivity accepts L1-L4, and priority is required and accepts S, P0, P1, P2 or P3. Other form options include `--retention-size-gb`, `--max-consumer-num`, `--create-lane`, `--contain-user-personal-info` and comma-separated `--allowed-dc-list`.

`--extra-json` appends unmapped user form fields. It cannot override managed fields, derived cluster/QPS values, workflow selection, or server-owned order/budget context.

Without `--yes`, the command reads service-tree/cluster metadata, production-quota metadata and the server's order configuration, then previews the complete request. This requires working authentication, but does not run the creation preflight or submit an approval order. The output includes `request` (BMQ form) and `order_request` (resource order). `--dry-run --yes` still previews.

With `--yes`, the creation preflight runs before order submission; it checks creation conditions such as whether the topic name is already used. The CLI checks the fresh order configuration's product, region, resource identity and parent node, then calls the native resource-order route once. The server creates the order association and executes its normal controls. `--skip-check` skips only that preflight; it does not skip metadata checks, order controls or approval. The preflight accepts the console's `code: 0` response without `data`, or a recognized positive decision in `data`. Explicit failures and unrecognized decisions stop submission. A rejection with a non-zero `code`, such as an existing topic name, reports `BMQ_API_ERROR` with the server message, the BMQ business code in `details.business_code` and the trace ID in `request_id`. A negative decision in `data` reports `BMQ_CREATE_CHECK_FAILED`; a response without a recognized decision reports `BMQ_CREATE_CHECK_RESPONSE_ERROR` with the server message in `details.serverMessage`.

A successful submission reports `status: submitted`, the BMQ approval ID and `topic_verified: false`. Track the approval workflow, then query the exact cluster/topic on the same site and region:

```bash
bytedcli --site cn bpm ticket get --ticket-id 12345
bytedcli --site cn bmq topic list --vregion China-North --search demo-topic --all
bytedcli --site cn bmq topic get --vregion China-North --topic-id 12345
```

Approval IDs and Topic IDs are separate identifiers. Verify the returned cluster, topic identity and resource status before use. An accepted order is not evidence of an effective Topic. If the submission response cannot identify the BMQ approval, the command reports `BMQ_CREATE_RESULT_UNCONFIRMED`; inspect existing orders before retrying to avoid duplicates. The CLI does not automatically retry the creation request.

The preview's `order_request.OrderConfig` (including `ChargeItems`) is returned by BMQ's `order_config` calculation and forwarded unchanged, as the console does; the CLI does not set charge-item VDCs.

## Mirror requests

`bmq mirror create` submits the console's CreateMirror application (`POST /bpm/bpmApply`, BPM workflow key `apply_mirror`). Select the control plane with `--site` and the mirror's **target** region with `--vregion`; the CLI maps the target region's BPM area to the CreateMirror workflow ID. Supported sites are `cn`, `boe` (China-BOE regions), `i18n-bd` (alias `i18n`) and `i18n-tt`. Other sites or unmapped target regions fail before any network call.

```bash
bytedcli --site i18n-tt bmq mirror create \
  --vregion Singapore-Central --target-cluster demo_target_cluster --target-topic demo_topic \
  --source-vregion US-East --source-cluster demo_source_cluster --source-topic demo_topic \
  --mirror-cluster mirror_demo --service-tree '|Demo|Messaging' --owner demo-owner \
  --throughput-quota 5 --description 'demo mirror: US-East to Singapore-Central' --dry-run
# After reviewing the preview, repeat the same command with --yes to submit once.
bytedcli --site i18n-tt bpm ticket get --ticket-id 12345
bytedcli --site i18n-tt bmq mirror list --vregion Singapore-Central --search demo_topic --all
```

Inputs mirror the console form: target cluster/topic, source region (same control plane, different from the target region), source cluster/topic, mirror cluster, service tree (numeric ID or exact path), owners (repeatable or comma separated), `--throughput-quota` in MB/s (topic level, positive integer) and a 1-255 character `--description`. `--hash-policy` defaults to `KAFKA_DEFAULT` (also `PARTITION_ALIGN`, `RANDOM`, `TIME_RANDOM`). `--start-from newest` (default, no backfill) sends `whence: "1"`; `--start-from earliest` sends `whence: "0"`. Priority is fixed to `P2`, as in the console where the field is read-only.

Both preview and `--yes` run the same read-only preflight: the source and target topics must each resolve to one exact cluster/topic, the mirror cluster must be offered for the target region (`/mirror/mirrorCluster`), no mirror with the same source region/cluster/topic and target cluster/topic may exist (`BMQ_MIRROR_EXISTS`), and no unfinished `apply_mirror` ticket may cover the same pair (`BMQ_MIRROR_PENDING_TICKET`). Quotas above 100 MB/s add a warning, matching the console's confirmation dialog.

`--yes` posts once as the directly logged-in user, with the target region as `x-bcgw-vregion`, without retries. Success reports `status: submitted`, `ticket_id` and `mirror_verified: false`; the ticket then waits for BMQ admin review. In the BPM readback, `config.workflowConfigId` is BPM's internal workflow config ID and differs from the request's `workflowConfigId`. A non-zero business `code` or HTTP 4xx reports `BMQ_MIRROR_SUBMIT_REJECTED` (no ticket). Timeouts, gateway errors or a response without a ticket ID report `BMQ_MIRROR_SUBMIT_UNCONFIRMED`: the request may have reached BMQ, so check `bpm ticket list --workflow-key apply_mirror --keyword '"sourceTopic":"<topic>"'` and `bmq mirror list --all` before retrying.
