---
name: managing-lark-bitable-data
description: 管理飞书多维表格：支持对表/视图/表单/字段的结构操作，带条件过滤的记录增删改查，以及通过知识库 URL 解析应用 Token。//Manages Feishu/Lark Bitable apps: tables/views/forms/fields schema operations, record CRUD with filters, and wiki URL resolution to app tokens.
---

# Managing Lark Bitable Data

This skill interacts with Lark/Feishu Bitable via Python scripts in `scripts/`.

Scripts call Agent Server RPC. `IRIS_AGENT_BASE_URL` must be set.

All person identifiers use `open_id`.

Run `python3 -m scripts.<script_name> --help` for full parameters.

Note: Skill resources are under `inner_skills/managing-lark-bitable-data` (linked from `/workspace/sensitive/skill`). When running scripts from `inner_skills` in bash tools, set `use_inner_skill=true` (especially for custom Python scripts that import this skill’s `scripts`).

## Quick Start (common path)

1) Resolve a wiki/base URL → get `app_token`:

```bash
python3 -m scripts.parse_wiki_url --doc_url <WIKI_OR_DOC_URL>
```

2) Find `table_id` / `view_id` / field names:

```bash
python3 -m scripts.list_tables --app_token <APP_TOKEN>
python3 -m scripts.list_views --app_token <APP_TOKEN> --table_id <TABLE_ID>
python3 -m scripts.list_fields --app_token <APP_TOKEN> --table_id <TABLE_ID>
```

You can also return a user-facing view link for the user to click/open (do not fetch data via browser) by composing:

`https://bytedance.larkoffice.com/base/<APP_TOKEN>?table=<TABLE_ID>&view=<VIEW_ID>`

1) Read records (by table / by view):

```bash
python3 -m scripts.search_records --app_token <APP_TOKEN> --table_id <TABLE_ID> [--view_id <VIEW_ID>] [--automatic_fields] [--page_token ""] [--page_size 20]
```

4) Write records (single / batch):

```bash
python3 -m scripts.add_record --app_token <APP_TOKEN> --table_id <TABLE_ID> --record '{"record_id":"","fields":{...}}'
python3 -m scripts.update_record --app_token <APP_TOKEN> --table_id <TABLE_ID> --record '{"record_id":"recxxx","fields":{...}}'
python3 -m scripts.batch_add_records --app_token <APP_TOKEN> --table_id <TABLE_ID> --records '[{"record_id":"","fields":{...}}]'
```

## Workflow Pattern: explore then automate

When the context is unclear (which table/view/field to operate), use CLI first to inspect, then write Python to orchestrate.

Explore (CLI):

> **Safe for analysis**: CLI output is formatted for readability. Large outputs are automatically saved to a file with a summary shown, ensuring no information loss during semantic analysis.

```bash
python3 -m scripts.list_tables --app_token <APP_TOKEN>
python3 -m scripts.list_views --app_token <APP_TOKEN> --table_id <TABLE_ID>
python3 -m scripts.list_fields --app_token <APP_TOKEN> --table_id <TABLE_ID>
```

Automate (Python):

> **Mandatory**: Automation scripts **must import** functions directly (e.g., `from scripts.list_tables import list_tables`).
> **Do not** use `subprocess` to run CLI commands. CLI formatting (truncation/summaries) breaks JSON parsing, whereas imported functions return raw data objects.

```python
import sys
import json


SKILL_ROOT = "/workspace/sensitive/skill/managing-lark-bitable-data"
if SKILL_ROOT not in sys.path:
    sys.path.append(SKILL_ROOT)


def delete_records_by_filter(app_token, table_id, filter_obj, page_size=200):
    from scripts.lark_bitable_client import RetryableRateLimitError
    from scripts.search_records_by_filter import search_records_by_filter
    from scripts.batch_delete_records import batch_delete_records

    page_token = ""
    to_delete = []
    while True:
        try:
            resp = search_records_by_filter(
                app_token,
                table_id,
                json.dumps(filter_obj, ensure_ascii=False),
                sort_json=None,
                automatic_fields=False,
                page_token=page_token,
                page_size=page_size,
            )
        except Exception as e:
            print(f"Search failed: {e}")
            return

        data = resp.get("data", {})
        for item in data.get("items", []) or []:
            rid = item.get("record_id")
            if rid:
                to_delete.append(rid)
        
        # Only has_more=true means there is a next page
        if not data.get("has_more"):
            break
        page_token = data["page_token"]

    chunk = 100
    for i in range(0, len(to_delete), chunk):
        try:
            batch_delete_records(app_token, table_id, json.dumps(to_delete[i : i + chunk]))
        except Exception as e:
            print(f"Delete failed: {e}")


def example(app_token, table_id):
    filter_obj = {
        "conjunction": "and",
        "conditions": [
            {"field_name": "状态", "operator": "is", "value": ["已归档"]}
        ],
    }
    delete_records_by_filter(app_token, table_id, filter_obj)
```

