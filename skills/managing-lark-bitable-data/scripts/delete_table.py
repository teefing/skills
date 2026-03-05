import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def delete_table(app_token, table_id):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
    }
    return client.call("DeleteBitableAppTable", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete a table in a Bitable app.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="Table ID.")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(delete_table, parsed.app_token, parsed.table_id)
