# Field Metadata: Options & specialized Numbers

This reference covers fields with options or specific numeric formatting.

## Select Options

### Single Select (`type=3`, `ui_type=SingleSelect`)
### Multi Select (`type=4`, `ui_type=MultiSelect`)

```json
{
  "field_name": "Status",
  "type": 3,
  "ui_type": "SingleSelect",
  "property": {
    "options": [
      { "name": "Todo", "color": 0 }, // create option
      { "id": "xxx", "name": "Done", "color": 1 } // update option
      // other option will be remoted
    ]
  }
}
```

## Specialized Numbers

### Currency (`type=2`, `ui_type=Currency`)

```json
{
  "field_name": "Price",
  "type": 2,
  "ui_type": "Currency",
  "property": {
    "formatter": "0.00",
    "currency_code": "CNY" // e.g., CNY, USD, EUR, JPY
  }
}
```

### Progress (`type=2`, `ui_type=Progress`)

```json
{
  "field_name": "Completion",
  "type": 2,
  "ui_type": "Progress",
  "property": {
    "formatter": "0%",
    "range_customize": true,
    "min": 0,
    "max": 100
  }
}
```

### Rating (`type=2`, `ui_type=Rating`)

```json
{
  "field_name": "Stars",
  "type": 2,
  "ui_type": "Rating",
  "property": {
    "formatter": "0",
    "min": 0,
    "max": 5,
    "rating": { "symbol": "star" } // enum: star|heart|thumbsup|fire|smile|lightning|flower|number
  }
}
```
