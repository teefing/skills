# Smart Promotion activities

`pearl smart-promotion list|get` reads Smart Promotion activities (the Pearl Smart Strategy pages under `/promote-platform/smart-strategy/activity`, backend path family `/api/v1/promotion/smart_promotion/*`). Both commands are read-only; drafting, submitting, and ending an activity stay in the console.

```bash
# Activities in a country, one page at a time; without filters the pages cover every activity
bytedcli --site i18n-tt pearl smart-promotion list --region mx --page-size 50

# Which activities use a voucher batch, or are bound to a resource place
bytedcli --site i18n-tt --json pearl smart-promotion list --region mx --voucher-type-id 7000000000000000002
bytedcli --site i18n-tt --json pearl smart-promotion list --region mx --resource-place-id 100

# Activities that have not ended, without test activities, on several resource places, all pages in one result
bytedcli --site us-ttp --json pearl smart-promotion list --region us --promotion-status ongoing,upcoming --is-test false --resource-place-id 100,99 --all

# Other filters: name substring, Libra flight ID, people, approval status
bytedcli --site i18n-tt pearl smart-promotion list --region sg --name sample --owner demo-owner --approval-status approved

# One activity: configuration, experiment groups, tasks
bytedcli --site i18n-tt --json pearl smart-promotion get --region mx --id 7000000000000000001

# Several activities in one call (comma-separated, repeated --id, or a file of IDs)
bytedcli --site us-ttp --json pearl smart-promotion get --region us --id 7000000000000000001,7000000000000000002
bytedcli --site us-ttp --json pearl smart-promotion get --region us --ids-file ids.txt --concurrency 6

# The same, plus every task benefit's claim window, status, and discount
bytedcli --site i18n-tt pearl smart-promotion get --region mx --id 7000000000000000001 --with-benefits
bytedcli --site us-ttp --json pearl smart-promotion get --region us --id 7000000000000000001
```

## Routing

- `--region` takes the country code and routes like Nova (see the Region routing table in `SKILL.md`): ROW countries need `--site i18n-tt`, `us` needs `--site us-ttp` or `--site us-ttp-bdee`, EU countries need an `eu-ttp` profile. The ID must belong to the selected region.
- Live-verified on 2026-10-25 with ROW (MX, SG), US-TTP, US-BDEE, and EU limited (DE). EU full is offline-covered only.

## `list`

- Filters: `--name` (substring), `--libra-id` (the Libra flight ID shown as `libra_id`), `--operator`, `--owner`, `--creator` (usernames), `--resource-place-id`, and `--voucher-type-id` (a voucher batch ID). ID filters must be digits. Filters combine.
- Status filters, applied by the backend:
  - `--promotion-status`: one or more of `invalid`, `ongoing`, `upcoming`, `expired` (or numeric codes); repeat or comma-separate.
  - `--approval-status`: one of `draft`, `pending_approval`, `approved` (or its code); the backend takes a single value.
  - `--is-test true|false`: only test activities, or none of them; omit it for both.
  - On US-TTP on 2026-10-27, `--promotion-status ongoing,upcoming --is-test false` cut 5835 activities to 123.
  - The status filter is coarse: 3 of 267 rows came back `expired` under `ongoing,upcoming`. Check each row's own `promotion_status`.
- There is no time-window filter: the backend list has no time field, and it sorts rows by `create_time` (newest first), not by end time. `--promotion-status ongoing,upcoming` leaves out most ended activities, but check each row's `promotion_status_name` (the filter can lag, see above); for "ended within the last N days", compare `configuration_info.end_time` yourself, or notice an activity leaving the ongoing set between runs.
- `--resource-place-id` accepts up to 50 IDs (repeat or comma-separate; leading zeros are ignored). The backend filter takes one ID, so several IDs need `--all`: the CLI reads every page of each ID and merges the activities by ID, newest `create_time` first. Each row then carries `matched_resource_place_ids`, the requested IDs that returned it; list rows have no tasks, so this is the only resource place information in a row. A single `--resource-place-id` adds the same field on a normal page.
- The console page pre-fills Operator with the signed-in user; the CLI does not, so an unfiltered list covers the whole region, one page at a time.
- `--page` is 1-based and `--page-size` accepts 1-500 (default 20). JSON carries `smart_promotions`, `total`, `current_count`, `page`, `page_size`, and `has_more` (true when another page may follow; when the backend sends no `total`, a full page counts as one).
- `--all` reads every page (500 rows each; `--page-size` is ignored, and `--page` other than 1 is rejected) and returns `{smart_promotions, total, current_count, page: 1, page_size, has_more: false}` (the merged result is one page, so `page_size` equals `total`), plus `resource_place_ids` when that filter is set. It stops with `PEARL_SMART_PROMOTION_LIST_LIMIT` rather than return a partial list when a scan runs past 40 pages.
- Each row is the backend row with `basic_info` lifted to the top level (`name`, `instruction`, `owner`, `creator`, `operators`); any other `basic_info` keys stay under `basic_info`. The schedule and AB settings stay under `configuration_info` (`start_time` / `end_time` are epoch milliseconds; text mode shows UTC). `extra_promotion_info` holds the console's child row for that activity when the backend returns one, otherwise `null`.

