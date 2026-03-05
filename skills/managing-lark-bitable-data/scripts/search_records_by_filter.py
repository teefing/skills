import argparse
import json
from .lark_bitable_client import LarkBitableClient, print_json


def search_records_by_filter(app_token, table_id, filter_json, sort_json=None, automatic_fields=False, page_token="", page_size=20):
    client = LarkBitableClient()
    try:
        filter_data = json.loads(filter_json)
    except (json.JSONDecodeError, TypeError) as e:
        client._handle_error("INVALID_ARGS", f"Error decoding filter JSON: {e}", "Ensure you provide a valid JSON object for filter.")

    args = {
        "app_token": app_token,
        "table_id": table_id,
        "filter": filter_data,
        "automatic_fields": automatic_fields,
        "page_token": page_token,
        "page_size": page_size,
    }

    if sort_json:
        try:
            sort_data = json.loads(sort_json)
        except (json.JSONDecodeError, TypeError) as e:
            client._handle_error("INVALID_ARGS", f"Error decoding sort JSON: {e}", "Ensure you provide a valid JSON array for sort.")
        args["sort"] = sort_data

    return client.call("SearchBitableRecordByFilter", args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search records in a Bitable table using filter and optional sort.")
    parser.add_argument("--app_token", required=True, help="The app_token of the Bitable app.")
    parser.add_argument("--table_id", required=True, help="The table_id of the table.")
    parser.add_argument("--filter", required=True, help="JSON object string representing the filter conditions. See references/filter-guide.md for schema.")
    parser.add_argument("--sort", help='Optional JSON array string representing sort conditions. Example: \'[{"field_name": "Field1", "desc": true}]\'')
    parser.add_argument("--automatic_fields", action="store_true", help="Return created_time/last_modified_time/created_by/last_modified_by fields.")
    parser.add_argument("--page_token", default="", help="Page token for pagination.")
    parser.add_argument("--page_size", type=int, default=20, help="Number of items per page (default 20, max 500).")

    args = parser.parse_args()

    original_filter = args.filter
    args.filter = args.filter.strip()
    if args.filter != original_filter:
        import sys
        print("NOTICE: trimmed surrounding whitespace for JSON arg --filter (model-generated cmd had extra spaces)", file=sys.stderr)

    if args.sort is not None:
        original_sort = args.sort
        args.sort = args.sort.strip()
        if args.sort != original_sort:
            import sys
            print("NOTICE: trimmed surrounding whitespace for JSON arg --sort (model-generated cmd had extra spaces)", file=sys.stderr)

    from .lark_bitable_client import run_script
    run_script(search_records_by_filter, args.app_token, args.table_id, args.filter, args.sort, args.automatic_fields, args.page_token, args.page_size)
