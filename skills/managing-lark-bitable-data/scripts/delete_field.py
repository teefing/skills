import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def delete_field(app_token, table_id, field_id):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "field_id": field_id,
    }
    return client.call("DeleteAppTableField", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete a field in a Bitable table.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--field_id", required=True, help="The field_id of the field.")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(delete_field, parsed.app_token, parsed.table_id, parsed.field_id)
