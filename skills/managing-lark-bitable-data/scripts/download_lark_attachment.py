#!/usr/bin/env python3
"""Download a file attachment from Lark Drive."""

import argparse
import sys

from .lark_bitable_client import LarkBitableClient


def download_lark_attachment(file_token: str, save_path: str) -> dict:
    """
    Download a file from Lark Drive using its file_token.

    Args:
        file_token: The file token obtained from attachment field or upload
        save_path: Absolute path where the file should be saved

    Returns:
        Dictionary with success status and file path

    Note:
        File tokens can be obtained from attachment field read values.
        See references/record-fields.md for attachment field structure.
    """ 
    client = LarkBitableClient()
    args = {"file_token": file_token, "save_path": save_path}
    return client.call("DownloadLarkAttachment", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download file from Lark by file token")
    parser.add_argument("--file_token", required=True, help="File token from Lark")
    parser.add_argument("--save_path", required=True, help="Path to save file")

    args = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(download_lark_attachment, args.file_token, args.save_path)