#!/usr/bin/env python3
"""
动态生成图标库文档

用法:
    # 列出所有图标(简略格式)
    python list_icons.py
    
    # 列出所有图标(详细格式,显示分类)
    python list_icons.py --detailed
    
    # 只列出特定一级分类
    python list_icons.py --category 线性
    
    # 只列出特定二级分类
    python list_icons.py --category 线性 --subcategory 系统
    
    # 按分类统计
    python list_icons.py --stats
    
    # 搜索图标名称
    python list_icons.py --search calendar
    
    # 组合使用
    python list_icons.py --category 彩色 --detailed
"""

import json
import sys
from pathlib import Path
from typing import Optional


def load_icons_data():
    """加载图标数据"""
    data_file = Path(__file__).parent / "icons_data.json"
    
    if not data_file.exists():
        print("❌ 错误: icons_data.json 不存在", file=sys.stderr)
        print("   请先运行 extract_icons.py 提取图标数据", file=sys.stderr)
        sys.exit(1)
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def show_stats(data: dict):
    """显示统计信息"""
    print("📊 图标库统计")
    print("=" * 50)
    
    total_icons = len(data["index"])
    print(f"图标总数: {total_icons}\n")
    
    for category in data["categories"]:
        cat_name = category["name"]
        subcat_count = len(category["subcategories"])
        cat_icon_count = sum(len(sub["icons"]) for sub in category["subcategories"])
        
        print(f"📁 {cat_name}")
        print(f"   - 子分类: {subcat_count} 个")
        print(f"   - 图标数: {cat_icon_count} 个")
        
        if subcat_count <= 10:  # 如果子分类不多,显示详情
            for subcategory in category["subcategories"]:
                icon_count = len(subcategory["icons"])
                print(f"      • {subcategory['name']}: {icon_count} 个")
        print()


def list_icons(
    data: dict,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    detailed: bool = False
):
    """列出图标"""
    
    # 显示使用说明
    print("# 图标库")
    print()
    print("本文档列出飞书卡片支持的所有图标名称。")
    print()
    print("## 如何获取图标 URL")
    print()
    print("需要获取图标 URL 时，请运行查询脚本：")
    print()
    print("```bash")
    print("# 查询单个图标")
    print("python scripts/get_icon_url.py add_outlined")
    print()
    print("# 批量查询多个图标")
    print("python scripts/get_icon_url.py add_outlined delete_outlined search_outlined")
    print()
    print("# 显示图标所属分类")
    print("python scripts/get_icon_url.py add_outlined --with-category")
    print()
    print("# JSON 格式输出")
    print("python scripts/get_icon_url.py add_outlined --json")
    print("```")
    print()
    print("---")
    
    # 过滤分类
    categories_to_show = data["categories"]
    if category:
        categories_to_show = [c for c in categories_to_show if c["name"] == category]
        if not categories_to_show:
            print(f"❌ 未找到分类: {category}", file=sys.stderr)
            return
    
    # 统计总数
    total_shown = 0
    
    for cat in categories_to_show:
        subcategories_to_show = cat["subcategories"]
        
        # 过滤子分类
        if subcategory:
            subcategories_to_show = [s for s in subcategories_to_show if s["name"] == subcategory]
            if not subcategories_to_show:
                continue
        
        # 显示分类标题
        print(f"\n## {cat['name']}")
        
        for subcat in subcategories_to_show:
            icons = subcat["icons"]
            
            # 搜索过滤
            if search:
                icons = [i for i in icons if search.lower() in i["name"].lower()]
            
            if not icons:
                continue
            
            print(f"\n### {subcat['name']}")
            
            if detailed:
                # 详细格式:每行一个图标
                print()
                for icon in icons:
                    print(f"- `{icon['name']}`")
                    total_shown += 1
            else:
                # 简略格式:每行 5 个图标
                print()
                icon_names = [icon["name"] for icon in icons]
                for i in range(0, len(icon_names), 5):
                    row = icon_names[i:i+5]
                    print("- " + ", ".join(f"`{name}`" for name in row))
                total_shown += len(icon_names)
    
    # 显示统计
    if search:
        print(f"\n🔍 搜索结果: 找到 {total_shown} 个包含 '{search}' 的图标")
    elif total_shown > 0:
        print(f"\n📋 共 {total_shown} 个图标")


def search_icons(data: dict, keyword: str):
    """搜索图标"""
    results = []
    keyword_lower = keyword.lower()
    
    for icon_name, info in data["index"].items():
        if keyword_lower in icon_name.lower():
            results.append({
                "name": icon_name,
                "category": info["category"],
                "subcategory": info["subcategory"],
                "url": info["url"]
            })
    
    if not results:
        print(f"❌ 未找到包含 '{keyword}' 的图标")
        return
    
    print(f"🔍 搜索 '{keyword}' 的结果 ({len(results)} 个):\n")
    
    for result in results:
        cat_path = result["category"]
        if result["subcategory"]:
            cat_path += f" / {result['subcategory']}"
        print(f"- `{result['name']}`")
        print(f"  分类: {cat_path}")
        print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="动态生成图标库文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --stats                          # 显示统计信息
  %(prog)s                                  # 列出所有图标
  %(prog)s --detailed                       # 列出所有图标(详细格式)
  %(prog)s --category 线性                   # 只列出线性图标
  %(prog)s --category 彩色 --detailed        # 列出彩色图标(详细格式)
  %(prog)s --search calendar                # 搜索包含 calendar 的图标
        """
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示统计信息"
    )
    
    parser.add_argument(
        "--category",
        help="筛选一级分类(如: 线性, 面性, 彩色)"
    )
    
    parser.add_argument(
        "--subcategory",
        help="筛选二级分类(需配合 --category 使用)"
    )
    
    parser.add_argument(
        "--search",
        help="搜索图标名称"
    )
    
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="显示详细格式(每行一个图标)"
    )
    
    args = parser.parse_args()
    
    # 加载数据
    data = load_icons_data()
    
    # 根据参数执行相应功能
    if args.stats:
        show_stats(data)
    elif args.search:
        search_icons(data, args.search)
    else:
        list_icons(
            data,
            category=args.category,
            subcategory=args.subcategory,
            detailed=args.detailed
        )


if __name__ == "__main__":
    main()
