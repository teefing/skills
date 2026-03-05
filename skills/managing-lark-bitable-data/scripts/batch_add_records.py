import argparse
import sys
import json
from .lark_bitable_client import LarkBitableClient, print_json

def batch_add_records(app_token, table_id, records_json):
    client = LarkBitableClient()
    try:
        records_list = json.loads(records_json)
        if not isinstance(records_list, list):
            raise ValueError("Input must be a JSON array of record objects.")
    except (json.JSONDecodeError, ValueError) as e:
        client._handle_error("INVALID_ARGS", f"Error decoding records JSON: {e}", "Ensure you provide a valid JSON array string.")
    
    # We pass the list directly; the server handler now expects list of objects with "fields" and "record_id" keys.
    # The previous script expected list of fields maps. The new schema wrapper is handled by the caller/Agent.
    # The input JSON must ALREADY represent the list of BitableRecord structs. 
    # Example: [{"fields": {...}, "record_id": ""}]

    args = {
        "app_token": app_token,
        "table_id": table_id,
        "records": records_list
    }
    return client.call("BatchCreateBitableRecord", args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch add records to a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--records", required=True, help="JSON array string of records. See references/record-fields.md for schema. objects. REQUIRED format: '[{\"fields\": {\"Field\": \"Val\"}, \"record_id\": \"\"}, ...]'. 'record_id' matches schema but is ignored for creation.")

    args = parser.parse_args()

    original_records = args.records
    args.records = args.records.strip()
    if args.records != original_records:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --records (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(batch_add_records, args.app_token, args.table_id, args.records)
    # Output structure:
    # {
    #   "records": [
    #      { "record_id": "recxxxx", "fields": { ... } },
    #      ...
    #   ]
