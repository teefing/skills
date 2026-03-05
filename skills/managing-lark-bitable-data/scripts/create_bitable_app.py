import argparse
from .lark_bitable_client import LarkBitableClient


def create_bitable_app(app_name):
    client = LarkBitableClient()
    args = {
        "app_name": app_name,
    }
    return client.call("CreateBitableApp", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Bitable app (base).")
    parser.add_argument("--app_name", required=True, help="The name of the Bitable app to create.")
    parsed = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(create_bitable_app, parsed.app_name)
