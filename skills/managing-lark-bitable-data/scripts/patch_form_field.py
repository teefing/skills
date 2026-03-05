import argparse
import json
from .lark_bitable_client import LarkBitableClient, print_json


def patch_form_field(app_token, table_id, form_id, field_id, body_json):
    client = LarkBitableClient()
    try:
        body_data = json.loads(body_json)
        if not isinstance(body_data, dict):
            raise ValueError("Input must be a JSON object.")
    except (json.JSONDecodeError, ValueError) as e:
        client._handle_error(
            "INVALID_ARGS",
            f"Error decoding body JSON: {e}",
            "Ensure you provide a valid JSON object for --body.",
        )

    args = {
        "app_token": app_token,
        "table_id": table_id,
        "form_id": form_id,
        "field_id": field_id,
        "body": body_data,
    }
    return client.call("PatchAppTableFormField", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patch a question in a Bitable form.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--form_id", required=True, help="The form_id of the form.")
    parser.add_argument("--field_id", required=True, help="The field_id of the form question.")
    parser.add_argument("--body", required=True, help="JSON object string representing the patch body. See references/form-operations.md for schema.")
    parsed = parser.parse_args()

    original_body = parsed.body
    parsed.body = parsed.body.strip()
    if parsed.body != original_body:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --body (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(patch_form_field, parsed.app_token, parsed.table_id, parsed.form_id, parsed.field_id, parsed.body)
