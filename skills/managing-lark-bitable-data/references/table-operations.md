# Bitable app & table operations

This guide documents the **complete set** of app/table operations supported by this Skill.

All scripts below live in `scripts/`.

## App

### Get app info

Returns app metadata.

```bash
python3 -m scripts.get_app_info --app_token <APP_TOKEN>
```

## Tables

### List tables

```bash
python3 -m scripts.list_tables --app_token <APP_TOKEN> [--page_token <TOKEN>] [--page_size <SIZE>]
```

### Create table

`--fields` is a JSON array of objects. Each object represents a new field:

```json
[
  { 
    "field_name": "Name", 
    "type": 1, 
    "ui_type": "Text" 
  },
  { 
    "field_name": "Age", 
    "type": 2, 
    "ui_type": "Number",
    "property": {
      "formatter": "0" 
    }
  }
]
```

```bash
python3 -m scripts.create_table \
  --app_token <APP_TOKEN> \
  --table_name "问卷Demo" \
  --fields '[{"field_name":"姓名","type":1,"ui_type":"Text"}]'
```

Notes:

- `type` / `ui_type` / `property` must follow `references/table-field-metadata.md`.
- The first field in the `fields` array becomes the **Primary Field** (Index). Note that this index is **not unique** (duplicates are allowed).

### Update table

Currently supports renaming.

```bash
python3 -m scripts.update_table --app_token <APP_TOKEN> --table_id <TABLE_ID> --table_name "NewName"
```

### Delete table

```bash
python3 -m scripts.delete_table --app_token <APP_TOKEN> --table_id <TABLE_ID>
```

