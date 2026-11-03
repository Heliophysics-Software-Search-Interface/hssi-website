[← Back to Frontend](index.md)

# filters/search.ts

The search bar: runs queries against `/api/search/`, shows matching results
(limited to those passing the active filters) in the main resource view, and
keeps the query in the `q` URL parameter. On page load it wires up the search
bar, the search button and the field-search help chips. Touch this when
changing search behavior or the search API call.

**Source:** [frontend/filters/search.ts](../../../frontend/filters/search.ts)

## Contents

- [Constants](#constants)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `idSearchbar` | `"searchbar"`: ID of the search input element. |
| `idSearchButton` | `"searchbar-btn"`: ID of the search button. |
| `searchParamQuery` | `"q"`: URL parameter holding the search query. |
| `searchModeQuery` | `"mode"`: search API parameter selecting the result format. |

## Functions

| Function | Description |
|---|---|
| `applyEnteredQuery()` | Reapplies the search from the URL to the main resource view, or shows all filtered items if there is none. |
| `searchForQuery(query, pushHistory)` | Searches for the query, shows the matching filtered results in the main view, and by default records the query in browser history and reports it to analytics. |
