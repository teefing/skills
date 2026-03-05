import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def list_form_fields(app_token, table_id, form_id, page_token="", page_size=20):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "form_id": form_id,
        "page_token": page_token,
        "page_size": page_size,
    }
    return client.call("ListAppTableFormField", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List questions in a Bitable form.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--form_id", required=True, help="The form_id of the form.")
    parser.add_argument("--page_token", default="", help="Page token for pagination.")
    parser.add_argument("--page_size", type=int, default=20, help="Number of items per page (default 20, max 100).")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(list_form_fields, parsed.app_token, parsed.table_id, parsed.form_id, parsed.page_token, parsed.page_size)
