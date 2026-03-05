#!/usr/bin/env python3
"""
GitHub Trending 爬虫脚本
获取 GitHub 热门仓库列表
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict, Optional
import argparse


def get_trending_repos(
    language: str = "",
    since: str = "daily",
    spoken_language: str = "",
) -> List[Dict]:
    """
    获取 GitHub Trending 仓库列表

    Args:
        language: 编程语言过滤 (如 python, javascript)
        since: 时间范围 (daily, weekly, monthly)
        spoken_language: 自然语言过滤 (如 zh, en)

    Returns:
        仓库列表
    """
    base_url = "https://bgithub.xyz/trending"
    if language:
        base_url += f"/{language}"

    params = {}
    if since != "daily":
        params["since"] = since
    if spoken_language:
        params["spoken_language_code"] = spoken_language

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return []

    return parse_trending_page(response.text)


def parse_trending_page(html: str) -> List[Dict]:
    """
    解析 GitHub Trending 页面 HTML

    Args:
        html: 页面 HTML 内容

    Returns:
        解析后的仓库列表
    """
    soup = BeautifulSoup(html, "html.parser")
    repos = []

    articles = soup.select("article.Box-row")

    for article in articles:
        repo = {}

        repo_name_elem = article.select_one("h2 a")
        if repo_name_elem:
            href = repo_name_elem.get("href", "").strip("/")
            repo["name"] = href
            repo["url"] = f"https://github.com/{href}"
            repo["author"] = href.split("/")[0] if "/" in href else ""
            repo["repo"] = href.split("/")[1] if "/" in href else ""

        desc_elem = article.select_one("p.col-9")
        if desc_elem:
            repo["description"] = desc_elem.get_text(strip=True)
        else:
            repo["description"] = ""

        lang_elem = article.select_one("[itemprop='programmingLanguage']")
        repo["language"] = lang_elem.get_text(strip=True) if lang_elem else "Unknown"

        stars_elem = article.select_one("a[href$='/stargazers']")
        if stars_elem:
            stars_text = stars_elem.get_text(strip=True).replace(",", "")
            repo["stars"] = int(stars_text) if stars_text.isdigit() else 0
        else:
            repo["stars"] = 0

        forks_elem = article.select_one("a[href$='/forks']")
        if forks_elem:
            forks_text = forks_elem.get_text(strip=True).replace(",", "")
            repo["forks"] = int(forks_text) if forks_text.isdigit() else 0
        else:
            repo["forks"] = 0

        stars_today_elem = article.select_one("span.float-sm-right")
        if stars_today_elem:
            text = stars_today_elem.get_text(strip=True)
            stars_today = text.split()[0].replace(",", "")
            repo["stars_today"] = int(stars_today) if stars_today.isdigit() else 0
        else:
            repo["stars_today"] = 0

        if repo.get("name"):
            repos.append(repo)

    return repos


def format_output(repos: List[Dict], output_format: str = "simple") -> str:
    """
    格式化输出结果

    Args:
        repos: 仓库列表
        output_format: 输出格式 (simple, json, markdown)

    Returns:
        格式化后的字符串
    """
    if output_format == "json":
        return json.dumps(repos, indent=2, ensure_ascii=False)

    if output_format == "markdown":
        lines = ["# GitHub Trending\n"]
        lines.append(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        for i, repo in enumerate(repos, 1):
            lines.append(f"## {i}. [{repo['name']}]({repo['url']})")
            lines.append(f"- 描述: {repo['description'] or '无'}")
            lines.append(f"- 语言: {repo['language']}")
            lines.append(f"- Stars: {repo['stars']:,} | Forks: {repo['forks']:,} | 今日新增: {repo['stars_today']:,}")
            lines.append("")
        return "\n".join(lines)

    lines = []
    lines.append("📱 GitHub Trending")
    lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    for i, repo in enumerate(repos, 1):
        lines.append(f"【{i}】{repo['name']}")
        lines.append(f"🔗 {repo['url']}")
        if repo['description']:
            desc = repo['description'][:80] + "..." if len(repo['description']) > 80 else repo['description']
            lines.append(f"📝 {desc}")
        lines.append(f"💻 {repo['language']}")
        lines.append(f"⭐ {repo['stars']:,} | 🍴 {repo['forks']:,} | 📈 +{repo['stars_today']:,}")
        lines.append("")

    lines.append(f"共 {len(repos)} 个仓库")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="获取 GitHub Trending 热门仓库")
    parser.add_argument(
        "-l", "--language",
        default="",
        help="按编程语言过滤 (如 python, javascript, go)"
    )
    parser.add_argument(
        "-s", "--since",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="时间范围 (默认: daily)"
    )
    parser.add_argument(
        "--spoken-language",
        default="",
        help="按自然语言过滤 (如 zh, en)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["simple", "json", "markdown"],
        default="simple",
        help="输出格式 (默认: simple)"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出到文件"
    )
    parser.add_argument(
        "-n", "--number",
        type=int,
        default=10,
        help="显示数量 (默认: 10)"
    )

    args = parser.parse_args()

    print(f"正在获取 GitHub Trending ({args.since})...")
    if args.language:
        print(f"语言过滤: {args.language}")

    repos = get_trending_repos(
        language=args.language,
        since=args.since,
        spoken_language=args.spoken_language,
    )

    if not repos:
        print("未获取到数据")
        return

    repos = repos[:args.number]

    output = format_output(repos, args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"结果已保存到: {args.output}")
    else:
        print(output)

    print(f"\n共获取 {len(repos)} 个仓库")


if __name__ == "__main__":
    main()
