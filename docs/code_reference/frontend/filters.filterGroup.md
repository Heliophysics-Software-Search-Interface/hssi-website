[← Back to Frontend](index.md)

# filters/filterGroup.ts

Filter groups and the "group maker" that builds them: the user collects
filter items as chips, chooses AND/OR mode, inverts individual chips to
exclude them, and applies the result as a `FilterGroup`. Touch this when
changing how a group decides whether a software entry passes.

**Source:** [frontend/filters/filterGroup.ts](../../../frontend/filters/filterGroup.ts)

## Contents

- [Types](#types)
- [Classes](#classes)

---

## Types

| Name | Description |
|---|---|
| `FilterGroupMode` | Enum for how included items combine: `Or` (0) or `And` (1). |

## Classes

### `FilterGroupMaker`

The control where selected filter items are collected as chips and turned into a `FilterGroup`.

| Member | Kind | Description |
|---|---|---|
| `constructor(menu)` | constructor | Stores the parent `FilterMenu` and creates the container element. |
| `onItemRemoved` | event | Fires with the item whenever an item is removed by clearing. |
| `containerElement` | field | Contains all display elements. |
| `build()` | method | Builds the chip container and the AND, OR, Clear and Apply controls; Apply creates a group and applies it in the parent menu. |
| `addItem(item)` | method | Adds a chip for the item if it isn't already included. |
| `removeItem(item)` | method | Removes the item's chip so it is not included in the group. |
| `clearItems()` | method | Removes all chips, firing `onItemRemoved` for each. |
| `createGroup()` | method | Creates a `FilterGroup` from the chips (inverted chips become excluded items) in the current mode, then clears the chips. |

### `FilterGroup`

A set of included and excluded filter items that software entries are tested against.

| Member | Kind | Description |
|---|---|---|
| `includedItems` | field | Items a result must match. |
| `excludedItems` | field | Items a result must not match. |
| `mode` | field | Whether a result must match any (`Or`) or all (`And`) included items. |
| `createChip()` | method | Creates a small element representing the whole group, with excluded items styled as inverted. |
| `passes(data)` | method | Whether the software data matches the included items (per `mode`) and none of the excluded items; a child item's ID also counts as a match. |
| `filterSoftware(softwares)` | method | The software entries that pass the group. |
