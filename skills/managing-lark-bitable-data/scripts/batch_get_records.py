import argparse
import json
from .lark_bitable_client import LarkBitableClient, print_json


def batch_get_records(app_token, table_id, record_ids_json, automatic_fields=False):
    client = LarkBitableClient()
    try:
        record_ids = json.loads(record_ids_json)
        if not isinstance(record_ids, list):
            raise ValueError("record_ids must be a JSON array")
        record_ids = [rid for rid in record_ids if isinstance(rid, str) and rid]
        if not record_ids:
            raise ValueError("record_ids must contain at least one record_id")
    except (json.JSONDecodeError, ValueError) as e:
        client._handle_error("INVALID_ARGS", f"Error decoding record_ids JSON: {e}", "Ensure you provide a JSON array of record_id strings.")

    args = {
        "app_token": app_token,
        "table_id": table_id,
        "record_ids": record_ids,
        "automatic_fields": automatic_fields,
    }
    return client.call("SearchBitableRecordByRecordIDs", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch get records by record_id list.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--record_ids", required=True, help="JSON array string of record_ids, e.g. '[""rec1"", ""rec2""]'.")
    parser.add_argument("--automatic_fields", action="store_true", help="Return created_time/last_modified_time/created_by/last_modified_by fields.")

    args = parser.parse_args()

    original_record_ids = args.record_ids
    args.record_ids = args.record_ids.strip()
    if args.record_ids != original_record_ids:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --record_ids (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(batch_get_records, args.app_token, args.table_id, args.record_ids, args.automatic_fields)
