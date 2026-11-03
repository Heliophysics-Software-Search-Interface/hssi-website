[← Back to Backend](index.md)

# admin/actions.py

The custom HSSI admin site and its extra admin views for exporting and
importing the database as CSV, fetching repository metadata, and refreshing
controlled vocabularies. Touch this when adding a custom admin page or bulk
database operation.

**Source:** [django/website/admin/actions.py](../../../django/website/admin/actions.py)

## Contents

- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `HssiAdminSite`

The HSSI admin site, with custom titles, index template, and extra URLs. **Extends:** `AdminSite`

| Member | Kind | Description |
|---|---|---|
| `site_title` | class attribute | `'HSSI admin'`. |
| `site_header` | class attribute | `'HSSI administration'`. |
| `index_title` | class attribute | `'HSSI administration'`. |
| `index_template` | class attribute | `'admin/index.html'`. |
| `get_urls()` | method | The default admin URLs plus `export_db_new/`, `import_db_new/`, `get_metadata/` and `fetch_vocab/`, inserted before the final catch-all pattern. |

## Functions

| Function | Description |
|---|---|
| `view_get_metadata(request)` | Returns JSON metadata extracted from the `repo_url` GET parameter's repository; 400 if no URL is given. |
| `view_export_db_new(request)` | On POST from a superuser, exports the database to CSV files; always redirects to the admin index. |
| `view_import_db_new(request)` | On POST from a superuser, deletes all HSSI model data and reimports it from CSV files; always redirects to the admin index. |
| `fetch_vocab(request)` | Superuser only: refreshes every controlled vocabulary from its source URL, repointing references from matching old terms to the new ones and appending " (OUTDATED)" to unmatched old names, then reloads function categories from TTL; redirects to the admin index. |
| `fetch_heliophysics_api(request)` | Fetches observatories and instruments from the heliophysics.net API into `InstrumentObservatory`; returns an empty response. |
