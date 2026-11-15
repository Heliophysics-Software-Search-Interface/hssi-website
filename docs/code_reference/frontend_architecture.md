[← Back to Code Reference](overview.md)

# Frontend Architecture

High-level overview of the TypeScript frontend: how it's built and loaded, 
how its modules are organized, and how it talks to the Django backend.

## Contents

- [Overview](#overview)
- [Entry Points](#entry-points)
- [Module Loading](#module-loading)
- [Subsystems](#subsystems)
- [Adding Code](#adding-code)

---

## Overview

The frontend is plain TypeScript with no framework. 
[esbuild](../../package.json) bundles everything under 
[`frontend/`](../../frontend) into a single file, 
`django/static/js/compiled/hssi-frontend.js`, which Django serves as a static 
file on every page.

Pages start as Django templates, and the frontend adds behavior on top: it 
fetches data from the REST API and builds HTML from it in the browser. See 
[Architecture](../architecture.md#frontend) for why new code should keep 
moving in that direction.

## Entry Points

- [`index.ts`](../../frontend/index.ts) exposes `initForms` and `initDialogue` 
on `window` for templates to call. `initForms` registers the form widget 
types and generates the form, and is called from 
`templates/pages/forms_base.html`.
- The search and filter code starts itself on page load 
([`filters/search.ts`](../../frontend/filters/search.ts), 
[`filters/filterMenu.ts`](../../frontend/filters/filterMenu.ts)), without a 
template calling it.

## Module Loading

Every module imports from [`loader.ts`](../../frontend/loader.ts) instead of 
from the file a name is defined in. `loader.ts` re-exports every module, and 
the order of its lines is the order modules load in, which avoids circular 
import problems.

## Subsystems

| Directory | Purpose | API endpoints used |
|---|---|---|
| [`modelData/`](../../frontend/modelData) | Fetches, caches, and displays database objects, and describes model structures | `/api/models/`, `/api/view/` |
| [`forms/`](../../frontend/forms) | Generates the submission and edit forms from model structures, and submits them | `/api/models/structures/`, `/api/describe_form` |
| [`filters/`](../../frontend/filters) | Homepage search, filter menus, and filter state in the URL | `/api/search/` |
| [`resources/`](../../frontend/resources) | Renders software result cards on the homepage | — |
| [`dialogues/`](../../frontend/dialogues) | Popup dialogues, including the ROR, ORCID, and DataCite DOI finders and form autofill | `/api/masked_emails/` |

[`util.ts`](../../frontend/util.ts) and 
[`simpleEvent.ts`](../../frontend/simpleEvent.ts) hold shared helpers used 
across these.

## Adding Code

- **New module:** import from `./loader` (or the matching relative path), and 
add an `export *` line to `loader.ts` after every module it depends on.
- **New form widget:** register it in `initForms` in `index.ts`.
- **New shared dialogue:** create its instance in `initDialogue` in `index.ts`.
- **After any change:** rebuild with `bun run build`, then reload the page.
