# Source Writing Pattern

The referenced document uses two layers: an outer SP that routes to skills, and individual business skills that define exact tool behavior.

## Outer SP Pattern

- List available skills with short trigger descriptions.
- If a user clearly matches one skill, call `read_skill` before business tools.
- If intent is ambiguous or may match multiple skills, call `list_and_search_skills`, then `read_skill`.
- Tool calls must happen through the tool channel, not as user-visible JSON.
- Final replies are based only on real business-tool returns.
- Card output is one MiniAppCard plus concise text when a real card reference exists.

## Individual Skill Pattern

Write each skill in this order:

1. `name: <registered skill name>`
2. `description: <coverage sentence>`
3. `# <business title>工具 Skill`
4. `## 通用规则`
5. `## 场景路由`
6. Business-specific constraints and mapping tables.
7. `## 回复与卡片规则`
8. `## 小程序卡片输出协议（最高优先级）`
9. One section per tool.
10. `## 失败处理`
11. `## 通用注意事项`

Each tool section usually contains:

- `### 工具说明与使用场景`
- `### 使用场景`
- `### 入参规则` or `### 注意事项`
- `### 工具调用格式`
- `### 返回结果理解`

## Style Rules

- Prefer exact rules over explanation.
- Repeat critical constraints near the relevant tool, even if already stated globally.
- Use concrete phrases: "工具返回是事实来源", "不得编造", "用户没说不要猜", "必填", "只允许使用".
- Separate pure-consultation flows from card/transaction flows.
- For two-step decisions, require a discovery call first, then a filtered/confirmed call.
- Mark unsupported scenarios and say which tools must not be called.
- For user-visible output, provide short result text first, then the card protocol on a separate line.
- Do not expose internal terms such as `entity_list`, `reference_id`, `ref_id`, or tool-call JSON unless the user explicitly asks about the protocol.

## MiniAppCard Rules

Use the wrapper required by the environment:

```text
<RichMediaShow>{"type":"MiniAppCard","ref_id":["完整reference_id"]}</RichMediaShow>
```

or:

```text
<RichMediaCreation>{"type":"MiniAppCard","ref_id":["完整reference_id"]}</RichMediaCreation>
```

Rules to preserve:

- `ref_id` must come from the business tool's real card reference.
- Complete card references usually look like `<|card|>:1`.
- If only a card number is available, convert `1` to `<|card|>:1`.
- Do not use `entity_id`, `product_id`, `sku_id`, `order_id`, `order_no`, `coupon_id`, `widget_id`, `jump_url`, or `redirect_url` as `ref_id`.
- MiniAppCard JSON contains only `type` and `ref_id`.
- Default to one card per reply unless the skill explicitly allows multiple cards.
- Tool failure, empty result, non-success status, or missing card reference means no MiniAppCard and no invented success.

## Ecommerce Adaptation Notes

Ecommerce skills need especially strict handling for:

- Product facts: price, stock, specs, shop, delivery, coupon, and after-sales policy.
- Transaction stages: browse/search, detail confirmation, cart/checkout, order query, cancellation/refund, customer service.
- Confirmation boundaries: do not create orders, change address, cancel, refund, or apply coupons unless user intent and tool preconditions are clear.
- Identifier boundaries: product ids, sku ids, order ids, and card ids are not interchangeable.
- Privacy: avoid echoing full phone numbers, addresses, or account identifiers unless the product explicitly requires it.