## `get`

- JSON is `{smart_promotion: {...}}` with the same lifted fields plus:
  - `experiment_group_infos[]` for AB activities: each group has `name`, `group_type`, `libra_vid`, and `tasks[]`.
  - `non_experiment_info.tasks[]` for activities without an AB test.
  - `experiment_layer_info` and the other backend fields, kept as returned.
- Each task carries `resource_place_ids[]` (the bound resource places) and `benefit_groups[]`; `benefit_groups[].benefit_ids[]` are voucher batch IDs (`voucher_type_id`) for voucher benefits. Text mode prints one row per task.
- The detail lists benefit IDs only. Add `--with-benefits` to also read each benefit's details.

## `get` with several IDs

- Pass several IDs with a repeated or comma-separated `--id`, or `--ids-file <path>` (IDs separated by commas, spaces, or new lines; `/dev/stdin` reads a pipe). Up to 1000 IDs; duplicates are read once.
- There is no batch detail endpoint, so each ID is one `get_smart_promotion` read, `--concurrency` at a time (1-8, default 4). In one process a read took about 1.2 s on US-TTP; 6 in parallel finished in about 2.4 s. A separate CLI process per ID costs 2-3 s each, mostly start-up.
- JSON is `{smart_promotions, errors}`:
  - `smart_promotions[]`: the activities that were read, in the requested order, each shaped like `get`'s `smart_promotion`.
  - `errors[]`: one entry `{id, code, backend_code, message, hint, status_code}` per ID that could not be read. `code` is what a single `get` would report (a number for a bare HTTP status), and a not-found entry carries the same `hint` as a single `get`. `backend_code` is the Pearl business code behind an API error: an unknown ID usually answers `PEARL_SMART_PROMOTION_API_ERROR` with `backend_code` `98001004`, and an ID from another country answers `98001040`. `PEARL_SMART_PROMOTION_NOT_FOUND` means the backend answered success without a record, and `PEARL_PROMOTION_FORBIDDEN` (`status_code` 403) means the page permission is missing.
- A failed ID does not stop the others. The result is still printed; when `errors` is not empty the envelope `status` is `partial_success` and the command exits non-zero. An expired Pearl session (`PEARL_AUTH_REQUIRED`) fails the whole batch instead.
- One `--id` value without `--ids-file` keeps the `{smart_promotion}` shape; passing the same ID twice still counts as several. `--with-benefits` reads one activity at a time and is rejected in the batch shape (several `--id` values or any `--ids-file`, even with one ID).

## `get --with-benefits`

