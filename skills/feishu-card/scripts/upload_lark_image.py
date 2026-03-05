#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书图片上传脚本

通过 AIME 工具上传图片到飞书

用法:
    python upload_lark_image.py <image_file_path>
    
示例:
    python upload_lark_image.py /path/to/image.jpg
    python upload_lark_image.py /absolute/path/to/image.png
"""
import os
import json
import sys
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.aime', 'sdk', 'python'))
from aime_client import call_aime_tool


def upload_lark_image(file_path):
    """
    Upload image to Lark using AIME tool.
    
    Args:
        file_path: Absolute path to the image file
        
    Returns:
        Upload result or None if failed
    """
    print(f'[INFO] 开始上传图片: {file_path}...')
    
    # 检查文件是否存在
    if not os.path.isfile(file_path):
        print(f'[ERROR] 文件不存在: {file_path}')
        return None
    
    # 检查是否为绝对路径
    if not os.path.isabs(file_path):
        print(f'[ERROR] 必须使用绝对路径: {file_path}')
        return None
    
    # 准备上传参数
    params = {
        "file_path": file_path
    }
    
    # 调用上传图片工具
    result = call_aime_tool("lark_card_message", "lark_upload_image", params)
    
    if result and result.get("response"):
        print('[OK] 图片上传成功')
        return result["response"]
    else:
        print('[ERROR] 图片上传失败')
        return None


def main():
    """Main execution flow."""
    if len(sys.argv) < 2:
        print("用法: python upload_lark_image.py <image_file_path>")
        print("\n示例:")
        print("  python upload_lark_image.py /path/to/image.jpg")
        print("  python upload_lark_image.py /absolute/path/to/image.png")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # 上传图片
    result = upload_lark_image(file_path)
    
    if result:
        print('[SUCCESS] 图片上传完成')
        print(f'响应结果: {json.dumps(result, ensure_ascii=False, indent=2)}')
        sys.exit(0)
    else:
        print('[FAILED] 图片上传失败')
        sys.exit(1)


if __name__ == '__main__':
    main()