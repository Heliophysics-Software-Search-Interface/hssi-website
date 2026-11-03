[← Back to Frontend](index.md)

# forms/widgets/modelBox.ts

A text input with a filterable dropdown of choices, either embedded in the
page or fetched from a backend model; selecting a choice fills the parent
field's subfields from that model row. Touch this when changing
controlled-vocabulary or related-model inputs on the form.

**Source:** [frontend/forms/widgets/modelBox.ts](../../../frontend/forms/widgets/modelBox.ts)

## Contents

- [Types](#types)
- [Classes](#classes)

---

## Types

| Name | Description |
|---|---|
| `ModelBoxProperties` | `BaseProperties` plus `targetModel` (model to load choices from), `modelFilter` (query string for the choices request), `dropdownButton`, `allowNewEntries` and `licenseModelbox`. |

## Classes

### `ModelBox`

Widget with a text input and a shared, keyboard-navigable dropdown of options filtered by keyword as the user types. **Extends:** `Widget`

| Member | Kind | Description |
|---|---|---|
| `options` | field | The available options (`id`, `name`, `keywords`, optional `tooltip` and `identifier`), or `null` until loaded. |
| `properties` | field | The widget's `ModelBoxProperties`. Overrides `Widget.properties`. |
| `rowFetchAbort` | field | Abort controller for the in-flight model row fetch, or `null`. |
| `fetchModelRow(uid)` | method (protected) | Fetches a row of `targetModel` and fills the parent field's subfields from it, matched via `FormGenerator.fieldMap`; aborts any previous fetch. |
| `selectOption(option)` | method | Puts the option (default: the highlighted one) in the input, stores it as the input's data and fetches its model row; `null` clears the stored option. |
| `setSelectedOptionLI(option)` | method (protected) | Highlights an option in the dropdown and scrolls it into view. |
| `collectData()` | method (protected) | Also loads options from a `json-options` `<script>` in the element. Overrides `Widget.collectData`. |
| `initialize(readOnly)` | method | Also builds the input, dropdown options and listeners. Overrides `Widget.initialize`. |
| `setValue(value, notify)` | method | Sets the input to the best-matching option by keyword or name similarity; with no match, keeps the raw value only if `allowNewEntries`. Loads options first if needed. Overrides `Widget.setValue`. |
| `showDropdown(filter)` | method | Shows the shared dropdown under this input with this widget's options, filtered by the input value unless `filter` is false. |
| `getInputElement()` | method | The text input. Overrides `Widget.getInputElement`. |
| `getInputValue()` | method | The selected option's ID if one is selected, otherwise the trimmed text. Overrides `Widget.getInputValue`. |
| `destroy()` | method | Also removes its listeners from the parent field. Overrides `Widget.destroy`. |
| `optionMap` | class attribute (protected) | Cache of fetched options by model name (and filter). |
| `getDropdownElement()` | static method (protected) | The shared dropdown element, created on first use. |
| `getTooltipElement()` | static method (protected) | The shared tooltip element, created on first use. |
| `hideDropdown()` | static method | Hides the shared dropdown and stops repositioning it. |
| `showTooltip(xPos, yPos, text)` | static method | Not implemented; does nothing. |
