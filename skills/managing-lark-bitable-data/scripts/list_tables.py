import argparse
import sys
import json
from .lark_bitable_client import LarkBitableClient, print_json

def list_tables(app_token, page_token="", page_size=20):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "page_token": page_token,
        "page_size": page_size
    }
    return client.call("ListBitableAppTable", args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List all tables in a Bitable app.")
    parser.add_argument("--app_token", required=True, help=" The app_token of the Bitable app (found in the URL).")
    parser.add_argument("--page_token", default="", help="Page token for pagination.")
    parser.add_argument("--page_size", type=int, default=20, help="Number of items per page (default 20, max 100).")

    args = parser.parse_args()

    from .lark_bitable_client import run_script
    run_script(list_tables, args.app_token, args.page_token, args.page_size)
    
    # Structure of output:
    # {
    #   "data": {
    #     "items": [
    #       { "table_id": "tblxxxx", "name": "TableName", "revision": 1, ... }
    #     ],
    #     "page_token": "xxx",
    #     "has_more": true,
    #     "total": 10
    #   }
    # }
