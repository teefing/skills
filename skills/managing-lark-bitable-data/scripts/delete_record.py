import argparse
import sys
import json
from .lark_bitable_client import LarkBitableClient, print_json

def delete_record(app_token, table_id, record_id):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "record_id": record_id
    }
    return client.call("DeleteBitableRecord", args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete a record from a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--record_id", required=True, help="The record_id of the record to delete.")

    args = parser.parse_args()

    from .lark_bitable_client import run_script
    run_script(delete_record, args.app_token, args.table_id, args.record_id)
    # Output structure:
    # {
    #   "success": true
    # }