## Record Fields: read vs write (must-know)

Record read APIs return field values in **read shape**. Create/update requires **write shape**. Do not reuse read values directly.

Common write shapes:

```json
{
  "Text": "hello",
  "Number": 123,
  "SingleSelect": "Option A",
  "MultiSelect": ["A", "B"],
  "DateTime": 1674206443000,
  "Checkbox": true
}
```

Full mapping for all field types (including Person, Link, Location): `references/record-fields.md`.

> **Note**: Always use the **Write Shape** for creating/updating records. Do not copy the full object from a read response (e.g., use `["rec_id"]` for links, not `{"link_record_ids": [...]}`).

## Pagination defaults & limits

Defaults:

- `page_size`: 20
- `page_token`: empty string for first page
- `has_more`: true indicates there are more pages; use returned `page_token` for next call

Max `page_size` by script:

- `scripts/list_tables.py`: 100
- `scripts/list_views.py`: 100
- `scripts/list_fields.py`: 100
- `scripts/list_form_fields.py`: 100
- `scripts/search_records.py`: 500
- `scripts/search_records_by_filter.py`: 500

Batch limits:

- `scripts/batch_get_records.py`: max 100 `record_id` per call
- `scripts/batch_add_records.py`: max 500 records per call
- `scripts/batch_update_records.py`: max 500 records per call
- `scripts/batch_delete_records.py`: max 500 `record_id` per call

## Common Scripts (minimum parameters)

### Create Bitable app

```bash
python3 -m scripts.create_bitable_app --app_name <APP_NAME>
```

### Resolve URL

```bash
python3 -m scripts.parse_wiki_url --doc_url <WIKI_OR_DOC_URL>
```

### List tables

```bash
python3 -m scripts.list_tables --app_token <APP_TOKEN> [--page_token ""] [--page_size 20]
```

### List views

```bash
python3 -m scripts.list_views --app_token <APP_TOKEN> --table_id <TABLE_ID> [--page_token ""] [--page_size 20]
```

### List fields

```bash
python3 -m scripts.list_fields --app_token <APP_TOKEN> --table_id <TABLE_ID> [--view_id <VIEW_ID>] [--page_token ""] [--page_size 20]
```

### Search records (table / view)

If `view_id` is empty, searches the whole table; if provided, searches records under that view.

```bash
python3 -m scripts.search_records --app_token <APP_TOKEN> --table_id <TABLE_ID> [--view_id <VIEW_ID>] [--automatic_fields] [--page_token ""] [--page_size 20]
```

### Search records by filter

```bash
python3 -m scripts.search_records_by_filter \
  --app_token <APP_TOKEN> \
  --table_id <TABLE_ID> \
  --filter '<FILTER_JSON>' \
  [--sort '<SORT_JSON>'] [--automatic_fields] [--page_token ""] [--page_size 20]
```

Filter schema: `references/filter-guide.md`
Sort example: `'[{"field_name": "Field1", "desc": true}]'`

Note: For Select / Multi Select filters, Record Search typically uses option names, while View filters (`filter_info`) use option ids.

### Batch get records

Max 100 `record_id` per call.

```bash
python3 -m scripts.batch_get_records --app_token <APP_TOKEN> --table_id <TABLE_ID> --record_ids '["rec1","rec2"]' [--automatic_fields]
```

### Add / update / delete record

