[← Back to Backend](index.md)

# views/model_rows.py

JSON views that serialize model rows for the frontend, filtered by the
requesting user's access level, plus a user-friendly view of one software
entry. Touch this when changing how model data is fetched by the frontend.

**Source:** [django/website/views/model_rows.py](../../../django/website/views/model_rows.py)

## Contents

- [Functions](#functions)

---

## Functions

| Function | Description |
|---|---|
| `get_fields_param(get)` | The comma-separated `columns` query parameter as a list of field names, or `None`. |
| `get_recursive_param(get)` | Whether the `recursive` query parameter is `"true"`. |
| `get_model_rows_all(request, model_name)` | Returns JSON `{data, total}` of serialized objects of an `HssiModel`, with optional `ids`, `offset`/`limit`, `columns` and `recursive` query parameters. For `VerifiedSoftware`, also accepts `sort` (`date`, `create` or `name`) to order the whole catalog before paging, and adds each entry's `metadata_modified_date`. Raises if the user's access level is below the model's. |
| `get_model_row(request, model_name, uid)` | Returns JSON of one serialized object by UID; falls back to the model's first object if the UID is invalid, and is forbidden for `SoftwareEditQueue`. |
| `api_view(request, uid)` | Returns a user-friendly JSON view of a software's submission data, with controlled-list fields reduced to name strings; looks the software up as published first, then through its edit link. |
