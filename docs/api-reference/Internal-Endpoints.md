[← Back to Overview](Overview.md)

# Internal Endpoints

These endpoints back the website's own admin/submission-form UI rather than
being a general public API. They're documented here for completeness, not
as a recommendation to build new integrations against them — they have
looser error handling than the endpoints in
[Software Catalog API](Software-Catalog-API.md) and
[Submission API](Submission-API.md), and none of their behavior is covered
by the test suite.

None of these go through the camelCase renderer; keys below are shown
exactly as the server sends/expects them.

## Contents

- [GET /api/models/structures/](#get-apimodelsstructures)
- [GET /api/models/{model_name}/choices/](#get-apimodelsmodel_namechoices)
- [GET /api/models/{model_name}/form/](#get-apimodelsmodel_nameform)
- [GET /api/models/{model_name}/rows/all/](#get-apimodelsmodel_namerowsall)
- [GET /api/models/{model_name}/rows/{uid}/](#get-apimodelsmodel_namerowsuid)
- [GET /api](#get-api)

---

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
access-level system unrelated to the `HSSI_UPDATE_TOKEN` used elsewhere in
this API.

**Query parameters**

| Param | Description |
|---|---|
| `ids` | Comma-separated list of primary keys to restrict to. |
| `offset`, `limit` | Pagination (both default `0`/`25` if either is present). Non-integer values return `400`. |
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

## `GET /api`

**Not currently functional.**

This route is registered (`path('api', ...)`, named `rest_api`) but its
view function requires a `uid` argument that the URL pattern never
supplies. As currently wired, a plain request to `/api` fails server-side
rather than returning data. It's included here for completeness and so it
isn't mistaken for a working top-level API entry point — don't build
against it until it's fixed.