```bash
python3 -m scripts.add_record --app_token <APP_TOKEN> --table_id <TABLE_ID> --record '{"record_id":"","fields":{...}}'
python3 -m scripts.update_record --app_token <APP_TOKEN> --table_id <TABLE_ID> --record '{"record_id":"recxxx","fields":{...}}'
python3 -m scripts.delete_record --app_token <APP_TOKEN> --table_id <TABLE_ID> --record_id recxxx
```

Batch write:

Max 500 items per call for batch create/update/delete.

```bash
python3 -m scripts.batch_add_records --app_token <APP_TOKEN> --table_id <TABLE_ID> --records '[{"record_id":"","fields":{...}}]'
python3 -m scripts.batch_update_records --app_token <APP_TOKEN> --table_id <TABLE_ID> --records '[{"record_id":"recxxx","fields":{...}}]'
python3 -m scripts.batch_delete_records --app_token <APP_TOKEN> --table_id <TABLE_ID> --record_ids '["rec1","rec2"]'
```

### Attachment upload / download

Upload files to Lark Drive, then use the `file_token` in record attachment fields:

```bash
# Upload a file and get file_token
python3 -m scripts.upload_file_attachment --app_token <APP_TOKEN> --file_path <FILE_PATH> [--file_type bitable_file]

# Download a file by file_token
python3 -m scripts.download_lark_attachment --file_token <FILE_TOKEN> --save_path <SAVE_PATH>
```

Note: `file_type` can be `bitable_file` (default) or `bitable_image`. The returned `file_token` is used in attachment fields. See `references/record-fields.md` for attachment write format.

## Advanced Guides

### Schema Definitions (Field Types)
> **Usage**: Read these to find the correct `type`, `ui_type`, and `property` for `create_table`, `create_field`, and `update_field`.
- **Basic** (Text, Number, Date...): `references/field-meta-basic.md`
- **Options** (Select, Rating, Currency...): `references/field-meta-option.md`
- **Relations** (Person, Link, Attachment...): `references/field-meta-relation.md`
- **Computed** (Formula, Lookup, System...): `references/field-meta-computed.md`
- **UI Controls** (Stage, Button): `references/field-meta-ui.md`
> Note: For script `--help`, use the index: `references/table-field-metadata.md`

- Table operations: `references/table-operations.md`
- Field operations: `references/field-operations.md`

### Data Manipulation (Records)
- **Record Value Shapes** (Read vs Write): `references/record-fields.md` (Review before writing data)

### Querying (Search & Views)
- **Filter Guide** (Record vs View): `references/filter-guide.md`
- View operations: `references/view-operations.md`
- Form operations: `references/form-operations.md`

## Key behaviors & references

- Record updates are **incremental**; set a field to `null` to clear it. Only fields present in the payload are modified.
- Record read APIs may return computed values (formula/lookup); inspect field metadata to view expressions.
- Writing record `fields` values must follow `references/record-fields.md`.
- Creating/updating table fields must follow `references/table-field-metadata.md`.

## Error handling (scripts)

When orchestrating multiple operations in Python, only `RetryableRateLimitError` is safe to retry. All other exceptions require reviewing the request or code before retrying. The helper functions raise exceptions rather than exiting the process when imported.

```python
import json
import time

def example(app_token, table_id):
    from scripts.lark_bitable_client import RetryableRateLimitError
    from scripts.search_records_by_filter import search_records_by_filter

    filter_obj = {"conjunction": "and", "conditions": [{"field_name": "状态", "operator": "is", "value": ["已归档"]}]}
    
    page_token = ""
    attempts = 3
    while True:
        for i in range(attempts):
            try:
                resp = search_records_by_filter(
                    app_token,
                    table_id,
                    json.dumps(filter_obj, ensure_ascii=False),
                    page_token=page_token,
                )
                break
            except RetryableRateLimitError:
                if i == attempts - 1:
                    raise
                time.sleep(2 ** i)
            except Exception as e:
                # e will contain the error details (e.g. JSON payload from LarkBitableError)
                print(f"Operation failed: {e}")
                return
        data = resp.get("data", {})
        for item in data.get("items", []) or []:
            yield item
        if not data.get("has_more"):
            break
        page_token = data["page_token"]
```
