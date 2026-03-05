import argparse
import json
from .lark_bitable_client import LarkBitableClient


def create_view(app_token, table_id, view_name, view_type):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "view_name": view_name,
        "view_type": view_type,
    }
    return client.call("CreateAppTableView", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a view in a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--view_name", required=True, help="The name of the view to create.")
    parser.add_argument("--view_type", required=True, help="The type of the view (e.g., 'grid', 'gallery').")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(create_view, parsed.app_token, parsed.table_id, parsed.view_name, parsed.view_type)
