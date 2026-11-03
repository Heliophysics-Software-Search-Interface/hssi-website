[← Back to Frontend](index.md)

# forms/widgets/widget.ts

The abstract base class for every form widget, plus the widget registry and
the `data-hssi-*` attribute names that tie widgets to their HTML elements.
Touch this when writing a new widget type or changing how widgets are found
and initialized.

**Source:** [frontend/forms/widgets/widget.ts](../../../frontend/forms/widgets/widget.ts)

## Contents

- [Constants](#constants)
- [Types](#types)
- [Classes](#classes)

---

## Constants

| Name | Description |
|---|---|
| `propertiesDataValue` | `"json-properties"`: the attribute (and JSON `<script>` marker) holding a widget's configuration properties. |
| `uidAttribute` | `"data-hssi-uid"`: attribute holding a widget element's UID. |
| `widgetAttribute` | `"data-hssi-widget"`: attribute naming the widget class an element belongs to. |
| `widgetDataAttribute` | `"data-hssi-data"`: attribute marking a JSON `<script>` element with widget data. |
| `typeAttribute` | `"data-hssi-type"`: attribute holding a widget element's type. |

## Types

| Name | Description |
|---|---|
| `BaseProperties` | Configuration properties shared by all widgets: `requirementLevel`, `maxLength`, `autofillSiblings`. Subclasses extend it with their own. |
| `AnyInputElement` | An `<input>`, `<textarea>` or `<select>` element, optionally carrying a `data` JSON object. |
| `WidgetType` | Constructor type of a widget class: `new (elem, field) => Widget`. |

## Classes

### `Widget`

Abstract base class for all widgets. The class name must match the widget type name used by the backend form structure. **Abstract**

| Member | Kind | Description |
|---|---|---|
| `constructor(elem, parentField)` | constructor | Binds the widget to its root element and field, applies default properties, then any from the element's `json-properties` attribute. |
| `element` | field | Root element of the widget; all widget elements live inside it. |
| `parentField` | field | The `ModelSubfield` this widget belongs to, or `null`. |
| `properties` | field | The widget's configuration properties. |
| `onEnterValue` | event | Fires with the input value once the user stops typing (after the entry delay). |
| `onValueChanged` | event | Change event for subclasses to fire; the base class never triggers it. |
| `inputEntryCallbackID` | field (protected) | Timer ID of the pending value-entered callback. |
| `initialize(readOnly)` | method | Custom initialization: loads JSON data, sets the requirement-level attribute, and hooks up input events. |
| `getInputElement()` | method (abstract) | Returns the element the user types or selects in; every subclass implements this. |
| `getInputValue()` | method | The input element's value, trimmed. |
| `setValue(value, notify)` | method | Sets the input value, and by default notifies the parent field that it changed. |
| `destroy()` | method | Removes the widget's element from the page. |
| `getDefaultProperties()` | method (protected) | Default configuration properties; override to add a widget's own defaults. |
| `collectData()` | method (protected) | Loads properties from a JSON `<script>` element inside the widget. |
| `checkForInputElementEventInit()` | method (protected) | Attaches input listeners, polling every second until the input element exists. |
| `getValueEntryDelay()` | method (protected) | Milliseconds to wait after input before treating a value as entered: 500 for text-like inputs, 50 otherwise. |
| `triggerValueEntered()` | method (protected) | Fires `onEnterValue` and expands the parent field's subfields the first time a value is entered. |
| `onInputChange(event)` | method (protected) | Input handler: schedules `triggerValueEntered` after the entry delay and notifies the parent field. |
| `initializeWidgets(widgetClass)` | static method | Creates and initializes a widget for every element on the page tagged with that widget class's name. |
| `initializeRegisteredWidgets()` | static method | Runs `initializeWidgets` for every registered widget type. |
| `registerWidgets(...widgetClasses)` | static method | Registers widget types by class name so form generation can look them up. |
| `getRegisteredWidget(className)` | static method | A registered widget type by name, or `null`. |
| `getAllRegisteredWidgets()` | static method | All registered widget types. |
