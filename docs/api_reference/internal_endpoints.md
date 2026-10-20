[← Back to Overview](overview.md)

# Internal Endpoints

These endpoints back the website's own admin/submission-form UI rather than
being a general public API. They're documented here for completeness, not
as a recommendation to build new integrations against them — they have
looser error handling than the endpoints in
[Software Catalog API](software_catalog_api.md) and
[Submission API](submission_api.md), and none of their behavior is covered
by the test suite.

None of these go through the camelCase renderer; keys below are shown
exactly as the server sends/expects them.

## Contents

- [Structure](#structure)
- [GET /api/models/structures/](#get-apimodelsstructures)
- [GET /api/models/{model_name}/choices/](#get-apimodelsmodel_namechoices)
- [GET /api/models/{model_name}/form/](#get-apimodelsmodel_nameform)
- [GET /api/models/{model_name}/rows/all/](#get-apimodelsmodel_namerowsall)
- [GET /api/models/{model_name}/rows/{uid}/](#get-apimodelsmodel_namerowsuid)

---

## Structure

**Why are these generic, not one-per-model?**

Every model in this codebase — `OperatingSystem`, `ProgrammingLanguage`,
`Keyword`, `SoftwareEditQueue`, and dozens more — inherits from one
`HssiModel` base class (`website/models/base.py`). That shared base is what
lets five endpoints cover every model in the app instead of needing one
bespoke endpoint per model:

- Every model gets a UUID primary key (`id`) the same way.
- Every model implements `get_choice()`, returning a uniform
  `(id, name, keywords, tooltip, identifier)` tuple no matter what the
  model actually represents.
- Every model declares an `access: AccessLevel` class attribute, so "can
  this caller read/write this model" is answerable generically too.

Because every model honors that same contract, a single view can take a
`model_name` from the URL, resolve it with Django's
`apps.get_model(app_label, model_name)`, and operate on it the same way
regardless of which specific table it is — the same trick Django's own
admin site uses to generate a change-list and edit form for any registered
model without per-model code.

That's the shape behind each endpoint below:

| Endpoint | Mirrors |
|---|---|
| `structures/` | Introspecting a model's fields (like `Model._meta.get_fields()`) |
| `{model_name}/choices/` | A queryset of choices for a dropdown (like populating a `ModelChoiceField`) |
| `{model_name}/form/` | A generic add/change form (like Django admin's auto-generated form) |
| `{model_name}/rows/all/` | A generic list view (`Model.objects.all()`, exposed over HTTP) |
| `{model_name}/rows/{uid}/` | A generic detail view (`Model.objects.get(pk=uid)`) |

This genericness is also why the error handling below is looser than the
public API's: `{model_name}` is a live lookup against *any* `HssiModel`
subclass in the app, so there's a much larger space of "what could go
wrong" than a hand-written endpoint built around one specific resource.

## `GET /api/models/structures/`

No parameters. Returns the schema the submission form renders itself from:

```json
{"data": [{"...": "registered form-field structure entries"}], "fieldMap": {"...": "..."}}
```

## `GET /api/models/{model_name}/choices/`

Returns the available choices for a controlled-vocabulary model (e.g.
`OperatingSystem`, `ProgrammingLanguage`) — the dropdown options shown in
the submission form.

**Query parameters:** any query parameter is treated as a Django filter
keyword, and its value is parsed with Python's `ast.literal_eval` — so
values must be valid Python literals (e.g. a quoted string), not bare text.
An unquoted value will raise an error server-side rather than a clean `400`.

```bash
curl "https://hssi.hsdcloud.org/api/models/ProgrammingLanguage/choices/"
```

```json
{"data": [{"id": "...", "name": "Python"}, {"id": "...", "name": "Rust"}]}
```

**Errors:** `400 "Target model must inherit from HssiModel"` if `model_name`
isn't a recognized controlled-vocabulary model.

## `GET /api/models/{model_name}/form/`

Renders an HTML form fragment for the given model, not JSON. Out of scope
for programmatic use.

## `GET /api/models/{model_name}/rows/all/`

Lists rows of an `HssiModel` subclass, gated by an internal role-based
access-level system.

**Query parameters**

| Param | Description |
|---|---|
| `ids` | Comma-separated list of primary keys to restrict to. |
| `offset`, `limit` | Pagination (default `0`/`25` if not present). Non-integer values return `400`. |
| `columns` | Comma-separated list of fields to include in each row. |
| `recursive` | `"true"`/`"false"` — whether related objects are serialized recursively. |

```bash
curl "https://hssi.hsdcloud.org/api/models/Keyword/rows/all/?limit=5&columns=id,name"
```

```json
{"data": [{"id": "...", "name": "magnetosphere"}], "total": 42}
```

> Insufficient access on this particular endpoint surfaces as an unhandled
> server error rather than a clean `403` — a known inconsistency versus
> the single-row endpoint below.

## `GET /api/models/{model_name}/rows/{uid}/`

Same `columns`/`recursive` parameters as above, for a single row.

- `{model_name}` of `SoftwareEditQueue` (or any subclass) is explicitly
  blocked: `403`.
- Insufficient access: `403 "Unauthorized"`.
- If `{uid}` doesn't parse as a UUID, this silently falls back to
  returning the *first* row of the model rather than a `404` — worth
  knowing if you're debugging an "invalid id" case that unexpectedly
  returns data.

```bash
curl "https://hssi.hsdcloud.org/api/models/Keyword/rows/9e1a2b3c-.../"
```

```json
{"id": "9e1a2b3c-...", "name": "magnetosphere"}
```
