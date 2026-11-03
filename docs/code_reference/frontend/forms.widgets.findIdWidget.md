[← Back to Frontend](index.md)

# forms/widgets/findIdWidget.ts

URL inputs for persistent identifiers (ROR, ORCID, DataCite DOI) with a
"find" button that opens a search popup. Touch this when adding an
identifier type or changing how identifier lookups fill the form.

**Source:** [frontend/forms/widgets/findIdWidget.ts](../../../frontend/forms/widgets/findIdWidget.ts)

## Contents

- [Constants](#constants)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `findButtonStyle` | `"button-find"`: CSS class for the find button. |
| `styleEmphasisAnimation` | `"emphasis-anim"`: CSS class that animates the find button to draw attention to it. |

## Classes

### `FindIdWidget`

Base class for URL inputs with a "find" button that opens an identifier search popup. **Extends:** `UrlWidget` **Abstract**

| Member | Kind | Description |
|---|---|---|
| `findButton` | field (protected) | The find button. |
| `findButtonText` | property (protected) | Find button label; `"find"`. |
| `placeholderExample` | property (protected) | Example identifier shown in the input placeholder; empty by default. |
| `onFindButtonPressed()` | method (protected, abstract) | Called when the find button is clicked; opens the search popup. |
| `onDataSelected(data)` | method | Called with the selected result's data when the user picks one in the search popup; does nothing by default. |
| `buildFindButton()` | method (protected) | Builds the find button beside the input; it animates the first time the empty input is focused. |
| `initialize(readOnly)` | method | Also builds the find button (unless read-only) and sets the placeholder. Overrides `Widget.initialize`. |

### `RorWidget`

Input for a ROR organization identifier. **Extends:** `FindIdWidget`

| Member | Kind | Description |
|---|---|---|
| `placeholderExample` | property (protected) | `"https://ror.org/00000xxxx"`. Overrides `FindIdWidget.placeholderExample`. |
| `onFindButtonPressed()` | method (protected) | Opens the `RorFinder` popup for this field. Overrides `FindIdWidget.onFindButtonPressed`. |

### `OrcidWidget`

Input for an ORCID person identifier. **Extends:** `FindIdWidget`

| Member | Kind | Description |
|---|---|---|
| `placeholderExample` | property (protected) | `"https://orcid.org/0000-0000-0000-0000"`. Overrides `FindIdWidget.placeholderExample`. |
| `onFindButtonPressed()` | method (protected) | Opens the `OrcidFinder` popup for this field. Overrides `FindIdWidget.onFindButtonPressed`. |
| `onDataSelected(data)` | method | Fills the last sibling multi-field (assumed to be affiliations) with the ORCID record's institutions, unless it already has valid input. Overrides `FindIdWidget.onDataSelected`. |

### `DataciteDoiWidget`

Input for a DataCite DOI. **Extends:** `FindIdWidget`

| Member | Kind | Description |
|---|---|---|
| `placeholderExample` | property (protected) | `"https://doi.org/10.5281/zenodo.00000000"`. Overrides `FindIdWidget.placeholderExample`. |
| `onFindButtonPressed()` | method (protected) | Opens the `DoiDataciteFinder` popup for this field. Overrides `FindIdWidget.onFindButtonPressed`. |

### `AuthorIdentifierWidget`

Author identifier input with an "Is Organization" checkbox that switches between ORCID and ROR mode. **Extends:** `FindIdWidget`

| Member | Kind | Description |
|---|---|---|
| `placeholderExample` | property (protected) | ROR example in organization mode, ORCID example otherwise. Overrides `FindIdWidget.placeholderExample`. |
| `onFindButtonPressed()` | method (protected) | Opens the `RorFinder` popup in organization mode, otherwise the `OrcidFinder` popup. Overrides `FindIdWidget.onFindButtonPressed`. |
| `onDataSelected(data)` | method | In ORCID mode, fills the last sibling multi-field (assumed to be affiliations) with the record's institutions unless it already has valid input. Overrides `FindIdWidget.onDataSelected`. |
| `setValue(value, notify)` | method | Also switches to ROR or ORCID mode to match a ROR or ORCID URL. Overrides `Widget.setValue`. |
| `initialize(readOnly)` | method | Also builds the checkbox and switches mode as the user types a ROR or ORCID URL; in organization mode, non-ROR values are marked invalid. Overrides `Widget.initialize`. |
