[← Back to Frontend](index.md)

# forms/fieldRequirement.ts

Requirement levels for form fields and the logic that highlights a field and
shows a note under it when it is invalid or left empty. Touch this when
changing how required, recommended, or invalid fields are flagged.

**Source:** [frontend/forms/fieldRequirement.ts](../../../frontend/forms/fieldRequirement.ts)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `requirementAttribute` | `"data-hssi-required"`: attribute holding an element's requirement level. |
| `requirementAttributeContainer` | `"data-hssi-required-container"`: attribute a widget's element gets holding its requirement level. |
| `invalidRecStyle` | `"invalid-recommended"`: CSS class for an empty or invalid recommended field. |
| `invalidManStyle` | `"invalid-mandatory"`: CSS class for an empty mandatory field, or any field with an invalid value. |
| `noteStyle` | `"note"`: CSS class for the warning note shown under a field. |

## Types

| Name | Description |
|---|---|
| `RequirementLevel` | Enum of how required a field is: `OPTIONAL` (0), `RECOMMENDED` (1), `MANDATORY` (2, blocks submission). |

## Classes

### `FieldRequirement`

Tracks a field's requirement level and applies or removes its warning styles and note as focus leaves or enters the field.

| Member | Kind | Description |
|---|---|---|
| `constructor(field, requirementLevel)` | constructor | Binds to the field's container, creates the hidden note element, and adds focus listeners. |
| `field` | field | The `ModelSubfield` this requirement applies to. |
| `containerElement` | field | Element that receives the warning styles and focus listeners. |
| `noteElement` | field | The warning note element placed after the styled element. |
| `level` | field | The field's `RequirementLevel`. |
| `removeStyles()` | method | Removes the warning styles and hides the note. |
| `getStyledElement()` | method | The element the `invalid-*` class is applied to. |
| `destroy()` | method | Removes the focus listeners, styles and note element, and unregisters the requirement. |
| `applyRequirementWarningStyles()` | method | Adds the warning style and note if the field's input isn't valid, otherwise removes them. |
| `applyStylesForAll()` | static method | Runs `applyRequirementWarningStyles` on every registered requirement. |
