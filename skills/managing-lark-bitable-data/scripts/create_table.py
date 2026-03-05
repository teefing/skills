import argparse
import json
from .lark_bitable_client import LarkBitableClient, print_json


def create_table(app_token, table_name, fields_json):
    client = LarkBitableClient()
    try:
        fields = json.loads(fields_json)
        if not isinstance(fields, list):
            raise ValueError("Input must be a JSON array.")
    except (json.JSONDecodeError, ValueError) as e:
        client._handle_error(
            "INVALID_ARGS",
            f"Error decoding fields JSON: {e}",
            "Ensure you provide a valid JSON array for --fields.",
        )

    args = {
        "app_token": app_token,
        "table_name": table_name,
        "fields": fields,
    }
    return client.call("CreateBitableAppTable", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a table in a Bitable app.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_name", required=True, help="New table name.")
    parser.add_argument("--fields", required=True, help="JSON array string for table fields (AppTableCreateHeader list). See references/table-field-metadata.md for schema.")
    parsed = parser.parse_args()

    original_fields = parsed.fields
    parsed.fields = parsed.fields.strip()
    if parsed.fields != original_fields:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --fields (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(create_table, parsed.app_token, parsed.table_name, parsed.fields)
