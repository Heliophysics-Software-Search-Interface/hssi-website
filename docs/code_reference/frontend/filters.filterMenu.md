[← Back to Frontend](index.md)

# filters/filterMenu.ts

The filter menu shown above the resource list: its tabs, the filter group
maker, the active filter group chips, and syncing active filters with the
`filt` URL parameter. Touch this when adding a filter tab to the page or
changing how filters are applied to a resource view.

**Source:** [frontend/filters/filterMenu.ts](../../../frontend/filters/filterMenu.ts)

## Contents

- [Constants](#constants)
- [Classes](#classes)
- [Functions](#functions)

---

## Constants

| Name | Description |
|---|---|
| `styleHidden` | `"hidden"`: CSS class used to hide filter elements. |
| `styleSelected` | `"selected"`: CSS class marking a selected tab, item or mode button. |

## Classes

### `FilterMenu`

The filter menu that holds the filter tabs and applies active filter groups to a resource view. Exposed on `window`.

| Member | Kind | Description |
|---|---|---|
| `main` | property (static) | The first `FilterMenu` created on the page. |
| `constructor(view)` | constructor | Creates the container element and, for the first menu created, registers it as `main` and re-parses the URL on `popstate`. |
| `containerElement` | field | Contains all elements of the menu. |
| `tabHeadersElement` | field | Container for the tab header elements. |
| `tabContentsElement` | field | Container for the tab content elements. |
| `tabs` | field | All filter tabs selectable in the menu. |
| `currentTab` | property | The tab currently selected by the user. |
| `targetView` | property | The resource view the filters apply to; defaults to `ResourceView.main`. |
| `build()` | method | Builds the menu's elements (group maker, active group chips, tabs), selects the first tab, and applies filter groups from the URL. |
| `selectTab(tab)` | method | Sets the current tab and shows its contents. |
| `setItemSelected(item, selected)` | method | Marks a filter item as selected or not, adding it to or removing it from the filter group maker. |
| `getTabForField(field)` | method | The tab that filters the given software field. |
| `addFilterGroup(group)` | method | Adds a filter group to the active filter groups without applying it. |
| `applyFilters(pushHistory)` | method | Applies all active filter groups to the target view, renders their chips, records them in the URL, and reapplies the search query. On phones, also closes the expanded Filters bar. |

## Functions

| Function | Description |
|---|---|
| `makeFilterMenuElement(targetView)` | Creates a `FilterMenu` with the category, programming language, region and data sources tabs, appends it next to the current `<script>` element, and builds it. Exposed on `window`. |
