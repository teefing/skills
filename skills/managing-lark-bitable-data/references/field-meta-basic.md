# Field Metadata: Basic Types

This reference covers basic scalar field types.

## Text (`type=1`, `ui_type=Text`)

- Use for plain text or rich text content.
- `property` must be `null`.

```json
{
  "field_name": "Notes",
  "type": 1,
  "ui_type": "Text",
  "property": null
}
```

## Number (`type=2`, `ui_type=Number`)

- `property.formatter` controls formatting.

```json
{
  "field_name": "Amount",
  "type": 2,
  "ui_type": "Number",
  "property": {
    "formatter": "1,000.00" // Options: "0", "0.0", "0.00", "0%", "0.00%"
  }
}
```

## DateTime (`type=5`, `ui_type=DateTime`)

- `date_formatter` controls display.

```json
{
  "field_name": "Due Date",
  "type": 5,
  "ui_type": "DateTime",
  "property": {
    "date_formatter": "yyyy-MM-dd HH:mm",
    "auto_fill": false
  }
}
```

## Checkbox (`type=7`, `ui_type=Checkbox`)

- Boolean field; `property` must be `null`.

```json
{
  "field_name": "Archived",
  "type": 7,
  "ui_type": "Checkbox",
  "property": null
}
```

## Contact Info

### Email (`type=1`, `ui_type=Email`)
```json
{ "field_name": "Email", "type": 1, "ui_type": "Email", "property": null }
```

### Phone (`type=13`, `ui_type=Phone`)
```json
{ "field_name": "Phone", "type": 13, "ui_type": "Phone", "property": null }
```

### URL (`type=15`, `ui_type=Url`)
```json
{ "field_name": "Website", "type": 15, "ui_type": "Url", "property": null }
```

### Barcode (`type=1`, `ui_type=Barcode`)
```json
{
  "field_name": "Code",
  "type": 1,
  "ui_type": "Barcode",
  "property": { "allowed_edit_modes": { "scan": true, "manual": true } }
}
```
