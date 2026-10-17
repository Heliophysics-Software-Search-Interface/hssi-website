# Software Catalog API

Read-only endpoints for listing, fetching, and searching publicly visible
software records. All four endpoints below are fully public — no
authentication required. See [Overview](Overview.md) for the camelCase and
"visible software only" conventions that apply throughout.

## `GET /api/list/software/`

A lightweight directory of every publicly visible software record: just
`id`, `name`, and `slug`. Use this to resolve a name to the slug/UUID the
detail endpoints need, or to look a record up by its repo URL.

**Query parameters**

| Param | Required | Description |
|---|---|---|
| `repo_url` | no | Exact (case-insensitive) match against the record's `codeRepositoryUrl`. |
| `view` | no | Only legal value is `jsonld`. When set, returns the full JSON-LD document for every visible record instead of the lightweight `id`/`name`/`slug` entries. |

**Errors:** `400` if `view` is set to anything other than `jsonld`.

### Simple example

```bash
curl https://hssi.hsdcloud.org/api/list/software/
```

```json
{
  "data": [
    {"id": "1b6ddaa6-6885-46b3-b59a-ea119e61bd74", "name": "PyMap3D", "slug": "pymap3d"},
    {"id": "a1f8de3a-1bde-4995-94e5-e88e841a62a6", "name": "SpacePy", "slug": "spacepy"}
  ]
}
```

### Complex example — resolve a GitHub repo to a software ID

This is the lookup pattern an automated updater would use: given a repo URL
it just pushed to, find the matching HSSI record before PATCHing it.

```bash
curl "https://hssi.hsdcloud.org/api/list/software/?repo_url=https://github.com/scivision/pymap3d"
```

```json
{"data": [{"id": "1b6ddaa6-6885-46b3-b59a-ea119e61bd74", "name": "PyMap3D", "slug": "pymap3d"}]}
```

### Complex example — bulk JSON-LD harvest

Combine `view=jsonld` with `repo_url` to pull one record's full metadata, or
drop `repo_url` to harvest the entire catalog's JSON-LD in a single request
(this is how external harvesters are expected to pull all of HSSI's metadata
rather than making one request per record):

```bash
curl "https://hssi.hsdcloud.org/api/list/software/?view=jsonld"
```

```json
{
  "data": [
    {
      "@context": {"...": "..."},
      "@id": "https://hssi.hsdcloud.org/software/pymap3d/",
      "@type": ["SoftwareSourceCode", "SoftwareApplication"],
      "name": "PyMap3D",
      "codeRepository": "https://github.com/scivision/pymap3d",
      "...": "see the full field list under GET /api/view/software/{id}/?view=jsonld below"
    }
  ]
}
```

---

## `GET /api/view/software/{id}/`

Fetch a single record. `{id}` is either the record's UUID or its slug (not
its display name — see [Overview](Overview.md)).

Default response (no `?view=`) is the **user-friendly view**: related
objects (authors, publisher, license, etc.) are resolved into flat nested
objects instead of raw foreign-key IDs, and empty/falsy fields are omitted.

**Query parameters**

| Param | Required | Description |
|---|---|---|
| `view` | no | `user` (default for this endpoint), `standard` (raw field-for-field DRF representation, FKs as IDs), or `jsonld` (full schema.org/CodeMeta document). Case-insensitive. |

**Errors:**
- `404 {"detail": "Not found."}` — no record with that UUID/slug, or the
  record exists but isn't publicly visible yet.
- `400 {"view": "Unsupported view '<v>'. Valid values: standard, user, jsonld."}`
  for any other `view` value.

### Simple example — default (user) view

```bash
curl https://hssi.hsdcloud.org/api/view/software/pymap3d/
```

```json
{
  "id": "1b6ddaa6-6885-46b3-b59a-ea119e61bd74",
  "softwareName": "PyMap3D",
  "description": "Pure-Python coordinate conversions for geospace ecosystems.",
  "codeRepositoryUrl": "https://github.com/scivision/pymap3d",
  "license": {"id": "...", "name": "BSD-2-Clause"},
  "authors": [{"id": "...", "givenName": "Michael", "familyName": "Hirsch"}]
}
```

### Complex example — JSON-LD view, by UUID

The JSON-LD representation is the largest and most complete shape this
endpoint returns. Selected fields (all omitted when empty):

| Field | Contents |
|---|---|
| `@id`, `@type`, `@context` | `["SoftwareSourceCode", "SoftwareApplication"]`, schema.org + codemeta/prov/sosa/dcat contexts |
| `name`, `description`, `url`, `codeRepository` | core identity fields |
| `author` | `{"@list": [...]}` of Person/Organization JSON-LD |
| `identifier` | `PropertyValue` list, including one pointing back at HSSI's own canonical URL for the record |
| `keywords` | combined data sources, formats, phenomena, functionality, and free-text keywords, as `DefinedTerm`s |
| `license`, `programmingLanguage`, `operatingSystem`, `processorRequirements` | environment/requirements metadata |
| `funder`, `funding` | funder plus `MonetaryGrant` entries built from any recorded award |
| `publisher` | only included if it has a doi.org/ror.org/orcid.org/zenodo.org identifier |
| `softwareVersion` / `version` | from the most recent `SoftwareVersion` by release date |
| `mentions` | related instruments, observatories, publications, datasets, and related/interoperable software |
| `subjectOf` | a `dcat:CatalogRecord` describing the HSSI metadata record itself — `@id` is this endpoint's own JSON-LD URL, `dateModified` is the record's last-modified date (or earliest submission date if never modified) |
| `offers` | static `{"@type": "Offer", "price": 0, "priceCurrency": "USD"}` |

