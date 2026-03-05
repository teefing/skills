import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def get_view(app_token, table_id, view_id):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "view_id": view_id,
    }
    return client.call("GetAppTableView", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get view details in a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--view_id", required=True, help="The view_id of the view.")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(get_view, parsed.app_token, parsed.table_id, parsed.view_id)
