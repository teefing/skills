# Field Metadata: Computed & System

This reference covers read-only or system-managed fields.

## Computed

### Formula (`type=20`, `ui_type=Formula`)

- `formula_expression` contains the logic.

```json
{
  "field_name": "Total",
  "type": 20,
  "ui_type": "Formula",
  "property": {
    "formula_expression": "[Price] * [Quantity]"
  }
}
```

### Lookup (`type=19`, `ui_type=Lookup`)

- Generally created via UI or as side-effect of links. Avoid creating manually if possible as it relies on complex relation IDs.

## System Auto-fill

### Auto Number (`type=1005`, `ui_type=AutoNumber`)

```json
{
  "field_name": "ID",
  "type": 1005,
  "ui_type": "AutoNumber",
  "property": {
    "auto_serial": { "type": "auto_increment_number" }
  }
}
```

### Created Time (`type=1001`, `ui_type=CreatedTime`)
### Modified Time (`type=1002`, `ui_type=ModifiedTime`)

```json
{
  "field_name": "Created At",
  "type": 1001,
  "ui_type": "CreatedTime",
  "property": { "date_formatter": "yyyy-MM-dd" }
}
```

### Created User (`type=1003`, `ui_type=CreatedUser`)
### Modified User (`type=1004`, `ui_type=ModifiedUser`)

```json
{
  "field_name": "Created By",
  "type": 1003,
  "ui_type": "CreatedUser",
  "property": null
}
```
