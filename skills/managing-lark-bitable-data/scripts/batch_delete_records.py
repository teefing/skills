import argparse
import sys
import json
from .lark_bitable_client import LarkBitableClient, print_json

def batch_delete_records(app_token, table_id, record_ids_json):
    client = LarkBitableClient()
    try:
        record_ids_list = json.loads(record_ids_json)
        if not isinstance(record_ids_list, list):
            raise ValueError("Input must be a JSON array of strings (record_ids).")
    except (json.JSONDecodeError, ValueError) as e:
        client._handle_error("INVALID_ARGS", f"Error decoding record_ids JSON: {e}", "Ensure you provide a valid JSON array string.")

    args = {
        "app_token": app_token,
        "table_id": table_id,
        "record_ids": record_ids_list
    }
    return client.call("BatchDeleteBitableRecord", args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch delete records from a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--record_ids", required=True, help="JSON array string representing the list of record_ids to delete. Example: '[\"rec1\", \"rec2\"]'")

    args = parser.parse_args()

    original_record_ids = args.record_ids
    args.record_ids = args.record_ids.strip()
    if args.record_ids != original_record_ids:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --record_ids (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(batch_delete_records, args.app_token, args.table_id, args.record_ids)
