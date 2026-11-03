[← Back to Frontend](index.md)

# modelData/asyncModelData.ts

Lazy references to model objects: related objects inside software and person
data are stored as `HssiDataAsync` handles holding only a model name and UUID,
whose full data is fetched through `ModelDataCache` on demand. Touch this when
a software or person field is added or changes its related model.

**Source:** [frontend/modelData/asyncModelData.ts](../../../frontend/modelData/asyncModelData.ts)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Classes](#classes)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `apiModel` | `"/api/models/"`: base URL of the model data API. |
| `apiSlugRowsAll` | `"/rows/all/"`: URL suffix for fetching all rows of a model. |

## Types

| Name | Description |
|---|---|
| `HssiDataAsync` | A handle to a model object (`id`, `model`) whose data can be fetched with `getData()`, with `hasData` and `loadedData` for already-loaded data. |
| `PersonDataAsync` | Person data with `affiliation` as async organization handles. |
| `SoftwareDataAsync` | Software data with every related-object field (authors, publisher, controlled list terms, version, etc.) as async handles. |

## Classes

### `HssiModelDataAsync`

The `HssiDataAsync` implementation: a model name and object UUID whose data is fetched on request.

| Member | Kind | Description |
|---|---|---|
| `constructor(model, id)` | constructor | Stores the model name and object UUID. |
| `model` | field | The model (database table) the data is fetched from. |
| `id` | property | UUID of the model object. |
| `data` | property (protected) | The object's data if loaded; typed generically for convenience, the actual shape depends on `model`. |
| `loadedData` | property | The data if it's loaded, without loading it. |
| `hasData` | property | Whether the object's data has been loaded. |
| `setData(data)` | method | Not implemented; logs an error. |
| `getData()` | method | Returns the object's data from `ModelDataCache`, fetching it if needed. |

## Functions

| Function | Description |
|---|---|
| `createAsyncSoftwareData(data)` | Converts `SoftwareData` to `SoftwareDataAsync`, replacing each related object (or UUID) with an `HssiModelDataAsync` for its model. |
| `createAsyncPersonData(data)` | Converts `PersonData` to `PersonDataAsync`, replacing affiliations with `HssiModelDataAsync` handles. |
