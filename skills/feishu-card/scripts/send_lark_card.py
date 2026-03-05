#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书卡片发送脚本

支持两种发送方式：
1. 通过飞书开放 API 发送卡片到指定邮箱或群组
2. 通过 webhook 直接发送飞书卡片

配置：
    首次使用前需要创建 lark_config.json 文件，包含：
    {
        "app_id": "your_app_id",
        "app_secret": "your_app_secret"
    }

用法:
    # API 方式（自动识别邮箱或群组ID）
    python send_lark_card.py <receiver_id> <card_json_file>
    python send_lark_card.py <receiver_id> <card_json_string>
    
    # Webhook 方式
    python send_lark_card.py --webhook <webhook_url> <card_json_file>
    python send_lark_card.py --webhook <webhook_url> <card_json_string>
    
示例:
    # API 方式 - 发送到邮箱（自动识别）
    python send_lark_card.py user@example.com card.json
    
    # API 方式 - 发送到群组（自动识别 oc_ 开头的群组ID）
    python send_lark_card.py oc_xxx card.json
    
    # Webhook 方式
    python send_lark_card.py --webhook https://open.larkoffice.com/open-apis/bot/v2/hook/xxx card.json
"""
import os
import re
import json
import sys
import requests
from pathlib import Path
from typing import Optional, Tuple

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'lark_config.json')
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), '.lark_token_cache.json')

LARK_API_BASE = "https://open.feishu.cn/open-apis"

# 硬编码的飞书应用凭证
APP_ID = "cli_a906250f0f389bd9"
APP_SECRET = "gOHjMw0ditA5ygs7WMfZPcQrJqlNsi72"


def detect_id_type(receiver_id: str) -> str:
    """
    自动判断 receiver_id 的类型
    
    规则:
    - 邮箱：包含 @ 符号，符合邮箱格式
    - 群组ID：以 oc_ 开头
    
    Args:
        receiver_id: 接收者ID（邮箱或群组ID）
        
    Returns:
        'email' 或 'chat_id'
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, receiver_id):
        return "email"
    elif receiver_id.startswith("oc_"):
        return "chat_id"
    else:
        print(f"[WARN] 无法自动识别 '{receiver_id}' 的类型，默认作为邮箱处理")
        return "email"


def load_config() -> Tuple[str, str]:
    """加载飞书应用配置（使用硬编码凭证）"""
    return APP_ID, APP_SECRET


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """
    获取飞书 tenant_access_token
    
    Args:
        app_id: 应用 ID
        app_secret: 应用密钥
        
    Returns:
        tenant_access_token
    """
    url = f"{LARK_API_BASE}/auth/v3/tenant_access_token/internal"
    
    response = requests.post(
        url,
        json={
            "app_id": app_id,
            "app_secret": app_secret
        },
        headers={'Content-Type': 'application/json'}
    )
    
    data = response.json()
    
    if data.get('code') != 0:
        raise Exception(f"获取 token 失败: {data.get('msg', 'Unknown error')}")
    
    return data['tenant_access_token']


def send_card_via_api(receiver_id: str, card_content: str, id_type: str, token: str) -> bool:
    """
    通过飞书 API 发送卡片消息
    
    Args:
        receiver_id: 接收者ID
        card_content: 卡片内容 JSON 字符串
        id_type: ID 类型 (email 或 chat_id)
        token: tenant_access_token
        
    Returns:
        是否发送成功
    """
    url = f"{LARK_API_BASE}/im/v1/messages?receive_id_type={id_type}"
    
    payload = {
        "receive_id": receiver_id,
        "msg_type": "interactive",
        "content": card_content
    }
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    
    if data.get('code') == 0:
        print(f"[OK] 飞书卡片发送成功")
        return True
    else:
        print(f"[ERROR] 发送失败: {data.get('msg', 'Unknown error')}")
        print(f"[ERROR] 错误码: {data.get('code')}")
        return False


