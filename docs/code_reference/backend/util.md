[← Back to Backend](index.md)

# util.py

Shared helpers used across the backend: access and requirement levels,
homepage filter/search URL encoding, and finding or replacing database
references to an object. Touch this when changing access rules or building
links into the homepage filters.

**Source:** [django/website/util.py](../../../django/website/util.py)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `SOFTWARE_FUNCAT_FILEPATH` | `"./software_funcat_map.csv"`: file used to export and import software functionality assignments. |
| `SPACE_REPLACE` | Regex matching `_`, `-` and `.`, for replacing with spaces. |
| `PARENTHESIS_MATCH` | Regex matching a parenthesized group and capturing its contents. |
| `FILTER_URL_UID_ENCODE_LENGTH` | `7`: number of base64 characters of a UUID kept in a filter URL value. |
| `SOFTWARE_FILTER_FIELD_PARAM_MAP` | Software field name to the suffix used in encoded filter URL values. |
| `REQ_LVL_ATTR` | `"data-hssi-required"`: HTML attribute holding a field's requirement level. |

## Types

| Name | Description |
|---|---|
| `RequirementLevel` | Integer enum of form field requirement levels: `OPTIONAL`, `RECOMMENDED`, `MANDATORY`. |
| `AccessLevel` | Integer enum of user access levels, from `PUBLIC` (0) to `ADMIN` (4); `from_user(user)` gives a user's level from their superuser, staff and login status. |

## Functions

| Function | Description |
|---|---|
| `name_to_abbreviation(name)` | Builds a four-character abbreviation from a name's words. |
| `uuid_to_urlsafe_base64(uid)` | Encodes a UUID as unpadded URL-safe base64, matching the frontend encoding. |
| `shorten_software_filter_value(field_name, uid)` | Encodes a filter value as the shortened UUID plus the field's suffix, matching `frontend/filters/urlEncoding.ts`; raises `ValueError` for unsupported fields. |
| `build_software_filter_query(field_name, uid)` | Builds the homepage `filt=` query string for a filter value. |
| `build_software_field_search_query(field_alias, value)` | Builds the homepage `q=` query string for a `field:"value"` search. |
| `find_database_references(object)` | All `(related object, field)` pairs in the database that reference the object. |
| `replace_database_references(old_object, new_object, unique_mapping)` | Repoints every reference to the old object at the new one in a transaction, preserving sorted many-to-many order; with `unique_mapping` off, avoids duplicate many-to-many links. |
| `export_software_functioncategory_names()` | Writes each software's functionality categories to `SOFTWARE_FUNCAT_FILEPATH` and returns the text. |
| `import_software_functioncategory_names(data)` | Adds functionality categories to software from the given text or `SOFTWARE_FUNCAT_FILEPATH`, in a transaction; raises if a category isn't found. |
