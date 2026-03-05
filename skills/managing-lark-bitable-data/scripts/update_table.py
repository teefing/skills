import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def update_table(app_token, table_id, table_name):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "table_name": table_name,
    }
    return client.call("UpdateBitableAppTable", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update a table in a Bitable app.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="Table ID.")
    parser.add_argument("--table_name", required=True, help="New table name.")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(update_table, parsed.app_token, parsed.table_id, parsed.table_name)
