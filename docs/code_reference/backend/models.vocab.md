[← Back to Backend](index.md)

# models/vocab.py

Controlled vocabulary models that categorize software entries, such as
keywords, programming languages, file formats, regions and function
categories. Touch this when adding a vocabulary, a field on a vocabulary
term, or changing post-fetch processing of a vocabulary.

**Source:** [django/website/models/vocab.py](../../../django/website/models/vocab.py)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `REGION_MAPPING_TTL` | Maps old region full names to their replacements in the current region vocabulary. |

## Types

| Name | Description |
|---|---|
| `InstrObsType` | Integer choices for whether an `InstrumentObservatory` entry is an `INSTRUMENT` (1), `OBSERVATORY` (2) or `UNKNOWN` (3). |

## Classes

### `Keyword`

A free-form keyword attached to software entries. **Extends:** `HssiModel`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `name` | field | The keyword text. |
| `get_top_field()` | class method | Returns the `name` field as the model's display field. |
| `get_homepage_filter_url()` | method | URL of the published resources page with a keyword field search for this keyword, since keywords have no filter menu tab. |

### `OperatingSystem`

Operating system on which the software can run. **Extends:** `ControlledList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |

### `CpuArchitecture`

CPU architecture on which the software can run. **Extends:** `ControlledList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |

### `RepoStatus`

Repo status as defined by the [repostatus.org](https://www.repostatus.org/badges/latest/ontology.jsonld) JSON-LD. **Extends:** `ControlledList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `image` | field | URL of the status badge image. |

### `ProgrammingLanguage`

Primary programming language used to develop the software. **Extends:** `ControlledList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `homepage_filter_field` | class attribute | `"programming_language"`. |
| `version` | field | Language version, appended to the name when displayed. |

### `DataInput`

Ways that the software can accept data as input. **Extends:** `ControlledList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `homepage_filter_field` | class attribute | `"data_sources"`. |
| `abbreviation` | field | Short abbreviation of the term. |

### `FileFormat`

File formats supported as input or output types by the software. **Extends:** `ControlledList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `extension` | field | File extension, shown after the name. |
| `softwares_to` | field | Editor hint for a reverse relation to `Software`; the actual reverse relations are `softwares_in` and `softwares_out`. |
| `softwares_from` | field | Editor hint for a reverse relation to `Software`; the actual reverse relations are `softwares_in` and `softwares_out`. |

### `InstrumentObservatory`

An observatory or scientific research instrument. **Extends:** `ControlledList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `type` | field | Whether this is an instrument or observatory, an `InstrObsType`. |
| `abbreviation` | field | Short abbreviation, shown after the name. |
| `landing_url` | field | User-friendly landing page URL preferred over `identifier` for outbound links; set during vocab fetch. |
| `get_search_terms()` | method | Search terms from `ControlledList`, plus the abbreviation and the name's words. |
| `get_identifier_url()` | method | The `identifier`, or `None` if empty. |
| `get_landing_url()` | method | The `landing_url`, falling back to `identifier`, or `None`. |

### `FunctionCategory`

A software functionality category, arranged as a parent/child hierarchy. **Extends:** `ControlledGraphList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `homepage_filter_field` | class attribute | `"software_functionality"`. |
| `abbreviation` | field | Short abbreviation of the category. |
| `backgroundColor` | field | Background color of the category's tag. |
| `textColor` | field | Text color of the category's tag. |
| `children` | field | Child categories. |
| `parent_nodes` | field | Reverse relation to parent categories. |
| `get_choice()` | method | The category as a `ModelObjectChoice`, named by its full name. |
| `post_fetch()` | class method | Fills in missing abbreviations and assigns each parent group a distinct hue, with lighter shades for children and contrasting text colors. |
| `get_search_terms()` | method | Search terms from `ControlledList`, plus each part of the full name. |
| `get_serialized_data(access, recursive, access_ovr, fields)` | method | Serialized data from `ControlledGraphList`, plus the full name if `fields` includes `FIELD_FUNCTIONCATEGORY_FULLNAME`. |

### `Region`

Region of the sun which relates to the software. **Extends:** `ControlledGraphList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `homepage_filter_field` | class attribute | `"related_region"`. |
| `children` | field | Child regions. |
| `post_fetch()` | class method | Clears any `identifier` that isn't a valid URL. |
| `get_full_name()` | method | Path of parent names to this region, with the parent's name removed from each child's name. |

### `Phenomena`

Solar phenomena that relate to the software. **Extends:** `ControlledGraphList`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `children` | field | Child phenomena. |
