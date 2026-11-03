[← Back to Frontend](index.md)

# filters/filterMenuItem.ts

The selectable items listed in a filter tab, including the subclasses for
controlled-list, graph-list and category models. Items can have one level of
child items, each separately selectable. Touch this when changing how a filter
item is displayed or adding an item type for a new filter tab.

**Source:** [frontend/filters/filterMenuItem.ts](../../../frontend/filters/filterMenuItem.ts)

## Contents

- [Classes](#classes)

---

## Classes

### `FilterMenuItem`

A selectable item in a filter tab, with an optional single level of selectable child items.

| Member | Kind | Description |
|---|---|---|
| `constructor(parent, data)` | constructor | Stores the parent tab and the item's data and creates its `<li>` container. |
| `parentTab` | field (protected) | The `FilterTab` the item belongs to. |
| `data` | field (protected) | The item's JSON data. |
| `parentFilterItem` | property | The parent item if this is a child item, else `null`. |
| `targetSoftwareField` | property | The software field the parent tab filters. |
| `targetModel` | property | The model name of the parent tab. |
| `containerElement` | field | Contains all other elements of the item. |
| `labelElement` | field | Holds the display text, checkbox and chip. |
| `checkboxElement` | field | The checkbox the user interacts with. |
| `subContainerElement` | field | Contains the child items. |
| `subItems` | field | The item's child items. |
| `onExpand` | event | Intended to fire when the item's children are expanded; never triggered in this module. |
| `id` | property | The item's UUID, from its data. |
| `labelString` | property | The label text shown for the item. |
| `parentMenu` | property | The `FilterMenu` the item belongs to. |
| `isExpanded` | property | Whether the child items are visible. |
| `createChip()` | method | Creates a small element representing the item, via `ModelData.createChip`, falling back to a clone of the item's container. |
| `build()` | method | Builds the checkbox, chip, label, expand button and child items, wiring clicks to select the item in the menu. |
| `buildChildItem(child)` | method | Sets this item as the child's parent and builds the child. |
| `destroy()` | method | Destroys the child items and removes the item's element from the DOM. |
| `setSubitemsExpanded(expand)` | method | Shows or hides the child items and updates the expand button. |

### `ControlledListItem`

Base item type for data from the `ControlledList` Django model. **Extends:** `FilterMenuItem`

| Member | Kind | Description |
|---|---|---|
| `objectData` | property | The item's data as a JSON object. |
| `name` | property | Get/set the `name` field of the data. |
| `abbreviation` | property | Get/set the `abbreviation` field of the data. |
| `identifier` | property | Get/set the `identifier` field of the data. |
| `labelString` | property | Overrides to return `name`. |
| `build()` | method | Overrides to also set the checkbox's `value` and `id` to the item's ID. |
| `createChip()` | method | Overrides so an item without an ID gets a chip based on its first child, showing the abbreviation with the name as the title. |

### `GraphListItem`

Base item type for data from the `ControlledGraphList` Django model, which already carries nested parent/child data. **Extends:** `ControlledListItem`

| Member | Kind | Description |
|---|---|---|
| `childData` | property | The `children` array of the data. |
| `parentData` | property | The `parents` array of the data. |

### `CategoryItem`

Item type used in the `CategoryFilterTab`. **Extends:** `GraphListItem`

| Member | Kind | Description |
|---|---|---|
| `bgColor` | property | The category's `backgroundColor`. |
| `textColor` | property | The category's `textColor`. |
| `children` | property | `subItems` typed as `CategoryItem`s. |
| `labelString` | property | Overrides to return the category's `name`. |
| `build()` | method | Overrides to also add the abbreviation as a CSS class on the checkbox. |
