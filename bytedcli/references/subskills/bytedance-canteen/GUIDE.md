---
name: bytedance-canteen
description: "Use when users ask what food is available at ByteDance canteens, including Meican login and read-only meal/order queries, and today's breakfast, lunch, or dinner menu for one or more office buildings, or mention ByteCanteen, 美餐, 字节食堂, 今天吃什么, 楼栋菜单, 早餐, 午餐, or 晚餐. Queries ByteCanteen in real time through bytedcli and reuses the saved Feishu Web session."
---

# ByteCanteen menus

Use `bytedcli canteen menu get` for real-time ByteDance canteen menus. For a first query or an abbreviated building name, search with a broad city or campus keyword first, then copy the complete returned building name verbatim into `--building`. Do not guess, shorten the returned name, or silently select among multiple candidates.

## Auth

The command reuses the Feishu Web session saved by bytedcli. If it reports `CANTEEN_FEISHU_SESSION_REQUIRED`, run:

```bash
bytedcli auth login --session --feishu
```

Never ask the user to paste a Feishu cookie, session, mina code, or ByteCanteen token. The CLI derives the ByteCanteen token internally and keeps it in memory only.

## Commands

```bash
# Discover candidates with a broad city or campus keyword
bytedcli canteen building search --keyword demo-city
bytedcli --json canteen building search --keyword demo-city

# Copy the complete returned building name, including city, campus, and phase
bytedcli canteen menu get --building demo-city-demo-campus-phase-2-building-c

# Query multiple buildings and one meal
bytedcli canteen menu get \
  --building demo-city-demo-campus-phase-2-building-c \
  --building demo-city-demo-campus-phase-2-building-d \
  --meal lunch

# Query a specific date and multiple meals
bytedcli canteen menu get \
  --building demo-city-demo-campus-phase-2-building-c \
  --date 2026-08-14 \
  --meal breakfast,dinner

# Structured output
bytedcli --json canteen menu get \
  --building demo-city-demo-campus-phase-2-building-c
```

`--building` and `--meal` are repeatable and also accept comma-separated values. The date defaults to today in `Asia/Shanghai`; omitting `--meal` queries breakfast, lunch, and dinner.

## Result handling

- For a first query or a shorthand building name, use `canteen building search` with a broad city or campus keyword. A shortened building name may return no candidates even when the building exists.
- Copy the displayed complete building name, or JSON `buildings[].name`, verbatim into `--building`; keep city, campus, phase, and building markers, and do not use the bracketed building ID.
- An exact normalized building-name match wins. If no exact match exists, the CLI accepts the result only when the search returns one candidate.
- Ambiguous building searches return candidates and do not silently select one.
- Multiple buildings are independent: successful menus are preserved, failures are reported, and the command exits nonzero on partial success.
- `hidingReason` is represented as an unavailable menu result. Do not invent dishes or recommendations.
- Text output follows building → meal → stall → dish category. Use `--json` for automation.

## References

- Read `../../invocation.md` for installation, global options, and JSON invocation rules.
- Read `../../troubleshooting.md` when authentication, network access, or command execution fails.

## Meican login and read-only queries

`canteen meican` connects through the existing Feishu Web session and ByteCanteen supplier SSO. It does not read a browser cookie database, require pasted tokens, persist Meican credentials, or submit/cancel/pay for orders. Each command obtains a short-lived in-memory session. `auth status` actively connects and verifies access by reading the calendar; a process exit code alone is not proof of authentication.

Use `canteen building search` first and pass a complete returned name to `--building`. This selects the **SSO entry building**, not a result filter: the Meican account can return meal sessions and existing orders across other buildings/floors. Select the intended session from its returned title, `tab`, `time`, and organization `namespace`.

```bash
bytedcli canteen building search --keyword demo-city
bytedcli --json canteen meican auth status --building demo-building
bytedcli --json canteen meican meal list --building demo-building --date 2026-01-01
bytedcli --json canteen meican order list --building demo-building --date 2026-01-01
bytedcli --json canteen meican restaurant list --building demo-building --tab demo-tab --time '2026-01-01 15:00'
bytedcli --json canteen meican menu get --building demo-building --tab demo-tab --time '2026-01-01 15:00' --restaurant demo-restaurant
bytedcli --json canteen meican address list --building demo-building --namespace demo-namespace
bytedcli --json canteen meican order get --building demo-building --id demo-order
```

- Dates default to today in `Asia/Shanghai`. Copy the returned `time` into subsequent requests: it is converted from the server's `targetTime` timestamp to `Asia/Shanghai`, and is not the pickup/locker opening time. A missing timestamp yields `time: null`; do not invent a value.
- `meal list` preserves upstream availability/status and existing orders. `order list` selects calendar entries containing an existing order; an order record alone does not prove payment or fulfillment. Check `order get` for detail.
- `menu get` maps the upstream flat `dishList` to `dishes`; it does not reconstruct `sectionList` groups or claim to include dishes available only through section references. Preserve section markers when interpreting the flat list.
- Structured results use `meals`, `orders`, `restaurants`, `dishes`, and `addresses`/`recentAddresses`. Copy `restaurants[].id` to `--restaurant` and `orders[].id` to `--id`. Optional values remain explicit `null`; a confirmed missing order returns `null`.
- Meican requires an existing authorization to the locker app for `auth:user.id:read`. The CLI refuses new or changed scopes. Missing/expired Feishu login: run `bytedcli auth login --session --feishu`. If Meican consent is missing, complete it personally in ByteCanteen before retrying. Never ask for Cookie, OAuth code, client secret, or access/refresh tokens.
- Meican data requests go to its own service; existing `canteen menu get` continues to query ByteCanteen menus. A successful canteen menu query does not prove Meican authentication.
- No purchase is made by these commands. Use the normal Meican ordering flow when an actual order is needed.
