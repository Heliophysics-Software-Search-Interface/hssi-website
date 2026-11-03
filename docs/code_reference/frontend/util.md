[← Back to Frontend](index.md)

# util.ts

Shared helpers used across the frontend: JSON types, API URLs, timed fetch,
identifier parsing, software/edit data fetching, the edit-link request flow,
and Google Analytics events. Touch this when adding a general-purpose helper
or changing one of the API URLs it holds.

**Source:** [frontend/util.ts](../../../frontend/util.ts)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `uuid4Regex` | Case-insensitive regex matching a UUIDv4 string. |
| `softwareApiUrl` | `"/api/models/Software/rows/"`: URL prefix for fetching one software entry's data. |
| `modelApiUrl` | `"/api/view/"`: URL prefix for a software entry's API view JSON. |
| `editApiUrl` | `"/sapi/software_edit_data/"`: URL prefix for a submission's edit data, including submitter data. |
| `requestEditUrl` | `"/request_edit/"`: URL prefix for requesting an edit-link email. |
| `maskedEmailsApiUrl` | `"/api/masked_emails/"`: URL prefix for a submission's masked submitter emails. |
| `csrfTokenName` | `"csrf-token"`: name of the `<meta>` tag holding the CSRF token. |

## Types

| Name | Description |
|---|---|
| `JSONValue` | Any JSON value (typed loosely, includes `any`). |
| `JSONObject` | A JSON object with string keys. |
| `JSONArray` | A JSON array, optionally typed by element. |
| `JSONArrayData` | A JSON object with a `data` array, as returned by the model rows API. |
| `NestedKeys` | Like `keyof`, but also includes the keys of nested object types. |

## Functions

| Function | Description |
|---|---|
| `getCsrfTokenValue()` | The page's CSRF token from its `csrf-token` `<meta>` tag. |
| `trackEvent(name, params, onComplete)` | Sends a custom Google Analytics event if the GA tag is present (production only); `onComplete` runs exactly once, after GA processes the event or a 2-second fallback. |
| `deepMerge(target, source, inPlace)` | Recursively merges `source` into `target`, cloning both unless `inPlace` is true. |
| `fetchTimeout(input, init, timeout)` | `fetch` that aborts if the request takes longer than `timeout` seconds (default 10). |
| `extractDoi(url)` | The DOI part of a `doi.org` URL, or the input unchanged. |
| `extractOrcId(url)` | The ORCID iD part of an `orcid.org` URL, or the input unchanged. |
| `getStringSimilarity(a, b)` | Similarity of two strings from 0 (completely different) to 1 (identical), based on edit distance. |
| `getSoftwareData(uid)` | Fetches a software entry's data from `softwareApiUrl`. Exposed on `window`. |
| `getEditData(uid)` | Fetches a submission's data from the edit data API, which includes submitter data when the edit link is valid. |
| `getSoftwareFormData(uid)` | Fetches a software entry's data for `FormGenerator.fillForm`. Exposed on `window`. |
| `getSoftwareEditFormData(uid)` | Fetches a submission's edit data and reshapes it for `FormGenerator.fillForm`, filling in submitter name/emails and keeping only the latest version. Exposed on `window`. |
| `getSimpleSoftwareFormData(uid)` | Fetches a software entry's API view JSON. Exposed on `window`. |
| `requestEditSubmission(uid)` | Shows the submission's masked email(s), prompts for the submitter's email, and POSTs it to request an edit-link email, reporting the result in a dialog. Exposed on `window`. |
| `isUuid4(uid)` | Whether the string is a UUIDv4. |
| `appendPromisedElement(parentElem, childPromise)` | Appends the child element to the parent once its promise resolves, logging any error. |
| `curateEditFormInit()` | Fetches the edit data for the `uid` URL parameter and fills the form with it, redirecting home if the link is invalid. Not exported; exposed on `window`. |
