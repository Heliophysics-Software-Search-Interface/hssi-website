[← Back to Backend](index.md)

# models/structurizer.py

Translates the Django model structure into serializable structures that the
frontend form modules in `frontend/forms` use to generate forms. Touch this
when changing how model fields map to form widgets or how form data is
serialized.

**Source:** [django/website/models/structurizer.py](../../../django/website/models/structurizer.py)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Classes](#classes)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `FORM_CONFIG_ATTR` | `"form_config"`: attribute name on a model field holding custom widget properties. |
| `registered_structures` | Registry of `ModelStructure`s keyed by type name, used to serialize nested objects. |

## Types

| Name | Description |
|---|---|
| `WidgetPrimitiveName` | String enum of the frontend widget class names for primitive fields: `CharWidget`, `NumberWidget`, `TextAreaWidget`, `UrlWidget`, `EmailWidget`, `DateWidget`, `CheckboxWidget`. |

## Classes

### `ModelSubfield`

Describes one field of a form structure: its name, widget type, requirement level and widget properties.

| Member | Kind | Description |
|---|---|---|
| `name` | class attribute | Field name. |
| `row_name` | class attribute | Alternate name used to look up the field's value on a model object. |
| `type` | class attribute | Widget type name, or the related model's name for relation fields. |
| `requirement` | class attribute | `RequirementLevel` of the field; optional by default. |
| `properties` | class attribute | Widget configuration properties. |
| `multi` | class attribute | Whether the field holds multiple values. |
| `serialized()` | method | The subfield as a serializable dictionary. |
| `to_json()` | method | Intended to return the subfield as JSON; passes the `serialized` method itself to `json.dumps` rather than calling it. |
| `create(field)` | class method | Builds a subfield from a model field, picking the widget type from `form_config`, the related model, or the field's Django form widget. |
| `define(name, type, requirement, properties, multi, row_name)` | class method | Builds a subfield from explicit values. |

### `ModelStructure`

Describes the form structure of a model: a top field followed by subfields.

| Member | Kind | Description |
|---|---|---|
| `target_model` | class attribute | The `HssiModel` this structure describes. |
| `type_name` | class attribute | Name of the structure, used as its type on the frontend. |
| `top_field` | class attribute | The structure's main `ModelSubfield`. |
| `subfields` | class attribute | The remaining `ModelSubfield`s. |
| `generate(model)` | class method | Builds a structure from a model's top field and subfields. |
| `define(target_model, name, *fields)` | class method | Builds a structure from explicit subfields; the first becomes the top field. |
| `split(field_name, name_left, name_right)` | method | Splits the structure into two at the named subfield; returns `[self]` if not found. |
| `serialize_model_object(object, recursive, access, access_ovr)` | method | A dictionary of the object's values for this structure's fields only, nesting related objects if `recursive`. Raises on insufficient access or an incompatible model. |
| `serialized()` | method | The structure as a serializable dictionary with `targetModel`, `typeName` and `subfields`; warns if there is no top field. |
| `to_json()` | method | The serialized structure as a JSON string. |

## Functions

| Function | Description |
|---|---|
| `register_structure(*structure)` | Adds structures to `registered_structures` by type name. |
