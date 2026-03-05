# Bitable view operations

This guide documents the **complete set** of view operations supported by this Skill.

All scripts below live in `scripts/`.

## Views

### List views

```bash
python3 -m scripts.list_views --app_token <APP_TOKEN> --table_id <TABLE_ID> [--page_token <TOKEN>] [--page_size <SIZE>]
```

### Get view (查询视图)

Fetches view details by `view_id`.

```bash
python3 -m scripts.get_view --app_token <APP_TOKEN> --table_id <TABLE_ID> --view_id <VIEW_ID>
```

### Create view

```bash
python3 -m scripts.create_view \
  --app_token <APP_TOKEN> \
  --table_id <TABLE_ID> \
  --view_name <VIEW_NAME> \
  --view_type <VIEW_TYPE>
```

Common `view_type` values include `grid`, `kanban`, `gantt`, `gallery`, `form`.

### Patch view

`--body` is a JSON object. Available fields:

```json
{
  "view_name": "New Name",
  "property": {
    "filter_info": {
      "conjunction": "and",
      "conditions": [
        {
          "field_id": "fldpTw2262",
          "operator": "isGreater",
          "value": ["ExactDate", "1642672432000"]
        }
      ]
    },
    "hidden_fields": ["fldmeqmpVA", "fldOtherId"]
  }
}
```

See `references/filter-guide.md` for `filter_info` schema details (Note: View filters use `field_id` and do not support nesting).

For Select / Multi Select fields in `filter_info.conditions[].value`, View filters use the option id (from `scripts.list_fields` → field `property.options`).

```bash
python3 -m scripts.patch_view \
  --app_token <APP_TOKEN> \
  --table_id <TABLE_ID> \
  --view_id <VIEW_ID> \
  --body '{"view_name":"Renamed"}'
```

### Delete view

```bash
python3 -m scripts.delete_view --app_token <APP_TOKEN> --table_id <TABLE_ID> --view_id <VIEW_ID>
```
