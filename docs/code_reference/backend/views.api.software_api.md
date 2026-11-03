[← Back to Backend](index.md)

# views/api/software_api.py

REST API views for published software: reading and token-gated partial
updates of a single entry, listing entries, and bulk submission. Touch this
when changing the public software API or how external tools update entries.

**Source:** [django/website/views/api/software_api.py](../../../django/website/views/api/software_api.py)

## Contents

- [Classes](#classes)

---

## Classes

### `HSSIGenericAPIView`

Base generic API view for the project's API views. **Extends:** `GenericAPIView`

| Member | Kind | Description |
|---|---|---|
| `get_serializer(*args, **kwargs)` | method | Same as the base method, typed to return a `Serializer`. |

### `SoftwareDetailAPI`

Returns or partially updates a single published software, by UUID or slug; CSRF-exempt. **Extends:** `HSSIGenericAPIView`

| Member | Kind | Description |
|---|---|---|
| `serializer_class` | class attribute | `SoftwareSerializer`. |
| `default_view` | class attribute | Serializer view used for GET, `SerialView.STANDARD`. |
| `authentication_classes` | class attribute | Empty: no session or token authentication. |
| `get_permissions()` | method | `HasUpdateToken` for PATCH, `AllowAny` otherwise. |
| `get_serializer_class()` | method | `SubmissionSerializer` for PATCH, `SoftwareSerializer` otherwise. |
| `get(request, uid)` | method | GET: returns the software serialized in `default_view`, or 404. |
| `patch(request, uid)` | method | PATCH: validates and saves a partial metadata update via `SubmissionSerializer` in USER view; returns the software ID and the updated field names, or 404. |

### `SoftwareViewAPI`

Same as `SoftwareDetailAPI`, but GET renders in the USER view. **Extends:** `SoftwareDetailAPI`

| Member | Kind | Description |
|---|---|---|
| `default_view` | class attribute | `SerialView.USER`. |

### `SoftwareListAPI`

Lists published software as ID, name and slug entries, ordered by name. **Extends:** `APIView`

| Member | Kind | Description |
|---|---|---|
| `authentication_classes` | class attribute | Empty: no session or token authentication. |
| `permission_classes` | class attribute | `[AllowAny]`. |
| `get(request)` | method | GET: returns the list, optionally filtered by exact `repo_url`; `?view=jsonld` returns full JSON-LD records instead, and any other `view` is a 400. |

### `SubmissionAPI`

Accepts new software submissions as a JSON array; CSRF-exempt. **Extends:** `APIView`

| Member | Kind | Description |
|---|---|---|
| `authentication_classes` | class attribute | Empty: no session or token authentication. |
| `permission_classes` | class attribute | `[AllowAny]`. |
| `post(request)` | method | POST: validates and saves every item in one transaction (400 with errors if any fail), then creates a 90-day edit link for each and emails it; returns 201 with the new software IDs. |
