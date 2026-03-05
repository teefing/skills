# Bitable form operations

This guide documents the **complete set** of form operations supported by this Skill.

Important: In Bitable v1, a **form is backed by a form view**, so `form_id` is the `view_id` of a view where `view_type=form`.

All scripts below live in `scripts/`.

## Form metadata

### Get form metadata

```bash
python3 -m scripts.get_form --app_token <APP_TOKEN> --table_id <TABLE_ID> --form_id <FORM_ID>
```

### Patch form metadata

`--form` is a JSON object. Available fields:

```json
{
  "name": "New Form Name",
  "description": "Form description",
  "shared": true,
  "submit_limit_once": true
}
```

```bash
python3 -m scripts.patch_form \
  --app_token <APP_TOKEN> \
  --table_id <TABLE_ID> \
  --form_id <FORM_ID> \
  --form '{"name":"问卷表单","shared":true,"submit_limit_once":true}'
```

## Form questions (fields)

### List questions

```bash
python3 -m scripts.list_form_fields --app_token <APP_TOKEN> --table_id <TABLE_ID> --form_id <FORM_ID> [--page_token <TOKEN>] [--page_size <SIZE>]
```

### Patch a question

`--body` is a JSON object. Available fields:

```json
{
  "pre_field_id": "",
  "title": "Question Title",
  "description": "Question Help Text",
  "required": true,
  "visible": true
}
```

```bash
python3 -m scripts.patch_form_field \
  --app_token <APP_TOKEN> \
  --table_id <TABLE_ID> \
  --form_id <FORM_ID> \
  --field_id <FIELD_ID> \
  --body '{"title":"1. 你的姓名","required":true}'
```