- Collects the `benefit_ids` of every task, groups them by `benefit_type`, and reads their details (the console's benefit lookup, `get_benefit_info`) in batches of 30.
- JSON is `{smart_promotion, benefits, invalid_benefits, missing_benefit_ids}`:
  - `benefits[]`: one entry per returned benefit with `benefit_type`, `benefit_id`, `name`, `status`, `claim_start_time`, `claim_end_time` (epoch milliseconds) lifted from its detail object, plus the detail object as returned. Vouchers (`benefit_type` 1) carry `voucher_info` with the claim window and a discount object such as `product_voucher_discount_info` (discount amount, minimum spend); activities (`benefit_type` 3) carry `activity_info` with `time_range` and no claim window.
  - `invalid_benefits[]`: the backend's rejections as `{benefit_ids[], reason, benefit_type}`; one entry can cover several IDs, and `benefit_type` is the type they were requested as.
  - `missing_benefit_ids[]`: IDs the backend neither returned nor rejected, plus IDs whose `benefit_type` is not numeric (never requested). Treat these as unresolved, not as valid.
- Text mode adds a benefits table (ID, type, name, status, claim start, claim end in UTC), then rejected and missing IDs.
- Voucher stock, usage counters, and budget are not part of these details; read them per voucher batch with `pearl voucher get --id <benefit_id>` ([`voucher.md`](voucher.md)).

## `resource-place list|get`

- `resource-place list` returns the resource place registry: `id` (the number in an activity's `tasks[].resource_place_ids`), `key` (the server-side resource place key, such as `sample_search_popup`), `name`, `instruction`, `status` (raw), `support_regions`, `create_time`, `update_time` (epoch milliseconds), plus `record_id` (the backend's own record id) and the wire `basic_info` / `conf_info`. `--key` and `--name` are substring filters; `--page-size` accepts 1-500, and `--page-size 500` returns the whole registry in one page today. JSON is `{resource_places, total, current_count, page, page_size, has_more}`.
- `resource-place get --id <id>` takes the activity-facing `id` (leading zeros are ignored) and pages through the same list, at most 20 pages of 500 (the backend's detail read takes the record id and answers the same fields). JSON is `{resource_place}`.
- The registry is one global list, not numbered per country: ROW (MX, ID), US-TTP (US), and EU limited (GB) answered the same 180 records with the same `id` and `key` on 2026-10-26. Which countries a resource place serves is `support_regions`.
- There is no scene field; `conf_info.resource_place_app(s)` are the raw app values.
- Reading it needs the "Resource Place Management" page permission for the `--region` country; permissions are granted per country (SG answered HTTP 403 for an account that could read MX).

## Field values

- `promotion_status` and `approval_status` stay the backend's numeric codes. Each also gets a name field (from the console's constants), and that field is `null` for a code the CLI does not know:

  | Field              | Name field              | Codes                                                                             |
  | ------------------ | ----------------------- | --------------------------------------------------------------------------------- |
  | `promotion_status` | `promotion_status_name` | 1 `invalid`, 2 `ongoing`, 3 `upcoming`, 4 `expired`                               |
  | `approval_status`  | `approval_status_name`  | 1 `draft` (the console shows "Not submitted"), 2 `pending_approval`, 3 `approved` |

  A live activity is `ongoing`; it is normally also `approved`. Text mode shows `name (code)`.

- `tool_approve_status`, `group_type`, `task_type`, `benefit_type`, and the other enum fields are the backend's raw values; the CLI does not map them to names.
- int64 identifiers are decimal strings end-to-end.

## Errors

| Signal                                             | Meaning                                                                                             |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `PEARL_SMART_PROMOTION_API_ERROR`, code `98001004` | Invalid input; an unknown activity ID answers `invalid smart promotion ids` with the same code      |
| `PEARL_SMART_PROMOTION_API_ERROR`, code `98001040` | `region mismatch`: the ID belongs to another country; retry with its `--region`                     |
| `PEARL_SMART_PROMOTION_API_ERROR`, code `15006002` | The account lacks Smart Strategy permission in this region                                          |
| `PEARL_PROMOTION_FORBIDDEN` (HTTP 403)             | The account lacks this Pearl page's permission for the `--region` country; request it in Pearl      |
| `PEARL_SMART_PROMOTION_NOT_FOUND`                  | The backend answered success without an activity record                                             |
| `PEARL_SMART_PROMOTION_LIST_LIMIT`                 | `list --all` passed 40 pages for one scan; add `--promotion-status`, `--is-test`, or another filter |
| `PEARL_INPUT_ERROR`                                | A bad filter value, several `--resource-place-id` values without `--all`, or `--page` with `--all`  |
| `PEARL_SMART_PROMOTION_RESOURCE_PLACE_NOT_FOUND`   | No resource place in the registry has this `id`                                                     |
| `PEARL_SMART_PROMOTION_RESOURCE_PLACE_SCAN_LIMIT`  | `get` stopped after 20 pages without an answer; narrow with `resource-place list --key` / `--name`  |
| `PEARL_AUTH_REQUIRED`                              | Log in with `bytedcli --site <site> auth pearl-session login`                                       |
