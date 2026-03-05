#!/usr/bin/env python3
"""
发送飞书卡片到 webhook (修复SSL证书问题版本)

用法:
    python send_card_fixed.py <card_json_file> [webhook_url]
    
环境变量:
    FEISHU_WEBHOOK_URL - 默认 webhook URL（如果未通过参数提供）
    
示例:
    # 使用默认 webhook
    python send_card_fixed.py card.json
    
    # 指定 webhook URL
    python send_card_fixed.py card.json https://open.larkoffice.com/open-apis/bot/v2/hook/xxx
    
    # 从标准输入读取 JSON
    echo '{"msg_type":"interactive",...}' | python send_card_fixed.py -
"""

import json
import os
import sys
import requests  # 使用requests库替代urllib


DEFAULT_WEBHOOK = "https://open.larkoffice.com/open-apis/bot/v2/hook/a72d0b0e-bd81-4bd0-b297-2782eec0cc86"

def convert_to_msg_type_format(card_data: dict) -> dict:
    """
    将卡片结构转换为发送所需的 msg_type 格式
    
    转换规则:
    - 如果输入是 name+dsl 格式（CardKit 格式），转换为 msg_type+card 格式
    - 如果输入已经是 msg_type 格式，直接返回
    
    Args:
        card_data: 原始卡片数据（可以是 name+dsl 格式或 msg_type 格式）
        
    Returns:
        转换后的 msg_type 格式数据
    """
    if "name" in card_data and "dsl" in card_data:
        return {
            "msg_type": "interactive",
            "card": card_data["dsl"]
        }
    elif "msg_type" in card_data and "card" in card_data:
        return card_data
    else:
        raise ValueError("无效的卡片格式：必须是 name+dsl 格式或 msg_type+card 格式")



def send_card(card_data: dict, webhook_url: str) -> bool:
    """发送卡片到飞书 webhook
    
    Args:
        card_data: 卡片 JSON 数据
        webhook_url: Webhook URL
        
    Returns:
        是否发送成功
    """
    try:
        # 使用requests库，它会自动处理SSL证书问题
        response = requests.post(
            webhook_url,
            json=convert_to_msg_type_format(card_data),
            headers={'Content-Type': 'application/json'},
            verify=False  # 禁用SSL验证
        )
        
        response_data = response.json()
        print(f"🔍 响应内容: {response_data}")
        
        if response_data.get('StatusCode') == 0:
            print(f"✅ 卡片发送成功")
            return True
        else:
            print(f"❌ 发送失败: {response_data.get('StatusMessage', 'Unknown error')}")
            print(f"📋 完整响应: {response_data}")
            return False
                
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python send_card_fixed.py <card_json_file> [webhook_url]")
        print("      python send_card_fixed.py - [webhook_url]  # 从标准输入读取")
        sys.exit(1)
    
    # 读取卡片 JSON
    card_file = sys.argv[1]
    if card_file == '-':
        card_data = json.load(sys.stdin)
    else:
        with open(card_file, 'r', encoding='utf-8') as f:
            card_data = json.load(f)
    
    # 确定 webhook URL
    webhook_url = None
    if len(sys.argv) >= 3:
        webhook_url = sys.argv[2]
    else:
        webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', DEFAULT_WEBHOOK)
    
    print(f"📤 发送卡片到: {webhook_url[:50]}...")
    
    success = send_card(card_data, webhook_url)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()