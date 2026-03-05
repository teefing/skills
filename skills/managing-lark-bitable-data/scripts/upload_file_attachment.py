#!/usr/bin/env python3
"""Upload a file attachment to Lark Drive for use in Bitable records."""

import argparse

from .lark_bitable_client import LarkBitableClient


def upload_file_attachment(app_token: str, file_path: str, file_type: str = "bitable_file") -> dict:
    """
    Upload a file to Lark Drive and get a file_token for use in Bitable attachment fields.

    Args:
        app_token: Bitable app token
        file_path: Absolute path to the file to upload
        file_type: Type of file upload ('bitable_image' or 'bitable_file', default: 'bitable_file')

    Returns:
        Dictionary containing the file_token

    Note:
        The file_token can be used in attachment fields when creating/updating records.
        See references/record-fields.md for attachment field write format.
    """
    client = LarkBitableClient()
    args = {"app_token": app_token, "file_path": file_path, "file_type": file_type}

    return client.call("UploadFileAttachment", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload file attachment to Lark for Bitable use"
    )
    parser.add_argument("--app_token", required=True, help="Bitable app token")
    parser.add_argument("--file_path", required=True, help="Path to file")
    parser.add_argument(
        "--file_type",
        default="bitable_file",
        choices=["bitable_file", "bitable_image"],
        help="File type (bitable_file or bitable_image)",
    )

    args = parser.parse_args()
    from .lark_bitable_client import run_script
    run_script(upload_file_attachment, args.app_token, args.file_path, args.file_type)
