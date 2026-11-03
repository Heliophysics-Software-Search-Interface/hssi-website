[← Back to Frontend](index.md)

# forms/fields/modelFieldStructure.ts

Parses the serialized model structures from the backend into a registry of
field types, each naming its widget and its layout of subfields. Touch this
when changing how structure data is parsed or how a field's widget type is
resolved.

**Source:** [frontend/forms/fields/modelFieldStructure.ts](../../../frontend/forms/fields/modelFieldStructure.ts)

## Contents

- [Types](#types)
- [Classes](#classes)

---

## Types

| Name | Description |
|---|---|
| `PropertyContainer` | A field's display and behavior properties: `label`, `tooltipExplanation` (hover tooltip text), `tooltipBestPractise` (help text below the label), `requirementLevel`, `topField`, plus any other keys. |
| `SerializedSubfield` | A subfield as sent by the backend: `name`, `rowName`, `type` (name or resolved `ModelFieldStructure`), `multi`, `requirement` and `properties`. |

## Classes

### `ModelFieldStructure`

A field type with its widget and subfield layout, nestable to any depth; also accepts arbitrary extra attributes from the serialized data.

| Member | Kind | Description |
|---|---|---|
| `widgetType` | field | The widget class, or its registered name until resolved. |
| `typeName` | field | Name the structure is registered and referred to by. |
| `topField` | field | The structure's first subfield, which provides its top-level value. |
| `subfields` | field | The remaining subfields. |
| `getWidgetType()` | method | Resolves the widget class, following `topField` types down if the structure has no widget of its own. |
| `generateInstance()` | method | Creates `ModelSubfield`s for the top field and each subfield, returned as `{topField, subFields}`. |
| `getFieldStructure(fieldType)` | static method | A registered structure by type name. |
| `parseBasicWidgetModels()` | static method | Registers a structure for every registered widget type, named after the widget class. |
| `parseModels(serializedModels)` | static method | Registers the given serialized structures and resolves subfield type names to structures, using each type's top-field properties as defaults. |