```bash
curl "https://hssi.hsdcloud.org/api/view/software/1b6ddaa6-6885-46b3-b59a-ea119e61bd74/?view=jsonld"
```

```json
{
  "@context": {"...": "schema.org + codemeta/prov/sosa/dcat namespaces"},
  "@id": "https://hssi.hsdcloud.org/software/pymap3d/",
  "@type": ["SoftwareSourceCode", "SoftwareApplication"],
  "name": "PyMap3D",
  "description": [
    "Pure-Python coordinate conversions.",
    "Pure-Python coordinate conversions for geospace ecosystems, with no required dependencies beyond the standard library."
  ],
  "codeRepository": "https://github.com/scivision/pymap3d",
  "author": {"@list": [{"@type": "Person", "givenName": "Michael", "familyName": "Hirsch"}]},
  "keywords": [{"@type": "DefinedTerm", "name": "coordinate transforms"}],
  "license": "https://opensource.org/licenses/BSD-2-Clause",
  "programmingLanguage": ["Python"],
  "subjectOf": {
    "@type": "dcat:CatalogRecord",
    "@id": "https://hssi.hsdcloud.org/api/view/software/pymap3d/?view=jsonld",
    "dateModified": "2024-02-03"
  },
  "offers": {"@type": "Offer", "price": 0, "priceCurrency": "USD"}
}
```

---

## `GET`/`PATCH /api/data/software/{id}/`

The same underlying record as `/api/view/software/{id}/`, but with a
different **default** view and an additional **PATCH** method for updates.

- `GET` here defaults to `?view=standard` (raw representation) rather than
  `user` — pass `?view=user` or `?view=jsonld` explicitly to get those
  shapes instead. Same `{id}`-by-UUID-or-slug and error behavior as
  `/api/view/software/{id}/`.
- `PATCH` is documented in full in the [Submission API](Submission-API.md)
  page, since it shares the field list and validation rules with creating a
  new submission.

### Simple example

```bash
curl https://hssi.hsdcloud.org/api/data/software/pymap3d/
```

```json
{
  "id": "1b6ddaa6-6885-46b3-b59a-ea119e61bd74",
  "software_name": "PyMap3D",
  "code_repository_url": "https://github.com/scivision/pymap3d",
  "license": "4f2c...",
  "authors": ["9e1a..."]
}
```

Note the raw/standard view uses the model's own field names and leaves
foreign keys as bare IDs — contrast with `/api/view/.../?view=user` above,
which resolves `license`/`authors` into nested objects.

---

## `GET /api/search/`

Full-text and field-filtered search across visible software. Supports
inline `field:"value"` tokens mixed with free text in a single `q` string.

**Query parameters**

| Param | Required | Description |
|---|---|---|
| `q` | no | Search string. Missing/empty returns `{"results": []}` — not an error. |
| `mode` | no | `jsonld` (default) returns full JSON-LD per match; `id` returns bare UUIDs. |

**Recognized field aliases** (use as `alias:"value"` inside `q`): `name`,
`description`, `repo`, `docs`, `pid`, `author`, `publisher`, `keyword`,
`lang`, `license`, `region`, `phenomena`, `instrument`, `observatory`,
`funder`, `award`, `status`, `os`, `cpu`, `source`, `function`, `input`,
`output`, `publication`, `reference_publication`, `dataset`, `related`,
`interoperable`, `version`.

Multiple tokens for the *same* alias are OR'd together; different aliases
are AND'd together, narrowing the result set. Any leftover free text (after
field tokens are stripped out) is matched against name/description first,
then keywords, then a widening set of related fields — results are ranked
by which tier they matched in. If you supply only field filters and no free
text, results come back unranked.

**Errors:** `400 {"error": "Invalid mode '<mode>'. Must be 'id' or 'jsonld'."}`

### Simple example — plain free-text search

```bash
curl "https://hssi.hsdcloud.org/api/search/?q=magnetosphere&mode=id"
```

```json
{"results": ["1b6ddaa6-6885-46b3-b59a-ea119e61bd74", "a1f8de3a-1bde-4995-94e5-e88e841a62a6"]}
```

### Complex example — combining field filters with free text

Find Python software related to a specific instrument, mentioning "plasma"
anywhere else in its metadata:

```bash
curl -G "https://hssi.hsdcloud.org/api/search/" \
  --data-urlencode 'q=lang:"Python" instrument:"MMS" plasma'
```

```json
{
  "results": [
    {
      "@type": ["SoftwareSourceCode", "SoftwareApplication"],
      "name": "...",
      "programmingLanguage": ["Python"],
      "mentions": [{"@type": "...", "name": "MMS"}]
    }
  ]
}
```
