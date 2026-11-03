[← Back to Frontend](index.md)

# index.ts and loader.ts

`index.ts` is the frontend entry point; `loader.ts` is the barrel module that
re-exports every other module. All modules import from `loader.ts` rather than
from the file that defines a symbol, and the order of its `export *` lines is
the load order, which keeps the dependency tree explicit and avoids circular
import problems. Touch `loader.ts` when adding a module (place it after
everything it depends on) and `index.ts` when registering a new client-side
widget or dialogue.

**Source:** [frontend/index.ts](../../../frontend/index.ts) · [frontend/loader.ts](../../../frontend/loader.ts)

## Contents

- [Functions](#functions)

---

## Functions

| Function | Description |
|---|---|
| `initForms()` | Registers the widget types that can be generated client-side (basic input widgets, `RorWidget`, `OrcidWidget`, `DataciteDoiWidget`, `AuthorIdentifierWidget`, `ModelBox` and the autofill widgets), then generates the form. Exposed on `window`. |
| `initDialogue()` | Creates the shared dialogue instances: confirm, autofill and text input dialogues, and the ROR, ORCID and DataCite DOI finders. Exposed on `window`. |
