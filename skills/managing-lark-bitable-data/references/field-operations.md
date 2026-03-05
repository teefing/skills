# Bitable field operations

This guide documents the **complete set** of field operations supported by this Skill.

For `type` / `ui_type` / `property` details, see the **Schema Definitions** in `SKILL.md` or the index at `references/table-field-metadata.md`.

All scripts below live in `scripts/`.

## Fields

### List fields

List all fields in a table, or fields visible in a view.

```bash
python3 -m scripts.list_fields --app_token <APP_TOKEN> --table_id <TABLE_ID> [--view_id <VIEW_ID>] [--page_token <TOKEN>] [--page_size <SIZE>]
```

### Create field

`--field` is a JSON object. Example:

```json
{
  "field_name": "Category",
  "type": 3,
  "ui_type": "SingleSelect",
  "property": {
    "options": [
      { "name": "Work" },
      { "name": "Personal" }
    ]
  }
}
```
*See `references/field-meta-option.md` for Option configuration details.*

```bash
python3 -m scripts.create_field \
  --app_token <APP_TOKEN> \
  --table_id <TABLE_ID> \
  --field '{"field_name":"评分","type":2,"ui_type":"Rating","property":{"formatter":"0","min":1,"max":5,"rating":{"symbol":"star"}}}'
```

Notes:

- `type` / `ui_type` / `proper  ty` must follow `references/table-field-metadata.md`.

### Update field

`--field` is a JSON object. Example:

```json
{
  "field_name": "Rating (Updated)",
  "type": 2,
  "ui_type": "Rating",
  "property": {
    "formatter": "0",
    "min": 0,
    "max": 10
  }
}
```

```bash
python3 -m scripts.update_field \
  --app_token <APP_TOKEN> \
  --table_id <TABLE_ID> \
  --field_id <FIELD_ID> \
  --field '{"field_name":"Rating (Updated)","type":2,"ui_type":"Rating","property":{"formatter": "0","min":0,"max":10}}'
```

Notes:

- `type` / `ui_type` / `property` must follow `references/table-field-metadata.md`.

### Delete field

```bash
python3 -m scripts.delete_field --app_token <APP_TOKEN> --table_id <TABLE_ID> --field_id <FIELD_ID>
```
