import argparse
import sys
import json
from .lark_bitable_client import LarkBitableClient

def search_records(app_token, table_id, view_id="", automatic_fields=False, page_token="", page_size=20):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "automatic_fields": automatic_fields,
        "page_token": page_token,
        "page_size": page_size
    }
    
    method = "SearchBitableRecord"
    if view_id:
        args["view_id"] = view_id
        method = "SearchBitableRecordByViewID"

    return client.call(method, args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search records in a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--view_id", default="", help="Optional view_id to filter records.")
    parser.add_argument("--automatic_fields", action="store_true", help="Return created_time/last_modified_time/created_by/last_modified_by fields.")
    parser.add_argument("--page_token", default="", help="Page token for pagination.")
    parser.add_argument("--page_size", type=int, default=20, help="Number of items per page (default 20, max 500).")

    args = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(search_records, args.app_token, args.table_id, args.view_id, args.automatic_fields, args.page_token, args.page_size)
    # Structure of output:
    # {
    #   "data": {
    #     "items": [
    #       { "record_id": "recxxxx", "fields": { "Field Name": "Value", ... }, ... }
    #     ],
    #     "page_token": "xxx",
    #     "has_more": true,
    #     "total": 100
    #   }
    # }