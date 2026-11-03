[← Back to Frontend](index.md)

# forms/widgets/autofillDatacite.ts

A DOI widget that offers to autofill the whole form from DataCite and Zenodo
metadata, then from the code repository if one is found. Touch this when
changing how DOI metadata maps onto form fields.

**Source:** [frontend/forms/widgets/autofillDatacite.ts](../../../frontend/forms/widgets/autofillDatacite.ts)

## Contents

- [Classes](#classes)

---

## Classes

### `AutofillDataciteWidget`

DOI input that, once a valid DOI is entered and focus leaves the field, asks to autofill the form from it. **Extends:** `DataciteDoiWidget`

| Member | Kind | Description |
|---|---|---|
| `autofillButton` | field (protected) | Unused; never assigned. |
| `initialize(readOnly)` | method | Also adds the focus-out listener that prompts for autofill if the form hasn't been autofilled from DataCite yet. Overrides `Widget.initialize`. |
| `getApiDataFromDoi(doiUrl)` | static method | Fetches the DataCite record for a DOI or DOI URL. |
| `getZenodoApiDataFromDoi(doiUrl)` | static method | Fetches the Zenodo record for a Zenodo DOI. |
| `autofillFromApiData(data, zenodoData)` | static method | Maps DataCite and Zenodo data to `SubmissionFormData` and returns it. Also fills the form (overwriting values) and marks it autofilled from DataCite. |
