[← Back to Overview](Overview.md)

# Utility Endpoints

Smaller, special-purpose public endpoints that support specific pages/flows
on the website rather than general catalog access. None of these are run
through the camelCase renderer (see [Overview](Overview.md)) — they use
plain `snake_case`/literal key names as shown below.

## Contents

- [GET /api/citation/](#get-apicitation)
- [GET /api/masked_emails/{uid}/](#get-apimasked_emailsuid)
- [GET /api/describe and GET /api/describe_form](#get-apidescribe-and-get-apidescribe_form)
  - [GET /api/describe](#get-apidescribe)
  - [GET /api/describe_form](#get-apidescribe_form)

---

## `GET /api/citation/`

**Format a citation for a DOI.**

Proxies a DOI to a content-negotiation citation service and caches the
formatted result for one hour.

**Query parameters**

| Param | Required | Description |
|---|---|---|
| `doi` | yes | Must start with the literal prefix `https://doi.org/`. |
| `style` | no | Default `apa`. One of: `apa`, `harvard-cite-them-right`, `modern-language-association`, `vancouver`, `chicago-fullnote-bibliography`, `ieee`, `bibtex`, `nature`, `science`, `american-geophysical-union`, `elsevier-harvard`. |

**Errors:**
- `400 {"error": "Invalid DOI URL"}` — `doi` missing the required prefix.
- `400 {"error": "Unsupported citation style"}` — unrecognized `style`.
- `504 {"error": "DOI service timed out"}`
- `502 {"error": "Failed to fetch citation: <details>"}`

### Simple example

```bash
curl "https://hssi.hsdcloud.org/api/citation/?doi=https://doi.org/10.1234/example.v1"
```

```json
{"citation": "Doe, J. (2024). Example Software (v1). https://doi.org/10.1234/example.v1"}
```

### Complex example — a specific citation style

```bash
curl "https://hssi.hsdcloud.org/api/citation/?doi=https://doi.org/10.1234/example.v1&style=bibtex"
```

```json
{"citation": "@misc{doe2024example,\n  author = {Doe, Jane},\n  title = {Example Software},\n  year = {2024},\n  doi = {10.1234/example.v1}\n}"}
```

Repeating the same `doi`+`style` pair within an hour is served from cache
rather than re-querying the upstream citation service.

---

## `GET /api/masked_emails/{uid}/`

**Look up masked submitter emails.**

Given a software record's UUID, returns a privacy-preserving masked version
of each email address on file for it (first/last character of the local
part kept, the rest replaced). Used by the "request an edit link" flow so a
user can confirm which address to type without the full address being
exposed on the page.

**Path parameter:** `{uid}` — the software's UUID.

**Response:** `{"emails": ["j***e@example.com"]}`, or `{"emails": []}` if
there's no submission info on file for that record.

**Errors:** an unhandled internal error returns a bare `500` with no JSON
body — this endpoint does not have the structured error handling the DRF
endpoints have.

### Simple example

```bash
curl https://hssi.hsdcloud.org/api/masked_emails/1b6ddaa6-6885-46b3-b59a-ea119e61bd74/
```

```json
{"emails": ["j***e@example.com"]}
```

### Complex example — no submission info on file

```bash
curl https://hssi.hsdcloud.org/api/masked_emails/00000000-0000-0000-0000-000000000000/
```

```json
{"emails": []}
```

---

## `GET /api/describe` and `GET /api/describe_form`

**Repo metadata extraction.**

Both shell out to the [SOMEF](https://github.com/KnowledgeCaptureAndDiscovery/somef)
CLI tool to analyze a code repository and extract CodeMeta-style metadata.
These back the submission form's "auto-fill from repo URL" feature rather
than being general-purpose catalog endpoints, and have no automated test
coverage.

### `GET /api/describe`

| Param | Required | Description |
|---|---|---|
| `target` | no | URL-encoded repository URL to analyze. Defaults to the HSSI website's own repo if omitted. |
| `fmt` | no | Output format flag passed through to the `somef` CLI. Default `o`. |

Returns the raw SOMEF/CodeMeta JSON with `Content-Type: application/ld+json`.

```bash
curl "https://hssi.hsdcloud.org/api/describe?target=https%3A%2F%2Fgithub.com%2Fscivision%2Fpymap3d"
```

```json
{"name": "pymap3d", "description": "...", "license": "...", "...": "raw SOMEF/CodeMeta output"}
```

### `GET /api/describe_form`

Same parameters as `/api/describe`, but maps the SOMEF output onto HSSI's
own submission-form field names (so the frontend can drop the result
straight into the new-submission form) and returns plain `application/json`.

```bash
curl "https://hssi.hsdcloud.org/api/describe_form?target=https%3A%2F%2Fgithub.com%2Fscivision%2Fpymap3d"
```

```json
{"softwareName": "pymap3d", "codeRepositoryUrl": "https://github.com/scivision/pymap3d", "license": "BSD-2-Clause"}
```

> **Operational note:** `/api/describe` writes a scratch file to the
> filesystem root (`/<uuid4>.json`) while it runs, rather than a temp
> directory. Not something to replicate elsewhere in the codebase, and
> worth knowing about if you ever see stray UUID-named `.json` files
> appear at `/` on the server.
