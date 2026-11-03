[← Back to Backend](index.md)

# admin/fetch_vocab.py

Fetches controlled vocabulary terms from the HSSI-vocab repository and the
heliophysics.net API and turns them into model entries. Touch this when a
vocabulary source URL changes or a new vocabulary is added.

**Source:** [django/website/admin/fetch_vocab.py](../../../django/website/admin/fetch_vocab.py)

## Contents

- [Constants](#constants)
- [Classes](#classes)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `URL_REPOSTATUS` | JSON-LD ontology URL for repostatus.org development statuses. |
| `URL_HSSIBASE` | Base raw-file URL of the HSSI-vocab GitHub repository. |
| `URL_JSONBASE` | `jsonld/` folder of the HSSI-vocab repository. |
| `URL_TTLBASE` | `ttl/` folder of the HSSI-vocab repository. |
| `URL_CPUARCHITECTURES` | CPU architecture vocabulary URL. |
| `URL_DATAINPUTS` | Data source vocabulary URL. |
| `URL_LICENSES` | License vocabulary URL. |
| `URL_OPERATINGSYSTEMS` | Operating system vocabulary URL. |
| `URL_SUPPORTEDFILEFORMATS` | File format vocabulary URL. |
| `URL_PROGRAMMINGLANGUAGES` | Programming language vocabulary URL. |
| `URL_FUNCTIONCATEGORIES` | Software functionality TTL URL (v0.3). |
| `URL_HELIOPHYSICS_API` | Base URL of the heliophysics.net API. |
| `URL_REGIONS_JSON` | Regions endpoint of the heliophysics.net API. |
| `URL_HELIOKNOWBASE` | Base URL of the Helio-KNOW data models. |
| `URL_REGIONS_TTL` | Helio-KNOW region TTL URL (no longer used for fetching). |
| `URL_PHENOMENA` | Helio-KNOW phenomenon TTL URL (not yet used). |
| `MODEL_URL_MAP` | Model class name to vocabulary URL, for the vocabularies `fetch_vocab` refreshes. |
| `SPASE_URL` | Base URL used to build SPASE identifier URLs. |
| `HELIODATA_MISSION_URL` | Base URL of HelioData mission landing pages. |
| `HELIODATA_LOAD_MISSION_URL` | HelioData backend endpoint returning mission JSON (with `datasetCount`) or 404, used to check whether a mission page is useful. |
| `HELIOPHYS_API_URL` | Base URL of the heliophysics.net API. |
| `HELIOPHYS_PROP_NAME` | `"long_name"`: API property for an item's long name. |
| `HELIOPHYS_PROP_NAME_2` | `"short_name"`: API property for an item's short name. |
| `HELIOPHYS_PROP_DEFINITION` | `"description"`: API property for an item's description. |
| `HELIOPHYS_PROP_SPASEID` | `"spase_id"`: API property for an item's SPASE ID. |

## Classes

### `DataListConcept`

A vocabulary term parsed from fetched data, before it becomes a model entry.

| Member | Kind | Description |
|---|---|---|
| `pref_label` | field | The term's name. |
| `definition` | field | The term's definition (a URL for licenses). |
| `identifier` | field | The term's identifier URL. |
| `to_model_entry(model)` | method | Creates and saves an entry of the model from this term; for `License` the definition is saved as the URL. |
| `from_concept_serialized(concepts)` | class method | Builds terms from JSON-LD concept dicts (`prefLabel`, `definition` or `licenseUrl`, `@id`), skipping empty ones. |

## Functions

| Function | Description |
|---|---|
| `get_data(url)` | Fetches JSON from a URL, replacing curly quotes and retrying if it doesn't parse. |
| `heliodata_mission_has_datasets(uid)` | Whether HelioData has a mission page with datasets: `True` if `datasetCount` > 0, `False` if missing or empty, `None` if the probe failed. |
| `ttl_spl_str(data_str)` | The part of a string after the last `#`, to strip full URLs from TTL JSON export keys. |
| `get_concepts_generalized(data, key_preflabel, key_ident, key_definition)` | Builds `DataListConcept`s from a list of dicts using the given keys for name, identifier and definition. |
| `get_concepts(data)` | The `Concept`-typed items of JSON-LD data, looking inside `@graph` if present. |
| `parse_jsonld(target_type, data)` | Creates and saves an empty-named entry of the model; ignores `data`. |
| `link_concept_children(model, concept_data, parent_field_name)` | Links each entry of a graph model as a child of the entries listed in its concept's parent field (`broader` by default). |
| `fetch_heliophysnet_list(api_slug)` | Fetches a list endpoint of the heliophysics.net API. |
| `fetch_heliophysnet_detail(api_slug, uid)` | Fetches one item from the heliophysics.net API. |
| `fetch_heliophysnet_vocab(model, api_slug)` | Creates or updates a model entry for every item at a heliophysics.net API list (e.g. `"observatories"`), keyed by SPASE URL. For `InstrumentObservatory` it also sets the type, the HelioData landing URL, and splits off a parenthesized abbreviation. |
