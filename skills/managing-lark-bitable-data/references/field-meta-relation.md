# Field Metadata: Relations & Objects

This reference covers fields that link to other entities or store complex objects.

## People & Groups

### Person (`type=11`, `ui_type=User`)

```json
{
  "field_name": "Owner",
  "type": 11,
  "ui_type": "User",
  "property": { "multiple": true }
}
```

### Group Chat (`type=23`, `ui_type=GroupChat`)

```json
{
  "field_name": "Related Chat",
  "type": 23,
  "ui_type": "GroupChat",
  "property": { "multiple": false }
}
```

## Table Links

### Single Link (`type=18`, `ui_type=SingleLink`)
### Duplex Link (`type=21`, `ui_type=DuplexLink`)

- Must specify `table_id` of the target table.

```json
{
  "field_name": "Related Orders",
  "type": 18,
  "ui_type": "SingleLink",
  "property": {
    "table_id": "xxxx",
    "multiple": true
  }
}
```

## Objects

### Attachment (`type=17`, `ui_type=Attachment`)

```json
{
  "field_name": "Files",
  "type": 17,
  "ui_type": "Attachment",
  "property": null
}
```

### Location (`type=22`, `ui_type=Location`)

```json
{
  "field_name": "Site",
  "type": 22,
  "ui_type": "Location",
  "property": {
    "location": { "input_type": "not_limit" } // enum: only_mobile/not_limit
  }
}
```
