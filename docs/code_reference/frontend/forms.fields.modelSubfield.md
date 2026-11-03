[← Back to Frontend](index.md)

# forms/fields/modelSubfield.ts

The form-side representation of a single model field: it builds the field's
label, widget, and lazily-built subfields, and reads and fills its data.
Touch this when changing how a form field renders, validates, or serializes
its value.

**Source:** [frontend/forms/fields/modelSubfield.ts](../../../frontend/forms/fields/modelSubfield.ts)

## Contents

- [Constants](#constants)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `labelStyle` | `"custom-label"`: CSS class for a field's label. |
| `explanationTextStyle` | `"explanation-text"`: CSS class for the help text shown below a label. |
| `requiredIndicatorStyle` | `"required-indicator"`: CSS class for the `*` shown on mandatory fields. |

## Classes

### `ModelSubfield`

A single field in a db model, plus the information needed to render it and interact with it in the form.

| Member | Kind | Description |
|---|---|---|
| `constructor(name, rowName, type, properties, parentField)` | constructor (protected) | Stores the field's definition and forwards value-change events up to the parent field. |
| `name` | field | The field's name, used as its key in submitted data. |
| `rowName` | field | Alternative name the field also matches when filling data. |
| `type` | field | The `ModelFieldStructure` describing the field's widget and subfields. |
| `properties` | field | The field's `PropertyContainer` (label, tooltips, requirement level, widget properties, …). |
| `widget` | field | The field's `Widget`, once built. |
| `containerElement` | field | Root element of the field's interface. |
| `requirement` | field | The field's `FieldRequirement`, once built. |
| `controlContainerElement` | field (protected) | Element holding the widget and subfield container. |
| `labelElement` | field (protected) | The field's label element. |
| `readOnly` | field (protected) | Whether the field was built read-only. |
| `condensed` | field (protected) | Whether the field was built condensed; passed on to subfields. |
| `parentField` | field (protected) | The field this one is a subfield of, or `null`. |
| `parent` | property | The parent field, or `null`. |
| `multi` | property | Whether this is a multi-entry field; `false` here. |
| `onValueChanged` | event | Fires when the field's value changes; also triggers the parent's `onChildValueChanged`. |
| `onChildValueChanged` | event | Fires when a descendant field's value changes; propagates up the parent chain. |
| `buildFieldInfo()` | method (protected) | Builds the label, required indicator, info tooltip and help text. |
| `buildWidget(readOnly)` | method (protected) | Creates the widget for the field's type, merges in `widgetProperties`, and initializes it. |
| `buildInterface(targetDiv, buildFieldInfo, readOnly, condensed)` | method | Builds the field's UI inside the target element and creates its `FieldRequirement`. |
| `applyValidityStyles()` | method | Applies requirement warning styles to the field and its built subfields, recursively. |
| `clearField()` | method | Clears the value, clears and collapses all subfields, and removes warning styles. |
| `fillField(data, notify, eraseIfNull)` | method | Fills the field from a value, nested object, array (multi-fields only), or option ID; a UUID on a `ModelBox` field fetches that row's data first. |
| `meetsRequirementLevel()` | method | True if the field is optional or has valid input. |
| `hasValidInput()` | method | True if the field has a value that passes the input's validity check; a `ModelBox` that disallows new entries also needs a selected option. |
| `hasValidFormatValue()` | method | True if the input element's value passes its validity check, empty or not. |
| `expandSubfields()` | method | Builds the subfields if needed and opens the subfield container. |
| `collapseSubfields()` | method | Closes the subfield container. |
| `showSubfieldContainer()` | method | Shows the subfield container and its expand button. |
| `hideSubfieldContianer()` | method | Hides the subfield container and destroys its subfields. |
| `destroy()` | method | Destroys the subfields, widget and requirement, and removes the field from the page. |
| `clearSubfields()` | method | Destroys all built subfields. |
| `hasSubfields()` | method | True if the field's type has subfields, so its data includes theirs. |
| `subfieldsExpanded()` | method | True if the subfield container is open and not hidden. |
| `subfieldsHidden()` | method | True if there is no subfield container or it's hidden. |
| `getSubfields()` | method | The field's subfields, building them first if needed. |
| `getInputElement()` | method | The widget's input element, or `null`. |
| `setValue(value, notify)` | method | Sets the widget's value. |
| `subfieldsAreBuilt()` | method | True once the subfields have been built (i.e. the container was ever expanded). |
| `getFieldData()` | method | The field's input value, or an object of it plus each subfield's data if it has subfields. |
| `isBuilt()` | method | True once the field's widget has been built. |
| `getSubfieldsRecursive(subfield, onlyRelevant, returnVal)` | static method | All built descendant subfields; with `onlyRelevant`, only recurses into mandatory subfields with valid input. |
| `parse(data)` | static method | Creates a `ModelSubfield` or `ModelMultiSubfield` from a `SerializedSubfield`, resolving its type by name. |
