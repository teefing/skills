import argparse
import json
from .lark_bitable_client import LarkBitableClient, print_json


def patch_view(app_token, table_id, view_id, body_json):
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
        "view_id": view_id,
        "body": body_data,
    }
    return client.call("PatchAppTableView", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patch a view in a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--view_id", required=True, help="The view_id of the view.")
    parser.add_argument("--body", required=True, help="JSON object string representing the patch body. See references/view-operations.md for schema.")
    parsed = parser.parse_args()

    original_body = parsed.body
    parsed.body = parsed.body.strip()
    if parsed.body != original_body:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --body (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(patch_view, parsed.app_token, parsed.table_id, parsed.view_id, parsed.body)
