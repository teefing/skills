import argparse
import sys
import json
from .lark_bitable_client import LarkBitableClient, print_json

def update_record(app_token, table_id, record_json):
    client = LarkBitableClient()
    try:
        record_data = json.loads(record_json)
        if not isinstance(record_data, dict):
            raise ValueError("Input must be a JSON object.")
        if "record_id" not in record_data or not record_data["record_id"]:
             # For update, record_id is mandatory
             raise ValueError("Input object must contain non-empty 'record_id' key.")
        if "fields" not in record_data:
             raise ValueError("Input object must contain 'fields' key.")

    except (json.JSONDecodeError, ValueError) as e:
        client._handle_error("INVALID_ARGS", f"Error decoding record JSON: {e}", "Ensure you provide a valid JSON object with 'record_id' and 'fields'.")

    args = {
        "app_token": app_token,
        "table_id": table_id,
        "record": record_data
    }
    return client.call("UpdateBitableRecord", args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update a record in a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--record", required=True, help="JSON object string representing the record. See references/record-fields.md for schema. Schema: '{\"record_id\": \"rec...\", \"fields\": {\"Field\": \"Val\"}}'.")

    args = parser.parse_args()

    original_record = args.record
    args.record = args.record.strip()
    if args.record != original_record:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --record (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(update_record, args.app_token, args.table_id, args.record)
    # Output structure:
    # {
    #   "record": {
    #      "record_id": "recxxxx",
    #      "fields": { ... }    
    #   }
    # }
