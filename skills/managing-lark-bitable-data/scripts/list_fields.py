import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def list_fields(app_token, table_id, view_id="", page_token="", page_size=20):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "view_id": view_id,
        "page_token": page_token,
        "page_size": page_size,
    }
    return client.call("ListAppTableField", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List fields in a Bitable table or view.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--view_id", default="", help="Optional view_id. If provided, list fields under this view; otherwise list fields for the whole table.")
    parser.add_argument("--page_token", default="", help="Page token for pagination.")
    parser.add_argument("--page_size", type=int, default=20, help="Number of items per page (default 20, max 100).")

    args = parser.parse_args()

    from .lark_bitable_client import run_script
    run_script(list_fields, args.app_token, args.table_id, args.view_id, args.page_token, args.page_size)
