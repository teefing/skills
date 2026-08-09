#!/usr/bin/env python3
"""拉取仓库级自定义工作流（custom workflows）。

按当前仓库向服务端拉取自定义评审 workflow 列表，写入 <output-dir>/custom_workflows.json，
供「自定义工作流检测」主线与通用检测并行执行。

使用方式:
  python scripts/fetch_custom_workflows.py --output-dir "<WORK_DIR>" \
    [--repo "<org/repo>"] [--git-remote "<git remote 值>"] [--endpoint "<base url>"]

仓库标识解析优先级：--repo > --git-remote 解析 > 自动从 `git remote` 解析。
接口实测对 `org/repo` 与完整 git url 均能容错，故无法解析出 `org/repo` 时原样把 remote 串传给接口。

设计原则：任何失败（解析失败、网络错误、非 0 返回码、未配置）都不抛出，
落到 workflows: [] 并在 stderr 记原因，**始终 exit 0**，不阻断 skill 主流程。
"""

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

# 自定义工作流拉取端点，可被环境变量覆盖
DEFAULT_ENDPOINT = "https://satcheck.bytedance.net"
ENDPOINT_ENV = "BITS_CODE_GUARD_WORKFLOW_ENDPOINT"
WORKFLOW_PATH = "/a2a/skill/v2/review/workflows"
OUTPUT_FILENAME = "custom_workflows.json"
HTTP_TIMEOUT = 10


def run_git(args: List[str]) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        return ""


def get_git_remote_url() -> str:
    """取当前仓库的 remote url：优先 origin，回退首个 remote。"""
    try:
        url = run_git(["remote", "get-url", "origin"])
        if url:
            return url
        remotes = run_git(["remote"])
        if not remotes:
            return ""
        lines = remotes.splitlines()
        if not lines:
            return ""
        first = lines[0].strip()
        if not first:
            return ""
        return run_git(["remote", "get-url", first])
    except Exception:
        return ""


def parse_repo_from_remote(remote: str) -> str:
    """从 git remote url 解析出 `org/repo`。

    支持常见形态：
      - git@code.byted.org:pdi-qa/flux-bug-finder.git
      - ssh://git@code.byted.org/pdi-qa/flux-bug-finder.git
      - https://code.byted.org/pdi-qa/flux-bug-finder.git
      - https://code.byted.org/org/sub/repo.git  -> 取末两段 sub/repo

    解析不出时返回空串，由调用方决定回退策略（原样传 remote 给接口）。
    """
    if not remote:
        return ""
    s = remote.strip()
    # 去掉 .git 后缀
    if s.endswith(".git"):
        s = s[:-4]
    # scp 形态 git@host:org/repo -> 取冒号后路径
    if "://" not in s and ":" in s and "@" in s:
        s = s.split(":", 1)[1]
    else:
        # 带协议：剥离 scheme://host，保留路径
        s = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", "", s)
        if "/" in s:
            # 去掉首段 host（含可能的 user@host）
            parts = s.split("/", 1)
            if "." in parts[0] or "@" in parts[0]:
                s = parts[1] if len(parts) > 1 else parts[0]
    s = s.strip("/")
    segments = [seg for seg in s.split("/") if seg]
    if len(segments) >= 2:
        return "/".join(segments[-2:])
    return ""


def resolve_repo(repo_arg: Optional[str], git_remote_arg: Optional[str]) -> str:
    """按优先级解析仓库标识，返回传给接口的 repo 值。

    优先级：--repo > --git-remote 解析 > 自动 git remote 解析。
    解析不出 org/repo 时，原样返回 remote 串（接口能容错完整 url）。
    """
    if repo_arg and repo_arg.strip():
        return repo_arg.strip()

    if git_remote_arg and git_remote_arg.strip():
        parsed = parse_repo_from_remote(git_remote_arg)
        return parsed if parsed else git_remote_arg.strip()

    remote = get_git_remote_url()
    if remote:
        parsed = parse_repo_from_remote(remote)
        return parsed if parsed else remote
    return ""


def fetch_workflows(endpoint: str, repo: str) -> tuple:
    """POST 拉取自定义 workflow 列表。

    返回 (workflows: list, error: str)。任何异常都吞掉转成 error 字符串，不抛出。
    """
    url = endpoint.rstrip("/") + WORKFLOW_PATH
    payload = json.dumps({"repo": repo}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return [], f"请求自定义工作流接口失败: {e}"
    except Exception as e:
        return [], f"请求自定义工作流接口异常: {e}"

    try:
        body = json.loads(raw)
    except Exception as e:
        return [], f"自定义工作流接口返回非法 JSON: {e}"

    code = body.get("code")
    if code != 0:
        return [], f"自定义工作流接口返回非成功 code={code}, message={body.get('message', '')}"

    data = body.get("data") or {}
    workflows = data.get("workflows") or []
    if not isinstance(workflows, list):
        return [], f"自定义工作流接口 workflows 字段非数组: {type(workflows).__name__}"

    # 仅保留结构合法的条目（需有 content 才能作为检测指令）
    cleaned = []
    for wf in workflows:
        if not isinstance(wf, dict):
            continue
        content = (wf.get("content") or "").strip()
        if not content:
            continue
        cleaned.append({
            "id": str(wf.get("id") or "").strip(),
            "name": (wf.get("name") or "").strip(),
            "content": content,
        })
    return cleaned, ""


def write_output(output_dir: str, result: dict) -> Optional[str]:
    """写 custom_workflows.json，返回写入路径；失败返回 None 并记 stderr。"""
    try:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / OUTPUT_FILENAME
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(out_path)
    except Exception as e:
        print(f"[custom-workflows] 写 {OUTPUT_FILENAME} 失败: {e}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="拉取仓库级自定义工作流")
    parser.add_argument("--output-dir", required=True, help="输出目录（WORK_DIR），写入 custom_workflows.json")
    parser.add_argument("--repo", default=None, help="仓库标识，形如 org/repo，最高优先级")
    parser.add_argument("--git-remote", default=None, help="git remote 值，脚本负责解析成 org/repo")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get(ENDPOINT_ENV, DEFAULT_ENDPOINT),
        help=f"自定义工作流接口 base url，默认 {DEFAULT_ENDPOINT}，可用环境变量 {ENDPOINT_ENV} 覆盖",
    )
    args = parser.parse_args()

    repo = resolve_repo(args.repo, args.git_remote)
    result = {
        "repo": repo,
        "endpoint": args.endpoint,
        "workflows": [],
        "error": "",
    }

    if not repo:
        result["error"] = "无法解析仓库标识（不在 git 仓库内且未传 --repo/--git-remote）"
        write_output(args.output_dir, result)
        print("[custom-workflows] 未能解析仓库标识，跳过自定义工作流检测", file=sys.stderr)
        return 0

    workflows, error = fetch_workflows(args.endpoint, repo)
    result["workflows"] = workflows
    result["error"] = error

    write_output(args.output_dir, result)

    if error:
        print(f"[custom-workflows] {error}；跳过自定义工作流检测", file=sys.stderr)
    elif workflows:
        names = ", ".join(wf["name"] or wf["id"] or "?" for wf in workflows)
        print(f"[custom-workflows] 拉取到 {len(workflows)} 条自定义工作流: {names}")
    else:
        print(f"[custom-workflows] 仓库 {repo} 未配置自定义工作流，跳过自定义工作流检测")

    return 0


if __name__ == "__main__":
    sys.exit(main())
