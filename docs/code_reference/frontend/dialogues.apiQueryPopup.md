[← Back to Frontend](index.md)

# dialogues/apiQueryPopup.ts

The abstract base for popups that search an external API (ORCID, ROR,
DataCite) and let the user pick a result to fill into a form field. Touch
this when writing a new external-lookup popup or changing how results are
listed, filtered or selected.

**Source:** [frontend/dialogues/apiQueryPopup.ts](../../../frontend/dialogues/apiQueryPopup.ts)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `faSearchIcon` | Font Awesome search icon HTML. |
| `propResultFilters` | `"resultFilters"`: widget property naming the result filters to pass to `withFilters`. |

## Types

| Name | Description |
|---|---|
| `ApiQueryResult` | One search result: its JSON data, a display element, and its ID URL. |

## Classes

### `ApiQueryPopup`

A popup that searches an external API and lets the user select a result for a target field. **Extends:** `PopupDialogue` **Abstract**

| Member | Kind | Description |
|---|---|---|
| `constructor()` | constructor (protected) | Calls the `PopupDialogue` constructor. |
| `targetField` | field (protected) | The `ModelSubfield` or input element a selected result is written to. |
| `formElement` | field (protected) | The query form. |
| `queryInputElement` | field (protected) | The query text input. |
| `resultBox` | field (protected) | Container for the result rows. |
| `filters` | field (protected) | Names of the result filters to apply; cleared when the popup hides. |
| `description` | property (protected) | Optional text shown above the form; empty by default. |
| `contentType` | property (protected) | Request `Content-Type`; `"application/json"` by default. |
| `endpoint` | property (protected, abstract) | The API endpoint. |
| `title` | property | Overrides to return `"Find Item"`. |
| `createContent()` | method (protected) | Overrides to add the description, query form and result box, focusing the input and clearing results on show and resetting the query and filters on hide. |
| `createQueryForm()` | method (protected) | Creates the query form with its input and search button; submitting runs `submitQuery`. |
| `createQueryInput()` | method (protected) | Creates the query text input. |
| `createResultBox()` | method (protected) | Creates the result container. |
| `getQueryUrl(query)` | method (protected, abstract) | The request URL for a query. |
| `getRequestHeaders()` | method (protected) | Request headers; sets `Content-Type` from `contentType`. |
| `getQueryResults(query)` | method (protected) | Fetches the query URL and returns the JSON response; throws if a request is already in progress or the response is not OK. |
| `handleQueryResults(results)` | method (protected, abstract) | Turns the API response into result rows. |
| `addResultRow(result)` | method (protected) | Adds a result row with a link and a Select button that writes the result to the target field and closes the popup. |
| `filterResults(results_in)` | method (protected) | Applies each filter in `filters` by calling the matching `resultsFiltered_<name>` method. |
| `resultsFiltered_software(results_in)` | method (protected) | Keeps DataCite results of type `Software`. |
| `resultsFiltered_notsoftware(results_in)` | method (protected) | Removes DataCite results of type `Software`. |
| `resultsFiltered_dataset(results_in)` | method (protected) | Keeps DataCite results of type `Dataset`. |
| `resultsFiltered_notdataset(results_in)` | method (protected) | Removes DataCite results of type `Dataset`. |
| `resultsFiltered_concept(results_in)` | method (protected) | Removes DataCite results that are a version of another record (`IsVersionOf`), keeping concept records. |
| `submitQuery(query)` | method | Clears the results, fetches results for the query and displays them; ignored while a request is in progress. |
| `setTarget(field, useParentField)` | method | Sets the field a selected result is written to; by default also searches the parent field's current value. Returns the popup. |
| `withQuery(query)` | method | Puts the query in the input and searches it if non-empty. Returns the popup. |
| `withFilters(filters)` | method | Adds result filters by name (e.g. `software`, `concept`). Returns the popup. |
| `clearResults()` | method | Removes all result rows. |
