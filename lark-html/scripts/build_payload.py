#!/usr/bin/env python3
"""
Build JSON payload for lark-cli api calls to create/manage HTML Box blocks.

Usage:
  python3 build_payload.py create <html_file> [--index N]
  python3 build_payload.py update <html_file> --index <N>

Output: JSON payload to stdout, pipe to file then use with `lark-cli api --data @file`
"""

import json
import sys
import argparse


COMPONENT_TYPE_ID = "blk_6900429af84180025ce76527"
BLOCK_TYPE = 40


def build_create_payload(html_content: str, index: int = -1) -> dict:
    record = json.dumps({"html": html_content})
    payload = {
        "children": [
            {
                "block_type": BLOCK_TYPE,
                "add_ons": {
                    "component_type_id": COMPONENT_TYPE_ID,
                    "record": record,
                },
            }
        ],
    }
    if index >= 0:
        payload["index"] = index
    return payload


def main():
    parser = argparse.ArgumentParser(description="Build HTML Box API payload")
    parser.add_argument("action", choices=["create", "update"], help="Action type")
    parser.add_argument("html_file", help="Path to HTML file")
    parser.add_argument("--index", type=int, default=-1, help="Insert position (0=start, -1=end)")

    args = parser.parse_args()

    with open(args.html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    if not html_content.strip():
        print("Error: HTML file is empty", file=sys.stderr)
        sys.exit(1)

    payload = build_create_payload(html_content, args.index)
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
