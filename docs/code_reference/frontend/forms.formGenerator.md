[← Back to Frontend](index.md)

# forms/formGenerator.ts

Builds the submission/edit form from the backend's model field structures,
validates it, and posts its data as JSON. Touch this when changing how the
form is laid out, validated, autofilled, or submitted.

**Source:** [frontend/forms/formGenerator.ts](../../../frontend/forms/formGenerator.ts)

## Contents

- [Constants](#constants)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `formRowStyle` | `"form-row"`: CSS class for the container of each form field row. |
| `formSeparatorStyle` | `"form-separator"`: CSS class for a (collapsible) section of fields. |

## Classes

### `FormGenerator`

Singleton that generates the form on the page and handles its submission; the class itself is exposed on `window` as `FormGenerator`.

| Member | Kind | Description |
|---|---|---|
| `autofilledFromDatacite` | field | Whether the form has already been autofilled from DataCite; set on edit forms to suppress the autofill prompt. |
| `autofilledFromRepo` | field | Whether the form has already been autofilled from the code repository; set on edit forms to suppress the autofill prompt. |
| `getJsonData()` | method | The form's data as a JSON object keyed by root field name. |
| `fieldMap` | class attribute | Map from form field names to model field names, loaded with the structure data from `/api/models/structures/`. |
| `generateForm(fields)` | static method | Fetches structure data if needed and builds the form inside the page's generated-form element, using the given fields or the structure names in the page's JSON data. |
| `fillForm(data, overwrite_values)` | static method | Fills root fields from a `{name: value}` object, skipping fields that already have valid input unless `overwrite_values`. Exposed on `window` as `fillForm`. |
| `getStructureData()` | static method | The loaded model structure data. |
| `clearForm()` | static method | Clears every field, collapses the form and resets both autofilled flags. |
| `collapseFormFields()` | static method | Collapses every field's subfields and closes the form sections. Exposed on `window` as `collapseGeneratedForm`. |
| `expandFormFields()` | static method | Opens the form sections and expands every field's subfields. Exposed on `window` as `expandGeneratedForm`. |
| `clearFormConfirm()` | static method | Asks the user for confirmation, then clears the form. Exposed on `window` as `clearGeneratedForm`. |
| `markAutofilledDatacite()` | static method | Sets `autofilledFromDatacite` on the form. |
| `markAutofilledRepo()` | static method | Sets `autofilledFromRepo` on the form. |
| `isAutofilledDatacite()` | static method | Whether the form has been autofilled from DataCite. |
| `isAutofilledRepo()` | static method | Whether the form has been autofilled from the code repository. |
| `debugAutofill()` | static method | Fills every field and subfield with test values (two entries per multi-field). Exposed on `window` as `debugAutofill`. |
| `awaitFormGeneration()` | static method | Resolves once the form has been generated, polling every 100 ms. Exposed on `window` as `awaitFormGeneration`. |
