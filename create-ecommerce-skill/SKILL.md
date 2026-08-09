---
name: create-ecommerce-skill
description: Create AgentHub/MCP mini-app skill prompts for ecommerce, shopping, product search, cart, checkout, order, refund, after-sales, coupon, and customer-service scenarios. Use when the user asks to generate a skill similar to the referenced mini-app skills, write or adapt an ecommerce business skill, produce SP skill entries, define tool routing and parameter rules, or turn ecommerce tool schemas into a production-ready skill prompt with MiniAppCard output rules.
---

# Create Ecommerce Skill

Use this skill to generate a business skill prompt in the same style as the referenced mini-app document: compact `name`/`description`, explicit trigger coverage, strict tool-routing rules, parameter constraints, MiniAppCard protocol, per-tool JSON schemas, and failure fallbacks.

## Required Reading

Read [references/writing-pattern.md](references/writing-pattern.md) before drafting. It summarizes the source document's writing pattern and the conventions to preserve.

Read [references/ecommerce-skill-template.md](references/ecommerce-skill-template.md) when the user wants a full skill prompt or when tool schemas are incomplete.

## Input Checklist

Collect or infer these items before writing:

- Skill name, usually `doubao-ecommerce-skill-<owner>` or another MCP platform name.
- Ecommerce scope: product search, product detail, cart, checkout, order status, cancellation, refund, after-sales, coupon, address, customer service.
- Tool names and JSON schemas. If schemas are missing, use template placeholders and clearly mark fields that must be replaced.
- Card wrapper required by the target environment: `<RichMediaShow>` or `<RichMediaCreation>`. Default to `<RichMediaShow>` unless the user names knowledge-network/SP requirements that use Creation.
- Unsupported capabilities: price guarantees, manual refund acceleration, merchant-side changes, address edits after shipping, direct payment completion, inventory promises, or any business-specific exclusions.
- Sensitive-data rules: phone, address, order id, user id, payment details, and coupon/account identifiers.

Ask at most one concise question only if the missing data would make the generated skill unusable. Otherwise produce a high-quality draft with explicit placeholders.

## Generation Workflow

1. Write the skill header:
   - `name: <skill-name>`
   - `description: <one sentence covering trigger scenarios, covered tools, MiniAppCard rules, and failure fallback>`

2. Write the body in this order:
   - Title, e.g. `# 电商购物工具 Skill`
   - Complete-source statement: this skill is the full source of ecommerce tool rules.
   - `## 通用规则`
   - `## 场景路由`
   - Domain-specific constraints such as product selection, inventory/price, address, coupon, payment, refund, and customer-service rules.
   - `## 回复与卡片规则`
   - `## 小程序卡片输出协议（最高优先级）`
   - One section per tool: `## 工具1：<tool_name>`, with usage, parameter rules, notes, JSON schema, and result interpretation.
   - `## 失败处理`
   - `## 通用注意事项`

3. Preserve the source style:
   - Use concrete rules, not abstract advice.
   - Use "不得/不要/必须/只能/优先" for fragile behavior.
   - Treat tool returns as the only fact source.
   - Never invent product price, stock, order state, refund state, card reference, coupon availability, or delivery timing.
   - Keep user-facing text separate from card protocol.

4. Add SP integration snippets only when requested:
   - A skill list entry for the outer SP.
   - `list_and_search_skills` / `read_skill` routing rules.
   - A one-card final-response rule matching the selected card wrapper.

## Optional Script

For a fast first draft, run:

```bash
python3 /Users/bytedance/.codex/skills/create-ecommerce-skill/scripts/generate_ecommerce_skill.py \
  --skill-name doubao-ecommerce-skill-demo \
  --wrapper RichMediaShow
```

Pass `--tools-json path/to/tools.json` when real tool schemas are available. The script emits Markdown that should still be reviewed against the checklist above.

## Quality Gate

Before returning the generated skill, verify:

- The `description` includes trigger scenarios and covered tools.
- Every required parameter is represented in a tool schema.
- No unsupported capability is silently routed to a tool.
- Order/refund/customer-service routes do not fabricate status.
- MiniAppCard `ref_id` can only come from real tool card references.
- Internal tool-call JSON and protocol tags are forbidden from user-visible replies.
- The final output is directly pasteable into the MCP skill editor.
