[← Back to Frontend](index.md)

# modelData/modelDataCache.ts

The client-side cache of model data fetched from `/api/models/`. There is one
cache per model; single-object requests are batched into chunked `?ids=`
requests, and software and person data are stored in their async form. Touch
this when changing how the frontend fetches or caches model data.

**Source:** [frontend/modelData/modelDataCache.ts](../../../frontend/modelData/modelDataCache.ts)

## Contents

- [Classes](#classes)

---

## Classes

### `ModelDataCache`

A per-model cache of fetched model object data, keyed by UUID. Exposed on `window`.

| Member | Kind | Description |
|---|---|---|
| `getCache(model)` | static method | The cache for a model, created on first use; `"Software"` shares the `"VerifiedSoftware"` cache. |
| `getModelDataAll(model)` | static method | All objects of a model, fetching them all first if not already done. |
| `getModelData(model, uid)` | static method | The object, or array of objects, with the given UUID(s). |
| `fetchPage(model, offset, limit)` | static method | One page of a model's objects and the total count, served from the cache if all data is already loaded. |
| `hasFetchedAllData` | property | Whether all of the model's objects have been fetched. |
| `model` | property | The model the cache holds. |
| `fetchAllData()` | method | Fetches all objects of the model, sharing any fetch already in progress. |
| `getMultiData(uids)` | method | The objects with the given UUIDs; throws if any is not a valid UUIDv4. |
| `getData(uid)` | method | The object with the given UUID; uncached requests are queued and fetched together after a 100 ms delay in chunks of 50. Throws if the UUID is not a valid UUIDv4. |
| `expandUidFromTruncated(truncatedUid)` | method | The first loaded UUID starting with the given string, or `null`. |
