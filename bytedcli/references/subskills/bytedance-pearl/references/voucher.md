# Voucher stock and usage

`pearl voucher get` reads one voucher batch from voucher management (the Pearl new-voucher-management pages, backend `GET /api/v1/promotion/business/get_voucher`): stock, live usage counters, budget, and claim window. It is read-only.

```bash
# Voucher batch IDs come from a Smart Promotion activity's tasks
bytedcli --site i18n-tt pearl smart-promotion get --region mx --id 7000000000000000001 --with-benefits

# Stock, usage, and budget of one voucher batch
bytedcli --site i18n-tt pearl voucher get --region mx --id 7000000000000000002
bytedcli --site us-ttp --json pearl voucher get --region us --id 7000000000000000002
```

## Output

- JSON is `{voucher: {...}}`: the backend's voucher detail with `id`, `name`, `status`, `region`, `claim_start_time`, and `claim_end_time` (epoch milliseconds) lifted to the top level, plus:
  - `stock_limit_info`: configured stock `total_quantity` and the per-user limit `claim_quantity_per_user`.
  - `usage_info`: live counters as decimal strings: `claimed`, `claim_returned`, `net_claimed` (claimed minus returned), `used`, `use_returned`, `net_used`, and on the ROW host `write_off`.
  - `budget_info`: `total_budget`, `used_budget`, `withholding_budget`, `available_budget`, `released_budget`, each in the local currency (`total_budget`) and USD (`total_budget_dollar`) with `percent` already a percentage of the total budget.
  - `approval_info` and the other voucher fields (`discount_info`, `restricted_collection_rule`, `operation_infos`, ...), kept as returned.
- The response's user directory (names and emails) is not included.
- Text mode prints the voucher, usage, and budget tables; times are UTC.
- `status` and other enum fields are the backend's raw values.

## Routing and errors

- `--region` routes like the rest of Pearl (see the Region routing table in `SKILL.md`). The backend does not check the voucher against `--region`, so a voucher read under another country still answers; its own country is `region` in the output.
- Live-verified on 2026-10-25 with ROW (MX), US-TTP, US-BDEE, and EU limited (DE).
- Under `--site us-ttp-bdee` the Pearl console reads this page from the ROW host; the CLI reads the US-TTP host, like every other Pearl command for `us`. Both answered the same voucher on 2026-10-25, with live counters that differed only by the claims made between the two reads; only the ROW host adds `usage_info.write_off`.
- `PEARL_VOUCHER_NOT_FOUND`: no voucher batch with this ID. `PEARL_VOUCHER_API_ERROR` carries the backend code and message; code `15006002` means the account lacks permission in this region. `PEARL_PROMOTION_FORBIDDEN` (HTTP 403) means the same for the voucher page in the `--region` country.
