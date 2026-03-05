# Record Field Value Shapes

This guide describes the data structure of record `fields` for both **Reading** (Search/Get) and **Writing** (Create/Update).

> **Important**: The "Write Shape" is often simpler than the "Read Shape". When updating records, do not simply copy-paste the read response; ensuring you match the required Write Shape is critical.

## Contents
- [Update Behavior](#update-behavior)
- [Field Value Mapping Table](#field-value-mapping-table)
- [Detailed Field Specifications](#detailed-field-specifications)
  - [Person (User)](#person-user)
  - [Attachment](#attachment)
  - [Link (Single/Duplex)](#link-singleduplex)
  - [Location](#location)
  - [Formula \& Lookup](#formula--lookup)

## Update Behavior

- **Incremental Update**: Updates are incremental. Only the fields you include in the `fields` object will be modified; others remain unchanged.
- **Clearing Values**: To clear/empty a field, set its value to `null`.

```json
{
  "fields": {
    "Text Field": null
  }
}
```

## Field Value Mapping Table

| Field Type | UI Type | Read Shape | Write Shape | Write Example | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Text** | `Text` | `[{ "text": "...", "type": "text" }]` | `string` | `"Plain text"` | |
| **Barcode** | `Barcode` | `[{ "text": "...", "type": "text" }]` | `string` | `"CODE123"` | |
| **Number** | `Number` | `number` | `number` | `123.45` | |
| **Progress** | `Progress` | `number` | `number` | `0.8` | |
| **Currency** | `Currency` | `number` | `number` | `99.99` | |
| **Rating** | `Rating` | `number` | `number` | `5` | |
| **Single Select** | `SingleSelect` | `string` | `string` | `"Option A"` | |
| **Multi Select** | `MultiSelect` | `string[]` | `string[]` | `["Option A", "Option B"]` | |
| **Date** | `DateTime` | `number` (ms timestamp) | `number` (ms timestamp) | `1674206443000` | |
| **Checkbox** | `Checkbox` | `boolean` | `boolean` | `true` | |
| **Person** | `User` | `[{ "id": "ou_xxx", "name": "...", "email":"...", "avatar_url":"...", "en_name":"..."}]` | `[{ "id": "ou_xxx" }]` or `[{ "email": "xxx@yyy.zzz" }]` | `[{"email": "xxx@yyy.zzz"}]` | Email will be converted to `open_id` automatically. |
| **Group** | `GroupChat` | `[{ "id": "oc_xxx", "name": "...", ... }]` | `[{ "id": "oc_xxx" }]` | `[{"id": "oc_12345"}]` | |
| **Phone** | `Phone` | `string` | `string` | `"13900000000"` | Max 64 chars. |
| **URL** | `Url` | `{ "text": "...", "link": "..." }` | `{ "text": "...", "link": "..." }` | `{"text": "Lark", "link": "https://larksuite.com"}` | |
| **Attachment** | `Attachment` | `[{ "file_token": "...", "name": "...", ... }]` | `[{ "file_token": "..." }]` | `[{"file_token": "boxcn..."}]` | Token from Drive API. |
| **Link** | `SingleLink`, `DuplexLink` | `{ "link_record_ids": ["rec_xxx"] }` | `string[]` | `["rec_xxx", "rec_yyy"]` | **Correction**: Write shape is just the ID array. |
| **Location** | `Location` | `{ "location": "lng,lat", "address": "...", ... }` | `string` | `"116.397,39.903"` | Input "lng,lat". |
| **Formula** | `Formula` | `[{ "text": "...", "type": "..." }]` (varies) | **Read Only** | - | Value structure depends on result type. |
| **Lookup** | `Lookup` | (varies) | **Read Only** | - | |
| **Created Time** | `CreatedTime` | `number` | **Read Only** | - | |
| **Modified Time** | `ModifiedTime` | `number` | **Read Only** | - | |
| **Created By** | `CreatedUser` | `User` object structure | **Read Only** | - | |
| **Modified By** | `ModifiedUser` | `User` object structure | **Read Only** | - | |
| **Auto Number** | `AutoNumber` | `string` | **Read Only** | - | |

## Detailed Field Specifications

### Person (User)
*   **Write**: Only `id` is required.
    ```json
    [
      { "id": "ou_xxxxxx" }
    ]
    ```

*   **Write (Alternative)**: You can pass `email`, it will be converted to `open_id` automatically.
    ```json
    [
      { "email": "xxx@yyy.zzz" }
    ]
    ```

### Attachment
*   **Write**: Only `file_token` is required. You must upload the file to Lark Drive first to get the token.
    ```json
    [
      { "file_token": "boxcnjQg8..." }
    ]
    ```

### Link (Single/Duplex)
*   **Write**: Pass an array of record IDs directly.
    ```json
    ["recHTLvO7x", "recbS8zb2m"]
    ```
    *Note: The Read format returns `{ "link_record_ids": [...] }`, but the Write format is a simple list of strings.*

### Location
*   **Write**: A single string containing comma-separated longitude and latitude.
    ```json
    "116.352681,40.01437"
    ```
*   **Read**: Returns a full object with address details.
    ```json
    {
      "location": "116.352681,40.01437",
      "pname": "北京市",
      "cityname": "北京市",
      "adname": "海淀区",
      "address": "学清路10号院...",
      "name": "字节跳动",
      "full_address": "..."
    }
    ```

### Formula & Lookup
These fields are **Read Only**. Their structure mimics the underlying data type but often wrapped.
*   **Example (Text formula)**:
    ```json
    [
      { "text": "Calculated Result", "type": "text" }
    ]
    ```
