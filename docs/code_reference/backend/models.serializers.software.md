[← Back to Backend](index.md)

# models/serializers/software.py

The REST serializer for `Software`, including its user-friendly view and its
schema.org JSON-LD view. Touch this when changing what the software API or
the detail page's JSON-LD metadata outputs.

**Source:** [django/website/models/serializers/software.py](../../../django/website/models/serializers/software.py)

## Contents

- [Constants](#constants)
- [Classes](#classes)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `URL_TERMSET_DATASOURCE` | URL of the data sources term set, used as `inDefinedTermSet` for data source keywords. |
| `URL_TERMSET_FILEFORMAT` | URL of the file formats term set, used for input and output format keywords. |
| `URL_TERMSET_PHENOMENA` | URL of the phenomena term set, used for related phenomena keywords. |
| `URL_TERMSET_FUNCTIONCATEGORY` | URL of the software functionality term set, used for functionality keywords. |
| `URL_TERMSET_REGIONS` | URL of the regions API. |
| `NAME_UNKOWN` | `"UNKNOWN"`: placeholder name; related items with this name and no identifier are left out of JSON-LD `mentions`. |

## Classes

### `SoftwareSerializer`

Serializer for `Software` model data, with standard, user and JSON-LD views. **Extends:** `HssiSerializer`

| Member | Kind | Description |
|---|---|---|
| `to_representation_user(instance)` | method | User-friendly view: all non-empty fields, with related objects resolved to user-friendly values. |
| `to_representation_jsonld(instance)` | method | The software as a schema.org `SoftwareSourceCode`/`SoftwareApplication` JSON-LD document, with authors, keywords, mentions, funding, license, identifiers and a `subjectOf` catalog record; empty values are dropped. Funders without a recorded award appear as funder-only grants under `funding`, and free-text keywords that duplicate a controlled term are left out. |

## Functions

| Function | Description |
|---|---|
| `serialize_with_relations(obj)` | Serializes a model instance's fields to a dictionary, expanding foreign key and many-to-many values via their serializers or `str()`. |
