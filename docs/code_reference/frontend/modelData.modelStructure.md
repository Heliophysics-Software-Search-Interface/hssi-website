[← Back to Frontend](index.md)

# modelData/modelStructure.ts

TypeScript types for the model names and JSON data shapes returned by the
backend model API. Touch this when a backend model or one of its serialized
fields is added or renamed.

**Source:** [frontend/modelData/modelStructure.ts](../../../frontend/modelData/modelStructure.ts)

## Contents

- [Types](#types)

---

## Types

| Name | Description |
|---|---|
| `ModelName` | Union of the backend model names that data can be fetched for, e.g. `"Software"`, `"VerifiedSoftware"`, `"FunctionCategory"`, `"Person"`. |
| `HSSIModelData` | Base data for every model object: its UUID `id`. |
| `ControlledListData` | Controlled list term data: display `name` and URL `identifier` (DOI, ROR, ORCID, etc.). |
| `GraphListData` | Controlled list term data with `children` and optional `parents` UUID lists. |
| `KeywordData` | Keyword data; same shape as `ControlledListData`. |
| `FunctionalityData` | Function category data: graph list data plus optional `abbreviation`, `backgroundColor` and `textColor`. |
| `VersionData` | Software version data: `number` and `release_date`. |
| `OrganizationData` | Organization data: `name` and optional ROR `identifier`. |
| `PersonData` | Person data: `given_name`, `family_name`, optional ORCID `identifier`, and `affiliation` organizations. |
| `SoftwareData` | Full software entry data with related objects nested as their data types. |
