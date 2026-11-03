[← Back to Backend](index.md)

# admin/csv_export.py

Exports every HSSI model to CSV files and imports them back, including the
ordering tables of sorted many-to-many fields. Touch this when adding a model
that must be included in database export/import, or changing import order.

**Source:** [django/website/admin/csv_export.py](../../../django/website/admin/csv_export.py)

## Contents

- [Constants](#constants)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `DEFAULT_DB_EXPORT_PATH` | `'/django/website/config/db/'`: directory the CSV files are written to and read from. |

## Functions

| Function | Description |
|---|---|
| `camel_to_snake(name)` | Converts a `CamelCase` name to `snake_case`. |
| `snake_to_camel(name)` | Converts a `snake_case` name to `CamelCase`. |
| `model_csv_filepath(model, directory)` | CSV file path for a model: its snake-case name in the directory. |
| `remove_all_model_entries()` | Deletes every row of every HSSI model, in reverse dependency order. |
| `export_model_csv(model, directory)` | Exports all rows of a model to its CSV file, replacing any existing file. |
| `export_db_csv()` | Exports every HSSI model plus the sorted many-to-many ordering tables of `Software` to CSV. |
| `import_model_csv(model, filepath, exclude_fields, two_passes)` | Imports a model's CSV file in a transaction, skipping excluded fields; optionally imports twice to resolve self-references. Raises on import errors; skips missing files. |
| `import_db_csv()` | Imports every HSSI model and the `Software` ordering tables from CSV, in dependency order. |
