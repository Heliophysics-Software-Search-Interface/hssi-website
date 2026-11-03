[← Back to Frontend](index.md)

# resources/resourceItem.ts

The card for a single software entry in the resource list: title link,
authors, description, logo, link buttons (code, docs, publication, DOI,
SciX), and category and tag chips, with an expanded view showing the full
description, all authors and labelled name tags. Touch this when changing
what a software entry shows in the search results.

**Source:** [frontend/resources/resourceItem.ts](../../../frontend/resources/resourceItem.ts)

## Contents

- [Classes](#classes)

---

## Classes

### `ResourceItem`

A single software entry rendered as an interactive element.

| Member | Kind | Description |
|---|---|---|
| `constructor()` | constructor | Creates the empty container element; use `createFromData` to build a populated item. |
| `softwareData` | property | The software data the item displays. |
| `containerElement` | field | Contains all of the item's elements. |
| `setExpanded(expand)` | method | Switches between the compact view and the expanded view, building the name tags the first time it expands. |
| `isExpanded()` | method | Whether the expanded content is visible. |
| `destroy()` | method | Removes the item from the DOM. |
| `createFromData(data)` | static method | Creates and builds an item for the given software data. |
