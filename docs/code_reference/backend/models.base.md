[← Back to Backend](index.md)

# models/base.py

The abstract base models every HSSI model inherits from, plus shared field
length limits and the choice tuple used by autocomplete form widgets. Touch
this when changing behavior common to all models, such as serialization,
search terms, or controlled-vocabulary handling.

**Source:** [django/website/models/base.py](../../../django/website/models/base.py)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `FIELD_FUNCTIONCATEGORY_FULLNAME` | `"fullname"`: pseudo-field name that makes `FunctionCategory` serialization include the category's full name. |
| `LEN_LONGNAME` | `512`: max length for long name fields. |
| `LEN_NAME` | `128`: max length for name fields. |
| `LEN_SHORTNAME` | `16`: max length for short name fields. |
| `LEN_ABBREVIATION` | `5`: max length for abbreviation fields. |

## Types

| Name | Description |
|---|---|
| `FIELD_HAS_FOREIGN_KEY` | Union of `ForeignKey \| ManyToManyField \| OneToOneField`, the field types that reference another model. |
| `ModelObjectChoice` | Named tuple describing one autocomplete choice for a model object: `id`, `name`, `keywords`, `tooltip` and optional `identifier`. |

## Classes

### `HssiBase`

Metaclass for HSSI models that sets a `name` attribute on each field descriptor, so fields can be referred to by name without hardcoded strings. **Extends:** `models.base.ModelBase`

### `HssiModel`

Base class for all models in the HSSI project. **Abstract** **Extends:** `models.Model`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | Minimum `AccessLevel` needed to read the model's data; `ADMIN` by default. |
| `id` | field | UUID primary key, generated automatically. |
| `get_search_terms()` | method | Terms used to filter autocomplete suggestions in form interfaces; by default the words of `str(self)`. |
| `get_choice()` | method | The object as a `ModelObjectChoice` for autocomplete widgets. |
| `get_tooltip()` | method | Tooltip text for the object's choice; empty by default. |
| `get_identifier_url()` | method | Identifier URL for the object's choice; `None` by default. |
| `collapse_objects(queryset)` | static method | Merges all objects in a queryset into the first one, filling its empty fields and many-to-many entries from the others, repointing all references to it, and deleting the rest. |
| `get_top_field()` | class method | The model's display field; `None` by default. |
| `get_second_top_field()` | class method | The model's secondary display field; `None` by default. |
| `get_subfields()` | class method | The model's concrete, editable fields, excluding the top field and auto-created fields. |
| `get_serialized_data(access, recursive, access_override, fields)` | method | The object's fields as a dictionary, optionally limited to `fields`; nests serialized related objects if `recursive`. Raises if neither access level meets the model's `access`. |
| `to_user_str()` | method | User-facing string for the object; `str(self)` by default. |

### `HssiSet`

Base for models whose rows flag objects of another model, sharing their UUID; reads are forwarded to the matching `target_model` object. **Abstract** **Extends:** `HssiModel`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `ADMIN`. |
| `target_model` | class attribute | The model whose objects this set references; set by subclasses. |
| `id` | field | UUID primary key, equal to the target object's UUID. |
| `get_search_terms()` | method | The target object's search terms. |
| `get_choice()` | method | The target object's choice. |
| `get_tooltip()` | method | The target object's tooltip. |
| `get_serialized_data(access, recursive, accessOverride, fields)` | method | The target object's serialized data, checked against this set's `access`. |

### `ControlledList`

Base class for all controlled vocabulary lists in the HSSI project. **Abstract** **Extends:** `HssiModel`

| Member | Kind | Description |
|---|---|---|
| `name` | field | Name of the term. |
| `identifier` | field | Identifier URL of the term. |
| `definition` | field | Definition of the term, used as its tooltip. |
| `homepage_filter_field` | class attribute | Software filter field that links this vocabulary to a homepage filter, or `None`. |
| `get_top_field()` | class method | Returns the `name` field as the model's display field. |
| `get_tooltip()` | method | The term's `definition`. |
| `get_homepage_filter_url()` | method | URL of the published resources page filtered by this term, or `None` if `homepage_filter_field` is unset. |
| `get_search_terms()` | method | Words of the name split on spaces and punctuation, plus the identifier. |
| `post_fetch()` | class method | Hook run after the vocabulary is fetched from its source; does nothing by default. |

### `ControlledGraphList`

Base class for controlled lists whose terms form a parent/child hierarchy. Subclasses must define a `children` many-to-many field with `related_name='parent_nodes'`. **Abstract** **Extends:** `ControlledList`

| Member | Kind | Description |
|---|---|---|
| `children` | field | Child terms (declared here as an editor hint; defined by subclasses). |
| `parent_nodes` | field | Reverse relation to parent terms. |
| `apply_old_to_new_mapping(mapping)` | class method | Repoints references from old terms to new terms by full name and deletes the old terms; does nothing if any old name is not found. |
| `get_parent_nodes()` | class method | All terms that have at least one child, ordered by name. |
| `get_object_with_full_name(full_name)` | class method | Finds a term by its `"Parent: Child"` full name path; raises if the path doesn't resolve. |
| `get_full_name()` | method | The term's path through its first parent at each level, joined with `": "`. |
| `get_serialized_data(access, recursive, access_ovr, fields)` | method | Serialized data from `HssiModel`, plus `children` and `parents` ID lists unless `fields` excludes them. |
