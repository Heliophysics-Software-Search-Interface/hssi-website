[← Back to Frontend](index.md)

# resources/resourceView.ts

The list of software entries on the search page. With no search or filter in
the URL it shows pages of 25 entries (tracked in the `page` URL parameter);
searching or filtering loads all entries and shows the matching ones. Touch
this when changing how results are loaded, paginated or displayed as a list.

**Source:** [frontend/resources/resourceView.ts](../../../frontend/resources/resourceView.ts)

## Contents

- [Classes](#classes)
- [Functions](#functions)

---

## Classes

### `ResourceView`

A list-style display of software entries from the HSSI database.

| Member | Kind | Description |
|---|---|---|
| `onMainViewCreated` | event (static) | Fires when the first (main) view is created. |
| `onReady` | event | Fires when the view's initial data has been fetched. |
| `main` | property (static) | The main view, which search queries update; the first view created. |
| `getViewInElement(element)` | static method | The view attached to the given element, if any. |
| `setParentElement(element)` | method | Sets the element the view is attached to, for lookup by `getViewInElement`. |
| `containerElement` | field | Contains all of the view's elements. |
| `constructor()` | constructor | Creates the container, "no results" message and pagination controls, registering the view as `main` if it is the first. |
| `onPopState()` | method | Loads the page in the `page` URL parameter after browser back/forward, when paginated. |
| `awaitAllItems()` | method | Loads all software data and leaves paginated mode. |
| `resetToPaginatedMode()` | method | Returns to the first page of paginated mode; does nothing if already paginated. |
| `clearFilter()` | method | Clears the UID restriction so all loaded items are shown. |
| `getAllItems()` | method | All software data loaded in the view. |
| `getActiveItems()` | method | The software data of the items currently displayed. |
| `getFilteredItems()` | method | The loaded software data within the view's UID restriction, or all of it if there is none. |
| `refreshItems()` | method | Recreates the displayed items from the loaded data, respecting the UID restriction, and updates the result count. |
| `filterToItems(uids)` | method | Restricts the view to the given software UIDs; throws if one is not a valid UUIDv4. |
| `showItems(items)` | method | Displays the given software data without replacing the view's loaded data. |
| `fetchAndBuild()` | method | Fetches the restricted UIDs, one page, or all software (if a search or filter is in the URL), then fires `onReady` and builds the items. |

## Functions

| Function | Description |
|---|---|
| `makeResourceView(uids)` | Creates a `ResourceView`, optionally restricted to the given UIDs, attaches it to the current `<script>` element's parent, fetches its data, and handles `popstate`. Not exported; exposed on `window`. |
