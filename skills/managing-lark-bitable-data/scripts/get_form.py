import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def get_form(app_token, table_id, form_id):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
        "table_id": table_id,
        "form_id": form_id,
    }
    return client.call("GetAppTableForm", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Bitable form metadata.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--form_id", required=True, help="The form_id of the form.")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(get_form, parsed.app_token, parsed.table_id, parsed.form_id)
