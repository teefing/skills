import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def get_app_info(app_token):
    client = LarkBitableClient()
    args = {
        "app_token": app_token,
    }
    return client.call("GetBitableInfo", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Bitable app metadata.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(get_app_info, parsed.app_token)
