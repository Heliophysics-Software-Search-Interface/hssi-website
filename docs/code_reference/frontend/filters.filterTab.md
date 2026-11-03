[← Back to Frontend](index.md)

# filters/filterTab/

The tabs of the filter menu. `FilterTab` fetches every row of one model,
turns them into filter items and builds the tab's header and item list; each
small subclass binds a tab to a specific model and software field. Touch this
when adding a new filter tab or changing how a tab's items are built.

**Source:** [frontend/filters/filterTab/filterTab.ts](../../../frontend/filters/filterTab/filterTab.ts) · [frontend/filters/filterTab/categoryFilterTab.ts](../../../frontend/filters/filterTab/categoryFilterTab.ts) · [frontend/filters/filterTab/dataSourcesFilterTab.ts](../../../frontend/filters/filterTab/dataSourcesFilterTab.ts) · [frontend/filters/filterTab/phenomenaFilterTab.ts](../../../frontend/filters/filterTab/phenomenaFilterTab.ts) · [frontend/filters/filterTab/programmingLanguageFilterTab.ts](../../../frontend/filters/filterTab/programmingLanguageFilterTab.ts) · [frontend/filters/filterTab/regionFilterTab.ts](../../../frontend/filters/filterTab/regionFilterTab.ts)

## Contents

- [Classes](#classes)

---

## Classes

### `FilterTab`

A tab in the filter menu that lists the rows of one model as filter items.

| Member | Kind | Description |
|---|---|---|
| `constructor(parentMenu)` | constructor | Creates the header and content container elements and stores the parent menu. |
| `headerElement` | field | The selectable header for the tab. |
| `contentContainerElement` | field | Contains the item list and its structure. |
| `itemContainerElement` | field | The `<ul>` containing the filter item elements. |
| `targetModel` | field | Name of the model the filter items are fetched from. |
| `targetField` | field | The software data field the tab filters. |
| `rootItems` | field | Filter items displayed directly, not as children of other items. |
| `selectedItems` | field | Filter items currently selected by the user. |
| `parentMenu` | field | The `FilterMenu` the tab belongs to. |
| `isDropdown` | field (protected) | Whether the item list gets the dropdown styles. |
| `modelData` | field (protected) | The fetched model rows. |
| `onReady` | event | Fires when the tab's elements are built and ready for display. |
| `headerText` | property | Text shown in the tab header; defaults to `targetModel`. |
| `build()` | method | Fetches the model data, then creates the items, builds the header and content, and fires `onReady`. |
| `setContentsVisible(visible)` | method | Shows or hides the tab contents (not the header). |
| `itemDataValid(itemData)` | method (protected) | Whether a model row should become a root item; always `true` here. |
| `createItem(itemData)` | method (protected) | Creates a root filter item for a model row. |
| `findItemWithUid(uid)` | method | The root or child item with the given UID, waiting for `onReady` if items aren't built yet. |
| `refreshItems()` | method | Recreates the root items from the model data. |
| `rebuildHeaderElement()` | method | Rebuilds the header, which selects this tab when clicked. |
| `rebuildContentElements()` | method | Rebuilds the item list and builds every root item into it. |
| `fetchModelData()` | method (protected) | Loads all rows of `targetModel` from `ModelDataCache`. |

### `ControlledListFilterTab`

A filter tab for a `ControlledList` model. **Extends:** `FilterTab`

| Member | Kind | Description |
|---|---|---|
| `fetchModelData()` | method (protected) | Overrides to sort the rows by name. |
| `createItem(itemData)` | method (protected) | Overrides to create `ControlledListItem`s. |

### `CategoryFilterTab`

The "Functionality" tab, filtering `software_functionality` by `FunctionCategory`. **Extends:** `ControlledListFilterTab`

| Member | Kind | Description |
|---|---|---|
| `constructor(parentMenu)` | constructor | Sets the target model and field. |
| `headerText` | property | Overrides to return `"Functionality"`. |
| `categories` | property | The root items as `CategoryItem`s. |
| `categoryData` | property | The model data as JSON objects. |
| `itemDataValid(itemData)` | method (protected) | Overrides so only categories without parents become root items. |
| `createItem(itemData)` | method (protected) | Overrides to create a `CategoryItem` with its direct child categories as sub-items. |

### `DataSourcesFilterTab`

The "Data Source" tab, filtering `data_sources` by `DataInput`. **Extends:** `ControlledListFilterTab`

| Member | Kind | Description |
|---|---|---|
| `constructor(parentMenu)` | constructor | Sets the target model and field. |
| `headerText` | property | Overrides to return `"Data Source"`. |

### `PhenomenaFilterTab`

The "Phenomena" tab, filtering `related_phenomena` by `Phenomena`. Not currently added to the filter menu. **Extends:** `ControlledListFilterTab`

| Member | Kind | Description |
|---|---|---|
| `constructor(parentMenu)` | constructor | Sets the target model and field. |
| `headerText` | property | Overrides to return `"Phenomena"`. |

### `ProgrammingLanguageFilterTab`

The "Prog. Language" tab, filtering `programming_language` by `ProgrammingLanguage`. **Extends:** `ControlledListFilterTab`

| Member | Kind | Description |
|---|---|---|
| `constructor(parentMenu)` | constructor | Sets the target model and field. |
| `headerText` | property | Overrides to return `"Prog. Language"`. |
| `refreshItems()` | method | Overrides to group all Python and all Fortran variants under a single "Python" and "Fortran" parent item each. |

### `RegionFilterTab`

The "Region" tab, filtering `related_region` by `Region`. **Extends:** `ControlledListFilterTab`

| Member | Kind | Description |
|---|---|---|
| `constructor(parentMenu)` | constructor | Sets the target model and field. |
| `headerText` | property | Overrides to return `"Region"`. |
