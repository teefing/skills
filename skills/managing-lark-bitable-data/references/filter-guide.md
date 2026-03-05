# Filter Guide

This guide details how to construct filter conditions for **Record Search** APIs and **View Property** configuration.

> **CRITICAL DISTINCTION**:
> - **Record Search** (`search_records_by_filter`): Uses `field_name` and supports **nested** logic (`children`).
> - **View Property** (`create_view`, `patch_view`): Uses `field_id` and **ONLY** supports flat logic (no `children`).
> - **Select / Multi Select values differ**: Record Search typically uses the **option name** (e.g. `"Done"`), while View Property filters use the **option id** (from `list_fields`).

## Contents
- [1. Record Search Filter](#1-record-search-filter) (Nested, uses `field_name`)
- [2. View Property Filter](#2-view-property-filter) (Flat, uses `field_id`)
- [3. Supported Operators](#3-supported-operators) (Common for both)
- [4. Value Formats](#4-value-formats) (Record vs View)

## 1. Record Search Filter

Used in `scripts/search_records_by_filter.py`.

### Structure

| Parameter | Type | Required | Description |
|---|---|---|---|
| `conjunction` | string | Yes | `"and"` or `"or"`. |
| `conditions` | list | No | Flat list of conditions. |
| `children` | list | No | Nested filter groups (max depth 1). |

### Condition Item
| Field | Value |
|---|---|
| `field_name` | String (e.g., "Amount") |
| `operator` | `is`, `isGreater`, `contains`, etc. |
| `value` | Array of strings (see Value Formats below) |

### Example (Nested)
```json
{
  "conjunction": "and",
  "children": [
    {
      "conjunction": "or",
      "conditions": [
        { "field_name": "Status", "operator": "is", "value": ["Done"] }
      ]
    }
  ]
}
```

## 2. View Property Filter

Used in `scripts/create_view.py` and `scripts/patch_view.py` inside the `property.filter_info` object.

### Structure

| Parameter | Type | Required | Description |
|---|---|---|---|
| `conjunction` | string | **Yes** | `"and"` or `"or"`. |
| `conditions` | list | Yes | List of conditions. **No nesting supported.** |

### Condition Item
| Field | Value |
|---|---|
| `field_id` | String (e.g., "fldxxxx") **NOT name** |
| `operator` | `is`, `isGreater`, `contains`, etc. |
| `value` | Array of strings (see Value Formats below) |

### Example (Flat only)
```json
{
  "conjunction": "and",
  "conditions": [
    { "field_id": "fldxx1", "operator": "is", "value": ["Done"] },
    { "field_id": "fldxx2", "operator": "isGreater", "value": ["100"] }
  ]
}
```

## 3. Supported Operators

The following operators are supported for **both** Record Search and View Property filters:

| Operator | Description | Notes |
|---|---|---|
| `is` | Equals | |
| `isNot` | Not equals | Not supported for **Date** fields |
| `contains` | Contains | Not supported for **Date** fields |
| `doesNotContain` | Does not contain | Not supported for **Date** fields |
| `isEmpty` | Is empty | |
| `isNotEmpty` | Is not empty | |
| `isGreater` | Greater than | |
| `isGreaterEqual` | Greater than or equal | Not supported for **Date** fields |
| `isLess` | Less than | |
| `isLessEqual` | Less than or equal | Not supported for **Date** fields |

> For `is` / `isNot`, the value must contain exactly one element; for `isEmpty` / `isNotEmpty`, the value must be an empty array `[]`.
> **Note**: Operators marked with have field type restrictions. Verify compatibility with your field type before use.

## 4. Value Formats

Many value formats are shared between Record Search and View Property filters, but **Select/Multi Select is not**.

### Generic Types
| Field Type | Record Search `value` example | View Property `value` example | Notes |
|---|---|---|---|
| Text | `["Some text"]` | `["Some text"]` | |
| Number | `["100"]` | `["100"]` | |
| Select / Multi Select | `["Option A"]` | `["optxxxxxxxx"]` | View uses option id from `list_fields` (`property.options`). |
| Checkbox | `["true"]` | `["true"]` | Only `is` supported. |

### Special Types
| Field Type | Value Example | Notes |
|---|---|---|
| **Date** | `["ExactDate", "1642672432000"]` | Timestamp in ms. |
| **Date (Dynamic)** | `["Today"]`, `["Tomorrow"]`, `["CurrentWeek"]` | Dynamic ranges. |
| **Person** | `["ou_xxx"]` or `["email_xxx@yyy.zzz"]` | Use Open ID, or use `email_` prefix to pass email which will be converted to Open ID automatically. |
| **Group** | `["oc_xxx"]` | Group ID. |

### Getting option id (for View Property filters)

Use `scripts.list_fields` to fetch field metadata, then read `property.options` for the Select field. Each option entry includes its id (commonly `property.options[].id`).
