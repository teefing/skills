import argparse
from .lark_bitable_client import LarkBitableClient, print_json


def parse_wiki_url(doc_url):
    client = LarkBitableClient()
    args = {
        "doc_url": doc_url,
    }
    return client.call("ParseLarkWikiURL", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse a Lark wiki URL and extract the underlying token/app_token.")
    parser.add_argument("--doc_url", required=True, help="A Lark wiki URL (or a direct /base/, /docx/, /docs/, /sheet/ URL).")

    args = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(parse_wiki_url, args.doc_url)

