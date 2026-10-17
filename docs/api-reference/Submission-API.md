# Submission API

Endpoints for creating new software records and updating existing ones.
Creating is fully public; updating requires the bearer token described in
[Overview](Overview.md#authentication).

## `POST /api/submission/` — create one or more records

**Auth:** none — `AllowAny`.

**Request body:** a JSON **array** of submission objects (not a single
object — even a one-record submission must be wrapped in `[...]`). All
items are validated and created inside one database transaction: if any
item fails validation, the whole batch is rolled back and no records are
created.

**Required fields per item:** `submitter`, `softwareName`,
`codeRepositoryUrl`, `authors`, `description`.

**All accepted fields per item** (camelCase on the wire): `submitter`,
`softwareName`, `codeRepositoryUrl`, `description`, `conciseDescription`
(≤200 chars), `documentation`, `persistentIdentifier`, `publicationDate`,
`logo`, `publisher`, `license` (must match an existing license name),
`developmentStatus`, `referencePublication`, `authors`, `programmingLanguage`,
`inputFormats`, `outputFormats`, `operatingSystem`, `cpuArchitecture`,
`softwareFunctionality` (dotted `"Parent:Child"` string for hierarchical
categories), `relatedRegion`, `relatedPhenomena`, `dataSources`, `keywords`
(free text, created if new), `relatedInstruments`, `relatedObservatories`,
`relatedPublications`, `relatedDatasets`, `relatedSoftware`,
`interoperableSoftware`, `funder`, `award`, `version`.

- `submitter` is an array of `{"email": "...", "person": {"givenName": "...", "familyName": "..."}}`.
- `authors` is an array of `{"givenName": "...", "familyName": "...", "identifier"?: "...", "affiliation"?: "..."}`.
- `version` is an object: `{"number": "...", "releaseDate"?: "...", "versionPid"?: "...", "description"?: "..."}`.
- Any field expecting a URL is validated as one; an invalid URL is a `400`.
- Any unrecognized top-level key is a `400` naming that exact key.

**Side effects on success:** a 90-day software-edit-queue entry is created
per record, and the submitter is emailed an edit link.

**Response:** `201 Created`

```json
{"status": "ok", "count": 1, "results": [{"index": 0, "softwareId": "<uuid>"}]}
```

**Errors:**
- `400 {"detail": "Root JSON value must be an array."}` if the body isn't a JSON array.
- `400 <field validation errors>` — DRF's structured per-field error object, e.g. `{"softwareName": ["This field is required."]}`.

### Simple example — minimal valid submission

```bash
curl -X POST https://hssi.hsdcloud.org/api/submission/ \
  -H "Content-Type: application/json" \
  -d '[{
    "submitter": [{"email": "ada@example.com", "person": {"givenName": "Ada", "familyName": "Lovelace"}}],
    "softwareName": "Created via API",
    "codeRepositoryUrl": "https://github.com/example/created",
    "authors": [{"givenName": "Ada", "familyName": "Lovelace"}],
    "description": "A description."
  }]'
```

```json
{"status": "ok", "count": 1, "results": [{"index": 0, "softwareId": "f3a1..."}]}
```

### Complex example — batch submission with full metadata

```bash
curl -X POST https://hssi.hsdcloud.org/api/submission/ \
  -H "Content-Type: application/json" \
  -d '[
    {
      "submitter": [{"email": "jane@example.org", "person": {"givenName": "Jane", "familyName": "Doe"}}],
      "softwareName": "Magnetosphere Toolkit",
      "codeRepositoryUrl": "https://github.com/example/magtoolkit",
      "description": "Tools for magnetosphere simulation post-processing.",
      "conciseDescription": "Magnetosphere simulation post-processing tools.",
      "authors": [{"givenName": "Jane", "familyName": "Doe", "identifier": "https://orcid.org/0000-0000-0000-0000"}],
      "license": "MIT",
      "developmentStatus": "Active",
      "programmingLanguage": ["Python"],
      "operatingSystem": ["Linux", "macOS"],
      "keywords": ["magnetosphere", "simulation"],
      "relatedInstruments": ["MMS"],
      "version": {"number": "2.1.0", "releaseDate": "2025-06-01"}
    },
    {
      "submitter": [{"email": "jane@example.org", "person": {"givenName": "Jane", "familyName": "Doe"}}],
      "softwareName": "Second package in the same batch",
      "codeRepositoryUrl": "https://github.com/example/second",
      "authors": [{"givenName": "Jane", "familyName": "Doe"}],
      "description": "A second record created in the same request."
    }
  ]'
```

```json
{
  "status": "ok",
  "count": 2,
  "results": [
    {"index": 0, "softwareId": "f3a1..."},
    {"index": 1, "softwareId": "7b2e..."}
  ]
}
```

If the second item were invalid (say, missing `authors`), the entire batch
— including the otherwise-valid first item — would roll back and the
response would be a `400` describing only the failing item's errors.

---

## `PATCH /api/data/software/{id}/` — update an existing record

**Auth:** required. Header:

```
Authorization: Bearer <HSSI_UPDATE_TOKEN>
```

Missing header, wrong prefix, or non-matching token all return
`403 {"detail": "Missing or invalid update token."}`. If the server has no
token configured at all, every PATCH is rejected the same way regardless of
what's sent.

**`{id}`:** UUID or slug of an existing, publicly visible record (same
lookup rules as the read endpoints). Unknown/unpublished `{id}` →
`404 {"detail": "Not found."}`.

**Request body:** a partial JSON object — same field list as
`POST /api/submission/` above, except:
- Nothing is required; omitted keys are left unchanged.
- **`submitter` cannot be updated via PATCH** — including it returns
  `400 {"submitter": "Updating submitter is not supported via PATCH."}`.
- An explicit `[]` on a list field (e.g. `keywords`) clears it; an explicit
  non-empty list replaces the whole set (it does not append).
- Unrecognized keys are rejected individually:
  `400 {"<key>": "Unknown field."}`.

**Side effects on success:** `dateModified` is updated to now, and if the
record has submission history, the most recent entry's modification
description is stamped with the list of changed fields.

**Response:** `200 OK`

```json
{"status": "ok", "softwareId": "<uuid>", "fieldsUpdated": ["developmentStatus"]}
```

### Simple example — update a single field

```bash
curl -X PATCH https://hssi.hsdcloud.org/api/data/software/pymap3d/ \
  -H "Authorization: Bearer $HSSI_UPDATE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"developmentStatus": "Active"}'
```

```json
{"status": "ok", "softwareId": "1b6ddaa6-6885-46b3-b59a-ea119e61bd74", "fieldsUpdated": ["developmentStatus"]}
```

### Complex example — multi-field update, replacing keywords and bumping version

```bash
curl -X PATCH https://hssi.hsdcloud.org/api/data/software/pymap3d/ \
  -H "Authorization: Bearer $HSSI_UPDATE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description after a major rewrite.",
    "keywords": ["coordinate transforms", "geodesy", "aerospace"],
    "version": {"number": "3.0.0", "releaseDate": "2026-01-15"},
    "relatedSoftware": []
  }'
```

```json
{
  "status": "ok",
  "softwareId": "1b6ddaa6-6885-46b3-b59a-ea119e61bd74",
  "fieldsUpdated": ["description", "keywords", "relatedSoftware", "version"]
}
```

Here `relatedSoftware: []` explicitly clears that relation, while
`keywords` is replaced wholesale with the three values given (not merged
with whatever keywords existed before).

### Error examples

```bash
# Wrong/missing token
curl -X PATCH https://hssi.hsdcloud.org/api/data/software/pymap3d/ \
  -H "Content-Type: application/json" -d '{"developmentStatus": "Active"}'
# -> 403 {"detail": "Missing or invalid update token."}

# Trying to change the submitter
curl -X PATCH https://hssi.hsdcloud.org/api/data/software/pymap3d/ \
  -H "Authorization: Bearer $HSSI_UPDATE_TOKEN" -H "Content-Type: application/json" \
  -d '{"submitter": [{"email": "new@example.com"}]}'
# -> 400 {"submitter": "Updating submitter is not supported via PATCH."}
```

---

## `POST /api/submit` — legacy batch submission endpoint

This predates `POST /api/submission/` above and is kept for backward
compatibility. **New integrations should use `POST /api/submission/`
instead** — it has clearer validation errors and dedicated test coverage,
while this endpoint has none.

Differences from `POST /api/submission/`:
- **No DRF, no camelCase conversion.** Field names are the legacy
  form-field names used by the HTML submission form (e.g.
  `codeRepositoryURL`, not `code_repository_url` or `codeRepositoryUrl`).
- **No auth, no permission classes at all** — it's a plain Django view, not
  gated by DRF's `AllowAny`/token system (though in practice it's equally
  open).
- Body must still be a JSON array; each item is converted through the
  website's legacy form-parsing pipeline rather than the DRF serializer.
- Success response is `200` (not `201`):
  ```json
  {"status": "ok", "count": 1, "results": [{"index": 0, "submissionId": "...", "softwareId": "..."}]}
  ```
- On any exception while processing an item, the whole batch rolls back and
  returns `400` with the raw exception message as the body — less
  structured than `POST /api/submission/`'s per-field errors.

If you're integrating something new, use `POST /api/submission/` and treat
this one as legacy/undocumented-shape.
