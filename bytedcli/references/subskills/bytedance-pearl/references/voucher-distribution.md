# Voucher distribution placements and strategies

The voucher distribution platform (the Pearl `voucher-distribution-platform` pages, backend path family `/api/v1/promotion_delivery/*`) attaches delivery strategies to resource placements. A strategy lists the benefits a placement delivers (voucher packages or recall templates), with their experiment groups, filters, sort templates, and priority rules. These commands are read-only: placement and strategy writes (create, update, release, gray-rate changes, delete, sync, copy) are not available.

```bash
# Find a placement: --name is a case-insensitive substring, --key and --owner are substrings, --domain is exact
bytedcli --site us-ttp-bdee pearl voucher-distribution placement list --region us --key sample_key
bytedcli --site us-ttp-bdee pearl voucher-distribution placement list --region us --domain sample-domain --status online --page-size 50

# One placement
bytedcli --site us-ttp-bdee pearl voucher-distribution placement get --region us --id 7000000000000000001

# Current strategies: ongoing, gray-releasing, and draft, in one unpaged response
bytedcli --site us-ttp-bdee pearl voucher-distribution strategy list --region us --placement-id 7000000000000000001

# Published history (it also contains the ongoing strategy), paged
bytedcli --site us-ttp-bdee pearl voucher-distribution strategy list --region us --placement-id 7000000000000000001 --history --page 2

# One strategy's benefits, experiment groups, and priority rules
bytedcli --site us-ttp-bdee --json pearl voucher-distribution strategy get --region us --id 7000000000000000002
```

- `--region` selects the control plane as described in the Region routing section of `SKILL.md`. US was live-verified with `--site us-ttp-bdee`. A valid ROW session answered HTTP 403 for these reads, so treat ROW access as permission-dependent.
- Paging is 1-based. `--page-size` accepts 1-50 for `placement list` and for `strategy list --history`, because the backend rejects larger pages. `strategy list` without `--history` takes no paging flags, and its `total` is the complete count. In the paged reads, `total` is null when the backend omits it; `current_count` is always the number of rows on the page, and `has_more` says whether another page follows (without a total, a full page counts as more).
- Strategy `status` is `draft`, `gray_releasing`, `ongoing`, or `history`. `gray_rate` is a percentage, or null when the backend omits it; live ongoing strategies report 100. Placement `status` is `draft`, `online`, `offline`, or `deleted`.
- Strategies have no name field, neither in `strategy list` nor in `strategy get`. The console labels a strategy as `# <id>` followed by its `description`, so use `id` and `description` when a strategy needs a display name.
- Console links: a placement opens at `https://pearl.tiktok-row.net/voucher-distribution-platform/placement/detail/<placement_id>?oec_site=default&oec_region=<REGION>` and a strategy at `https://pearl.tiktok-row.net/voucher-distribution-platform/placement/detail/<placement_id>/view_strategy/<strategy_id>?oec_site=default&oec_region=<REGION>`, with `<REGION>` in upper case (for example `US`). When opened from the strategy list, the console also appends `&strategy_status=<1|2|3>` (draft, gray_releasing, ongoing); it is optional, and the console's own sync-history links omit it. `placement list`, `placement get`, and both `strategy list` modes return the matching link as `console_url` (null when a placement has no ID); `strategy get` does not, because the strategy detail does not say which placement it belongs to.
- `strategy get` returns enum codes as names, for example `source_type: benefit_package`, `filter_type: unclaimed_available`, and `claim_policy: manual_claim`. A code outside the known table stays as its raw number. The base64 fields are decoded into `extra_config` and, on each experiment group, `custom_filter_rule` and `custom_sort_rule`.
- `create_time` and `update_time` are epoch seconds; `publish_time` is epoch milliseconds. All three are strings.
- `placement get` with an unknown ID fails with `PEARL_VOUCHER_DISTRIBUTION_PLACEMENT_NOT_FOUND`. `strategy list` with an unknown placement ID and `strategy get` with an unknown strategy ID fail with `PEARL_VOUCHER_DISTRIBUTION_API_ERROR`, carrying the backend message (`the resource placement is not exist` or `strategy info is nil`). The backend reuses those business codes for other input errors, so read the message rather than the code.
