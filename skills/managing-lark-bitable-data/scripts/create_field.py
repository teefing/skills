import argparse
import json
from .lark_bitable_client import LarkBitableClient, print_json


def create_field(app_token, table_id, field_json):
    client = LarkBitableClient()
    try:
        field_data = json.loads(field_json)
        if not isinstance(field_data, dict):
            raise ValueError("Input must be a JSON object.")
    except (json.JSONDecodeError, ValueError) as e:
        client._handle_error(
            "INVALID_ARGS",
            f"Error decoding field JSON: {e}",
            "Ensure you provide a valid JSON object for --field.",
        )

    args = {
        "app_token": app_token,
        "table_id": table_id,
        "field": field_data,
    }
    return client.call("CreateAppTableField", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a field in a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--field", required=True, help="JSON object string representing the field. See references/table-field-metadata.md for schema.")
    parsed = parser.parse_args()

    original_field = parsed.field
    parsed.field = parsed.field.strip()
    if parsed.field != original_field:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --field (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(create_field, parsed.app_token, parsed.table_id, parsed.field)
