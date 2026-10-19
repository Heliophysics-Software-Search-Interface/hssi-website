[← Back to Documentation Home](../Home.md)

# API Reference

This section documents the HTTP API exposed by the HSSI website at
`https://hssi.hsdcloud.org`. There is no version prefix — every endpoint is
rooted directly at the domain.

## Contents

- [Sections](#sections)
- [Conventions](#conventions)
  - [camelCase on the wire, snake_case in query params](#camelcase-on-the-wire-snake_case-in-query-params)
  - [Authentication](#authentication)
  - [Error shape](#error-shape)
  - ["Visible" software only](#visible-software-only)
  - [Looking records up by slug vs. UUID](#looking-records-up-by-slug-vs-uuid)

---

## Sections

- [Software Catalog API](Software-Catalog-API.md) — read-only endpoints for
  listing, fetching, and searching published software records (e.g.
  `GET /api/list/software/` means
  `GET https://hssi.hsdcloud.org/api/list/software/`).
- [Submission API](Submission-API.md) — creating new software submissions
  and updating existing ones.
- [Utility Endpoints](Utility-Endpoints.md) — citation formatting, masked
  email lookup, and repo metadata extraction.
- [Internal Endpoints](Internal-Endpoints.md) — model-introspection
  endpoints that back the website's own forms. Not intended for external
  integrators; documented here for completeness and flagged where unstable.

## Conventions

### camelCase on the wire, snake_case in query params

Endpoints built on Django REST Framework (everything under
`/api/list/software/`, `/api/view/software/`, `/api/data/software/`, and
`/api/submission/`) run every response through a camelCase renderer, and
decamelize incoming request bodies before validating them. So:

- **Response JSON and PATCH/POST request bodies use camelCase**
  (`developmentStatus`, `softwareName`, `codeRepositoryUrl`, `fieldsUpdated`).
- **Query string parameter names stay as written below** (e.g. `?view=`,
  `?repo_url=`) — the camelCase conversion only applies to JSON body/response
  keys, not query params.

The handful of plain Django endpoints documented under
[Utility Endpoints](Utility-Endpoints.md) and
[Internal Endpoints](Internal-Endpoints.md) (`/api/citation/`,
`/api/masked_emails/...`, `/api/describe*`, `/api/models/...`, legacy
`/api/submit`) are **not** run through the camelCase renderer — their JSON
uses whatever key names are shown in their examples, as-is.

### Authentication

Most of the API is fully public (`AllowAny`) — no API key or login is
needed to read catalog data, run searches, or even submit new software.

The one exception is **partially updating an existing record**
(`PATCH /api/data/software/{id}/`), which requires a bearer token:

```
Authorization: Bearer <HSSI_UPDATE_TOKEN>
```

The token is a single shared secret configured via the `HSSI_UPDATE_TOKEN`
environment variable on the server. There's no per-user token issuance —
treat it like a deploy secret. If the server has no token configured at all,
every PATCH request is rejected regardless of what's sent (fail closed).

### Error shape

DRF-backed endpoints return structured JSON errors:

```json
{"detail": "Not found."}
```

```json
{"detail": "Unsupported view 'xml'. This endpoint supports view=jsonld."}
```

PATCH/POST validation errors return one entry per invalid field:

```json
{"notAField": "Unknown field."}
```

HTTP status codes used throughout: `400` (bad input), `403` (missing/invalid
update token), `404` (record doesn't exist or isn't publicly visible yet),
`200`/`201` (success).

### "Visible" software only

Software that hasn't finished verification has no `VerifiedSoftware` row
yet, and is **invisible to every read endpoint** — `GET` by UUID or slug
returns `404` for it, and it's excluded from `/api/list/software/` and
`/api/search/` results, even though the underlying `Software` row exists in
the database. This is intentional: it's how unpublished/in-progress
submissions stay hidden from the public catalog.

### Looking records up by slug vs. UUID

Every detail endpoint (`/api/view/software/{id}/`,
`/api/data/software/{id}/`) accepts **either** the record's UUID **or** its
slug — never its display name. `GET /api/list/software/` is the place to
find a record's slug if you only have its name:

```json
{"data": [{"id": "1b6ddaa6-...", "name": "PyMap3D", "slug": "pymap3d"}]}
```
