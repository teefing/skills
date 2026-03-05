import argparse
import json
from .lark_bitable_client import LarkBitableClient, print_json


def patch_form(app_token, table_id, form_id, form_json):
    client = LarkBitableClient()
    try:
        form_data = json.loads(form_json)
        if not isinstance(form_data, dict):
            raise ValueError("Input must be a JSON object.")
    except (json.JSONDecodeError, ValueError) as e:
        client._handle_error(
            "INVALID_ARGS",
            f"Error decoding form JSON: {e}",
            "Ensure you provide a valid JSON object for --form.",
        )

    args = {
        "app_token": app_token,
        "table_id": table_id,
        "form_id": form_id,
        "form": form_data,
    }
    return client.call("PatchAppTableForm", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patch Bitable form metadata.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--form_id", required=True, help="The form_id of the form.")
    parser.add_argument("--form", required=True, help="JSON object string representing form metadata. See references/form-operations.md for schema.")
    parsed = parser.parse_args()

    original_form = parsed.form
    parsed.form = parsed.form.strip()
    if parsed.form != original_form:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --form (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(patch_form, parsed.app_token, parsed.table_id, parsed.form_id, parsed.form)
