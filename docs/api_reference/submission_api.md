[← Back to Overview](overview.md)

# Submission API

Endpoints for creating new software records and updating existing ones.
Creating is fully public; updating requires the bearer token described in
[Overview](overview.md#authentication).

Each record created through `POST /api/submission/` or `POST /api/submit` opens a "New submission" issue in the hssi-website GitHub repository, as submissions through the website's form do, so the team knows to review it. A batch that fails opens none. Only a server with a GitHub token configured, such as production, opens these issues.

## Contents

- [POST /api/submission/](#post-apisubmission)
- [PATCH /api/data/software/{id}/](#patch-apidatasoftwareid)
- [POST /api/submit](#post-apisubmit)

---

## `POST /api/submission/`

**Create one or more records.**

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
- `authors` is an array of `{"givenName": "...", "familyName": "...", "identifier"?: "...", "affiliation"?: [{"name": "...", "identifier"?: "..."}]}`
  — note `affiliation` is itself an array of organization objects, not a string. Two entries that resolve to the same person, such as two with the same `identifier` or the same name, are a `400`. So is `personId`, which only PATCH accepts, even when it's empty or `null`.
- `version` is an object: `{"number": "...", "releaseDate"?: "...", "versionPid"?: "...", "description"?: "..."}`.
- `award` is an array of `{"name": "...", "identifier"?: "...", "funder"?: {"name": "...", "identifier"?: "..."}}`. An award whose `identifier` (or, without one, `name`) matches an existing award reuses that record as it is, since other software may share it, so `funder` only applies to a new award. A PATCH can also fill in the funder of an existing award that has none, but never replaces one. A `name` over 128 characters is a `400`.
- Any field expecting a URL is validated as one; an invalid URL is a `400`.
- **Unrecognized top-level keys are silently ignored on create** — unlike
  PATCH below, there's no whitelist check here. A typo'd field name (e.g.
  `sofwareName`) won't error; it just won't do anything, and the record
  will fail the *required*-field check instead if that typo was on a
  required field.

**Side effects on success:** a 90-day software-edit-queue entry is created
per record, and the submitter is emailed an edit link.

**Response:** `201 Created`

```json
{"status": "ok", "count": 1, "results": [{"index": 0, "softwareId": "<uuid>"}]}
```

**Errors:**
- `400 {"detail": "Root JSON value must be an array."}` if the body isn't a JSON array.
- `400 <field validation errors>` — one entry per invalid field, e.g. `{"softwareName": "This field is required."}` (a bare string per field, not a list).

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

## `PATCH /api/data/software/{id}/`

**Update an existing record.**

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
- `authors` entries resolve to person records that other software may share. Without `personId`, a person matched by `identifier` keeps its stored names (only empty ones are filled). On updates only, where "the same" name means the same words in the same order, ignoring capitalization, accents and hyphens, however `givenName` and `familyName` split them:
  - An `identifier` that matches no person is attached to this record's current author with the same full name and no identifier, instead of creating a new person. Authors of other records, and authors with a different identifier, are never matched. If more than one current author has that full name and no identifier, it's a `400`.
  - A person resolved by `identifier` with the same full name takes the sent names (stored `Maria de` / `Souza`, sent `Maria` / `De Souza`), so one PATCH can attach an ORCID and correct the split, capitalization, accents or hyphens together. Sent names with fewer accents than the stored ones are not applied, so a source that drops accents can't remove them. A different full name is not applied.
  - An author sent with an empty or missing `givenName` resolves to this record's one current author stored without a given name under the same family name, so records with such authors stay patchable. That person is left as it is, apart from an `identifier` filling an empty one when no other person holds it. Any other blank given name is a `400`, and a person without a given name is never created.
- `personId` (PATCH only) selects an existing person by UUID, including one linked only to other records, so one request can add that person here and fill in their `identifier`. The UUID is the person's `id` in the `authors` of `GET /api/view/software/{id-or-slug}/`. A `personId` replaces the lookups above: it never falls back to another person or creates one.
  - It must be a UUID string naming an existing person; anything else, including empty or `null`, is a `400`.
  - The sent name must be the same full name as the person's, or it's a `400` that says how the person is stored. The person then takes the sent names, as above. An empty or missing `givenName` is accepted only when the person has none.
  - An `identifier` must be a URL. It may fill an empty identifier or repeat the stored one; a different stored identifier, or one another person holds, is a `400`. Omitting it, or sending it empty, leaves the stored identifier unchanged.
  - The changes show on every record that lists the person, so confirm the UUID is the right person before sending it.

A PATCH is all or nothing: if it fails, the record and any people or other shared records it would have changed are left as they were.

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

### Complex example — multi-field update, replacing keywords and the version record

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

Here `relatedSoftware: []` explicitly clears that relation, and `keywords`
is replaced wholesale with the three values given (not merged with
whatever keywords existed before). **`version` behaves the same way, more
destructively than it looks:** including it always creates a brand-new
version record and replaces the record's *entire* version history with
that one entry — it does not add a version alongside existing ones. If
`pymap3d` had five prior versions on file, this PATCH leaves it with just
the one (`3.0.0`).

### Example — add a person from another record and attach their ORCID

`authors` replaces the whole list, so the request lists every author to keep, in order. The second author is a person already linked to another record, selected by the `id` that record's `GET /api/view/software/{id-or-slug}/` response gives them:

```bash
curl -X PATCH https://hssi.hsdcloud.org/api/data/software/pymap3d/ \
  -H "Authorization: Bearer $HSSI_UPDATE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "authors": [
      {"givenName": "Michael", "familyName": "Hirsch"},
      {"personId": "<person id>", "givenName": "Jane", "familyName": "Doe", "identifier": "https://orcid.org/0000-0000-0000-0000"}
    ]
  }'
```

```json
{"status": "ok", "softwareId": "1b6ddaa6-6885-46b3-b59a-ea119e61bd74", "fieldsUpdated": ["authors"]}
```

The person stays on their other records, which now show the ORCID too.

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

## `POST /api/submit`

**Legacy batch submission endpoint.**

This predates `POST /api/submission/` above and is kept for backward
compatibility. **New integrations should use `POST /api/submission/`
instead** — it has clearer validation errors and dedicated test coverage,
while this endpoint has none.

Differences from `POST /api/submission/`:
- **No DRF, no camelCase conversion.** Field names are mostly the same
  snake_case names as the model/API fields (`software_name`,
  `code_repository_url`, `description`, `authors`, `development_status`,
  `version`, with nested `name`/`identifier`/`affiliation` on
  people/orgs) — **not** camelCase like `POST /api/submission/` uses. A
  couple of fields break that pattern inconsistently (`publisher.publisherIdentifier`,
  `license.licenseURI`), which is part of why this endpoint is deprecated
  in favor of the more consistent one above.
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
  returns `400` with the **raw exception message as a plain-text body**
  (`HttpResponseBadRequest`) — not JSON like every other error in this API,
  so don't assume `response.json()` will work on a failed call here.

If you're integrating something new, use `POST /api/submission/` and treat
this one as legacy/undocumented-shape.
