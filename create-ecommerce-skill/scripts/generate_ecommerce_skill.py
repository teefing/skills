#!/usr/bin/env python3
"""Generate a first-draft ecommerce mini-app skill prompt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_TOOLS = [
    {
        "name": "Ecommerce_searchProduct",
        "description": "搜索商品并返回商品候选、价格摘要和商品卡片。",
        "when": "用户搜索商品、找某类商品、比较品牌/规格、询问有没有某商品时使用。",
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "description": "商品关键词或用户原始需求"},
            "category": {"type": "string", "description": "商品类目，可选"},
            "brand": {"type": "string", "description": "品牌，可选"},
            "price_min": {"type": "number", "description": "最低价格，可选"},
            "price_max": {"type": "number", "description": "最高价格，可选"},
        },
    },
    {
        "name": "Ecommerce_getProductDetail",
        "description": "查询商品详情、SKU、价格、库存、优惠、配送和售后政策。",
        "when": "用户询问商品详情、规格、价格、库存、优惠、配送或售后政策，且已有明确商品时使用。",
        "required": ["product_id"],
        "properties": {
            "product_id": {"type": "string", "description": "商品 ID，必须来自搜索或详情工具返回"},
            "sku_id": {"type": "string", "description": "SKU ID，可选"},
        },
    },
    {
        "name": "Ecommerce_createOrderPreview",
        "description": "生成下单预览或购买确认卡片。",
        "when": "用户明确要购买、下单、加入购物车或确认某个 SKU 时使用。",
        "required": ["product_id"],
        "properties": {
            "product_id": {"type": "string", "description": "商品 ID，必须来自工具返回"},
            "sku_id": {"type": "string", "description": "SKU ID；商品存在多规格时必填"},
            "quantity": {"type": "integer", "description": "购买数量，可选，默认 1"},
            "coupon_id": {"type": "string", "description": "优惠券 ID，可选，必须来自工具返回"},
        },
    },
    {
        "name": "Ecommerce_queryOrder",
        "description": "查询订单状态、物流、支付状态和历史订单。",
        "when": "用户询问订单状态、物流、是否发货、是否支付成功、历史订单时使用。",
        "required": ["search_type"],
        "properties": {
            "search_type": {"type": "string", "enum": ["recent", "ongoing", "history", "specific"], "description": "查询类型"},
            "order_id": {"type": "string", "description": "订单 ID，可选"},
        },
    },
    {
        "name": "Ecommerce_customerService",
        "description": "获取客服、售后、退款退货、投诉或政策咨询入口。",
        "when": "用户咨询退款、退货、售后、投诉、人工客服、政策或订单异常时使用。",
        "required": ["issue_type"],
        "properties": {
            "issue_type": {"type": "string", "description": "问题类型，如 refund、return、complaint、manual_service"},
            "order_id": {"type": "string", "description": "订单 ID，可选，必须来自工具返回或用户明确提供"},
        },
    },
]


def load_tools(path: str | None) -> list[dict]:
    if not path:
        return DEFAULT_TOOLS
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("--tools-json must contain a JSON array")
    for tool in data:
        if not isinstance(tool, dict) or "name" not in tool:
            raise ValueError("each tool must be an object with at least a name")
    return data


def schema_for(tool: dict) -> dict:
    properties = tool.get("properties") or {
        "TODO": {"type": "string", "description": "替换为真实参数"}
    }
    schema = {
        "name": tool["name"],
        "description": tool.get("description", "替换为真实工具说明。"),
        "parameters": {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        },
    }
    required = tool.get("required")
    if required:
        schema["parameters"]["required"] = required
    return schema


def card_block(wrapper: str) -> str:
    return f"""MiniAppCard 唯一允许的输出格式：

<{wrapper}>{{"type":"MiniAppCard","ref_id":["完整reference_id"]}}</{wrapper}>

其中：

