import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def list_views(app_token, table_id, page_token="", page_size=20):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "page_token": page_token,
        "page_size": page_size,
    }
    return client.call("ListAppTableView", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List views in a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--page_token", default="", help="Page token for pagination.")
    parser.add_argument("--page_size", type=int, default=20, help="Number of items per page (default 20, max 100).")

    args = parser.parse_args()

    from .lark_bitable_client import run_script
    run_script(list_views, args.app_token, args.table_id, args.page_token, args.page_size)

