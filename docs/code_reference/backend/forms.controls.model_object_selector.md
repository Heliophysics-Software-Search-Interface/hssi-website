[← Back to Backend](index.md)

# forms/controls/model_object_selector.py

A Django form widget that lets users pick one or more existing objects of a
model through an autocomplete text box or dropdown. Touch this when changing
how a model-backed selector is configured or which choices it renders.

**Source:** [django/website/forms/controls/model_object_selector.py](../../../django/website/forms/controls/model_object_selector.py)

## Contents

- [Types](#types)
- [Classes](#classes)

---

## Types

| Name | Description |
|---|---|
| `ModelObjectChoice` | Named tuple describing one selectable object: `id`, `name`, `keywords` and `tooltip`. |

## Classes

### `ModelObjectSelector`

Widget for selecting one or multiple instances of its associated model. **Extends:** `forms.TextInput`

| Member | Kind | Description |
|---|---|---|
| `constructor(model, requirement, attrs)` | constructor | Sets the target model and requirement level, and reads the selector options from `attrs`. |
| `attrs` | class attribute | HTML attributes of the widget. |
| `template_name` | class attribute | `"widgets/model_object_selector.html"`. |
| `model` | class attribute | The `HssiModel` whose objects are offered as choices. |
| `filter` | class attribute | Queryset filter keyword arguments applied to the choices. |
| `case_sensitive_filtering` | class attribute | Whether filtering is case sensitive; the constructor never overrides the default `False`. |
| `multi_select` | class attribute | Whether multiple objects can be selected. |
| `filter_on_focus` | class attribute | Whether choices are filtered when the input gains focus. |
| `dropdown_button` | class attribute | Whether a dropdown button is shown. |
| `dropdown_on_focus` | class attribute | Whether the dropdown opens when the input gains focus. |
| `dropdown_on_blank` | class attribute | Whether the dropdown opens when the input is empty. |
| `option_tooltips` | class attribute | Whether choices show tooltips. |
| `new_object_field` | class attribute | Name of a field used to create new objects, or `None`. |
| `requirement_level` | class attribute | `RequirementLevel` of the field; `RECOMMENDED` by default. |
| `dropdown_selector(model, mutli_select, requirement, attrs)` | class method | Creates a selector with a dropdown button that doesn't filter on focus. |
| `auto_textbox(model, mutli_select, requirement, attrs)` | class method | Creates an autocomplete text box whose dropdown doesn't open on focus or when blank. |
| `modelbox(model, mutli_select, requirement, attrs)` | class method | Creates a selector with default options. |
| `get_context(name, value, attrs)` | method | Template context with the selector's properties and its choices, both also as JSON. |
| `get_choices()` | method | All objects of the model matching `filter`, as `ModelObjectChoice`s. |