def send_card_to_webhook(card_data: dict, webhook_url: str) -> bool:
    """发送卡片到飞书 webhook
    
    Args:
        card_data: 卡片 JSON 数据
        webhook_url: Webhook URL
        
    Returns:
        是否发送成功
    """
    try:
        response = requests.post(
            webhook_url,
            json=card_data,
            headers={'Content-Type': 'application/json'},
            verify=False
        )
        
        response_data = response.json()
        print(f"[INFO] 响应内容: {response_data}")
        
        if response_data.get('StatusCode') == 0:
            print(f"[OK] 卡片发送成功")
            print(f"[INFO] 可以在飞书 CardKit 平台导入该卡片进行二次编辑: https://open.feishu.cn/cardkit")
            return True
        else:
            print(f"[ERROR] 发送失败: {response_data.get('StatusMessage', 'Unknown error')}")
            print(f"[ERROR] 完整响应: {response_data}")
            return False
                
    except Exception as e:
        print(f"[ERROR] 错误: {str(e)}")
        return False


def convert_to_msg_type_format(card_data: dict) -> dict:
    """
    将卡片结构转换为发送所需的格式
    
    转换规则:
    - 如果输入是 name+dsl 格式（CardKit 格式），转换为 msg_type+card 格式
    - 如果输入已经是 msg_type 格式，直接返回
    
    Args:
        card_data: 原始卡片数据
        
    Returns:
        转换后的格式数据
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


def main():
    """Main execution flow."""
    if len(sys.argv) < 2:
        print("API 模式用法: python send_lark_card.py <receiver_id> <card_json_file_or_string>")
        print("Webhook 模式用法: python send_lark_card.py --webhook <webhook_url> <card_json_file_or_string>")
        print("\nAPI 模式示例:")
        print("  python send_lark_card.py user@example.com card.json")
        print("  python send_lark_card.py oc_xxx card.json")
        print("\nWebhook 模式示例:")
        print("  python send_lark_card.py --webhook https://open.larkoffice.com/open-apis/bot/v2/hook/xxx card.json")
        sys.exit(1)
    
    # 检查是否使用 webhook 模式
    if sys.argv[1] == "--webhook":
        if len(sys.argv) < 4:
            print("Webhook 模式用法: python send_lark_card.py --webhook <webhook_url> <card_json_file_or_string>")
            sys.exit(1)
        
        webhook_url = sys.argv[2]
        card_input = sys.argv[3]
        
        if os.path.isfile(card_input):
            try:
                with open(card_input, 'r', encoding='utf-8') as f:
                    card_data = json.load(f)
                print(f"[INFO] 从文件加载卡片内容: {card_input}")
            except Exception as e:
                print(f"[ERROR] 读取卡片文件失败: {e}")
                sys.exit(1)
        else:
            try:
                card_data = json.loads(card_input)
                print("[INFO] 使用命令行传入的卡片 JSON 字符串")
            except json.JSONDecodeError as e:
                print(f"[ERROR] 无效的 JSON 字符串: {e}")
                sys.exit(1)
        
        card_data = convert_to_msg_type_format(card_data)
        print(f"[INFO] 发送卡片到: {webhook_url[:50]}...")
        success = send_card_to_webhook(card_data, webhook_url)
        sys.exit(0 if success else 1)
    
    # API 模式
    if len(sys.argv) < 3:
        print("API 模式用法: python send_lark_card.py <receiver_id> <card_json_file_or_string>")
        sys.exit(1)
    
    receiver_id = sys.argv[1]
    card_input = sys.argv[2]
    
    id_type = detect_id_type(receiver_id)
    print(f"[INFO] 检测到 ID 类型: {id_type}")
    
    if os.path.isfile(card_input):
        try:
            with open(card_input, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            print(f"[INFO] 从文件加载卡片内容: {card_input}")
        except Exception as e:
            print(f"[ERROR] 读取卡片文件失败: {e}")
            sys.exit(1)
    else:
        try:
            card_data = json.loads(card_input)
            print("[INFO] 使用命令行传入的卡片 JSON 字符串")
        except json.JSONDecodeError as e:
            print(f"[ERROR] 无效的 JSON 字符串: {e}")
            sys.exit(1)
    
    card_data = convert_to_msg_type_format(card_data)
    card_content = json.dumps(card_data.get('card', card_data), ensure_ascii=False)
    
    print(f"[INFO] 开始发送飞书卡片到 {receiver_id}...")
    
    try:
        app_id, app_secret = load_config()
        token = get_tenant_access_token(app_id, app_secret)
        success = send_card_via_api(receiver_id, card_content, id_type, token)
        
        if success:
            print('[SUCCESS] 卡片发送完成')
            print(f"[INFO] 可以在飞书 CardKit 平台导入该卡片进行二次编辑: https://open.feishu.cn/cardkit")
            sys.exit(0)
        else:
            print('[FAILED] 卡片发送失败')
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
