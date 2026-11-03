[← Back to Frontend](index.md)

# forms/fields/modelMultisubfield.ts

A field that lets users add and remove any number of entries of the same type,
such as a list of authors or keywords. Touch this when changing how
multi-entry fields render, collapse, or collect their data.

**Source:** [frontend/forms/fields/modelMultisubfield.ts](../../../frontend/forms/fields/modelMultisubfield.ts)

## Contents

- [Constants](#constants)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `faCloseIcon` | Font Awesome close icon HTML, used on each entry's remove button. |

## Classes

### `ModelMultiSubfield`

A `ModelSubfield` that holds a dynamic list of entries, each its own `ModelSubfield` sharing this field's requirement. **Extends:** `ModelSubfield`

| Member | Kind | Description |
|---|---|---|
| `multiFields` | field | The field's current entries. |
| `multi` | property | `true`. Overrides `ModelSubfield.multi`. |
| `getRowContainer()` | method (protected) | The element entry rows are added to, building it if needed. |
| `fillMultiFields(data, notify)` | method | Replaces all entries with one per array item. |
| `clearMultifields()` | method | Removes all entries. |
| `expandMultiFields()` | method | Expands each entry's subfields and un-collapses the field. |
| `collapseMultiFields()` | method | Collapses each entry's subfields. |
| `addNewMultifieldWithValue(value, notify)` | method | Adds an entry filled with the value and returns it. |
| `collapseField()` | method | Hides the entry list and add button, showing "-- hidden --" instead. |
| `expandField()` | method | Shows the entry list and add button again. |
| `buildInterface(targetDiv, buildFieldInfo, readOnly, condensed)` | method | Builds the label, entry container, one initial entry, the "+ add" button (unless read-only) and the hide/show button. Overrides `ModelSubfield.buildInterface`. |
| `applyValidityStyles()` | method | Applies warning styles to the field and to every entry's subfields. Overrides `ModelSubfield.applyValidityStyles`. |
| `expandSubfields()` | method | Also expands every entry. Overrides `ModelSubfield.expandSubfields`. |
| `collapseSubfields()` | method | Also collapses every entry. Overrides `ModelSubfield.collapseSubfields`. |
| `destroy()` | method | Also drops the entry list and its elements. Overrides `ModelSubfield.destroy`. |
| `clearField()` | method | Removes all entries and warning styles. Overrides `ModelSubfield.clearField`. |
| `hasValidInput()` | method | True if there is at least one entry and every entry has valid input. Overrides `ModelSubfield.hasValidInput`. |
| `getFieldData()` | method | Array of each non-empty entry's data. Overrides `ModelSubfield.getFieldData`. |
| `getInputElement()` | method | The first entry input with a validation message, else the first entry input, or `null`. Overrides `ModelSubfield.getInputElement`. |