- `ref_id` 必须来自工具返回的卡片引用。
- 完整 reference_id 通常形如 `<|card|>:1`、`<|card|>:4`。
- 如果只出现卡片编号 `1`，必须补全为 `"<|card|>:1"`。
- MiniAppCard JSON 内只包含 `type` 和 `ref_id` 两个字段。
- 默认每次回复只输出一张 MiniAppCard。
- 不要把 `product_id`、`sku_id`、`order_id`、`order_no`、`coupon_id`、`widget_id`、`jump_url` 或 `redirect_url` 当作 `ref_id`。
- 工具失败、无卡片引用、状态异常或主体为空时，不输出 MiniAppCard，也不要编造成功。"""


def generate(skill_name: str, title: str, wrapper: str, tools: list[dict]) -> str:
    tool_names = "、".join(tool["name"] for tool in tools)
    lines: list[str] = []
    lines.append(f"name: {skill_name}")
    lines.append("")
    lines.append(
        "description: 电商购物 Agent 工具使用说明。用于商品搜索、商品详情、SKU/规格选择、优惠与库存查询、加购/下单、订单查询、取消订单、退款售后和客服咨询等场景；"
        f"覆盖 {tool_names} 的调用边界、参数规则、MiniAppCard 输出规范和失败兜底。"
    )
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(
        "本 Skill 是电商购物相关 system prompt 的完整来源。只要用户意图涉及商品查找、商品对比、规格选择、价格/库存/优惠查询、加购/下单、订单状态、取消、退款、售后或客服咨询，就按本 Skill 执行；不要假设外层 system prompt 还会补充电商规则。"
    )
    lines.append("")
    lines.append("## 通用规则")
    lines.append("")
    lines.append("工具返回是事实来源，不得编造商品、价格、库存、优惠、配送时效、订单状态、退款状态、售后政策、客服入口或卡片引用。")
    lines.append("")
    lines.append("所有 required 参数必须提供；用户没说、历史没有、工具返回没有的字段不要猜。")
    lines.append("")
    lines.append("商品 `product_id`、SKU `sku_id`、订单 `order_id/order_no`、卡片 `reference_id` 不能互相替代。")
    lines.append("")
    lines.append("## 场景路由")
    lines.append("")
    for tool in tools:
        when = tool.get("when", f"符合 {tool['name']} 的业务场景时使用。")
        lines.append(f"- {when}调用 `{tool['name']}`。")
    lines.append("")
    lines.append("创建订单、取消订单、退款退货属于高风险动作；必须有明确用户意图和真实订单标识。")
    lines.append("")
    lines.append("## 商品与 SKU 规则")
    lines.append("")
    lines.append("用户只给商品类目但没有明确商品时，先搜索，不要直接下单。")
    lines.append("")
    lines.append("商品有多个规格/SKU 时，必须确认规格；用户没有指定颜色、尺码、版本等 required SKU 字段时，不得下单。")
    lines.append("")
    lines.append("价格、优惠、库存、配送时效以最近一次详情或下单预览工具返回为准。")
    lines.append("")
    lines.append("## 回复与卡片规则")
    lines.append("")
    lines.append("文本与卡片互补：文本提炼结论、说明选择原因和下一步；卡片承载商品、下单、订单、售后或客服入口。")
    lines.append("")
    lines.append("纯咨询场景如果只需要价格、库存或政策说明，可只输出自然语言，不输出 MiniAppCard。")
    lines.append("")
    lines.append("## 小程序卡片输出协议（最高优先级）")
    lines.append("")
    lines.append(card_block(wrapper))
    for index, tool in enumerate(tools, start=1):
        lines.append("")
        lines.append(f"## 工具{index}：{tool['name']}")
        lines.append("")
        lines.append("### 工具说明与使用场景")
        lines.append("")
        lines.append(tool.get("description", "替换为真实工具说明。"))
        lines.append("")
        lines.append("### 使用场景")
        lines.append("")
        lines.append(tool.get("when", f"符合 `{tool['name']}` 的业务诉求时使用。"))
        lines.append("")
        lines.append("### 入参规则")
        lines.append("")
        required = tool.get("required") or []
        if required:
            lines.append("必填参数：" + "、".join(f"`{name}`" for name in required) + "。")
        else:
            lines.append("根据真实工具 schema 填写入参；用户没说、历史没有、工具返回没有的字段不要猜。")
        lines.append("")
        lines.append("### 工具调用格式")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(schema_for(tool), ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("### 返回结果理解")
        lines.append("")
        lines.append("优先使用工具返回的摘要、状态、价格、库存、卡片引用和下一步建议；不要展示内部 ID，除非用户明确需要核对。")
    lines.append("")
    lines.append("## 失败处理")
    lines.append("")
    lines.append("工具失败、空结果、返回错误或缺少必要数据时，只说明当前无法完成，并给出下一步建议；不得编造商品、价格、库存、订单或卡片。")
    lines.append("")
    lines.append("## 通用注意事项")
    lines.append("")
    lines.append("工具调用名必须使用线上注册名。不要把内部协议、工具 JSON、`entity_list`、`reference_id`、`ref_id` 等暴露给用户。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-name", required=True)
    parser.add_argument("--title", default="电商购物工具 Skill")
    parser.add_argument("--wrapper", choices=["RichMediaShow", "RichMediaCreation"], default="RichMediaShow")
    parser.add_argument("--tools-json", help="JSON array of tool definitions")
    parser.add_argument("--output", help="Write generated Markdown to this file")
    args = parser.parse_args()

    text = generate(args.skill_name, args.title, args.wrapper, load_tools(args.tools_json))
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
